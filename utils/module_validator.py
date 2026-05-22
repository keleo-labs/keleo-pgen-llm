"""
Module Validator: Check module sizes and recommend splitting.
"""
import re
from pathlib import Path
from typing import Tuple, List

# Size thresholds in words
MODULE_THRESHOLDS = {
    "00": 20000,  # analysis-plan
    "01": 20000,  # practice-details
    "02": 20000,  # citations
    "03": 20000,  # alphas - SPLIT BY FOCUS
    "04": 20000,  # workproducts - SPLIT BY FOCUS
    "05": 25000,  # activities-roles - SPLIT activities/personas
    "06": 20000,  # patterns
    "07": 20000,  # aliases
    "08": 20000,  # method-assembly
}

SPLIT_STRATEGIES = {
    "03": "focus",      # 03a-alphas-value, 03b-alphas-solution, 03c-alphas-endeavor
    "04": "focus",      # 04a-workproducts-value, 04b-workproducts-solution, etc.
    "05": "type",       # 05a-activities, 05b-personas-teams
}


def count_words(filepath: Path) -> int:
    """
    Count words in markdown file.

    Args:
        filepath: Path to markdown file

    Returns:
        Word count
    """
    if not filepath.exists():
        return 0

    content = filepath.read_text()

    # Remove markdown formatting
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # code blocks
    content = re.sub(r'`[^`]+`', '', content)  # inline code
    content = re.sub(r'#+\s', '', content)  # headers
    content = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', content)  # bold/italic

    # Count words
    words = content.split()
    return len(words)


def should_split_module(module_num: str, word_count: int) -> Tuple[bool, str]:
    """
    Determine if module should be split based on size.

    Args:
        module_num: Module number (e.g., "03", "05")
        word_count: Current word count

    Returns:
        (should_split: bool, strategy: str)
        strategy is "focus", "type", or "generic"
    """
    threshold = MODULE_THRESHOLDS.get(module_num, 20000)

    if word_count < threshold:
        return False, ""

    strategy = SPLIT_STRATEGIES.get(module_num, "generic")
    return True, strategy


def get_split_filenames(module_num: str, strategy: str, base_name: str) -> List[str]:
    """
    Get expected filenames for split module.

    Args:
        module_num: Module number (e.g., "03")
        strategy: Split strategy ("focus", "type", "generic")
        base_name: Base module name (e.g., "alphas")

    Returns:
        List of expected filenames
    """
    if strategy == "focus":
        return [
            f"{module_num}a-{base_name}-value.md",
            f"{module_num}b-{base_name}-solution.md",
            f"{module_num}c-{base_name}-endeavor.md",
        ]
    elif strategy == "type" and module_num == "05":
        return [
            "05a-activities.md",
            "05b-personas-teams.md",
        ]
    else:  # generic
        return [
            f"{module_num}a-{base_name}-part-1.md",
            f"{module_num}b-{base_name}-part-2.md",
        ]


def validate_module_completeness(module_path: Path) -> List[str]:
    """
    Check if module contains expected sections.

    Args:
        module_path: Path to module file

    Returns:
        List of issues found (empty if complete)
    """
    issues = []

    if not module_path.exists():
        return [f"Module file not found: {module_path}"]

    content = module_path.read_text()

    # Check for placeholder text
    if "TODO" in content or "PLACEHOLDER" in content or "[...]" in content:
        issues.append("Contains placeholder content (TODO/PLACEHOLDER/[...])")

    # Check minimum length
    word_count = count_words(module_path)
    if word_count < 500:
        issues.append(f"Module too short ({word_count} words, expected >500)")

    # Check for section headers (basic structure validation)
    if content.count("##") < 2:
        issues.append("Missing expected section structure (few headers)")

    return issues


def check_module_size(filepath: Path) -> dict:
    """
    Check module size and provide recommendations.

    Args:
        filepath: Path to module file

    Returns:
        Dict with word_count, should_split, strategy, and recommended_filenames
    """
    word_count = count_words(filepath)

    # Extract module number from filename (e.g., "03-alphas.md" -> "03")
    filename = filepath.name
    match = re.match(r'^(\d{2})', filename)
    if not match:
        return {
            "word_count": word_count,
            "should_split": False,
            "strategy": "",
            "recommended_filenames": []
        }

    module_num = match.group(1)
    should_split, strategy = should_split_module(module_num, word_count)

    # Extract base name (e.g., "03-alphas.md" -> "alphas")
    base_match = re.match(r'^\d{2}-(.+)\.md$', filename)
    base_name = base_match.group(1) if base_match else "module"

    recommended_filenames = []
    if should_split:
        recommended_filenames = get_split_filenames(module_num, strategy, base_name)

    return {
        "word_count": word_count,
        "should_split": should_split,
        "strategy": strategy,
        "recommended_filenames": recommended_filenames
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python module_validator.py <module_file>")
        sys.exit(1)

    module_path = Path(sys.argv[1])
    result = check_module_size(module_path)

    print(f"Module: {module_path.name}")
    print(f"Word count: {result['word_count']}")
    print(f"Should split: {result['should_split']}")

    if result['should_split']:
        print(f"Strategy: {result['strategy']}")
        print(f"Recommended files:")
        for filename in result['recommended_filenames']:
            print(f"  - {filename}")

    issues = validate_module_completeness(module_path)
    if issues:
        print(f"\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\nNo issues found")
