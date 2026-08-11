#!/usr/bin/env python3
"""Fix invalid competency level names in practice/method JSON.

Replaces competencyLevelName values that don't match the baseline practice's
CompetencyLevel.name values with valid ones.

Usage:
    # Show invalid levels and suggested replacements (dry run)
    python3 utils/fix-competency-levels.py practice.json baseline.json

    # Apply fixes in-place
    python3 utils/fix-competency-levels.py practice.json baseline.json --fix

    # Apply fixes with explicit mapping overrides
    python3 utils/fix-competency-levels.py practice.json baseline.json --fix \
        --map "Advanced=Masters" --map "Expert=Innovating"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json

COMMON_MAPPINGS = {
    "Advanced": "Masters",
    "Expert": "Innovating",
    "Intermediate": "Applies",
    "Beginner": "Basic",
    "Novice": "Basic",
}


def extract_baseline_levels(baseline_data):
    levels = set()
    by_competency = {}
    for comp in baseline_data.get("competencies", []):
        comp_name = comp.get("name", "")
        comp_levels = []
        for level in comp.get("competencyLevels", comp.get("levels", [])):
            name = level.get("name")
            if name:
                levels.add(name)
                comp_levels.append(name)
        by_competency[comp_name] = comp_levels
    return levels, by_competency


def find_invalid_levels(data, valid_levels):
    invalid = []
    kind = data.get("kind", "practice")
    sources = [("root", data)]
    if kind == "method":
        for i, p in enumerate(data.get("practices", [])):
            sources.append((p.get("name", f"practice[{i}]"), p))

    for source_name, source in sources:
        for act in source.get("activities", []):
            for rcl in act.get("recommendedCompetencyLevels", []):
                name = rcl.get("competencyLevelName")
                if name and name not in valid_levels:
                    invalid.append({
                        "location": f"activities['{act.get('name')}'].recommendedCompetencyLevels",
                        "source": source_name,
                        "competencyName": rcl.get("competencyName"),
                        "invalidLevel": name,
                    })
        for persona in source.get("personas", []):
            for comp in persona.get("competencies", []):
                name = comp.get("competencyLevelName")
                if name and name not in valid_levels:
                    invalid.append({
                        "location": f"personas['{persona.get('name')}'].competencies",
                        "source": source_name,
                        "competencyName": comp.get("competencyName"),
                        "invalidLevel": name,
                    })
    return invalid


def build_mapping(invalid_entries, explicit_maps, valid_levels):
    mapping = {}
    for entry in invalid_entries:
        name = entry["invalidLevel"]
        if name in mapping:
            continue
        if name in explicit_maps:
            mapping[name] = explicit_maps[name]
        elif name in COMMON_MAPPINGS and COMMON_MAPPINGS[name] in valid_levels:
            mapping[name] = COMMON_MAPPINGS[name]
        else:
            mapping[name] = None
    return mapping


def apply_fixes(data, mapping):
    replaced = 0
    kind = data.get("kind", "practice")
    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        for act in source.get("activities", []):
            for rcl in act.get("recommendedCompetencyLevels", []):
                name = rcl.get("competencyLevelName")
                if name in mapping and mapping[name] is not None:
                    rcl["competencyLevelName"] = mapping[name]
                    replaced += 1
        for persona in source.get("personas", []):
            for comp in persona.get("competencies", []):
                name = comp.get("competencyLevelName")
                if name in mapping and mapping[name] is not None:
                    comp["competencyLevelName"] = mapping[name]
                    replaced += 1
    return replaced


def main():
    parser = argparse.ArgumentParser(
        description="Fix invalid competency level names in practice/method JSON"
    )
    parser.add_argument("file", help="Path to practice/method JSON file")
    parser.add_argument("baseline", help="Path to baseline practice JSON")
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply fixes in-place (default: dry run showing what would change)",
    )
    parser.add_argument(
        "--map", action="append", default=[],
        help="Explicit mapping override: 'InvalidName=ValidName' (repeatable)",
    )
    args = parser.parse_args()

    data = load_json(args.file)
    baseline_data = load_json(args.baseline)

    explicit_maps = {}
    for m in args.map:
        if "=" not in m:
            print(json.dumps({"error": f"Invalid map format '{m}', expected 'Old=New'"}))
            sys.exit(1)
        old, new = m.split("=", 1)
        explicit_maps[old] = new

    valid_levels, by_competency = extract_baseline_levels(baseline_data)
    invalid_entries = find_invalid_levels(data, valid_levels)

    if not invalid_entries:
        output = {
            "file": args.file,
            "valid": True,
            "message": "All competency level names are valid",
            "baselineLevels": sorted(valid_levels),
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    mapping = build_mapping(invalid_entries, explicit_maps, valid_levels)
    unmapped = {k: v for k, v in mapping.items() if v is None}

    if args.fix:
        if unmapped:
            print(json.dumps({
                "error": "Cannot fix: some invalid levels have no mapping",
                "unmapped": list(unmapped.keys()),
                "hint": "Provide explicit mappings with --map 'InvalidName=ValidName'",
                "baselineLevels": sorted(valid_levels),
            }, indent=2))
            sys.exit(1)

        replaced = apply_fixes(data, mapping)
        with open(args.file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        output = {
            "file": args.file,
            "fixed": True,
            "replacements": replaced,
            "mapping": mapping,
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)
    else:
        output = {
            "file": args.file,
            "valid": False,
            "invalidCount": len(invalid_entries),
            "invalidEntries": invalid_entries,
            "suggestedMapping": mapping,
            "unmapped": list(unmapped.keys()) if unmapped else [],
            "baselineLevels": sorted(valid_levels),
            "byCompetency": by_competency,
        }
        print(json.dumps(output, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
