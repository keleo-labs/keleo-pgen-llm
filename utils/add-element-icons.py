#!/usr/bin/env python3
"""Add Font Awesome icon assets to practice/baseline elements in bulk.

Takes a JSON practice file and an icon mapping file, then:
1. Creates font-character Asset entries in the top-level assets[] array
2. Sets assetNames on the matching elements
3. Saves the result (or dry-runs)

Icon mapping format (JSON):
{
  "mappings": [
    {"section": "focuses", "name": "Value", "icon": "fa-coins"},
    {"section": "alphas", "name": "Platform", "icon": "fa-cubes"},
    {"section": "activities", "name": "Deploy Service", "icon": "fa-rocket"}
  ]
}

Supported sections: focuses, narrativeTypes, competencies, alphas,
activitySpaces, activities, workProducts, patterns, personas, personaGroups
"""

import argparse
import json
import re
import sys


def kebab(name):
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", name)
    s = re.sub(r"\s+", "-", s.strip()).lower()
    return re.sub(r"-+", "-", s)


def make_asset(element_name, icon_char):
    slug = kebab(element_name)
    return {
        "name": f"{slug}-icon",
        "type": "font-character",
        "description": f"{element_name} icon",
        "fontFamily": "Font Awesome 6 Free",
        "fontCharacter": icon_char,
        "fontWeight": "900",
    }


def make_asset_ref(asset_name):
    return {"assetName": asset_name, "type": "icon"}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Practice/baseline JSON file")
    parser.add_argument("--map", required=True, help="Icon mapping JSON file")
    parser.add_argument("--fix", action="store_true", help="Apply changes (default: dry run)")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip elements that already have icon assetNames (default)")
    args = parser.parse_args()

    with open(args.file) as f:
        data = json.load(f)

    with open(args.map) as f:
        mapping = json.load(f)

    assets = data.setdefault("assets", [])
    existing_asset_names = {a["name"] for a in assets}

    added_assets = []
    updated_elements = []
    skipped = []

    for entry in mapping["mappings"]:
        section = entry["section"]
        elem_name = entry["name"]
        icon = entry["icon"]

        elements = data.get(section, [])
        matched = [e for e in elements if e.get("name") == elem_name]

        if not matched:
            print(f"  WARN: {section}[{elem_name}] not found, skipping", file=sys.stderr)
            continue

        element = matched[0]

        if args.skip_existing:
            existing_refs = element.get("assetNames", [])
            has_icon = any(r.get("type") == "icon" for r in existing_refs)
            if has_icon:
                skipped.append(f"{section}[{elem_name}]")
                continue

        asset = make_asset(elem_name, icon)
        if asset["name"] not in existing_asset_names:
            assets.append(asset)
            existing_asset_names.add(asset["name"])
            added_assets.append(asset["name"])

        asset_refs = element.setdefault("assetNames", [])
        ref = make_asset_ref(asset["name"])
        if not any(r.get("assetName") == asset["name"] for r in asset_refs):
            asset_refs.append(ref)
            updated_elements.append(f"{section}[{elem_name}]")

    print(json.dumps({
        "file": args.file,
        "added_assets": len(added_assets),
        "updated_elements": len(updated_elements),
        "skipped_existing": len(skipped),
        "applied": args.fix,
        "details": {
            "new_assets": added_assets,
            "elements_with_icons": updated_elements,
            "skipped": skipped,
        }
    }, indent=2))

    if args.fix:
        with open(args.file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


if __name__ == "__main__":
    main()
