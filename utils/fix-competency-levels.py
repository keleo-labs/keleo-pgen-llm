#!/usr/bin/env python3
"""Fix invalid competency names and level names in practice/method JSON.

Replaces competencyName and competencyLevelName values that don't match the
baseline practice with valid ones, and deduplicates after remapping.

Usage:
    # Show invalid names/levels and suggested replacements (dry run)
    python3 utils/fix-competency-levels.py practice.json baseline.json

    # Apply fixes in-place
    python3 utils/fix-competency-levels.py practice.json baseline.json --fix

    # Apply fixes with explicit mapping overrides
    python3 utils/fix-competency-levels.py practice.json baseline.json --fix \
        --map "Advanced=Masters" --map-name "Market Development=Partner Strategic Alignment"
"""

import argparse
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json

COMMON_LEVEL_MAPPINGS = {
    "Advanced": "Masters",
    "Expert": "Innovating",
    "Intermediate": "Applies",
    "Beginner": "Basic",
    "Novice": "Basic",
    "Practitioner": "Applies",
    "Foundational": "Basic",
    "Proficient": "Masters",
    "Leader": "Innovating",
    "Awareness": "Basic",
    "Working": "Applies",
    "Professional": "Masters",
    "Strategic": "Innovating",
}


def extract_baseline_competencies(baseline_data):
    """Extract valid competency names and level names from baseline."""
    comp_names = set()
    level_names = set()
    by_competency = {}
    for comp in baseline_data.get("competencies", []):
        name = comp.get("name", "")
        comp_names.add(name)
        levels = []
        for level in comp.get("competencyLevels", comp.get("levels", [])):
            lname = level.get("name")
            if lname:
                level_names.add(lname)
                levels.append(lname)
        by_competency[name] = levels
    return comp_names, level_names, by_competency


def fuzzy_match(invalid_name, valid_names, threshold=0.4):
    """Find best fuzzy match for an invalid name among valid names."""
    best_match = None
    best_score = 0.0
    for valid in valid_names:
        score = SequenceMatcher(None, invalid_name.lower(), valid.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = valid
    if best_score >= threshold:
        return best_match
    return None


def find_invalid_refs(data, valid_comp_names, valid_level_names):
    """Find all invalid competency name and level name references."""
    invalid_names = {}
    invalid_levels = {}
    kind = data.get("kind", "practice")
    sources = [("root", data)]
    if kind == "method":
        for i, p in enumerate(data.get("practices", [])):
            sources.append((p.get("name", f"practice[{i}]"), p))

    for source_name, source in sources:
        for act in source.get("activities", []):
            for rc in act.get("requiredCompetencies", []):
                if rc not in valid_comp_names:
                    invalid_names.setdefault(rc, []).append(
                        f"activities['{act.get('name')}'].requiredCompetencies"
                    )
            for rcl in act.get("recommendedCompetencyLevels", []):
                cn = rcl.get("competencyName")
                ln = rcl.get("competencyLevelName")
                if cn and cn not in valid_comp_names:
                    invalid_names.setdefault(cn, []).append(
                        f"activities['{act.get('name')}'].recommendedCompetencyLevels"
                    )
                if ln and ln not in valid_level_names:
                    invalid_levels.setdefault(ln, []).append(
                        f"activities['{act.get('name')}'].recommendedCompetencyLevels"
                    )
        for persona in source.get("personas", []):
            for comp in persona.get("competencies", []):
                cn = comp.get("competencyName")
                ln = comp.get("competencyLevelName")
                if cn and cn not in valid_comp_names:
                    invalid_names.setdefault(cn, []).append(
                        f"personas['{persona.get('name')}'].competencies"
                    )
                if ln and ln not in valid_level_names:
                    invalid_levels.setdefault(ln, []).append(
                        f"personas['{persona.get('name')}'].competencies"
                    )
    return invalid_names, invalid_levels


def build_name_mapping(invalid_names, explicit_maps, valid_comp_names):
    """Build mapping for invalid competency names → valid baseline names."""
    mapping = {}
    for name in invalid_names:
        if name in mapping:
            continue
        if name in explicit_maps:
            mapping[name] = explicit_maps[name]
        else:
            match = fuzzy_match(name, valid_comp_names)
            if match:
                mapping[name] = match
            else:
                mapping[name] = None
    return mapping


def build_level_mapping(invalid_levels, explicit_maps, valid_level_names):
    """Build mapping for invalid level names → valid baseline level names."""
    mapping = {}
    for name in invalid_levels:
        if name in mapping:
            continue
        if name in explicit_maps:
            mapping[name] = explicit_maps[name]
        elif name in COMMON_LEVEL_MAPPINGS and COMMON_LEVEL_MAPPINGS[name] in valid_level_names:
            mapping[name] = COMMON_LEVEL_MAPPINGS[name]
        else:
            match = fuzzy_match(name, valid_level_names)
            if match:
                mapping[name] = match
            else:
                mapping[name] = None
    return mapping


def apply_fixes(data, name_mapping, level_mapping):
    """Apply competency name and level name fixes in place."""
    replaced = {"names": 0, "levels": 0}
    kind = data.get("kind", "practice")
    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        for act in source.get("activities", []):
            rc = act.get("requiredCompetencies", [])
            new_rc = []
            for name in rc:
                mapped = name_mapping.get(name, name) or name
                new_rc.append(mapped)
                if mapped != name:
                    replaced["names"] += 1
            act["requiredCompetencies"] = new_rc

            for rcl in act.get("recommendedCompetencyLevels", []):
                cn = rcl.get("competencyName")
                if cn in name_mapping and name_mapping[cn]:
                    rcl["competencyName"] = name_mapping[cn]
                    replaced["names"] += 1
                ln = rcl.get("competencyLevelName")
                if ln in level_mapping and level_mapping[ln]:
                    rcl["competencyLevelName"] = level_mapping[ln]
                    replaced["levels"] += 1

        for persona in source.get("personas", []):
            for comp in persona.get("competencies", []):
                cn = comp.get("competencyName")
                if cn in name_mapping and name_mapping[cn]:
                    comp["competencyName"] = name_mapping[cn]
                    replaced["names"] += 1
                ln = comp.get("competencyLevelName")
                if ln in level_mapping and level_mapping[ln]:
                    comp["competencyLevelName"] = level_mapping[ln]
                    replaced["levels"] += 1

    return replaced


def deduplicate(data):
    """Remove duplicate competency entries created by many-to-one name mapping."""
    deduped = 0
    kind = data.get("kind", "practice")
    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        for act in source.get("activities", []):
            rc = act.get("requiredCompetencies", [])
            unique_rc = list(dict.fromkeys(rc))
            if len(unique_rc) != len(rc):
                deduped += len(rc) - len(unique_rc)
                act["requiredCompetencies"] = unique_rc

            rcl = act.get("recommendedCompetencyLevels", [])
            seen = set()
            new_rcl = []
            for item in rcl:
                cn = item.get("competencyName")
                if cn not in seen:
                    seen.add(cn)
                    new_rcl.append(item)
            if len(new_rcl) != len(rcl):
                deduped += len(rcl) - len(new_rcl)
                act["recommendedCompetencyLevels"] = new_rcl

        for persona in source.get("personas", []):
            comps = persona.get("competencies", [])
            seen = set()
            new_comps = []
            for c in comps:
                cn = c.get("competencyName")
                if cn not in seen:
                    seen.add(cn)
                    new_comps.append(c)
            if len(new_comps) != len(comps):
                deduped += len(comps) - len(new_comps)
                persona["competencies"] = new_comps

    return deduped


def main():
    parser = argparse.ArgumentParser(
        description="Fix invalid competency names and level names in practice/method JSON"
    )
    parser.add_argument("file", help="Path to practice/method JSON file")
    parser.add_argument("baseline", help="Path to baseline practice JSON")
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply fixes in-place (default: dry run showing what would change)",
    )
    parser.add_argument(
        "--map", action="append", default=[],
        help="Explicit level mapping: 'InvalidLevel=ValidLevel' (repeatable)",
    )
    parser.add_argument(
        "--map-name", action="append", default=[],
        help="Explicit competency name mapping: 'InvalidName=ValidName' (repeatable)",
    )
    parser.add_argument(
        "--partial", action="store_true",
        help="Fix mappable entries and report unmapped ones without failing (exit 0)",
    )
    args = parser.parse_args()

    data = load_json(args.file)
    baseline_data = load_json(args.baseline)

    explicit_level_maps = {}
    for m in args.map:
        if "=" not in m:
            print(json.dumps({"error": f"Invalid map format '{m}', expected 'Old=New'"}))
            sys.exit(1)
        old, new = m.split("=", 1)
        explicit_level_maps[old] = new

    explicit_name_maps = {}
    for m in args.map_name:
        if "=" not in m:
            print(json.dumps({"error": f"Invalid map-name format '{m}', expected 'Old=New'"}))
            sys.exit(1)
        old, new = m.split("=", 1)
        explicit_name_maps[old] = new

    valid_comp_names, valid_level_names, by_competency = extract_baseline_competencies(baseline_data)
    invalid_names, invalid_levels = find_invalid_refs(data, valid_comp_names, valid_level_names)

    if not invalid_names and not invalid_levels:
        output = {
            "file": args.file,
            "valid": True,
            "message": "All competency names and level names are valid",
            "baselineCompetencies": sorted(valid_comp_names),
            "baselineLevels": sorted(valid_level_names),
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    name_mapping = build_name_mapping(invalid_names, explicit_name_maps, valid_comp_names) if invalid_names else {}
    level_mapping = build_level_mapping(invalid_levels, explicit_level_maps, valid_level_names) if invalid_levels else {}

    unmapped_names = {k for k, v in name_mapping.items() if v is None}
    unmapped_levels = {k for k, v in level_mapping.items() if v is None}

    if args.fix:
        if unmapped_names or unmapped_levels:
            if not args.partial:
                hints = []
                if unmapped_names:
                    hints.append(f"Competency names: {sorted(unmapped_names)} — use --map-name 'Invalid=Valid'")
                if unmapped_levels:
                    hints.append(f"Level names: {sorted(unmapped_levels)} — use --map 'Invalid=Valid'")
                print(json.dumps({
                    "error": "Cannot fix: some entries have no mapping",
                    "unmappedNames": sorted(unmapped_names),
                    "unmappedLevels": sorted(unmapped_levels),
                    "hint": hints,
                    "baselineCompetencies": sorted(valid_comp_names),
                    "baselineLevels": sorted(valid_level_names),
                }, indent=2))
                sys.exit(1)

        mappable_names = {k: v for k, v in name_mapping.items() if v is not None}
        mappable_levels = {k: v for k, v in level_mapping.items() if v is not None}
        replaced = apply_fixes(data, mappable_names, mappable_levels)
        deduped = deduplicate(data)

        with open(args.file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        output = {
            "file": args.file,
            "fixed": True,
            "nameReplacements": replaced["names"],
            "levelReplacements": replaced["levels"],
            "deduplicated": deduped,
            "nameMapping": {k: v for k, v in mappable_names.items()},
            "levelMapping": {k: v for k, v in mappable_levels.items()},
        }
        if unmapped_names:
            output["unmappedNames"] = sorted(unmapped_names)
        if unmapped_levels:
            output["unmappedLevels"] = sorted(unmapped_levels)
        print(json.dumps(output, indent=2))
        sys.exit(0)
    else:
        output = {
            "file": args.file,
            "valid": False,
            "invalidNames": {k: {"count": len(v), "suggestedMapping": name_mapping.get(k)} for k, v in invalid_names.items()},
            "invalidLevels": {k: {"count": len(v), "suggestedMapping": level_mapping.get(k)} for k, v in invalid_levels.items()},
            "unmappedNames": sorted(unmapped_names),
            "unmappedLevels": sorted(unmapped_levels),
            "baselineCompetencies": sorted(valid_comp_names),
            "baselineLevels": sorted(valid_level_names),
            "byCompetency": by_competency,
        }
        print(json.dumps(output, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
