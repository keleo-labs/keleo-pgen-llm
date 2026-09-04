#!/usr/bin/env python3
"""Add canonical patternGroups to baseline practice JSONs.

PatternGroups are defined at root baselines and inherited down the
dependency tree.  Each group has empty entries — extension practices
populate them.

Usage:
    python3 utils/add-baseline-pattern-groups.py <baseline.json> [--tree <tree>] [--dry-run]
    python3 utils/add-baseline-pattern-groups.py --all [--dry-run]

Options:
    --tree      Override tree detection (project|sales|horticulture|digital-transformation)
    --dry-run   Print changes without writing
    --all       Process all known baselines
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── Canonical group definitions per tree ──────────────────────────

COMMON_GROUPS = [
    {
        "name": "Core Lifecycles",
        "description": "Primary end-to-end lifecycle patterns coordinating the main value stream from initiation through completion or retirement.",
        "entries": [],
        "seq": 0,
    },
    {
        "name": "Maturity Progressions",
        "description": "Patterns tracking incremental capability growth along a maturity axis, measuring depth of practice adoption rather than progress through lifecycle stages.",
        "entries": [],
        "seq": 1,
    },
]

OPTIMISATION_GROUP = {
    "name": "Optimisation Cycles",
    "description": "Iterative improvement patterns that refine existing capabilities through structured feedback loops and continuous learning.",
    "entries": [],
    "seq": 2,
}

STRATEGIC_GROUP = {
    "name": "Strategic & Cross-Cutting Journeys",
    "description": "Patterns coordinating multiple concerns across engagements, accounts, or customer segments that span practice boundaries.",
    "entries": [],
    "seq": 2,
}

GOVERNANCE_GROUP = {
    "name": "Governance & Compliance",
    "description": "Patterns coordinating oversight, risk management, policy enforcement, and stakeholder accountability across the engagement lifecycle.",
    "entries": [],
    "seq": 3,
}

TREES = {
    "project": COMMON_GROUPS + [OPTIMISATION_GROUP, GOVERNANCE_GROUP],
    "sales": COMMON_GROUPS + [STRATEGIC_GROUP, GOVERNANCE_GROUP],
    "horticulture": COMMON_GROUPS + [OPTIMISATION_GROUP, GOVERNANCE_GROUP],
    "digital-transformation": COMMON_GROUPS + [OPTIMISATION_GROUP, GOVERNANCE_GROUP],
}

# ── Tree detection by name or dependency ──────────────────────────

TREE_MAP = {
    "Project Essentials": "project",
    "Programme Essentials": "project",
    "Platform Adoption Essentials": "project",
    "IDP Essentials": "project",
    "Infrastructure Automation Essentials": "project",
    "Red Hat Sales Essentials": "sales",
    "Partner Ecosystem Essentials": "sales",
    "Horticulture Essentials": "horticulture",
    "Digital Transformation Essentials": "digital-transformation",
}


def detect_tree(data: dict) -> str | None:
    name = data.get("name", "")
    if name in TREE_MAP:
        return TREE_MAP[name]
    return None


def bump_minor(version: str) -> str:
    parts = version.split(".")
    if len(parts) >= 2:
        parts[1] = str(int(parts[1]) + 1)
        if len(parts) >= 3:
            parts[2] = "0"
    return ".".join(parts)


def add_pattern_groups(filepath: Path, tree_override: str | None = None, dry_run: bool = False) -> bool:
    with open(filepath) as f:
        data = json.load(f)

    if data.get("kind") != "practiceBaseline":
        print(f"  SKIP {filepath.name}: not a practiceBaseline (kind={data.get('kind')})")
        return False

    tree = tree_override or detect_tree(data)
    if not tree:
        print(f"  SKIP {filepath.name}: cannot determine tree for '{data.get('name')}'")
        return False

    groups = TREES[tree]
    existing = {pg.get("name") for pg in data.get("patternGroups", [])}
    new_groups = [g for g in groups if g["name"] not in existing]

    if not new_groups:
        print(f"  SKIP {filepath.name}: all canonical groups already present")
        return False

    if "patternGroups" not in data:
        data["patternGroups"] = []
    data["patternGroups"].extend(new_groups)
    data["patternGroups"].sort(key=lambda g: g.get("seq", 999))

    old_version = data.get("version", "1.0.0")
    new_version = bump_minor(old_version)
    data["version"] = new_version

    data["schemaVersion"] = "2.5.0"

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


def find_all_baselines() -> list[Path]:
    base = Path(__file__).resolve().parent.parent
    paths = []

    baselines_dir = base / "baselines"
    if baselines_dir.exists():
        for d in sorted(baselines_dir.iterdir()):
            if d.is_dir():
                for f in sorted(d.glob("*.json")):
                    if not f.name.startswith("_") and "backup" not in f.name:
                        paths.append(f)

    deps_dir = base / "deps"
    if deps_dir.exists():
        for f in sorted(deps_dir.glob("*.json")):
            if f.name != "language.schema.json" and not f.name.startswith("_"):
                paths.append(f)

    return paths


def main():
    parser = argparse.ArgumentParser(description="Add canonical patternGroups to baseline JSONs")
    parser.add_argument("files", nargs="*", help="Baseline JSON files to process")
    parser.add_argument("--tree", choices=list(TREES.keys()), help="Override tree detection")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--all", action="store_true", help="Process all known baselines")
    args = parser.parse_args()

    if args.all:
        files = find_all_baselines()
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    updated = 0
    for filepath in files:
        if not filepath.exists():
            print(f"  ERROR: {filepath} not found")
            continue
        if add_pattern_groups(filepath, args.tree, args.dry_run):
            updated += 1

    print(f"\n{'Would update' if args.dry_run else 'Updated'} {updated}/{len(files)} files")


if __name__ == "__main__":
    main()
