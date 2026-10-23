#!/usr/bin/env python3
"""Find where a schema construct is actually declared across the corpus.

`detect-schema-gaps.py` answers the negative question — which constructs a
document is missing. This answers the positive one: a construct exists in the
schema, who uses it, and what does their use look like? That question comes up
whenever a newly-surfaced property needs a worked example, whenever a prompt
change needs to know how much of the corpus it affects, and whenever triage
asks whether a defect pattern is isolated or systemic.

Each hit is reported with a breadcrumb built from the `name` of every element
above it, so `patterns[Opportunity Cycle].patternViews[Qualify]` says where the
declaration sits without anyone opening the file.

Usage:
    python3 utils/find-construct.py loopsBackTo
    python3 utils/find-construct.py mapsTo contributesTo --dir practices
    python3 utils/find-construct.py loopsBackTo --values --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, get_project_root

DEFAULT_DIRS = ["baselines", "practices", "deps"]


def candidate_documents(root, dirs):
    """Authored documents only — no backups, no build artifacts.

    Mirrors scan-corpus.py: a sweep that counts backup copies reports the same
    declaration five times and makes the corpus look busier than it is.
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
                if ".changerequest" in path.name:
                    continue
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                yield path


def walk(node, targets, trail, hits):
    """Collect every occurrence of a target key, with its breadcrumb."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in targets:
                hits.append({"path": ".".join(trail + [key]), "property": key,
                             "value": value})
            walk(value, targets, trail + [key], hits)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            label = item.get("name") if isinstance(item, dict) else None
            step = f"[{label}]" if label else f"[{index}]"
            # Attach the index to the key already on the trail rather than
            # adding a segment, so the path reads patterns[Name] not
            # patterns.[Name].
            inner = trail[:-1] + [trail[-1] + step] if trail else [step]
            walk(item, targets, inner, hits)


def summarise(value, full=False, width=160):
    """One-line rendering of a found value."""
    text = json.dumps(value, ensure_ascii=False)
    if full or len(text) <= width:
        return text
    return text[: width - 1] + "…"


def main():
    parser = argparse.ArgumentParser(
        description="Find where a schema construct is declared across the corpus")
    parser.add_argument("property", nargs="+",
                        help="Property name to find, repeatable")
    parser.add_argument("--dir", dest="dirs", action="append",
                        help=f"Directory to scan, repeatable (default: {', '.join(DEFAULT_DIRS)})")
    parser.add_argument("--values", action="store_true",
                        help="Print each value in full rather than truncated")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    targets = set(args.property)
    root = get_project_root()
    results = []

    for path in candidate_documents(root, args.dirs or DEFAULT_DIRS):
        try:
            data = load_json(path, exit_on_error=False)
        except ValueError:
            # An unreadable document is not this tool's business to report —
            # scan-corpus and the validators own that.
            continue
        if not isinstance(data, dict):
            continue
        hits = []
        walk(data, targets, [], hits)
        if hits:
            results.append({
                "document": str(path.relative_to(root)),
                "name": data.get("name"),
                "kind": data.get("kind"),
                "hits": hits,
            })

    total = sum(len(entry["hits"]) for entry in results)

    if args.json:
        print(json.dumps({"properties": sorted(targets), "documentCount": len(results),
                          "hitCount": total, "documents": results}, indent=2))
    else:
        for entry in results:
            print(f"\n{entry['document']}  ({entry['name']})")
            for hit in entry["hits"]:
                print(f"  {hit['path']}")
                print(f"    {summarise(hit['value'], args.values)}")
        print(f"\n{total} declaration(s) of {', '.join(sorted(targets))} "
              f"across {len(results)} document(s)")

    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
