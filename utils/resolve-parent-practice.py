#!/usr/bin/env python3
"""
Parent Practice Resolver

Detects whether a JSON file is a practiceBaseline, practice, or method,
and when given a practice or method, produces an "effective parent" composite
by merging all embedded practices' elements into a single document.

Usage:
    python3 utils/resolve-parent-practice.py <input.json> --check-only
    python3 utils/resolve-parent-practice.py <input.json> -o <output.json>

The script:
1. Reads the input JSON and classifies it by schema discrimination
2. For a practice: outputs the practice directly as the effective parent
3. For a method: unions all embedded practices' elements (name-keyed merge)
4. Applies practiceElementAliases as _aliasContext annotations (canonical names preserved)
5. Reports parent practice names, baselinePracticeName, element counts

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
from collections import OrderedDict


def load_json(file_path: Path) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(json.dumps({
            "success": False,
            "error": f"File not found: {file_path}"
        }))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "error": f"Invalid JSON in {file_path}: {e}"
        }))
        sys.exit(1)


def detect_kind(data: Dict) -> str:
    """Classify JSON by schema discrimination rules (same as language.schema.json)."""
    if any(key in data for key in ('practices', 'practiceNames', 'baselinePractice')):
        return "method"
    if 'baselinePracticeName' in data:
        return "practice"
    return "practiceBaseline"


def merge_by_name(base_list: List[Dict], overlay_list: List[Dict]) -> List[Dict]:
    """Merge two lists of objects by 'name' key. Overlay overrides base."""
    merged = OrderedDict()
    for item in (base_list or []):
        if 'name' in item:
            merged[item['name']] = item
    for item in (overlay_list or []):
        if 'name' in item:
            if item['name'] in merged:
                existing = merged[item['name']]
                combined = copy.deepcopy(existing)
                combined.update(copy.deepcopy(item))
                merged[item['name']] = combined
            else:
                merged[item['name']] = copy.deepcopy(item)
    return list(merged.values())


MERGEABLE_ARRAYS = [
    'focuses', 'alphas', 'activitySpaces', 'competencies',
    'narrativeTypes', 'narratives', 'citations', 'assets',
    'workProducts', 'patterns', 'personas', 'personaGroups',
    'alphaInstances', 'workProductInstances',
]


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


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect input kind and resolve parent practice/method into effective parent"
    )
    parser.add_argument(
        "input",
        help="Path to the input practice, method, or baseline JSON"
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
    input_path = Path(args.input)
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
