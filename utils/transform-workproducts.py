#!/usr/bin/env python3
"""Batch work product transformation: rename, convert relationship types, align LODs.

Applies a spec of transformations to a practice JSON, updating all cross-references.

Usage:
    # Dry-run with inline spec
    python3 utils/transform-workproducts.py practice.json --spec '[{"workProduct":"Old","rename":"New","setMapsTo":"Parent","lodMap":{"S1":"T1"}}]'

    # Apply from spec file
    python3 utils/transform-workproducts.py practice.json --spec-file transforms.json --fix

    # Show what would change
    python3 utils/transform-workproducts.py practice.json --spec-file transforms.json

Spec format (JSON array of objects):
    [
        {
            "workProduct": "Current WP Name",         # required: which WP to transform
            "rename": "New WP Name",                   # optional: rename the work product
            "setMapsTo": "Parent WP",                  # optional: set mapsTo (removes partOf)
            "setPartOf": "Parent WP",                  # optional: set partOf (removes mapsTo)
            "lodMap": {"OldLOD": "NewLOD"},            # optional: rename LODs (1:1)
            "addLods": [{"name":"L","description":"D","seq":N,"checklist":[]}]  # optional: new LODs
        }
    ]

Transformations are applied in spec order. Cross-references updated:
    - WP name in: activities.worksOn, references.evidenceBy, patterns.workProductLevels,
      background.workProductLevels, other WPs' partOf/mapsTo targets, practiceElementAliases
    - LOD names in: activities.worksOn.levelOfDetailName, references.evidenceBy.levelOfDetailName,
      patterns.workProductLevels.levelOfDetailName, background.workProductLevels
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def _update_wp_lod_refs(practice, wp_name, new_wp_name, lod_map, changes):
    """Update all cross-references to a work product name and/or its LOD names.

    wp_name: the current (possibly already-renamed) name to match
    new_wp_name: new name to set (can equal wp_name if only LODs changed)
    lod_map: dict of old LOD name → new LOD name
    """
    ref_count = 0

    def _fix_entry(entry, label):
        nonlocal ref_count
        changed = False
        if entry.get("workProductName") == wp_name:
            if new_wp_name and new_wp_name != wp_name:
                entry["workProductName"] = new_wp_name
                changed = True
            lod_field = "levelOfDetailName"
            if entry.get(lod_field) in lod_map:
                entry[lod_field] = lod_map[entry[lod_field]]
                changed = True
        if changed:
            ref_count += 1

    # 1. activities[].worksOn[]
    for act in practice.get("activities", []):
        for wo in act.get("worksOn", []):
            if isinstance(wo, dict):
                _fix_entry(wo, f"activity:{act.get('name','?')}.worksOn")

    # 2. references[].evidenceBy[]
    for ref in practice.get("references", []):
        for eb in ref.get("evidenceBy", []):
            if isinstance(eb, dict):
                _fix_entry(eb, f"reference:{ref.get('name','?')}.evidenceBy")

    # 3. patterns[].patternViews[].workProductLevels[]
    for pat in practice.get("patterns", []):
        for view in pat.get("patternViews", []):
            for wpl in view.get("workProductLevels", []):
                if isinstance(wpl, dict):
                    _fix_entry(wpl, f"pattern:{pat.get('name','?')}.workProductLevels")

    # 4. alphas[].states[].background.workProductLevels[]
    for alpha in practice.get("alphas", []):
        for state in alpha.get("states", []):
            bg = state.get("background", {})
            for wpl in bg.get("workProductLevels", []):
                if isinstance(wpl, dict):
                    _fix_entry(wpl, f"alpha:{alpha.get('name','?')}.state:{state.get('name','?')}.bg")

    # 5. activities[].background.workProductLevels[]
    for act in practice.get("activities", []):
        bg = act.get("background", {})
        for wpl in bg.get("workProductLevels", []):
            if isinstance(wpl, dict):
                _fix_entry(wpl, f"activity:{act.get('name','?')}.bg")

    # 6. practiceElementAliases[]
    for alias in practice.get("practiceElementAliases", []):
        if alias.get("practiceElementName") == wp_name:
            if new_wp_name and new_wp_name != wp_name:
                alias["practiceElementName"] = new_wp_name
                ref_count += 1
        if alias.get("name") == wp_name:
            if new_wp_name and new_wp_name != wp_name:
                alias["name"] = new_wp_name
                ref_count += 1

    # 7. Other WPs' partOf/mapsTo targets referencing this WP
    for wp in practice.get("workProducts", []):
        if wp.get("partOf") == wp_name and new_wp_name and new_wp_name != wp_name:
            wp["partOf"] = new_wp_name
            ref_count += 1
        if wp.get("mapsTo") == wp_name and new_wp_name and new_wp_name != wp_name:
            wp["mapsTo"] = new_wp_name
            ref_count += 1

    return ref_count


def transform_workproduct(practice, spec):
    """Apply a single work product transformation. Returns (changes, error)."""
    wp_name = spec["workProduct"]
    new_name = spec.get("rename")
    set_mapsto = spec.get("setMapsTo")
    set_partof = spec.get("setPartOf")
    lod_map = spec.get("lodMap", {})
    add_lods = spec.get("addLods", [])
    changes = []

    wp = None
    for w in practice.get("workProducts", []):
        if w["name"] == wp_name:
            wp = w
            break

    if not wp:
        return [], f"Work product '{wp_name}' not found"

    # 0. Add new LODs
    if add_lods:
        for new_lod in add_lods:
            wp.setdefault("levelsOfDetail", []).append(new_lod)
            changes.append(f"  addLod: {new_lod['name']} (seq={new_lod.get('seq', '?')})")
        wp["levelsOfDetail"].sort(key=lambda l: l.get("seq", 0))

    # 1. Change relationship type
    if set_mapsto:
        old_partof = wp.pop("partOf", None)
        old_mapsto = wp.pop("mapsTo", None)
        wp["mapsTo"] = set_mapsto
        if old_partof:
            changes.append(f"  relationship: partOf:{old_partof} → mapsTo:{set_mapsto}")
        elif old_mapsto and old_mapsto != set_mapsto:
            changes.append(f"  relationship: mapsTo:{old_mapsto} → mapsTo:{set_mapsto}")
        else:
            changes.append(f"  relationship: set mapsTo:{set_mapsto}")

    if set_partof:
        old_mapsto = wp.pop("mapsTo", None)
        old_partof = wp.pop("partOf", None)
        wp["partOf"] = set_partof
        if old_mapsto:
            changes.append(f"  relationship: mapsTo:{old_mapsto} → partOf:{set_partof}")
        elif old_partof and old_partof != set_partof:
            changes.append(f"  relationship: partOf:{old_partof} → partOf:{set_partof}")
        else:
            changes.append(f"  relationship: set partOf:{set_partof}")

    # 2. Rename LODs within this WP
    if lod_map:
        matched_lods = set()
        for lod in wp.get("levelsOfDetail", []):
            old_lod_name = lod["name"]
            if old_lod_name in lod_map:
                lod["name"] = lod_map[old_lod_name]
                matched_lods.add(old_lod_name)
                changes.append(f"  lod: {old_lod_name} → {lod_map[old_lod_name]}")

        unmatched = set(lod_map.keys()) - matched_lods
        for um in sorted(unmatched):
            changes.append(f"  WARNING: lodMap key '{um}' not found in levelsOfDetail")

    # 3. Update all cross-references (LOD names and optionally WP name)
    effective_new_name = new_name if new_name and new_name != wp_name else None
    ref_count = _update_wp_lod_refs(
        practice, wp_name, effective_new_name or wp_name, lod_map, changes
    )

    # 4. Rename the WP itself (after cross-refs are updated)
    if new_name and new_name != wp_name:
        wp["name"] = new_name
        changes.append(f"  rename: {wp_name} → {new_name}")

    if ref_count:
        changes.append(f"  references updated: {ref_count}")

    return changes, None


def main():
    parser = argparse.ArgumentParser(
        description="Batch work product transformation: rename, convert relationships, align LODs"
    )
    parser.add_argument("file", help="Practice JSON file to transform")
    parser.add_argument("--fix", action="store_true", help="Apply changes in-place (default: dry-run)")

    spec_group = parser.add_mutually_exclusive_group(required=True)
    spec_group.add_argument("--spec", help="Inline JSON spec (array of transformation objects)")
    spec_group.add_argument("--spec-file", help="Path to JSON spec file")

    args = parser.parse_args()

    practice = load_json(args.file)

    if args.spec_file:
        spec_list = load_json(args.spec_file)
    else:
        spec_list = json.loads(args.spec)

    if not isinstance(spec_list, list):
        spec_list = [spec_list]

    all_changes = []
    errors = []

    for spec in spec_list:
        wp_name = spec.get("workProduct", "?")
        spec_changes, err = transform_workproduct(practice, spec)
        if err:
            errors.append(f"{wp_name}: {err}")
        else:
            all_changes.append({"workProduct": wp_name, "changes": spec_changes})

    if args.fix and not errors:
        with open(args.file, "w", encoding="utf-8") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")

    result = {
        "file": args.file,
        "dryRun": not args.fix,
        "transformations": len(all_changes),
        "errors": errors,
    }

    print(json.dumps(result, indent=2))
    for entry in all_changes:
        print(f"\n{entry['workProduct']}:")
        for c in entry["changes"]:
            print(c)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
