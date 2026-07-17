#!/usr/bin/env python3
"""Inspect practice/method/baseline JSON for quality gate checks.

Replaces ~30 inline jq commands used in generate-method and update-method skills
for post-generation quality validation.
"""

import argparse
import json
import sys
from collections import Counter


ALL_CHECKS = ["kind", "counts", "uniqueness", "competencies", "properties", "required"]
ALL_EXTRACTS = ["alphas"]


def check_kind(data):
    """Verify discriminator property is present and correct."""
    issues = []
    kind = data.get("kind")

    if kind is None:
        issues.append("Missing 'kind' property at root level")
    elif kind not in ("practice", "method", "practiceBaseline"):
        issues.append(f"Invalid 'kind' value: '{kind}' (expected practice/method/practiceBaseline)")

    if kind == "method":
        for i, p in enumerate(data.get("practices", [])):
            p_kind = p.get("kind")
            p_name = p.get("name", f"practice[{i}]")
            if p_kind is None:
                issues.append(f"Practice '{p_name}' missing 'kind' property")
            elif p_kind != "practice":
                issues.append(f"Practice '{p_name}' has kind='{p_kind}' (expected 'practice')")

    return {
        "check": "kind",
        "pass": len(issues) == 0,
        "kind": kind,
        "issues": issues,
    }


def check_counts(data):
    """Count major element arrays and compare against minimums."""
    minimums = {
        "alphas": 3,
        "workProducts": 3,
        "activities": 5,
        "patterns": 1,
        "citations": 3,
    }

    kind = data.get("kind", "practice")
    elements = {}

    if kind == "method":
        for key in minimums:
            total = len(data.get(key, []))
            for p in data.get("practices", []):
                total += len(p.get(key, []))
            elements[key] = total
    else:
        for key in minimums:
            elements[key] = len(data.get(key, []))

    issues = []
    for key, minimum in minimums.items():
        if kind == "practiceBaseline" and key in ("workProducts", "activities", "patterns"):
            continue
        if elements.get(key, 0) < minimum:
            issues.append(f"{key}: {elements.get(key, 0)} (minimum: {minimum})")

    return {
        "check": "counts",
        "pass": len(issues) == 0,
        "elements": elements,
        "issues": issues,
    }


def _collect_all_elements(data):
    """Collect all practice elements from data, handling methods."""
    kind = data.get("kind", "practice")
    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    all_elements = []
    for source in sources:
        for key in ("alphas", "workProducts", "activities", "personas", "patterns", "assets"):
            for item in source.get(key, []):
                if isinstance(item, dict) and "name" in item:
                    all_elements.append((key, item["name"]))
    return all_elements


def check_uniqueness(data):
    """Verify PracticeElement names are globally unique across all element types."""
    all_elements = _collect_all_elements(data)
    name_counts = Counter(name for _, name in all_elements)
    duplicates = []
    for name, count in name_counts.items():
        if count > 1:
            types = [t for t, n in all_elements if n == name]
            duplicates.append({"name": name, "count": count, "elementTypes": types})

    return {
        "check": "uniqueness",
        "pass": len(duplicates) == 0,
        "duplicates": duplicates,
    }


def check_competencies(data, baseline_data):
    """Cross-validate competencyLevelName values against baseline competency levels."""
    if baseline_data is None:
        return {
            "check": "competencies",
            "pass": True,
            "skipped": True,
            "reason": "No baseline provided (use --baseline to enable this check)",
        }

    baseline_levels = set()
    for comp in baseline_data.get("competencies", []):
        for level in comp.get("competencyLevels", comp.get("levels", [])):
            name = level.get("name")
            if name:
                baseline_levels.add(name)

    practice_levels = set()
    sources = [data]
    kind = data.get("kind", "practice")
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        for activity in source.get("activities", []):
            for rcl in activity.get("recommendedCompetencyLevels", []):
                name = rcl.get("competencyLevelName")
                if name:
                    practice_levels.add(name)
        for persona in source.get("personas", []):
            for comp in persona.get("competencies", []):
                name = comp.get("competencyLevelName")
                if name:
                    practice_levels.add(name)

    invalid = sorted(practice_levels - baseline_levels)

    return {
        "check": "competencies",
        "pass": len(invalid) == 0,
        "baselineLevels": sorted(baseline_levels),
        "practiceLevels": sorted(practice_levels),
        "invalidLevels": invalid,
    }


def check_properties(data):
    """Verify activities and alphas have required properties."""
    issues = []
    sources = [data]
    kind = data.get("kind", "practice")
    if kind == "method":
        sources.extend(data.get("practices", []))
    if kind == "practiceBaseline":
        return {"check": "properties", "pass": True, "skipped": True, "reason": "Baseline practices don't have activities/alphas with these requirements"}

    for source in sources:
        source_name = source.get("name", "root")
        for act in source.get("activities", []):
            act_name = act.get("name", "unnamed")
            if not act.get("activitySpaceName"):
                issues.append(f"Activity '{act_name}' ({source_name}) missing activitySpaceName")
            asset_names = act.get("assetNames", [])
            if not asset_names:
                issues.append(f"Activity '{act_name}' ({source_name}) missing assetNames")
            if not act.get("contributesTo"):
                issues.append(f"Activity '{act_name}' ({source_name}) missing contributesTo")

        for alpha in source.get("alphas", []):
            alpha_name = alpha.get("name", "unnamed")
            asset_names = alpha.get("assetNames", [])
            icons = [a for a in asset_names if isinstance(a, dict) and a.get("type") == "icon"]
            if not icons:
                issues.append(f"Alpha '{alpha_name}' ({source_name}) missing icon AssetReference")

    return {
        "check": "properties",
        "pass": len(issues) == 0,
        "issues": issues,
        "issueCount": len(issues),
    }


def check_required(data):
    """Check root-level required properties."""
    issues = []
    kind = data.get("kind", "practice")

    required_fields = ["name", "description"]
    if kind in ("practice", "method"):
        required_fields.append("baselinePracticeName")

    for field in required_fields:
        if not data.get(field):
            issues.append(f"Missing required property: '{field}'")

    if kind in ("practice", "method"):
        narratives = data.get("narratives", [])
        if not narratives:
            issues.append("Missing 'narratives' array (at least one narrative required)")

    if kind == "method":
        practices = data.get("practices", [])
        if not practices:
            issues.append("Missing 'practices' array in method")

    return {
        "check": "required",
        "pass": len(issues) == 0,
        "issues": issues,
    }


def extract_alphas(data):
    """Extract alpha metadata for delineation analysis."""
    kind = data.get("kind", "practice")
    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    alphas = []
    for source in sources:
        source_name = source.get("name", "root")
        for alpha in source.get("alphas", []):
            entry = {
                "name": alpha.get("name"),
                "description": alpha.get("description"),
                "focusName": alpha.get("focusName"),
            }
            if alpha.get("relatesTo"):
                entry["relatesTo"] = alpha["relatesTo"]
            if alpha.get("contributesTo"):
                entry["contributesTo"] = alpha["contributesTo"]
            if alpha.get("_domainAlias"):
                entry["_domainAlias"] = alpha["_domainAlias"]
            if kind == "method":
                entry["_sourcePractice"] = source_name
            states = alpha.get("states", [])
            if states:
                entry["stateCount"] = len(states)
                entry["states"] = [s.get("name") for s in states]
            alphas.append(entry)
    return alphas


def run_extracts(data, selected_extracts):
    results = {}
    for extract_name in selected_extracts:
        if extract_name == "alphas":
            results["alphas"] = extract_alphas(data)
    return results


def run_checks(data, baseline_data, selected_checks):
    results = []
    for check_name in selected_checks:
        if check_name == "kind":
            results.append(check_kind(data))
        elif check_name == "counts":
            results.append(check_counts(data))
        elif check_name == "uniqueness":
            results.append(check_uniqueness(data))
        elif check_name == "competencies":
            results.append(check_competencies(data, baseline_data))
        elif check_name == "properties":
            results.append(check_properties(data))
        elif check_name == "required":
            results.append(check_required(data))
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Inspect practice/method/baseline JSON for quality gate checks"
    )
    parser.add_argument("file", help="Path to practice/method JSON file to inspect")
    parser.add_argument(
        "--baseline",
        help="Path to baseline practice JSON (required for competency validation)",
    )
    parser.add_argument(
        "--check",
        help=f"Comma-separated list of checks to run (default: all). Options: {', '.join(ALL_CHECKS)}",
    )
    parser.add_argument(
        "--extract",
        help=f"Extract data instead of running checks. Options: {', '.join(ALL_EXTRACTS)}",
    )
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"Cannot read file: {e}"}))
        sys.exit(1)

    baseline_data = None
    if args.baseline:
        try:
            with open(args.baseline) as f:
                baseline_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(json.dumps({"error": f"Cannot read baseline: {e}"}))
            sys.exit(1)

    if args.extract:
        selected_extracts = args.extract.split(",")
        invalid_extracts = [e for e in selected_extracts if e not in ALL_EXTRACTS]
        if invalid_extracts:
            print(json.dumps({"error": f"Unknown extracts: {invalid_extracts}. Valid: {ALL_EXTRACTS}"}))
            sys.exit(1)
        results = run_extracts(data, selected_extracts)
        output = {"file": args.file, "kind": data.get("kind")}
        output.update(results)
        print(json.dumps(output, indent=2))
        sys.exit(0)

    selected = args.check.split(",") if args.check else ALL_CHECKS
    invalid_checks = [c for c in selected if c not in ALL_CHECKS]
    if invalid_checks:
        print(json.dumps({"error": f"Unknown checks: {invalid_checks}. Valid: {ALL_CHECKS}"}))
        sys.exit(1)

    results = run_checks(data, baseline_data, selected)

    passed = sum(1 for r in results if r.get("pass", True))
    total = sum(1 for r in results if "pass" in r)
    all_pass = passed == total

    output = {
        "file": args.file,
        "kind": data.get("kind"),
        "valid": all_pass,
        "summary": f"{passed}/{total} checks passed",
        "checks": results,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
