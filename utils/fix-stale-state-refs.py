#!/usr/bin/env python3
"""Fix stale state name references in workProducts and activities after alpha state corrections.

After fixing redeclared alphas to match their baseline/parent states, workProducts and activities
may still reference old state names. This script identifies and attempts to map them to canonical states.

Usage:
    python3 utils/fix-stale-state-refs.py <method.json> [--fix]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def get_alpha_states(practice):
    """Build a map of alpha name -> set of valid state names for a practice."""
    alpha_states = {}
    for alpha in practice.get("alphas", []):
        alpha_states[alpha["name"]] = {s["name"] for s in alpha.get("states", [])}
    return alpha_states


def find_closest_state(old_state, valid_states):
    """Find closest matching state using simple heuristics."""
    old_lower = old_state.lower()

    # Exact match (case insensitive)
    for state in valid_states:
        if state.lower() == old_lower:
            return state

    # Substring match
    for state in valid_states:
        if old_lower in state.lower() or state.lower() in old_lower:
            return state

    # Keyword mapping heuristics
    keyword_map = {
        "identified": ["Identified", "Discovered", "Scoped", "Basic Event Matching"],
        "defined": ["Defined", "Specified", "Documented", "Multi-Condition Logic"],
        "tested": ["Tested", "Validated", "Event Correlation"],
        "operational": ["Operational", "Ready", "Hosting Assets", "Simplified Event Routing"],
        "optimized": ["Optimized", "Evolving", "Self-Healing", "Governed"],
        "published": ["Published", "Available", "Value Yielding"],
        "created": ["Provisioned", "Specified"],
        "transforming": ["Converged", "Governed"],
    }

    for keyword, candidates in keyword_map.items():
        if keyword in old_lower:
            for candidate in candidates:
                if candidate in valid_states:
                    return candidate

    # If no match, return first state (safest fallback)
    return sorted(valid_states)[0] if valid_states else None


def fix_workproduct_refs(practice, alpha_states):
    """Fix state references in workProduct levelsOfDetail."""
    changes = []

    for wp in practice.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            for contrib in lod.get("contributesTo", []):
                alpha_name = contrib.get("alphaName")
                state_name = contrib.get("stateName")

                if not alpha_name or not state_name:
                    continue

                valid_states = alpha_states.get(alpha_name)
                if not valid_states:
                    continue

                if state_name not in valid_states:
                    new_state = find_closest_state(state_name, valid_states)
                    if new_state:
                        changes.append({
                            "type": "workProduct",
                            "workProduct": wp["name"],
                            "levelOfDetail": lod["name"],
                            "alpha": alpha_name,
                            "old_state": state_name,
                            "new_state": new_state
                        })
                        contrib["stateName"] = new_state

    return changes


def fix_activity_refs(practice, alpha_states):
    """Fix state references in activity contributesTo."""
    changes = []

    for activity in practice.get("activities", []):
        for contrib in activity.get("contributesTo", []):
            alpha_name = contrib.get("alphaName")
            state_name = contrib.get("stateName")

            if not alpha_name or not state_name:
                continue

            valid_states = alpha_states.get(alpha_name)
            if not valid_states:
                continue

            if state_name not in valid_states:
                new_state = find_closest_state(state_name, valid_states)
                if new_state:
                    changes.append({
                        "type": "activity",
                        "activity": activity["name"],
                        "alpha": alpha_name,
                        "old_state": state_name,
                        "new_state": new_state
                    })
                    contrib["stateName"] = new_state

    return changes


def fix_pattern_refs(practice, alpha_states):
    """Fix state references in pattern views."""
    changes = []

    for pattern in practice.get("patterns", []):
        for view in pattern.get("patternViews", []):
            for alpha_state in view.get("alphaStates", []):
                alpha_name = alpha_state.get("alphaName")
                state_name = alpha_state.get("stateName")

                if not alpha_name or not state_name:
                    continue

                valid_states = alpha_states.get(alpha_name)
                if not valid_states:
                    continue

                if state_name not in valid_states:
                    new_state = find_closest_state(state_name, valid_states)
                    if new_state:
                        changes.append({
                            "type": "pattern",
                            "pattern": pattern["name"],
                            "view": view["name"],
                            "alpha": alpha_name,
                            "old_state": state_name,
                            "new_state": new_state
                        })
                        alpha_state["stateName"] = new_state

    return changes


def fix_method_practices(method_json):
    """Fix all practices in a method JSON."""
    all_changes = []

    for practice_idx, practice in enumerate(method_json.get("practices", [])):
        practice_name = practice.get("name", f"Practice {practice_idx + 1}")
        alpha_states = get_alpha_states(practice)

        # Fix workProduct references
        wp_changes = fix_workproduct_refs(practice, alpha_states)
        for change in wp_changes:
            change["practice"] = practice_name
            all_changes.append(change)

        # Fix activity references
        act_changes = fix_activity_refs(practice, alpha_states)
        for change in act_changes:
            change["practice"] = practice_name
            all_changes.append(change)

        # Fix pattern references
        pat_changes = fix_pattern_refs(practice, alpha_states)
        for change in pat_changes:
            change["practice"] = practice_name
            all_changes.append(change)

    return all_changes


def main():
    parser = argparse.ArgumentParser(description="Fix stale state references in workProducts and activities")
    parser.add_argument("method_file", help="Method JSON file")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place")
    args = parser.parse_args()

    method_json = load_json(args.method_file)

    changes = fix_method_practices(method_json)

    if args.fix and changes:
        with open(args.method_file, "w", encoding="utf-8") as f:
            json.dump(method_json, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"✓ Applied {len(changes)} fixes to {args.method_file}")

    result = {
        "totalChanges": len(changes),
        "dryRun": not args.fix,
        "changes": changes
    }

    print(json.dumps(result, indent=2))
    return 0 if not changes or args.fix else 1


if __name__ == "__main__":
    sys.exit(main())
