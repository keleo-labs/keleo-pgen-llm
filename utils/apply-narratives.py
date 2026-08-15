#!/usr/bin/env python3
"""
Apply narrative JSON to matching elements in a practice/baseline JSON file.

Replaces inline scripts that merged narrative data into elements by name.

Usage:
    # Dry run (show what would be applied)
    python3 utils/apply-narratives.py practice.json --map narratives.json

    # Apply narratives and save
    python3 utils/apply-narratives.py practice.json --map narratives.json --fix

Map file formats:

  Flat (keyed by element name):
    {
      "Business Case Document": {"narratives": [<narrative object>]},
      "Stakeholder Register": {"narratives": [<narrative object>]}
    }

  Sectioned (keyed by element section):
    {
      "competency_narratives": {
        "Analysis": [<narrative object>],
        "Leadership": [<narrative object>]
      },
      "activitySpace_narratives": {
        "Assess and Monitor Value": [<narrative object>]
      }
    }
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json

# Top-level arrays whose elements can receive narratives.
NARRATIVE_TARGETS = [
    "alphas", "activities", "workProducts", "competencies",
    "activitySpaces", "focuses", "narrativeTypes", "personas",
]

# Recognised section keys in the sectioned map format, mapped to the
# corresponding top-level JSON array name.
SECTION_TO_ARRAY = {
    "alpha_narratives": "alphas",
    "activity_narratives": "activities",
    "workProduct_narratives": "workProducts",
    "competency_narratives": "competencies",
    "activitySpace_narratives": "activitySpaces",
    "focus_narratives": "focuses",
    "narrativeType_narratives": "narrativeTypes",
    "persona_narratives": "personas",
}

REQUIRED_NARRATIVE_FIELDS = {"name", "description", "narrativeTypeName", "narrativeContexts"}
REQUIRED_CONTEXT_FIELDS = {"seq", "narrativeElementName", "context"}


def _validate_narrative(narr, element_name, warnings):
    """Validate a single narrative object, returning cleaned copy or None."""
    missing = REQUIRED_NARRATIVE_FIELDS - set(narr.keys())
    if missing:
        warnings.append(f"{element_name}: narrative missing {missing}")
        return None

    if "kind" in narr:
        warnings.append(f"{element_name}: stripped invalid kind={narr['kind']}")
        narr = {k: v for k, v in narr.items() if k != "kind"}

    contexts = narr.get("narrativeContexts", [])
    for ctx in contexts:
        ctx_missing = REQUIRED_CONTEXT_FIELDS - set(ctx.keys())
        if ctx_missing:
            warnings.append(
                f"{element_name}/{narr['name']}: context missing {ctx_missing}"
            )

    return narr


def _find_element(data, name):
    """Find an element by name across all narrative-target arrays.

    Returns (element_dict, section_name) or (None, None).
    """
    for section in NARRATIVE_TARGETS:
        for elem in data.get(section, []):
            if elem.get("name") == name:
                return elem, section
    return None, None


def _apply_one(data, element_name, narratives, warnings):
    """Apply a list of narratives to a single element. Returns True if applied."""
    elem, section = _find_element(data, element_name)
    if elem is None:
        warnings.append(f"{element_name}: no matching element found")
        return False

    existing = elem.get("narratives", [])
    existing_names = {n.get("name") for n in existing}
    added = 0

    for narr in narratives:
        cleaned = _validate_narrative(narr, element_name, warnings)
        if cleaned is None:
            continue
        if cleaned.get("name") in existing_names:
            warnings.append(
                f"{element_name}: duplicate narrative '{cleaned['name']}' skipped"
            )
            continue
        existing.append(cleaned)
        existing_names.add(cleaned.get("name"))
        added += 1

    if added > 0:
        elem["narratives"] = existing
    return added > 0


def _is_sectioned(map_data):
    """Detect whether the map uses the sectioned format."""
    return any(key in SECTION_TO_ARRAY for key in map_data)


def apply_narratives(data, map_data):
    """Apply all narratives from map_data to data.

    Returns (applied_count, skipped_count, warnings).
    """
    warnings = []
    applied = 0
    skipped = 0

    if _is_sectioned(map_data):
        for section_key, element_dict in map_data.items():
            if section_key not in SECTION_TO_ARRAY:
                warnings.append(f"Unknown section key: {section_key}")
                continue
            if not isinstance(element_dict, dict):
                warnings.append(f"{section_key}: expected dict, got {type(element_dict).__name__}")
                continue
            for elem_name, narr_list in element_dict.items():
                if not isinstance(narr_list, list):
                    narr_list = [narr_list]
                if _apply_one(data, elem_name, narr_list, warnings):
                    applied += 1
                else:
                    skipped += 1
    else:
        for elem_name, entry in map_data.items():
            if isinstance(entry, dict) and "narratives" in entry:
                narr_list = entry["narratives"]
            elif isinstance(entry, list):
                narr_list = entry
            else:
                warnings.append(
                    f"{elem_name}: expected dict with 'narratives' or array, "
                    f"got {type(entry).__name__}"
                )
                skipped += 1
                continue

            if not isinstance(narr_list, list):
                narr_list = [narr_list]

            if _apply_one(data, elem_name, narr_list, warnings):
                applied += 1
            else:
                skipped += 1

    return applied, skipped, warnings


def main():
    parser = argparse.ArgumentParser(
        description="Apply narrative JSON to matching elements in a practice/baseline JSON file."
    )
    parser.add_argument("target", help="Practice/baseline JSON file to update")
    parser.add_argument(
        "--map", required=True, dest="map_file",
        help="JSON file mapping element names to narratives",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Write changes to the file (default is dry run)",
    )
    args = parser.parse_args()

    target_path = Path(args.target)
    if not target_path.exists():
        print(json.dumps({"error": f"File not found: {args.target}"}))
        sys.exit(1)

    data = load_json(args.target)
    map_data = load_json(args.map_file)

    if not isinstance(map_data, dict):
        print(json.dumps({"error": "Map file must contain a JSON object"}))
        sys.exit(1)

    applied, skipped, warnings = apply_narratives(data, map_data)

    report = {
        "file": str(target_path),
        "applied": applied,
        "skipped": skipped,
        "warnings": warnings,
        "dryRun": not args.fix,
    }

    if args.fix:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
