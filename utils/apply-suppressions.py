#!/usr/bin/env python3
"""Switch inherited elements off in a practice by declaring `suppressed: true`.

A restricted variant -- the same technology family with a smaller footprint and a
narrower deployment model -- inherits the whole of what it depends on. `suppressed`
(schema 3.2.0) lets it diminish that rather than only add to it. See
references/semantics/composition.md section 4.9.

The property itself is one boolean, but declaring it by hand is not one edit. Every
element type carries required properties that do not relax when the element is being
switched off: an Alpha requires `focusName` and `states`, each State requires
`seq`, `description` and `checklist`, a WorkProduct requires `levelsOfDetail`. The
redeclaration validator separately requires that every inherited state name is
present. So suppressing one state of an inherited alpha means restating that alpha's
whole state list, and the worked example in composition.md section 4.9 -- four lines,
no `focusName`, no `states` -- does not validate.

This script generates that scaffold from the resolved context instead, carrying the
inherited `description`, `focusName` and `seq` across verbatim and leaving each
`checklist` empty, which is what makes the restatement additive-but-empty rather than
a rewrite of content the practice does not own.

It does not chase what pointed at the suppressed element. References into a suppressed
element are dangling by design (composition.md section 4.9.2) and `resolve-context.py`
reports them under `suppression.danglingReferences`; clearing them is a modelling
decision, not a mechanical one. Run the resolver afterwards and read that list.

Usage:
    # Dry-run: show the scaffold that would be written
    python3 utils/apply-suppressions.py practice.json --context _effective-context.json \
        --spec '[{"alpha":"Distributed Inference Capability"}]'

    # Apply from a spec file
    python3 utils/apply-suppressions.py practice.json --context ctx.json \
        --spec-file suppressions.json --fix

    # List what is already suppressed
    python3 utils/apply-suppressions.py practice.json --list

Spec format (JSON array; each object names exactly one target):
    [
        {"alpha": "Distributed Inference Capability"},          # whole alpha
        {"alpha": "Platform Infrastructure",
         "state": "Multi-Cluster Operations"},                  # one state of an alpha
        {"workProduct": "Cloud Credential Manifests"},          # whole work product
        {"workProduct": "Installation Configuration File",
         "levelOfDetail": "Minimal Template"},                  # one LOD of a work product
        {"reference": "LLMInferenceService CR Template"}        # a curated reference
    ]

Each entry may carry an optional "reason" string, recorded in the report but not
written to the JSON -- the practice's own prompt history is where rationale belongs.

Exits 1 when a spec entry names an element the context does not inherit, since
`suppressed` is only valid on inherited content and declaring it on anything else is
a validation error.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json


def find_by_name(items, name):
    """Return the first record in `items` whose `name` matches, or None."""
    for item in items or []:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def minimal_state(state):
    """Minimal valid State carrying the inherited identity, with an empty checklist."""
    return {
        "name": state.get("name"),
        "description": state.get("description", ""),
        "seq": state.get("seq", 0),
        "checklist": [],
    }


def minimal_lod(lod):
    """Minimal valid LevelOfDetail carrying the inherited identity and its anchor.

    `contributesTo` comes across because a work product with no anchored level and no
    `contributesToAlphaNames` is a floating work product, which the integrity check
    rejects whether or not the element is on its way out of the composition.
    """
    minimal = {
        "name": lod.get("name"),
        "description": lod.get("description", ""),
        "seq": lod.get("seq", 0),
        "checklist": [],
    }
    if lod.get("contributesTo"):
        minimal["contributesTo"] = lod["contributesTo"]
    return minimal


def scaffold_alpha(inherited):
    """Minimal valid Alpha redeclaration: focusName plus every inherited state."""
    return {
        "name": inherited.get("name"),
        "description": inherited.get("description", ""),
        "focusName": inherited.get("focusName", ""),
        "states": [minimal_state(s) for s in inherited.get("states", [])],
    }


def scaffold_workproduct(inherited):
    """Minimal valid WorkProduct redeclaration: every inherited level of detail.

    The purpose-hub anchors (`contributesToAlphaNames`, `partOf`, `mapsTo`) come
    across verbatim. Dropping them would leave a floating work product, which is a
    different defect from the one being declared.
    """
    scaffold = {
        "name": inherited.get("name"),
        "description": inherited.get("description", ""),
        "levelsOfDetail": [minimal_lod(l) for l in inherited.get("levelsOfDetail", [])],
    }
    for anchor in ("contributesToAlphaNames", "partOf", "mapsTo"):
        if inherited.get(anchor):
            scaffold[anchor] = inherited[anchor]
    return scaffold


def scaffold_reference(inherited):
    """Minimal valid AlphaInstance: the anchor plus at least one link."""
    scaffold = {
        "name": inherited.get("name"),
        "description": inherited.get("description", ""),
        "alphaName": inherited.get("alphaName", ""),
        "stateName": inherited.get("stateName", ""),
    }
    links = inherited.get("links")
    if links:
        scaffold["links"] = links
    return scaffold


def ensure_declaration(practice, collection, inherited, scaffold_fn):
    """Return the practice's own declaration of an inherited element, creating it if absent.

    A practice that already redeclares the element keeps its own content -- the
    suppression is set on what is there rather than replacing it.
    """
    existing = find_by_name(practice.get(collection), inherited.get("name"))
    if existing is not None:
        return existing, False
    scaffold = scaffold_fn(inherited)
    practice.setdefault(collection, []).insert(0, scaffold)
    return scaffold, True


def ensure_part(declaration, part_key, inherited_parts, part_name, minimal_fn):
    """Return a named part of a declaration, backfilling the full inherited part list.

    The redeclaration validator requires every inherited part name to be present, so a
    partial restatement is not an option even when only one part is being suppressed.
    """
    present = {p.get("name") for p in declaration.get(part_key, []) if isinstance(p, dict)}
    for part in inherited_parts:
        if part.get("name") not in present:
            declaration.setdefault(part_key, []).append(minimal_fn(part))
    declaration[part_key].sort(key=lambda p: p.get("seq", 0))
    return find_by_name(declaration.get(part_key), part_name)


def apply_entry(practice, context, entry, report):
    """Apply one spec entry. Returns False when the target is not inherited."""
    reason = entry.get("reason", "")

    if entry.get("alpha"):
        alpha_name = entry["alpha"]
        inherited = find_by_name(context.get("alphas"), alpha_name)
        if inherited is None:
            report["notInherited"].append(f"alpha '{alpha_name}'")
            return False
        declaration, created = ensure_declaration(practice, "alphas", inherited, scaffold_alpha)

        if entry.get("state"):
            state_name = entry["state"]
            if find_by_name(inherited.get("states"), state_name) is None:
                report["notInherited"].append(f"state '{alpha_name}' -> '{state_name}'")
                return False
            state = ensure_part(
                declaration, "states", inherited.get("states", []), state_name, minimal_state
            )
            state["suppressed"] = True
            report["suppressed"].append(
                {"path": f"alphas/{alpha_name}/states/{state_name}",
                 "scaffolded": created, "reason": reason}
            )
        else:
            declaration["suppressed"] = True
            report["suppressed"].append(
                {"path": f"alphas/{alpha_name}", "scaffolded": created, "reason": reason}
            )
        return True

    if entry.get("workProduct"):
        wp_name = entry["workProduct"]
        inherited = find_by_name(context.get("workProducts"), wp_name)
        if inherited is None:
            report["notInherited"].append(f"workProduct '{wp_name}'")
            return False
        declaration, created = ensure_declaration(
            practice, "workProducts", inherited, scaffold_workproduct
        )

        if entry.get("levelOfDetail"):
            lod_name = entry["levelOfDetail"]
            if find_by_name(inherited.get("levelsOfDetail"), lod_name) is None:
                report["notInherited"].append(f"levelOfDetail '{wp_name}' -> '{lod_name}'")
                return False
            lod = ensure_part(
                declaration, "levelsOfDetail", inherited.get("levelsOfDetail", []),
                lod_name, minimal_lod,
            )
            lod["suppressed"] = True
            report["suppressed"].append(
                {"path": f"workProducts/{wp_name}/levelsOfDetail/{lod_name}",
                 "scaffolded": created, "reason": reason}
            )
        else:
            declaration["suppressed"] = True
            report["suppressed"].append(
                {"path": f"workProducts/{wp_name}", "scaffolded": created, "reason": reason}
            )
        return True

    if entry.get("reference"):
        ref_name = entry["reference"]
        inherited = find_by_name(context.get("references"), ref_name)
        if inherited is None:
            report["notInherited"].append(f"reference '{ref_name}'")
            return False
        declaration, created = ensure_declaration(
            practice, "references", inherited, scaffold_reference
        )
        declaration["suppressed"] = True
        report["suppressed"].append(
            {"path": f"references/{ref_name}", "scaffolded": created, "reason": reason}
        )
        return True

    report["notInherited"].append(f"spec entry names no target: {json.dumps(entry)}")
    return False


def collect_suppressed(practice):
    """List every `suppressed: true` already declared, as element paths."""
    found = []
    for collection, part_key in (
        ("alphas", "states"),
        ("workProducts", "levelsOfDetail"),
        ("references", None),
        ("activities", None),
        ("patterns", None),
    ):
        for element in practice.get(collection, []) or []:
            if not isinstance(element, dict):
                continue
            name = element.get("name")
            if element.get("suppressed") is True:
                found.append(f"{collection}/{name}")
            if not part_key:
                continue
            for part in element.get(part_key, []) or []:
                if isinstance(part, dict) and part.get("suppressed") is True:
                    found.append(f"{collection}/{name}/{part_key}/{part.get('name')}")
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Declare `suppressed: true` on inherited elements of a practice"
    )
    parser.add_argument("file", help="Practice JSON file to transform")
    parser.add_argument(
        "--context",
        help="Resolved effective context JSON (from resolve-context.py) holding the "
             "inherited elements. Required unless --list",
    )
    parser.add_argument("--spec", help="Inline JSON spec (array of suppression objects)")
    parser.add_argument("--spec-file", help="Path to JSON spec file")
    parser.add_argument(
        "--list", action="store_true", help="List suppressions already declared and exit"
    )
    parser.add_argument("--fix", action="store_true", help="Apply changes in-place (default: dry-run)")
    args = parser.parse_args()

    practice = load_json(args.file)

    if args.list:
        print(json.dumps({"file": args.file, "suppressed": collect_suppressed(practice)}, indent=2))
        return 0

    if not args.spec and not args.spec_file:
        parser.error("one of --spec or --spec-file is required (or use --list)")
    if not args.context:
        parser.error("--context is required when applying a spec")

    spec = json.loads(args.spec) if args.spec else load_json(args.spec_file)
    if not isinstance(spec, list):
        parser.error("spec must be a JSON array of suppression objects")

    context = load_json(args.context)
    report = {"file": args.file, "suppressed": [], "notInherited": []}

    for entry in spec:
        apply_entry(practice, context, entry, report)

    report["appliedCount"] = len(report["suppressed"])
    report["mode"] = "applied" if args.fix else "dry-run"

    if args.fix and not report["notInherited"]:
        Path(args.file).write_text(json.dumps(practice, indent=2, ensure_ascii=False) + "\n")
    elif args.fix:
        report["mode"] = "aborted -- spec names elements the context does not inherit"

    print(json.dumps(report, indent=2))
    return 1 if report["notInherited"] else 0


if __name__ == "__main__":
    sys.exit(main())
