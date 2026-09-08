#!/usr/bin/env python3
"""Adopt baseline patternGroups in extension practices.

Replaces practice-local patternGroup names with canonical baseline group names.
For single-pattern practices, assigns the pattern to the appropriate baseline group.
Only emits groups that have patterns assigned (no empty baseline groups).

Usage:
    python3 utils/adopt-baseline-pattern-groups.py <practice.json> <baseline.json> [--fix]
    python3 utils/adopt-baseline-pattern-groups.py --dir <dir> <baseline.json> [--fix]
"""

import argparse
import json
import sys
from pathlib import Path


PATTERN_GROUP_ASSIGNMENTS = {
    # Account Planning (5 patterns)
    "Continuous Account Planning Journey": "Core Lifecycles",
    "Manager Coaching and Governance Cycle": "Governance & Compliance",
    "Technical Decision Point Landing Journey": "Core Lifecycles",
    "Account Transition Journey": "Strategic & Cross-Cutting Journeys",
    "IBM Co-Sell Journey": "Strategic & Cross-Cutting Journeys",

    # CRM Foundations (4 patterns)
    "CRM Adoption Journey": "Core Lifecycles",
    "Deal Execution Lifecycle": "Core Lifecycles",
    "Account Growth Strategy": "Strategic & Cross-Cutting Journeys",
    "Compliance Orchestration": "Governance & Compliance",

    # Sales Play Framework (3 patterns)
    "Play Activation Lifecycle": "Core Lifecycles",
    "TDP-Tactic Alignment Journey": "Core Lifecycles",
    "Seller Readiness Maturity Journey": "Maturity Progressions",

    # MEDDPICC (1 pattern)
    "MEDDPICC Qualification Journey": "Core Lifecycles",

    # TDPs - all are core lifecycle engagement journeys
    "AI Platform TDP Technical Engagement Journey": "Core Lifecycles",
    "App Platform Technical Engagement Journey": "Core Lifecycles",
    "Automation TDP Technical Engagement Journey": "Core Lifecycles",
    "Container Management Technical Engagement Journey": "Core Lifecycles",
    "Digital Sovereignty Advisory Journey": "Core Lifecycles",
    "Server Cloud OS Technical Engagement Journey": "Core Lifecycles",
    "Virtualization Displacement Journey": "Core Lifecycles",

    # Sales Plays - all are core lifecycle patterns
    "AI-Ready Enterprise Execution Lifecycle": "Core Lifecycles",
    "Build and Run Applications Sales Play Lifecycle": "Core Lifecycles",
    "IT Operations Play Execution Lifecycle": "Core Lifecycles",
    "Infrastructure Modernization Sales Lifecycle": "Core Lifecycles",
}


def load_baseline_groups(baseline_path: Path) -> dict:
    baseline = json.loads(baseline_path.read_text())
    groups = {}
    for pg in baseline.get("patternGroups", []):
        groups[pg["name"]] = {
            "name": pg["name"],
            "description": pg["description"],
            "seq": pg["seq"],
        }
    return groups


def adopt_groups(practice_path: Path, baseline_groups: dict, fix: bool) -> dict:
    practice = json.loads(practice_path.read_text())
    practice_name = practice.get("name", practice_path.stem)
    patterns = practice.get("patterns", [])
    pattern_names = [p["name"] for p in patterns]

    if not patterns:
        return {"file": str(practice_path), "changes": 0, "skipped": "no patterns"}

    # Build group -> entries mapping from pattern assignments
    group_entries = {}
    unassigned = []
    for pname in pattern_names:
        group_name = PATTERN_GROUP_ASSIGNMENTS.get(pname)
        if group_name:
            if group_name not in group_entries:
                group_entries[group_name] = []
            group_entries[group_name].append(pname)
        else:
            unassigned.append(pname)

    if unassigned:
        print(f"  WARNING: No assignment for patterns: {unassigned}", file=sys.stderr)
        return {"file": str(practice_path), "changes": 0, "error": f"unassigned patterns: {unassigned}"}

    # Build new patternGroups array (only groups with entries, baseline seq order)
    new_groups = []
    for group_name in sorted(group_entries.keys(), key=lambda g: baseline_groups.get(g, {}).get("seq", 99)):
        bg = baseline_groups.get(group_name)
        if not bg:
            print(f"  WARNING: Group '{group_name}' not in baseline", file=sys.stderr)
            continue

        entries = []
        for i, pname in enumerate(group_entries[group_name]):
            entries.append({"patternName": pname, "seq": i})

        new_groups.append({
            "name": bg["name"],
            "description": bg["description"],
            "seq": bg["seq"],
            "entries": entries,
        })

    old_groups = practice.get("patternGroups", [])
    old_group_names = [g["name"] for g in old_groups]
    new_group_names = [g["name"] for g in new_groups]

    changes = []
    if old_group_names != new_group_names:
        changes.append(f"groups: {old_group_names} -> {new_group_names}")
    elif not old_groups and new_groups:
        changes.append(f"added groups: {new_group_names}")

    # Check entry assignments changed
    for ng in new_groups:
        old_match = next((g for g in old_groups if g["name"] == ng["name"]), None)
        if old_match:
            old_entries = [e["patternName"] for e in old_match.get("entries", [])]
            new_entries = [e["patternName"] for e in ng["entries"]]
            if old_entries != new_entries:
                changes.append(f"  {ng['name']}: {old_entries} -> {new_entries}")

    result = {
        "file": practice_path.name,
        "practice": practice_name,
        "patterns": len(patterns),
        "old_groups": old_group_names,
        "new_groups": new_group_names,
        "changes": len(changes),
        "details": changes,
    }

    if fix and (old_groups != new_groups or not old_groups):
        practice["patternGroups"] = new_groups
        practice_path.write_text(json.dumps(practice, indent=2, ensure_ascii=False) + "\n")
        result["applied"] = True

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="Practice JSON file")
    parser.add_argument("baseline", help="Baseline JSON file")
    parser.add_argument("--dir", help="Process all practice JSONs in directory")
    parser.add_argument("--fix", action="store_true", help="Apply changes in-place")
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    baseline_groups = load_baseline_groups(baseline_path)

    if not baseline_groups:
        print("ERROR: Baseline has no patternGroups", file=sys.stderr)
        sys.exit(1)

    print(f"Baseline groups: {list(baseline_groups.keys())}")
    print()

    files = []
    if args.dir:
        dir_path = Path(args.dir)
        for f in sorted(dir_path.glob("*.json")):
            try:
                d = json.loads(f.read_text())
                if isinstance(d, dict) and d.get("kind") == "practice":
                    files.append(f)
            except (json.JSONDecodeError, KeyError):
                pass
    elif args.file:
        files.append(Path(args.file))

    total_changes = 0
    for f in files:
        result = adopt_groups(f, baseline_groups, args.fix)
        status = "APPLIED" if result.get("applied") else ("DRY-RUN" if result.get("changes") else "OK")
        print(f"{status} {result['file']}: {result.get('practice', '?')}")
        if result.get("details"):
            for d in result["details"]:
                print(f"  {d}")
        total_changes += result.get("changes", 0)

    print(f"\nTotal changes: {total_changes}")
    if not args.fix and total_changes:
        print("Run with --fix to apply")


if __name__ == "__main__":
    main()
