#!/usr/bin/env python3
"""Build schema-compliant AlphaInstance references from a compact spec.

Validates all anchors (alphaName, stateName, workProductName, levelOfDetailName)
against the target practice and outputs full reference JSON ready for patching.

Usage:
    # Validate and output reference JSON to stdout
    python3 utils/build-references.py practice.json --spec refs-spec.json

    # Inline spec
    python3 utils/build-references.py practice.json --spec-inline '[{...}]'

    # Apply directly to practice (merge with existing references)
    python3 utils/build-references.py practice.json --spec refs-spec.json --fix

    # Output to file instead of stdout
    python3 utils/build-references.py practice.json --spec refs-spec.json -o _references.json

Compact spec format (JSON array):
    [
        {
            "name": "Standard OpenShift Campaign Library",
            "description": "Curated campaign assets for OpenShift partner demand generation",
            "alpha": "Demand Campaign",
            "state": "Provisioned",
            "links": [
                "https://example.com/hub|Campaign Hub Page",
                {"name": "Partner Portal", "uri": "https://example.com/portal"}
            ],
            "evidence": [
                {
                    "name": "OpenShift Partner Campaign Guide",
                    "description": "Step-by-step campaign execution guide",
                    "wp": "Campaign Brief",
                    "lod": "Outlined",
                    "links": ["https://example.com/guide|Campaign Guide PDF"]
                }
            ]
        }
    ]

Link shorthand: "url|label" expands to {"name": "label", "uri": "url"}.
Full ExternalLink objects are also accepted.

Merge rules (--fix mode):
    - Same-name AlphaInstance: merge to highest state, aggregate links and evidenceBy
    - Same-name WorkProductInstance: merge to highest LOD, aggregate links
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def _parse_link(link):
    """Parse a link entry — either shorthand string or full object."""
    if isinstance(link, dict):
        return link
    if isinstance(link, str) and "|" in link:
        url, label = link.split("|", 1)
        result = {"name": label.strip(), "uri": url.strip()}
        return result
    if isinstance(link, str):
        return {"name": link, "uri": link}
    return None


def _build_alpha_index(practice):
    """Build lookup: alphaName → {stateName → stateIndex}."""
    index = {}
    for alpha in practice.get("alphas", []):
        states = {}
        for i, state in enumerate(alpha.get("states", [])):
            states[state["name"]] = i
        index[alpha["name"]] = states
    return index


def _build_wp_index(practice):
    """Build lookup: workProductName → {lodName → lodIndex}."""
    index = {}
    for wp in practice.get("workProducts", []):
        lods = {}
        for i, lod in enumerate(wp.get("levelsOfDetail", [])):
            lods[lod["name"]] = i
        index[wp["name"]] = lods
    return index


def _validate_spec_entry(entry, alpha_index, wp_index, errors):
    """Validate a single spec entry against practice elements. Returns True if valid."""
    valid = True
    name = entry.get("name", "<unnamed>")

    if not entry.get("name"):
        errors.append(f"  {name}: missing 'name'")
        valid = False
    if not entry.get("description"):
        errors.append(f"  {name}: missing 'description'")
        valid = False

    alpha = entry.get("alpha")
    state = entry.get("state")

    if not alpha:
        errors.append(f"  {name}: missing 'alpha'")
        valid = False
    elif alpha not in alpha_index:
        errors.append(f"  {name}: alpha '{alpha}' not found in practice")
        valid = False
    elif state and state not in alpha_index.get(alpha, {}):
        errors.append(f"  {name}: state '{state}' not found in alpha '{alpha}'")
        valid = False

    if not state:
        errors.append(f"  {name}: missing 'state'")
        valid = False

    links = entry.get("links", [])
    if not links:
        errors.append(f"  {name}: no links (references without links provide no actionable value)")
        valid = False

    for ev in entry.get("evidence", []):
        ev_name = ev.get("name", "<unnamed evidence>")
        if not ev.get("name"):
            errors.append(f"  {name}.evidence: missing 'name'")
            valid = False
        if not ev.get("description"):
            errors.append(f"  {name}.evidence[{ev_name}]: missing 'description'")
            valid = False

        wp = ev.get("wp")
        lod = ev.get("lod")

        if not wp:
            errors.append(f"  {name}.evidence[{ev_name}]: missing 'wp'")
            valid = False
        elif wp not in wp_index:
            errors.append(f"  {name}.evidence[{ev_name}]: work product '{wp}' not found")
            valid = False
        elif lod and lod not in wp_index.get(wp, {}):
            errors.append(f"  {name}.evidence[{ev_name}]: LOD '{lod}' not found in work product '{wp}'")
            valid = False

        if not lod:
            errors.append(f"  {name}.evidence[{ev_name}]: missing 'lod'")
            valid = False

        ev_links = ev.get("links", [])
        if not ev_links:
            errors.append(f"  {name}.evidence[{ev_name}]: no links")
            valid = False

    return valid


def _expand_entry(entry):
    """Expand a compact spec entry into a full AlphaInstance object."""
    ref = {
        "name": entry["name"],
        "description": entry["description"],
        "alphaName": entry["alpha"],
        "stateName": entry["state"],
    }

    links = []
    for link in entry.get("links", []):
        parsed = _parse_link(link)
        if parsed:
            links.append(parsed)
    if links:
        ref["links"] = links

    evidence_by = []
    for ev in entry.get("evidence", []):
        wpi = {
            "name": ev["name"],
            "description": ev["description"],
            "workProductName": ev["wp"],
            "levelOfDetailName": ev["lod"],
        }
        ev_links = []
        for link in ev.get("links", []):
            parsed = _parse_link(link)
            if parsed:
                ev_links.append(parsed)
        if ev_links:
            wpi["links"] = ev_links
        evidence_by.append(wpi)

    if evidence_by:
        ref["evidenceBy"] = evidence_by

    return ref


def _merge_references(existing, new_refs, alpha_index):
    """Merge new references into existing, following same-name merge rules."""
    by_name = {}
    for ref in existing:
        by_name[ref["name"]] = ref

    for ref in new_refs:
        name = ref["name"]
        if name in by_name:
            existing_ref = by_name[name]
            # Merge to highest state
            existing_alpha = ref.get("alphaName", existing_ref.get("alphaName"))
            existing_state_idx = alpha_index.get(existing_alpha, {}).get(
                existing_ref.get("stateName"), -1
            )
            new_state_idx = alpha_index.get(existing_alpha, {}).get(
                ref.get("stateName"), -1
            )
            if new_state_idx > existing_state_idx:
                existing_ref["stateName"] = ref["stateName"]

            # Aggregate links
            existing_link_uris = {
                lnk.get("uri") for lnk in existing_ref.get("links", []) if lnk.get("uri")
            }
            for lnk in ref.get("links", []):
                if lnk.get("uri") not in existing_link_uris:
                    existing_ref.setdefault("links", []).append(lnk)
                    existing_link_uris.add(lnk.get("uri"))

            # Aggregate evidenceBy
            existing_ev_names = {
                ev.get("name") for ev in existing_ref.get("evidenceBy", [])
            }
            for ev in ref.get("evidenceBy", []):
                if ev.get("name") not in existing_ev_names:
                    existing_ref.setdefault("evidenceBy", []).append(ev)
                    existing_ev_names.add(ev.get("name"))
        else:
            by_name[name] = ref

    return list(by_name.values())


def main():
    parser = argparse.ArgumentParser(
        description="Build schema-compliant AlphaInstance references from compact spec"
    )
    parser.add_argument("practice", help="Practice JSON file (for anchor validation)")
    parser.add_argument("--fix", action="store_true",
                        help="Apply references directly to practice JSON (merge with existing)")
    parser.add_argument("-o", "--output", help="Write expanded references to file")

    spec_group = parser.add_mutually_exclusive_group(required=True)
    spec_group.add_argument("--spec", help="Path to compact spec JSON file")
    spec_group.add_argument("--spec-inline", help="Inline compact spec JSON")

    args = parser.parse_args()

    practice = load_json(args.practice)

    if args.spec:
        spec_list = load_json(args.spec)
    else:
        spec_list = json.loads(args.spec_inline)

    if not isinstance(spec_list, list):
        spec_list = [spec_list]

    alpha_index = _build_alpha_index(practice)
    wp_index = _build_wp_index(practice)

    errors = []
    for entry in spec_list:
        _validate_spec_entry(entry, alpha_index, wp_index, errors)

    if errors:
        print("Validation errors:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    expanded = [_expand_entry(entry) for entry in spec_list]

    if args.fix:
        existing_refs = practice.get("references", [])
        merged = _merge_references(existing_refs, expanded, alpha_index)
        practice["references"] = merged
        with open(args.practice, "w", encoding="utf-8") as f:
            json.dump(practice, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(json.dumps({
            "file": args.practice,
            "existingReferences": len(existing_refs),
            "specEntries": len(spec_list),
            "totalReferences": len(merged),
            "merged": len(existing_refs) + len(spec_list) - len(merged),
        }, indent=2))
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(expanded, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Wrote {len(expanded)} references to {args.output}")
    else:
        print(json.dumps(expanded, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
