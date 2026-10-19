#!/usr/bin/env python3
"""Report which root $defs type the schema's dispatcher selects for a document.

The schema's root is a chain of if/then/else branches that routes on the
*presence of properties*, not on `kind`. A document whose property set and
whose `kind` disagree is therefore validated against the wrong shape and
reports `valid: true` while every constraint of its declared type goes
unenforced. The known case is a PracticeBaseline that declares the singular
`baselinePracticeName` instead of the array `baselinePracticeNames`: it routes
to #/$defs/Practice whatever its `kind` says.

This tool resolves the dispatcher the same way a validator does, reports the
branch each document lands on, and flags any document where that branch
disagrees with its declared `kind`.

    python3 utils/check-root-dispatch.py <file>.json [...] [--schema S] [--json]
    python3 utils/check-root-dispatch.py --dir baselines/ --dir practices/

Exits 1 when any document is misrouted.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils._shared import load_json  # noqa: E402

DEFAULT_SCHEMA = Path(__file__).resolve().parent.parent / "deps" / "language.schema.json"

# Root `kind` values and the $defs branch each one must route to.
KIND_TO_DEF = {
    "practiceBaseline": "PracticeBaseline",
    "practice": "Practice",
    "method": "Method",
    "project": "Project",
    "changeRequest": "ChangeRequest",
    "changeSet": "ChangeSet",
    "integrationMapping": "IntegrationMapping",
}

SKIP_DIR_MARKERS = ("backup-", "_effective-context", "node_modules", ".git")


def _condition_matches(document, condition):
    """Evaluate the subset of JSON Schema the root dispatcher actually uses."""
    for prop in condition.get("required", []):
        if prop not in document:
            return False
    any_of = condition.get("anyOf")
    if any_of and not any(_condition_matches(document, branch) for branch in any_of):
        return False
    return True


def resolve_branch(document, schema):
    """Walk the root if/then/else chain and return the selected $defs name.

    Returns (def_name, trail) where trail lists the properties that decided it.
    """
    node = schema
    trail = []
    while True:
        if "$ref" in node:
            return node["$ref"].rsplit("/", 1)[-1], trail
        if "if" not in node:
            return None, trail
        condition = node["if"]
        if _condition_matches(document, condition):
            required = condition.get("required", [])
            options = [r for branch in condition.get("anyOf", []) for r in branch.get("required", [])]
            trail.append("+" + ",".join(required or options))
            node = node.get("then", {})
        else:
            node = node.get("else", {})


def check_document(path, schema):
    try:
        document = load_json(path, exit_on_error=False)
    except (ValueError, OSError):
        document = None
    if not isinstance(document, dict):
        return {"file": str(path), "status": "unreadable"}
    kind = document.get("kind")
    branch, trail = resolve_branch(document, schema)
    expected = KIND_TO_DEF.get(kind)
    if expected is None:
        status = "unknown-kind"
    elif expected == branch:
        status = "ok"
    else:
        status = "misrouted"
    return {
        "file": str(path),
        "kind": kind,
        "routedTo": branch,
        "expected": expected,
        "decidedBy": trail,
        "status": status,
    }


def collect_paths(files, dirs):
    paths = [Path(f) for f in files]
    for directory in dirs:
        for path in sorted(Path(directory).rglob("*.json")):
            text = str(path)
            if any(marker in text for marker in SKIP_DIR_MARKERS):
                continue
            if path.name.startswith("_"):
                continue
            paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="Document JSON files to check")
    parser.add_argument("--dir", action="append", default=[], help="Sweep a directory tree (repeatable)")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Path to language.schema.json")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON")
    args = parser.parse_args()

    paths = collect_paths(args.files, args.dir)
    if not paths:
        parser.error("no documents given — pass files or --dir")

    schema = load_json(args.schema)
    results = [check_document(path, schema) for path in paths]
    misrouted = [r for r in results if r["status"] == "misrouted"]

    if args.as_json:
        print(json.dumps({"results": results, "misroutedCount": len(misrouted)}, indent=2))
    else:
        for result in results:
            marker = {"ok": "OK", "misrouted": "MISROUTED", "unknown-kind": "SKIP", "unreadable": "UNREADABLE"}[
                result["status"]
            ]
            print(f"{marker:<10} {result['file']}")
            if result["status"] != "unreadable":
                decided = " ".join(result["decidedBy"]) or "(no discriminating property)"
                print(f"           kind={result['kind']} routed to #/$defs/{result['routedTo']} via {decided}")
                if result["status"] == "misrouted":
                    print(f"           expected #/$defs/{result['expected']}")
        print(f"\n{len(results)} document(s), {len(misrouted)} misrouted")

    return 1 if misrouted else 0


if __name__ == "__main__":
    sys.exit(main())
