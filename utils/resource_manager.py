"""
Resource Manager: Load and cache baseline framework and schema.

Handles compaction scenarios by providing reload capabilities.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

# Module-level cache to survive across function calls
_BASELINE_CACHE: Optional[Dict] = None
_SCHEMA_CACHE: Optional[Dict] = None


def get_repo_root() -> Path:
    """Find repository root (contains deps/)."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "deps").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root")


def load_baseline(force_reload: bool = False) -> Dict:
    """
    Load baseline framework JSON.

    Args:
        force_reload: If True, bypass cache and reload from disk

    Returns:
        Baseline framework as dict
    """
    global _BASELINE_CACHE

    if _BASELINE_CACHE is None or force_reload:
        repo_root = get_repo_root()
        baseline_path = repo_root / "deps" / "platform-adoption-kernel.json"

        if not baseline_path.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_path}")

        with open(baseline_path) as f:
            _BASELINE_CACHE = json.load(f)

    return _BASELINE_CACHE


def load_schema(force_reload: bool = False) -> Dict:
    """
    Load JSON schema.

    Args:
        force_reload: If True, bypass cache and reload from disk

    Returns:
        Schema as dict
    """
    global _SCHEMA_CACHE

    if _SCHEMA_CACHE is None or force_reload:
        repo_root = get_repo_root()
        schema_path = repo_root / "deps" / "language.schema.json"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path) as f:
            _SCHEMA_CACHE = json.load(f)

    return _SCHEMA_CACHE


def get_baseline_names(category: str) -> List[str]:
    """
    Get list of baseline element names for a category.

    Args:
        category: "alphas", "activitySpaces", "competencies", "focuses"

    Returns:
        List of element names
    """
    baseline = load_baseline()

    if category == "focuses":
        return ["Value", "Solution", "Endeavor"]

    if category not in baseline:
        raise ValueError(f"Unknown category: {category}")

    return [elem["name"] for elem in baseline[category]]


def get_baseline_alpha_states(alpha_name: str) -> List[str]:
    """
    Get state names for a baseline alpha.

    Args:
        alpha_name: Name of alpha (e.g., "Platform")

    Returns:
        List of state names in sequence order
    """
    baseline = load_baseline()

    for alpha in baseline["alphas"]:
        if alpha["name"] == alpha_name:
            return [state["name"] for state in sorted(alpha["states"], key=lambda s: s["seq"])]

    raise ValueError(f"Alpha not found in baseline: {alpha_name}")


def verify_baseline_reference(name: str, category: str) -> bool:
    """
    Verify a name exists in baseline for given category.

    Args:
        name: Element name to verify
        category: "alphas", "activitySpaces", "competencies", "focuses"

    Returns:
        True if name exists in baseline, False otherwise
    """
    try:
        baseline_names = get_baseline_names(category)
        return name in baseline_names
    except ValueError:
        return False


def clear_cache():
    """Clear cached resources (for testing or explicit reload)."""
    global _BASELINE_CACHE, _SCHEMA_CACHE
    _BASELINE_CACHE = None
    _SCHEMA_CACHE = None


# Convenience function for Phase 2 prompts
def verify_resources_loaded() -> bool:
    """
    Verify that critical resources are loaded.

    Returns:
        True if both baseline and schema are cached, False otherwise
    """
    return _BASELINE_CACHE is not None and _SCHEMA_CACHE is not None


if __name__ == "__main__":
    # Test loading
    baseline = load_baseline()
    print(f"Loaded baseline with {len(baseline['alphas'])} alphas")

    schema = load_schema()
    print(f"Loaded schema")

    alpha_names = get_baseline_names("alphas")
    print(f"Baseline alphas: {', '.join(alpha_names)}")

    platform_states = get_baseline_alpha_states("Platform")
    print(f"Platform states: {', '.join(platform_states)}")

    print(f"Resources loaded: {verify_resources_loaded()}")
