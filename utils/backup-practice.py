#!/usr/bin/env python3
"""Create a timestamped backup of practice/baseline files.

Usage:
    python3 utils/backup-practice.py practices/my-practice/
    python3 utils/backup-practice.py practices/my-practice/ --prune 3
    python3 utils/backup-practice.py practices/my-practice/ --prune 3 --prune-only
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime


def find_backup_dirs(directory):
    """Find all backup-YYYYMMDD-HHMMSS directories, sorted oldest first."""
    backups = []
    for entry in os.listdir(directory):
        if entry.startswith("backup-") and os.path.isdir(
            os.path.join(directory, entry)
        ):
            backups.append(entry)
    backups.sort()
    return backups


def prune_backups(directory, keep):
    """Remove old backup directories, keeping only the N most recent."""
    backups = find_backup_dirs(directory)
    to_remove = backups[:-keep] if keep > 0 else backups
    removed = []
    for name in to_remove:
        path = os.path.join(directory, name)
        shutil.rmtree(path)
        removed.append(name)
    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Create timestamped backup of practice or baseline files"
    )
    parser.add_argument(
        "directory",
        nargs="+",
        help="One or more practice or baseline directories (e.g., practices/my-practice/)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific files to back up (default: *.json, 01-analysis-report.md, 02-mapping-guide.md)",
    )
    parser.add_argument(
        "--prune",
        type=int,
        metavar="N",
        help="Keep only the N most recent backups, remove older ones",
    )
    parser.add_argument(
        "--prune-only",
        action="store_true",
        help="Only prune old backups, do not create a new one",
    )
    args = parser.parse_args()

    results = []
    missing = []
    for raw in args.directory:
        directory = raw.rstrip("/")
        if not os.path.isdir(directory):
            missing.append(directory)
            continue
        results.append(backup_one(directory, args))

    if len(args.directory) == 1 and not results:
        print(json.dumps({"error": f"Directory not found: {missing[0]}"}))
        sys.exit(1)

    if len(args.directory) == 1:
        print(json.dumps(results[0], indent=2))
    else:
        print(json.dumps({
            "backups": results,
            "count": len(results),
            "missing": missing,
            "totalFiles": sum(r.get("count", 0) for r in results),
        }, indent=2))
    sys.exit(1 if missing else 0)


def backup_one(directory, args):
    """Back up one practice or baseline directory, returning a result record."""
    result = {"directory": directory}

    if not args.prune_only:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = os.path.join(directory, f"backup-{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        if args.files:
            targets = args.files
        else:
            targets = []
            for f in os.listdir(directory):
                full = os.path.join(directory, f)
                if not os.path.isfile(full):
                    continue
                # Phase outputs are numbered by convention (00-prompt-history,
                # 01-analysis-report, 01.5-distilled-essentials, 02-mapping-guide,
                # and the per-practice 02-mapping-guide-practice-*.md a method
                # directory carries). Matching the convention rather than a fixed
                # list keeps split mapping guides from being left unprotected.
                if f.endswith(".json") or (
                    f.endswith(".md") and f[:2].isdigit() and f[2] in ".-"
                ):
                    targets.append(full)

        backed_up = []
        for src in targets:
            if not os.path.isabs(src):
                src_full = (
                    os.path.join(directory, src)
                    if not os.path.exists(src)
                    else src
                )
            else:
                src_full = src
            if os.path.isfile(src_full):
                shutil.copy2(src_full, backup_dir)
                backed_up.append(os.path.basename(src_full))

        result["backupDir"] = backup_dir
        result["files"] = backed_up
        result["count"] = len(backed_up)

    if args.prune is not None:
        removed = prune_backups(directory, args.prune)
        remaining = find_backup_dirs(directory)
        result["pruned"] = removed
        result["prunedCount"] = len(removed)
        result["remaining"] = len(remaining)

    return result


if __name__ == "__main__":
    main()
