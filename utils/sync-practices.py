#!/usr/bin/env python3
"""Synchronize shared practice JSON files between method directories.

When practices in one method directory are updated, other methods that contain
copies of the same practices need to be updated too.  This utility finds
practices with matching ``name`` fields across ``practices/*/`` directories
and copies newer versions from the source to each target.

Usage:
    # Dry-run — show what would be synced
    python3 utils/sync-practices.py practices/red-hat-sales-plays/

    # Apply changes
    python3 utils/sync-practices.py practices/red-hat-sales-plays/ --fix

    # Apply and rebuild affected .keleo bundles
    python3 utils/sync-practices.py practices/red-hat-sales-plays/ --fix --rebuild-bundles

    # Machine-readable output
    python3 utils/sync-practices.py practices/red-hat-sales-plays/ --json
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json_pair, detect_kind


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_semver(version_str):
    """Parse a version string into a comparable tuple of ints.

    Handles shortened forms like ``"1.0"`` or ``"2"`` by zero-padding.
    Returns ``(0, 0, 0)`` for empty/unparseable strings so they sort lowest.
    """
    if not version_str:
        return (0, 0, 0)
    parts = version_str.split(".")
    try:
        while len(parts) < 3:
            parts.append("0")
        return tuple(int(p) for p in parts[:3])
    except (ValueError, TypeError):
        return (0, 0, 0)


def should_skip_file(path):
    """Return True if *path* should be excluded from scanning."""
    name = path.name
    if name.startswith("_"):
        return True
    if name.startswith("change-request"):
        return True
    if "backup" in str(path).lower():
        return True
    return False


def scan_directory(directory):
    """Return a dict mapping ``name`` -> ``(Path, version, kind)`` for
    every eligible practice/method JSON in *directory*.
    """
    directory = Path(directory)
    index = {}
    if not directory.is_dir():
        return index
    for f in sorted(directory.glob("*.json")):
        if should_skip_file(f):
            continue
        data, err = load_json_pair(f)
        if err or not isinstance(data, dict):
            continue
        name = data.get("name", "")
        version = data.get("version", "")
        kind = detect_kind(data)
        if name:
            index[name] = (f, version, kind)
    return index


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def sync_practices(source_dir, fix=False):
    """Compare source practices against all other ``practices/*/`` directories.

    Returns a list of result dicts, one per target directory, each containing
    a list of per-practice action records.
    """
    source_dir = Path(source_dir).resolve()
    practices_root = source_dir.parent  # e.g. <repo>/practices

    if not practices_root.is_dir():
        print(json.dumps({"error": f"Parent directory does not exist: {practices_root}"}))
        sys.exit(1)

    source_index = scan_directory(source_dir)
    if not source_index:
        print(json.dumps({"error": f"No eligible practice JSON files found in {source_dir}"}))
        sys.exit(1)

    results = []

    for target_dir in sorted(practices_root.iterdir()):
        if not target_dir.is_dir():
            continue
        if target_dir.resolve() == source_dir:
            continue

        target_index = scan_directory(target_dir)
        if not target_index:
            continue

        # Only process directories that share at least one practice name
        shared_names = set(source_index.keys()) & set(target_index.keys())
        if not shared_names:
            continue

        dir_result = {
            "target": str(target_dir),
            "actions": [],
        }

        for name in sorted(target_index.keys()):
            target_path, target_version, target_kind = target_index[name]

            if name not in source_index:
                dir_result["actions"].append({
                    "name": name,
                    "status": "not_in_source",
                    "target_file": target_path.name,
                    "target_version": target_version,
                })
                continue

            source_path, source_version, source_kind = source_index[name]
            src_ver = parse_semver(source_version)
            tgt_ver = parse_semver(target_version)

            if src_ver > tgt_ver:
                action = {
                    "name": name,
                    "status": "sync",
                    "source_file": source_path.name,
                    "target_file": target_path.name,
                    "source_version": source_version,
                    "target_version": target_version,
                }
                if fix:
                    try:
                        shutil.copy2(str(source_path), str(target_path))
                        action["applied"] = True
                    except OSError as e:
                        action["applied"] = False
                        action["error"] = str(e)
                dir_result["actions"].append(action)

            elif src_ver == tgt_ver:
                dir_result["actions"].append({
                    "name": name,
                    "status": "up_to_date",
                    "target_file": target_path.name,
                    "version": target_version,
                })

            else:
                # Target is newer than source
                dir_result["actions"].append({
                    "name": name,
                    "status": "target_newer",
                    "source_file": source_path.name,
                    "target_file": target_path.name,
                    "source_version": source_version,
                    "target_version": target_version,
                })

        results.append(dir_result)

    return results


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_results(results, source_dir, fix):
    """Print human-readable sync results."""
    source_dir = Path(source_dir)
    print(f"Syncing from {source_dir}/\n")

    total_sync = 0
    total_up_to_date = 0
    total_not_in_source = 0
    total_target_newer = 0

    for dr in results:
        target = dr["target"]
        print(f"Target: {target}/")

        for a in dr["actions"]:
            status = a["status"]
            name = a["name"]

            if status == "sync":
                src_file = a["source_file"]
                tgt_file = a["target_file"]
                src_ver = a["source_version"]
                tgt_ver = a["target_version"]
                file_note = f"{src_file} -> {tgt_file}" if src_file != tgt_file else tgt_file
                if fix:
                    if a.get("applied"):
                        print(f"  ✓ {name}: {tgt_ver} -> {src_ver} ({file_note})")
                    else:
                        print(f"  ✗ {name}: {tgt_ver} -> {src_ver} FAILED: {a.get('error', '?')} ({file_note})")
                else:
                    print(f"  ✓ {name}: {tgt_ver} -> {src_ver} ({file_note})")
                total_sync += 1

            elif status == "up_to_date":
                ver = a["version"]
                print(f"  · {name}: {ver} = {ver} (up to date)")
                total_up_to_date += 1

            elif status == "target_newer":
                src_ver = a["source_version"]
                tgt_ver = a["target_version"]
                print(f"  ⚠ {name}: target {tgt_ver} > source {src_ver} (skipped)")
                total_target_newer += 1

            elif status == "not_in_source":
                print(f"  ⚠ {name}: not in source (skipped)")
                total_not_in_source += 1

        print()

    # Summary
    parts = []
    if total_sync:
        verb = "synced" if fix else "would sync"
        parts.append(f"{total_sync} {verb}")
    if total_up_to_date:
        parts.append(f"{total_up_to_date} up-to-date")
    if total_target_newer:
        parts.append(f"{total_target_newer} target-newer")
    if total_not_in_source:
        parts.append(f"{total_not_in_source} target-only")

    print(f"Summary: {', '.join(parts)}")

    if not fix and total_sync:
        print("(dry run — use --fix to apply)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Synchronize shared practice files between method directories"
    )
    parser.add_argument(
        "source_dir",
        help="Source directory containing the authoritative practice JSON files"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply changes (default is dry-run)"
    )
    parser.add_argument(
        "--rebuild-bundles", action="store_true",
        help="After syncing, rebuild affected .keleo bundles via rebuild-keleo.py"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(json.dumps({"error": f"Source directory does not exist: {source_dir}"}))
        sys.exit(1)

    results = sync_practices(source_dir, fix=args.fix)

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    else:
        print_results(results, source_dir, fix=args.fix)

    # Rebuild bundles if requested and changes were applied
    if args.rebuild_bundles and args.fix:
        any_synced = any(
            a["status"] == "sync" and a.get("applied")
            for dr in results
            for a in dr["actions"]
        )
        if any_synced:
            if not args.json:
                print("\nRebuilding affected bundles...")
            rebuild_result = subprocess.run(
                [sys.executable, "utils/rebuild-keleo.py", "--all", "--if-changed"],
                capture_output=True, text=True
            )
            if not args.json:
                if rebuild_result.stdout:
                    print(rebuild_result.stdout)
                if rebuild_result.returncode != 0 and rebuild_result.stderr:
                    print(f"rebuild-keleo.py error: {rebuild_result.stderr}", file=sys.stderr)
        else:
            if not args.json:
                print("\nNo changes applied, skipping bundle rebuild.")


if __name__ == "__main__":
    main()
