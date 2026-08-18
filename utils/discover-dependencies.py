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
from _shared import load_json_pair, detect_kind, load_json_from_keleo

DEFAULT_SEARCH_DIRS = ["baselines", "practices", "deps", "bundles"]


def build_index(search_dirs):
    """Scan directories for JSON files and .keleo bundles, building a name-to-entries index.

    Returns:
        (index, skipped) where index is {name: [{path, kind, name, ...}]} and
        skipped is a list of paths that could not be indexed.
    """
    import zipfile as _zf

    index = defaultdict(list)
    skipped = []

    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.is_dir():
            continue

        if search_path.name == "bundles":
            for keleo_file in search_path.glob("*.keleo"):
                try:
                    with _zf.ZipFile(keleo_file, "r") as zf:
                        if "manifest.json" not in zf.namelist():
                            skipped.append(str(keleo_file))
                            continue
                        manifest = json.loads(zf.read("manifest.json"))
                        for doc in manifest.get("documents", []):
                            doc_name = doc.get("documentName")
                            doc_type = doc.get("documentType", "")
                            if not doc_name:
                                continue
                            kind_map = {
                                "practiceBaseline": "practiceBaseline",
                                "practice": "practice",
                                "method": "method",
                            }
                            kind = kind_map.get(doc_type, doc_type)
                            index[doc_name].append({
                                "name": doc_name,
                                "path": f"{keleo_file}::{doc.get('path', '')}",
                                "kind": kind,
                                "keleo_path": str(keleo_file),
                                "zip_path": doc.get("path", ""),
                            })
                except (_zf.BadZipFile, json.JSONDecodeError):
                    skipped.append(str(keleo_file))
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


def load_resolved_json(entry):
    """Load JSON for a resolved index entry, handling .keleo archives."""
    if "keleo_path" in entry:
        return load_json_from_keleo(
            entry["keleo_path"],
            document_name=entry.get("name"),
        )
    return load_json_pair(entry["path"])


def resolve_name(name, index, prefer_filesystem=False):
    """Resolve a single name against the index.

    If prefer_filesystem is True and multiple candidates exist, prefer
    non-keleo (filesystem) entries over keleo-sourced entries.
    """
    entries = index.get(name, [])
    if len(entries) == 1:
        return {"name": name, "status": "found", **entries[0]}
    elif len(entries) > 1:
        if prefer_filesystem:
            fs_entries = [e for e in entries if "keleo_path" not in e]
            if len(fs_entries) == 1:
                return {"name": name, "status": "found", **fs_entries[0]}
            if fs_entries:
                return {"name": name, "status": "ambiguous", "candidates": fs_entries}
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
        bpn = data.get("baselinePracticeName")
        if bpn and not any(n == bpn for n, _ in deps):
            deps.append((bpn, "baselinePractice"))

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


def _load_for_transitive(match, file_path_fallback):
    """Load JSON data from a resolved match entry or a filesystem path."""
    if "keleo_path" in match:
        return load_resolved_json(match)
    return load_json_pair(file_path_fallback)


def resolve_transitive(file_path_or_entry, index, visited=None, prefer_filesystem=True):
    """Recursively resolve transitive baseline dependencies.

    file_path_or_entry can be a filesystem path (str/Path) or a resolved
    index entry dict (with optional keleo_path).

    Only baselinePracticeNames are resolved transitively.
    practiceDependencyNames are reported but not recursed into.
    """
    if visited is None:
        visited = set()

    if isinstance(file_path_or_entry, dict):
        data, err = load_resolved_json(file_path_or_entry)
    else:
        data, err = load_json_pair(file_path_or_entry)
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
        match = resolve_name(dep_name, index, prefer_filesystem=prefer_filesystem)
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
                match, index, visited, prefer_filesystem=prefer_filesystem
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


def cmd_resolve(names, index, prefer_filesystem=True):
    """Handle --resolve mode."""
    results = [resolve_name(name, index, prefer_filesystem=prefer_filesystem) for name in names]
    return {"results": results}


def cmd_resolve_from(file_path, index, transitive=False, prefer_filesystem=True):
    """Handle --resolve-from mode."""
    data, err = load_json_pair(file_path)
    if err:
        return {"error": err}

    kind = detect_kind(data)
    name = data.get("name", Path(file_path).stem)
    dep_names = extract_dependency_names(data, kind)

    if transitive:
        dependencies = resolve_transitive(file_path, index, prefer_filesystem=prefer_filesystem)
    else:
        dependencies = []
        for dep_name, role in dep_names:
            match = resolve_name(dep_name, index, prefer_filesystem=prefer_filesystem)
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


def cmd_dependents(target_name, index):
    """Find all practices/methods that depend on the named baseline or practice."""
    dependents = []

    for name, entries in index.items():
        for entry in entries:
            if "keleo_path" in entry:
                continue
            data, err = load_json_pair(entry["path"])
            if err:
                continue
            kind = detect_kind(data)
            dep_names = extract_dependency_names(data, kind)
            for dep_name, role in dep_names:
                if dep_name == target_name:
                    dependents.append({
                        "name": name,
                        "path": entry["path"],
                        "kind": kind,
                        "role": role,
                    })
                    break

    return {
        "target": target_name,
        "dependents": dependents,
        "count": len(dependents),
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
        "--dependents", metavar="NAME",
        help="Find all practices/methods depending on a named baseline or practice"
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
    parser.add_argument(
        "--include-bundles", action="store_true",
        help="When ambiguous, include bundle-embedded candidates instead of preferring filesystem paths"
    )
    args = parser.parse_args()

    index, skipped = build_index(args.search_dirs)

    prefer_fs = not getattr(args, 'include_bundles', False)

    if args.list:
        result = cmd_list(index, skipped)
    elif args.resolve:
        result = cmd_resolve(args.resolve, index, prefer_filesystem=prefer_fs)
    elif args.dependents:
        result = cmd_dependents(args.dependents, index)
    elif args.resolve_from:
        if not Path(args.resolve_from).is_file():
            print(json.dumps({"error": f"File not found: {args.resolve_from}"}))
            sys.exit(1)
        result = cmd_resolve_from(args.resolve_from, index, transitive=args.transitive,
                                  prefer_filesystem=prefer_fs)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
