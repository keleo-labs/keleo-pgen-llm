"""
Integrity Validator: Cross-practice and schema validation.

Refactored from validate-cross-practice-integrity.py.
"""
import json
from pathlib import Path
from typing import Dict, List


def validate_cross_practice_references(
    method_json: Dict,
    practice_jsons: List[Dict],
    baseline: Dict
) -> Dict[str, List[str]]:
    """
    Validate cross-practice references and integrity.

    Args:
        method_json: Method JSON dict
        practice_jsons: List of practice JSON dicts
        baseline: Baseline framework dict

    Returns:
        Dict of validation errors by category
    """
    errors = {
        "method_references": [],
        "baseline_alphas": [],
        "activity_spaces": [],
        "competencies": [],
        "internal_alphas": [],
        "cross_practice_alphas": [],
        "element_counts": []
    }

    # TODO: Implement validation logic
    # 1. Method-to-practice references
    # 2. Baseline alpha references
    # 3. ActivitySpace references
    # 4. Competency references
    # 5. Internal alpha state references
    # 6. Cross-practice shared alphas
    # 7. Element count summary

    return errors


def validate_single_practice(practice_json: Dict, baseline: Dict) -> List[str]:
    """
    Validate single practice against baseline.

    Args:
        practice_json: Practice JSON dict
        baseline: Baseline framework dict

    Returns:
        List of validation errors
    """
    errors = []

    # TODO: Implement single practice validation
    # - Check all baseline references valid
    # - Check internal consistency
    # - Check schema compliance

    return errors


def generate_validation_report(errors: Dict[str, List[str]]) -> str:
    """
    Generate human-readable validation report.

    Args:
        errors: Dict of errors by category

    Returns:
        Formatted validation report
    """
    lines = ["# Validation Report\n"]

    total_errors = sum(len(v) for v in errors.values())

    if total_errors == 0:
        lines.append("✓ All validation checks passed\n")
        return "\n".join(lines)

    lines.append(f"⚠ Found {total_errors} validation issues\n")

    for category, error_list in errors.items():
        if error_list:
            lines.append(f"## {category.replace('_', ' ').title()}\n")
            for error in error_list:
                lines.append(f"- {error}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python integrity_validator.py <method_json> <practice_json> [<practice_json> ...]")
        sys.exit(1)

    method_path = Path(sys.argv[1])
    practice_paths = [Path(p) for p in sys.argv[2:]]

    from .resource_manager import load_baseline

    method_json = json.loads(method_path.read_text())
    practice_jsons = [json.loads(p.read_text()) for p in practice_paths]
    baseline = load_baseline()

    errors = validate_cross_practice_references(method_json, practice_jsons, baseline)
    report = generate_validation_report(errors)

    print(report)
