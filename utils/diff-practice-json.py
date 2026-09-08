#!/usr/bin/env python3
"""
Compare two practice/baseline JSON files and report structural differences.

Usage:
    # Compare old vs new version
    python3 utils/diff-practice-json.py old.json new.json

    # JSON output
    python3 utils/diff-practice-json.py old.json new.json --json

    # Show only sections with changes
    python3 utils/diff-practice-json.py old.json new.json --changes-only
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


ARRAY_SECTIONS = [
    "alphas", "workProducts", "activities", "patterns", "citations",
    "activitySpaces", "competencies", "narrativeTypes", "assets",
    "personas", "personaGroups", "practiceElementAliases", "narratives",
    "focuses", "references", "outcomes",
]

SCALAR_FIELDS = [
    "name", "description", "kind", "baselinePracticeName", "version",
]


def names_from(items):
    return {item["name"] for item in items if isinstance(item, dict) and "name" in item}


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


def _diff_wp_properties(old, new):
    """Compare partOf/mapsTo properties across work products."""
    changes = []
    old_wps = {wp["name"]: wp for wp in old.get("workProducts", []) if "name" in wp}
    new_wps = {wp["name"]: wp for wp in new.get("workProducts", []) if "name" in wp}
    for wp_name in sorted(set(old_wps) | set(new_wps)):
        old_wp = old_wps.get(wp_name, {})
        new_wp = new_wps.get(wp_name, {})
        for prop in ("partOf", "mapsTo"):
            old_val = old_wp.get(prop)
            new_val = new_wp.get(prop)
            if old_val != new_val:
                changes.append({
                    "workProduct": wp_name,
                    "property": prop,
                    "old": old_val,
                    "new": new_val,
                })
    return changes


def extract_aliases(data):
    aliases = data.get("aliases", data.get("practiceElementAliases", []))
    return [
        {"elementType": a.get("elementType"), "name": a.get("name"), "aliasName": a.get("aliasName")}
        for a in aliases if isinstance(a, dict)
    ]


def diff_files(old, new):
    result = {"sections": {}, "scalars": {}}

    for field in SCALAR_FIELDS:
        old_val = old.get(field)
        new_val = new.get(field)
        if old_val != new_val:
            result["scalars"][field] = {"old": old_val, "new": new_val}

    for section in ARRAY_SECTIONS:
        old_items = old.get(section, [])
        new_items = new.get(section, [])
        old_count = len(old_items)
        new_count = len(new_items)
        delta = new_count - old_count

        old_names = names_from(old_items)
        new_names = names_from(new_items)
        added = sorted(new_names - old_names)
        removed = sorted(old_names - new_names)

        result["sections"][section] = {
            "old": old_count,
            "new": new_count,
            "delta": delta,
            "added": added,
            "removed": removed,
        }

    wp_prop_changes = _diff_wp_properties(old, new)
    if wp_prop_changes:
        result["workProductProperties"] = wp_prop_changes

    old_kw = set(old.get("keywords", []))
    new_kw = set(new.get("keywords", []))
    if old_kw != new_kw:
        result["keywords"] = {
            "added": sorted(new_kw - old_kw),
            "removed": sorted(old_kw - new_kw),
        }

    old_tags = old.get("tags", {})
    new_tags = new.get("tags", {})
    tag_diffs = {}
    for tag_key in set(list(old_tags.keys()) + list(new_tags.keys())):
        ot = set(old_tags.get(tag_key, []))
        nt = set(new_tags.get(tag_key, []))
        if ot != nt:
            tag_diffs[tag_key] = {
                "added": sorted(nt - ot),
                "removed": sorted(ot - nt),
            }
    if tag_diffs:
        result["tags"] = tag_diffs

    old_levels = set(extract_competency_levels(old))
    new_levels = set(extract_competency_levels(new))
    if old_levels != new_levels:
        result["competencyLevels"] = {
            "added": sorted(new_levels - old_levels),
            "removed": sorted(old_levels - new_levels),
        }

    new_aliases = extract_aliases(new)
    if new_aliases:
        result["aliases"] = new_aliases

    return result


def print_report(diff, changes_only=False):
    if diff["scalars"]:
        print("=== SCALAR CHANGES ===")
        for field, vals in diff["scalars"].items():
            old_str = str(vals["old"])[:80] if vals["old"] else "(none)"
            new_str = str(vals["new"])[:80] if vals["new"] else "(none)"
            print(f"  {field}: {old_str}")
            print(f"       → {new_str}")
        print()

    print("=== SECTION COUNTS ===")
    for section, info in diff["sections"].items():
        if changes_only and info["delta"] == 0 and not info["added"] and not info["removed"]:
            continue
        sign = "+" if info["delta"] > 0 else ""
        print(f"  {section}: {info['old']} → {info['new']} ({sign}{info['delta']})")
        if info["added"]:
            for name in info["added"]:
                print(f"    + {name}")
        if info["removed"]:
            for name in info["removed"]:
                print(f"    - {name}")
    print()

    if diff.get("workProductProperties"):
        print("=== WORK PRODUCT PROPERTY CHANGES ===")
        for change in diff["workProductProperties"]:
            old_val = change["old"] or "(none)"
            new_val = change["new"] or "(none)"
            print(f"  {change['workProduct']}.{change['property']}: {old_val} → {new_val}")
        print()

    if diff.get("keywords"):
        print("=== KEYWORD CHANGES ===")
        for kw in diff["keywords"].get("added", []):
            print(f"  + {kw}")
        for kw in diff["keywords"].get("removed", []):
            print(f"  - {kw}")
        print()

    if diff.get("tags"):
        print("=== TAG CHANGES ===")
        for tag_key, changes in diff["tags"].items():
            print(f"  {tag_key}:")
            for t in changes.get("added", []):
                print(f"    + {t}")
            for t in changes.get("removed", []):
                print(f"    - {t}")
        print()

    if diff.get("competencyLevels"):
        print("=== COMPETENCY LEVEL CHANGES ===")
        for cl in diff["competencyLevels"].get("added", []):
            print(f"  + {cl}")
        for cl in diff["competencyLevels"].get("removed", []):
            print(f"  - {cl}")
        print()

    if diff.get("aliases"):
        print("=== ALIASES ===")
        for a in diff["aliases"]:
            etype = a.get("elementType") or "?"
            name = a.get("name") or "?"
            alias = a.get("aliasName") or "?"
            print(f"  {etype}: {name} → {alias}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Compare two practice/baseline JSON files structurally"
    )
    parser.add_argument("old", help="Original/old JSON file")
    parser.add_argument("new", help="Updated/new JSON file")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of human-readable report")
    parser.add_argument("--changes-only", action="store_true",
                        help="Only show sections with changes")
    args = parser.parse_args()

    old_data = load_json(args.old)
    new_data = load_json(args.new)

    diff = diff_files(old_data, new_data)

    if args.json:
        print(json.dumps(diff, indent=2))
    else:
        print_report(diff, args.changes_only)


if __name__ == "__main__":
    main()
