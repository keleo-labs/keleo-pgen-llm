#!/usr/bin/env python3
"""Add citations to a practice/baseline JSON and link them to element narratives."""

import argparse
import json
import sys
from pathlib import Path


def collect_narratives(elements, element_type):
    """Collect all narrative objects from a list of elements."""
    results = []
    for elem in elements:
        for narr in elem.get("narratives", []):
            results.append((element_type, elem.get("name", "?"), narr))
    return results


def add_citation_names(narratives_list, new_names):
    """Add citation names to narrative objects, deduplicating."""
    updated_count = 0
    for _etype, _ename, narr in narratives_list:
        existing = narr.get("citationNames", [])
        before = len(existing)
        merged = list(dict.fromkeys(existing + new_names))
        narr["citationNames"] = merged
        if len(merged) > before:
            updated_count += 1
    return updated_count


def main():
    parser = argparse.ArgumentParser(
        description="Add citations to a practice JSON and link to element narratives."
    )
    parser.add_argument("target", help="Practice/baseline JSON file to update")
    parser.add_argument(
        "--citations-file",
        required=True,
        help="JSON file containing an array of citation objects to add",
    )
    parser.add_argument(
        "--link-to",
        nargs="+",
        choices=["alphas", "activities", "workProducts", "practice", "all"],
        default=["alphas"],
        help="Which element narratives to add citationNames to (default: alphas)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing",
    )
    args = parser.parse_args()

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"Error: {target_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(target_path) as f:
        data = json.load(f)

    with open(args.citations_file) as f:
        new_citations = json.load(f)

    if not isinstance(new_citations, list):
        print("Error: citations file must contain a JSON array", file=sys.stderr)
        sys.exit(1)

    existing_names = {c["name"] for c in data.get("citations", [])}
    added = []
    skipped = []

    for cit in new_citations:
        if not all(k in cit for k in ("name", "description", "authors", "date", "source")):
            print(f"Warning: citation missing required fields: {cit.get('name', '?')}", file=sys.stderr)
            continue
        if cit["name"] in existing_names:
            skipped.append(cit["name"])
            continue
        if "citations" not in data:
            data["citations"] = []
        data["citations"].append(cit)
        existing_names.add(cit["name"])
        added.append(cit["name"])

    targets = set(args.link_to)
    if "all" in targets:
        targets = {"alphas", "activities", "workProducts", "practice"}

    new_names = [c["name"] for c in new_citations if c["name"] in existing_names]

    narratives_to_update = []

    if "practice" in targets:
        for narr in data.get("narratives", []):
            narratives_to_update.append(("practice", data.get("name", "?"), narr))

    if "alphas" in targets:
        narratives_to_update.extend(
            collect_narratives(data.get("alphas", []), "alpha")
        )

    if "activities" in targets:
        narratives_to_update.extend(
            collect_narratives(data.get("activities", []), "activity")
        )

    if "workProducts" in targets:
        narratives_to_update.extend(
            collect_narratives(data.get("workProducts", []), "workProduct")
        )

    linked_count = add_citation_names(narratives_to_update, new_names)

    report = {
        "target": str(target_path),
        "citationsAdded": len(added),
        "citationsSkipped": len(skipped),
        "narrativesUpdated": linked_count,
        "narrativesScanned": len(narratives_to_update),
        "addedNames": added,
        "skippedNames": skipped,
        "dryRun": args.dry_run,
    }

    if args.dry_run:
        print(json.dumps(report, indent=2))
    else:
        with open(target_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
