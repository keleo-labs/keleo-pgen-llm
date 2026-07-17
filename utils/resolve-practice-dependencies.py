#!/usr/bin/env python3
"""Resolve practiceDependencyNames for a practice extending a parent practice/method.

Compares alpha names between the effective parent and effective baseline to
identify "parent-only" alphas (defined in the parent but NOT in the baseline).
Then maps each parent-only alpha to its owning practice in the parent method.

Usage:
    # Show parent-only alphas and their owning practices
    python3 utils/resolve-practice-dependencies.py \
        --parent effective-parent.json \
        --baseline effective-baseline.json

    # Also provide the original parent method to map alphas to practices
    python3 utils/resolve-practice-dependencies.py \
        --parent effective-parent.json \
        --baseline effective-baseline.json \
        --parent-method parent-method.json

    # Check which dependencies a specific practice needs (filter by contributesTo targets)
    python3 utils/resolve-practice-dependencies.py \
        --parent effective-parent.json \
        --baseline effective-baseline.json \
        --parent-method parent-method.json \
        --practice my-practice.json
"""

import argparse
import json
import sys


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"Cannot read {path}: {e}"}))
        sys.exit(1)


def collect_alpha_names(data):
    names = set()
    for alpha in data.get("alphas", []):
        name = alpha.get("name")
        if name:
            names.add(name)
    kind = data.get("kind", "practice")
    if kind == "method":
        for p in data.get("practices", []):
            for alpha in p.get("alphas", []):
                name = alpha.get("name")
                if name:
                    names.add(name)
    return names


def map_alphas_to_practices(method_data):
    alpha_to_practice = {}
    for p in method_data.get("practices", []):
        practice_name = p.get("name", "unknown")
        for alpha in p.get("alphas", []):
            name = alpha.get("name")
            if name:
                alpha_to_practice[name] = practice_name
    for alpha in method_data.get("alphas", []):
        name = alpha.get("name")
        if name and name not in alpha_to_practice:
            alpha_to_practice[name] = method_data.get("name", "root")
    return alpha_to_practice


def collect_contributes_to(data):
    targets = set()
    local_alphas = set()
    sources = [data]
    kind = data.get("kind", "practice")
    if kind == "method":
        sources.extend(data.get("practices", []))
    for source in sources:
        for alpha in source.get("alphas", []):
            name = alpha.get("name")
            if name:
                local_alphas.add(name)
            ct = alpha.get("contributesTo")
            if ct:
                targets.add(ct)
    return targets - local_alphas


def main():
    parser = argparse.ArgumentParser(
        description="Resolve practiceDependencyNames by comparing parent and baseline alphas"
    )
    parser.add_argument(
        "--parent", required=True,
        help="Path to effective parent JSON (merged parent practice/method)",
    )
    parser.add_argument(
        "--baseline", required=True,
        help="Path to effective baseline JSON",
    )
    parser.add_argument(
        "--parent-method",
        help="Path to original parent method JSON (for mapping alphas to practices)",
    )
    parser.add_argument(
        "--practice",
        help="Path to the practice JSON to compute dependencies for (filters by contributesTo)",
    )
    args = parser.parse_args()

    parent_data = load_json(args.parent)
    baseline_data = load_json(args.baseline)

    parent_alphas = collect_alpha_names(parent_data)
    baseline_alphas = collect_alpha_names(baseline_data)
    parent_only = sorted(parent_alphas - baseline_alphas)

    alpha_to_practice = {}
    if args.parent_method:
        method_data = load_json(args.parent_method)
        alpha_to_practice = map_alphas_to_practices(method_data)

    parent_only_with_practice = []
    for alpha_name in parent_only:
        entry = {"alphaName": alpha_name}
        if alpha_name in alpha_to_practice:
            entry["owningPractice"] = alpha_to_practice[alpha_name]
        parent_only_with_practice.append(entry)

    output = {
        "parentAlphaCount": len(parent_alphas),
        "baselineAlphaCount": len(baseline_alphas),
        "parentOnlyAlphas": parent_only_with_practice,
        "parentOnlyCount": len(parent_only),
        "baselineAlphas": sorted(baseline_alphas),
        "parentAlphas": sorted(parent_alphas),
    }

    if args.practice:
        practice_data = load_json(args.practice)
        external_targets = collect_contributes_to(practice_data)
        parent_only_set = set(parent_only)

        referenced_parent_only = sorted(external_targets & parent_only_set)
        referenced_baseline = sorted(external_targets & baseline_alphas)
        unresolved = sorted(external_targets - parent_alphas - baseline_alphas)

        owning_practices = set()
        for alpha_name in referenced_parent_only:
            if alpha_name in alpha_to_practice:
                owning_practices.add(alpha_to_practice[alpha_name])

        output["practiceAnalysis"] = {
            "practice": args.practice,
            "externalContributesTo": sorted(external_targets),
            "referencedBaselineAlphas": referenced_baseline,
            "referencedParentOnlyAlphas": referenced_parent_only,
            "unresolvedTargets": unresolved,
            "practiceDependencyNames": sorted(owning_practices),
        }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
