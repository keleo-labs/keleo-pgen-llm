#!/usr/bin/env python3
"""Manage patternGroups for baselines and extension practices.

Auto-detects mode based on the target's kind field:
  - practiceBaseline: Init mode — add canonical group definitions
  - practice/method:  Adopt mode — adopt baseline groups and assign patterns

Usage:
    # Init baseline groups (auto-detects tree from config or baseline name)
    python3 utils/manage-pattern-groups.py <baseline.json> --groups <groups.json> [--fix]

    # Adopt baseline groups in extension practice
    python3 utils/manage-pattern-groups.py <practice.json> <baseline.json> --assignments <map.json> [--fix]

    # Batch mode for extensions
    python3 utils/manage-pattern-groups.py --dir <dir> <baseline.json> --assignments <map.json> [--fix]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, increment_version


# ── Init mode: add canonical groups to baselines ────────────────


def init_baseline_groups(filepath, groups_config, dry_run=False):
    data = load_json(str(filepath))

    if data.get("kind") != "practiceBaseline":
        print(f"  SKIP {filepath.name}: not a practiceBaseline (kind={data.get('kind')})")
        return False

    groups = groups_config if isinstance(groups_config, list) else groups_config.get("groups", [])
    existing = {pg.get("name") for pg in data.get("patternGroups", [])}
    new_groups = [g for g in groups if g["name"] not in existing]

    if not new_groups:
        print(f"  SKIP {filepath.name}: all groups already present")
        return False

    if "patternGroups" not in data:
        data["patternGroups"] = []
    data["patternGroups"].extend(new_groups)
    data["patternGroups"].sort(key=lambda g: g.get("seq", 999))

    old_version = data.get("version", "1.0.0")
    new_version = increment_version(old_version, "minor")
    data["version"] = new_version

    if dry_run:
        group_names = ", ".join(g["name"] for g in new_groups)
        print(f"  DRY-RUN {filepath.name}: would add [{group_names}], version {old_version} → {new_version}")
        return True

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    group_names = ", ".join(g["name"] for g in new_groups)
    print(f"  UPDATED {filepath.name}: added [{group_names}], version {old_version} → {new_version}")
    return True


# ── Adopt mode: assign patterns to baseline groups ──────────────


def load_baseline_groups(baseline_path):
    baseline = load_json(str(baseline_path))
    groups = {}
    for pg in baseline.get("patternGroups", []):
        groups[pg["name"]] = {
            "name": pg["name"],
            "description": pg["description"],
            "seq": pg["seq"],
        }
    return groups


def adopt_groups(practice_path, baseline_groups, assignments, fix):
    practice = load_json(str(practice_path))
    practice_name = practice.get("name", practice_path.stem)
    patterns = practice.get("patterns", [])
    pattern_names = [p["name"] for p in patterns]

    if not patterns:
        return {"file": str(practice_path), "changes": 0, "skipped": "no patterns"}

    group_entries = {}
    unassigned = []
    for pname in pattern_names:
        group_name = assignments.get(pname)
        if group_name:
            if group_name not in group_entries:
                group_entries[group_name] = []
            group_entries[group_name].append(pname)
        else:
            unassigned.append(pname)

    if unassigned:
        print(f"  WARNING: No assignment for patterns: {unassigned}", file=sys.stderr)
        return {"file": str(practice_path), "changes": 0, "error": f"unassigned patterns: {unassigned}"}

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
        with open(practice_path, "w") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")
        result["applied"] = True

    return result


# ── Main ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", nargs="?", help="Target JSON file (baseline or practice)")
    parser.add_argument("baseline", nargs="?", help="Baseline JSON file (for adopt mode)")
    parser.add_argument("--dir", help="Process all practice JSONs in directory (adopt mode)")
    parser.add_argument(
        "--groups",
        help="JSON file with group definitions for init mode (array of {name, description, entries, seq})",
    )
    parser.add_argument(
        "--assignments",
        help='JSON file mapping pattern names to group names ({"Pattern Name": "Group Name"})',
    )
    parser.add_argument("--fix", action="store_true", help="Apply changes in-place")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.print_help()
        sys.exit(1)

    # Auto-detect mode from target kind
    if args.file:
        target = load_json(args.file)
        kind = target.get("kind", "")
    elif args.dir:
        kind = "practice"
    else:
        kind = ""

    if kind == "practiceBaseline":
        # Init mode
        if not args.groups:
            print("ERROR: --groups required for baseline init mode", file=sys.stderr)
            sys.exit(1)
        with open(args.groups) as f:
            groups_config = json.load(f)
        init_baseline_groups(Path(args.file), groups_config, dry_run=args.dry_run or not args.fix)

    else:
        # Adopt mode
        if not args.baseline and not args.dir:
            print("ERROR: baseline argument required for adopt mode", file=sys.stderr)
            sys.exit(1)

        baseline_path = Path(args.baseline) if args.baseline else None
        if not baseline_path or not baseline_path.exists():
            print(f"ERROR: Baseline not found: {args.baseline}", file=sys.stderr)
            sys.exit(1)

        baseline_groups = load_baseline_groups(baseline_path)
        if not baseline_groups:
            print("ERROR: Baseline has no patternGroups", file=sys.stderr)
            sys.exit(1)

        if not args.assignments:
            print("ERROR: --assignments required for adopt mode", file=sys.stderr)
            print('Provide a JSON file: {"Pattern Name": "Group Name", ...}', file=sys.stderr)
            sys.exit(1)

        with open(args.assignments) as f:
            assignments = json.load(f)

        print(f"Baseline groups: {list(baseline_groups.keys())}")
        print()

        files = []
        if args.dir:
            dir_path = Path(args.dir)
            for fp in sorted(dir_path.glob("*.json")):
                try:
                    d = json.loads(fp.read_text())
                    if isinstance(d, dict) and d.get("kind") in ("practice", "method"):
                        files.append(fp)
                except (json.JSONDecodeError, KeyError):
                    pass
        elif args.file:
            files.append(Path(args.file))

        total_changes = 0
        for fp in files:
            result = adopt_groups(fp, baseline_groups, assignments, args.fix)
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
