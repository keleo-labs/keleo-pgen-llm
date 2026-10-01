#!/usr/bin/env python3
"""Build a compact, LLM-readable index of all discoverable practices and methods.

Scans the same directories as discover-dependencies.py (baselines/, practices/,
deps/, bundles/) and extracts matchable metadata from each document: name, kind,
description, outcomes, keywords, tags, and baseline reference.

Usage:
    # Full index of practices and methods
    python3 utils/library-index.py --kind practice method

    # Compact one-line-per-entry view for LLM consumption
    python3 utils/library-index.py --kind practice method --compact

    # All document types, full detail, written to file
    python3 utils/library-index.py -o /tmp/library-index.json

    # Include baselines
    python3 utils/library-index.py --kind practice method practiceBaseline
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json_pair, detect_kind

DEFAULT_SEARCH_DIRS = ["baselines", "practices", "deps", "bundles"]


def truncate(text, max_len):
    """Truncate text to max_len, appending ellipsis if shortened."""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


def _flatten_tags(tags):
    """Flatten tags dict {category: [values]} or list into a flat list of strings."""
    if isinstance(tags, dict):
        flat = []
        for values in tags.values():
            if isinstance(values, list):
                flat.extend(str(v) for v in values)
        return flat
    if isinstance(tags, list):
        return [t.get("name", str(t)) if isinstance(t, dict) else str(t)
                for t in tags]
    return []


def extract_metadata(data, path_str):
    """Extract matchable metadata from a parsed practice/method/baseline JSON."""
    outcomes = []
    for o in data.get("outcomes", []):
        outcomes.append({
            "name": o.get("name", ""),
            "description": truncate(o.get("description", ""), 150),
        })

    return {
        "name": data.get("name", ""),
        "kind": detect_kind(data),
        "description": truncate(data.get("description", ""), 200),
        "outcomes": outcomes,
        "keywords": data.get("keywords", []),
        "tags": _flatten_tags(data.get("tags", {})),
        "baselinePracticeName": data.get("baselinePracticeName", ""),
        "path": path_str,
    }


def scan_directories(search_dirs):
    """Scan directories for Practice Language JSON files and .keleo bundles.

    Returns a dict of {name: metadata_dict}, deduplicating by name with
    filesystem paths preferred over bundle-embedded copies.
    """
    index = {}
    bundle_pending = []

    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.is_dir():
            continue

        if search_path.name == "bundles":
            for keleo_file in search_path.glob("*.keleo"):
                try:
                    with zipfile.ZipFile(keleo_file, "r") as zf:
                        if "manifest.json" not in zf.namelist():
                            continue
                        manifest = json.loads(zf.read("manifest.json"))
                        for doc in manifest.get("documents", []):
                            zip_path = doc.get("path", "")
                            if not zip_path or zip_path not in zf.namelist():
                                continue
                            try:
                                data = json.loads(zf.read(zip_path))
                            except (json.JSONDecodeError, KeyError):
                                continue
                            name = data.get("name")
                            if not name:
                                continue
                            meta = extract_metadata(
                                data, f"{keleo_file}::{zip_path}")
                            bundle_pending.append((name, meta))
                except (zipfile.BadZipFile, json.JSONDecodeError):
                    continue
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
                continue

            name = data.get("name")
            if not name:
                continue

            meta = extract_metadata(data, str(json_file))
            index[name] = meta

    for name, meta in bundle_pending:
        if name not in index:
            index[name] = meta

    return index


def format_compact(entries):
    """Format entries as compact one-line-per-entry text."""
    lines = []
    for e in entries:
        desc = e.get("description", "")
        outcome_names = ", ".join(o["name"] for o in e.get("outcomes", [])
                                  if o.get("name"))
        parts = [f"[{e['kind']}] {e['name']}"]
        if desc:
            parts.append(f"  {desc}")
        if outcome_names:
            parts.append(f"  Outcomes: {outcome_names}")
        if e.get("keywords"):
            parts.append(f"  Keywords: {', '.join(e['keywords'])}")
        if e.get("tags"):
            parts.append(f"  Tags: {', '.join(e['tags'])}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Build a compact index of discoverable practices and methods")
    parser.add_argument("--kind", nargs="+",
                        help="Filter by document kind (practice, method, practiceBaseline)")
    parser.add_argument("--compact", action="store_true",
                        help="Output compact text (one entry per block) instead of JSON")
    parser.add_argument("--search-dirs", nargs="+", default=DEFAULT_SEARCH_DIRS,
                        help=f"Override search directories (default: {' '.join(DEFAULT_SEARCH_DIRS)})")
    parser.add_argument("-o", "--output",
                        help="Write output to file instead of stdout")
    args = parser.parse_args()

    index = scan_directories(args.search_dirs)

    entries = sorted(index.values(), key=lambda e: e["name"])

    if args.kind:
        entries = [e for e in entries if e["kind"] in args.kind]

    if args.compact:
        output = format_compact(entries)
    else:
        output = json.dumps(entries, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
            if args.compact:
                f.write("\n")
        print(f"Wrote {len(entries)} entries to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
