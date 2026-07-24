#!/usr/bin/env python3
"""Alpha reference operations: add redeclarations, remap references, remove alphas.

Usage:
    # Add missing baseline alpha as redeclaration (dry-run)
    python3 utils/fix-alpha-refs.py practice.json baseline.json --add-redeclaration "Alpha Name"

    # Remap all references from one alpha to another
    python3 utils/fix-alpha-refs.py practice.json baseline.json \\
        --remap "Old Alpha" "New Alpha" --state-map '{"OldState":"NewState"}'

    # Remove an alpha and all its references
    python3 utils/fix-alpha-refs.py practice.json baseline.json --remove-alpha "Alpha Name"

    # Apply changes (add --fix to any mode)
    python3 utils/fix-alpha-refs.py practice.json baseline.json --add-redeclaration "Alpha Name" --fix
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def _scan_references(practice, target_alpha):
    """Find all locations referencing target_alpha. Returns list of (obj, key_path) tuples."""
    refs = []

    for act in practice.get("activities", []):
        for c in act.get("contributesTo", []):
            if isinstance(c, dict) and c.get("alphaName") == target_alpha:
                refs.append({
                    "obj": c,
                    "location": f"activities[{act.get('name', '?')}].contributesTo",
                    "type": "contributesTo",
                })

    for wp in practice.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            for c in lod.get("contributesTo", []):
                if isinstance(c, dict) and c.get("alphaName") == target_alpha:
                    refs.append({
                        "obj": c,
                        "location": f"workProducts[{wp.get('name', '?')}].levelsOfDetail[{lod.get('name', '?')}].contributesTo",
                        "type": "contributesTo",
                    })

    for pat in practice.get("patterns", []):
        for view in pat.get("patternViews", []):
            for state in view.get("alphaStates", []):
                if isinstance(state, dict) and state.get("alphaName") == target_alpha:
                    refs.append({
                        "obj": state,
                        "location": f"patterns[{pat.get('name', '?')}].patternViews[{view.get('name', '?')}].alphaStates",
                        "type": "alphaState",
                    })

    for alpha in practice.get("alphas", []):
        for r in alpha.get("relatesTo", []):
            if r.get("alphaName") == target_alpha:
                refs.append({
                    "obj": r,
                    "location": f"alphas[{alpha.get('name', '?')}].relatesTo",
                    "type": "relatesTo",
                })

    return refs


def add_redeclaration(practice, baseline, alpha_name):
    """Copy a baseline alpha as a minimal redeclaration into the practice."""
    existing_names = {a["name"] for a in practice.get("alphas", [])}
    if alpha_name in existing_names:
        return [], f"Alpha '{alpha_name}' already exists in practice"

    baseline_alphas = {a["name"]: a for a in baseline.get("alphas", [])}
    ba = baseline_alphas.get(alpha_name)
    if not ba:
        return [], f"Alpha '{alpha_name}' not found in baseline"

    redecl = {
        "name": ba["name"],
        "description": ba["description"],
        "focusName": ba["focusName"],
        "states": ba["states"],
    }
    if "relatesTo" in ba:
        redecl["relatesTo"] = ba["relatesTo"]

    practice.setdefault("alphas", []).append(redecl)

    changes = [{
        "location": "alphas",
        "field": "name",
        "action": "added",
        "new": alpha_name,
    }]
    return changes, None


def remap_alpha_references(practice, old_alpha, new_alpha, state_map):
    """Replace all references to old_alpha with new_alpha, applying state_map."""
    changes = []
    refs = _scan_references(practice, old_alpha)

    for ref in refs:
        obj = ref["obj"]
        old_state = obj.get("stateName", obj.get("alphaStateName"))
        new_state = state_map.get(old_state, old_state)

        change = {
            "location": ref["location"],
            "field": "alphaName",
            "old": old_alpha,
            "new": new_alpha,
        }

        obj["alphaName"] = new_alpha
        if "stateName" in obj and old_state in state_map:
            obj["stateName"] = new_state
            change["stateOld"] = old_state
            change["stateNew"] = new_state
        elif "alphaStateName" in obj and old_state in state_map:
            obj["alphaStateName"] = new_state
            change["stateOld"] = old_state
            change["stateNew"] = new_state

        changes.append(change)

    # Remove old alpha from alphas array if present
    original_count = len(practice.get("alphas", []))
    practice["alphas"] = [a for a in practice.get("alphas", []) if a["name"] != old_alpha]
    if len(practice["alphas"]) < original_count:
        changes.append({
            "location": "alphas",
            "field": "name",
            "action": "removed",
            "old": old_alpha,
        })

    # Clean up relatesTo references to old alpha on remaining alphas
    for alpha in practice.get("alphas", []):
        original_relates = alpha.get("relatesTo", [])
        cleaned = [r for r in original_relates if r.get("alphaName") != old_alpha]
        if len(cleaned) < len(original_relates):
            alpha["relatesTo"] = cleaned
            changes.append({
                "location": f"alphas[{alpha['name']}].relatesTo",
                "action": "cleaned",
                "old": old_alpha,
            })

    return changes


def remove_alpha(practice, alpha_name):
    """Remove an alpha definition and all references to it."""
    changes = []

    # Remove from alphas array
    original_count = len(practice.get("alphas", []))
    practice["alphas"] = [a for a in practice.get("alphas", []) if a["name"] != alpha_name]
    if len(practice["alphas"]) < original_count:
        changes.append({
            "location": "alphas",
            "field": "name",
            "action": "removed",
            "old": alpha_name,
        })

    # Remove contributesTo entries in activities
    for act in practice.get("activities", []):
        original = act.get("contributesTo", [])
        cleaned = [c for c in original if not (isinstance(c, dict) and c.get("alphaName") == alpha_name)]
        if len(cleaned) < len(original):
            act["contributesTo"] = cleaned
            changes.append({
                "location": f"activities[{act.get('name', '?')}].contributesTo",
                "action": "removed-refs",
                "old": alpha_name,
                "count": len(original) - len(cleaned),
            })

    # Remove contributesTo entries in LODs
    for wp in practice.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            original = lod.get("contributesTo", [])
            cleaned = [c for c in original if not (isinstance(c, dict) and c.get("alphaName") == alpha_name)]
            if len(cleaned) < len(original):
                lod["contributesTo"] = cleaned
                changes.append({
                    "location": f"workProducts[{wp.get('name', '?')}].levelsOfDetail[{lod.get('name', '?')}].contributesTo",
                    "action": "removed-refs",
                    "old": alpha_name,
                    "count": len(original) - len(cleaned),
                })

    # Remove alphaStates entries in patterns
    for pat in practice.get("patterns", []):
        for view in pat.get("patternViews", []):
            original = view.get("alphaStates", [])
            cleaned = [s for s in original if not (isinstance(s, dict) and s.get("alphaName") == alpha_name)]
            if len(cleaned) < len(original):
                view["alphaStates"] = cleaned
                changes.append({
                    "location": f"patterns[{pat.get('name', '?')}].patternViews[{view.get('name', '?')}].alphaStates",
                    "action": "removed-refs",
                    "old": alpha_name,
                    "count": len(original) - len(cleaned),
                })

    # Remove relatesTo entries
    for alpha in practice.get("alphas", []):
        original = alpha.get("relatesTo", [])
        cleaned = [r for r in original if r.get("alphaName") != alpha_name]
        if len(cleaned) < len(original):
            alpha["relatesTo"] = cleaned
            changes.append({
                "location": f"alphas[{alpha['name']}].relatesTo",
                "action": "removed-refs",
                "old": alpha_name,
                "count": len(original) - len(cleaned),
            })

    return changes


def main():
    parser = argparse.ArgumentParser(description="Alpha reference operations")
    parser.add_argument("file", help="Practice JSON file")
    parser.add_argument("baseline", help="Baseline or effective-baseline JSON file")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place (default: dry-run)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--add-redeclaration", metavar="ALPHA",
                       help="Add missing baseline alpha as redeclaration")
    group.add_argument("--remap", nargs=2, metavar=("OLD", "NEW"),
                       help="Remap all references from OLD alpha to NEW alpha")
    group.add_argument("--remove-alpha", metavar="ALPHA",
                       help="Remove alpha and all its references")

    parser.add_argument("--state-map", default="{}",
                        help='State name mapping as JSON (e.g. \'{"OldState":"NewState"}\'). Used with --remap.')

    args = parser.parse_args()

    practice = load_json(args.file)
    baseline = load_json(args.baseline)

    if args.add_redeclaration:
        mode = "add-redeclaration"
        changes, err = add_redeclaration(practice, baseline, args.add_redeclaration)
        target = args.add_redeclaration
        if err:
            print(json.dumps({"mode": mode, "targetAlpha": target, "error": err}))
            sys.exit(1)
    elif args.remap:
        mode = "remap"
        old_alpha, new_alpha = args.remap
        target = f"{old_alpha} -> {new_alpha}"
        state_map = json.loads(args.state_map)
        changes = remap_alpha_references(practice, old_alpha, new_alpha, state_map)
    elif args.remove_alpha:
        mode = "remove-alpha"
        target = args.remove_alpha
        changes = remove_alpha(practice, target)

    if args.fix and changes:
        with open(args.file, "w", encoding="utf-8") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")

    result = {
        "mode": mode,
        "targetAlpha": target,
        "dryRun": not args.fix,
        "changesApplied": len(changes),
        "changes": changes,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
