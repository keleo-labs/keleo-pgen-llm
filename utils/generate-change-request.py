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
    "focuses", "references",
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


def _by_name(items):
    return {item["name"]: item for item in items if isinstance(item, dict) and "name" in item}


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


def _detect_sub_renames(old_items, new_items):
    """Detect renames in ordered sub-element lists (states, LODs) by index position."""
    renames = []
    old_names = [item.get("name") for item in old_items if isinstance(item, dict)]
    new_names = [item.get("name") for item in new_items if isinstance(item, dict)]

    if len(old_names) != len(new_names):
        return renames

    for i, (old_name, new_name) in enumerate(zip(old_names, new_names)):
        if old_name and new_name and old_name != new_name:
            renames.append({"fromName": old_name, "toName": new_name})

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


def generate_change_request(old_data, new_data, author, status, note_text, schema_path):
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
    name_changes = []

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

        # Top-level renames (by index position)
        top_renames = _detect_sub_renames(old_items, new_items)
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
                    name_changes.append({
                        "elementType": "State",
                        "fromName": sr["fromName"],
                        "toName": sr["toName"],
                    })

            if section == "workProducts":
                old_lods = old_elem.get("levelsOfDetail", [])
                new_lods = new_elem.get("levelsOfDetail", [])
                lod_renames = _detect_sub_renames(old_lods, new_lods)
                for lr in lod_renames:
                    name_changes.append({
                        "elementType": "LevelOfDetail",
                        "fromName": lr["fromName"],
                        "toName": lr["toName"],
                    })

            operations.append({
                "operation": "modify",
                "elementType": element_type,
                "elementName": name,
                "modifications": mods,
                "rationale": _summarize_modifications(mods),
            })

    # Deduplicate nameChanges
    seen = set()
    unique_nc = []
    for nc in name_changes:
        key = (nc["elementType"], nc["fromName"], nc["toName"])
        if key not in seen:
            seen.add(key)
            unique_nc.append(nc)
    name_changes = unique_nc

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
    parser.add_argument("-o", "--output", default=None,
                        help="Output file path (default: stdout)")
    args = parser.parse_args()

    old_data = load_json(args.old)
    new_data = load_json(args.new)
    author = args.author or _git_user()
    schema_path = args.schema

    cr = generate_change_request(old_data, new_data, author, args.status, args.note, schema_path)

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
