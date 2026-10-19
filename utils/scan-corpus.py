#!/usr/bin/env python3
"""Run assess-practice across every authored document and report where a defect occurs.

Triage repeatedly asks a question one document cannot answer: a defect has been
found here, where else does it occur? Answering it means running the assessment
over the whole corpus and filtering to one issue category — which is otherwise a
hand-written shell loop every time, and the loop is where the skipping of backup
directories and build artifacts gets forgotten.

Each document is assessed on its own, so assess-practice's per-directory
auto-discovery of _effective-context.json still applies.

`--validator` runs the schema and integrity validators instead of the
assessment. The two check different things, and only the assessment reached
this sweep — so an error class the validator owns was invisible to the tool
triage uses to ask where else a defect occurs. Ambiguous pattern views are the
clearest case: `validate-practice-json.py` calls them errors, the assessment
never looked, and 57 accumulated across 11 documents against a rule nobody
disputed.

Usage:
    # Where else does this defect class occur?
    python3 utils/scan-corpus.py --category outcome-forecast

    # Schema and integrity errors the assessment does not check
    python3 utils/scan-corpus.py --validator --severity error --json

    # Errors only, across one directory, as JSON
    python3 utils/scan-corpus.py --dir practices/red-hat-ai --severity error --json

    # Which documents have duplicate element names?
    python3 utils/scan-corpus.py --category structure:uniqueness uniqueness
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import get_project_root

DEFAULT_DIRS = ["baselines", "practices", "deps"]
ASSESS = Path(__file__).resolve().parent / "assess-practice.py"
VALIDATE_PRACTICE = Path(__file__).resolve().parent / "validate-practice-json.py"
VALIDATE_BASELINE = Path(__file__).resolve().parent / "validate-baseline-json.py"
DEFAULT_SCHEMA = Path(__file__).resolve().parent.parent / "deps" / "language.schema.json"


def candidate_documents(root, dirs):
    """Authored documents only — no backups, no build artifacts.

    Build artifacts are the ones named with a leading underscore
    (_effective-context.json and friends); they are regenerable and assessing
    them reports defects against a merge, not against anything anyone authored.
    """
    seen = set()
    for dirname in dirs:
        base = root / dirname
        if not base.is_dir():
            continue
        patterns = ["*.json"] if base.name == "deps" else ["*.json", "*/*.json"]
        for pattern in patterns:
            for path in sorted(base.glob(pattern)):
                if path.name.startswith("_") or "backup" in str(path).lower():
                    continue
                if path.name.endswith(".changerequest.json"):
                    continue
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                yield path


DISCOVER = Path(__file__).resolve().parent / "discover-dependencies.py"

# Categories whose findings depend on resolving the document's baseline and
# dependency practices. Without that context every symbolic reference into the
# baseline looks dangling, so reporting them unresolved would be noise rather
# than findings.
CROSSREF_CATEGORIES = (
    "crossref",
    "baseline",
    "redeclaration",
    "competency",
    "contributesto",
    "mapsto",
    "alpha-relationship",
    "evidence-coverage",
    "alpha-state-activity",
    "schema",
)


def resolve_context_paths(path):
    """Resolve a document's dependencies. Returns (baselines, parents, complete)."""
    try:
        out = subprocess.run(
            [sys.executable, str(DISCOVER), "--resolve-from", str(path), "--transitive"],
            capture_output=True, text=True, timeout=120,
        )
        deps = json.loads(out.stdout).get("dependencies", [])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
        return [], [], False

    baselines, parents, complete = [], [], True
    for dep in deps:
        dep_path = dep.get("path")
        if not dep_path and dep.get("candidates"):
            # Same document at several versions is not a real ambiguity here;
            # anything else is, and the context is then incomplete.
            names = {c.get("name") for c in dep["candidates"]}
            if len(names) == 1:
                newest = next(
                    (c for c in dep["candidates"] if c.get("newest")), dep["candidates"][0]
                )
                dep_path = newest.get("path")
        if not dep_path or "::" in dep_path:
            complete = False
            continue
        (baselines if dep.get("role") == "baselinePractice" else parents).append(dep_path)
    return baselines, parents, complete


def resolve_context(path):
    """Resolve a document's baseline and dependency practices. Returns CLI args."""
    baselines, parents, complete = resolve_context_paths(path)
    args = []
    for dep_path in baselines:
        args += ["--baseline", dep_path]
    for dep_path in parents:
        args += ["--parent", dep_path]
    return args, complete


def assess(path, schema, resolve=True):
    """Assess one document. Returns (issues, context_complete), or (None, False) on failure."""
    cmd = [sys.executable, str(ASSESS), str(path)]
    context_complete = True
    if resolve:
        context_args, context_complete = resolve_context(path)
        cmd += context_args
    if schema:
        cmd += ["--schema", str(schema)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError):
        return None, False
    try:
        return json.loads(out.stdout).get("issues", []), context_complete
    except (json.JSONDecodeError, AttributeError):
        return None, False


def validate(path, schema):
    """Validate one document against the schema and integrity rules.

    `assess-practice.py` and `validate-practice-json.py` check different
    things, and only the assessment reaches corpus-wide triage — so an
    error class the validator owns is invisible to it. Ambiguous pattern
    views are the clearest case: the validator calls them errors, the
    assessment never looked, and 50 of them accumulated across 11 documents
    against a rule nobody disputed.

    Resolving the right baseline matters more here than for the assessment.
    Pointed at the wrong one, every symbolic reference into it reports as
    dangling and a clean document shows hundreds of errors.

    Returns (issues, context_complete), or (None, False) on failure.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            kind = json.load(fh).get("kind")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None, False

    if kind not in ("practice", "method", "practiceBaseline"):
        # A change request, a working file, a fragment someone left behind.
        # Not a document this validates, and not a document that failed to
        # validate — reporting it as unreadable would overstate both.
        return [], True

    baselines, parents, complete = resolve_context_paths(path)

    if kind == "practiceBaseline":
        # validate-baseline.py: <baseline> [parent-baseline] <schema>
        cmd = [sys.executable, str(VALIDATE_BASELINE), str(path)]
        cmd += baselines[:1]
        cmd += [str(schema)]
    else:
        # validate-practice.py: <practice> <baseline> <schema> [deps ...]
        if not baselines:
            return None, False
        cmd = [sys.executable, str(VALIDATE_PRACTICE), str(path),
               baselines[0], str(schema)] + parents

    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError):
        return None, False
    try:
        report = json.loads(out.stdout)
    except (json.JSONDecodeError, AttributeError):
        return None, False

    issues = []
    for severity in ("errors", "warnings"):
        for entry in report.get(severity, []):
            issues.append({
                "severity": entry.get("severity", severity[:-1]),
                "category": entry.get("category", "integrity"),
                "path": entry.get("path", ""),
                "message": entry.get("issue", ""),
                "suggestion": entry.get("suggestion", ""),
                "autoFixable": False,
            })
    return issues, complete


def _counts_by_category(issues):
    counts = {}
    for issue in issues:
        category = issue.get("category", "?")
        counts[category] = counts.get(category, 0) + 1
    return counts


def compare_scans(before_path, results, summary):
    """Compare this scan against an earlier --json report.

    The question a change to the generator or the resolver has to answer is
    not "how many findings are there" but "did I introduce any". Comparing by
    document and category answers it: a total that happens to match can still
    hide one defect traded for another.
    """
    try:
        with open(before_path, encoding="utf-8") as fh:
            before = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return {"error": f"could not read {before_path}: {exc}", "regressed": True}

    old = {r["file"]: r for r in before.get("results", [])}
    new = {r["file"]: r for r in results}

    changed, gained, resolved = [], [], []
    for name in sorted(set(old) | set(new)):
        old_counts = _counts_by_category(old.get(name, {}).get("issues", []))
        new_counts = _counts_by_category(new.get(name, {}).get("issues", []))
        if old_counts == new_counts:
            continue
        entry = {
            "file": name,
            "old": sum(old_counts.values()),
            "new": sum(new_counts.values()),
            "categories": {
                category: {"old": old_counts.get(category, 0),
                           "new": new_counts.get(category, 0)}
                for category in sorted(set(old_counts) | set(new_counts))
                if old_counts.get(category, 0) != new_counts.get(category, 0)
            },
        }
        changed.append(entry)
        (gained if entry["new"] > entry["old"] else resolved).append(name)

    # Documents only one side scanned are reported rather than counted as a
    # regression: the usual cause is a different --dir, not a new defect.
    only_before = sorted(set(old) - set(new))
    only_after = sorted(set(new) - set(old))

    return {
        "before": before.get("summary", {}),
        "after": summary,
        "changed": changed,
        "documentsThatGained": gained,
        "documentsThatImproved": resolved,
        "onlyInBefore": only_before,
        "onlyInAfter": only_after,
        "regressed": bool(gained),
    }


def print_comparison(delta):
    if delta.get("error"):
        print(delta["error"], file=sys.stderr)
        return
    before, after = delta["before"], delta["after"]
    print(f"before: {before.get('totalFindings', '?')} finding(s) over "
          f"{before.get('documentsWithFindings', '?')} document(s)")
    print(f"after:  {after.get('totalFindings', '?')} finding(s) over "
          f"{after.get('documentsWithFindings', '?')} document(s)")
    if not delta["changed"]:
        print("\nno document changed, in any category")
        return
    print()
    for entry in delta["changed"]:
        marker = "WORSE" if entry["new"] > entry["old"] else "better"
        print(f"  [{marker}] {entry['file']}: {entry['old']} → {entry['new']}")
        for category, counts in entry["categories"].items():
            print(f"      {category}: {counts['old']} → {counts['new']}")
    for name in delta["onlyInBefore"]:
        print(f"  [absent] {name} was scanned before and not now")
    for name in delta["onlyInAfter"]:
        print(f"  [new]    {name} was not scanned before")


def main():
    parser = argparse.ArgumentParser(
        description="Scan every authored document for an issue category",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--dir", action="append", dest="dirs", metavar="DIR",
                        help="Directory to scan, repeatable (default: baselines, practices, deps)")
    parser.add_argument("--category", nargs="+", metavar="CAT",
                        help="Only report these issue categories; prefix match, so "
                             "'pattern' matches every pattern-* category")
    parser.add_argument("--severity", choices=["error", "warning"],
                        help="Only report issues at this severity")
    parser.add_argument("--schema", help="Language schema JSON, to include schema validation")
    parser.add_argument("--validator", action="store_true",
                        help="Run validate-practice-json.py / validate-baseline-json.py "
                             "instead of assess-practice.py. The two check different "
                             "things and only the assessment reached this sweep, so "
                             "error classes the validator owns — an ambiguous pattern "
                             "view, a dangling symbolic reference — were invisible to "
                             "corpus-wide triage")
    parser.add_argument("--no-resolve", action="store_true",
                        help="Skip per-document baseline and dependency resolution. Much "
                             "faster, but cross-reference findings are then suppressed as "
                             "unjudgeable unless --include-unresolved is also given")
    parser.add_argument("--include-unresolved", action="store_true",
                        help="Report cross-reference findings even where the document's "
                             "baseline could not be fully resolved. Expect false positives: "
                             "every reference into an unloaded baseline reads as dangling")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--compare", metavar="BEFORE.json",
                        help="Compare this scan against an earlier --json report and "
                             "report only what changed. Exits 1 if any document gained "
                             "findings, so a change can be shown not to have regressed "
                             "the corpus")
    args = parser.parse_args()

    root = get_project_root()
    dirs = args.dirs or DEFAULT_DIRS

    results = []
    scanned = 0
    unreadable = []
    incomplete_context = []
    schema = args.schema or (str(DEFAULT_SCHEMA) if args.validator else None)
    for path in candidate_documents(root, dirs):
        if args.validator:
            issues, context_complete = validate(path, schema)
        else:
            issues, context_complete = assess(path, args.schema,
                                              resolve=not args.no_resolve)
        scanned += 1
        rel = str(path.relative_to(root))
        if issues is None:
            unreadable.append(rel)
            continue
        matched = []
        for i in issues:
            category = i.get("category", "")
            if args.severity and i.get("severity") != args.severity:
                continue
            if args.category and not any(category.startswith(c) for c in args.category):
                continue
            # Suppress cross-reference findings the resolved context cannot be
            # trusted to judge, rather than reporting a dangling reference that
            # is only dangling because the baseline was not loaded.
            if (not context_complete or args.no_resolve) and not args.include_unresolved:
                if any(category.startswith(c) for c in CROSSREF_CATEGORIES):
                    if rel not in incomplete_context:
                        incomplete_context.append(rel)
                    continue
            matched.append(i)
        if matched:
            results.append({
                "file": rel,
                "issueCount": len(matched),
                "contextComplete": context_complete,
                "issues": matched,
            })

    summary = {
        "documentsScanned": scanned,
        "documentsWithFindings": len(results),
        "totalFindings": sum(r["issueCount"] for r in results),
        "unreadable": unreadable,
        "crossRefSuppressedFor": incomplete_context,
    }

    if args.compare:
        delta = compare_scans(args.compare, results, summary)
        if args.json:
            print(json.dumps(delta, indent=2))
        else:
            print_comparison(delta)
        sys.exit(1 if delta["regressed"] else 0)

    if args.json:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
    else:
        for r in results:
            print(f"=== {r['file']}  ({r['issueCount']})")
            for i in r["issues"]:
                print(f"    [{i.get('severity')}] {i.get('category')}: {i.get('message','')[:150]}")
        print(f"\n--- Scanned {summary['documentsScanned']} document(s); "
              f"{summary['documentsWithFindings']} with findings, "
              f"{summary['totalFindings']} finding(s) total ---")
        for u in unreadable:
            print(f"  could not assess: {u}", file=sys.stderr)

    sys.exit(1 if results else 0)


if __name__ == "__main__":
    main()
