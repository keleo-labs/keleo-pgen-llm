#!/usr/bin/env python3
"""Apply reviewed text edits to Practice Language JSON without changing other fields."""

import argparse
import json
from pathlib import Path

__version__ = "1.0.0"

def apply_edits(manifest, root, fix):
    changed = []
    pending = {}
    for entry in manifest:
        path = root / entry["file"]
        if path in pending:
            raise ValueError(f"duplicate file in manifest: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        file_changed = False
        for edit in entry["edits"]:
            parent = data
            for key in edit["path"][:-1]:
                parent = parent[key]
            key = edit["path"][-1]
            if parent[key] != edit["before"]:
                raise ValueError(f"{path}: stale text at {edit['path']}")
            if edit["before"] == edit["after"]:
                continue
            parent[key] = edit["after"]
            file_changed = True
            changed.append(f"{path}: {edit['path']}")
        if file_changed:
            pending[path] = data
    if fix:
        for path, data in pending.items():
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("manifest", type=Path, help="JSON array of file and exact before/after path edits")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root for manifest file paths")
    parser.add_argument("--fix", action="store_true", help="Write reviewed edits; default is a dry run")
    args = parser.parse_args()
    for line in apply_edits(json.loads(args.manifest.read_text(encoding="utf-8")), args.root, args.fix):
        print(line)


if __name__ == "__main__":
    main()
