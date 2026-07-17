#!/usr/bin/env python3
"""Compare old and new practice/method JSON files and produce a structured diff report."""

import argparse
import json
import sys


ELEMENT_ARRAYS = ["alphas", "workProducts", "activities", "patterns", "citations", "personas", "assets"]


def count_elements(data):
    counts = {}
    for key in ELEMENT_ARRAYS:
        arr = data.get(key, [])
        counts[key] = len(arr) if isinstance(arr, list) else 0
    return counts


def extract_competency_levels(data):
    levels = set()
    for activity in data.get("activities", []):
        for rcl in activity.get("recommendedCompetencyLevels", []):
            name = rcl.get("competencyLevelName")
            if name:
                levels.add(name)
    for persona in data.get("personas", []):
        for comp in persona.get("competencies", []):
            name = comp.get("competencyLevelName")
            if name:
                levels.add(name)
    return sorted(levels)


def extract_element_names(data, key):
    return sorted(item.get("name", "") for item in data.get(key, []) if isinstance(item, dict))


def extract_aliases(data):
    aliases = data.get("aliases", data.get("practiceElementAliases", []))
    return [
        {"elementType": a.get("elementType"), "name": a.get("name"), "aliasName": a.get("aliasName")}
        for a in aliases
        if isinstance(a, dict)
    ]


def diff_lists(old_list, new_list):
    old_set, new_set = set(old_list), set(new_list)
    return {
        "added": sorted(new_set - old_set),
        "removed": sorted(old_set - new_set),
        "unchanged": sorted(old_set & new_set),
    }


def compare(old_data, new_data):
    old_counts = count_elements(old_data)
    new_counts = count_elements(new_data)

    count_changes = {}
    for key in ELEMENT_ARRAYS:
        old_val = old_counts[key]
        new_val = new_counts[key]
        count_changes[key] = {
            "old": old_val,
            "new": new_val,
            "delta": new_val - old_val,
        }

    element_diffs = {}
    for key in ["alphas", "workProducts", "activities", "patterns", "personas"]:
        old_names = extract_element_names(old_data, key)
        new_names = extract_element_names(new_data, key)
        d = diff_lists(old_names, new_names)
        if d["added"] or d["removed"]:
            element_diffs[key] = d

    old_levels = extract_competency_levels(old_data)
    new_levels = extract_competency_levels(new_data)
    competency_diff = diff_lists(old_levels, new_levels)

    new_aliases = extract_aliases(new_data)

    old_kind = old_data.get("kind")
    new_kind = new_data.get("kind")

    report = {
        "counts": count_changes,
        "elementChanges": element_diffs,
        "competencyLevels": {
            "old": old_levels,
            "new": new_levels,
            "changes": competency_diff,
        },
        "aliases": new_aliases,
        "kind": {"old": old_kind, "new": new_kind, "changed": old_kind != new_kind},
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Compare old and new practice/method JSON files")
    parser.add_argument("old_file", help="Path to old/original JSON file")
    parser.add_argument("new_file", help="Path to new/updated JSON file")
    args = parser.parse_args()

    try:
        with open(args.old_file) as f:
            old_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"Cannot read old file: {e}"}))
        sys.exit(1)

    try:
        with open(args.new_file) as f:
            new_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"Cannot read new file: {e}"}))
        sys.exit(1)

    report = compare(old_data, new_data)
    report["oldFile"] = args.old_file
    report["newFile"] = args.new_file
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
