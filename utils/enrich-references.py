#!/usr/bin/env python3
"""Generate build-references specs from a Sales Hub content inventory.

Transforms a content inventory (with document IDs and categories) into
per-practice compact spec files suitable for `build-references.py --fix`.

Usage:
    # Generate spec files (dry run)
    python3 utils/enrich-references.py practices/red-hat-sales-plays/_saleshub-content-inventory.json

    # Generate and apply to practice JSONs
    python3 utils/enrich-references.py practices/red-hat-sales-plays/_saleshub-content-inventory.json --apply

    # Custom output directory for spec files
    python3 utils/enrich-references.py inventory.json -o /tmp/specs
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

DOCCENTER_BASE = (
    "https://saleshub.redhat.com/apps/doccenter/"
    "1d1918e9-b5b0-4428-b8fc-87e02ad44156/doc/"
    "%252Fdd04d516a5-19b3-48c9-e01a-d2bf52939de4"
    "%252FdfMmNhNDhiYjktYzE1Ny00ZjgyLWJlYjUtNTdhY2NjZmY5Y2Rh"
    "%252CPT0%253D%252C"
)

CAT_CHEATSHEET = "Q2hlYXRzaGVldA%253D%253D"
CAT_BUSINESS = "QnVzaW5lc3MgcHJlc2VudGF0aW9u"
CAT_ENABLEMENT = "RW5hYmxlbWVudA%253D%253D"
CAT_SALES_TRAINING = "U2FsZXMgdHJhaW5pbmcgcHJlc2VudGF0aW9u"
CAT_SALES_CONVO = "U2FsZXMgY29udmVyc2F0aW9uIGd1aWRl"
CAT_TEMPLATE = "VGVtcGxhdGU%253D"
CAT_OVERVIEW = "T3ZlcnZpZXc%253D"

# Per-item Seismic folder category (from search result URLs)
ITEM_CATEGORY = {
    # Cheatsheets
    "lfecf67abd-e8f1-42df-ad11-a8922c532c86": CAT_CHEATSHEET,
    "lf04c86646-1391-4f60-b9d5-f7ecc527c472": CAT_CHEATSHEET,
    "lff76544e3-7cdb-44fd-8484-582e143787d5": CAT_CHEATSHEET,
    "lf7a89b9b2-ca56-41c3-96e5-a1763c48168a": CAT_CHEATSHEET,
    "lf22cb9d79-ec7c-4580-b224-e03ed5ddc85f": CAT_CHEATSHEET,
    "lff64ec365-2520-4cbb-b9e3-5f3a9afdbe55": CAT_CHEATSHEET,
    "lfd7e9fefe-3d6f-414a-bcf8-a7437e214699": CAT_CHEATSHEET,
    "lfe5f850d4-4469-4a6c-9544-d71504715a4b": CAT_CHEATSHEET,
    "lf7b6c7c58-4c76-4d3d-a415-9fa7e45001b3": CAT_CHEATSHEET,
    "lf5b2914e2-6f5b-47bf-8bef-ec80587cacd4": CAT_CHEATSHEET,
    "lfc7079e15-f70e-4b45-b370-748a01337345": CAT_CHEATSHEET,
    "lfa5b30f26-1b41-4f4f-8f97-ae953d6484b4": CAT_CHEATSHEET,
    "lf5f689afc-b506-44cf-b0c1-84c959401e6a": CAT_OVERVIEW,
    "lf8f5b7f56-bc08-4e00-84dc-d979b6b2a831": CAT_CHEATSHEET,
    "lf845c185c-c6cb-47b0-823a-e2d1499324c7": CAT_CHEATSHEET,
    "lf1373db9a-2f7b-4004-a930-16c13f5b082a": CAT_CHEATSHEET,
    "lf25d16f5b-12e2-4b56-9460-88b263e1ed08": CAT_CHEATSHEET,
    # Customer decks
    "lf68672986-b889-4cf5-8dc8-6281538474fa": CAT_BUSINESS,
    "lf4035d68e-ea6d-42ee-b109-900393b70247": CAT_BUSINESS,
    "lf6bfb6e23-69d6-476d-be70-cc80b3dc56a3": CAT_BUSINESS,
    "lfbd8968f4-481d-40d2-bea9-5adffc355e74": CAT_BUSINESS,
    "lf94747066-7d2b-4396-93dd-26c559b799a1": CAT_ENABLEMENT,
    "lf3a1d4864-3582-49b1-b33d-277c02e33f00": CAT_BUSINESS,
    "lf34ef8e91-8cd6-403a-8ed2-841e412de817": CAT_BUSINESS,
    "lf2c3f9329-e161-4452-999c-b698a29b6c78": CAT_BUSINESS,
    "lf6c997c6c-bbb2-45d8-b480-ebece4d5f7d4": CAT_BUSINESS,
    "lf43da85d7-83b6-44dd-ad01-e27c361a09af": CAT_BUSINESS,
    "lf042db6a9-51d5-4d8e-be25-8f37b187c33d": CAT_BUSINESS,
    "lf71243072-6151-4261-887d-d62dccf6ecf9": CAT_BUSINESS,
    "lff8e0e12a-d0f3-43d4-8ee7-49428fd9a85b": CAT_BUSINESS,
    "lf70729f07-a021-4e65-b231-5e9a9541e65a": CAT_BUSINESS,
    "lfcc190722-af8d-4b4f-b925-a57f02699704": CAT_BUSINESS,
    "lf3f503a4c-6b3c-4798-98b1-07a63133430f": CAT_BUSINESS,
    "lf158c3bba-1198-4800-8a4b-6e8267a06ee5": CAT_SALES_CONVO,
    # Intro decks - tactic
    "lfd997f6e9-3634-4934-abaf-2a8e131cfacb": CAT_SALES_TRAINING,
    "lf002585ad-ca06-4ee0-9b08-3069b795096b": CAT_SALES_TRAINING,
    "lf1894c1d0-b152-40d9-bdb1-377ab54ad1ce": CAT_SALES_TRAINING,
    "lf92335139-7fd0-4ddb-aecb-59a376046f9a": CAT_SALES_TRAINING,
    "lfb67e99b6-c8ec-4987-8932-adcc15da58e8": CAT_ENABLEMENT,
    "lf15542995-0dbe-428c-a8be-fea7f23847c3": CAT_ENABLEMENT,
    "lff205bad4-f23f-4c9d-b154-d5f4fa44e4a4": CAT_ENABLEMENT,
    "lfbd2b1b7f-cf36-41f0-9cce-b2a2ed46c8e8": CAT_ENABLEMENT,
    "lf99ac64db-e4b0-4ee8-8878-4ce353c11c74": CAT_ENABLEMENT,
    "lfb90bfdd5-99e7-439e-8e7d-9a4fca57a5b0": CAT_ENABLEMENT,
    "lfd25130f5-5380-4798-9945-b20fbc655ce4": CAT_ENABLEMENT,
    "lf27448e9f-f36f-4481-b32f-2f033a177ef7": CAT_ENABLEMENT,
    "lfbafc7b59-74c0-4a86-910d-080e04e60d6d": CAT_ENABLEMENT,
    "lff36c8476-4ade-49d0-aa23-5d06a93abc35": CAT_SALES_TRAINING,
    "lf3f08a1b4-e3b5-4390-b64c-16c19e99f3ad": CAT_SALES_TRAINING,
    "lfa13dfe88-acee-4c75-8996-c435da000d69": CAT_SALES_TRAINING,
    "lfcce28a8f-1bbc-4e6b-85fb-a20ee6c06190": CAT_SALES_TRAINING,
    # Intro decks - TDP
    "lfa1142fd4-a4a7-41b2-b2f2-2c1e05e9d7e2": CAT_SALES_TRAINING,
    "lf3e838ebe-c048-4a52-9433-184a7344cfb4": CAT_ENABLEMENT,
    "lfdd7dc4ea-2216-4477-aa51-4db50c3ddee7": CAT_ENABLEMENT,
    "lf983aa119-a618-4a29-97a0-85dd30e37787": CAT_SALES_TRAINING,
    # Customer decks - TDP
    "lf1e7c7227-3def-4478-8b88-9ea3e6a59e33": CAT_BUSINESS,
    "lf8779fbb9-4f43-4fff-8c2f-b729048a8dfd": CAT_BUSINESS,
    # Persona discovery docs
    "lf56d3fe97-8b63-47f7-bcb4-911df0e27b49": CAT_SALES_CONVO,
    "lf2b68f833-1188-441c-80c0-1e8f0f852fe8": CAT_SALES_CONVO,
    "lfedb1d4b2-585b-41bc-b52c-98a493bc40fa": CAT_SALES_CONVO,
    "lf143531f7-6ce8-43d8-ba8a-a884f0c2b065": CAT_SALES_CONVO,
    "lf589cdb31-25d8-4786-aa54-14bea0679865": CAT_SALES_TRAINING,
    # Sovereignty workshop
    "lf33e7b42c-108f-4e42-845e-58083719eca5": CAT_BUSINESS,
    "lf138b0864-7880-4a9f-bfa3-b98c5014d78d": CAT_ENABLEMENT,
    "lfbca0b430-95e0-4983-bdb6-4f3fa67bc67f": CAT_TEMPLATE,
    "lf1f87d43a-03d6-43a3-8207-a8a0dbcfcf30": CAT_TEMPLATE,
    "lfcb7390ef-28b4-4c9b-b1cc-390acfc3cb84": CAT_TEMPLATE,
}

BRIEF_WP = {
    "server-cloud-os-tdp": "Server Cloud OS Brief",
    "container-management-tdp": "Container Management Brief",
    "app-platform-tdp": "App Platform Brief",
    "automation-tdp": "Automation Brief",
    "ai-platform-tdp": None,
    "virtualization-tdp": "Virtualization Brief",
}

# IDs to skip (already linked in existing references)
SKIP_IDS = {
    # Persona docs (already in sales play refs via shortlinks)
    "lf56d3fe97-8b63-47f7-bcb4-911df0e27b49",
    "lf2b68f833-1188-441c-80c0-1e8f0f852fe8",
    "lfedb1d4b2-585b-41bc-b52c-98a493bc40fa",
    "lf143531f7-6ce8-43d8-ba8a-a884f0c2b065",
    "lf589cdb31-25d8-4786-aa54-14bea0679865",
    # Container Management TDP customer deck (already in TDP ref)
    "lf1e7c7227-3def-4478-8b88-9ea3e6a59e33",
}


def build_url(doc_id):
    cat = ITEM_CATEGORY.get(doc_id)
    if not cat:
        print(f"  WARNING: no category for {doc_id}, skipping", file=sys.stderr)
        return None
    return f"{DOCCENTER_BASE}{cat}%252F{doc_id}//"


def generate_specs(inventory_path, practice_dir):
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
        spec = _build_practice_spec(practice, items, practice_dir)
        if spec:
            specs[practice] = spec

    return specs


def _build_practice_spec(practice, items, practice_dir):
    # Load practice JSON to read existing references
    practice_path = practice_dir / f"{practice}.json"
    if not practice_path.exists():
        print(f"  WARNING: {practice_path} not found", file=sys.stderr)
        return None

    with open(practice_path) as f:
        pdata = json.load(f)

    existing_refs = {r["name"]: r for r in pdata.get("references", [])}
    brief_wp = BRIEF_WP.get(practice)

    # Group items by alpha for merging into references
    alpha_items = defaultdict(list)
    workshop_items = []
    for item in items:
        if item["id"] in SKIP_IDS:
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
            url = build_url(item["id"])
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
            url = build_url(item["id"])
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", help="Path to content inventory JSON")
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

    inv_path = Path(args.inventory)
    practice_dir = inv_path.parent
    output_dir = Path(args.output_dir) if args.output_dir else practice_dir

    print(f"Reading inventory: {inv_path}")
    specs = generate_specs(inv_path, practice_dir)

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
