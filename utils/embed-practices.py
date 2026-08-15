#!/usr/bin/env python3
"""
Re-embed updated standalone practice JSON files into a method JSON file.

Replaces inline scripts that updated embedded practices and aggregated assets.

Usage:
    # Dry run
    python3 utils/embed-practices.py method.json practice1.json practice2.json

    # Re-embed and save
    python3 utils/embed-practices.py method.json practice1.json practice2.json --fix
"""
import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def _collect_assets(data):
    """Collect all assets from a document, keyed by name (last-wins)."""
    assets = OrderedDict()
    for asset in data.get("assets", []):
        name = asset.get("name")
        if name:
            assets[name] = asset
    return assets


def embed_practices(method_data, practice_files):
    """Replace embedded practices with standalone versions and aggregate assets.

    Returns (replaced_names, not_found_names, total_asset_count).
    """
    practices = method_data.get("practices", [])
    practice_index = {p.get("name"): i for i, p in enumerate(practices)}

    replaced = []
    not_found = []

    for pf in practice_files:
        practice_data = load_json(pf)
        name = practice_data.get("name")
        if not name:
            not_found.append(str(pf))
            continue

        if name in practice_index:
            idx = practice_index[name]
            practices[idx] = practice_data
            replaced.append(name)
        else:
            not_found.append(name)

    method_data["practices"] = practices

    # Aggregate assets: method-level first, then each embedded practice.
    all_assets = _collect_assets(method_data)
    for practice in practices:
        for name, asset in _collect_assets(practice).items():
            all_assets[name] = asset

    if all_assets:
        method_data["assets"] = list(all_assets.values())
    elif "assets" in method_data:
        # Keep empty array if it was already present.
        method_data["assets"] = []

    return replaced, not_found, len(all_assets)


def main():
    parser = argparse.ArgumentParser(
        description="Re-embed standalone practice JSON files into a method JSON."
    )
    parser.add_argument("method", help="Method JSON file to update")
    parser.add_argument(
        "practices", nargs="+",
        help="Standalone practice JSON files to embed",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Write changes to the file (default is dry run)",
    )
    args = parser.parse_args()

    method_path = Path(args.method)
    if not method_path.exists():
        print(json.dumps({"error": f"File not found: {args.method}"}))
        sys.exit(1)

    method_data = load_json(args.method)

    if not method_data.get("practices"):
        print(json.dumps({
            "error": "Method JSON has no 'practices' array to embed into"
        }))
        sys.exit(1)

    replaced, not_found, total_assets = embed_practices(
        method_data, args.practices
    )

    report = {
        "file": str(method_path),
        "replaced": replaced,
        "notFound": not_found,
        "totalAssets": total_assets,
        "applied": args.fix,
    }

    if args.fix:
        with open(method_path, "w", encoding="utf-8") as f:
            json.dump(method_data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(json.dumps(report, indent=2))

    if not_found:
        sys.exit(1)


if __name__ == "__main__":
    main()
