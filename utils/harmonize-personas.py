#!/usr/bin/env python3
"""Harmonize personas across practice dependency chains.

Ensures that redeclared personas (same name as dependency persona) do not
narrow scope — competencies from dependencies are preserved, and missing
ones are added. Also detects personaGroup composition opportunities.

Usage:
    python3 utils/harmonize-personas.py <practice.json> --deps <dep1.json> [dep2.json ...]
    python3 utils/harmonize-personas.py <practice.json> --deps <dep1.json> --fix
    python3 utils/harmonize-personas.py <practice.json> --deps <dep1.json> --json
"""

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import load_json


COMPETENCY_LEVEL_ORDER = [
    "Assists", "Basic", "Applies", "Masters", "Adapts", "Innovates", "Innovating",
]


def level_rank(level_name):
    try:
        return COMPETENCY_LEVEL_ORDER.index(level_name)
    except ValueError:
        return -1


def build_persona_index(sources):
    """Build name -> richest persona definition across all sources."""
    index = {}
    for source in sources:
        for persona in source.get("personas", []):
            name = persona.get("name", "")
            if not name:
                continue
            if name not in index:
                index[name] = copy.deepcopy(persona)
            else:
                existing = index[name]
                existing_comps = {
                    c["competencyName"]: c
                    for c in existing.get("competencies", [])
                }
                for comp in persona.get("competencies", []):
                    cn = comp["competencyName"]
                    if cn not in existing_comps:
                        existing.setdefault("competencies", []).append(
                            copy.deepcopy(comp)
                        )
                        existing_comps[cn] = comp
                    else:
                        old_rank = level_rank(
                            existing_comps[cn].get("competencyLevelName", "")
                        )
                        new_rank = level_rank(
                            comp.get("competencyLevelName", "")
                        )
                        if new_rank > old_rank:
                            existing_comps[cn]["competencyLevelName"] = comp[
                                "competencyLevelName"
                            ]
    return index


def build_group_index(sources):
    """Build name -> group definition across all sources."""
    index = {}
    for source in sources:
        for group in source.get("personaGroups", []):
            name = group.get("name", "")
            if name and name not in index:
                index[name] = copy.deepcopy(group)
    return index


def harmonize_personas(practice, dep_persona_index):
    """Harmonize practice personas against dependency persona index.

    Returns (updated_personas, changes) where changes is a list of dicts
    describing what was modified.
    """
    changes = []
    updated = []

    for persona in practice.get("personas", []):
        name = persona.get("name", "")
        p = copy.deepcopy(persona)

        if name in dep_persona_index:
            dep = dep_persona_index[name]
            dep_comps = {
                c["competencyName"]: c for c in dep.get("competencies", [])
            }
            practice_comps = {
                c["competencyName"]: c for c in p.get("competencies", [])
            }

            added_comps = []
            upgraded_comps = []

            for cn, dep_comp in dep_comps.items():
                if cn not in practice_comps:
                    p.setdefault("competencies", []).append(
                        copy.deepcopy(dep_comp)
                    )
                    added_comps.append(
                        f"{cn}: {dep_comp['competencyLevelName']}"
                    )
                else:
                    old_level = practice_comps[cn].get(
                        "competencyLevelName", ""
                    )
                    dep_level = dep_comp.get("competencyLevelName", "")
                    if level_rank(dep_level) > level_rank(old_level):
                        for c in p["competencies"]:
                            if c["competencyName"] == cn:
                                c["competencyLevelName"] = dep_level
                                break
                        upgraded_comps.append(
                            f"{cn}: {old_level} -> {dep_level}"
                        )

            if added_comps or upgraded_comps:
                change = {
                    "persona": name,
                    "type": "redeclaration",
                    "added_competencies": added_comps,
                    "upgraded_competencies": upgraded_comps,
                }
                changes.append(change)
            else:
                changes.append({
                    "persona": name,
                    "type": "redeclaration",
                    "status": "already_harmonized",
                })
        else:
            changes.append({"persona": name, "type": "new"})

        updated.append(p)

    return updated, changes


def detect_group_composition(practice, dep_group_index):
    """Detect personaGroup composition opportunities."""
    suggestions = []
    for group in practice.get("personaGroups", []):
        name = group.get("name", "")
        members = set(group.get("personaNames", []))
        existing_sub = group.get("personaGroupNames", [])

        for dep_name, dep_group in dep_group_index.items():
            if dep_name == name:
                continue
            dep_members = set(dep_group.get("personaNames", []))
            if dep_members and dep_members.issubset(members) and len(dep_members) >= 2:
                remaining = members - dep_members
                suggestions.append({
                    "group": name,
                    "can_include": dep_name,
                    "dep_members": sorted(dep_members),
                    "remaining_direct": sorted(remaining),
                    "already_uses_groupnames": bool(existing_sub),
                })

    return suggestions


def main():
    parser = argparse.ArgumentParser(
        description="Harmonize personas across practice dependencies"
    )
    parser.add_argument("practice", help="Practice JSON file to harmonize")
    parser.add_argument(
        "--deps",
        nargs="+",
        required=True,
        help="Dependency practice JSON files",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply changes to the file (default: dry-run report)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output report as JSON",
    )
    args = parser.parse_args()

    practice = load_json(args.practice)
    deps = [load_json(d) for d in args.deps]

    dep_persona_index = build_persona_index(deps)
    dep_group_index = build_group_index(deps)

    updated_personas, persona_changes = harmonize_personas(
        practice, dep_persona_index
    )
    group_suggestions = detect_group_composition(practice, dep_group_index)

    report = {
        "practice": practice.get("name", Path(args.practice).stem),
        "persona_changes": persona_changes,
        "group_composition_suggestions": group_suggestions,
    }

    if args.json_output or not args.fix:
        print(json.dumps(report, indent=2))

    if args.fix:
        practice["personas"] = updated_personas
        with open(args.practice, "w", encoding="utf-8") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")

        modified = sum(
            1
            for c in persona_changes
            if c.get("added_competencies") or c.get("upgraded_competencies")
        )
        if not args.json_output:
            print(
                f"Updated {modified} persona(s) in "
                f"{Path(args.practice).name}"
            )
    elif not args.json_output:
        would_modify = sum(
            1
            for c in persona_changes
            if c.get("added_competencies") or c.get("upgraded_competencies")
        )
        print(f"Would update {would_modify} persona(s) (dry run)")


if __name__ == "__main__":
    main()
