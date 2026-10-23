#!/usr/bin/env python3
"""
Generate a ChangeRequest JSON from the diff between old and new practice JSON files.

Compares two versions of a practice/baseline/method JSON, detects structural
changes, and produces a schema-compliant ChangeRequest with operations and
nameChanges for downstream propagation via apply-change-request.py.

Usage:
    # Generate ChangeRequest (stdout)
    python3 utils/generate-change-request.py old.json new.json

    # With metadata
    python3 utils/generate-change-request.py old.json new.json \
        --author "Ed Seymour" --status accepted --note "Baseline alignment remap"

    # Write to file
    python3 utils/generate-change-request.py old.json new.json -o changes.json

    # Pipe to apply-change-request.py for downstream propagation
    python3 utils/generate-change-request.py old.json new.json -o cr.json
    python3 utils/apply-change-request.py cr.json downstream.json --fix
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json, detect_kind, get_schema_version


NAMED_SECTIONS = [
    "alphas", "workProducts", "activities", "patterns", "personas",
    "personaGroups", "citations", "assets", "practiceElementAliases",
    "narratives", "activitySpaces", "competencies", "narrativeTypes",
    "focuses", "references", "workProductInstances", "alphaInstances",
    "patternOrchestrations", "outcomes", "patternGroups",
]

ELEMENT_TYPE_MAP = {
    "alphas": "Alpha",
    "workProducts": "WorkProduct",
    "activities": "Activity",
    "patterns": "Pattern",
    "personas": "Persona",
    "personaGroups": "PersonaGroup",
    "citations": "Citation",
    "assets": "Asset",
    "practiceElementAliases": "PracticeElementAlias",
    "narratives": "Narrative",
    "activitySpaces": "ActivitySpace",
    "competencies": "Competency",
    "narrativeTypes": "NarrativeType",
    "focuses": "Focus",
    "references": "AlphaInstance",
    "workProductInstances": "WorkProductInstance",
    "alphaInstances": "AlphaInstanceName",
    "outcomes": "Outcome",
    "patternGroups": "PatternGroup",
    "patternOrchestrations": "PatternOrchestration",
}

SCALAR_FIELDS = [
    "version", "description", "baselinePracticeName", "schemaVersion",
]


def _git_user():
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _make_change_id(author):
    slug = re.sub(r"[^a-z0-9]+", "-", author.lower()).strip("-")
    now = datetime.now(timezone.utc)
    return f"{slug}-{now.strftime('%Y%m%d-%H%M%S')}"


def _identity(item):
    """The key that identifies an element within its section.

    Most elements are keyed on `name`, but two sections are not and were
    therefore invisible to this generator: `practiceElementAliases` entries
    carry `practiceElementName`/`aliasName` and no `name` at all, so a document
    adding eight aliases and deleting two emitted **zero** alias operations;
    `workProductInstances` likewise. Both failures were silent — the sections
    are simply absent from the ChangeRequest rather than reported as skipped.
    """
    if not isinstance(item, dict):
        return None
    if "name" in item:
        return item["name"]
    if "aliasName" in item:
        element = item.get("practiceElementName", "?")
        return f"{element}::{item['aliasName']}"
    if "workProductName" in item:
        return f"{item['workProductName']}::{item.get('levelOfDetailName', '')}"
    return None


def _by_name(items):
    return {k: item for item, k in ((i, _identity(i)) for i in items) if k}


def _diff_fields(old_obj, new_obj, skip_keys=None):
    """Return dict of fields that differ between old and new objects."""
    skip = skip_keys or set()
    modifications = {}
    all_keys = set(old_obj.keys()) | set(new_obj.keys())
    for key in sorted(all_keys):
        if key in skip or key.startswith("_"):
            continue
        old_val = old_obj.get(key)
        new_val = new_obj.get(key)
        if old_val != new_val:
            modifications[key] = new_val
    return modifications


def _child_names(item):
    """Names of an element's ordered children — states, levels of detail, views."""
    names = set()
    for key in ("states", "levelsOfDetail", "views", "checklist"):
        for child in item.get(key, []) or []:
            if isinstance(child, dict) and child.get("name"):
                names.add(child["name"])
    return names


def _looks_like_rename(old_item, new_item):
    """Corroborate a positional pairing before calling it a rename.

    Index position alone is not evidence at the top level: an array that
    withdraws four elements and adds four others keeps its length, so every
    positional mismatch reads as a rename. That produced six fabricated alpha
    renames on one document in practice — including instructions to rename
    *baseline* alphas, which would have been propagated into dependents by
    apply-change-request.py.

    A real rename keeps the element's substance. Require either an identical
    description or a majority of shared child names before believing it.

    One shape is refused outright, ahead of either test: a candidate that
    declares ``mapsTo`` or ``contributesTo`` naming the element it is supposedly
    a rename of. An element cannot be both a child of X and a renaming of X —
    the first says X still exists and this is a kind of it, the second says X is
    gone. This is the common Phase 3 shape of withdrawing a redeclaration and
    adding a variant in its place: a four-state redeclaration of
    ``Partner Capability`` withdrawn, a five-state ``Campaign Readiness``
    carrying ``mapsTo: Partner Capability`` added, four shared state names, and
    the shared-children test corroborating a rename of a root baseline alpha
    that four practices touch.
    """
    for key in ("mapsTo", "contributesTo"):
        target = new_item.get(key)
        if isinstance(target, str) and target == old_item.get("name"):
            return False

    old_desc = (old_item.get("description") or "").strip()
    new_desc = (new_item.get("description") or "").strip()
    if old_desc and old_desc == new_desc:
        return True

    old_children, new_children = _child_names(old_item), _child_names(new_item)
    if not old_children or not new_children:
        return False
    shared = len(old_children & new_children)
    return shared * 2 >= min(len(old_children), len(new_children))


def _detect_sub_renames(old_items, new_items, corroborate=False):
    """Detect renames in ordered sub-element lists (states, LODs) by index position.

    **A name present in both versions was not renamed.** That is the whole of the
    first filter and it is not an optimisation — it is what makes the inference
    sound. Pairing by index alone turns a *reordering* into a rename cascade:
    five sales-tactic alphas written in guide order rather than backup order
    produced four fabricated renames forming a cycle, where every ``fromName``
    was also someone's ``toName`` and the one alpha that kept its index produced
    nothing.

    Corroboration alone could not catch that. These were ``mapsTo`` variants of
    one parent, so all five carried byte-identical state names and
    ``_looks_like_rename`` matched 100% on shared children for *any* pairing
    among them — the guard is blind precisely where variant alphas are involved.
    Only set membership distinguishes a reorder from a rename.

    With ``corroborate``, what survives the filter must still look like the same
    element, for the case where an array genuinely withdraws some elements and
    adds others.
    """
    renames = []

    def _named(items):
        return [i for i in items if isinstance(i, dict) and i.get("name")]

    old_named, new_named = _named(old_items), _named(new_items)
    survived = {i["name"] for i in old_named} & {i["name"] for i in new_named}

    old_rest = [i for i in old_named if i["name"] not in survived]
    new_rest = [i for i in new_named if i["name"] not in survived]

    if not old_rest or len(old_rest) != len(new_rest):
        return renames

    for old_item, new_item in zip(old_rest, new_rest):
        if corroborate and not _looks_like_rename(old_item, new_item):
            continue
        entry = {"fromName": old_item["name"], "toName": new_item["name"]}
        # Sub-element lists are ordered progressions, so position is real
        # evidence there and inference is usually right — nine of nine state
        # and level renames on one document were correct. But a withdrawal plus
        # an unrelated addition is indistinguishable from a rename by position
        # alone, and one document emitted exactly that. Mark the weak ones so
        # the caller is told which to read rather than trusting the lot.
        if not corroborate and not _looks_like_rename(old_item, new_item):
            entry["_uncorroborated"] = True
        renames.append(entry)

    return renames


def _summarize_modifications(mods):
    """Create a concise rationale string from a modifications dict."""
    parts = []
    for key in sorted(mods.keys()):
        val = mods[key]
        if val is None:
            parts.append(f"removed {key}")
        elif isinstance(val, list):
            parts.append(f"updated {key} ({len(val)} items)")
        elif isinstance(val, dict):
            parts.append(f"updated {key}")
        else:
            parts.append(f"set {key}={json.dumps(val)[:60]}")
    return "; ".join(parts[:5]) + ("..." if len(parts) > 5 else "")


def generate_change_request(old_data, new_data, author, status, note_text, schema_path,
                            declared_name_changes=None):
    doc_name = new_data.get("name") or old_data.get("name") or "Unknown"
    doc_kind = detect_kind(new_data) or detect_kind(old_data)
    target_type_map = {
        "practice": "practice",
        "practiceBaseline": "practiceBaseline",
        "method": "method",
    }
    target_type = target_type_map.get(doc_kind, "practice")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    change_id = _make_change_id(author)
    schema_version = get_schema_version(schema_path)

    operations = []
    # Renames the author declares explicitly come first: a rename the differ
    # cannot infer — because the new name shares little text with the old, or
    # because the element was rewritten in the same release — is still a rename
    # dependents must be told about, and silently losing it is the expensive
    # failure. Inferred renames are appended and deduplicated below.
    name_changes = list(declared_name_changes or [])

    # --- Scalar root-level changes ---
    scalar_mods = {}
    for field in SCALAR_FIELDS:
        old_val = old_data.get(field)
        new_val = new_data.get(field)
        if old_val != new_val:
            scalar_mods[field] = new_val
    if scalar_mods:
        operations.append({
            "operation": "modify",
            "elementType": target_type.replace("practiceBaseline", "PracticeBaseline")
                                      .replace("practice", "Practice")
                                      .replace("method", "Method"),
            "elementName": doc_name,
            "modifications": scalar_mods,
            "rationale": _summarize_modifications(scalar_mods),
        })

    # --- Named array sections ---
    for section in NAMED_SECTIONS:
        element_type = ELEMENT_TYPE_MAP[section]
        old_items = old_data.get(section, [])
        new_items = new_data.get(section, [])
        old_map = _by_name(old_items)
        new_map = _by_name(new_items)
        old_names = set(old_map.keys())
        new_names = set(new_map.keys())

        # Top-level renames (by index position, corroborated by content)
        top_renames = _detect_sub_renames(old_items, new_items, corroborate=True)
        rename_from = {r["fromName"] for r in top_renames}
        rename_to = {r["toName"] for r in top_renames}
        for r in top_renames:
            name_changes.append({
                "elementType": element_type,
                "fromName": r["fromName"],
                "toName": r["toName"],
            })

        # Added elements (excluding rename targets)
        for name in sorted(new_names - old_names - rename_to):
            operations.append({
                "operation": "add",
                "elementType": element_type,
                "elementName": name,
                "element": new_map[name],
                "rationale": f"New {element_type} added",
            })

        # Removed elements (excluding rename sources)
        for name in sorted(old_names - new_names - rename_from):
            operations.append({
                "operation": "remove",
                "elementType": element_type,
                "elementName": name,
                "rationale": f"{element_type} removed",
            })

        # Modified elements (present in both, different content)
        for name in sorted(old_names & new_names):
            old_elem = old_map[name]
            new_elem = new_map[name]
            if old_elem == new_elem:
                continue

            mods = _diff_fields(old_elem, new_elem, skip_keys={"name"})
            if not mods:
                continue

            # Detect sub-element renames (states within alphas, LODs within work products)
            if section == "alphas":
                old_states = old_elem.get("states", [])
                new_states = new_elem.get("states", [])
                state_renames = _detect_sub_renames(old_states, new_states)
                for sr in state_renames:
                    entry = {
                        "elementType": "State",
                        "fromName": sr["fromName"],
                        "toName": sr["toName"],
                    }
                    if sr.get("_uncorroborated"):
                        entry["_uncorroborated"] = True
                    name_changes.append(entry)

            if section == "workProducts":
                old_lods = old_elem.get("levelsOfDetail", [])
                new_lods = new_elem.get("levelsOfDetail", [])
                lod_renames = _detect_sub_renames(old_lods, new_lods)
                for lr in lod_renames:
                    entry = {
                        "elementType": "LevelOfDetail",
                        "fromName": lr["fromName"],
                        "toName": lr["toName"],
                    }
                    if lr.get("_uncorroborated"):
                        entry["_uncorroborated"] = True
                    name_changes.append(entry)

            operations.append({
                "operation": "modify",
                "elementType": element_type,
                "elementName": name,
                "modifications": mods,
                "rationale": _summarize_modifications(mods),
            })

    # Deduplicate nameChanges, and strip the internal corroboration marker —
    # it is not part of the schema. The weak ones are reported to stderr so the
    # caller knows which entries to read before letting them propagate.
    seen = set()
    unique_nc = []
    weak = []
    for nc in name_changes:
        key = (nc["elementType"], nc["fromName"], nc["toName"])
        if key in seen:
            continue
        seen.add(key)
        if nc.pop("_uncorroborated", False):
            weak.append(f"{nc['elementType']}: {nc['fromName']} → {nc['toName']}")
        unique_nc.append(nc)
    name_changes = unique_nc

    if weak:
        sys.stderr.write(
            "\nReview these inferred renames before letting them propagate — "
            "position paired them but their content does not corroborate it, "
            "which is also what a withdrawal plus an unrelated addition looks "
            "like:\n"
        )
        for w in weak:
            sys.stderr.write(f"  ? {w}\n")
        sys.stderr.write("")

    # Auto-generate note if not provided
    if not note_text:
        parts = []
        adds = sum(1 for op in operations if op["operation"] == "add")
        mods = sum(1 for op in operations if op["operation"] == "modify")
        removes = sum(1 for op in operations if op["operation"] == "remove")
        if adds:
            parts.append(f"{adds} additions")
        if mods:
            parts.append(f"{mods} modifications")
        if removes:
            parts.append(f"{removes} removals")
        if name_changes:
            parts.append(f"{len(name_changes)} name changes for downstream propagation")
        note_text = f"Changes to {doc_name}: {', '.join(parts)}" if parts else f"No changes detected in {doc_name}"

    cr = {
        "changeId": change_id,
        "targetDocumentName": doc_name,
        "targetDocumentType": target_type,
        "status": status,
        "note": {
            "name": note_text[:80],
            "timestamp": now,
            "content": note_text,
        },
        "authors": [author],
        "createdAt": now,
        "updatedAt": now,
        "operations": operations,
    }

    if name_changes:
        cr["nameChanges"] = name_changes
    if schema_version:
        cr["schemaVersion"] = schema_version

    return cr


def main():
    parser = argparse.ArgumentParser(
        description="Generate a ChangeRequest JSON from the diff between old and new practice JSON files"
    )
    parser.add_argument("old", help="Original/old JSON file")
    parser.add_argument("new", help="Updated/new JSON file")
    parser.add_argument("--author", default=None,
                        help="Author name (default: git user.name)")
    parser.add_argument("--status", default="draft",
                        choices=["draft", "proposed", "accepted", "rejected", "withdrawn"],
                        help="ChangeRequest status (default: draft)")
    parser.add_argument("--note", default=None,
                        help="Description of changes (auto-generated if omitted)")
    parser.add_argument("--schema", default=None,
                        help="Path to language.schema.json (default: deps/language.schema.json)")
    parser.add_argument("--name-change", action="append", default=[], metavar="TYPE:FROM=TO",
                        help="Declare a rename the diff cannot infer, e.g. "
                             "--name-change 'Focus:Partner Value=Value'. Repeatable. "
                             "TYPE is free text — it is written through to the "
                             "ChangeRequest as given. The types in use are Alpha, State, "
                             "LevelOfDetail, Focus, ActivitySpace, Competency, "
                             "CompetencyLevel, NarrativeType, WorkProduct, Pattern, "
                             "PatternView, Persona, PersonaGroup, Citation and Alias. "
                             "An earlier, shorter list here read as an enum and pushed "
                             "agents into mislabelling a persona-group rename as Persona.")
    parser.add_argument("-o", "--output", default=None,
                        help="Output file path (default: stdout)")
    args = parser.parse_args()

    declared = []
    for spec in args.name_change:
        if ":" not in spec or "=" not in spec.split(":", 1)[1]:
            parser.error(f"--name-change '{spec}' is not of the form TYPE:FROM=TO")
        element_type, remainder = spec.split(":", 1)
        from_name, to_name = remainder.split("=", 1)
        if not element_type.strip() or not from_name.strip() or not to_name.strip():
            parser.error(f"--name-change '{spec}' has an empty TYPE, FROM or TO")
        declared.append({
            "elementType": element_type.strip(),
            "fromName": from_name.strip(),
            "toName": to_name.strip(),
        })

    old_data = load_json(args.old)
    new_data = load_json(args.new)
    author = args.author or _git_user()
    schema_path = args.schema

    cr = generate_change_request(old_data, new_data, author, args.status, args.note, schema_path,
                                 declared_name_changes=declared)

    output = json.dumps(cr, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        sys.stderr.write(f"ChangeRequest written to {args.output}\n")
        sys.stderr.write(f"  operations: {len(cr['operations'])}\n")
        sys.stderr.write(f"  nameChanges: {len(cr.get('nameChanges', []))}\n")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
