"""Shared utilities for Practice Language JSON tools.

Internal module — not a CLI tool. Import from individual scripts:
    from utils._shared import load_json, merge_by_name, MERGEABLE_ARRAYS
"""

import copy
import json
import sys
from collections import OrderedDict
from pathlib import Path


def load_json(file_path, exit_on_error=True):
    """Load and parse a JSON file.

    Args:
        file_path: Path to JSON file (str or Path).
        exit_on_error: If True, print error JSON and sys.exit(1) on failure.
                       If False, raise the underlying exception.

    Returns:
        Parsed JSON as dict/list.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if exit_on_error:
            print(json.dumps({"error": f"File not found: {file_path}"}))
            sys.exit(1)
        raise
    except json.JSONDecodeError as e:
        if exit_on_error:
            print(json.dumps({"error": f"Invalid JSON in {file_path}: {e}"}))
            sys.exit(1)
        raise


def load_json_pair(file_path):
    """Load JSON returning (data, error_string) tuple. Never exits."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {file_path}: {e}"


MERGEABLE_ARRAYS = [
    "focuses", "alphas", "activitySpaces", "competencies",
    "narrativeTypes", "narratives", "citations", "assets",
    "workProducts", "patterns", "personas", "personaGroups",
    "alphaInstances", "workProductInstances",
]


def merge_by_name(base_list, overlay_list):
    """Merge two lists of objects by 'name' key. Overlay overrides base."""
    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            merged[item["name"]] = item
    for item in (overlay_list or []):
        if "name" in item:
            if item["name"] in merged:
                existing = merged[item["name"]]
                combined = copy.deepcopy(existing)
                combined.update(copy.deepcopy(item))
                merged[item["name"]] = combined
            else:
                merged[item["name"]] = copy.deepcopy(item)
    return list(merged.values())


def collect_element_names(data, element_type):
    """Collect all names from an element type across root and embedded practices."""
    names = set()
    for item in data.get(element_type, []):
        name = item.get("name")
        if name:
            names.add(name)
    for practice in data.get("practices", []):
        for item in practice.get(element_type, []):
            name = item.get("name")
            if name:
                names.add(name)
    return names


def collect_alpha_state_names(data):
    """Build dict mapping alpha_name -> set of state names."""
    result = {}
    for alpha in data.get("alphas", []):
        name = alpha.get("name")
        if name:
            result[name] = {s.get("name") for s in alpha.get("states", []) if s.get("name")}
    for practice in data.get("practices", []):
        for alpha in practice.get("alphas", []):
            name = alpha.get("name")
            if name:
                result[name] = {s.get("name") for s in alpha.get("states", []) if s.get("name")}
    return result


def detect_kind(data):
    """Classify JSON by schema discrimination rules."""
    if any(key in data for key in ("practices", "practiceNames", "baselinePractice")):
        return "method"
    if "baselinePracticeName" in data:
        return "practice"
    kind = data.get("kind", "")
    if kind in ("practice", "method", "practiceBaseline"):
        return kind
    return "practiceBaseline"
