"""Shared utilities for Practice Language JSON tools.

Internal module — not a CLI tool. Import from individual scripts:
    from utils._shared import load_json, merge_by_name, MERGEABLE_ARRAYS
"""

import copy
import json
import sys
import zipfile
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


def merge_by_name_annotated(base_list, overlay_list, base_source, overlay_source):
    """Merge two lists by 'name', stamping _contributingPracticeName on each element.

    Same semantics as merge_by_name (overlay wins on conflict).
    """
    base_names = {item["name"] for item in (base_list or []) if "name" in item}
    overlay_names = {item["name"] for item in (overlay_list or []) if "name" in item}

    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            entry = copy.deepcopy(item)
            if "_contributingPracticeName" not in entry:
                entry["_contributingPracticeName"] = base_source
            merged[item["name"]] = entry
    for item in (overlay_list or []):
        if "name" in item:
            if item["name"] in merged:
                existing = merged[item["name"]]
                combined = copy.deepcopy(existing)
                combined.update(copy.deepcopy(item))
                combined["_contributingPracticeName"] = overlay_source
                merged[item["name"]] = combined
            else:
                entry = copy.deepcopy(item)
                entry["_contributingPracticeName"] = overlay_source
                merged[item["name"]] = entry
    return list(merged.values())


def load_json_from_keleo(keleo_path, document_name=None, document_type=None):
    """Load a JSON document from a .keleo ZIP archive.

    Returns (data, None) on success or (None, error_string) on failure.
    If document_name is provided, matches against manifest documentName.
    If document_type is provided, filters by documentType.
    If neither is provided, returns the entry-point document.
    """
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None, f"No manifest.json in {keleo_path}"
            manifest = json.loads(zf.read("manifest.json"))
            documents = manifest.get("documents", [])
            if not documents:
                return None, f"No documents in manifest of {keleo_path}"

            target = None
            for doc in documents:
                if document_name and doc.get("documentName") == document_name:
                    if document_type is None or doc.get("documentType") == document_type:
                        target = doc
                        break
                elif document_type and doc.get("documentType") == document_type:
                    target = doc
                    break

            if target is None:
                for doc in documents:
                    if doc.get("entryPoint"):
                        target = doc
                        break

            if target is None:
                target = documents[0]

            zip_path = target.get("path", "")
            if zip_path not in zf.namelist():
                return None, f"Document path {zip_path} not found in {keleo_path}"

            data = json.loads(zf.read(zip_path))
            return data, None
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {keleo_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {keleo_path}: {e}"


def load_all_from_keleo(keleo_path):
    """Load all JSON documents from a .keleo ZIP archive.

    Returns (list_of_dicts, None) on success or (None, error_string) on failure.
    """
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None, f"No manifest.json in {keleo_path}"
            manifest = json.loads(zf.read("manifest.json"))
            documents = manifest.get("documents", [])
            if not documents:
                return None, f"No documents in manifest of {keleo_path}"

            result = []
            for doc_entry in documents:
                zip_path = doc_entry.get("path", "")
                if zip_path not in zf.namelist():
                    continue
                data = json.loads(zf.read(zip_path))
                result.append(data)
            return result, None
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {keleo_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {keleo_path}: {e}"


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
    kind = data.get("kind", "")
    if kind in ("practice", "method", "practiceBaseline"):
        return kind
    if any(key in data for key in ("practices", "practiceNames", "baselinePractice")):
        return "method"
    if "baselinePracticeName" in data:
        return "practice"
    return "practiceBaseline"
