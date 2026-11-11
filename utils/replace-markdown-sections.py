#!/usr/bin/env python3
"""Replace uniquely marked Markdown sections from a JSON manifest."""

import argparse
import json
from pathlib import Path

__version__ = "1.1.1"


def replace_sections(text, changes, manifest_dir):
    for change in changes:
        start = change["start"]
        end = change.get("end")
        if text.count(start) != 1 or (end is not None and text.count(end) != 1):
            raise ValueError(f"section markers must occur once: {start!r}, {end!r}")
        first = text.index(start)
        last = text.index(end) if end is not None else len(text)
        if last <= first:
            raise ValueError(f"end marker precedes start marker: {end!r}")
        replacement = (manifest_dir / change["replacementFile"]).read_text(encoding="utf-8")
        separator = "\n" if end is None else "\n\n"
        text = text[:first] + replacement.rstrip("\n") + separator + text[last:]
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("manifest", type=Path, help="JSON array of start, optional end and replacementFile entries")
    parser.add_argument("--fix", action="store_true", help="Write changes; default is a dry run")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()
    changes = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(changes, list) or not changes:
        parser.error("manifest must be a nonempty JSON array")
    original = args.target.read_text(encoding="utf-8")
    updated = replace_sections(original, changes, args.manifest.parent)
    if args.fix:
        args.target.write_text(updated, encoding="utf-8")
    print(f"{args.target}: {len(changes)} section(s), {'written' if args.fix else 'dry run'}")


if __name__ == "__main__":
    main()
