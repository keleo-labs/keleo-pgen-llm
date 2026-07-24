#!/usr/bin/env python3
"""
Align Child Baseline States

Ensures a child baseline's redeclared alpha states match parent canonical
state names exactly, moving domain-specific terminology to practiceElementAliases.

When a child baseline redeclares parent alphas, the states MUST use the parent's
canonical names. Programme/domain-specific state names are captured as aliases.

Usage:
    # Check for misaligned states:
    python3 utils/align-baseline-states.py child.json parent.json --check

    # Fix misaligned states using a mapping config:
    python3 utils/align-baseline-states.py child.json parent.json \\
        --mapping mapping.json -o output.json

Mapping config format:
    {
      "AlphaName": {
        "stateMapping": [
          ["ChildStateName", "ParentStateName"],
          ...
        ],
        "restoreFromParent": ["StateName1", "StateName2"]
      }
    }

    - stateMapping: pairs of [child_name, parent_name] for renaming
      Multiple child states can map to the same parent state (content merged)
    - restoreFromParent: parent state names to restore (dropped by child)

Exit codes:
    0 - Success (or --check with no mismatches)
    1 - Mismatches found (--check) or error
"""

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def check_state_alignment(child, parent):
    """Report state mismatches between shared alphas in child and parent."""
    parent_alphas = {a["name"]: a for a in parent.get("alphas", [])}
    child_alphas = {a["name"]: a for a in child.get("alphas", [])}

    shared = sorted(set(parent_alphas) & set(child_alphas))
    mismatches = {}

    for name in shared:
        p_states = [s["name"] for s in parent_alphas[name]["states"]]
        c_states = [s["name"] for s in child_alphas[name]["states"]]
        if p_states != c_states:
            mismatches[name] = {
                "parentStates": p_states,
                "childStates": c_states,
                "parentCount": len(p_states),
                "childCount": len(c_states),
            }

    return mismatches


def apply_mapping(child, parent, mapping):
    """Apply state mapping to align child states with parent canonical names."""
    result = copy.deepcopy(child)

    parent_alphas = {a["name"]: a for a in parent.get("alphas", [])}

    # (alphaName, oldStateName) -> newStateName for contributesTo updates
    rename_map = {}
    aliases = list(result.get("practiceElementAliases", []))
    # Track canonical names that already have an alias to avoid duplicates
    aliased_names = {
        (a.get("practiceElementType"), a.get("practiceElementName"))
        for a in aliases
    }

    for alpha_name, config in mapping.items():
        state_mapping = config.get("stateMapping", [])
        restore_states = set(config.get("restoreFromParent", []))

        for child_state, parent_state in state_mapping:
            rename_map[(alpha_name, child_state)] = parent_state
            if child_state != parent_state:
                alias_key = ("State", parent_state)
                if alias_key not in aliased_names:
                    aliases.append(
                        {
                            "practiceElementType": "State",
                            "practiceElementName": parent_state,
                            "aliasName": child_state,
                        }
                    )
                    aliased_names.add(alias_key)

        parent_alpha = parent_alphas.get(alpha_name)
        if not parent_alpha:
            print(
                json.dumps({"warning": f"Alpha '{alpha_name}' not in parent"}),
                file=sys.stderr,
            )
            continue

        for alpha in result.get("alphas", []):
            if alpha["name"] != alpha_name:
                continue

            child_state_lookup = {s["name"]: s for s in alpha["states"]}

            # parent_state_name -> first child_state_name that maps to it
            parent_to_child_primary = {}
            # parent_state_name -> all child_state_names (for merging)
            parent_to_child_all = {}
            for cs, ps in state_mapping:
                parent_to_child_all.setdefault(ps, []).append(cs)
                if ps not in parent_to_child_primary:
                    parent_to_child_primary[ps] = cs

            new_states = []
            for p_state in parent_alpha["states"]:
                p_name = p_state["name"]

                if p_name in restore_states:
                    restored = copy.deepcopy(p_state)
                    new_states.append(restored)

                elif p_name in parent_to_child_primary:
                    primary_child = parent_to_child_primary[p_name]
                    child_state = child_state_lookup.get(primary_child)

                    if child_state:
                        new_state = copy.deepcopy(child_state)
                        new_state["name"] = p_name
                        new_state["seq"] = p_state["seq"]

                        # Merge checklists from secondary mapped states
                        for extra_name in parent_to_child_all.get(p_name, [])[1:]:
                            extra = child_state_lookup.get(extra_name)
                            if extra and "checklist" in extra:
                                existing = {
                                    c["name"] for c in new_state.get("checklist", [])
                                }
                                for check in extra["checklist"]:
                                    if check["name"] not in existing:
                                        merged = copy.deepcopy(check)
                                        merged["seq"] = (
                                            len(new_state.get("checklist", [])) + 1
                                        )
                                        new_state.setdefault("checklist", []).append(
                                            merged
                                        )

                        new_states.append(new_state)
                    else:
                        new_states.append(copy.deepcopy(p_state))
                else:
                    new_states.append(copy.deepcopy(p_state))

            alpha["states"] = new_states
            break

    # Update contributesTo references in activitySpaces
    for asp in result.get("activitySpaces", []):
        for ct in asp.get("contributesTo", []):
            key = (ct.get("alphaName", ""), ct.get("stateName", ""))
            if key in rename_map:
                ct["stateName"] = rename_map[key]

        # Deduplicate (multiple child states may map to same parent state)
        if "contributesTo" in asp:
            seen = set()
            deduped = []
            for ct in asp["contributesTo"]:
                key = (ct.get("alphaName", ""), ct.get("stateName", ""))
                if key not in seen:
                    seen.add(key)
                    deduped.append(ct)
            asp["contributesTo"] = deduped

    if aliases:
        result["practiceElementAliases"] = aliases

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Align child baseline alpha states with parent canonical names"
    )
    parser.add_argument("child", help="Child baseline JSON path")
    parser.add_argument("parent", help="Parent baseline JSON path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report state mismatches only (no changes)",
    )
    parser.add_argument("--mapping", help="Mapping config JSON path")
    parser.add_argument("-o", "--output", help="Output path for aligned baseline")

    args = parser.parse_args()

    child = load_json(Path(args.child))
    parent = load_json(Path(args.parent))

    if args.check:
        mismatches = check_state_alignment(child, parent)
        if not mismatches:
            print(
                json.dumps(
                    {"aligned": True, "message": "All shared alpha states match parent"}
                )
            )
        else:
            print(json.dumps({"aligned": False, "mismatches": mismatches}, indent=2))
        sys.exit(0 if not mismatches else 1)

    if not args.mapping or not args.output:
        parser.error("--mapping and -o are required when not using --check")

    mapping = load_json(Path(args.mapping))
    result = apply_mapping(child, parent, mapping)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    mismatches = check_state_alignment(result, parent)
    alias_count = len(result.get("practiceElementAliases", []))

    report = {
        "success": not mismatches,
        "outputPath": str(output_path),
        "aliasesGenerated": alias_count,
    }
    if mismatches:
        report["remainingMismatches"] = mismatches

    print(json.dumps(report, indent=2))
    sys.exit(0 if not mismatches else 1)


if __name__ == "__main__":
    main()
