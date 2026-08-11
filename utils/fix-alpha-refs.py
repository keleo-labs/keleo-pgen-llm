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

    # Remove alpha + cascade activities, patterns, activitySpaces, assets, keywords
    python3 utils/fix-alpha-refs.py practice.json baseline.json --remove-alpha "Alpha Name" \\
        --remove-activities "Develop Seller Readiness" \\
        --remove-patterns "Seller Readiness Maturity Journey" \\
        --remove-activityspaces "Enable Sellers" \\
        --remove-assets "seller-readiness-icon" \\
        --remove-keywords "seller-readiness" \\
        --fix

    # Remove only references (alpha defined in parent, not locally)
    python3 utils/fix-alpha-refs.py practice.json baseline.json --remove-alpha "Alpha Name" --refs-only --fix

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


def remove_alpha(practice, alpha_name, *,
                 refs_only=False,
                 remove_activities=None,
                 remove_patterns=None,
                 remove_activityspaces=None,
                 remove_assets=None,
                 remove_keywords=None):
    """Remove an alpha definition and all references to it.

    Args:
        practice: The parsed JSON document (mutated in place).
        alpha_name: Name of the alpha to remove.
        refs_only: If True, skip removing the alpha definition itself
                   (for files where the alpha is inherited from a parent).
        remove_activities: List of activity names to remove entirely.
        remove_patterns: List of pattern names to remove entirely.
        remove_activityspaces: List of activitySpace names to remove entirely.
        remove_assets: List of asset names to remove.
        remove_keywords: List of keywords to remove.
    """
    changes = []
    remove_activities = set(remove_activities or [])
    remove_patterns = set(remove_patterns or [])
    remove_activityspaces = set(remove_activityspaces or [])
    remove_assets = set(remove_assets or [])
    remove_keywords = set(remove_keywords or [])

    # --- Alpha definition ---
    if not refs_only:
        original_count = len(practice.get("alphas", []))
        practice["alphas"] = [a for a in practice.get("alphas", [])
                              if a["name"] != alpha_name]
        if len(practice["alphas"]) < original_count:
            changes.append({
                "location": "alphas",
                "action": "removed-alpha",
                "old": alpha_name,
            })

    # --- relatesTo entries on remaining alphas ---
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

    # --- background.alphaStates on alpha states ---
    for alpha in practice.get("alphas", []):
        for state in alpha.get("states", []):
            bg = state.get("background")
            if bg and "alphaStates" in bg:
                original = bg["alphaStates"]
                cleaned = [s for s in original
                           if not (isinstance(s, dict) and s.get("alphaName") == alpha_name)]
                if len(cleaned) < len(original):
                    bg["alphaStates"] = cleaned
                    changes.append({
                        "location": f"alphas[{alpha['name']}].states[{state['name']}].background.alphaStates",
                        "action": "removed-refs",
                        "old": alpha_name,
                        "count": len(original) - len(cleaned),
                    })
                    if not cleaned:
                        del bg["alphaStates"]
                        if not bg.get("given") and not bg.get("workProductLevels"):
                            del state["background"]

    # --- Remove entire activities ---
    if remove_activities:
        original_count = len(practice.get("activities", []))
        practice["activities"] = [a for a in practice.get("activities", [])
                                  if a.get("name") not in remove_activities]
        removed_count = original_count - len(practice.get("activities", []))
        if removed_count:
            changes.append({
                "location": "activities",
                "action": "removed-activities",
                "names": sorted(remove_activities),
                "count": removed_count,
            })

    # --- contributesTo entries in remaining activities ---
    for act in practice.get("activities", []):
        original = act.get("contributesTo", [])
        cleaned = [c for c in original
                   if not (isinstance(c, dict) and c.get("alphaName") == alpha_name)]
        if len(cleaned) < len(original):
            act["contributesTo"] = cleaned
            changes.append({
                "location": f"activities[{act.get('name', '?')}].contributesTo",
                "action": "removed-refs",
                "old": alpha_name,
                "count": len(original) - len(cleaned),
            })

    # --- background.alphaStates on activities ---
    for act in practice.get("activities", []):
        bg = act.get("background")
        if bg and "alphaStates" in bg:
            original = bg["alphaStates"]
            cleaned = [s for s in original
                       if not (isinstance(s, dict) and s.get("alphaName") == alpha_name)]
            if len(cleaned) < len(original):
                bg["alphaStates"] = cleaned
                changes.append({
                    "location": f"activities[{act.get('name', '?')}].background.alphaStates",
                    "action": "removed-refs",
                    "old": alpha_name,
                    "count": len(original) - len(cleaned),
                })
                if not cleaned:
                    del bg["alphaStates"]
                    if not bg.get("given") and not bg.get("workProductLevels"):
                        del act["background"]

    # --- contributesTo entries in work product LODs ---
    for wp in practice.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            original = lod.get("contributesTo", [])
            cleaned = [c for c in original
                       if not (isinstance(c, dict) and c.get("alphaName") == alpha_name)]
            if len(cleaned) < len(original):
                lod["contributesTo"] = cleaned
                changes.append({
                    "location": f"workProducts[{wp.get('name', '?')}].levelsOfDetail[{lod.get('name', '?')}].contributesTo",
                    "action": "removed-refs",
                    "old": alpha_name,
                    "count": len(original) - len(cleaned),
                })

    # --- Remove entire patterns ---
    if remove_patterns:
        original_count = len(practice.get("patterns", []))
        practice["patterns"] = [p for p in practice.get("patterns", [])
                                if p.get("name") not in remove_patterns]
        removed_count = original_count - len(practice.get("patterns", []))
        if removed_count:
            changes.append({
                "location": "patterns",
                "action": "removed-patterns",
                "names": sorted(remove_patterns),
                "count": removed_count,
            })

    # --- alphaStates + activity refs in remaining pattern views ---
    for pat in practice.get("patterns", []):
        for view in pat.get("patternViews", []):
            # alphaStates
            original = view.get("alphaStates", [])
            cleaned = [s for s in original
                       if not (isinstance(s, dict) and s.get("alphaName") == alpha_name)]
            if len(cleaned) < len(original):
                view["alphaStates"] = cleaned
                changes.append({
                    "location": f"patterns[{pat.get('name', '?')}].patternViews[{view.get('name', '?')}].alphaStates",
                    "action": "removed-refs",
                    "old": alpha_name,
                    "count": len(original) - len(cleaned),
                })

            # activity references
            if remove_activities:
                original_acts = view.get("activities", [])
                cleaned_acts = [a for a in original_acts if a not in remove_activities]
                if len(cleaned_acts) < len(original_acts):
                    view["activities"] = cleaned_acts
                    changes.append({
                        "location": f"patterns[{pat.get('name', '?')}].patternViews[{view.get('name', '?')}].activities",
                        "action": "removed-activity-refs",
                        "count": len(original_acts) - len(cleaned_acts),
                    })

    # --- activitySpaces: remove entirely + clean contributesTo on remaining ---
    if remove_activityspaces:
        original_count = len(practice.get("activitySpaces", []))
        practice["activitySpaces"] = [s for s in practice.get("activitySpaces", [])
                                      if s.get("name") not in remove_activityspaces]
        removed_count = original_count - len(practice.get("activitySpaces", []))
        if removed_count:
            changes.append({
                "location": "activitySpaces",
                "action": "removed-activityspaces",
                "names": sorted(remove_activityspaces),
                "count": removed_count,
            })

    for asp in practice.get("activitySpaces", []):
        original = asp.get("contributesTo", [])
        cleaned = [c for c in original
                   if not (isinstance(c, dict) and c.get("alphaName") == alpha_name)]
        if len(cleaned) < len(original):
            asp["contributesTo"] = cleaned
            changes.append({
                "location": f"activitySpaces[{asp.get('name', '?')}].contributesTo",
                "action": "removed-refs",
                "old": alpha_name,
                "count": len(original) - len(cleaned),
            })

    # --- Assets ---
    if remove_assets:
        # Remove from top-level assets array
        original_count = len(practice.get("assets", []))
        practice["assets"] = [a for a in practice.get("assets", [])
                              if a.get("name") not in remove_assets]
        removed_count = original_count - len(practice.get("assets", []))
        if removed_count:
            changes.append({
                "location": "assets",
                "action": "removed-assets",
                "names": sorted(remove_assets),
                "count": removed_count,
            })

        # Remove assetNames references on alphas and other elements
        for collection_key in ("alphas", "activities", "workProducts", "patterns",
                               "activitySpaces", "competencies"):
            for elem in practice.get(collection_key, []):
                original = elem.get("assetNames", [])
                cleaned = [an for an in original
                           if an.get("assetName") not in remove_assets]
                if len(cleaned) < len(original):
                    elem["assetNames"] = cleaned
                    changes.append({
                        "location": f"{collection_key}[{elem.get('name', '?')}].assetNames",
                        "action": "removed-asset-refs",
                        "count": len(original) - len(cleaned),
                    })

    # --- Keywords ---
    if remove_keywords:
        original = practice.get("keywords", [])
        cleaned = [k for k in original if k not in remove_keywords]
        if len(cleaned) < len(original):
            practice["keywords"] = cleaned
            changes.append({
                "location": "keywords",
                "action": "removed-keywords",
                "removed": sorted(remove_keywords & set(original)),
            })

    return changes


def main():
    parser = argparse.ArgumentParser(description="Alpha reference operations")
    parser.add_argument("file", help="Practice/baseline JSON file")
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
    parser.add_argument("--refs-only", action="store_true",
                        help="With --remove-alpha: skip alpha definition removal (alpha inherited from parent)")
    parser.add_argument("--remove-activities", nargs="+", metavar="NAME",
                        help="With --remove-alpha: remove these activities entirely")
    parser.add_argument("--remove-patterns", nargs="+", metavar="NAME",
                        help="With --remove-alpha: remove these patterns entirely")
    parser.add_argument("--remove-activityspaces", nargs="+", metavar="NAME",
                        help="With --remove-alpha: remove these activitySpaces entirely")
    parser.add_argument("--remove-assets", nargs="+", metavar="NAME",
                        help="With --remove-alpha: remove these assets by name")
    parser.add_argument("--remove-keywords", nargs="+", metavar="KW",
                        help="With --remove-alpha: remove these keywords")

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
        changes = remove_alpha(
            practice, target,
            refs_only=args.refs_only,
            remove_activities=args.remove_activities,
            remove_patterns=args.remove_patterns,
            remove_activityspaces=args.remove_activityspaces,
            remove_assets=args.remove_assets,
            remove_keywords=args.remove_keywords,
        )

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
