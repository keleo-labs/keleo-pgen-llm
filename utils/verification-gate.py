#!/usr/bin/env python3
"""Collect verification-agent findings for a phase, reconcile them, and gate on errors.

Each verification agent writes its findings to
`<output-dir>/_verification/phase-<N>-<verifier>.json` in the findings shape:

    {"verifier": "source-fidelity", "summary": "...", "findings": [
        {"rule": "fidelity-001", "severity": "error",
         "message": "...", "evidence": "..."}
    ]}

The reconciliation agent writes `<output-dir>/_verification/phase-<N>-reconcile.json`
in the verdict shape:

    {"overallVerdict": "fail", "summary": "...",
     "confirmed": [{"originalMessage": "...", "verdict": "confirmed",
                    "reasoning": "..."}],
     "newFindings": [{"severity": "warning", "message": "...", "evidence": "..."}]}

This script is purely mechanical: it merges, dedupes, applies the reconciler's
verdicts, writes a consolidated verdict plus a markdown summary, and sets the
exit code. Deciding whether a finding is real stays with the reconciliation
agent.

Usage:
    # Consolidate and gate after a phase's verifiers have run
    python3 utils/verification-gate.py practices/my-practice/ --phase 2 --gate

    # Fail if a verifier crashed without writing its findings file
    python3 utils/verification-gate.py practices/my-practice/ --phase 2 --gate \\
        --expect source-fidelity,alpha-semantics,coverage,naming-consistency

    # One-line verdict for a progress report
    python3 utils/verification-gate.py practices/my-practice/ --phase 1 --one-line

    # Inspect the merged findings without writing anything
    python3 utils/verification-gate.py practices/my-practice/ --phase 3 --json --no-write
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import load_json_pair  # noqa: E402


VERIFICATION_DIRNAME = "_verification"
RECONCILE_STEM = "reconcile"

# This script writes its verdict into the same directory it reads findings
# from, so a second run would otherwise ingest its own output as a verifier
# called "verdict" and double-count every finding.
RESERVED_STEMS = {"verdict", "summary"}

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
BLOCKING_SEVERITIES = {"error"}

# A reconciler verdict of "needs-context" means the finding could not be
# cleared on the evidence available. It does not block the phase, but it must
# stay visible — silently dropping it would turn an unanswered question into a
# pass.
VERDICT_ACTIONS = {
    "confirmed": "keep",
    "false-positive": "dismiss",
    "needs-context": "downgrade",
}


def _normalize(text):
    """Collapse a message to a dedupe key: case, whitespace and tail punctuation."""
    return re.sub(r"\s+", " ", (text or "").strip().lower()).rstrip(".!?,;:")


def _phase_label(phase):
    """Render a phase for filenames: 1, 1.5, 2, 3 (never 1.0), or a named stage.

    The reporting skills have one gate rather than numbered phases, so they
    pass `report` and their findings land at `report-<verifier>.json`.
    """
    try:
        as_float = float(phase)
    except (TypeError, ValueError):
        return str(phase)
    return str(int(as_float)) if as_float.is_integer() else str(as_float)


def verification_dir(directory):
    return Path(directory) / VERIFICATION_DIRNAME


def _prefix(phase):
    """Filename prefix for a stage: `phase-2-` for a numbered phase, `report-`
    for a named one. A named stage is already its own word, so `phase-report-`
    would read as a phase called "report".
    """
    label = _phase_label(phase)
    return f"phase-{label}-" if label[0].isdigit() else f"{label}-"


def findings_path(directory, phase, verifier):
    """The path a verification agent should write its findings to."""
    return verification_dir(directory) / f"{_prefix(phase)}{verifier}.json"


def discover_inputs(directory, phase):
    """Find every findings file for a phase, separating the reconcile verdict.

    Returns (findings_files, reconcile_file_or_None) with findings_files sorted
    by verifier name so output ordering is stable across runs.
    """
    vdir = verification_dir(directory)
    if not vdir.is_dir():
        return [], None

    prefix = _prefix(phase)
    reconcile = None
    files = []
    for path in sorted(vdir.glob(f"{prefix}*.json")):
        stem = path.stem[len(prefix):]
        if stem == RECONCILE_STEM:
            reconcile = path
        elif stem not in RESERVED_STEMS:
            files.append(path)
    return files, reconcile


def _verifier_name(path, phase):
    return path.stem[len(_prefix(phase)):]


def collect_findings(files, phase):
    """Read findings files into a flat list, stamping each with its verifier.

    A file that is unreadable or malformed becomes an error-severity finding of
    its own rather than being skipped — a verifier whose output cannot be parsed
    has not verified anything, and the gate must say so.
    """
    collected = []
    summaries = {}

    for path in files:
        verifier = _verifier_name(path, phase)
        data, parse_error = load_json_pair(path)

        if data is None:
            collected.append({
                "verifier": verifier,
                "rule": "process-verification",
                "severity": "error",
                "message": f"Verifier '{verifier}' produced unreadable findings",
                "evidence": parse_error or f"Could not parse {path}",
            })
            continue

        if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
            collected.append({
                "verifier": verifier,
                "rule": "process-verification",
                "severity": "error",
                "message": f"Verifier '{verifier}' output is not in the findings shape",
                "evidence": f"{path} has no 'findings' array",
            })
            continue

        summaries[verifier] = data.get("summary", "")
        for finding in data["findings"]:
            if not isinstance(finding, dict):
                continue
            collected.append({
                "verifier": data.get("verifier", verifier),
                "rule": finding.get("rule", ""),
                "severity": finding.get("severity", "warning"),
                "message": finding.get("message", ""),
                "evidence": finding.get("evidence", ""),
            })

    return collected, summaries


def check_expected(files, phase, expected):
    """Report verifiers that were expected to run but wrote no findings file."""
    present = {_verifier_name(p, phase) for p in files}
    return [
        {
            "verifier": name,
            "rule": "process-verification",
            "severity": "error",
            "message": f"Expected verifier '{name}' did not write findings",
            "evidence": f"No {findings_path('<dir>', phase, name).name} in {VERIFICATION_DIRNAME}/",
        }
        for name in expected
        if name not in present
    ]


def dedupe(findings):
    """Merge findings that say the same thing, keeping the highest severity.

    Verifiers overlap by design — coverage and source-fidelity will both notice
    a dropped concern. Reporting it twice inflates the error count and makes the
    gate look worse than the output is.
    """
    merged = {}
    order = []

    for finding in findings:
        key = (finding.get("rule", ""), _normalize(finding.get("message")))
        if key not in merged:
            merged[key] = dict(finding)
            merged[key]["verifiers"] = [finding.get("verifier", "")]
            merged[key].pop("verifier", None)
            order.append(key)
            continue

        existing = merged[key]
        if finding.get("verifier") and finding["verifier"] not in existing["verifiers"]:
            existing["verifiers"].append(finding["verifier"])
        if SEVERITY_ORDER.get(finding.get("severity"), 9) < SEVERITY_ORDER.get(existing.get("severity"), 9):
            # The verifier that rated it highest is the one justifying the
            # block, so its wording and evidence are the ones worth showing.
            existing["severity"] = finding["severity"]
            if finding.get("message"):
                existing["message"] = finding["message"]
            if finding.get("evidence"):
                existing["evidence"] = finding["evidence"]
        elif not existing.get("evidence") and finding.get("evidence"):
            existing["evidence"] = finding["evidence"]

    return [merged[k] for k in order]


def apply_reconciliation(findings, reconcile):
    """Apply the reconciler's per-finding verdicts and fold in its new findings.

    Matching is on the normalized message. A reconciler that paraphrases a
    finding will not match it, and the finding stays as the verifier reported
    it — conservative in the right direction.
    """
    if not reconcile:
        return findings, []

    verdicts = {}
    for entry in reconcile.get("confirmed") or []:
        if not isinstance(entry, dict):
            continue
        verdicts[_normalize(entry.get("originalMessage"))] = entry

    unmatched = []
    for finding in findings:
        entry = verdicts.pop(_normalize(finding.get("message")), None)
        if not entry:
            finding["reconciled"] = "unmatched"
            continue

        verdict = entry.get("verdict", "confirmed")
        finding["reconciled"] = verdict
        finding["reasoning"] = entry.get("reasoning", "")
        action = VERDICT_ACTIONS.get(verdict, "keep")
        if action == "dismiss":
            finding["dismissed"] = True
        elif action == "downgrade" and finding.get("severity") == "error":
            finding["severity"] = "warning"

    unmatched = list(verdicts.values())

    for entry in reconcile.get("newFindings") or []:
        if not isinstance(entry, dict):
            continue
        findings.append({
            "verifiers": [RECONCILE_STEM],
            "rule": entry.get("rule", ""),
            "severity": entry.get("severity", "warning"),
            "message": entry.get("message", ""),
            "evidence": entry.get("evidence", ""),
            "reconciled": "confirmed",
        })

    return findings, unmatched


def build_verdict(directory, phase, findings, summaries, reconcile, unmatched):
    live = [f for f in findings if not f.get("dismissed")]
    dismissed = [f for f in findings if f.get("dismissed")]

    errors = [f for f in live if f.get("severity") in BLOCKING_SEVERITIES]
    warnings = [f for f in live if f.get("severity") == "warning"]
    infos = [f for f in live if f.get("severity") == "info"]

    if errors:
        gate = "fail"
    elif warnings:
        gate = "pass-with-warnings"
    else:
        gate = "pass"

    verdict = {
        "directory": str(directory),
        "phase": _phase_label(phase),
        "gate": gate,
        "summary": (
            f"{len(errors)} error, {len(warnings)} warning, {len(infos)} info "
            f"({len(dismissed)} dismissed) from {len(summaries)} verifiers"
        ),
        "counts": {
            "error": len(errors),
            "warning": len(warnings),
            "info": len(infos),
            "dismissed": len(dismissed),
        },
        "verifiers": summaries,
        "findings": live,
    }

    if dismissed:
        verdict["dismissed"] = dismissed
    if reconcile and reconcile.get("summary"):
        verdict["reconcileSummary"] = reconcile["summary"]
    if unmatched:
        # A reconciler verdict with no matching finding usually means it
        # paraphrased the message. Surface it so the mismatch is visible rather
        # than silently discarded.
        verdict["unmatchedVerdicts"] = unmatched

    return verdict


def render_markdown(verdict):
    """Render the verdict for pasting into the user review gate."""
    phase = verdict["phase"]
    counts = verdict["counts"]
    lines = [
        f"## Verification gate — Phase {phase}",
        "",
        f"**Verdict:** {verdict['gate']} — {verdict['summary']}",
        "",
    ]

    if verdict.get("reconcileSummary"):
        lines += [verdict["reconcileSummary"], ""]

    for severity, heading in (("error", "Errors (blocking)"),
                              ("warning", "Warnings"),
                              ("info", "Observations")):
        group = [f for f in verdict["findings"] if f.get("severity") == severity]
        if not group:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        for finding in group:
            rule = f"`{finding['rule']}` " if finding.get("rule") else ""
            who = ", ".join(finding.get("verifiers") or []) or "unknown"
            lines.append(f"- {rule}{finding.get('message', '')} _({who})_")
            if finding.get("evidence"):
                lines.append(f"  - Evidence: {finding['evidence']}")
            if finding.get("reasoning"):
                lines.append(f"  - Reconciler: {finding['reasoning']}")
        lines.append("")

    if counts["dismissed"]:
        lines.append(
            f"_{counts['dismissed']} finding(s) dismissed as false positives "
            f"by the reconciler._"
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def calibration_warnings(phase, verifier_names):
    """Note any verifier at this gate that has never been proven to catch anything.

    A clean verdict from a verifier nobody has tested looks exactly like a clean
    verdict from one that works. This does not block -- the gate is already
    user-reviewed, and stopping a generation over an edited brief would be
    hostile -- but the reviewer should know which verifiers are unproven.
    See utils/calibrate-verifiers.py.
    """
    state_path = (Path(__file__).resolve().parent.parent / ".claude" / "skills" /
                  "verification-foundation" / "calibration.json")
    if not state_path.exists():
        return []
    try:
        recorded = json.loads(state_path.read_text(encoding="utf-8")).get("calibrations", {})
    except (OSError, ValueError):
        return []

    label = _phase_label(phase)
    unproven = [name for name in sorted(verifier_names)
                if not recorded.get(f"{label}:{name}", {}).get("passed")]
    if not unproven:
        return []
    return [{
        "verifiers": ["calibration"],
        "rule": "process-calibration",
        "severity": "info",
        "message": (
            f"{len(unproven)} verifier(s) at this gate have no passing calibration: "
            f"{', '.join(unproven)}"
        ),
        "evidence": "python3 utils/calibrate-verifiers.py --check",
    }]


def _run_gate(directory, phase, expect=None):
    """The main() pipeline without argument parsing or output, for the selftest."""
    files, reconcile_path = discover_inputs(directory, phase)
    raw, summaries = collect_findings(files, phase)
    raw.extend(check_expected(files, phase, expect or []))
    reconcile = None
    if reconcile_path:
        reconcile, _ = load_json_pair(reconcile_path)
    findings, unmatched = apply_reconciliation(dedupe(raw), reconcile)
    return build_verdict(directory, phase, findings, summaries, reconcile, unmatched)


# Each case: (label, phase, findings files, reconcile doc or None, expect list,
#             expected gate, expected live-finding count)
_SELFTEST_CASES = [
    (
        "clean phase passes", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "summary": "ok", "findings": []}},
        None, None, "pass", 0,
    ),
    (
        "a confirmed error blocks", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "summary": "1 issue", "findings": [
            {"rule": "fidelity-001", "severity": "error",
             "message": "Claim has no support in the source", "evidence": "line 42"}]}},
        None, None, "fail", 1,
    ),
    (
        "a warning passes but is carried", 2,
        {"coverage": {"verifier": "coverage", "summary": "1 gap", "findings": [
            {"rule": "coverage-002", "severity": "warning",
             "message": "Source concern thinly covered", "evidence": "section 3"}]}},
        None, None, "pass-with-warnings", 1,
    ),
    (
        "the reconciler can dismiss a false positive", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "summary": "1 issue", "findings": [
            {"rule": "fidelity-001", "severity": "error",
             "message": "Claim has no support in the source", "evidence": "line 42"}]}},
        {"overallVerdict": "pass", "summary": "false positive",
         "confirmed": [{"originalMessage": "Claim has no support in the source",
                        "verdict": "false-positive", "reasoning": "the source does say this"}]},
        None, "pass", 0,
    ),
    (
        "needs-context downgrades an error to a warning", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "findings": [
            {"rule": "fidelity-001", "severity": "error",
             "message": "Claim has no support in the source", "evidence": "line 42"}]}},
        {"overallVerdict": "pass", "summary": "needs context",
         "confirmed": [{"originalMessage": "Claim has no support in the source",
                        "verdict": "needs-context", "reasoning": "source is a sibling doc"}]},
        None, "pass-with-warnings", 1,
    ),
    (
        "an unrecognised verdict keeps the finding", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "findings": [
            {"rule": "fidelity-001", "severity": "error",
             "message": "Claim has no support in the source", "evidence": "line 42"}]}},
        {"overallVerdict": "pass", "summary": "typo in the verdict word",
         "confirmed": [{"originalMessage": "Claim has no support in the source",
                        "verdict": "dismissed", "reasoning": "not a verdict the gate knows"}]},
        None, "fail", 1,
    ),
    (
        "a paraphrased reconciler verdict does not dismiss", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "findings": [
            {"rule": "fidelity-001", "severity": "error",
             "message": "Claim has no support in the source", "evidence": "line 42"}]}},
        {"overallVerdict": "pass", "summary": "paraphrased",
         "confirmed": [{"originalMessage": "The claim is unsupported",
                        "verdict": "false-positive", "reasoning": "paraphrase"}]},
        None, "fail", 1,
    ),
    (
        "the same finding from two verifiers is deduped", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "findings": [
            {"rule": "fidelity-001", "severity": "error",
             "message": "Claim has no support in the source", "evidence": "line 42"}]},
         "coverage": {"verifier": "coverage", "findings": [
             {"rule": "fidelity-001", "severity": "error",
              "message": "Claim has no support in the source", "evidence": "line 42"}]}},
        None, None, "fail", 1,
    ),
    (
        "a verifier that never wrote its file blocks", 2,
        {"source-fidelity": {"verifier": "source-fidelity", "findings": []}},
        None, ["source-fidelity", "alpha-semantics"], "fail", 1,
    ),
    (
        "the report stage uses its own filename prefix", "report",
        {"citation-integrity": {"verifier": "citation-integrity", "findings": [
            {"rule": "cite-001", "severity": "error",
             "message": "Citation does not support the claim", "evidence": "para 2"}]}},
        None, None, "fail", 1,
    ),
    (
        "phase 1.5 is not rendered as phase 1.0", 1.5,
        {"distillation-fidelity": {"verifier": "distillation-fidelity", "findings": []}},
        None, None, "pass", 0,
    ),
]


def selftest():
    """Prove the gate blocks on what it claims to block on.

    Writes synthetic findings files into a temp directory and drives the real
    collect/dedupe/reconcile/verdict path over them. Without this, a refactor
    that stopped the gate failing on a confirmed error would look like a clean
    run on every practice.

    Pattern borrowed from ponytail's agentic benchmark (MIT): prove the
    instrument on a good and a bad reference before trusting a measurement.
    """
    import tempfile

    failures = 0
    for label, phase, findings_files, reconcile, expect, want_gate, want_count in _SELFTEST_CASES:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            vdir = verification_dir(directory)
            vdir.mkdir(parents=True, exist_ok=True)
            for verifier, doc in findings_files.items():
                findings_path(directory, phase, verifier).write_text(
                    json.dumps(doc), encoding="utf-8")
            if reconcile:
                findings_path(directory, phase, RECONCILE_STEM).write_text(
                    json.dumps(reconcile), encoding="utf-8")

            try:
                verdict = _run_gate(directory, phase, expect)
            except Exception as exc:
                print(f"XX {label}: raised {type(exc).__name__}: {exc}")
                failures += 1
                continue

            got_gate = verdict["gate"]
            got_count = len(verdict["findings"])
            if got_gate != want_gate or got_count != want_count:
                print(f"XX {label}: gate={got_gate} findings={got_count} "
                      f"(wanted gate={want_gate} findings={want_count})")
                failures += 1
            else:
                print(f"ok {label}")

    # The verdict is written into the directory it reads from, so a second run
    # must not ingest its own output as a verifier called "verdict".
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        vdir = verification_dir(directory)
        vdir.mkdir(parents=True, exist_ok=True)
        findings_path(directory, 2, "source-fidelity").write_text(json.dumps(
            {"verifier": "source-fidelity", "findings": [
                {"rule": "fidelity-001", "severity": "error",
                 "message": "Claim has no support in the source", "evidence": "line 42"}]}),
            encoding="utf-8")
        first = _run_gate(directory, 2)
        (vdir / "phase-2-verdict.json").write_text(json.dumps(first), encoding="utf-8")
        (vdir / "phase-2-summary.md").write_text(render_markdown(first), encoding="utf-8")
        second = _run_gate(directory, 2)
        if len(second["findings"]) != len(first["findings"]):
            print(f"XX re-running the gate double-counts: {len(first['findings'])} "
                  f"-> {len(second['findings'])} findings")
            failures += 1
        else:
            print("ok re-running the gate does not ingest its own verdict")

    print(f"\nselftest: {'all instruments valid' if not failures else f'{failures} BROKEN'}")
    return 0 if not failures else 1


def main():
    parser = argparse.ArgumentParser(
        description="Collect verification-agent findings for a phase and gate on errors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Verifiers write to <directory>/_verification/phase-<N>-<verifier>.json "
            "(or report-<verifier>.json with --phase report); the reconciler writes "
            "the matching -reconcile.json."
        ),
    )
    parser.add_argument("directory", nargs="?",
                        help="Practice, baseline or report output directory")
    parser.add_argument("--selftest", action="store_true",
                        help="Prove the gate blocks on what it claims to (no API, no network)")
    parser.add_argument(
        "--phase", choices=["1", "1.5", "2", "3", "report"],
        help="Stage whose findings to consolidate (`report` for the reporting skills' single gate)",
    )
    parser.add_argument(
        "--expect", metavar="NAMES",
        help="Comma-separated verifier names that must have written findings",
    )
    parser.add_argument(
        "--gate", action="store_true",
        help="Exit 1 when a blocking error survives reconciliation",
    )
    parser.add_argument("--summary", action="store_true", help="Print the markdown summary")
    parser.add_argument("--one-line", action="store_true", help="Print a single-line verdict")
    parser.add_argument("--json", action="store_true", help="Print the verdict JSON to stdout")
    parser.add_argument(
        "--no-write", action="store_true",
        help="Do not write the verdict or markdown files",
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE",
        help="Verdict JSON path (default: <directory>/_verification/phase-<N>-verdict.json)",
    )
    parser.add_argument(
        "--markdown", metavar="FILE",
        help="Markdown summary path (default: <directory>/_verification/phase-<N>-summary.md)",
    )
    parser.add_argument(
        "--path-for", metavar="VERIFIER",
        help="Print the findings path a named verifier should write to, then exit",
    )
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if not args.directory or not args.phase:
        parser.error("directory and --phase are required (or pass --selftest)")

    directory = Path(args.directory)
    label = _phase_label(args.phase)

    if args.path_for:
        print(findings_path(directory, args.phase, args.path_for))
        sys.exit(0)

    if not directory.is_dir():
        print(f"Error: not a directory: {directory}", file=sys.stderr)
        sys.exit(2)

    files, reconcile_path = discover_inputs(directory, args.phase)
    expected = [n.strip() for n in args.expect.split(",") if n.strip()] if args.expect else []

    if not files and not expected:
        print(
            f"Error: no findings files matching {_prefix(args.phase)}*.json in "
            f"{verification_dir(directory)}",
            file=sys.stderr,
        )
        sys.exit(2)

    raw, summaries = collect_findings(files, args.phase)
    raw.extend(check_expected(files, args.phase, expected))

    reconcile = None
    if reconcile_path:
        reconcile, reconcile_error = load_json_pair(reconcile_path)
        if reconcile is None:
            raw.append({
                "verifier": RECONCILE_STEM,
                "rule": "process-verification",
                "severity": "error",
                "message": "Reconciliation output is unreadable",
                "evidence": reconcile_error or f"Could not parse {reconcile_path}",
            })

    findings, unmatched = apply_reconciliation(dedupe(raw), reconcile)
    findings.extend(calibration_warnings(
        args.phase, [_verifier_name(p, args.phase) for p in files]))

    verdict = build_verdict(directory, args.phase, findings, summaries, reconcile, unmatched)
    markdown = render_markdown(verdict)

    if not args.no_write:
        vdir = verification_dir(directory)
        vdir.mkdir(parents=True, exist_ok=True)
        stem = _prefix(args.phase)
        out = Path(args.output) if args.output else vdir / f"{stem}verdict.json"
        md = Path(args.markdown) if args.markdown else vdir / f"{stem}summary.md"
        out.write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
        md.write_text(markdown, encoding="utf-8")
        verdict["verdictPath"] = str(out)
        verdict["summaryPath"] = str(md)

    if args.one_line:
        counts = verdict["counts"]
        print(
            f"{verdict['gate'].upper()} {_prefix(args.phase).rstrip('-')} "
            f"{counts['error']}E/{counts['warning']}W/{counts['info']}I {directory}"
        )
    elif args.summary:
        print(markdown, end="")
    elif args.json or not args.no_write:
        print(json.dumps(verdict, indent=2))
    else:
        print(json.dumps(verdict, indent=2))

    if args.gate:
        sys.exit(1 if verdict["gate"] == "fail" else 0)
    sys.exit(0)


if __name__ == "__main__":
    main()
