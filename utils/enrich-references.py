#!/usr/bin/env python3
"""Generate build-references specs from a content inventory.

Transforms a content inventory (with document IDs and categories) into
per-practice compact spec files suitable for `build-references.py --fix`.

Requires a --config file with URL templates and category mappings.
Config format:
{
    "urlTemplate": "https://example.com/doc/{category}/{docId}//",
    "categories": { "docId": "categoryCode", ... },
    "briefWorkProducts": { "practice-slug": "WP Name", ... },
    "skipIds": ["docId1", ...]
}

Usage:
    python3 utils/enrich-references.py inventory.json --config config.json
    python3 utils/enrich-references.py inventory.json --config config.json --apply
    python3 utils/enrich-references.py inventory.json --config config.json -o /tmp/specs
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def load_config(config_path):
    with open(config_path) as f:
        config = json.load(f)
    required = ["urlTemplate", "categories"]
    missing = [k for k in required if k not in config]
    if missing:
        print(f"ERROR: config missing required keys: {missing}", file=sys.stderr)
        print("Required config format:", file=sys.stderr)
        print('  {"urlTemplate": "...", "categories": {...}, "briefWorkProducts": {...}, "skipIds": [...]}', file=sys.stderr)
        sys.exit(1)
    return config


def build_url(doc_id, config):
    categories = config.get("categories", {})
    cat = categories.get(doc_id)
    if not cat:
        print(f"  WARNING: no category for {doc_id}, skipping", file=sys.stderr)
        return None
    return config["urlTemplate"].replace("{category}", cat).replace("{docId}", doc_id)


def generate_specs(inventory_path, practice_dir, config):
    with open(inventory_path) as f:
        inv = json.load(f)

    # Group all items by practice, tagging content type
    items_by_practice = defaultdict(list)

    for section, content_type in [
        ("tacticCheatsheets", "cheatsheet"),
        ("tacticCustomerDecks", "customerDeck"),
        ("tacticIntroDecks", "introDeck"),
        ("tdpIntroDecks", "tdpIntroDeck"),
        ("tdpCustomerDecks", "tdpCustomerDeck"),
        ("personaDiscoveryDocs", "personaDoc"),
        ("sovereigntyWorkshop", "workshop"),
    ]:
        for item in inv.get(section, []):
            item["_type"] = content_type
            items_by_practice[item["practice"]].append(item)

    specs = {}
    for practice, items in items_by_practice.items():
        spec = _build_practice_spec(practice, items, practice_dir, config)
        if spec:
            specs[practice] = spec

    return specs


def _build_practice_spec(practice, items, practice_dir, config):
    # Load practice JSON to read existing references
    practice_path = practice_dir / f"{practice}.json"
    if not practice_path.exists():
        print(f"  WARNING: {practice_path} not found", file=sys.stderr)
        return None

    with open(practice_path) as f:
        pdata = json.load(f)

    existing_refs = {r["name"]: r for r in pdata.get("references", [])}
    brief_wp = config.get("briefWorkProducts", {}).get(practice)

    # Group items by alpha for merging into references
    skip_ids = set(config.get("skipIds", []))
    alpha_items = defaultdict(list)
    workshop_items = []
    for item in items:
        if item["id"] in skip_ids:
            continue
        if item["_type"] == "workshop":
            workshop_items.append(item)
        else:
            alpha_items[item["alpha"]].append(item)

    refs = []

    # Process tactic/TDP alphas
    for alpha, aitems in alpha_items.items():
        ref_name = f"Standard {alpha}"
        if ref_name not in existing_refs:
            print(
                f"  WARNING: ref '{ref_name}' not in {practice}, skipping",
                file=sys.stderr,
            )
            continue
        existing = existing_refs[ref_name]

        links = []
        evidence_links = []

        for item in aitems:
            url = build_url(item["id"], config)
            if not url:
                continue

            if item["_type"] in ("introDeck", "tdpIntroDeck"):
                links.append(f"{url}|{item['title']}")
            elif item["_type"] in ("cheatsheet", "customerDeck", "tdpCustomerDeck"):
                if brief_wp:
                    evidence_links.append(f"{url}|{item['title']}")
                else:
                    links.append(f"{url}|{item['title']}")

        # When there are evidence items but no links, promote all to links
        if evidence_links and not links:
            links = evidence_links
            evidence_links = []

        ref = {
            "name": ref_name,
            "description": existing.get(
                "description",
                f"Reference {alpha} with sales enablement content",
            ),
            "alpha": existing["alphaName"],
            "state": existing["stateName"],
        }
        if links:
            ref["links"] = links
        if evidence_links and brief_wp:
            ref["evidence"] = [
                {
                    "name": f"Standard {alpha} Positioning Brief",
                    "description": (
                        f"Standard instance of {brief_wp} "
                        f"with curated {alpha} tactic content"
                    ),
                    "wp": brief_wp,
                    "lod": "Content-Complete",
                    "links": evidence_links,
                }
            ]
        if links or evidence_links:
            refs.append(ref)

    # Process sovereignty workshop items (new reference)
    if workshop_items:
        ws_links = []
        ws_evidence_links = []
        wp_name = workshop_items[0].get("wp")
        lod_name = workshop_items[0].get("lod")

        for item in workshop_items:
            url = build_url(item["id"], config)
            if not url:
                continue
            title = item["title"]
            if title.startswith("[TEMPLATE]"):
                ws_evidence_links.append(f"{url}|{title}")
            else:
                ws_links.append(f"{url}|{title}")

        ref = {
            "name": "Standard Sovereignty Readiness Workshop",
            "description": (
                "Reference Sovereignty Readiness Workshop instance "
                "with assessment templates and enablement materials"
            ),
            "alpha": "Sovereignty Readiness",
            "state": "Readiness Assessment Completed",
            "links": ws_links,
        }
        if ws_evidence_links and wp_name and lod_name:
            ref["evidence"] = [
                {
                    "name": "Standard Sovereignty Readiness Assessment Workshop",
                    "description": (
                        f"Standard instance of {wp_name} "
                        f"at {lod_name} level with workshop templates"
                    ),
                    "wp": wp_name,
                    "lod": lod_name,
                    "links": ws_evidence_links,
                }
            ]
        refs.append(ref)

    return refs if refs else None


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inventory", help="Path to content inventory JSON")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to config JSON with urlTemplate, categories, briefWorkProducts, skipIds",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory for spec files (default: same as inventory)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply specs using build-references.py --fix",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    inv_path = Path(args.inventory)
    practice_dir = inv_path.parent
    output_dir = Path(args.output_dir) if args.output_dir else practice_dir

    print(f"Reading inventory: {inv_path}")
    specs = generate_specs(inv_path, practice_dir, config)

    utils_dir = Path(__file__).resolve().parent
    total_items = 0

    for practice, spec in sorted(specs.items()):
        spec_path = output_dir / f"_enrich-spec-{practice}.json"
        with open(spec_path, "w") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)

        item_count = sum(
            len(r.get("links", []))
            + sum(len(e.get("links", [])) for e in r.get("evidence", []))
            for r in spec
        )
        total_items += item_count
        print(f"  {practice}: {len(spec)} refs, {item_count} new links → {spec_path}")

        if args.apply:
            practice_path = practice_dir / f"{practice}.json"
            cmd = [
                sys.executable,
                str(utils_dir / "build-references.py"),
                str(practice_path),
                "--spec",
                str(spec_path),
                "--fix",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"    ERROR: {result.stderr.strip()}", file=sys.stderr)
            else:
                print(f"    Applied to {practice_path}")

    print(f"\nTotal: {total_items} new links across {len(specs)} practices")
    if not args.apply:
        print("Run with --apply to merge into practice JSONs")


if __name__ == "__main__":
    main()
