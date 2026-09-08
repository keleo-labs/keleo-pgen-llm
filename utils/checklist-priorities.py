#!/usr/bin/env python3
"""Extract checklist items for priority review and apply priority assignments.

Two modes:
  extract  — Dump every checklist item from a practice JSON as a compact
              inventory suitable for priority review by a human or LLM.
  apply    — Read a priority-assignment JSON and patch the practice JSON.

Extract mode
------------
    python3 utils/checklist-priorities.py extract practice.json [-o inventory.json]

Produces a JSON with structure:
    {
      "practice": "Account Planning",
      "totalItems": 270,
      "alphas": [
        {
          "name": "Account Plan",
          "states": [
            {
              "name": "Identified",
              "description": "...",
              "items": [
                {"seq": 1, "name": "...", "description": "...", "currentPriority": null},
                ...
              ]
            }
          ]
        }
      ],
      "workProducts": [
        {
          "name": "Account Plan Document",
          "levelsOfDetail": [
            {
              "name": "Starter",
              "description": "...",
              "items": [
                {"seq": 1, "name": "...", "description": "...", "currentPriority": null}
              ]
            }
          ]
        }
      ]
    }

Apply mode
----------
    python3 utils/checklist-priorities.py apply practice.json assignments.json [--fix]

The assignments JSON maps checklist items to priorities:
    {
      "assignments": [
        {
          "alpha": "Account Plan",
          "state": "Identified",
          "item": "Account ownership confirmed",
          "priority": "should"
        },
        {
          "alpha": null,
          "workProduct": "Account Plan Document",
          "lod": "Starter",
          "item": "Basic fields populated",
          "priority": "could"
        }
      ],
      "fixes": [
        {
          "alpha": "Account Plan",
          "state": "Active",
          "item": "Metrics absent",
          "newName": "Key Metrics Defined",
          "newDescription": "Performance metrics identified and baselined"
        }
      ]
    }

Only items with "should" or "could" need to be listed — unlisted items
default to "must" (i.e., priority is omitted from the JSON, per schema
guidance).

With --fix, writes changes in place.  Without --fix, prints a dry-run
summary of what would change.
"""

import argparse
import json
import sys
from pathlib import Path

# Allow import from utils/ when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def extract_checklists(practice: dict) -> dict:
    """Extract all checklist items in compact inventory format."""
    result = {
        "practice": practice.get("name", "Unknown"),
        "totalItems": 0,
        "alphas": [],
        "workProducts": [],
    }

    for alpha in practice.get("alphas", []):
        alpha_entry = {"name": alpha["name"], "states": []}
        for state in alpha.get("states", []):
            items = []
            for cl in state.get("checklist", []):
                items.append({
                    "seq": cl.get("seq"),
                    "name": cl.get("name", ""),
                    "description": cl.get("description", ""),
                    "currentPriority": cl.get("priority"),
                })
                result["totalItems"] += 1
            if items:
                alpha_entry["states"].append({
                    "name": state["name"],
                    "description": state.get("description", ""),
                    "items": items,
                })
        if alpha_entry["states"]:
            result["alphas"].append(alpha_entry)

    for wp in practice.get("workProducts", []):
        wp_entry = {"name": wp["name"], "levelsOfDetail": []}
        for lod in wp.get("levelsOfDetail", []):
            items = []
            for cl in lod.get("checklist", []):
                items.append({
                    "seq": cl.get("seq"),
                    "name": cl.get("name", ""),
                    "description": cl.get("description", ""),
                    "currentPriority": cl.get("priority"),
                })
                result["totalItems"] += 1
            if items:
                wp_entry["levelsOfDetail"].append({
                    "name": lod["name"],
                    "description": lod.get("description", ""),
                    "items": items,
                })
        if wp_entry["levelsOfDetail"]:
            result["workProducts"].append(wp_entry)

    return result


def apply_assignments(practice: dict, assignments_data: dict, fix: bool) -> dict:
    """Apply priority assignments and fixes to a practice JSON.

    Returns a summary dict with counts of changes made/would-be-made.
    """
    assignments = assignments_data.get("assignments", [])
    fixes = assignments_data.get("fixes", [])

    # Build lookup maps — handle variant formats from different agents
    priority_map = {}  # (alpha_or_wp, state_or_lod, item_name) -> priority
    for a in assignments:
        container = a.get("alpha") or a.get("workProduct") or a.get("container") or a.get("element", "")
        level = a.get("state") or a.get("lod") or a.get("parent", "")
        item = a.get("item") or a.get("name", "")
        priority = a.get("priority")
        if container and level and item and priority:
            priority_map[(container, level, item)] = priority

    fix_map = {}  # (alpha_or_wp, state_or_lod, item_name) -> {newName, newDescription}
    for f in fixes:
        container = f.get("alpha") or f.get("workProduct") or f.get("container") or f.get("element", "")
        level = f.get("state") or f.get("lod") or f.get("parent", "")
        item = f.get("item") or f.get("name") or f.get("oldName") or f.get("currentName", "")
        fix_entry = {}
        if "newName" in f:
            fix_entry["newName"] = f["newName"]
        elif "fixedName" in f:
            fix_entry["newName"] = f["fixedName"]
        if "newDescription" in f:
            fix_entry["newDescription"] = f["newDescription"]
        elif "fixedDescription" in f:
            fix_entry["newDescription"] = f["fixedDescription"]
        if container and level and item and fix_entry:
            fix_map[(container, level, item)] = fix_entry

    summary = {
        "prioritiesSet": 0,
        "prioritiesRemoved": 0,
        "checklistsFixed": 0,
        "unmatched": [],
    }

    # Track which assignments were used
    used_priorities = set()
    used_fixes = set()

    def process_checklists(container_name, level_name, checklist):
        for cl in checklist:
            item_name = cl.get("name", "")
            key = (container_name, level_name, item_name)

            # Apply priority
            if key in priority_map:
                priority = priority_map[key]
                used_priorities.add(key)
                if priority in ("should", "could"):
                    if cl.get("priority") != priority:
                        if fix:
                            cl["priority"] = priority
                        summary["prioritiesSet"] += 1
                elif priority == "must":
                    if "priority" in cl:
                        if fix:
                            del cl["priority"]
                        summary["prioritiesRemoved"] += 1

            # Apply fixes
            if key in fix_map:
                used_fixes.add(key)
                f = fix_map[key]
                if "newName" in f and cl.get("name") != f["newName"]:
                    if fix:
                        cl["name"] = f["newName"]
                    summary["checklistsFixed"] += 1
                if "newDescription" in f and cl.get("description") != f["newDescription"]:
                    if fix:
                        cl["description"] = f["newDescription"]

    for alpha in practice.get("alphas", []):
        for state in alpha.get("states", []):
            process_checklists(alpha["name"], state["name"], state.get("checklist", []))

    for wp in practice.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            process_checklists(wp["name"], lod["name"], lod.get("checklist", []))

    # Report unmatched assignments
    for key in set(priority_map.keys()) - used_priorities:
        summary["unmatched"].append({"type": "priority", "key": list(key)})
    for key in set(fix_map.keys()) - used_fixes:
        summary["unmatched"].append({"type": "fix", "key": list(key)})

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Extract checklist items or apply priority assignments"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Extract subcommand
    extract_parser = subparsers.add_parser("extract", help="Extract checklist inventory")
    extract_parser.add_argument("practice", help="Practice JSON file")
    extract_parser.add_argument("-o", "--output", help="Output file (default: stdout)")

    # Apply subcommand
    apply_parser = subparsers.add_parser("apply", help="Apply priority assignments")
    apply_parser.add_argument("practice", help="Practice JSON file")
    apply_parser.add_argument("assignments", help="Assignments JSON file")
    apply_parser.add_argument("--fix", action="store_true", help="Write changes in place")

    args = parser.parse_args()

    if args.command == "extract":
        practice = load_json(args.practice)
        inventory = extract_checklists(practice)
        output = json.dumps(inventory, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(json.dumps({
                "extracted": args.practice,
                "totalItems": inventory["totalItems"],
                "alphaCount": len(inventory["alphas"]),
                "workProductCount": len(inventory["workProducts"]),
                "output": args.output,
            }))
        else:
            print(output)

    elif args.command == "apply":
        practice = load_json(args.practice)
        assignments_data = load_json(args.assignments)
        summary = apply_assignments(practice, assignments_data, fix=args.fix)

        if args.fix:
            with open(args.practice, "w", encoding="utf-8") as f:
                json.dump(practice, f, indent=2, ensure_ascii=False)
                f.write("\n")

        print(json.dumps({
            "file": args.practice,
            "mode": "applied" if args.fix else "dry-run",
            **summary,
        }, indent=2))


if __name__ == "__main__":
    main()
