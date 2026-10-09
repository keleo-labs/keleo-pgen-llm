#!/usr/bin/env python3
"""Prove a verification agent can catch the defect it exists to catch.

The verification gate dispatches twelve agents for a single practice and about
thirty for a four-practice method, and treats what they report as the check on
meaning that mechanical validation cannot do. Nothing established that any of
them can actually detect a planted defect. A brief that has drifted into
vagueness returns a clean verdict, and a clean verdict from a blind verifier is
indistinguishable from a clean verdict from a working one.

This runs each verifier against a matched pair: a clean artifact it should pass,
and the same artifact carrying one planted defect of the kind that verifier is
for. A verifier that flags the clean one is too eager; one that misses the
planted one is not worth dispatching.

The prompt is extracted from the brief the gate actually uses, not copied, so a
reworded brief is re-tested rather than silently diverging from its calibration.

Borrowed from ponytail's judge.py (MIT), which refuses to score its matrix
unless the judge first ranks a known-bad reference above a known-good one. This
is softer by design: a stale calibration warns at the gate rather than blocking,
because the gate is already user-reviewed and a hard stop mid-generation over an
edited brief would be hostile.

Usage:
    python3 utils/calibrate-verifiers.py --list
    python3 utils/calibrate-verifiers.py --check                  # offline
    python3 utils/calibrate-verifiers.py --verifier source-fidelity --phase 2
    python3 utils/calibrate-verifiers.py --all                    # spends money

Cost: two short headless sessions per verifier, on small fixtures. Run it when
a brief changes, not routinely.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FOUNDATION = PROJECT_ROOT / ".claude" / "skills" / "verification-foundation"
VERIFIERS_DIR = FOUNDATION / "verifiers"
CALIBRATION_FILE = FOUNDATION / "calibration.json"
FIXTURES = PROJECT_ROOT / "tests" / "calibration"

ISOLATION_ENV = {
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
}

# Each pair names the verifier, the brief it lives in, the fixture directory,
# and what was planted. `expect` is the substring the defective run's findings
# must mention for the catch to count as the right catch rather than a lucky one.
PAIRS = [
    {
        "verifier": "source-fidelity",
        "phase": "2",
        "fixture": "phase-2/source-fidelity",
        "planted": (
            "An 'Onboarding Telemetry' alpha, a 'Self Optimising' state, an "
            "'Onboarding Programme Manager' persona with budget authority, an "
            "industry-median benchmarking activity, and an outcome asserting "
            "'eleven working days' and '80%' — none of which appear in the "
            "analysis, which records that nothing has been measured."
        ),
        "expect": ["telemetry", "programme manager", "eleven", "80", "benchmark",
                   "self optimising", "median"],
        "inputs": ["sources.md", "01-analysis-report.md"],
    },
]


def brief_path(phase):
    return VERIFIERS_DIR / f"phase-{phase}.md" if phase != "report" else VERIFIERS_DIR / "report.md"


def extract_prompt(phase, verifier):
    """Pull a verifier's prompt blockquote out of the brief the gate dispatches.

    Reading the live brief rather than a copy is the point: a reworded brief
    must invalidate its calibration, which cannot happen if the prompt is
    duplicated here.
    """
    path = brief_path(phase)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")

    header = re.compile(rf"^##\s+Verifier\s+\d+\s+—\s+`{re.escape(verifier)}`\s*$", re.M)
    match = header.search(text)
    if not match:
        raise ValueError(f"no '{verifier}' section in {path.name}")

    rest = text[match.end():]
    next_section = re.search(r"^##\s+", rest, re.M)
    section = rest[:next_section.start()] if next_section else rest

    lines = [re.sub(r"^>\s?", "", ln) for ln in section.splitlines() if ln.startswith(">")]
    if not lines:
        raise ValueError(f"'{verifier}' in {path.name} has no prompt blockquote")
    return "\n".join(lines).strip()


def brief_digest(phase, verifier):
    """Hash the verifier's own prompt, so an edit elsewhere in the brief does
    not spuriously invalidate a calibration that is still good."""
    return hashlib.sha256(extract_prompt(phase, verifier).encode("utf-8")).hexdigest()[:16]


def substitute(prompt, output_dir, pair):
    fixture = FIXTURES / pair["fixture"]
    values = {
        "{OUTPUT_DIR}": f"{output_dir}/",
        "{GUIDE}": f"{output_dir}/02-mapping-guide.md",
        "{REPORT}": f"{output_dir}/01-analysis-report.md",
        "{SOURCES}": f"{output_dir}/sources.md",
        "{CONTEXT}": str(PROJECT_ROOT / "deps" / "platform-adoption-kernel.json"),
        "{BASELINE}": str(PROJECT_ROOT / "deps" / "platform-adoption-kernel.json"),
        "{PARENTS}": "No parent practices",
        "{SUFFIX}": "",
        "{PRACTICE}": "Calibration Practice",
    }
    for token, value in values.items():
        prompt = prompt.replace(token, value)
    return prompt


def run_variant(pair, variant, timeout):
    """Run one verifier against one variant. Returns (findings, error)."""
    fixture = FIXTURES / pair["fixture"]
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="keleo-cal-") as tmp:
        work = Path(tmp) / "ws"
        work.mkdir()
        for name in pair["inputs"]:
            shutil.copy(fixture / name, work / name)
        for item in (fixture / variant).iterdir():
            shutil.copy(item, work / item.name)
        (work / "_verification").mkdir()

        prompt = substitute(extract_prompt(pair["phase"], pair["verifier"]), str(work), pair)
        cmd = [
            shutil.which("claude") or "claude",
            "-p", prompt,
            "--output-format", "json",
            "--permission-mode", "bypassPermissions",
            "--setting-sources", "project,local",
            "--strict-mcp-config",
        ]
        try:
            subprocess.run(cmd, cwd=work, env={**os.environ, **ISOLATION_ENV},
                           capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, "timed out"

        written = list((work / "_verification").glob("*.json"))
        if not written:
            return None, "verifier wrote no findings file"
        try:
            doc = json.loads(written[0].read_text(encoding="utf-8"))
        except ValueError:
            return None, "findings file is not valid JSON"
        return doc.get("findings", []), None


def calibrate(pair, timeout):
    name = pair["verifier"]
    print(f"\n=== {name} (phase {pair['phase']}) ===")
    print(f"planted: {pair['planted']}")

    clean, err = run_variant(pair, "clean", timeout)
    if err:
        print(f"XX clean run: {err}")
        return False
    blocking = [f for f in clean if f.get("severity") in ("error", "warning")]
    if blocking:
        print(f"XX clean run raised {len(blocking)} finding(s) — too eager:")
        for f in blocking[:3]:
            print(f"     [{f.get('severity')}] {str(f.get('message'))[:110]}")
        clean_ok = False
    else:
        print(f"ok clean run raised no error or warning ({len(clean)} info)")
        clean_ok = True

    defective, err = run_variant(pair, "defective", timeout)
    if err:
        print(f"XX defective run: {err}")
        return False
    found = [f for f in defective if f.get("severity") in ("error", "warning")]
    if not found:
        print("XX defective run raised nothing — the verifier is blind to its own defect")
        return False

    blob = " ".join(str(f.get("message", "")) + " " + str(f.get("evidence", ""))
                    for f in found).lower()
    hits = [token for token in pair["expect"] if token in blob]
    if not hits:
        print(f"XX defective run raised {len(found)} finding(s), none naming the "
              f"planted defect — a lucky catch, not a real one")
        for f in found[:3]:
            print(f"     [{f.get('severity')}] {str(f.get('message'))[:110]}")
        return False

    print(f"ok defective run named the planted defect ({len(found)} findings, "
          f"matched on: {', '.join(hits[:4])})")
    return clean_ok


def load_state():
    if CALIBRATION_FILE.exists():
        return json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
    return {"calibrations": {}}


def save_state(state):
    CALIBRATION_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def check():
    """Offline: report verifiers whose brief changed since they last passed."""
    state = load_state()
    recorded = state.get("calibrations", {})
    stale, never, ok = [], [], []

    for pair in PAIRS:
        key = f"{pair['phase']}:{pair['verifier']}"
        try:
            digest = brief_digest(pair["phase"], pair["verifier"])
        except (FileNotFoundError, ValueError) as exc:
            stale.append((key, f"brief unreadable: {exc}"))
            continue
        entry = recorded.get(key)
        if not entry or not entry.get("passed"):
            never.append(key)
        elif entry.get("briefDigest") != digest:
            stale.append((key, f"brief changed since {entry.get('at', 'unknown')}"))
        else:
            ok.append(key)

    # Verifiers with no calibration pair at all are the larger gap: nothing has
    # ever established that they work.
    uncalibrated = []
    for brief in sorted(VERIFIERS_DIR.glob("*.md")):
        phase = brief.stem.replace("phase-", "")
        for match in re.finditer(r"^##\s+Verifier\s+\d+\s+—\s+`([^`]+)`",
                                 brief.read_text(encoding="utf-8"), re.M):
            key = f"{phase}:{match.group(1)}"
            if not any(f"{p['phase']}:{p['verifier']}" == key for p in PAIRS):
                uncalibrated.append(key)

    for key in ok:
        print(f"ok    {key}")
    for key in never:
        print(f"warn  {key} — has a pair but has never passed")
    for key, why in stale:
        print(f"warn  {key} — {why}")
    if uncalibrated:
        print(f"\nNO CALIBRATION PAIR ({len(uncalibrated)}) — nothing establishes "
              f"these can catch anything:")
        for key in uncalibrated:
            print(f"      {key}")

    print(f"\n{len(ok)} calibrated, {len(stale)} stale, {len(never)} untested, "
          f"{len(uncalibrated)} with no pair")
    return 1 if (stale or never) else 0


def main():
    parser = argparse.ArgumentParser(
        description="Prove a verification agent catches the defect it exists to catch")
    parser.add_argument("--verifier", help="Calibrate one verifier by name")
    parser.add_argument("--phase", help="Phase of the verifier (with --verifier)")
    parser.add_argument("--all", action="store_true", help="Calibrate every pair (spends money)")
    parser.add_argument("--check", action="store_true",
                        help="Offline: report stale or missing calibrations")
    parser.add_argument("--list", action="store_true", help="List pairs and exit")
    parser.add_argument("--timeout", type=int, default=900, help="Per-run timeout in seconds")
    args = parser.parse_args()

    if args.list:
        for pair in PAIRS:
            print(f"  phase {pair['phase']:<6} {pair['verifier']:<28} {pair['fixture']}")
        return 0
    if args.check:
        return check()

    selected = PAIRS
    if args.verifier:
        selected = [p for p in PAIRS if p["verifier"] == args.verifier
                    and (not args.phase or p["phase"] == args.phase)]
        if not selected:
            sys.exit(f"no calibration pair for '{args.verifier}'"
                     f"{' at phase ' + args.phase if args.phase else ''}")
    elif not args.all:
        parser.error("give --verifier, --all, --check or --list")

    state = load_state()
    state.setdefault("calibrations", {})
    failures = 0
    for pair in selected:
        passed = calibrate(pair, args.timeout)
        state["calibrations"][f"{pair['phase']}:{pair['verifier']}"] = {
            "passed": passed,
            "briefDigest": brief_digest(pair["phase"], pair["verifier"]),
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fixture": pair["fixture"],
        }
        if not passed:
            failures += 1
    save_state(state)

    print(f"\ncalibration: {len(selected) - failures}/{len(selected)} verifiers proven")
    print(f"recorded in {CALIBRATION_FILE.relative_to(PROJECT_ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
