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

    # Check whether a named set of practices shares a root baseline
    python3 utils/library-index.py --name "Platform Operations" "HPE OpenShift" \
        --group-by-root
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
        "baselinePracticeNames": data.get("baselinePracticeNames", []),
        "path": path_str,
    }


def _parents(entry):
    """Return the names of an entry's direct baseline parents.

    Practices and methods reference a single baseline via baselinePracticeName;
    baselines may reference one or more parent baselines via baselinePracticeNames.
    """
    parents = list(entry.get("baselinePracticeNames", []))
    direct = entry.get("baselinePracticeName", "")
    if direct and direct not in parents:
        parents.insert(0, direct)
    return parents


def resolve_roots(index):
    """Annotate each entry with the root baseline(s) at the top of its chain.

    Walks baseline parents until reaching documents with no parent of their own.
    Names that cannot be resolved in the index terminate the walk and are
    reported as roots, so an unresolvable dependency is visible rather than
    silently dropped. Cycles are broken by tracking visited names.
    """
    for entry in index.values():
        roots = []
        seen = set()
        queue = _parents(entry)
        if not queue:
            entry["rootBaselines"] = [entry["name"]]
            continue
        while queue:
            name = queue.pop(0)
            if name in seen:
                continue
            seen.add(name)
            parent = index.get(name)
            next_up = _parents(parent) if parent else []
            if next_up:
                queue.extend(next_up)
            elif name not in roots:
                roots.append(name)
        entry["rootBaselines"] = roots
    return index


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
        parents = _parents(e)
        roots = e.get("rootBaselines", [])
        if parents:
            line = f"  Baseline: {', '.join(parents)}"
            if roots and roots != parents:
                line += f" (root: {', '.join(roots)})"
            parts.append(line)
        if outcome_names:
            parts.append(f"  Outcomes: {outcome_names}")
        if e.get("keywords"):
            parts.append(f"  Keywords: {', '.join(e['keywords'])}")
        if e.get("tags"):
            parts.append(f"  Tags: {', '.join(e['tags'])}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


def format_by_root(entries):
    """Group entries by root baseline.

    Answers the planning question "do these documents share a root baseline?" —
    more than one group means separate effective contexts are required.
    """
    groups = {}
    for e in entries:
        key = ", ".join(e.get("rootBaselines", [])) or "(unresolved)"
        groups.setdefault(key, []).append(e)

    blocks = []
    for root in sorted(groups):
        members = "\n".join(f"  [{e['kind']}] {e['name']}"
                            for e in groups[root])
        blocks.append(f"Root: {root}\n{members}")
    summary = (f"{len(groups)} root baseline(s) across {len(entries)} "
               f"document(s)")
    return "\n\n".join(blocks) + f"\n\n{summary}"


def main():
    parser = argparse.ArgumentParser(
        description="Build a compact index of discoverable practices and methods")
    parser.add_argument("--kind", nargs="+",
                        help="Filter by document kind (practice, method, practiceBaseline)")
    parser.add_argument("--name", nargs="+",
                        help="Filter to specific document names (case-insensitive)")
    parser.add_argument("--compact", action="store_true",
                        help="Output compact text (one entry per block) instead of JSON")
    parser.add_argument("--group-by-root", action="store_true",
                        help="Group output by root baseline (implies compact text output)")
    parser.add_argument("--search-dirs", nargs="+", default=DEFAULT_SEARCH_DIRS,
                        help=f"Override search directories (default: {' '.join(DEFAULT_SEARCH_DIRS)})")
    parser.add_argument("-o", "--output",
                        help="Write output to file instead of stdout")
    args = parser.parse_args()

    index = resolve_roots(scan_directories(args.search_dirs))

    entries = sorted(index.values(), key=lambda e: e["name"])

    if args.kind:
        entries = [e for e in entries if e["kind"] in args.kind]

    if args.name:
        wanted = {n.casefold() for n in args.name}
        entries = [e for e in entries if e["name"].casefold() in wanted]
        found = {e["name"].casefold() for e in entries}
        for missing in sorted(n for n in wanted if n not in found):
            print(f"Warning: no document named '{missing}' was found",
                  file=sys.stderr)

    if args.group_by_root:
        output = format_by_root(entries)
    elif args.compact:
        output = format_compact(entries)
    else:
        output = json.dumps(entries, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
            if args.compact or args.group_by_root:
                f.write("\n")
        print(f"Wrote {len(entries)} entries to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
