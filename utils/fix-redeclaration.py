#!/usr/bin/env python3
"""Fix alpha redeclaration compliance in extension practice JSON.

Restores baseline descriptions and state descriptions for redeclared alphas,
and merges checklists (baseline items first, practice-specific items appended).

Usage:
    python3 utils/fix-redeclaration.py <practice.json> <baseline.json>         # dry-run
    python3 utils/fix-redeclaration.py <practice.json> <baseline.json> --fix   # apply in-place
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def find_redeclared_alphas(practice, baseline):
    baseline_names = {a["name"] for a in baseline.get("alphas", [])}
    redeclared = []
    for alpha in practice.get("alphas", []):
        if alpha["name"] in baseline_names and not alpha.get("contributesTo"):
            redeclared.append(alpha["name"])
    return redeclared


def merge_checklists(baseline_checklist, practice_checklist):
    baseline_names_lower = {c["name"].lower() for c in baseline_checklist}
    merged = list(baseline_checklist)
    next_seq = max((c["seq"] for c in baseline_checklist), default=0) + 1
    for item in practice_checklist:
        if item["name"].lower() not in baseline_names_lower:
            new_item = dict(item)
            new_item["seq"] = next_seq
            merged.append(new_item)
            next_seq += 1
    return merged


def fix_redeclarations(practice, baseline):
    changes = []
    baseline_alphas = {a["name"]: a for a in baseline.get("alphas", [])}
    redeclared_names = find_redeclared_alphas(practice, baseline)

    for alpha in practice.get("alphas", []):
        if alpha["name"] not in redeclared_names:
            continue

        ba = baseline_alphas[alpha["name"]]

        if alpha.get("description") != ba.get("description"):
            changes.append({
                "alpha": alpha["name"],
                "field": "description",
                "old": alpha["description"][:80] + "...",
                "new": ba["description"][:80] + "...",
            })
            alpha["description"] = ba["description"]

        baseline_states = {s["name"]: s for s in ba.get("states", [])}
        for state in alpha.get("states", []):
            bs = baseline_states.get(state["name"])
            if not bs:
                continue

            if state.get("description") != bs.get("description"):
                changes.append({
                    "alpha": alpha["name"],
                    "field": f"states[{state['name']}].description",
                    "old": state["description"][:60] + "...",
                    "new": bs["description"][:60] + "...",
                })
                state["description"] = bs["description"]

            bc = bs.get("checklist", [])
            pc = state.get("checklist", [])
            bc_names = {c["name"] for c in bc}
            pc_names = {c["name"] for c in pc}

            missing = bc_names - {c["name"] for c in pc if c["name"] in bc_names}
            # Only if baseline items are missing
            if bc_names - pc_names or pc_names - bc_names:
                merged = merge_checklists(bc, pc)
                added_count = len(merged) - len(bc)
                changes.append({
                    "alpha": alpha["name"],
                    "field": f"states[{state['name']}].checklist",
                    "action": f"merged: {len(bc)} baseline + {added_count} practice-specific = {len(merged)} total",
                })
                state["checklist"] = merged

    return changes


def main():
    parser = argparse.ArgumentParser(description="Fix alpha redeclaration compliance")
    parser.add_argument("file", help="Practice JSON file")
    parser.add_argument("baseline", help="Baseline or effective-baseline JSON file")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place")
    args = parser.parse_args()

    practice = load_json(args.file)
    baseline = load_json(args.baseline)

    redeclared = find_redeclared_alphas(practice, baseline)
    if not redeclared:
        print(json.dumps({"redeclaredAlphas": [], "changes": [], "message": "No redeclared alphas found"}))
        return

    changes = fix_redeclarations(practice, baseline)

    if args.fix and changes:
        with open(args.file, "w", encoding="utf-8") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")

    result = {
        "redeclaredAlphas": redeclared,
        "changesApplied": len(changes),
        "dryRun": not args.fix,
        "changes": changes,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
