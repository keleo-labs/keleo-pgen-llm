#!/usr/bin/env python3
"""Rename and deduplicate citation names in practice/method/baseline JSON files.

Reads a rename map from a JSON file or command-line arguments, then:
1. Renames citation objects (name field)
2. Merges duplicates (when new name already exists, copies missing fields from old)
3. Updates all citationNames references throughout the JSON
4. Removes duplicate citations after merge

Usage:
    python3 utils/fix-citation-names.py <file.json> --map <rename-map.json>
    python3 utils/fix-citation-names.py <file.json> --rename "Old Name=New Name" [--rename ...]
    python3 utils/fix-citation-names.py <file.json> --map <rename-map.json> --dry-run

Rename map JSON format:
    {
        "renames": [
            {"old": "Old Citation Name", "new": "New Citation Name"},
            ...
        ]
    }
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def load_rename_map(map_file):
    data = load_json(map_file)
    return [(r["old"], r["new"]) for r in data["renames"]]


def find_citation_by_name(citations, name):
    for i, c in enumerate(citations):
        if c.get("name") == name:
            return i, c
    return -1, None


def merge_citation_fields(target, source):
    """Copy fields from source to target that target is missing."""
    merged = []
    for key, value in source.items():
        if key == "name":
            continue
        if key not in target or target[key] is None:
            target[key] = value
            merged.append(key)
    return merged


def rename_citations_in_list(citations, old_name, new_name):
    """Rename or merge a citation in a citations list. Returns actions taken."""
    actions = []
    old_idx, old_citation = find_citation_by_name(citations, old_name)
    if old_idx == -1:
        return actions

    new_idx, new_citation = find_citation_by_name(citations, new_name)

    if new_citation is not None:
        merged_fields = merge_citation_fields(new_citation, old_citation)
        citations.pop(old_idx)
        actions.append(f"merged '{old_name}' into '{new_name}' (copied: {merged_fields or 'nothing'}), removed duplicate")
    else:
        old_citation["name"] = new_name
        actions.append(f"renamed '{old_name}' to '{new_name}'")

    return actions


def update_citation_names_refs(obj, old_name, new_name):
    """Recursively update citationNames arrays throughout the JSON."""
    count = 0
    if isinstance(obj, dict):
        if "citationNames" in obj and isinstance(obj["citationNames"], list):
            for i, ref in enumerate(obj["citationNames"]):
                if ref == old_name:
                    obj["citationNames"][i] = new_name
                    count += 1
            # Deduplicate citationNames after rename
            seen = set()
            deduped = []
            for ref in obj["citationNames"]:
                if ref not in seen:
                    seen.add(ref)
                    deduped.append(ref)
            obj["citationNames"] = deduped
        for v in obj.values():
            count += update_citation_names_refs(v, old_name, new_name)
    elif isinstance(obj, list):
        for item in obj:
            count += update_citation_names_refs(item, old_name, new_name)
    return count


def process_file(filepath, renames, dry_run=False):
    data = load_json(filepath)

    original = json.dumps(data)
    all_actions = []

    for old_name, new_name in renames:
        rename_actions = []

        # Rename in root-level citations
        if "citations" in data:
            actions = rename_citations_in_list(data["citations"], old_name, new_name)
            rename_actions.extend(("root", a) for a in actions)

        # Rename in practice-level citations
        if "practices" in data:
            for p in data["practices"]:
                pname = p.get("name", "unknown")
                if "citations" in p:
                    actions = rename_citations_in_list(p["citations"], old_name, new_name)
                    rename_actions.extend((pname, a) for a in actions)

        # Update all citationNames references
        ref_count = update_citation_names_refs(data, old_name, new_name)
        if ref_count > 0:
            rename_actions.append(("refs", f"updated {ref_count} citationNames reference(s)"))

        all_actions.extend(rename_actions)

    if not dry_run and json.dumps(data) != original:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    # Count final citations
    total = len(data.get("citations", []))
    if "practices" in data:
        for p in data["practices"]:
            total += len(p.get("citations", []))

    unique_names = set()
    for c in data.get("citations", []):
        unique_names.add(c.get("name", ""))
    if "practices" in data:
        for p in data["practices"]:
            for c in p.get("citations", []):
                unique_names.add(c.get("name", ""))

    result = {
        "file": filepath,
        "dryRun": dry_run,
        "renames": len(renames),
        "actions": [{"location": loc, "action": act} for loc, act in all_actions],
        "finalCitationCount": total,
        "finalUniqueNames": len(unique_names),
        "changed": json.dumps(data) != original,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Rename and deduplicate citation names")
    parser.add_argument("file", help="Practice/method/baseline JSON file")
    parser.add_argument("--map", dest="map_file", help="JSON file with rename map")
    parser.add_argument("--rename", action="append", default=[], help="Rename pair: 'Old Name=New Name'")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    renames = []
    if args.map_file:
        renames.extend(load_rename_map(args.map_file))
    for r in args.rename:
        if "=" not in r:
            print(f"Error: --rename must be 'Old=New', got: {r}", file=sys.stderr)
            sys.exit(1)
        old, new = r.split("=", 1)
        renames.append((old, new))

    if not renames:
        print("Error: no renames specified (use --map or --rename)", file=sys.stderr)
        sys.exit(1)

    result = process_file(args.file, renames, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
