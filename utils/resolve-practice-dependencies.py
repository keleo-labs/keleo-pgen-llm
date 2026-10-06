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

    # Per-alpha detail: show each alpha's contributesTo target and its origin
    python3 utils/resolve-practice-dependencies.py \
        --parent effective-parent.json \
        --baseline effective-baseline.json \
        --practice my-practice.json \
        --per-alpha

    # Analyze all practices in a method at once (--practice accepts methods too)
    python3 utils/resolve-practice-dependencies.py \
        --parent effective-parent.json \
        --baseline effective-baseline.json \
        --practice my-method.json \
        --per-alpha
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


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
    """Map each parent alpha to the practice that defines it.

    Two parent shapes exist. A legacy method embeds its practices as objects
    under ``practices``. A resolved effective context produced by
    ``resolve-context.py`` is flat: one merged ``alphas`` array where every
    element carries ``_contributingPracticeName`` provenance. Reading only the
    embedded shape leaves the map empty for an effective context, so every
    parent-only target resolves to no owning practice and the tool reports an
    empty ``practiceDependencyNames`` while simultaneously listing the alpha
    under ``referencedParentOnlyAlphas`` — a silent under-report.
    """
    alpha_to_practice = {}

    # Legacy embedded-practice method shape.
    for p in method_data.get("practices", []):
        practice_name = p.get("name", "unknown")
        for alpha in p.get("alphas", []):
            name = alpha.get("name")
            if name:
                alpha_to_practice[name] = [practice_name]

    # Resolved effective context: provenance lives on each element. Only the
    # practice tier creates a practiceDependencyNames entry — a baseline
    # contributor creates none, and a method contributor is coordination-level
    # rather than a practice dependency.
    # An alpha declared identically by two practices keeps only the last writer
    # in `_contributingPracticeName`. Prefer the full `_contributingPracticeNames`
    # list so a shared alpha reports every practice that declares it — reading
    # the scalar alone silently drops dependencies the practice genuinely needs.
    tiers = (method_data.get("_provenance") or {}).get("tiers") or {}
    practice_tier = set(tiers.get("practices") or [])
    for alpha in method_data.get("alphas", []):
        name = alpha.get("name")
        if not name or name in alpha_to_practice:
            continue
        contributors = alpha.get("_contributingPracticeNames") or []
        if not contributors:
            scalar = alpha.get("_contributingPracticeName")
            contributors = [scalar] if scalar else []
        owners = [
            c for c in contributors
            if c and (not practice_tier or c in practice_tier)
        ]
        if owners:
            alpha_to_practice[name] = owners

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


def build_per_alpha_detail(practice_data, baseline_alphas, parent_only_set,
                           alpha_to_practice):
    """Build per-alpha detail rows for a single practice."""
    rows = []
    local_alphas = {a["name"] for a in practice_data.get("alphas", [])
                    if a.get("name")}
    for alpha in practice_data.get("alphas", []):
        name = alpha.get("name", "")
        ct = alpha.get("contributesTo")
        row = {
            "alphaName": name,
            "inBaseline": name in baseline_alphas,
            "contributesTo": ct,
        }
        if ct:
            if ct in local_alphas:
                row["targetOrigin"] = "practice-local"
            elif ct in baseline_alphas:
                row["targetOrigin"] = "baseline"
            elif ct in parent_only_set:
                row["targetOrigin"] = "parent-only"
                owners = alpha_to_practice.get(ct, [])
                if owners:
                    row["targetOwningPractice"] = owners[-1]
                    row["targetOwningPractices"] = owners
            else:
                row["targetOrigin"] = "unresolved"
        rows.append(row)
    return rows


def analyze_practice_with_detail(practice_data, practice_name, baseline_alphas,
                                 parent_only_set, alpha_to_practice):
    """Full analysis for a single practice including per-alpha detail."""
    external_targets = collect_contributes_to(practice_data)

    referenced_parent_only = sorted(external_targets & parent_only_set)
    referenced_baseline = sorted(external_targets & baseline_alphas)
    unresolved = sorted(
        external_targets - parent_only_set - baseline_alphas
    )

    # An alpha with exactly one owner forces that dependency. An alpha declared
    # by several practices is satisfied by ANY one of them, so unioning the
    # owners would inflate the dependency graph; report those separately and let
    # the caller pick on semantic grounds (which owner the content really
    # belongs to), rather than guessing here.
    required = set()
    shared = {}
    for alpha_name in referenced_parent_only:
        owners = alpha_to_practice.get(alpha_name, [])
        if len(owners) == 1:
            required.add(owners[0])
        elif len(owners) > 1:
            shared[alpha_name] = owners

    unresolved_shared = {
        a: o for a, o in shared.items() if not (set(o) & required)
    }

    result = {
        "practice": practice_name,
        "externalContributesTo": sorted(external_targets),
        "referencedBaselineAlphas": referenced_baseline,
        "referencedParentOnlyAlphas": referenced_parent_only,
        "unresolvedTargets": unresolved,
        "practiceDependencyNames": sorted(required),
        "alphas": build_per_alpha_detail(
            practice_data, baseline_alphas, parent_only_set,
            alpha_to_practice,
        ),
    }
    if shared:
        result["sharedAlphaOwners"] = shared
    if unresolved_shared:
        result["requiresDependencyChoice"] = {
            "note": (
                "These alphas are declared by more than one practice and none of "
                "their owners is already required. Add one owner per alpha to "
                "practiceDependencyNames, choosing on semantic grounds."
            ),
            "alphas": unresolved_shared,
        }
    return result


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
        help="Path to the practice or method JSON to compute dependencies for",
    )
    parser.add_argument(
        "--per-alpha", action="store_true",
        help="Include per-alpha detail (contributesTo target, origin classification)",
    )
    args = parser.parse_args()

    parent_data = load_json(args.parent)
    baseline_data = load_json(args.baseline)

    parent_alphas = collect_alpha_names(parent_data)
    baseline_alphas = collect_alpha_names(baseline_data)
    parent_only = sorted(parent_alphas - baseline_alphas)

    # Ownership comes from an explicit --parent-method when one is given.
    # Otherwise derive it from the parent document itself: a resolved effective
    # context already carries `_contributingPracticeName` on every element.
    # Without this fallback the map stays empty on the documented invocation
    # (--parent/--baseline/--practice), so practiceDependencyNames is always
    # reported as [] no matter what the practice actually references.
    if args.parent_method:
        alpha_to_practice = map_alphas_to_practices(load_json(args.parent_method))
    else:
        alpha_to_practice = map_alphas_to_practices(parent_data)

    parent_only_with_practice = []
    for alpha_name in parent_only:
        entry = {"alphaName": alpha_name}
        owners = alpha_to_practice.get(alpha_name, [])
        if owners:
            entry["owningPractice"] = owners[-1]
            entry["owningPractices"] = owners
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
        parent_only_set = set(parent_only)
        practice_kind = practice_data.get("kind", "practice")

        if practice_kind == "method" and practice_data.get("practices"):
            analyses = []
            for p in practice_data["practices"]:
                analysis = analyze_practice_with_detail(
                    p, p.get("name", "unknown"),
                    baseline_alphas, parent_only_set, alpha_to_practice,
                )
                if not args.per_alpha:
                    del analysis["alphas"]
                analyses.append(analysis)
            output["practiceAnalyses"] = analyses
        else:
            analysis = analyze_practice_with_detail(
                practice_data, args.practice,
                baseline_alphas, parent_only_set, alpha_to_practice,
            )
            if not args.per_alpha:
                del analysis["alphas"]
            output["practiceAnalysis"] = analysis

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
