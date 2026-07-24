#!/usr/bin/env python3
"""Discover and resolve Practice Language JSON dependencies by scanning project directories.

Builds a name-to-path index from baselines/, practices/, and deps/ directories,
then resolves dependency names to file paths. Used by skills to auto-discover
dependencies instead of requiring users to provide exact file paths.

Usage:
    # Resolve specific names to file paths
    python3 utils/discover-dependencies.py --resolve "Platform Adoption Essentials"

    # Extract dependency names from a JSON file and resolve them
    python3 utils/discover-dependencies.py --resolve-from baselines/idp-essentials/idp-essentials.json

    # Recursively resolve transitive baseline dependencies
    python3 utils/discover-dependencies.py --resolve-from baselines/idp-essentials/idp-essentials.json --transitive

    # List all discoverable JSON files in the project
    python3 utils/discover-dependencies.py --list
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json_pair, detect_kind

DEFAULT_SEARCH_DIRS = ["baselines", "practices", "deps"]


def build_index(search_dirs):
    """Scan directories for JSON files and build a name-to-entries index.

    Returns:
        (index, skipped) where index is {name: [{path, kind, name}]} and
        skipped is a list of paths that could not be indexed.
    """
    index = defaultdict(list)
    skipped = []

    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.is_dir():
            continue

        json_files = []
        if search_path.name == "deps":
            json_files = list(search_path.glob("*.json"))
        else:
            json_files = list(search_path.glob("*/*.json"))
            json_files.extend(search_path.glob("*.json"))

        for json_file in json_files:
            if json_file.name.startswith("_"):
                continue
            if "backup" in str(json_file).lower():
                continue

            data, err = load_json_pair(json_file)
            if err:
                skipped.append(str(json_file))
                continue

            name = data.get("name")
            if not name:
                skipped.append(str(json_file))
                continue

            kind = detect_kind(data)
            index[name].append({
                "name": name,
                "path": str(json_file),
                "kind": kind,
            })

    return dict(index), skipped


def resolve_name(name, index):
    """Resolve a single name against the index."""
    entries = index.get(name, [])
    if len(entries) == 1:
        return {"name": name, "status": "found", **entries[0]}
    elif len(entries) > 1:
        return {"name": name, "status": "ambiguous", "candidates": entries}
    else:
        return {"name": name, "status": "not_found"}


def extract_dependency_names(data, kind):
    """Extract dependency names and their roles from a JSON file.

    Returns list of (name, role) tuples.
    """
    deps = []

    if kind == "practiceBaseline":
        for name in data.get("baselinePracticeNames", []):
            deps.append((name, "baselinePractice"))

    elif kind == "practice":
        bpn = data.get("baselinePracticeName")
        if bpn:
            deps.append((bpn, "baselinePractice"))
        for name in data.get("practiceDependencyNames", []):
            deps.append((name, "practiceDependency"))

    elif kind == "method":
        bpn = data.get("baselinePracticeName")
        if bpn:
            deps.append((bpn, "baselinePractice"))
        seen_practice_deps = set()
        for name in data.get("practiceDependencyNames", []):
            if name not in seen_practice_deps:
                deps.append((name, "practiceDependency"))
                seen_practice_deps.add(name)
        for practice in data.get("practices", []):
            for name in practice.get("practiceDependencyNames", []):
                if name not in seen_practice_deps:
                    deps.append((name, "practiceDependency"))
                    seen_practice_deps.add(name)

    return deps


def resolve_transitive(file_path, index, visited=None):
    """Recursively resolve transitive baseline dependencies.

    Only baselinePracticeNames are resolved transitively.
    practiceDependencyNames are reported but not recursed into.
    """
    if visited is None:
        visited = set()

    data, err = load_json_pair(file_path)
    if err:
        return []

    kind = detect_kind(data)
    name = data.get("name", "")

    if name in visited:
        return []
    visited.add(name)

    dep_names = extract_dependency_names(data, kind)
    results = []

    for dep_name, role in dep_names:
        match = resolve_name(dep_name, index)
        dep_result = {
            "name": dep_name,
            "role": role,
            "status": match["status"],
            "path": match.get("path"),
            "kind": match.get("kind"),
            "transitiveDependencies": [],
        }

        if match.get("candidates"):
            dep_result["candidates"] = match["candidates"]

        if match["status"] == "found" and role != "practiceDependency":
            dep_result["transitiveDependencies"] = resolve_transitive(
                match["path"], index, visited
            )

        results.append(dep_result)

    return results


def cmd_list(index, skipped):
    """Handle --list mode."""
    files = []
    for name, entries in sorted(index.items()):
        for entry in entries:
            files.append(entry)

    return {
        "files": files,
        "totalFiles": len(files),
        "skippedFiles": skipped,
    }


def cmd_resolve(names, index):
    """Handle --resolve mode."""
    results = [resolve_name(name, index) for name in names]
    return {"results": results}


def cmd_resolve_from(file_path, index, transitive=False):
    """Handle --resolve-from mode."""
    data, err = load_json_pair(file_path)
    if err:
        return {"error": err}

    kind = detect_kind(data)
    name = data.get("name", Path(file_path).stem)
    dep_names = extract_dependency_names(data, kind)

    if transitive:
        dependencies = resolve_transitive(file_path, index)
    else:
        dependencies = []
        for dep_name, role in dep_names:
            match = resolve_name(dep_name, index)
            dep_result = {
                "name": dep_name,
                "role": role,
                "status": match["status"],
                "path": match.get("path"),
                "kind": match.get("kind"),
            }
            if match.get("candidates"):
                dep_result["candidates"] = match["candidates"]
            dependencies.append(dep_result)

    unresolved = [d["name"] for d in dependencies if d["status"] == "not_found"]
    ambiguous = [d["name"] for d in dependencies if d["status"] == "ambiguous"]

    return {
        "inputFile": str(file_path),
        "inputKind": kind,
        "inputName": name,
        "dependencies": dependencies,
        "unresolved": unresolved,
        "ambiguous": ambiguous,
        "summary": {
            "total": len(dependencies),
            "resolved": sum(1 for d in dependencies if d["status"] == "found"),
            "unresolved": len(unresolved),
            "ambiguous": len(ambiguous),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Discover and resolve Practice Language JSON dependencies"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--resolve", nargs="+", metavar="NAME",
        help="Resolve one or more practice/baseline names to file paths"
    )
    group.add_argument(
        "--resolve-from", metavar="FILE",
        help="Extract dependency names from a JSON file and resolve them"
    )
    group.add_argument(
        "--list", action="store_true",
        help="List all discoverable JSON files with names and kinds"
    )
    parser.add_argument(
        "--transitive", action="store_true",
        help="Recursively resolve transitive baseline dependencies (with --resolve-from)"
    )
    parser.add_argument(
        "--search-dirs", nargs="+", default=DEFAULT_SEARCH_DIRS,
        help=f"Override search directories (default: {' '.join(DEFAULT_SEARCH_DIRS)})"
    )
    args = parser.parse_args()

    index, skipped = build_index(args.search_dirs)

    if args.list:
        result = cmd_list(index, skipped)
    elif args.resolve:
        result = cmd_resolve(args.resolve, index)
    elif args.resolve_from:
        if not Path(args.resolve_from).is_file():
            print(json.dumps({"error": f"File not found: {args.resolve_from}"}))
            sys.exit(1)
        result = cmd_resolve_from(args.resolve_from, index, transitive=args.transitive)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
