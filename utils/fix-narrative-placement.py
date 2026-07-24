#!/usr/bin/env python3
"""Move element-specific narratives from top-level narratives[] to their elements.

Narratives that belong to a specific alpha, activitySpace, or competency should
be embedded on that element's `narratives` property, not in the top-level array.
Only baseline/practice-level narratives remain at the top level.

Matching logic:
- Checks if narrative name contains an element name (case-insensitive)
- Falls back to description matching ("for the X alpha/competency/activity space")

Usage:
    # Dry run — show what would be moved
    python3 utils/fix-narrative-placement.py <file.json>

    # Apply fixes in-place
    python3 utils/fix-narrative-placement.py <file.json> --fix

Output: JSON report to stdout. Exit 0 on success, 1 on error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_element_index(data):
    """Build a map from element name (lowercased) to (collection_key, index)."""
    index = {}
    for collection_key in ("alphas", "activitySpaces", "competencies"):
        for i, element in enumerate(data.get(collection_key, [])):
            name = element.get("name", "")
            index[name.lower()] = (collection_key, i, name)
    return index


def find_matching_element(narrative, element_index):
    """Find which element a narrative belongs to, if any.

    Prefers longer element name matches to avoid "Business Model" matching
    before "Business Model and Service Design".
    """
    narr_name = narrative.get("name", "")
    narr_desc = narrative.get("description", "")
    narr_name_lower = narr_name.lower()

    candidates = sorted(element_index.items(), key=lambda x: len(x[0]), reverse=True)

    for elem_name_lower, (coll_key, idx, elem_name) in candidates:
        if elem_name_lower in narr_name_lower:
            return coll_key, idx, elem_name

    desc_lower = narr_desc.lower()
    for elem_name_lower, (coll_key, idx, elem_name) in candidates:
        if elem_name_lower in desc_lower:
            return coll_key, idx, elem_name

    return None


def fix_narrative_placement(data, dry_run=True):
    """Move element-specific narratives to their elements."""
    element_index = build_element_index(data)
    top_level_narratives = data.get("narratives", [])

    moves = []
    keep_at_top = []

    for i, narrative in enumerate(top_level_narratives):
        match = find_matching_element(narrative, element_index)
        if match:
            coll_key, elem_idx, elem_name = match
            moves.append({
                "narrativeIndex": i,
                "narrativeName": narrative.get("name", f"<unnamed-{i}>"),
                "targetCollection": coll_key,
                "targetIndex": elem_idx,
                "targetElement": elem_name,
            })
        else:
            keep_at_top.append(narrative)

    if not dry_run and moves:
        for move in moves:
            narrative = top_level_narratives[move["narrativeIndex"]]
            coll_key = move["targetCollection"]
            elem_idx = move["targetIndex"]
            element = data[coll_key][elem_idx]
            if "narratives" not in element:
                element["narratives"] = []
            element["narratives"].append(narrative)

        data["narratives"] = keep_at_top

    return {
        "totalNarratives": len(top_level_narratives),
        "moved": len(moves),
        "keptAtTopLevel": len(keep_at_top),
        "moves": moves,
        "dryRun": dry_run,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Move element-specific narratives to their elements"
    )
    parser.add_argument("file", help="Practice/baseline JSON file")
    parser.add_argument(
        "--fix", action="store_true", help="Apply fixes in-place (default: dry run)"
    )
    args = parser.parse_args()

    path = Path(args.file)
    data = load_json(path)

    result = fix_narrative_placement(data, dry_run=not args.fix)

    if args.fix and result["moved"] > 0:
        save_json_file(path, data)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
