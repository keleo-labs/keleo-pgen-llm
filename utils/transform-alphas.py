#!/usr/bin/env python3
"""Batch alpha transformation: rename, convert relationship types, align states.

Applies a spec of transformations to a practice JSON, updating all cross-references.

Usage:
    # Dry-run with inline spec
    python3 utils/transform-alphas.py practice.json --spec '[{"alpha":"Old","rename":"New","setMapsTo":"Parent","stateMap":{"S1":"T1"}}]'

    # Apply from spec file
    python3 utils/transform-alphas.py practice.json --spec-file transforms.json --fix

    # Show what would change
    python3 utils/transform-alphas.py practice.json --spec-file transforms.json

Spec format (JSON array of objects):
    [
        {
            "alpha": "Current Alpha Name",        # required: which alpha to transform
            "rename": "New Alpha Name",            # optional: rename the alpha
            "setMapsTo": "Parent Alpha",           # optional: set mapsTo (removes contributesTo)
            "setContributesTo": "Parent Alpha",    # optional: set contributesTo (removes mapsTo)
            "stateMap": {"OldState": "NewState"},  # optional: rename states (1:1 or many:1 merge)
            "addStates": [{"name":"S","description":"D","seq":N,"checklist":[]}]  # optional: new states
        }
    ]

When stateMap maps multiple old states to the same new state, their checklists and
backgrounds are merged. Use addStates to insert states that have no existing source.

Transformations are applied in spec order. Cross-references updated:
    - Alpha name in: relatesTo, activities.contributesTo, workProducts.levelsOfDetail.contributesTo,
      patterns.patternViews.alphaStates, other alphas' contributesTo/mapsTo targets,
      background.alphaStates, practiceElementAliases
    - State names in: contributesToState, stateName, alphaStateName in all reference locations,
      background.alphaStates
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def _deep_rename_strings(obj, old_val, new_val):
    """Recursively replace string values (not keys) throughout a JSON structure."""
    count = 0
    if isinstance(obj, dict):
        for k in obj:
            if isinstance(obj[k], str) and obj[k] == old_val:
                obj[k] = new_val
                count += 1
            else:
                count += _deep_rename_strings(obj[k], old_val, new_val)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and item == old_val:
                obj[i] = new_val
                count += 1
            else:
                count += _deep_rename_strings(item, old_val, new_val)
    return count


def transform_alpha(practice, spec):
    """Apply a single alpha transformation. Returns (changes, error)."""
    alpha_name = spec["alpha"]
    new_name = spec.get("rename")
    set_mapsto = spec.get("setMapsTo")
    set_contributesto = spec.get("setContributesTo")
    state_map = spec.get("stateMap", {})
    add_states = spec.get("addStates", [])
    changes = []

    alpha = None
    for a in practice.get("alphas", []):
        if a["name"] == alpha_name:
            alpha = a
            break

    if not alpha:
        return [], f"Alpha '{alpha_name}' not found"

    # 0. Handle state merging (many:1 in stateMap) and new states
    if state_map:
        # Detect many:1 merges (multiple old states → same new state)
        merge_groups = {}
        for old_s, new_s in state_map.items():
            merge_groups.setdefault(new_s, []).append(old_s)

        for new_state_name, old_names in merge_groups.items():
            if len(old_names) <= 1:
                continue
            # Merge: keep first state, append checklists/backgrounds from others, remove others
            states = alpha.get("states", [])
            primary = None
            merge_sources = []
            for s in states:
                if s["name"] in old_names:
                    if primary is None:
                        primary = s
                    else:
                        merge_sources.append(s)

            if primary and merge_sources:
                for src in merge_sources:
                    primary.setdefault("checklist", []).extend(src.get("checklist", []))
                    # Merge background.given
                    p_bg = primary.get("background", {})
                    s_bg = src.get("background", {})
                    if s_bg.get("given"):
                        p_bg.setdefault("given", []).extend(s_bg["given"])
                        primary["background"] = p_bg
                # Renumber merged checklist seq values
                for i, c in enumerate(primary.get("checklist", []), 1):
                    c["seq"] = i
                # Remove merged-away states
                merge_names = {s["name"] for s in merge_sources}
                alpha["states"] = [s for s in states if s["name"] not in merge_names]
                changes.append(f"  merge: {old_names} → {new_state_name} ({len(primary.get('checklist', []))} checklists)")

    # Add new states
    if add_states:
        for new_state in add_states:
            alpha.setdefault("states", []).append(new_state)
            changes.append(f"  addState: {new_state['name']} (seq={new_state.get('seq', '?')})")
        # Re-sort states by seq
        alpha["states"].sort(key=lambda s: s.get("seq", 0))

    # 1. Change relationship type
    if set_mapsto:
        old_rel = alpha.pop("contributesTo", None)
        alpha["mapsTo"] = set_mapsto
        if old_rel:
            changes.append(f"  relationship: contributesTo:{old_rel} → mapsTo:{set_mapsto}")
        else:
            changes.append(f"  relationship: set mapsTo:{set_mapsto}")

    if set_contributesto:
        old_rel = alpha.pop("mapsTo", None)
        alpha["contributesTo"] = set_contributesto
        if old_rel:
            changes.append(f"  relationship: mapsTo:{old_rel} → contributesTo:{set_contributesto}")
        else:
            changes.append(f"  relationship: set contributesTo:{set_contributesto}")

    # 2. Rename states (within the alpha AND across all cross-references)
    if state_map:
        # First rename within this alpha's states
        for state in alpha.get("states", []):
            old_state_name = state["name"]
            if old_state_name in state_map:
                state["name"] = state_map[old_state_name]
                changes.append(f"  state: {old_state_name} → {state_map[old_state_name]}")

        # Update contributesToState on states of OTHER alphas that reference this alpha's states
        effective_name = new_name or alpha_name
        for a in practice.get("alphas", []):
            target = a.get("contributesTo") or a.get("mapsTo", "")
            if target == alpha_name or target == effective_name:
                for s in a.get("states", []):
                    cts = s.get("contributesToState")
                    if cts and cts in state_map:
                        s["contributesToState"] = state_map[cts]

        # Deep-rename state name strings in all cross-reference locations
        # (activities.contributesTo[].stateName, patterns.alphaStates[].stateName, etc.)
        for old_state, new_state in state_map.items():
            # Targeted scan of known reference structures
            for act in practice.get("activities", []):
                for c in act.get("contributesTo", []):
                    if isinstance(c, dict) and c.get("alphaName") in (alpha_name, new_name):
                        if c.get("stateName") == old_state:
                            c["stateName"] = new_state
                for c in act.get("worksOn", []):
                    if isinstance(c, dict) and c.get("alphaName") in (alpha_name, new_name):
                        if c.get("stateName") == old_state:
                            c["stateName"] = new_state

            for wp in practice.get("workProducts", []):
                for lod in wp.get("levelsOfDetail", []):
                    for c in lod.get("contributesTo", []):
                        if isinstance(c, dict) and c.get("alphaName") in (alpha_name, new_name):
                            if c.get("stateName") == old_state:
                                c["stateName"] = new_state

            for pat in practice.get("patterns", []):
                for view in pat.get("patternViews", []):
                    for s in view.get("alphaStates", []):
                        if isinstance(s, dict) and s.get("alphaName") in (alpha_name, new_name):
                            sn = s.get("stateName") or s.get("alphaStateName")
                            if sn == old_state:
                                if "stateName" in s:
                                    s["stateName"] = new_state
                                if "alphaStateName" in s:
                                    s["alphaStateName"] = new_state

            # Background alphaStates on alpha states and activities
            def _fix_bg(bg):
                for astate in bg.get("alphaStates", []):
                    if isinstance(astate, dict) and astate.get("alphaName") in (alpha_name, new_name):
                        for field in ("stateName", "alphaStateName"):
                            if astate.get(field) == old_state:
                                astate[field] = new_state

            for a in practice.get("alphas", []):
                for s in a.get("states", []):
                    if "background" in s:
                        _fix_bg(s["background"])

            for act in practice.get("activities", []):
                if "background" in act:
                    _fix_bg(act["background"])

    # 3. Rename the alpha itself (must be done AFTER state renames to not break lookups)
    if new_name and new_name != alpha_name:
        # Update the alpha's own name
        alpha["name"] = new_name
        changes.append(f"  rename: {alpha_name} → {new_name}")

        # Update all cross-references to this alpha name
        ref_count = 0

        # relatesTo on other alphas
        for a in practice.get("alphas", []):
            for r in a.get("relatesTo", []):
                if r.get("alphaName") == alpha_name:
                    r["alphaName"] = new_name
                    ref_count += 1

        # contributesTo/mapsTo targets on other alphas
        for a in practice.get("alphas", []):
            if a is not alpha:
                if a.get("contributesTo") == alpha_name:
                    a["contributesTo"] = new_name
                    ref_count += 1
                if a.get("mapsTo") == alpha_name:
                    a["mapsTo"] = new_name
                    ref_count += 1

        # Activity contributesTo and worksOn
        for act in practice.get("activities", []):
            for c in act.get("contributesTo", []):
                if isinstance(c, dict) and c.get("alphaName") == alpha_name:
                    c["alphaName"] = new_name
                    ref_count += 1
            for c in act.get("worksOn", []):
                if isinstance(c, dict) and c.get("alphaName") == alpha_name:
                    c["alphaName"] = new_name
                    ref_count += 1

        # WorkProduct LOD contributesTo
        for wp in practice.get("workProducts", []):
            for lod in wp.get("levelsOfDetail", []):
                for c in lod.get("contributesTo", []):
                    if isinstance(c, dict) and c.get("alphaName") == alpha_name:
                        c["alphaName"] = new_name
                        ref_count += 1

        # Pattern alphaStates
        for pat in practice.get("patterns", []):
            for view in pat.get("patternViews", []):
                for s in view.get("alphaStates", []):
                    if isinstance(s, dict) and s.get("alphaName") == alpha_name:
                        s["alphaName"] = new_name
                        ref_count += 1

        # Background alphaStates on states
        for a in practice.get("alphas", []):
            for s in a.get("states", []):
                bg = s.get("background", {})
                for astate in bg.get("alphaStates", []):
                    if isinstance(astate, dict) and astate.get("alphaName") == alpha_name:
                        astate["alphaName"] = new_name
                        ref_count += 1

        # practiceElementAliases
        for alias in practice.get("practiceElementAliases", []):
            if alias.get("practiceElementName") == alpha_name:
                alias["practiceElementName"] = new_name
                ref_count += 1
            if alias.get("name") == alpha_name:
                alias["name"] = new_name
                ref_count += 1

        # Narrative contexts that reference alpha by name (in narrativeContexts strings)
        # These are caught by a broader string scan if needed, but usually not structural

        changes.append(f"  references updated: {ref_count}")

    return changes, None


def main():
    parser = argparse.ArgumentParser(
        description="Batch alpha transformation: rename, convert relationships, align states"
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
        alpha_name = spec.get("alpha", "?")
        changes, err = transform_alpha(practice, spec)
        if err:
            errors.append(f"{alpha_name}: {err}")
        else:
            all_changes.append({"alpha": alpha_name, "changes": changes})

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
        print(f"\n{entry['alpha']}:")
        for c in entry["changes"]:
            print(c)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
