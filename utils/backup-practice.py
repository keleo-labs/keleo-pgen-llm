#!/usr/bin/env python3
"""Create a timestamped backup of practice/baseline files."""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime


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
    args = parser.parse_args()

    directory = args.directory.rstrip("/")
    if not os.path.isdir(directory):
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

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
            src_full = os.path.join(directory, src) if not os.path.exists(src) else src
        else:
            src_full = src
        if os.path.isfile(src_full):
            shutil.copy2(src_full, backup_dir)
            backed_up.append(os.path.basename(src_full))

    result = {"backupDir": backup_dir, "files": backed_up, "count": len(backed_up)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
