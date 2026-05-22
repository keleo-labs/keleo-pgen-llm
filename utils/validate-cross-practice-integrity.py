#!/usr/bin/env python3
"""
Cross-Practice Referential Integrity Validation

Validates that all references across the 5 Red Hat AI 3 practices and Method JSON
are internally consistent and reference valid baseline elements.
"""
import json
from pathlib import Path
from collections import defaultdict

def load_json(path: Path):
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)

def main():
    # Determine if we're running from repo root or practices/red-hat-ai-3
    if Path("practice-1-platform-management.json").exists():
        # We're in practices/red-hat-ai-3
        base = Path(".")
        baseline_path = Path("../../deps/platform-adoption-kernel.json")
    else:
        # We're in repo root
        base = Path("practices/red-hat-ai-3")
        baseline_path = Path("deps/platform-adoption-kernel.json")

    # Load baseline
    baseline = load_json(baseline_path)
    baseline_alphas = {a["name"] for a in baseline["alphas"]}
    baseline_activity_spaces = {a["name"] for a in baseline["activitySpaces"]}
    baseline_competencies = {c["name"] for c in baseline["competencies"]}

    print("=== Cross-Practice Referential Integrity Validation ===\n")

    # Load Method JSON
    method = load_json(base / "red-hat-ai-3.json")
    print(f"Method: {method['name']}")
    print(f"Practice Names: {', '.join(method['practiceNames'])}\n")

    # Load all practice JSONs
    practices = []
    practice_files = [
        "practice-1-platform-management.json",
        "practice-2-model-lifecycle.json",
        "practice-3-model-development.json",
        "practice-4-inference.json",
        "practice-5-agentic-ai.json"
    ]

    for filename in practice_files:
        path = base / filename
        if path.exists():
            practice = load_json(path)
            practices.append((filename, practice))
            print(f"✓ Loaded {filename}: {practice['name']}")
        else:
            print(f"✗ Missing {filename}")

    print()

    # Validation 1: Method-to-Practice References
    print("--- Validation 1: Method References ---")
    method_practice_names = set(method["practiceNames"])
    actual_practice_names = {p["name"] for _, p in practices}

    if method_practice_names == actual_practice_names:
        print(f"✓ All {len(method_practice_names)} practice names in Method match actual practices")
    else:
        missing = method_practice_names - actual_practice_names
        extra = actual_practice_names - method_practice_names
        if missing:
            print(f"✗ Method references missing practices: {missing}")
        if extra:
            print(f"✗ Extra practices not in Method: {extra}")

    print()

    # Validation 2: Baseline Alpha References
    print("--- Validation 2: Baseline Alpha References ---")
    alpha_errors = []
    for filename, practice in practices:
        practice_name = practice["name"]
        for alpha in practice.get("alphas", []):
            alpha_name = alpha["name"]

            # Check contributesTo references
            if "contributesTo" in alpha:
                contrib = alpha["contributesTo"]
                if contrib not in baseline_alphas:
                    alpha_errors.append(f"{practice_name}: Alpha '{alpha_name}' contributesTo invalid '{contrib}'")

            # Check supportingAlphas references
            for supporting in alpha.get("supportingAlphas", []):
                if supporting not in baseline_alphas:
                    alpha_errors.append(f"{practice_name}: Alpha '{alpha_name}' references invalid supportingAlpha '{supporting}'")

    if alpha_errors:
        print(f"✗ Found {len(alpha_errors)} alpha reference errors:")
        for err in alpha_errors[:10]:
            print(f"  - {err}")
        if len(alpha_errors) > 10:
            print(f"  ... and {len(alpha_errors) - 10} more")
    else:
        print("✓ All alpha contributesTo and supportingAlphas references are valid")

    print()

    # Validation 3: ActivitySpace References
    print("--- Validation 3: ActivitySpace References ---")
    activity_space_errors = []
    for filename, practice in practices:
        practice_name = practice["name"]
        for activity in practice.get("activities", []):
            activity_name = activity["name"]
            as_name = activity.get("activitySpaceName")

            if as_name and as_name not in baseline_activity_spaces:
                activity_space_errors.append(f"{practice_name}: Activity '{activity_name}' references invalid ActivitySpace '{as_name}'")

    if activity_space_errors:
        print(f"✗ Found {len(activity_space_errors)} ActivitySpace reference errors:")
        for err in activity_space_errors:
            print(f"  - {err}")
    else:
        print("✓ All ActivitySpace references are valid")

    print()

    # Validation 4: Competency References
    print("--- Validation 4: Competency References ---")
    competency_errors = []
    for filename, practice in practices:
        practice_name = practice["name"]
        for activity in practice.get("activities", []):
            activity_name = activity["name"]
            for comp in activity.get("competencies", []):
                # Handle both string and object formats
                if isinstance(comp, str):
                    comp_name = comp
                elif isinstance(comp, dict):
                    comp_name = comp.get("competencyName", "")
                else:
                    competency_errors.append(f"{practice_name}: Activity '{activity_name}' has invalid competency format: {type(comp)}")
                    continue

                if comp_name and comp_name not in baseline_competencies:
                    competency_errors.append(f"{practice_name}: Activity '{activity_name}' references invalid competency '{comp_name}'")

    if competency_errors:
        print(f"✗ Found {len(competency_errors)} competency reference errors:")
        for err in competency_errors[:10]:
            print(f"  - {err}")
        if len(competency_errors) > 10:
            print(f"  ... and {len(competency_errors) - 10} more")
    else:
        print("✓ All competency references are valid")

    print()

    # Validation 5: Internal Practice References (alphaName in state progressions)
    print("--- Validation 5: Internal Alpha State References ---")
    internal_alpha_errors = []
    for filename, practice in practices:
        practice_name = practice["name"]
        practice_alphas = {a["name"] for a in practice.get("alphas", [])}

        # Check work product progressions reference valid alphas
        for wp in practice.get("workProducts", []):
            for progression in wp.get("levelsOfDetail", []):
                for evidence in progression.get("progressions", []):
                    alpha_name = evidence.get("alphaName")
                    if alpha_name and alpha_name not in practice_alphas and alpha_name not in baseline_alphas:
                        internal_alpha_errors.append(f"{practice_name}: WorkProduct '{wp['name']}' references undefined alpha '{alpha_name}'")

        # Check activity outcomes reference valid alphas
        for activity in practice.get("activities", []):
            for outcome in activity.get("outcomes", []):
                # Handle both string and object formats
                if isinstance(outcome, str):
                    # String format: "Alpha Name → State Name"
                    if " → " in outcome:
                        alpha_name = outcome.split(" → ")[0]
                    else:
                        alpha_name = outcome
                elif isinstance(outcome, dict):
                    alpha_name = outcome.get("alphaName")
                else:
                    continue

                if alpha_name and alpha_name not in practice_alphas and alpha_name not in baseline_alphas:
                    internal_alpha_errors.append(f"{practice_name}: Activity '{activity['name']}' outcome references undefined alpha '{alpha_name}'")

    if internal_alpha_errors:
        print(f"✗ Found {len(internal_alpha_errors)} internal alpha reference errors:")
        for err in internal_alpha_errors[:10]:
            print(f"  - {err}")
        if len(internal_alpha_errors) > 10:
            print(f"  ... and {len(internal_alpha_errors) - 10} more")
    else:
        print("✓ All internal alpha references are valid")

    print()

    # Validation 6: Cross-Practice Shared Alphas
    print("--- Validation 6: Cross-Practice Shared Alphas ---")
    alpha_usage = defaultdict(list)
    for filename, practice in practices:
        practice_name = practice["name"]
        for alpha in practice.get("alphas", []):
            alpha_usage[alpha["name"]].append(practice_name)

    shared_alphas = {name: practices for name, practices in alpha_usage.items() if len(practices) > 1}
    print(f"Found {len(shared_alphas)} alphas shared across practices:")
    for alpha_name, practice_list in sorted(shared_alphas.items()):
        print(f"  - {alpha_name}: {len(practice_list)} practices ({', '.join(practice_list[:3])}{'...' if len(practice_list) > 3 else ''})")

    print()

    # Validation 7: Element Count Summary
    print("--- Validation 7: Element Count Summary ---")
    total_alphas = sum(len(p.get("alphas", [])) for _, p in practices)
    total_work_products = sum(len(p.get("workProducts", [])) for _, p in practices)
    total_activities = sum(len(p.get("activities", [])) for _, p in practices)
    total_personas = sum(len(p.get("personas", [])) for _, p in practices)
    total_patterns = sum(len(p.get("patterns", [])) for _, p in practices)

    print(f"Total Alphas: {total_alphas}")
    print(f"Total Work Products: {total_work_products}")
    print(f"Total Activities: {total_activities}")
    print(f"Total Personas: {total_personas}")
    print(f"Total Patterns: {total_patterns}")

    # Load cross-reference index for comparison
    cross_ref = load_json(base / "cross-reference-index.json")
    expected = cross_ref["totalElements"]

    print(f"\nCross-Reference Index Expectations:")
    print(f"  Alphas: {expected['alphas']} (actual: {total_alphas})")
    print(f"  Work Products: {expected['workProducts']} (actual: {total_work_products})")
    print(f"  Activities: {expected['activities']} (actual: {total_activities})")
    print(f"  Personas: {expected['personas']} (actual: {total_personas})")
    print(f"  Patterns: {expected['patterns']} (actual: {total_patterns})")

    print()

    # Summary
    print("=== Validation Summary ===")
    total_errors = (len(alpha_errors) + len(activity_space_errors) +
                   len(competency_errors) + len(internal_alpha_errors))

    if total_errors == 0:
        print("✓ ALL VALIDATIONS PASSED")
        print(f"✓ Method JSON references {len(method_practice_names)} practices correctly")
        print(f"✓ All baseline references (alphas, activity spaces, competencies) are valid")
        print(f"✓ All internal practice references are valid")
        print(f"✓ {len(shared_alphas)} alphas successfully shared across practices")
        return 0
    else:
        print(f"✗ FOUND {total_errors} ERRORS")
        print(f"  - Alpha reference errors: {len(alpha_errors)}")
        print(f"  - ActivitySpace reference errors: {len(activity_space_errors)}")
        print(f"  - Competency reference errors: {len(competency_errors)}")
        print(f"  - Internal alpha reference errors: {len(internal_alpha_errors)}")
        return 1

if __name__ == "__main__":
    exit(main())
