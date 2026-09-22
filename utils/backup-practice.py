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
        help="Path to practice or baseline directory (e.g., practices/my-practice/)",
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

    directory = args.directory.rstrip("/")
    if not os.path.isdir(directory):
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    result = {}

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
                if f.endswith(".json") or f in (
                    "01-analysis-report.md",
                    "01.5-distilled-essentials.md",
                    "02-mapping-guide.md",
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

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
