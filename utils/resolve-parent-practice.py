#!/usr/bin/env python3
"""
Parent Practice Resolver

Detects whether a JSON file is a practiceBaseline, practice, or method,
and when given a practice or method, produces an "effective parent" composite
by merging all embedded practices' elements into a single document.

Usage:
    python3 utils/resolve-parent-practice.py <input.json> --check-only
    python3 utils/resolve-parent-practice.py <input.json> -o <output.json>

    # Merge multiple parent sources (later files override earlier on name conflicts)
    python3 utils/resolve-parent-practice.py parent1.json parent2.json -o combined.json

The script:
1. Reads the input JSON and classifies it by schema discrimination
2. For a practice: outputs the practice directly as the effective parent
3. For a method: unions all embedded practices' elements (name-keyed merge)
4. Applies practiceElementAliases as _aliasContext annotations (canonical names preserved)
5. Reports parent practice names, baselinePracticeName, element counts
6. Multiple inputs: resolves each, then merges (later inputs take precedence)

Exit codes:
    0 - Success
    1 - Error (missing files, invalid JSON, etc.)

Outputs structured JSON report to stdout.
"""

import json
import sys
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, detect_kind, merge_by_name, MERGEABLE_ARRAYS


def merge_practices(practices: List[Dict]) -> Dict:
    """Merge multiple practices into a single composite parent document."""
    if not practices:
        return {}

    result = {}
    for practice in practices:
        p = copy.deepcopy(practice)
        for key in MERGEABLE_ARRAYS:
            p_items = p.get(key, [])
            r_items = result.get(key, [])
            if p_items or r_items:
                result[key] = merge_by_name(r_items, p_items)

    return result


def extract_practice_names(data: Dict, kind: str) -> List[str]:
    """Extract all practice names from a practice or method."""
    if kind == "practice":
        name = data.get('name', '')
        return [name] if name else []

    if kind == "method":
        names = []
        for practice in data.get('practices', []):
            name = practice.get('name', '')
            if name:
                names.append(name)
        for name in data.get('practiceNames', []):
            if name:
                names.append(name)
        if not names:
            name = data.get('name', '')
            if name:
                names.append(name)
        return names

    return []


def extract_baseline_practice_name(data: Dict, kind: str) -> Optional[str]:
    """Extract the baselinePracticeName from a practice or method."""
    if kind == "practice":
        return data.get('baselinePracticeName')

    if kind == "method":
        if 'baselinePracticeName' in data:
            return data['baselinePracticeName']
        bp = data.get('baselinePractice')
        if isinstance(bp, dict):
            return bp.get('name')
        for practice in data.get('practices', []):
            bpn = practice.get('baselinePracticeName')
            if bpn:
                return bpn

    return None


def apply_alias_context(effective: Dict, aliases: List[Dict]) -> Dict:
    """Add _aliasContext and _domainAlias annotations from practiceElementAliases."""
    if not aliases:
        return effective

    alias_context = {
        "description": (
            "Domain-specific terminology from parent practice aliases. "
            "Use these terms for semantic understanding during analysis and mapping. "
            "Always use canonical names (canonicalName) in structural references "
            "(contributesTo, alphaName, stateName, competencyName, etc.)."
        ),
        "aliases": [
            {
                "type": a.get("practiceElementType", ""),
                "canonicalName": a.get("practiceElementName", ""),
                "domainName": a.get("aliasName", "")
            }
            for a in aliases
        ]
    }
    effective["_aliasContext"] = alias_context

    alias_lookup = {}
    for a in aliases:
        element_type = a.get("practiceElementType", "")
        canonical = a.get("practiceElementName", "")
        domain = a.get("aliasName", "")
        alias_lookup.setdefault(element_type, {})[canonical] = domain

    type_to_array = {
        "Alpha": "alphas",
        "ActivitySpace": "activitySpaces",
        "Competency": "competencies",
        "Focus": "focuses",
        "NarrativeType": "narrativeTypes",
        "Narrative": "narratives",
        "WorkProduct": "workProducts",
        "Pattern": "patterns",
        "Persona": "personas",
        "PersonaGroup": "personaGroups",
    }

    for element_type, array_key in type_to_array.items():
        if element_type in alias_lookup and array_key in effective:
            for item in effective[array_key]:
                name = item.get("name", "")
                if name in alias_lookup[element_type]:
                    item["_domainAlias"] = alias_lookup[element_type][name]

    return effective


def resolve_parent(data: Dict, kind: str) -> tuple:
    """
    Resolve a practice or method into an effective parent document.

    Returns (effective_parent, report_dict).
    """
    if kind == "practiceBaseline":
        return None, {
            "success": True,
            "inputKind": "practiceBaseline",
            "message": "Input is a practiceBaseline, not a practice or method. Use resolve-baseline.py instead."
        }

    baseline_practice_name = extract_baseline_practice_name(data, kind)
    practice_names = extract_practice_names(data, kind)

    if kind == "practice":
        effective = copy.deepcopy(data)
        for key in ('kind', 'baselinePracticeName', 'practiceDependencyNames'):
            effective.pop(key, None)

        all_aliases = data.get('practiceElementAliases', [])
        if all_aliases:
            effective = apply_alias_context(effective, all_aliases)

        report = {
            "success": True,
            "inputKind": "practice",
            "parentPracticeNames": practice_names,
            "baselinePracticeName": baseline_practice_name,
            "effectiveParent": {
                "name": data.get("name", ""),
                "alphaCount": len(effective.get("alphas", [])),
                "activitySpaceCount": len(effective.get("activitySpaces", [])),
                "workProductCount": len(effective.get("workProducts", [])),
                "patternCount": len(effective.get("patterns", [])),
                "competencyCount": len(effective.get("competencies", [])),
                "aliasCount": len(all_aliases),
            }
        }
        return effective, report

    # kind == "method"
    practices = data.get('practices', [])

    effective = merge_practices(practices)
    effective['name'] = data.get('name', '')
    effective['description'] = data.get('description', '')

    for key in MERGEABLE_ARRAYS:
        method_items = data.get(key, [])
        if method_items and key not in ('practices',):
            existing = effective.get(key, [])
            if existing:
                effective[key] = merge_by_name(existing, method_items)
            elif method_items:
                effective[key] = copy.deepcopy(method_items)

    all_aliases = []
    for practice in practices:
        all_aliases.extend(practice.get('practiceElementAliases', []))
    all_aliases.extend(data.get('practiceElementAliases', []))
    if all_aliases:
        effective = apply_alias_context(effective, all_aliases)

    report = {
        "success": True,
        "inputKind": "method",
        "parentPracticeNames": practice_names,
        "baselinePracticeName": baseline_practice_name,
        "effectiveParent": {
            "name": data.get("name", ""),
            "practiceCount": len(practices),
            "alphaCount": len(effective.get("alphas", [])),
            "activitySpaceCount": len(effective.get("activitySpaces", [])),
            "workProductCount": len(effective.get("workProducts", [])),
            "patternCount": len(effective.get("patterns", [])),
            "competencyCount": len(effective.get("competencies", [])),
            "aliasCount": len(all_aliases),
        }
    }
    return effective, report


def merge_effective_parents(documents: List[Dict]) -> tuple:
    """Merge multiple resolved effective parent documents.

    Later documents take precedence on name conflicts.
    Returns (merged_document, report_dict).
    """
    merged = {}
    source_names = []

    for doc in documents:
        name = doc.get("name", "")
        if name:
            source_names.append(name)

        for key in MERGEABLE_ARRAYS:
            doc_items = doc.get(key, [])
            merged_items = merged.get(key, [])
            if doc_items or merged_items:
                merged[key] = merge_by_name(merged_items, doc_items)

        if "_aliasContext" in doc:
            if "_aliasContext" not in merged:
                merged["_aliasContext"] = copy.deepcopy(doc["_aliasContext"])
            else:
                existing = merged["_aliasContext"]
                incoming = doc["_aliasContext"]
                if "aliases" in incoming:
                    existing.setdefault("aliases", []).extend(
                        copy.deepcopy(incoming["aliases"])
                    )

    merged["name"] = " + ".join(source_names) if source_names else ""
    merged["description"] = f"Merged effective parent from: {', '.join(source_names)}"

    report = {
        "success": True,
        "mergedFrom": source_names,
        "effectiveParent": {
            "name": merged["name"],
            "alphaCount": len(merged.get("alphas", [])),
            "activitySpaceCount": len(merged.get("activitySpaces", [])),
            "workProductCount": len(merged.get("workProducts", [])),
            "activityCount": len(merged.get("activities", [])),
            "patternCount": len(merged.get("patterns", [])),
            "assetCount": len(merged.get("assets", [])),
            "aliasCount": len(merged.get("practiceElementAliases", [])),
        },
    }
    return merged, report


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect input kind and resolve parent practice/method into effective parent"
    )
    parser.add_argument(
        "input", nargs="+",
        help="Path(s) to input JSON. Multiple files are resolved individually then merged.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output path for the effective parent JSON (required unless --check-only)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only detect input kind and report metadata, don't produce output"
    )

    args = parser.parse_args()

    if len(args.input) > 1:
        if args.check_only:
            print(json.dumps({
                "success": False,
                "error": "--check-only is not supported with multiple inputs"
            }))
            sys.exit(1)
        if not args.output:
            print(json.dumps({
                "success": False,
                "error": "Output path (-o) is required when merging multiple inputs"
            }))
            sys.exit(1)

        resolved = []
        for input_file in args.input:
            data = load_json(Path(input_file))
            kind = detect_kind(data)
            if kind == "practiceBaseline":
                print(json.dumps({
                    "success": False,
                    "error": f"{input_file} is a practiceBaseline — cannot merge baselines here"
                }))
                sys.exit(1)
            effective, _ = resolve_parent(data, kind)
            resolved.append(effective)

        merged, report = merge_effective_parents(resolved)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        report["outputPath"] = str(output_path)
        print(json.dumps(report, indent=2))
        return

    input_path = Path(args.input[0])
    data = load_json(input_path)
    kind = detect_kind(data)

    if args.check_only:
        baseline_practice_name = extract_baseline_practice_name(data, kind)
        practice_names = extract_practice_names(data, kind)

        check_report = {
            "success": True,
            "inputKind": kind,
        }

        if kind != "practiceBaseline":
            check_report["parentPracticeNames"] = practice_names
            check_report["baselinePracticeName"] = baseline_practice_name

            if kind == "method":
                practices = data.get('practices', [])
                all_alpha_names = []
                for p in practices:
                    for a in p.get('alphas', []):
                        name = a.get('name', '')
                        if name and name not in all_alpha_names:
                            all_alpha_names.append(name)
                check_report["practiceCount"] = len(practices)
                check_report["totalAlphaCount"] = len(all_alpha_names)
            else:
                check_report["alphaCount"] = len(data.get("alphas", []))

            aliases = data.get('practiceElementAliases', [])
            if kind == "method":
                for p in data.get('practices', []):
                    aliases.extend(p.get('practiceElementAliases', []))
            check_report["aliasCount"] = len(aliases)
            if aliases:
                check_report["aliases"] = [
                    {
                        "type": a.get("practiceElementType", ""),
                        "canonicalName": a.get("practiceElementName", ""),
                        "domainName": a.get("aliasName", "")
                    }
                    for a in aliases
                ]
        else:
            check_report["message"] = "Input is a practiceBaseline. Use standard baseline flow."

        print(json.dumps(check_report, indent=2))
        return

    if not args.output:
        print(json.dumps({
            "success": False,
            "error": "Output path (-o) is required unless using --check-only"
        }))
        sys.exit(1)

    effective, report = resolve_parent(data, kind)

    if kind == "practiceBaseline":
        print(json.dumps(report, indent=2))
        return

    if not report["success"]:
        print(json.dumps(report, indent=2))
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(effective, f, indent=2, ensure_ascii=False)

    report["outputPath"] = str(output_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
