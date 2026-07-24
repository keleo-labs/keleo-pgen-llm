#!/usr/bin/env python3
"""
Baseline Dependency Resolver

Resolves baseline practice dependencies and creates an effective baseline
by merging parent baselines in dependency order, then annotating with
alias context from practiceElementAliases.

Usage:
    python3 utils/resolve-baseline.py <baseline.json> [<dep1.json> <dep2.json> ...] -o <output.json>

The script:
1. Reads the target baseline and checks for baselinePracticeNames
2. If dependencies exist, merges provided dependency files in order (root-first)
3. Layers the target baseline on top of the merged parent
4. Applies practiceElementAliases as _aliasContext annotations
5. Writes the effective baseline to the output path

The effective baseline keeps canonical names in all structural positions
but adds _domainAlias and _aliasContext annotations so LLM agents can
understand domain-specific terminology during analysis and mapping.

Exit codes:
    0 - Success
    1 - Error (missing files, unresolved dependencies, etc.)

Outputs structured JSON report to stdout.
"""

import json
import sys
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, merge_by_name, MERGEABLE_ARRAYS


def merge_baselines(parent: Dict, child: Dict) -> Dict:
    """Merge parent and child baselines. Child overrides parent for same-name elements."""
    result = copy.deepcopy(child)

    for key in MERGEABLE_ARRAYS:
        parent_items = parent.get(key, [])
        child_items = child.get(key, [])
        if parent_items or child_items:
            result[key] = merge_by_name(parent_items, child_items)

    return result


def apply_alias_context(effective: Dict, aliases: List[Dict]) -> Dict:
    """Add _aliasContext and _domainAlias annotations from practiceElementAliases."""
    if not aliases:
        return effective

    alias_context = {
        "description": (
            "Domain-specific terminology from baseline aliases. "
            "Use these terms for semantic understanding during analysis and mapping. "
            "Always use canonical names (canonicalName) in structural references "
            "(contributesTo, alphaName, stateName, competencyName, etc.)."
        ),
        "aliases": [
            {
                "type": a.get("practiceElementType", ""),
                "canonicalName": a.get("practiceElementName", ""),
                "domainName": a.get("aliasName", "")
            }
            for a in aliases
        ]
    }
    effective["_aliasContext"] = alias_context

    alias_lookup = {}
    for a in aliases:
        element_type = a.get("practiceElementType", "")
        canonical = a.get("practiceElementName", "")
        domain = a.get("aliasName", "")
        alias_lookup.setdefault(element_type, {})[canonical] = domain

    type_to_array = {
        "Alpha": "alphas",
        "ActivitySpace": "activitySpaces",
        "Competency": "competencies",
        "Focus": "focuses",
        "NarrativeType": "narrativeTypes",
        "Narrative": "narratives",
    }

    for element_type, array_key in type_to_array.items():
        if element_type in alias_lookup and array_key in effective:
            for item in effective[array_key]:
                name = item.get("name", "")
                if name in alias_lookup[element_type]:
                    item["_domainAlias"] = alias_lookup[element_type][name]

    return effective


def resolve_dependencies(
    baseline_path: Path,
    dep_paths: List[Path]
) -> tuple:
    """
    Resolve baseline dependencies.

    Returns (effective_baseline, report_dict).
    """
    baseline = load_json(baseline_path)
    dep_names = baseline.get("baselinePracticeNames", [])

    if not dep_names:
        return baseline, {
            "success": True,
            "hasDependencies": False,
            "message": "No baseline dependencies to resolve."
        }

    dep_files = {}
    for dep_path in dep_paths:
        dep_data = load_json(dep_path)
        dep_name = dep_data.get("name", "")
        dep_files[dep_name] = (dep_path, dep_data)

    unresolved = [name for name in dep_names if name not in dep_files]
    if unresolved:
        return None, {
            "success": False,
            "hasDependencies": True,
            "dependencyNames": dep_names,
            "unresolvedDependencies": unresolved,
            "error": (
                f"Unresolved baseline dependencies: {unresolved}. "
                f"Provide the JSON files for these baselines."
            )
        }

    merge_order = []
    resolved_names = set()

    def resolve_chain(name: str):
        if name in resolved_names:
            return
        if name not in dep_files:
            return
        _, dep_data = dep_files[name]
        transitive = dep_data.get("baselinePracticeNames", [])
        for t_name in transitive:
            resolve_chain(t_name)
        resolved_names.add(name)
        merge_order.append(name)

    for name in dep_names:
        resolve_chain(name)

    effective = None
    for name in merge_order:
        _, dep_data = dep_files[name]
        if effective is None:
            effective = copy.deepcopy(dep_data)
        else:
            effective = merge_baselines(effective, dep_data)

    effective = merge_baselines(effective, baseline)

    all_aliases = []
    for name in merge_order:
        _, dep_data = dep_files[name]
        all_aliases.extend(dep_data.get("practiceElementAliases", []))
    all_aliases.extend(baseline.get("practiceElementAliases", []))

    effective = apply_alias_context(effective, all_aliases)

    alias_summary = [
        {"canonicalName": a["canonicalName"], "domainName": a["domainName"]}
        for a in effective.get("_aliasContext", {}).get("aliases", [])
    ]

    report = {
        "success": True,
        "hasDependencies": True,
        "dependencyNames": dep_names,
        "mergeOrder": merge_order,
        "effectiveBaseline": {
            "name": effective.get("name", ""),
            "alphaCount": len(effective.get("alphas", [])),
            "activitySpaceCount": len(effective.get("activitySpaces", [])),
            "competencyCount": len(effective.get("competencies", [])),
            "focusCount": len(effective.get("focuses", [])),
            "aliasCount": len(alias_summary),
            "aliasedElements": alias_summary
        }
    }

    return effective, report


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Resolve baseline practice dependencies and create effective baseline"
    )
    parser.add_argument(
        "baseline",
        help="Path to the target baseline practice JSON"
    )
    parser.add_argument(
        "dependencies",
        nargs="*",
        help="Paths to dependency baseline JSON files (order does not matter)"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output path for the effective baseline JSON"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for dependencies, don't merge (reports dependency names)"
    )

    args = parser.parse_args()
    baseline_path = Path(args.baseline)

    if args.check_only:
        baseline = load_json(baseline_path)
        dep_names = baseline.get("baselinePracticeNames", [])
        aliases = baseline.get("practiceElementAliases", [])
        print(json.dumps({
            "success": True,
            "hasDependencies": bool(dep_names),
            "dependencyNames": dep_names,
            "aliasCount": len(aliases),
            "aliases": [
                {
                    "type": a.get("practiceElementType", ""),
                    "canonicalName": a.get("practiceElementName", ""),
                    "domainName": a.get("aliasName", "")
                }
                for a in aliases
            ]
        }, indent=2))
        return

    dep_paths = [Path(p) for p in args.dependencies]
    effective, report = resolve_dependencies(baseline_path, dep_paths)

    if not report["success"]:
        print(json.dumps(report, indent=2))
        sys.exit(1)

    if not report["hasDependencies"]:
        import shutil
        shutil.copy2(baseline_path, args.output)
        print(json.dumps(report, indent=2))
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(effective, f, indent=2, ensure_ascii=False)

    report["outputPath"] = str(output_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
