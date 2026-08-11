#!/usr/bin/env python3
"""Fix alpha redeclaration issues in method JSON files.

Handles:
1. Missing states in redeclared baseline alphas
2. Missing states in redeclared parent practice alphas
3. Missing contributesTo on parent practice alphas
4. State count violations (minItems: 3)

Usage:
    python3 utils/fix-method-redeclarations.py <method.json> <parent.json> <baseline.json> [--fix]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def get_alpha_by_name(alphas, name):
    """Find alpha by name in list."""
    for alpha in alphas:
        if alpha["name"] == name:
            return alpha
    return None


def is_baseline_alpha(alpha_name, baseline_alphas):
    """Check if alpha exists in baseline."""
    return any(a["name"] == alpha_name for a in baseline_alphas)


def is_parent_alpha(alpha_name, parent_alphas):
    """Check if alpha exists in parent."""
    return any(a["name"] == alpha_name for a in parent_alphas)


def generate_checklist_for_state(state_name, alpha_name, context=""):
    """Generate contextually appropriate checklist items for a state."""
    # Generate 5-7 generic checklist items based on state name
    base_items = [
        f"{state_name} criteria are met for {alpha_name}",
        f"{state_name} status is documented and verified",
        f"Required artifacts for {state_name} are in place",
        f"Stakeholder approval obtained for {state_name}",
        f"{state_name} quality gates passed",
        f"{state_name} metrics are being tracked",
        f"Team is ready to maintain {alpha_name} at {state_name}",
    ]

    items = []
    for i, name in enumerate(base_items[:6], start=1):  # Use 6 items
        items.append({
            "name": name,
            "description": name,
            "seq": i
        })

    return items


def merge_states(canonical_states, practice_states, alpha_name, is_parent_practice=False):
    """Merge canonical states with practice states, preserving practice checklists where they exist."""
    canonical_by_name = {s["name"]: s for s in canonical_states}
    practice_by_name = {s["name"]: s for s in practice_states}
    canonical_names = {s["name"] for s in canonical_states}
    practice_names = {s["name"] for s in practice_states}

    # Detect non-canonical states (practice has states not in canonical)
    extra_states = practice_names - canonical_names
    missing_states = canonical_names - practice_names

    merged = []
    for seq, canonical_state in enumerate(canonical_states, start=1):
        state_name = canonical_state["name"]

        if state_name in practice_by_name:
            # Keep practice state but ensure seq is correct
            state = dict(practice_by_name[state_name])
            state["seq"] = seq
            # Ensure description matches canonical
            state["description"] = canonical_state["description"]
        else:
            # Add missing state with generated checklist
            state = {
                "name": state_name,
                "description": canonical_state["description"],
                "seq": seq,
                "checklist": generate_checklist_for_state(state_name, alpha_name)
            }

        merged.append(state)

    return merged, extra_states, missing_states


def fix_method_practices(method_json, parent_json, baseline_json):
    """Fix all practices in a method JSON."""
    changes = []

    baseline_alphas = baseline_json.get("alphas", [])
    parent_alphas = parent_json.get("alphas", [])

    baseline_alphas_by_name = {a["name"]: a for a in baseline_alphas}
    parent_alphas_by_name = {a["name"]: a for a in parent_alphas}

    for practice_idx, practice in enumerate(method_json.get("practices", [])):
        practice_name = practice.get("name", f"Practice {practice_idx + 1}")

        for alpha in practice.get("alphas", []):
            alpha_name = alpha["name"]

            # Determine if this is a redeclared baseline alpha or parent alpha
            is_baseline = is_baseline_alpha(alpha_name, baseline_alphas)
            is_parent = is_parent_alpha(alpha_name, parent_alphas)

            has_contributes_to = "contributesTo" in alpha

            # Case 1: Baseline alpha redeclaration (should NOT have contributesTo)
            if is_baseline and not has_contributes_to:
                canonical_alpha = baseline_alphas_by_name[alpha_name]
                canonical_states = canonical_alpha.get("states", [])
                practice_states = alpha.get("states", [])

                merged_states, extra_states, missing_states = merge_states(canonical_states, practice_states, alpha_name, False)

                # Report state mismatches
                if extra_states or missing_states:
                    action_parts = []
                    if missing_states:
                        action_parts.append(f"Added {len(missing_states)} missing states: {', '.join(sorted(missing_states))}")
                    if extra_states:
                        action_parts.append(f"Removed {len(extra_states)} non-canonical states: {', '.join(sorted(extra_states))}")

                    changes.append({
                        "practice": practice_name,
                        "alpha": alpha_name,
                        "type": "baseline_redeclaration",
                        "action": "; ".join(action_parts),
                        "states_before": len(practice_states),
                        "states_after": len(merged_states)
                    })
                    alpha["states"] = merged_states

                # Ensure focusName is set
                if "focusName" not in alpha and "focusName" in canonical_alpha:
                    alpha["focusName"] = canonical_alpha["focusName"]
                    changes.append({
                        "practice": practice_name,
                        "alpha": alpha_name,
                        "type": "baseline_redeclaration",
                        "action": f"Added focusName: {canonical_alpha['focusName']}"
                    })

            # Case 2: Parent practice alpha redeclaration (SHOULD have contributesTo)
            elif is_parent:
                canonical_alpha = parent_alphas_by_name[alpha_name]
                canonical_states = canonical_alpha.get("states", [])
                practice_states = alpha.get("states", [])
                canonical_contributes_to = canonical_alpha.get("contributesTo")

                # Fix missing contributesTo
                if not has_contributes_to and canonical_contributes_to:
                    alpha["contributesTo"] = canonical_contributes_to
                    changes.append({
                        "practice": practice_name,
                        "alpha": alpha_name,
                        "type": "parent_redeclaration",
                        "action": f"Added contributesTo: {canonical_contributes_to}"
                    })

                # Fix state mismatches
                merged_states, extra_states, missing_states = merge_states(canonical_states, practice_states, alpha_name, True)

                if extra_states or missing_states:
                    action_parts = []
                    if missing_states:
                        action_parts.append(f"Added {len(missing_states)} missing states: {', '.join(sorted(missing_states))}")
                    if extra_states:
                        action_parts.append(f"Removed {len(extra_states)} non-canonical states: {', '.join(sorted(extra_states))}")

                    changes.append({
                        "practice": practice_name,
                        "alpha": alpha_name,
                        "type": "parent_redeclaration",
                        "action": "; ".join(action_parts),
                        "states_before": len(practice_states),
                        "states_after": len(merged_states)
                    })
                    alpha["states"] = merged_states

                # Ensure focusName is set
                if "focusName" not in alpha and "focusName" in canonical_alpha:
                    alpha["focusName"] = canonical_alpha["focusName"]
                    changes.append({
                        "practice": practice_name,
                        "alpha": alpha_name,
                        "type": "parent_redeclaration",
                        "action": f"Added focusName: {canonical_alpha['focusName']}"
                    })

            # Case 3: Check for state count violations (minimum 3 states)
            if len(alpha.get("states", [])) < 3 and not is_baseline and not is_parent:
                # This is a new alpha with too few states - just report it
                changes.append({
                    "practice": practice_name,
                    "alpha": alpha_name,
                    "type": "validation_warning",
                    "action": f"Alpha has only {len(alpha.get('states', []))} states (minimum 3 required)"
                })

    return changes


def main():
    parser = argparse.ArgumentParser(description="Fix method redeclaration issues")
    parser.add_argument("method_file", help="Method JSON file")
    parser.add_argument("parent_file", help="Parent practice JSON file")
    parser.add_argument("baseline_file", help="Baseline JSON file")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place")
    args = parser.parse_args()

    method_json = load_json(args.method_file)
    parent_json = load_json(args.parent_file)
    baseline_json = load_json(args.baseline_file)

    changes = fix_method_practices(method_json, parent_json, baseline_json)

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
