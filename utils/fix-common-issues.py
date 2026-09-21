#!/usr/bin/env python3
"""Auto-fix common practice/method/baseline JSON issues.

Consolidates structural fixes detected by assess-practice.py:
- Missing 'kind' discriminator property
- Method-invalid properties (strips authors/etc. from method-kind docs)
- Narrative structure (missing name/description from PracticeElement)
- Citation structure (missing PracticeElement fields)
- Empty contributesTo on baseline alphas (should not exist)
- Narrative citation references (adds all citations to narratives)
- focusName correction (aligns sub-alpha focus to contributesTo/mapsTo parent)
- Truncated checklist names (replaces 50-char truncated names with full description)
- Relationship type normalization
- relatesTo rationale→description rename (rationale is not a schema field)
- Schema violations: techniqueNarratives→narratives, tags nesting, teams→personaGroups
- Persona property names (personaName→name, personaDescription→description)
- contributesTo arrays→strings (schema defines as string, not array)
- relatesTo direction inference (adds required 'direction' field based on relationship verb)
- Gherkin structure (background/test/examples type coercion and placement validation)
- Element-level kind discriminators (narrativeTypes, activitySpaces, etc.)
- Alias isolation (replace alias names in structural references with canonical names)
- mapsTo variant naming (strip parent type name from variant alpha names and update refs)
- Narrative schema (remove invalid kind='narrative', fix narrativeContext field names)
- Self-referencing backgrounds (remove alphaStates entries that reference the owning alpha)
- Unknown activity spaces (replace invalid activitySpaceNames with closest baseline match)
- Invalid narrative types (replace narrativeTypeName values not in baseline with closest match)
- Invalid competency refs (fix competency names and levels not in baseline, with deduplication)
- Nested narrative wrappers (flatten narratives[i].narratives[] into top-level, merge citations)
- Missing version/schemaVersion (add version 1.0.0 and schemaVersion from schema)

Usage:
    # Dry run — show what would be fixed
    python3 utils/fix-common-issues.py <file.json>

    # Apply fixes in-place
    python3 utils/fix-common-issues.py <file.json> --fix

    # With baseline (enables focusName correction)
    python3 utils/fix-common-issues.py <file.json> <baseline.json> --fix

    # Also normalize relationship types to standard set
    python3 utils/fix-common-issues.py <file.json> --fix --normalize-relationships

    # Also fix truncated checklist names
    python3 utils/fix-common-issues.py <file.json> --fix --fix-truncated-names

    # Fix schema violations (tags, persona groups, persona properties)
    python3 utils/fix-common-issues.py <file.json> --fix --fix-schema

    # Fix contributesTo arrays to strings
    python3 utils/fix-common-issues.py <file.json> --fix --fix-contributesto-arrays

    # Fix Gherkin structure issues (background/test/examples)
    python3 utils/fix-common-issues.py <file.json> --fix --fix-gherkin

    # Move top-level narratives to matching elements
    python3 utils/fix-common-issues.py <file.json> --fix --fix-narrative-placement

    # Add carry-forward alpha states to incomplete pattern views
    python3 utils/fix-common-issues.py <file.json> --fix --fix-pattern-completeness

    # Replace alias names in structural references with canonical names
    python3 utils/fix-common-issues.py <file.json> --fix --fix-alias-isolation

    # Strip parent type name from mapsTo variant alpha names
    python3 utils/fix-common-issues.py <file.json> <baseline.json> --fix --fix-mapsto-naming

    # Fix invalid kind='narrative' and wrong narrativeContext field names
    python3 utils/fix-common-issues.py <file.json> --fix --fix-narrative-schema

    # Auto-create asset definitions for unresolved assetNames references
    python3 utils/fix-common-issues.py <file.json> --fix --fix-missing-assets

    # Remove self-referencing background alphaStates
    python3 utils/fix-common-issues.py <file.json> --fix --fix-self-ref-backgrounds

    # Replace unknown activitySpaceNames with closest baseline match
    python3 utils/fix-common-issues.py <file.json> <baseline.json> --fix --fix-unknown-activity-spaces

    # Flatten nested narrative wrappers (narratives[i].narratives[])
    python3 utils/fix-common-issues.py <file.json> --fix --fix-nested-narratives

    # Add missing version and schemaVersion
    python3 utils/fix-common-issues.py <file.json> --fix --fix-versions

    # Apply all optional fixes
    python3 utils/fix-common-issues.py <file.json> --fix --all

Output: JSON report to stdout. Exit 0 on success, 1 on error.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json_pair, get_schema_version


STANDARD_RELATIONSHIP_TYPES = {"produces", "governed by", "uses"}

RELATIONSHIP_NORMALIZATIONS = {
    "governs": "governed by",
    "supports": "produces",
    "enables": "produces",
    "enables delivery of": "produces",
    "provides": "produces",
    "enhances": "produces",
    "strengthens": "produces",
    "strengthened by": "uses",
    "drives": "produces",
    "constrains": "governed by",
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


COLLECTION_KIND_MAP = {
    "narrativeTypes": "narrativeType",
    "activitySpaces": "activitySpace",
    "alphas": "alpha",
    "activities": "activity",
    "workProducts": "workProduct",
    "patterns": "pattern",
    "personas": "persona",
    "personaGroups": "personaGroup",
    "citations": "citation",
}


def fix_element_kind(data):
    fixes = []
    sources = [data] + data.get("practices", [])
    for source in sources:
        for coll_key, expected_kind in COLLECTION_KIND_MAP.items():
            for i, elem in enumerate(source.get(coll_key, [])):
                current = elem.get("kind")
                if current != expected_kind:
                    elem["kind"] = expected_kind
                    elem_name = elem.get("name", f"[{i}]")
                    fixes.append({
                        "category": "element-kind",
                        "path": f"{coll_key}['{elem_name}'].kind",
                        "old": current,
                        "new": expected_kind,
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


METHOD_INVALID_PROPERTIES = {"authors", "createdAt", "updatedAt", "keywords"}


def fix_method_properties(data):
    """Strip properties that are invalid on method-kind documents."""
    fixes = []
    if data.get("kind") != "method":
        return fixes
    for prop in sorted(METHOD_INVALID_PROPERTIES):
        if prop in data:
            del data[prop]
            fixes.append({
                "category": "method-properties",
                "path": prop,
                "old": "(present)",
                "new": "(removed — not valid on method-kind documents)",
            })
    return fixes


def fix_focus_names(data, baseline=None):
    """Correct focusName on sub-alphas to match their contributesTo parent's focus."""
    fixes = []
    if not baseline:
        return fixes

    baseline_alpha_focus = {}
    for alpha in baseline.get("alphas", []):
        baseline_alpha_focus[alpha["name"]] = alpha.get("focusName", "")

    local_alpha_focus = {}
    for alpha in data.get("alphas", []):
        local_alpha_focus[alpha["name"]] = alpha.get("focusName", "")

    for alpha in data.get("alphas", []):
        parent = alpha.get("contributesTo") or alpha.get("mapsTo")
        if not parent:
            continue
        expected_focus = baseline_alpha_focus.get(parent) or local_alpha_focus.get(parent)
        if not expected_focus:
            continue
        current_focus = alpha.get("focusName", "")
        if current_focus != expected_focus:
            old = current_focus
            alpha["focusName"] = expected_focus
            fixes.append({
                "category": "focus-name",
                "path": f"alphas[{alpha['name']}].focusName",
                "old": old,
                "new": expected_focus,
                "reason": f"contributesTo/mapsTo parent '{parent}' has focusName '{expected_focus}'",
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


DIRECTION_HEURISTICS = {
    "produces": "outgoing",
    "enables": "outgoing",
    "constrains": "outgoing",
    "guides": "outgoing",
    "depends on": "outgoing",
    "consumes": "outgoing",
    "hosts": "outgoing",
    "provides": "outgoing",
    "validates": "outgoing",
    "influences": "outgoing",
    "requires": "outgoing",
    "uses": "outgoing",
    "supports": "outgoing",
    "implements": "outgoing",
    "governs": "outgoing",
    "protects": "outgoing",
    "justifies": "outgoing",
    "enforces": "outgoing",
    "informs": "outgoing",
    "defines": "outgoing",
    "drives": "outgoing",
    "motivates": "outgoing",
    "aligns": "outgoing",
    "initiates": "outgoing",
    "adapts": "outgoing",
    "filters": "outgoing",
    "identifies": "outgoing",
    "realizes": "outgoing",
    "establishes": "outgoing",
    "evidences": "outgoing",
    "measures": "outgoing",
    "shapes": "outgoing",
    "coordinates": "outgoing",
    "exposes": "outgoing",
    "monitors": "outgoing",
    "optimizes": "outgoing",
    "enhances": "outgoing",
    "improves": "outgoing",
    "mitigates": "outgoing",
    "performs": "outgoing",
    "applies": "outgoing",
    "reduces": "outgoing",
    "addresses": "outgoing",
    "extends": "outgoing",
    "remediates": "outgoing",
    "integrates": "outgoing",
    "generates": "outgoing",
    "analyzes": "outgoing",
    "triggers": "outgoing",
    "executes": "outgoing",
    "develops": "outgoing",
    "tracks": "outgoing",
    "demonstrates": "outgoing",
    "allocates": "outgoing",
    "packages": "outgoing",
    "feeds": "outgoing",
    "maintains": "outgoing",
    "formalizes": "outgoing",
    "funds": "outgoing",
    "operationalizes": "outgoing",
    "assesses": "outgoing",
    "challenges": "outgoing",
    "threatens": "outgoing",
    "contributes to": "outgoing",
    "governed by": "incoming",
    "built by": "incoming",
    "validated by": "incoming",
    "supported by": "incoming",
    "required by": "incoming",
    "constrained by": "incoming",
    "guided by": "incoming",
    "managed by": "incoming",
    "enabled by": "incoming",
    "provided by": "incoming",
    "protected by": "incoming",
    "enhanced by": "incoming",
    "optimized by": "incoming",
    "informed by": "incoming",
    "evidenced by": "incoming",
    "justified by": "incoming",
    "driven by": "incoming",
    "influenced by": "incoming",
    "produced by": "incoming",
    "shaped by": "incoming",
    "reinforced by": "incoming",
    "monitored by": "incoming",
    "decided by": "incoming",
    "measured by": "incoming",
    "performed by": "incoming",
    "scoped by": "incoming",
    "reviewed by": "incoming",
    "realized by": "incoming",
    "configured by": "incoming",
    "hosted by": "incoming",
    "secured by": "incoming",
    "identified by": "incoming",
    "executed by": "incoming",
    "reduced by": "incoming",
    "powered by": "incoming",
    "established by": "incoming",
    "complemented by": "incoming",
    "referenced by": "incoming",
    "runs on": "incoming",
    "deployed on": "incoming",
    "based on": "incoming",
    "consumed via": "incoming",
    "aligned with": "mutual",
    "correlates with": "mutual",
    "co-evolves with": "mutual",
    "coordinates with": "mutual",
    "integrates with": "mutual",
    "shares knowledge with": "mutual",
    "synchronizes": "mutual",
    "complements": "mutual",
}

_INCOMING_SUFFIXES = (" by", " from", " via")


def _infer_direction(verb):
    if verb in DIRECTION_HEURISTICS:
        return DIRECTION_HEURISTICS[verb]
    v = verb.lower().strip()
    if any(v.endswith(s) for s in _INCOMING_SUFFIXES):
        return "incoming"
    if " with " in v or v.endswith(" with"):
        return "mutual"
    return "outgoing"


def fix_relates_to_rationale(data):
    fixes = []
    sources = [data] + data.get("practices", [])
    for source in sources:
        for i, alpha in enumerate(source.get("alphas", [])):
            for j, rel in enumerate(alpha.get("relatesTo", [])):
                if "rationale" in rel:
                    rel["description"] = rel.pop("rationale")
                    fixes.append({
                        "category": "relates-to-rationale",
                        "path": f"alphas[{i}].relatesTo[{j}]",
                        "old": "rationale",
                        "new": "description",
                    })
    return fixes


def fix_relates_to_direction(data):
    fixes = []
    sources = [data] + data.get("practices", [])
    for source in sources:
        for i, alpha in enumerate(source.get("alphas", [])):
            for j, rel in enumerate(alpha.get("relatesTo", [])):
                if "direction" not in rel:
                    verb = rel.get("relationship", "")
                    inferred = _infer_direction(verb)
                    rel["direction"] = inferred
                    fixes.append({
                        "category": "relates-to-direction",
                        "path": f"alphas[{i}].relatesTo[{j}].direction",
                        "old": "(missing)",
                        "new": inferred,
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


def _fix_background_type(obj, path):
    """Fix background when it is a string or list instead of an object."""
    fixes = []
    bg = obj.get("background")
    if bg is None or isinstance(bg, dict):
        return fixes
    if isinstance(bg, str):
        obj["background"] = {"given": [bg]}
        fixes.append({
            "category": "gherkin-structure",
            "path": f"{path}.background",
            "old": repr(bg),
            "new": {"given": [bg]},
        })
    elif isinstance(bg, list):
        obj["background"] = {"given": bg}
        fixes.append({
            "category": "gherkin-structure",
            "path": f"{path}.background",
            "old": repr(bg),
            "new": {"given": bg},
        })
    return fixes


def _fix_test_type(obj, path):
    """Fix test when it is a string or list instead of a Test object."""
    fixes = []
    test = obj.get("test")
    if test is None or isinstance(test, dict):
        return fixes
    if isinstance(test, str):
        new_val = {"name": "Verification", "description": test}
        obj["test"] = new_val
        fixes.append({
            "category": "gherkin-structure",
            "path": f"{path}.test",
            "old": repr(test),
            "new": new_val,
        })
    elif isinstance(test, list):
        new_val = {"name": "Verification", "description": "Verification scenario", "then": test}
        obj["test"] = new_val
        fixes.append({
            "category": "gherkin-structure",
            "path": f"{path}.test",
            "old": repr(test),
            "new": new_val,
        })
    return fixes


def _fix_examples_type(obj, path):
    """Fix examples when it is a dict or string instead of an array of Test objects."""
    fixes = []
    ex = obj.get("examples")
    if ex is None or isinstance(ex, list):
        return fixes
    if isinstance(ex, dict):
        obj["examples"] = [ex]
        fixes.append({
            "category": "gherkin-structure",
            "path": f"{path}.examples",
            "old": repr(ex),
            "new": [ex],
        })
    elif isinstance(ex, str):
        new_val = [{"name": "Example", "description": ex}]
        obj["examples"] = new_val
        fixes.append({
            "category": "gherkin-structure",
            "path": f"{path}.examples",
            "old": repr(ex),
            "new": new_val,
        })
    return fixes


def _remove_gherkin_placement(obj, path, prop):
    """Remove a Gherkin property that is on a wrong element."""
    fixes = []
    if prop in obj:
        old_val = obj.pop(prop)
        fixes.append({
            "category": "gherkin-placement",
            "path": f"{path}.{prop}",
            "old": repr(old_val),
            "new": "(removed — only valid on Checklist items and Activity)",
        })
    return fixes


def fix_gherkin_structure(data):
    """Fix Gherkin structural issues: type coercion and placement validation.

    Fixes:
    - background as string/list → wrap in object with 'given' key
    - test as string/list → wrap in Test object
    - examples as dict/string → wrap in array
    - Remove test/examples from States and LevelsOfDetail (wrong placement)
    """
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        # --- Alphas → States ---
        for ai, alpha in enumerate(source.get("alphas", [])):
            alpha_name = alpha.get("name", f"alpha[{ai}]")
            for si, state in enumerate(alpha.get("states", [])):
                state_name = state.get("name", f"state[{si}]")
                state_path = f"alphas['{alpha_name}'].states['{state_name}']"

                # Fix background type on states (valid location)
                fixes.extend(_fix_background_type(state, state_path))

                # Remove test/examples from states (wrong placement)
                fixes.extend(_remove_gherkin_placement(state, state_path, "test"))
                fixes.extend(_remove_gherkin_placement(state, state_path, "examples"))

                # Fix test/examples type on checklist items (valid location)
                for ci, cl in enumerate(state.get("checklist", [])):
                    cl_name = cl.get("name", f"checklist[{ci}]")
                    cl_path = f"{state_path}.checklist['{cl_name}']"
                    fixes.extend(_fix_test_type(cl, cl_path))
                    fixes.extend(_fix_examples_type(cl, cl_path))

        # --- WorkProducts → LevelsOfDetail ---
        for wi, wp in enumerate(source.get("workProducts", [])):
            wp_name = wp.get("name", f"workProduct[{wi}]")
            for li, lod in enumerate(wp.get("levelsOfDetail", [])):
                lod_name = lod.get("name", f"lod[{li}]")
                lod_path = f"workProducts['{wp_name}'].levelsOfDetail['{lod_name}']"

                # Fix background type on levelsOfDetail (valid location)
                fixes.extend(_fix_background_type(lod, lod_path))

                # Remove test/examples from levelsOfDetail (wrong placement)
                fixes.extend(_remove_gherkin_placement(lod, lod_path, "test"))
                fixes.extend(_remove_gherkin_placement(lod, lod_path, "examples"))

        # --- ActivitySpaces ---
        for asi, aspace in enumerate(source.get("activitySpaces", [])):
            aspace_name = aspace.get("name", f"activitySpace[{asi}]")
            aspace_path = f"activitySpaces['{aspace_name}']"

            # Fix background type on activitySpaces (valid location)
            fixes.extend(_fix_background_type(aspace, aspace_path))

        # --- Activities ---
        for acti, activity in enumerate(source.get("activities", [])):
            act_name = activity.get("name", f"activity[{acti}]")
            act_path = f"activities['{act_name}']"

            # Fix background type on activities (valid location)
            fixes.extend(_fix_background_type(activity, act_path))

            # Fix test/examples type on activities (valid location)
            fixes.extend(_fix_test_type(activity, act_path))
            fixes.extend(_fix_examples_type(activity, act_path))

    return fixes


def fix_narrative_placement(data):
    """Move top-level narratives to matching element's narratives[] array."""
    fixes = []
    element_map = {}
    for coll_key in ("alphas", "activitySpaces", "competencies"):
        for elem in data.get(coll_key, []):
            name = elem.get("name", "")
            if name:
                element_map[name.lower()] = (coll_key, elem)

    sorted_names = sorted(element_map.keys(), key=len, reverse=True)

    to_remove = []
    for i, narrative in enumerate(data.get("narratives", [])):
        narr_name = narrative.get("name", "").lower()
        narr_desc = narrative.get("description", "").lower()
        for elem_name_lower in sorted_names:
            if elem_name_lower in narr_name or elem_name_lower in narr_desc:
                coll_key, elem = element_map[elem_name_lower]
                elem.setdefault("narratives", []).append(narrative)
                to_remove.append(i)
                fixes.append({
                    "category": "narrative-placement",
                    "path": f"narratives[{i}]",
                    "old": f"top-level narrative '{narrative.get('name', '')}'",
                    "new": f"moved to {coll_key}['{elem.get('name', '')}'].narratives",
                })
                break

    for idx in reversed(to_remove):
        data["narratives"].pop(idx)

    if data.get("narratives") == []:
        del data["narratives"]

    return fixes


def fix_pattern_completeness(data):
    """Add carry-forward alpha states to pattern views missing practice alphas,
    then compress by removing unchanged carry-forward states from non-final views."""
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        alpha_first_state = {}
        for alpha in source.get("alphas", []):
            aname = alpha.get("name", "")
            states = alpha.get("states", [])
            if aname and states:
                alpha_first_state[aname] = states[0].get("name", "")

        all_alpha_names = set(alpha_first_state.keys())
        if len(all_alpha_names) < 2:
            continue

        for pi, pattern in enumerate(source.get("patterns", [])):
            pat_name = pattern.get("name", f"pattern[{pi}]")
            views = pattern.get("patternViews", [])
            views_sorted = sorted(views, key=lambda v: v.get("seq", 0))

            # Pass 1: Add carry-forward states for truly missing alphas (final view only)
            last_state = {}
            for vi, view in enumerate(views_sorted):
                is_final = (vi == len(views_sorted) - 1)
                view_seq = view.get("seq", "?")
                for astate in view.get("alphaStates", []):
                    aname = astate.get("alphaName", "")
                    sname = astate.get("stateName", "")
                    last_state[aname] = sname

                if is_final:
                    view_alphas = {a.get("alphaName", "") for a in view.get("alphaStates", [])}
                    missing = all_alpha_names - view_alphas
                    for aname in sorted(missing):
                        carry = last_state.get(aname, alpha_first_state.get(aname, ""))
                        if not carry:
                            continue
                        view.setdefault("alphaStates", []).append({
                            "alphaName": aname,
                            "stateName": carry,
                        })
                        fixes.append({
                            "category": "pattern-completeness",
                            "path": f"patterns['{pat_name}'].patternViews[{view_seq}]",
                            "old": f"missing alpha '{aname}' in final view",
                            "new": f"carry-forward state '{carry}'",
                        })

            # Pass 2: Compress — remove unchanged carry-forward states from non-final views
            fixes.extend(compress_pattern_states_for_pattern(
                pattern, pat_name, views_sorted
            ))

    return fixes


def compress_pattern_states(data):
    """Remove unchanged carry-forward alpha states from non-final pattern views."""
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        for pi, pattern in enumerate(source.get("patterns", [])):
            pat_name = pattern.get("name", f"pattern[{pi}]")
            views = pattern.get("patternViews", [])
            views_sorted = sorted(views, key=lambda v: v.get("seq", 0))
            fixes.extend(compress_pattern_states_for_pattern(
                pattern, pat_name, views_sorted
            ))

    return fixes


def compress_pattern_states_for_pattern(pattern, pat_name, views_sorted):
    """Remove unchanged carry-forward alpha states from non-final views,
    then remove empty non-final views (merging activities into the next view)."""
    fixes = []
    prev_states = {}

    for vi, view in enumerate(views_sorted):
        is_final = (vi == len(views_sorted) - 1)
        view_seq = view.get("seq", "?")
        alpha_states = view.get("alphaStates", [])

        if is_final:
            for astate in alpha_states:
                prev_states[astate.get("alphaName", "")] = astate.get("stateName", "")
            continue

        kept = []
        for astate in alpha_states:
            aname = astate.get("alphaName", "")
            sname = astate.get("stateName", "")
            if aname in prev_states and prev_states[aname] == sname:
                fixes.append({
                    "category": "pattern-compression",
                    "path": f"patterns['{pat_name}'].patternViews[{view_seq}]",
                    "old": f"carry-forward '{aname}' = '{sname}'",
                    "new": "removed (unchanged from previous view)",
                })
            else:
                kept.append(astate)
            prev_states[aname] = sname

        view["alphaStates"] = kept

    # Remove empty non-final views, merging activities into next view
    to_remove = []
    for vi in range(len(views_sorted) - 1):
        view = views_sorted[vi]
        if not view.get("alphaStates"):
            next_view = views_sorted[vi + 1] if vi + 1 < len(views_sorted) else None
            if next_view:
                orphaned = view.get("activities", [])
                next_view["activities"] = orphaned + next_view.get("activities", [])
                fixes.append({
                    "category": "pattern-compression",
                    "path": f"patterns['{pat_name}'].patternViews[{view.get('seq', '?')}]",
                    "old": f"empty view '{view.get('name', '?')}' with {len(orphaned)} activities",
                    "new": f"removed, activities merged into '{next_view.get('name', '?')}'",
                })
                to_remove.append(vi)

    for idx in reversed(to_remove):
        views_sorted.pop(idx)

    # Renumber seq values
    for i, view in enumerate(views_sorted):
        if view.get("seq") != i:
            fixes.append({
                "category": "pattern-compression",
                "path": f"patterns['{pat_name}'].patternViews",
                "old": f"'{view.get('name', '?')}' seq={view['seq']}",
                "new": f"seq={i}",
            })
            view["seq"] = i

    pattern["patternViews"] = views_sorted

    return fixes


def _update_alpha_references(source, renames):
    """Update all alpha name references in a source document. Returns list of fix dicts."""
    fixes = []

    for alpha in source.get("alphas", []):
        alpha_name = alpha.get("name", "")
        for rel in alpha.get("relatesTo", []):
            old_target = rel.get("alphaName", "")
            if old_target in renames:
                rel["alphaName"] = renames[old_target]
                fixes.append({
                    "category": "alpha-rename-ref",
                    "path": f"alphas['{alpha_name}'].relatesTo[].alphaName",
                    "old": old_target,
                    "new": renames[old_target],
                })

    for activity in source.get("activities", []):
        act_name = activity.get("name", "")
        for ct in activity.get("contributesTo", []):
            old = ct.get("alphaName", "")
            if old in renames:
                ct["alphaName"] = renames[old]
                fixes.append({
                    "category": "alpha-rename-ref",
                    "path": f"activities['{act_name}'].contributesTo[].alphaName",
                    "old": old,
                    "new": renames[old],
                })
        for wo in activity.get("worksOn", []):
            old = wo.get("alphaName", "")
            if old in renames:
                wo["alphaName"] = renames[old]
                fixes.append({
                    "category": "alpha-rename-ref",
                    "path": f"activities['{act_name}'].worksOn[].alphaName",
                    "old": old,
                    "new": renames[old],
                })

    for pattern in source.get("patterns", []):
        pat_name = pattern.get("name", "")
        for view in pattern.get("patternViews", []):
            for astate in view.get("alphaStates", []):
                old = astate.get("alphaName", "")
                if old in renames:
                    astate["alphaName"] = renames[old]
                    fixes.append({
                        "category": "alpha-rename-ref",
                        "path": f"patterns['{pat_name}'].patternViews[].alphaStates[].alphaName",
                        "old": old,
                        "new": renames[old],
                    })

    for wp in source.get("workProducts", []):
        wp_name = wp.get("name", "")
        for lod in wp.get("levelsOfDetail", []):
            for astate in lod.get("alphaStates", []):
                old = astate.get("alphaName", "")
                if old in renames:
                    astate["alphaName"] = renames[old]
                    fixes.append({
                        "category": "alpha-rename-ref",
                        "path": f"workProducts['{wp_name}'].levelsOfDetail[].alphaStates[].alphaName",
                        "old": old,
                        "new": renames[old],
                    })

    aliases_key = "practiceElementAliases" if "practiceElementAliases" in source else "aliases"
    for alias in source.get(aliases_key, []):
        old = alias.get("name", "")
        if old in renames:
            alias["name"] = renames[old]
            fixes.append({
                "category": "alpha-rename-ref",
                "path": f"{aliases_key}[].name",
                "old": old,
                "new": renames[old],
            })

    return fixes


def fix_alias_isolation(data):
    """Replace alias names in structural references with canonical names."""
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        aliases_key = "practiceElementAliases" if "practiceElementAliases" in source else "aliases"
        aliases = source.get(aliases_key, [])
        alias_to_canonical = {}
        for alias in aliases:
            aname = alias.get("aliasName", "")
            canonical = alias.get("name", "")
            if aname and canonical:
                alias_to_canonical[aname] = canonical

        if not alias_to_canonical:
            continue

        for alpha in source.get("alphas", []):
            alpha_name = alpha.get("name", "")
            for field in ("contributesTo", "mapsTo"):
                val = alpha.get(field, "")
                if val in alias_to_canonical:
                    alpha[field] = alias_to_canonical[val]
                    fixes.append({
                        "category": "alias-isolation",
                        "path": f"alphas['{alpha_name}'].{field}",
                        "old": val,
                        "new": alias_to_canonical[val],
                    })

            for rel in alpha.get("relatesTo", []):
                target = rel.get("alphaName", "")
                if target in alias_to_canonical:
                    rel["alphaName"] = alias_to_canonical[target]
                    fixes.append({
                        "category": "alias-isolation",
                        "path": f"alphas['{alpha_name}'].relatesTo[].alphaName",
                        "old": target,
                        "new": alias_to_canonical[target],
                    })

        for activity in source.get("activities", []):
            act_name = activity.get("name", "")

            as_name = activity.get("activitySpaceName", "")
            if as_name in alias_to_canonical:
                activity["activitySpaceName"] = alias_to_canonical[as_name]
                fixes.append({
                    "category": "alias-isolation",
                    "path": f"activities['{act_name}'].activitySpaceName",
                    "old": as_name,
                    "new": alias_to_canonical[as_name],
                })

            for ct in activity.get("contributesTo", []):
                aname = ct.get("alphaName", "")
                if aname in alias_to_canonical:
                    ct["alphaName"] = alias_to_canonical[aname]
                    fixes.append({
                        "category": "alias-isolation",
                        "path": f"activities['{act_name}'].contributesTo[].alphaName",
                        "old": aname,
                        "new": alias_to_canonical[aname],
                    })

    return fixes


def fix_mapsto_naming(data, baseline=None):
    """Strip parent type name from mapsTo variant alpha names and update all references."""
    fixes = []
    if data.get("kind") == "practiceBaseline":
        return fixes

    all_alphas = {}
    for a in data.get("alphas", []):
        all_alphas[a.get("name", "")] = a
    if baseline:
        for a in baseline.get("alphas", []):
            all_alphas.setdefault(a.get("name", ""), a)

    renames = {}

    for alpha in data.get("alphas", []):
        maps_to = alpha.get("mapsTo")
        if not maps_to:
            continue

        alpha_name = alpha.get("name", "")
        parent = all_alphas.get(maps_to)
        if not parent:
            continue

        parent_name = parent.get("name", maps_to)
        if parent_name.lower() not in alpha_name.lower():
            continue

        idx = alpha_name.lower().find(parent_name.lower())
        new_name = (alpha_name[:idx] + alpha_name[idx + len(parent_name):]).strip(" -–—")
        if not new_name:
            continue

        renames[alpha_name] = new_name

    if not renames:
        return fixes

    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        for alpha in source.get("alphas", []):
            old_name = alpha.get("name", "")
            if old_name in renames:
                alpha["name"] = renames[old_name]
                fixes.append({
                    "category": "mapsto-naming",
                    "path": f"alphas['{old_name}'].name",
                    "old": old_name,
                    "new": renames[old_name],
                })

        fixes.extend(_update_alpha_references(source, renames))

    return fixes


def fix_narrative_schema(data):
    """Fix narrative schema issues: invalid kind='narrative' and wrong narrativeContext field names.

    Fixes:
    - Remove kind='narrative' from narratives (not a valid PracticeElement kind enum value)
    - Rename sequenceNumber→seq in narrativeContexts
    - Rename name→narrativeElementName in narrativeContexts (when narrativeElementName absent)
    - Rename narrativeElements→context in narrativeContexts (join array with space if list)
    """
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        narrative_locations = []

        # Top-level narratives
        if "narratives" in source:
            narrative_locations.append((source["narratives"], "narratives"))

        # Element-level narratives across all sections
        for coll_key in ("alphas", "activities", "workProducts", "competencies",
                         "activitySpaces", "focuses", "narrativeTypes", "personas",
                         "patterns"):
            for ei, elem in enumerate(source.get(coll_key, [])):
                if "narratives" in elem:
                    narrative_locations.append(
                        (elem["narratives"], f"{coll_key}.{ei}.narratives")
                    )

        for narratives, path_prefix in narrative_locations:
            for ni, narrative in enumerate(narratives):
                narr_path = f"{path_prefix}.{ni}"

                # Issue 1: Remove invalid kind="narrative"
                if narrative.get("kind") == "narrative":
                    del narrative["kind"]
                    fixes.append({
                        "category": "narrative-schema",
                        "path": narr_path,
                        "old": "kind=narrative",
                        "new": "kind removed",
                    })

                # Issue 2: Fix narrativeContext field names
                for ci, ctx in enumerate(narrative.get("narrativeContexts", [])):
                    ctx_path = f"{narr_path}.narrativeContexts.{ci}"

                    if "sequenceNumber" in ctx:
                        ctx["seq"] = ctx.pop("sequenceNumber")
                        fixes.append({
                            "category": "narrative-schema",
                            "path": f"{ctx_path}.seq",
                            "old": "sequenceNumber",
                            "new": "seq (renamed)",
                        })

                    if "name" in ctx and "narrativeElementName" not in ctx:
                        ctx["narrativeElementName"] = ctx.pop("name")
                        fixes.append({
                            "category": "narrative-schema",
                            "path": f"{ctx_path}.narrativeElementName",
                            "old": "name",
                            "new": "narrativeElementName (renamed)",
                        })

                    if "narrativeElements" in ctx and "context" not in ctx:
                        val = ctx.pop("narrativeElements")
                        if isinstance(val, list):
                            ctx["context"] = " ".join(str(v) for v in val)
                        else:
                            ctx["context"] = val
                        fixes.append({
                            "category": "narrative-schema",
                            "path": f"{ctx_path}.context",
                            "old": "narrativeElements",
                            "new": "context (renamed)",
                        })

    return fixes


DEFAULT_ICONS = {
    "Opportunity": "fa-lightbulb",
    "Stakeholders": "fa-people-group",
    "Objectives": "fa-bullseye",
    "Deliverable": "fa-box",
    "Work": "fa-list-check",
    "Team": "fa-users",
    "Way Of Working": "fa-gears",
    "Platform": "fa-cubes",
    "Requirements": "fa-clipboard-list",
}


def fix_missing_assets(data):
    """Auto-create asset definitions for unresolved assetNames references."""
    fixes = []
    existing = {a["name"] for a in data.get("assets", [])}
    if "assets" not in data:
        data["assets"] = []

    element_sections = [
        ("alphas", "alphas"), ("workProducts", "workProducts"),
        ("activities", "activities"), ("personas", "personas"),
        ("personaGroups", "personaGroups"), ("patterns", "patterns"),
    ]

    for section_key, section_label in element_sections:
        for i, elem in enumerate(data.get(section_key, [])):
            for ref in elem.get("assetNames", []):
                asset_name = ref.get("assetName", "")
                if asset_name and asset_name not in existing:
                    elem_name = elem.get("name", "unknown")
                    icon = DEFAULT_ICONS.get(elem_name, "fa-circle")
                    new_asset = {
                        "name": asset_name,
                        "description": f"Icon for {elem_name}",
                        "type": "font-character",
                        "fontFamily": "Font Awesome 6 Free",
                        "fontCharacter": icon,
                        "fontWeight": "900",
                    }
                    data["assets"].append(new_asset)
                    existing.add(asset_name)
                    fixes.append({
                        "category": "missing-asset",
                        "path": f"assets (new: {asset_name})",
                        "old": "missing",
                        "new": f"created for {section_label}[{i}] '{elem_name}'",
                    })

    return fixes


def fix_self_ref_backgrounds(data):
    """Remove background alphaStates entries that reference the same alpha the state belongs to.

    A state's background should list *prerequisite* alpha-state pairs from OTHER alphas,
    not from the alpha that owns the state.  Self-references are tautological and can
    create acyclicity errors.
    """
    fixes = []
    for alpha in data.get("alphas", []):
        alpha_name = alpha.get("name", "")
        for si, state in enumerate(alpha.get("states", [])):
            bg = state.get("background")
            if not bg or not isinstance(bg, dict):
                continue
            orig = bg.get("alphaStates", [])
            if not orig:
                continue
            filtered = [a for a in orig if a.get("alphaName") != alpha_name]
            if len(filtered) < len(orig):
                removed = len(orig) - len(filtered)
                state_name = state.get("name", f"states[{si}]")
                if filtered:
                    bg["alphaStates"] = filtered
                else:
                    del bg["alphaStates"]
                    if not bg.get("given") and not bg.get("workProductLevels"):
                        del state["background"]
                fixes.append({
                    "category": "self-ref-background",
                    "path": f"alphas['{alpha_name}'].states['{state_name}'].background.alphaStates",
                    "old": f"{len(orig)} entries ({removed} self-referencing)",
                    "new": f"{len(filtered)} entries",
                })
    return fixes


def fix_unknown_activity_spaces(data, baseline):
    """Replace unknown activitySpaceNames with the closest valid baseline match.

    Uses a simple heuristic: if the unknown name contains keywords that match
    a baseline activity space, use that.  Falls back to 'Execute the Sales Play'
    if no heuristic match is found.
    """
    if not baseline:
        return []
    bl_spaces = {a["name"] for a in baseline.get("activitySpaces", [])}
    if not bl_spaces:
        return []

    fixes = []
    for activity in data.get("activities", []):
        asn = activity.get("activitySpaceName", "")
        if not asn or asn in bl_spaces:
            continue
        # Heuristic: keyword matching
        asn_lower = asn.lower()
        best = None
        for sp in sorted(bl_spaces):
            sp_words = set(sp.lower().split())
            asn_words = set(asn_lower.split())
            overlap = sp_words & asn_words
            if len(overlap) >= 2:
                best = sp
                break
        if not best:
            for sp in sorted(bl_spaces):
                if any(w in sp.lower() for w in ["execute", "play", "sell"]):
                    best = sp
                    break
        if not best:
            best = sorted(bl_spaces)[0]
        act_name = activity.get("name", "")
        activity["activitySpaceName"] = best
        fixes.append({
            "category": "unknown-activity-space",
            "path": f"activities['{act_name}'].activitySpaceName",
            "old": asn,
            "new": best,
        })
    return fixes


def fix_narrative_types(data, baseline):
    """Replace narrativeTypeName values not in baseline with closest match."""
    if not baseline:
        return []
    from difflib import SequenceMatcher
    valid_types = {nt["name"] for nt in baseline.get("narrativeTypes", [])}
    if not valid_types:
        return []
    fixes = []

    def _best_match(invalid_name):
        best, best_score = None, 0.0
        for vt in valid_types:
            score = SequenceMatcher(None, invalid_name.lower(), vt.lower()).ratio()
            if score > best_score:
                best_score = score
                best = vt
        return best if best_score >= 0.3 else None

    def _walk(obj, path=""):
        if isinstance(obj, dict):
            ntn = obj.get("narrativeTypeName")
            if ntn and ntn not in valid_types:
                replacement = _best_match(ntn)
                if replacement:
                    obj["narrativeTypeName"] = replacement
                    fixes.append({
                        "category": "narrative-type",
                        "path": f"{path}.narrativeTypeName" if path else "narrativeTypeName",
                        "old": ntn,
                        "new": replacement,
                    })
            for k, v in obj.items():
                _walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk(item, f"{path}[{i}]")

    _walk(data)
    return fixes


def fix_competency_refs(data, baseline, file_path):
    """Fix invalid competency names and levels by delegating to fix-competency-levels.py."""
    if not baseline:
        return []
    valid_comp_names = {c.get("name") for c in baseline.get("competencies", [])}
    valid_levels = set()
    for c in baseline.get("competencies", []):
        for lv in c.get("competencyLevels", c.get("levels", [])):
            if lv.get("name"):
                valid_levels.add(lv["name"])
    if not valid_comp_names:
        return []

    has_invalid = False
    for act in data.get("activities", []):
        for rc in act.get("requiredCompetencies", []):
            if rc not in valid_comp_names:
                has_invalid = True
                break
        if has_invalid:
            break
        for rcl in act.get("recommendedCompetencyLevels", []):
            if rcl.get("competencyName") not in valid_comp_names or rcl.get("competencyLevelName") not in valid_levels:
                has_invalid = True
                break
        if has_invalid:
            break
    if not has_invalid:
        for p in data.get("personas", []):
            for c in p.get("competencies", []):
                if c.get("competencyName") not in valid_comp_names or c.get("competencyLevelName") not in valid_levels:
                    has_invalid = True
                    break
            if has_invalid:
                break

    if not has_invalid:
        return []

    script = Path(__file__).resolve().parent / "fix-competency-levels.py"
    baseline_path = None
    for d in [Path("deps"), Path("baselines")]:
        for f in d.glob("**/*.json"):
            try:
                with open(f) as fh:
                    bd = json.load(fh)
                if bd.get("name") == baseline.get("name"):
                    baseline_path = str(f)
                    break
            except Exception:
                continue
        if baseline_path:
            break

    if not baseline_path:
        return [{"category": "competency-refs", "path": "competencies", "old": "invalid refs detected", "new": "cannot auto-fix: baseline file path unknown"}]

    result = subprocess.run(
        [sys.executable, str(script), str(file_path), baseline_path, "--fix", "--partial"],
        capture_output=True, text=True
    )

    fixes = []
    if result.returncode == 0:
        try:
            output = json.loads(result.stdout)
            name_map = output.get("nameMapping", {})
            level_map = output.get("levelMapping", {})
            deduped = output.get("deduplicated", 0)
            for old, new in name_map.items():
                fixes.append({"category": "competency-name", "path": "competencies", "old": old, "new": new})
            for old, new in level_map.items():
                fixes.append({"category": "competency-level", "path": "competencies", "old": old, "new": new})
            if deduped:
                fixes.append({"category": "competency-dedup", "path": "competencies", "old": f"{deduped} duplicates", "new": "removed"})
            unmapped_names = output.get("unmappedNames", [])
            unmapped_levels = output.get("unmappedLevels", [])
            for name in unmapped_names:
                fixes.append({"category": "competency-name-unmapped", "path": "competencies", "old": name, "new": f"UNMAPPED — use --map-name '{name}=ValidName'"})
            for level in unmapped_levels:
                fixes.append({"category": "competency-level-unmapped", "path": "competencies", "old": level, "new": f"UNMAPPED — use --map '{level}=ValidLevel'"})
            with open(file_path, "r") as f:
                reloaded = json.load(f)
            data.clear()
            data.update(reloaded)
        except json.JSONDecodeError:
            pass
    return fixes


def fix_nested_narratives(data):
    """Flatten narratives[i] wrappers that contain a 'narratives' sub-array."""
    fixes = []
    top_narratives = data.get("narratives", [])
    if not top_narratives:
        return fixes

    replacement = []
    top_citations = data.get("citations", [])
    top_citation_names = {c.get("name") for c in top_citations if c.get("name")}
    top_citation_urls = {}
    for c in top_citations:
        url = c.get("url")
        if url and c.get("name"):
            top_citation_urls[url] = c["name"]

    changed = False
    for i, item in enumerate(top_narratives):
        inner = item.get("narratives")
        if isinstance(inner, list):
            changed = True
            inner_citations = item.get("citations", [])
            for ic in inner_citations:
                ic_name = ic.get("name")
                if ic_name and ic_name not in top_citation_names:
                    ic_url = ic.get("url")
                    if ic_url and ic_url in top_citation_urls:
                        pass
                    else:
                        top_citations.append(ic)
                        top_citation_names.add(ic_name)
                        fixes.append({
                            "category": "nested-narrative",
                            "path": f"citations",
                            "old": None,
                            "new": f"merged inner citation '{ic_name}' to top-level",
                        })

            for j, narr in enumerate(inner):
                cn_list = narr.get("citationNames", [])
                remapped = []
                for cn in cn_list:
                    if cn in top_citation_names:
                        remapped.append(cn)
                    else:
                        matched = False
                        for ic in inner_citations:
                            if ic.get("name") == cn:
                                ic_url = ic.get("url")
                                if ic_url and ic_url in top_citation_urls:
                                    remapped.append(top_citation_urls[ic_url])
                                    fixes.append({
                                        "category": "nested-narrative",
                                        "path": f"narratives[{i}].narratives[{j}].citationNames",
                                        "old": cn,
                                        "new": top_citation_urls[ic_url],
                                    })
                                    matched = True
                                    break
                        if not matched:
                            remapped.append(cn)
                if remapped != cn_list:
                    narr["citationNames"] = remapped
                replacement.append(narr)
            fixes.append({
                "category": "nested-narrative",
                "path": f"narratives[{i}]",
                "old": f"wrapper with {len(inner)} inner narrative(s) and {len(inner_citations)} citation(s)",
                "new": f"flattened {len(inner)} narrative(s) to top level",
            })
        else:
            replacement.append(item)

    if changed:
        data["narratives"] = replacement
        if top_citations:
            data["citations"] = top_citations

    return fixes


def fix_versions(data):
    """Add missing version and schemaVersion."""
    fixes = []
    if not data.get("version"):
        data["version"] = "1.0.0"
        fixes.append({
            "category": "versioning",
            "path": "version",
            "old": None,
            "new": "1.0.0",
        })
    schema_ver = get_schema_version()
    if schema_ver and not data.get("schemaVersion"):
        data["schemaVersion"] = schema_ver
        fixes.append({
            "category": "versioning",
            "path": "schemaVersion",
            "old": None,
            "new": schema_ver,
        })
    return fixes


def fix_narrative_element_names(data, baseline):
    """Remap narrativeElementName values to match the baseline narrativeType's elements."""
    if not baseline:
        return []
    type_elements = {}
    for nt in baseline.get("narrativeTypes", []):
        elems = nt.get("narrativeElements", [])
        if elems:
            type_elements[nt["name"]] = [e["name"] for e in elems]

    if not type_elements:
        return []

    fixes = []

    def _walk(obj, path=""):
        if isinstance(obj, dict):
            ntn = obj.get("narrativeTypeName")
            contexts = obj.get("narrativeContexts")
            if ntn and ntn in type_elements and contexts:
                expected = type_elements[ntn]
                for ctx in contexts:
                    elem_name = ctx.get("narrativeElementName", "")
                    if elem_name and elem_name not in expected:
                        seq = ctx.get("seq")
                        if seq is not None and 1 <= seq <= len(expected):
                            new_name = expected[seq - 1]
                            ctx_path = f"{path}.narrativeContexts[seq={seq}]" if path else f"narrativeContexts[seq={seq}]"
                            fixes.append({
                                "category": "narrative-element-name",
                                "path": ctx_path,
                                "old": elem_name,
                                "new": new_name,
                            })
                            ctx["narrativeElementName"] = new_name
            for k, v in obj.items():
                _walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk(item, f"{path}[{i}]")

    _walk(data)
    return fixes


def main():
    parser = argparse.ArgumentParser(
        description="Auto-fix common practice/method/baseline JSON issues"
    )
    parser.add_argument("file", help="Practice, method, or baseline JSON file")
    parser.add_argument("baseline", nargs="?", default=None,
                        help="Baseline JSON file (optional, enables focusName correction)")
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
        "--fix-gherkin", action="store_true",
        help="Fix Gherkin structure issues (background/test/examples type and placement)"
    )
    parser.add_argument(
        "--fix-narrative-placement", action="store_true",
        help="Move top-level narratives to matching element's narratives[] array"
    )
    parser.add_argument(
        "--fix-pattern-completeness", action="store_true",
        help="Ensure final view completeness and compress unchanged carry-forward states"
    )
    parser.add_argument(
        "--compress-patterns", action="store_true",
        help="Remove unchanged carry-forward alpha states from non-final pattern views"
    )
    parser.add_argument(
        "--fix-alias-isolation", action="store_true",
        help="Replace alias names in structural references with canonical names"
    )
    parser.add_argument(
        "--fix-mapsto-naming", action="store_true",
        help="Strip parent type name from mapsTo variant alpha names"
    )
    parser.add_argument(
        "--fix-narrative-schema", action="store_true",
        help="Fix invalid kind='narrative' and wrong narrativeContext field names"
    )
    parser.add_argument(
        "--fix-missing-assets", action="store_true",
        help="Auto-create asset definitions for unresolved assetNames references"
    )
    parser.add_argument(
        "--fix-self-ref-backgrounds", action="store_true",
        help="Remove background alphaStates that reference the same alpha the state belongs to"
    )
    parser.add_argument(
        "--fix-unknown-activity-spaces", action="store_true",
        help="Replace unknown activitySpaceNames with closest baseline match (requires baseline arg)"
    )
    parser.add_argument(
        "--fix-narrative-types", action="store_true",
        help="Replace invalid narrativeTypeName values with closest baseline match (requires baseline arg)"
    )
    parser.add_argument(
        "--fix-competency-refs", action="store_true",
        help="Fix invalid competency names and levels via fix-competency-levels.py (requires baseline arg)"
    )
    parser.add_argument(
        "--fix-nested-narratives", action="store_true",
        help="Flatten nested narrative wrappers (narratives[i].narratives[]) into top-level"
    )
    parser.add_argument(
        "--fix-versions", action="store_true",
        help="Add missing version (1.0.0) and schemaVersion (from schema)"
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

    baseline = None
    if args.baseline:
        baseline, b_err = load_json_pair(Path(args.baseline))
        if b_err:
            print(json.dumps({"error": f"baseline: {b_err}"}))
            sys.exit(1)

    all_fixes = []

    all_fixes.extend(fix_kind(data))
    all_fixes.extend(fix_element_kind(data))
    all_fixes.extend(fix_method_properties(data))
    all_fixes.extend(fix_narratives(data))
    all_fixes.extend(fix_citations(data))
    all_fixes.extend(fix_contributes_to(data))
    all_fixes.extend(fix_narrative_citations(data))
    all_fixes.extend(fix_relates_to_rationale(data))
    all_fixes.extend(fix_focus_names(data, baseline))

    if args.fix_truncated_names or args.all:
        all_fixes.extend(fix_truncated_names(data))

    if args.normalize_relationships or args.all:
        all_fixes.extend(fix_relationship_types(data))

    if args.fix_schema or args.all:
        all_fixes.extend(fix_tags_structure(data))
        all_fixes.extend(fix_persona_groups(data))
        all_fixes.extend(fix_persona_properties(data))
        all_fixes.extend(fix_activity_technique_narratives(data))
        all_fixes.extend(fix_relates_to_direction(data))

    if args.fix_contributesto_arrays or args.all:
        all_fixes.extend(fix_contributesto_arrays(data))

    if args.fix_gherkin or args.all:
        all_fixes.extend(fix_gherkin_structure(data))

    if args.fix_narrative_placement or args.all:
        all_fixes.extend(fix_narrative_placement(data))

    if args.fix_pattern_completeness or args.all:
        all_fixes.extend(fix_pattern_completeness(data))

    if args.compress_patterns or args.all:
        all_fixes.extend(compress_pattern_states(data))

    if args.fix_alias_isolation or args.all:
        all_fixes.extend(fix_alias_isolation(data))

    if args.fix_mapsto_naming or args.all:
        all_fixes.extend(fix_mapsto_naming(data, baseline))

    if args.fix_narrative_schema or args.all:
        all_fixes.extend(fix_narrative_schema(data))

    if args.fix_missing_assets or args.all:
        all_fixes.extend(fix_missing_assets(data))

    if args.fix_self_ref_backgrounds or args.all:
        all_fixes.extend(fix_self_ref_backgrounds(data))

    if args.fix_unknown_activity_spaces or args.all:
        all_fixes.extend(fix_unknown_activity_spaces(data, baseline))

    if args.fix_nested_narratives or args.all:
        all_fixes.extend(fix_nested_narratives(data))

    if args.fix_narrative_types or args.all:
        nt_fixes = fix_narrative_types(data, baseline)
        all_fixes.extend(nt_fixes)
        if nt_fixes:
            all_fixes.extend(fix_narrative_element_names(data, baseline))

    if args.fix_competency_refs or args.all:
        all_fixes.extend(fix_competency_refs(data, baseline, file_path))

    if args.fix_versions or args.all:
        all_fixes.extend(fix_versions(data))

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
