#!/usr/bin/env python3
"""
Apply versioning fields to Practice Language JSON documents.

Adds schemaVersion, normalizes version to three-part semver, and populates
dependencyVersions from resolved dependency versions.

Usage:
    # Update a single file (dry-run by default):
    python3 utils/apply-versioning.py practices/name/name.json

    # Update with write:
    python3 utils/apply-versioning.py practices/name/name.json --fix

    # Bump version on a single file (for update workflows):
    python3 utils/apply-versioning.py practices/name/name.json --bump patch --fix
    python3 utils/apply-versioning.py practices/name/name.json --bump minor --fix

    # Update multiple files:
    python3 utils/apply-versioning.py deps/*.json baselines/*/*.json practices/*/*.json --fix

    # Process all documents in dependency order:
    python3 utils/apply-versioning.py --all --fix
"""
import argparse
import json
import sys
from collections import OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import (
    detect_kind,
    get_schema_version,
    increment_version,
    load_json_pair,
    MERGEABLE_ARRAYS,
)


def normalize_version(version_str):
    """Normalize version to three-part semver."""
    if not version_str:
        return "1.0.0"
    parts = version_str.split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts[:3])


def resolve_dependency_version(dep_name, version_index):
    """Look up a dependency's version from the index."""
    return version_index.get(dep_name, "")


def build_version_index(file_paths):
    """Build name → version mapping from all input files."""
    index = {}
    for path in file_paths:
        data, err = load_json_pair(path)
        if err or not isinstance(data, dict):
            continue
        name = data.get("name", "")
        version = data.get("version", "")
        if name and version:
            index[name] = normalize_version(version)
    return index


def get_dependency_names(data, kind):
    """Extract unique dependency names from a document, preserving order."""
    deps = []
    seen = set()
    def add(name):
        if name and name not in seen:
            seen.add(name)
            deps.append(name)
    if kind == "practiceBaseline":
        for name in data.get("baselinePracticeNames", []):
            add(name)
    else:
        add(data.get("baselinePracticeName", ""))
        for name in data.get("practiceDependencyNames", []):
            add(name)
    return deps


def apply_versioning(data, schema_version, version_index, today, bump=None):
    """Apply versioning fields to a document dict. Returns list of changes."""
    changes = []
    kind = detect_kind(data)

    if not data.get("schemaVersion"):
        data["schemaVersion"] = schema_version
        changes.append(f"added schemaVersion={schema_version}")
    elif data["schemaVersion"] != schema_version:
        old = data["schemaVersion"]
        data["schemaVersion"] = schema_version
        changes.append(f"updated schemaVersion {old} → {schema_version}")

    old_version = data.get("version", "")
    if bump:
        normalized = normalize_version(old_version)
        new_version = increment_version(normalized, bump)
        data["version"] = new_version
        changes.append(f"bumped version {old_version or '(empty)'} → {new_version} ({bump})")
        if not data.get("updatedAt"):
            data["updatedAt"] = today
            changes.append(f"added updatedAt={today}")
        else:
            data["updatedAt"] = today
            changes.append(f"updated updatedAt={today}")
    else:
        new_version = normalize_version(old_version)
        if old_version != new_version:
            data["version"] = new_version
            changes.append(f"normalized version {old_version!r} → {new_version}")

    dep_names = get_dependency_names(data, kind)
    if dep_names:
        existing_dvs = {
            dv.get("documentName"): dv.get("versionRange", "")
            for dv in data.get("dependencyVersions", [])
        }
        new_dvs = []
        for name in dep_names:
            if bump:
                dep_version = resolve_dependency_version(name, version_index)
                if dep_version:
                    vr = f"^{dep_version}"
                    new_dvs.append({"documentName": name, "versionRange": vr})
                    old_vr = existing_dvs.get(name, "")
                    if old_vr != vr:
                        changes.append(f"refreshed dependencyVersion {name} {old_vr or '(new)'} → {vr}")
                else:
                    changes.append(f"WARNING: no version found for dependency {name!r}")
            elif name in existing_dvs and existing_dvs[name]:
                new_dvs.append({
                    "documentName": name,
                    "versionRange": existing_dvs[name],
                })
            else:
                dep_version = resolve_dependency_version(name, version_index)
                if dep_version:
                    vr = f"^{dep_version}"
                    new_dvs.append({
                        "documentName": name,
                        "versionRange": vr,
                    })
                    changes.append(f"added dependencyVersion {name} {vr}")
                else:
                    changes.append(f"WARNING: no version found for dependency {name!r}")

        if new_dvs:
            if data.get("dependencyVersions") != new_dvs:
                data["dependencyVersions"] = new_dvs
                if not any(c.startswith(("added dependency", "refreshed dependency")) for c in changes):
                    changes.append("updated dependencyVersions")

    if not bump and data.get("updatedAt"):
        data["updatedAt"] = today
        changes.append(f"updated updatedAt={today}")

    return changes


def collect_all_files():
    """Collect all JSON files in deps/, baselines/, practices/ for --all mode."""
    files = []

    for f in sorted(Path("deps").glob("*.json")):
        if f.name == "language.schema.json":
            continue
        data, err = load_json_pair(f)
        if err or not isinstance(data, dict):
            continue
        kind = detect_kind(data)
        if kind == "practiceBaseline" and data.get("name", ""):
            files.append(str(f))

    for d in sorted(Path("baselines").iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        for f in sorted(d.glob("*.json")):
            if f.name.startswith("_") or "backup" in str(f):
                continue
            data, err = load_json_pair(f)
            if err or not isinstance(data, dict):
                continue
            files.append(str(f))

    for d in sorted(Path("practices").iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        for f in sorted(d.glob("*.json")):
            if f.name.startswith("_") or "backup" in str(f):
                continue
            data, err = load_json_pair(f)
            if err or not isinstance(data, dict):
                continue
            files.append(str(f))

    return files


def topo_sort_files(file_paths):
    """Topologically sort files so dependencies come before dependents."""
    file_data = {}
    name_to_path = {}

    for path in file_paths:
        data, err = load_json_pair(path)
        if err or not isinstance(data, dict):
            continue
        kind = detect_kind(data)
        name = data.get("name", "")
        file_data[path] = (name, kind, data)
        if name:
            name_to_path[name] = path

    sorted_paths = []
    visited = set()

    def visit(path):
        if path in visited:
            return
        visited.add(path)
        if path not in file_data:
            return
        name, kind, data = file_data[path]
        dep_names = get_dependency_names(data, kind)
        for dep_name in dep_names:
            dep_path = name_to_path.get(dep_name)
            if dep_path:
                visit(dep_path)
        sorted_paths.append(path)

    for path in file_paths:
        visit(path)

    return sorted_paths


def main():
    parser = argparse.ArgumentParser(
        description="Apply versioning fields to Practice Language JSON documents"
    )
    parser.add_argument(
        "files", nargs="*",
        help="JSON files to update"
    )
    parser.add_argument(
        "--dir",
        help="Process all JSON files in the specified directory"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process all JSON files in deps/, baselines/, practices/"
    )
    parser.add_argument(
        "--bump", choices=["patch", "minor", "major"],
        help="Increment version by bump level (patch/minor/major)"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Write changes to files (default is dry-run)"
    )

    args = parser.parse_args()

    if args.all:
        file_paths = collect_all_files()
    elif args.dir:
        import glob
        dir_path = args.dir.rstrip("/")
        file_paths = sorted(glob.glob(f"{dir_path}/*.json"))
        if not file_paths:
            parser.error(f"No JSON files found in {dir_path}/")
    elif args.files:
        file_paths = args.files
    else:
        parser.error("Provide file paths, --dir <directory>, or --all")

    file_paths = topo_sort_files(file_paths)

    if not file_paths:
        print("No files to process.")
        return

    schema_version = get_schema_version() or "1.0.0"
    today = date.today().isoformat()

    if args.bump and not args.all:
        all_files = collect_all_files()
        version_index = build_version_index(all_files)
        for path in all_files:
            data, err = load_json_pair(path)
            if err or not isinstance(data, dict):
                continue
            name = data.get("name", "")
            if name and name not in version_index:
                version_index[name] = normalize_version(data.get("version", ""))
    else:
        version_index = build_version_index(file_paths)
        for path in file_paths:
            data, err = load_json_pair(path)
            if err or not isinstance(data, dict):
                continue
            name = data.get("name", "")
            if name and name not in version_index:
                version_index[name] = normalize_version(data.get("version", ""))

    print(f"Schema version: {schema_version}")
    print(f"Files to process: {len(file_paths)}")
    print(f"Mode: {'WRITE' if args.fix else 'DRY-RUN'}")
    print()

    total_changes = 0

    for path in file_paths:
        data, err = load_json_pair(path)
        if err:
            print(f"SKIP {path}: {err}")
            continue
        if not isinstance(data, dict):
            print(f"SKIP {path}: not a JSON object")
            continue

        kind = detect_kind(data)
        name = data.get("name", Path(path).stem)

        changes = apply_versioning(data, schema_version, version_index, today, bump=args.bump)

        if changes:
            total_changes += len(changes)
            print(f"{'UPDATE' if args.fix else 'WOULD UPDATE'} {path}")
            print(f"  [{kind}] {name}")
            for c in changes:
                print(f"    - {c}")

            if args.fix:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

            version_index[name] = data.get("version", "1.0.0")
        else:
            print(f"OK {path} (no changes needed)")

    print()
    print(f"Total changes: {total_changes}")
    if not args.fix and total_changes:
        print("Run with --fix to apply changes.")


if __name__ == "__main__":
    main()
