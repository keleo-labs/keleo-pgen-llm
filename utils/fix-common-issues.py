#!/usr/bin/env python3
"""Auto-fix common practice/method/baseline JSON issues.

Consolidates structural fixes detected by assess-practice.py:
- Missing 'kind' discriminator property
- Narrative structure (missing name/description from PracticeElement)
- Citation structure (missing PracticeElement fields)
- Empty contributesTo on baseline alphas (should not exist)
- Narrative citation references (adds all citations to narratives)
- Truncated checklist names (replaces 50-char truncated names with full description)
- Relationship type normalization
- Schema violations: techniqueNarratives→narratives, tags nesting, teams→personaGroups
- Persona property names (personaName→name, personaDescription→description)
- contributesTo arrays→strings (schema defines as string, not array)

Usage:
    # Dry run — show what would be fixed
    python3 utils/fix-common-issues.py <file.json>

    # Apply fixes in-place
    python3 utils/fix-common-issues.py <file.json> --fix

    # Also normalize relationship types to standard set
    python3 utils/fix-common-issues.py <file.json> --fix --normalize-relationships

    # Also fix truncated checklist names
    python3 utils/fix-common-issues.py <file.json> --fix --fix-truncated-names

    # Fix schema violations (tags, persona groups, persona properties)
    python3 utils/fix-common-issues.py <file.json> --fix --fix-schema

    # Fix contributesTo arrays to strings
    python3 utils/fix-common-issues.py <file.json> --fix --fix-contributesto-arrays

    # Apply all optional fixes
    python3 utils/fix-common-issues.py <file.json> --fix --all

Output: JSON report to stdout. Exit 0 on success, 1 on error.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json_pair


STANDARD_RELATIONSHIP_TYPES = {"produces", "governed by", "uses"}

RELATIONSHIP_NORMALIZATIONS = {
    "governs": "governed by",
    "supports": "produces",
    "enables": "produces",
    "provides": "produces",
    "enhances": "produces",
    "protects": "governed by",
    "protected by": "governed by",
    "managed by": "governed by",
    "constrained by": "governed by",
    "guided by": "governed by",
    "aligned with": "governed by",
    "coordinates with": "uses",
    "requires": "uses",
    "provided by": "uses",
    "enabled by": "uses",
    "enhanced by": "uses",
    "optimized by": "uses",
}


# --- Core fixes (always run) ---

def fix_kind(data):
    fixes = []
    kind = data.get("kind")
    if kind == "practiceBaseline" or kind == "practice" or kind == "method":
        return fixes
    if kind == "baseline":
        data["kind"] = "practiceBaseline"
        fixes.append({
            "category": "kind",
            "path": "kind",
            "old": kind,
            "new": "practiceBaseline",
        })
    elif kind is None:
        has_practices = "practices" in data
        has_baseline_name = "baselinePracticeName" in data
        if has_practices:
            data["kind"] = "method"
        elif has_baseline_name:
            data["kind"] = "practice"
        else:
            data["kind"] = "practiceBaseline"
        fixes.append({
            "category": "kind",
            "path": "kind",
            "old": None,
            "new": data["kind"],
        })
    return fixes


def fix_narrative_structure(narratives, parent_name="", path_prefix="narratives"):
    fixes = []
    for i, narrative in enumerate(narratives):
        if "name" not in narrative:
            if "narrativeName" in narrative:
                narrative["name"] = narrative["narrativeName"]
            else:
                type_name = narrative.get("narrativeTypeName", f"Narrative {i + 1}")
                narrative["name"] = f"{parent_name} {type_name}" if parent_name else type_name
            fixes.append({
                "category": "narrative-structure",
                "path": f"{path_prefix}[{i}].name",
                "old": None,
                "new": narrative["name"],
            })

        if "description" not in narrative:
            type_name = narrative.get("narrativeTypeName", "narrative")
            narrative["description"] = (
                f"Provides {type_name.lower()} context and guidance "
                f"for {parent_name or 'this element'}"
            )
            fixes.append({
                "category": "narrative-structure",
                "path": f"{path_prefix}[{i}].description",
                "old": None,
                "new": narrative["description"],
            })

        if "narrativeName" in narrative:
            del narrative["narrativeName"]
            fixes.append({
                "category": "narrative-structure",
                "path": f"{path_prefix}[{i}].narrativeName",
                "old": "(removed obsolete property)",
                "new": None,
            })

        for j, ctx in enumerate(narrative.get("narrativeContexts", [])):
            if "contextText" in ctx and "context" not in ctx:
                ctx["context"] = ctx.pop("contextText")
                fixes.append({
                    "category": "narrative-structure",
                    "path": f"{path_prefix}[{i}].narrativeContexts[{j}]",
                    "old": "contextText",
                    "new": "context (renamed)",
                })

    return fixes


def fix_narratives(data):
    fixes = fix_narrative_structure(
        data.get("narratives", []),
        parent_name=data.get("name", ""),
    )
    for coll_key in ("alphas", "activities", "workProducts", "patterns",
                     "activitySpaces", "competencies"):
        for ei, elem in enumerate(data.get(coll_key, [])):
            if "narratives" in elem:
                fixes.extend(fix_narrative_structure(
                    elem["narratives"],
                    parent_name=elem.get("name", ""),
                    path_prefix=f"{coll_key}[{ei}].narratives",
                ))
    return fixes


def fix_citations(data):
    fixes = []
    for i, citation in enumerate(data.get("citations", [])):
        if "name" not in citation:
            title = citation.get("title", f"Citation {i + 1}")
            citation["name"] = title[:100]
            fixes.append({
                "category": "citation-structure",
                "path": f"citations[{i}].name",
                "old": None,
                "new": citation["name"],
            })

        if "description" not in citation:
            title = citation.get("title", "source material")
            citation["description"] = f"Citation for {title}"
            fixes.append({
                "category": "citation-structure",
                "path": f"citations[{i}].description",
                "old": None,
                "new": citation["description"],
            })

        if "author" in citation and "authors" not in citation:
            author = citation["author"]
            citation["authors"] = [author] if isinstance(author, str) else author
            del citation["author"]
            fixes.append({
                "category": "citation-structure",
                "path": f"citations[{i}].authors",
                "old": "author (singular)",
                "new": "authors (array)",
            })

    return fixes


def fix_contributes_to(data):
    fixes = []
    for i, alpha in enumerate(data.get("alphas", [])):
        if "contributesTo" in alpha:
            old_val = alpha["contributesTo"]
            if old_val == "" or old_val is None or old_val == []:
                del alpha["contributesTo"]
                fixes.append({
                    "category": "baseline-alpha",
                    "path": f"alphas[{i}].contributesTo",
                    "old": repr(old_val),
                    "new": "(removed — baseline alphas are root-level)",
                })
    return fixes


def fix_narrative_citations(data):
    fixes = []
    citations = data.get("citations", [])
    if not citations:
        return fixes

    citation_names = [c.get("name") for c in citations if c.get("name")]
    if not citation_names:
        return fixes

    for i, narrative in enumerate(data.get("narratives", [])):
        existing = narrative.get("citationNames")
        if not existing or len(existing) == 0:
            narrative["citationNames"] = citation_names
            fixes.append({
                "category": "narrative-citations",
                "path": f"narratives[{i}].citationNames",
                "old": existing,
                "new": f"{len(citation_names)} citation names added",
            })
    return fixes


# --- Optional fixes (flag-gated) ---

def fix_truncated_names(data):
    fixes = []
    for alpha in data.get("alphas", []):
        alpha_name = alpha.get("name", "")
        for state in alpha.get("states", []):
            state_name = state.get("name", "")
            for j, cl in enumerate(state.get("checklist", [])):
                name = cl.get("name", "")
                desc = cl.get("description", "")
                if len(name) == 50 and desc.startswith(name) and len(desc) > 50:
                    old_name = name
                    cl["name"] = desc
                    fixes.append({
                        "category": "checklist-quality",
                        "path": f"alphas['{alpha_name}'].states['{state_name}'].checklist[{j}].name",
                        "old": old_name,
                        "new": desc,
                    })
    return fixes


def fix_relationship_types(data):
    fixes = []
    for i, alpha in enumerate(data.get("alphas", [])):
        for j, rel in enumerate(alpha.get("relatesTo", [])):
            rel_type = rel.get("relationship", "")
            if rel_type not in STANDARD_RELATIONSHIP_TYPES:
                normalized = RELATIONSHIP_NORMALIZATIONS.get(rel_type)
                if normalized:
                    rel["relationship"] = normalized
                    fixes.append({
                        "category": "relationship-type",
                        "path": f"alphas[{i}].relatesTo[{j}].relationship",
                        "old": rel_type,
                        "new": normalized,
                    })
    return fixes


def fix_tags_structure(data):
    fixes = []
    has_domain = "domainTags" in data
    has_lifecycle = "lifecycleTags" in data
    has_org = "organizationalTags" in data

    if has_domain or has_lifecycle or has_org:
        tags = {}
        if has_domain:
            tags["domainTags"] = data.pop("domainTags")
        if has_lifecycle:
            tags["lifecycleTags"] = data.pop("lifecycleTags")
        if has_org:
            tags["organizationalTags"] = data.pop("organizationalTags")
        data["tags"] = tags
        fixes.append({
            "category": "schema-violation",
            "path": "tags",
            "old": "flat domainTags/lifecycleTags/organizationalTags",
            "new": "nested tags object",
        })
    return fixes


def fix_persona_groups(data):
    fixes = []
    if "teams" in data:
        data["personaGroups"] = data.pop("teams")
        fixes.append({
            "category": "schema-violation",
            "path": "personaGroups",
            "old": "teams",
            "new": "personaGroups (renamed)",
        })
    return fixes


def fix_persona_properties(data):
    fixes = []
    for i, persona in enumerate(data.get("personas", [])):
        if "personaName" in persona:
            persona["name"] = persona.pop("personaName")
            fixes.append({
                "category": "schema-violation",
                "path": f"personas[{i}].name",
                "old": "personaName",
                "new": "name (renamed)",
            })
        if "personaDescription" in persona:
            persona["description"] = persona.pop("personaDescription")
            fixes.append({
                "category": "schema-violation",
                "path": f"personas[{i}].description",
                "old": "personaDescription",
                "new": "description (renamed)",
            })
    return fixes


def fix_activity_technique_narratives(data):
    fixes = []
    for i, activity in enumerate(data.get("activities", [])):
        if "techniqueNarratives" in activity:
            narratives = activity.pop("techniqueNarratives")
            activity["narratives"] = narratives
            fixes.append({
                "category": "schema-violation",
                "path": f"activities[{i}].narratives",
                "old": "techniqueNarratives",
                "new": "narratives (renamed)",
            })
    return fixes


def fix_contributesto_arrays(data):
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        for i, alpha in enumerate(source.get("alphas", [])):
            ct = alpha.get("contributesTo")
            if isinstance(ct, list):
                if len(ct) > 0:
                    alpha["contributesTo"] = ct[0]
                    fixes.append({
                        "category": "contributesto-array",
                        "path": f"alphas[{i}].contributesTo",
                        "old": repr(ct),
                        "new": ct[0],
                    })
                else:
                    del alpha["contributesTo"]
                    fixes.append({
                        "category": "contributesto-array",
                        "path": f"alphas[{i}].contributesTo",
                        "old": "[]",
                        "new": "(removed empty array)",
                    })
    return fixes


def main():
    parser = argparse.ArgumentParser(
        description="Auto-fix common practice/method/baseline JSON issues"
    )
    parser.add_argument("file", help="Practice, method, or baseline JSON file")
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply fixes in-place (default: dry run)"
    )
    parser.add_argument(
        "--normalize-relationships", action="store_true",
        help="Normalize relationship types to standard set (produces/governed by/uses)"
    )
    parser.add_argument(
        "--fix-truncated-names", action="store_true",
        help="Replace 50-char truncated checklist names with full description text"
    )
    parser.add_argument(
        "--fix-schema", action="store_true",
        help="Fix schema violations (tags nesting, teams→personaGroups, persona properties, techniqueNarratives)"
    )
    parser.add_argument(
        "--fix-contributesto-arrays", action="store_true",
        help="Convert contributesTo arrays to strings"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Enable all optional fixes"
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    data, err = load_json_pair(file_path)
    if err:
        print(json.dumps({"error": err}))
        sys.exit(1)

    all_fixes = []

    all_fixes.extend(fix_kind(data))
    all_fixes.extend(fix_narratives(data))
    all_fixes.extend(fix_citations(data))
    all_fixes.extend(fix_contributes_to(data))
    all_fixes.extend(fix_narrative_citations(data))

    if args.fix_truncated_names or args.all:
        all_fixes.extend(fix_truncated_names(data))

    if args.normalize_relationships or args.all:
        all_fixes.extend(fix_relationship_types(data))

    if args.fix_schema or args.all:
        all_fixes.extend(fix_tags_structure(data))
        all_fixes.extend(fix_persona_groups(data))
        all_fixes.extend(fix_persona_properties(data))
        all_fixes.extend(fix_activity_technique_narratives(data))

    if args.fix_contributesto_arrays or args.all:
        all_fixes.extend(fix_contributesto_arrays(data))

    if args.fix and all_fixes:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    category_counts = {}
    for fix in all_fixes:
        cat = fix["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    report = {
        "file": str(file_path),
        "mode": "fix" if args.fix else "dry-run",
        "fixCount": len(all_fixes),
        "categoryCounts": category_counts,
        "fixes": all_fixes,
        "applied": args.fix,
    }

    print(json.dumps(report, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
