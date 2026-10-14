#!/usr/bin/env python3
"""Run assess-practice across every authored document and report where a defect occurs.

Triage repeatedly asks a question one document cannot answer: a defect has been
found here, where else does it occur? Answering it means running the assessment
over the whole corpus and filtering to one issue category — which is otherwise a
hand-written shell loop every time, and the loop is where the skipping of backup
directories and build artifacts gets forgotten.

Each document is assessed on its own, so assess-practice's per-directory
auto-discovery of _effective-context.json still applies.

Usage:
    # Where else does this defect class occur?
    python3 utils/scan-corpus.py --category outcome-forecast

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


def resolve_context(path):
    """Resolve a document's baseline and dependency practices. Returns CLI args."""
    try:
        out = subprocess.run(
            [sys.executable, str(DISCOVER), "--resolve-from", str(path), "--transitive"],
            capture_output=True, text=True, timeout=120,
        )
        deps = json.loads(out.stdout).get("dependencies", [])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
        return [], False

    args, complete = [], True
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
        args += (["--baseline", dep_path] if dep.get("role") == "baselinePractice"
                 else ["--parent", dep_path])
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
    parser.add_argument("--no-resolve", action="store_true",
                        help="Skip per-document baseline and dependency resolution. Much "
                             "faster, but cross-reference findings are then suppressed as "
                             "unjudgeable unless --include-unresolved is also given")
    parser.add_argument("--include-unresolved", action="store_true",
                        help="Report cross-reference findings even where the document's "
                             "baseline could not be fully resolved. Expect false positives: "
                             "every reference into an unloaded baseline reads as dangling")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    root = get_project_root()
    dirs = args.dirs or DEFAULT_DIRS

    results = []
    scanned = 0
    unreadable = []
    incomplete_context = []
    for path in candidate_documents(root, dirs):
        issues, context_complete = assess(path, args.schema, resolve=not args.no_resolve)
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
