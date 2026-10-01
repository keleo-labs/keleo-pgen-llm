#!/usr/bin/env python3
"""Transform a work product into an alpha + revised work product.

Reads a practice JSON, extracts the named work product's LODs as alpha states,
creates a new alpha, revises the work product with new LODs, and updates all
cross-references (pattern views, activity worksOn/contributesTo, aliases).

Usage:
    python3 utils/transform-wp-to-alpha.py <practice.json> --config <config.json> [--fix]

The config JSON defines the transformation:
{
    "sourceWorkProductName": "Infrastructure as Code",
    "newAlpha": {
        "name": "Infrastructure as Code",
        "description": "...",
        "focusName": "Solution",
        "contributesTo": "Platform Infrastructure",
        "contributesToStateMappings": {
            "Declarative Configuration": "Basic Cluster Provisioned",
            ...
        },
        "relatesTo": [ ... ],
        "states": [ { "name": "...", "description": "...", "sourceLodNames": [...] } ]
    },
    "revisedWorkProduct": {
        "name": "Infrastructure as Code Configuration",
        "description": "...",
        "levelsOfDetail": [ { "name": "...", ... } ]
    },
    "lodToLodMapping": {
        "Installation Configuration": "Basic Manifests",
        "Operator Configuration": "Parameterized Templates",
        ...
    },
    "lodToStateMapping": {
        "Installation Configuration": "Declarative Configuration",
        ...
    },
    "patternAlphaStates": {
        "0": "Declarative Configuration",
        "1": "Operator-Managed Configuration",
        ...
    }
}
"""

import argparse
import json
import sys
from copy import deepcopy


def transform(practice: dict, config: dict, fix: bool = False) -> dict:
    """Apply the transformation and return the modified practice."""

    src_wp_name = config["sourceWorkProductName"]
    new_alpha_cfg = config["newAlpha"]
    revised_wp_cfg = config["revisedWorkProduct"]
    lod_to_lod = config.get("lodToLodMapping", {})
    lod_to_state = config.get("lodToStateMapping", {})
    pattern_alpha_states = config.get("patternAlphaStates", {})

    changes = []

    # 1. Find and extract the source work product
    wp_idx = None
    source_wp = None
    for i, wp in enumerate(practice.get("workProducts", [])):
        if wp["name"] == src_wp_name:
            wp_idx = i
            source_wp = deepcopy(wp)
            break

    if source_wp is None:
        print(f"ERROR: Work product '{src_wp_name}' not found", file=sys.stderr)
        sys.exit(1)

    # 2. Build the new alpha from config + source WP LOD checklists
    new_alpha = {
        "name": new_alpha_cfg["name"],
        "description": new_alpha_cfg["description"],
        "focusName": new_alpha_cfg["focusName"],
        "contributesTo": new_alpha_cfg["contributesTo"],
        "relatesTo": new_alpha_cfg.get("relatesTo", []),
        "states": []
    }

    # Build state objects from config, transferring checklists from source LODs
    lod_by_name = {lod["name"]: lod for lod in source_wp.get("levelsOfDetail", [])}

    for seq_idx, state_cfg in enumerate(new_alpha_cfg["states"], 1):
        state = {
            "name": state_cfg["name"],
            "description": state_cfg["description"],
            "seq": seq_idx,
        }

        # Map to parent state
        parent_state = new_alpha_cfg["contributesToStateMappings"].get(state_cfg["name"])
        if parent_state:
            state["contributesToState"] = parent_state

        # Transfer checklists from the source LOD(s) mapped to this state
        source_lod_names = state_cfg.get("sourceLodNames", [])
        all_checklist_items = []
        for sln in source_lod_names:
            src_lod = lod_by_name.get(sln)
            if src_lod and src_lod.get("checklist"):
                all_checklist_items.extend(deepcopy(src_lod["checklist"]))

        if all_checklist_items:
            # Re-sequence and strip test property (not valid on state checklists)
            for i, item in enumerate(all_checklist_items, 1):
                item["seq"] = i
                item.pop("test", None)
            state["checklist"] = all_checklist_items

        # Transfer background from source LOD if available
        if source_lod_names and lod_by_name.get(source_lod_names[0], {}).get("background"):
            bg = deepcopy(lod_by_name[source_lod_names[0]]["background"])
            # Remove alphaStates that reference the alpha's own states (self-ref)
            if "alphaStates" in bg:
                bg["alphaStates"] = [
                    s for s in bg["alphaStates"]
                    if s["alphaName"] != new_alpha_cfg["name"]
                ]
                if not bg["alphaStates"]:
                    del bg["alphaStates"]
            if bg.get("given") or bg.get("alphaStates") or bg.get("workProductLevels"):
                state["background"] = bg

        new_alpha["states"].append(state)

    changes.append(f"ADD alpha: {new_alpha['name']} (contributesTo: {new_alpha['contributesTo']})")

    # 3. Revise the work product
    revised_wp = deepcopy(source_wp)
    revised_wp["name"] = revised_wp_cfg["name"]
    revised_wp["description"] = revised_wp_cfg["description"]

    # Replace contributesToAlphaNames - add new alpha, keep others
    if new_alpha_cfg["name"] not in revised_wp.get("contributesToAlphaNames", []):
        revised_wp.setdefault("contributesToAlphaNames", []).insert(0, new_alpha_cfg["name"])

    # Replace LODs with new ones from config
    revised_wp["levelsOfDetail"] = revised_wp_cfg["levelsOfDetail"]

    # Update WP narrative if present
    if revised_wp.get("narratives"):
        for narr in revised_wp["narratives"]:
            narr["name"] = narr["name"].replace(src_wp_name, revised_wp_cfg["name"])

    changes.append(f"RENAME WP: {src_wp_name} → {revised_wp_cfg['name']}")
    changes.append(f"REPLACE WP LODs: {len(source_wp['levelsOfDetail'])} → {len(revised_wp['levelsOfDetail'])}")

    if fix:
        # 4. Insert new alpha (after the one it contributesTo)
        insert_idx = len(practice["alphas"])
        for i, a in enumerate(practice["alphas"]):
            if a["name"] == new_alpha_cfg["contributesTo"]:
                insert_idx = i + 1
                break
        practice["alphas"].insert(insert_idx, new_alpha)

        # 5. Replace the work product
        practice["workProducts"][wp_idx] = revised_wp

        # 6. Update reciprocal relatesTo on target alphas
        for rt in new_alpha.get("relatesTo", []):
            target_name = rt["alphaName"]
            for a in practice["alphas"]:
                if a["name"] == target_name:
                    existing_rt = a.get("relatesTo", [])
                    already_has = any(r["alphaName"] == new_alpha_cfg["name"] for r in existing_rt)
                    if not already_has:
                        reciprocal_dir = {"outgoing": "incoming", "incoming": "outgoing", "mutual": "mutual"}
                        existing_rt.append({
                            "relationship": rt["relationship"],
                            "alphaName": new_alpha_cfg["name"],
                            "direction": reciprocal_dir.get(rt["direction"], "mutual"),
                            "relationshipKind": rt.get("relationshipKind", "information-flow")
                        })
                        a["relatesTo"] = existing_rt
                        changes.append(f"ADD relatesTo reciprocal: {target_name} → {new_alpha_cfg['name']}")

        # Also add reciprocal on the contributesTo parent
        parent_name = new_alpha_cfg["contributesTo"]
        for a in practice["alphas"]:
            if a["name"] == parent_name:
                existing_rt = a.get("relatesTo", [])
                already_has = any(r["alphaName"] == new_alpha_cfg["name"] for r in existing_rt)
                if not already_has:
                    existing_rt.append({
                        "relationship": "defined by",
                        "alphaName": new_alpha_cfg["name"],
                        "direction": "incoming",
                        "relationshipKind": "enabling"
                    })
                    a["relatesTo"] = existing_rt
                    changes.append(f"ADD relatesTo: {parent_name} ← {new_alpha_cfg['name']}")

        # 7. Update pattern views
        for pattern in practice.get("patterns", []):
            for view in pattern.get("patternViews", []):
                seq_str = str(view["seq"])

                # Add new alpha state to view if configured
                if seq_str in pattern_alpha_states:
                    state_name = pattern_alpha_states[seq_str]
                    view.setdefault("alphaStates", []).append({
                        "alphaName": new_alpha_cfg["name"],
                        "stateName": state_name
                    })
                    changes.append(f"ADD pattern view {seq_str} alphaState: {new_alpha_cfg['name']}/{state_name}")

                # Update WP LOD references
                for wpl in view.get("workProductLevels", []):
                    if wpl["workProductName"] == src_wp_name:
                        wpl["workProductName"] = revised_wp_cfg["name"]
                        old_lod = wpl["levelOfDetailName"]
                        if old_lod in lod_to_lod:
                            wpl["levelOfDetailName"] = lod_to_lod[old_lod]
                            changes.append(f"UPDATE pattern WP ref: {old_lod} → {lod_to_lod[old_lod]}")

        # 8. Update activity worksOn references
        for act in practice.get("activities", []):
            for wo in act.get("worksOn", []):
                if wo["workProductName"] == src_wp_name:
                    wo["workProductName"] = revised_wp_cfg["name"]
                    old_lod = wo["levelOfDetailName"]
                    if old_lod in lod_to_lod:
                        wo["levelOfDetailName"] = lod_to_lod[old_lod]

            # Add contributesTo for new alpha states where activity has matching LOD mapping
            if "activityAlphaContributions" in config:
                for contrib in config["activityAlphaContributions"]:
                    if contrib["activityName"] == act["name"]:
                        existing_ct = act.get("contributesTo", [])
                        for state_name in contrib["stateNames"]:
                            already_has = any(
                                c["alphaName"] == new_alpha_cfg["name"] and c["stateName"] == state_name
                                for c in existing_ct
                            )
                            if not already_has:
                                existing_ct.append({
                                    "alphaName": new_alpha_cfg["name"],
                                    "stateName": state_name
                                })
                                changes.append(f"ADD activity contributesTo: {act['name']} → {new_alpha_cfg['name']}/{state_name}")
                        act["contributesTo"] = existing_ct

        # 9. Update aliases
        for alias in practice.get("practiceElementAliases", []):
            if alias.get("practiceElementName") == src_wp_name:
                alias["practiceElementName"] = revised_wp_cfg["name"]
                changes.append(f"UPDATE alias: {src_wp_name} → {revised_wp_cfg['name']}")

        # Add alias for new alpha if configured
        if "newAlphaAlias" in config:
            practice.setdefault("practiceElementAliases", []).append({
                "practiceElementType": "Alpha",
                "practiceElementName": new_alpha_cfg["name"],
                "aliasName": config["newAlphaAlias"]
            })
            changes.append(f"ADD alias: {new_alpha_cfg['name']} → {config['newAlphaAlias']}")

        # 10. Global rename: old WP name → new WP name in ALL references
        def rename_wp_refs(obj, old_name, new_name, lod_map, path=""):
            """Recursively rename workProductName and levelOfDetailName references."""
            renames = []
            if isinstance(obj, dict):
                if obj.get("workProductName") == old_name:
                    obj["workProductName"] = new_name
                    old_lod = obj.get("levelOfDetailName", "")
                    if old_lod in lod_map:
                        obj["levelOfDetailName"] = lod_map[old_lod]
                    renames.append(path)
                for k, v in obj.items():
                    renames.extend(rename_wp_refs(v, old_name, new_name, lod_map, f"{path}.{k}"))
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    renames.extend(rename_wp_refs(v, old_name, new_name, lod_map, f"{path}[{i}]"))
            return renames

        renames = rename_wp_refs(practice, src_wp_name, revised_wp_cfg["name"], lod_to_lod)
        if renames:
            changes.append(f"RENAME WP refs in {len(renames)} locations: {src_wp_name} → {revised_wp_cfg['name']}")

    # Report
    print(json.dumps({"changes": changes, "applied": fix}, indent=2))
    return practice


def main():
    parser = argparse.ArgumentParser(description="Transform a work product into an alpha + revised work product")
    parser.add_argument("practice", help="Practice JSON file")
    parser.add_argument("--config", required=True, help="Transformation config JSON")
    parser.add_argument("--fix", action="store_true", help="Apply changes (default: dry run)")
    args = parser.parse_args()

    with open(args.practice) as f:
        practice = json.load(f)

    with open(args.config) as f:
        config = json.load(f)

    practice = transform(practice, config, fix=args.fix)

    if args.fix:
        with open(args.practice, "w") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")


if __name__ == "__main__":
    main()
