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

    # Compute dependency tiers for a method's practices
    python3 utils/discover-dependencies.py --tiers practices/red-hat-sales-plays/red-hat-sales-plays.json

    # Find all methods/practices that contain a given practice name
    python3 utils/discover-dependencies.py --consumers "AI Platform TDP"
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json_pair, detect_kind, load_json_from_keleo, get_project_root

DEFAULT_SEARCH_DIRS = ["baselines", "practices", "deps", "bundles"]
REMOTE_INDEX_PATH = "bundles/.remote-index.json"


def _load_remote_index():
    """Load cached remote index from bundles/.remote-index.json."""
    index_path = get_project_root() / REMOTE_INDEX_PATH
    if not index_path.exists():
        return None
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _refresh_remote_index_if_stale(max_age=3600):
    """Refresh remote index via studio-client if stale. Returns cached index or None."""
    cached = _load_remote_index()
    if cached:
        fetched = cached.get("_fetchedAt", "")
        if fetched:
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(fetched.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                if age < max_age:
                    return cached
            except (ValueError, TypeError):
                pass

    studio_client = Path(__file__).resolve().parent / "studio-client.py"
    if studio_client.exists():
        import subprocess
        try:
            subprocess.run(
                [sys.executable, str(studio_client), "--index", "--max-age", str(max_age)],
                capture_output=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass
        return _load_remote_index()

    return cached


def build_index(search_dirs, include_remote=False):
    """Scan directories for JSON files and .keleo bundles, building a name-to-entries index.

    Args:
        search_dirs: List of directory paths to scan.
        include_remote: If True, also include entries from the cached remote index.

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

    if include_remote:
        remote = _load_remote_index()
        if remote:
            for bundle in remote.get("bundles", []):
                bname = bundle.get("name", "")
                if not bname:
                    continue
                if bname in index:
                    continue
                index[bname].append({
                    "name": bname,
                    "kind": "",
                    "version": bundle.get("version", ""),
                    "slug": bundle.get("slug", ""),
                    "remote": True,
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
    Remote-only entries return status "remote" instead of "found".
    """
    entries = index.get(name, [])
    if not entries:
        return {"name": name, "status": "not_found"}

    local_entries = [e for e in entries if not e.get("remote")]
    remote_entries = [e for e in entries if e.get("remote")]

    if local_entries:
        if len(local_entries) == 1:
            return {"name": name, "status": "found", **local_entries[0]}
        if prefer_filesystem:
            fs_entries = [e for e in local_entries if "keleo_path" not in e]
            if len(fs_entries) == 1:
                return {"name": name, "status": "found", **fs_entries[0]}
            if fs_entries:
                return {"name": name, "status": "ambiguous", "candidates": fs_entries}
        return {"name": name, "status": "ambiguous", "candidates": local_entries}

    if remote_entries:
        return {"name": name, "status": "remote", **remote_entries[0]}

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


def _load_practices_from_method_dir(method_data, method_path):
    """Load practice JSON files from a method's directory, matched by name field.

    Args:
        method_data: Parsed method JSON dict.
        method_path: Path to the method JSON file.

    Returns:
        Dict mapping practice name to (data, file_path) tuples.
        Practices not found in the directory are omitted.
    """
    practice_names = set(method_data.get("practiceNames", []))
    method_dir = Path(method_path).parent
    practices = {}

    for json_file in method_dir.glob("*.json"):
        if json_file.name.startswith("_"):
            continue
        if "backup" in str(json_file).lower():
            continue
        data, err = load_json_pair(json_file)
        if err:
            continue
        name = data.get("name")
        if name and name in practice_names:
            practices[name] = (data, json_file)

    return practices


def cmd_tiers(file_path):
    """Compute dependency tiers for all practices in a method.

    Tier 1: practices whose practiceDependencyNames contains no other
            practice in the method's practiceNames.
    Tier 2: practices that depend on other practices within the method.
    """
    data, err = load_json_pair(file_path)
    if err:
        return {"error": err}

    kind = detect_kind(data)
    if kind != "method":
        return {"error": f"Expected a method JSON, got kind '{kind}'"}

    method_name = data.get("name", Path(file_path).stem)
    practice_names = set(data.get("practiceNames", []))
    if not practice_names:
        return {"error": "Method has no practiceNames"}

    practices = _load_practices_from_method_dir(data, file_path)

    tier1 = []
    tier2 = []
    not_found = []

    for pname in sorted(practice_names):
        if pname not in practices:
            not_found.append(pname)
            continue

        pdata, _ = practices[pname]
        dep_names = pdata.get("practiceDependencyNames", [])
        intra_method_deps = [d for d in dep_names if d in practice_names]

        if intra_method_deps:
            tier2.append({"name": pname, "dependsOn": sorted(intra_method_deps)})
        else:
            tier1.append(pname)

    return {
        "method": method_name,
        "tier1": tier1,
        "tier2": tier2,
        "notFound": not_found if not_found else None,
    }


def fmt_tiers(result):
    """Format tier result as human-readable text."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [f"Dependency Tiers for {result['method']}:", ""]

    lines.append("Tier 1 (baseline-only, can run in parallel):")
    if result["tier1"]:
        for name in result["tier1"]:
            lines.append(f"  - {name}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Tier 2 (depends on other practices, run after Tier 1):")
    if result["tier2"]:
        for entry in result["tier2"]:
            deps_str = ", ".join(entry["dependsOn"])
            lines.append(f"  - {entry['name']} (depends on: {deps_str})")
    else:
        lines.append("  (none)")

    if result.get("notFound"):
        lines.append("")
        lines.append("Not found in directory:")
        for name in result["notFound"]:
            lines.append(f"  - {name}")

    return "\n".join(lines)


def cmd_consumers(target_name, search_dirs):
    """Find all methods/practices that contain or reference a given practice name.

    Scans practice directories for JSON files whose name field matches, and
    checks whether any method in the same directory includes the name in
    practiceNames.
    """
    consumers = []

    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.is_dir():
            continue
        if search_path.name not in ("practices", "baselines"):
            continue

        for subdir in sorted(search_path.iterdir()):
            if not subdir.is_dir():
                continue

            matching_files = []
            methods_containing = []

            for json_file in subdir.glob("*.json"):
                if json_file.name.startswith("_"):
                    continue
                if "backup" in str(json_file).lower():
                    continue

                data, err = load_json_pair(json_file)
                if err:
                    continue

                name = data.get("name")
                kind = detect_kind(data)

                if name == target_name:
                    matching_files.append({
                        "fileName": json_file.name,
                        "version": data.get("version"),
                        "kind": kind,
                    })

                if kind == "method" and target_name in (data.get("practiceNames") or []):
                    methods_containing.append(name or json_file.stem)

            if matching_files or methods_containing:
                consumer = {
                    "directory": str(subdir),
                    "files": matching_files,
                    "methods": methods_containing,
                }
                consumers.append(consumer)

    return {
        "practiceName": target_name,
        "consumers": consumers,
        "count": len(consumers),
    }


def fmt_consumers(result):
    """Format consumers result as human-readable text."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [f'Consumers of "{result["practiceName"]}":']

    if not result["consumers"]:
        lines.append("  (none found)")
        return "\n".join(lines)

    for consumer in result["consumers"]:
        lines.append("")
        lines.append(f"  {consumer['directory']}/")

        for f in consumer["files"]:
            version_str = f" (v{f['version']})" if f.get("version") else ""
            lines.append(f"    file: {f['fileName']}{version_str}")

        for method_name in consumer["methods"]:
            lines.append(f"    method: {method_name} (in practiceNames)")

    return "\n".join(lines)


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
        "--tiers", metavar="FILE",
        help="Compute dependency tiers for a method's practices"
    )
    group.add_argument(
        "--consumers", metavar="NAME",
        help="Find all methods/practices containing or referencing a named practice"
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
        "--json", action="store_true",
        help="Output as JSON instead of human-readable text (for --tiers, --consumers)"
    )
    parser.add_argument(
        "--search-dirs", nargs="+", default=DEFAULT_SEARCH_DIRS,
        help=f"Override search directories (default: {' '.join(DEFAULT_SEARCH_DIRS)})"
    )
    parser.add_argument(
        "--include-bundles", action="store_true",
        help="When ambiguous, include bundle-embedded candidates instead of preferring filesystem paths"
    )
    parser.add_argument(
        "--remote", action="store_true",
        help="Check cached remote index when local resolution fails"
    )
    parser.add_argument(
        "--auto-pull", action="store_true",
        help="With --remote: automatically download remote bundles that aren't found locally"
    )
    args = parser.parse_args()

    prefer_fs = not getattr(args, 'include_bundles', False)
    use_remote = getattr(args, 'remote', False)
    auto_pull = getattr(args, 'auto_pull', False)

    if use_remote:
        _refresh_remote_index_if_stale()

    if args.tiers:
        if not Path(args.tiers).is_file():
            print(json.dumps({"error": f"File not found: {args.tiers}"}) if args.json
                  else f"Error: File not found: {args.tiers}")
            sys.exit(1)
        result = cmd_tiers(args.tiers)
        print(json.dumps(result, indent=2) if args.json else fmt_tiers(result))
        sys.exit(0)

    if args.consumers:
        result = cmd_consumers(args.consumers, args.search_dirs)
        print(json.dumps(result, indent=2) if args.json else fmt_consumers(result))
        sys.exit(0)

    index, skipped = build_index(args.search_dirs, include_remote=use_remote)

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

    if auto_pull and use_remote:
        result = _auto_pull_remote(result, index, args.search_dirs, prefer_fs)

    print(json.dumps(result, indent=2))


def _auto_pull_remote(result, index, search_dirs, prefer_fs):
    """Download remote-only entries and re-resolve them locally."""
    import subprocess

    studio_client = Path(__file__).resolve().parent / "studio-client.py"
    if not studio_client.exists():
        return result

    pulled = False

    def _pull_and_flag(items):
        nonlocal pulled
        for item in items:
            if item.get("status") == "remote":
                name = item.get("name", "")
                try:
                    proc = subprocess.run(
                        [sys.executable, str(studio_client), "--pull", name, "--json"],
                        capture_output=True, text=True, timeout=60,
                    )
                    if proc.returncode == 0:
                        pulled = True
                        print(f"Auto-pulled: {name}", file=sys.stderr)
                except (subprocess.TimeoutExpired, OSError):
                    pass
            for dep in item.get("transitiveDependencies", []):
                _pull_and_flag([dep])

    if "results" in result:
        _pull_and_flag(result["results"])
    if "dependencies" in result:
        _pull_and_flag(result["dependencies"])

    if pulled:
        new_index, _ = build_index(search_dirs, include_remote=True)
        if "results" in result:
            names = [r["name"] for r in result["results"]]
            result = cmd_resolve(names, new_index, prefer_filesystem=prefer_fs)
        elif "dependencies" in result and "inputFile" in result:
            result = cmd_resolve_from(
                result["inputFile"], new_index,
                transitive="transitiveDependencies" in json.dumps(result),
                prefer_filesystem=prefer_fs,
            )

    return result


if __name__ == "__main__":
    main()
