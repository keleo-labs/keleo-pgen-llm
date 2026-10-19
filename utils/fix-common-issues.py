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
- Invalid kind values (remove `kind` from states, checklists, levels of detail and
  narratives, which the schema's PracticeElement enum does not admit; schema-driven)
- Alias isolation (replace alias names in structural references with canonical names)
- mapsTo variant naming (strip parent type name from variant alpha names and update refs)
- Narrative schema (remove invalid kind='narrative', fix narrativeContext field names)
- Self-referencing backgrounds (remove alphaStates entries that reference the owning alpha)
- Unknown activity spaces (replace invalid activitySpaceNames with closest baseline match)
- Invalid narrative types (replace narrativeTypeName values not in baseline with closest match)
- Invalid competency refs (fix competency names and levels not in baseline, with deduplication)
- Nested narrative wrappers (flatten narratives[i].narratives[] into top-level, merge citations)
- Missing checklist seq (add sequential seq values to items that lack them)
- Missing version/schemaVersion (add version 1.0.0 and schemaVersion from schema)
- Reference evidence links (copy a reference's links onto evidenceBy rows carrying none)

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
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import (load_json, load_json_pair, get_schema_version,
                           resolve_reference_context, merge_ancestor_baselines)


STANDARD_RELATIONSHIP_TYPES = {"produces", "governed by", "uses"}

RELATIONSHIP_NORMALIZATIONS = {
    # REMOVED: the active enabling verbs that used to map to "produces" —
    # "supports", "enables", "enables delivery of", "provides", "enhances",
    # "strengthens", "drives". Three things were wrong with them.
    #
    # First, semantics/alphas.md §6 lists "enables" and "provides" among the
    # valid domain verbs and says outright that the relationship string "is the
    # human-readable label; tooling should not parse this string
    # programmatically" — which is precisely what this table does.
    #
    # Second, it rewrote the verb and left `relationshipKind` alone, so the two
    # disagreed. The spec maps kind `enabling` to exactly "enables",
    # "facilitates", "supports"; `produces` belongs to kind `production`. 16
    # documents in this corpus now carry `relationship: produces` beside
    # `relationshipKind: enabling`, which this table created.
    #
    # Third, "A enables B" and "A produces B" are different claims. One
    # practice caught it on "the value case produces the deal", which it does
    # not — it enables it.
    #
    # The passive-to-canonical entries below stay: they regularise voice
    # without changing the claim or contradicting the declared kind.
    "strengthened by": "uses",
    # NOTE: active governance verbs ("governs", "constrains", "protects") are
    # deliberately NOT normalised. Per references/semantics/alphas.md the verb
    # reads from the declaring alpha, so rewriting "A governs B" to "A governed
    # by B" inverts the meaning, and flipping direction to match only makes the
    # inversion internally consistent. The canonical set has no active
    # governance verb, so these are left as authored.
    "protected by": "governed by",
    "managed by": "governed by",
    "constrained by": "governed by",
    "guided by": "governed by",
    "aligned with": "governed by",
    # "requires" and "coordinates with" are gone for the same reason as the
    # enabling verbs above: both are *active* verbs being genericised, and both
    # cross a kind boundary doing it. "requires" is a dependency; "uses" is
    # consumption. "coordinates with" is mutual. The entries below are all
    # passive forms being put into a consistent voice, which changes no claim.
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


def _schema_kind_enum(schema_path=None):
    """Read the PracticeElement kind enum from the schema.

    Returns a set of permitted values, or None when the schema cannot be read —
    in which case the caller must do nothing rather than guess, since removing a
    valid kind is worse than leaving an invalid one for the validator to report.
    """
    if schema_path is None:
        schema_path = (Path(__file__).resolve().parent.parent
                       / "deps" / "language.schema.json")
    try:
        schema = load_json(Path(schema_path), exit_on_error=False)
    except Exception:
        return None
    if not isinstance(schema, dict):
        return None
    element = schema.get("$defs", {}).get("PracticeElement", {})
    values = element.get("properties", {}).get("kind", {}).get("enum")
    if isinstance(values, list) and values:
        return set(values)
    return None


def fix_invalid_kind(data, schema_path=None):
    """Remove `kind` values the schema's PracticeElement enum does not admit.

    `kind` is optional and only a handful of element types carry it. States,
    checklists, levels of detail and narratives do not, so a generating agent
    that stamps `kind` uniformly produces one hard schema error per element —
    several hundred on a full practice. The value is dropped rather than
    corrected because there is no correct value to put there: the enum has no
    member for these types.

    Schema-driven rather than hardcoded, so the enum growing does not turn a
    newly valid kind into a deletion.
    """
    permitted = _schema_kind_enum(schema_path)
    if not permitted:
        return []

    fixes = []

    def walk(node, path):
        if isinstance(node, dict):
            kind = node.get("kind")
            if isinstance(kind, str) and kind not in permitted:
                del node["kind"]
                fixes.append({
                    "category": "invalid-kind",
                    "path": f"{path}.kind" if path else "kind",
                    "old": kind,
                    "new": "kind removed",
                    "reason": "not a member of the schema's PracticeElement kind enum",
                })
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}.{i}")

    walk(data, "")
    return fixes


def fix_reference_evidence_links(data):
    """Give an evidenceBy entry the links of the reference that carries it.

    `assess-practice.py` reports `reference-evidence` for an evidenceBy row with
    no links, on the ground that evidence nobody can open is not evidence. The
    row describes what a practitioner produces from the reference, so the
    reference's own links are the honest source to point at — copying them is a
    transcription, not an invention, and it is what the shipped Account Planning
    references already do by hand.

    All of the reference's links are copied rather than the first, because a
    reference carrying two names two documents and guessing which one the
    evidence came from is the only way this fixer could be wrong.
    """
    fixes = []
    sources = [data] + data.get("practices", [])
    for source in sources:
        for ri, ref in enumerate(source.get("references", [])):
            parent_links = ref.get("links") or []
            if not parent_links:
                continue
            for ei, evidence in enumerate(ref.get("evidenceBy", [])):
                if evidence.get("links"):
                    continue
                evidence["links"] = [dict(link) for link in parent_links]
                fixes.append({
                    "category": "reference-evidence-links",
                    "path": f"references.{ri}.evidenceBy.{ei}.links",
                    "old": None,
                    "new": f"{len(parent_links)} link(s) copied from "
                           f"reference '{ref.get('name', f'[{ri}]')}'",
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


# `authors`, `createdAt`, `updatedAt` and `keywords` were once stripped from
# method-kind documents as invalid. They are all declared on the Method shape in
# language.schema.json 3.1.0, so stripping them silently deleted valid authored
# content. Nothing replaces the fixer: the schema validator is what rejects a
# property a shape does not admit.


def fix_focus_names(data, baseline=None, apply=True):
    """Correct focusName on sub-alphas to match their contributesTo parent's focus.

    Only where the declared focus does not exist. A focus that *is* declared in
    the chain but differs from the parent's is a choice, not a defect — a
    mapsTo variant can legitimately sit in a different focus from its parent,
    and three documents in this run argued exactly that from their sources.

    This fixer runs unconditionally, so until now there was no way to decline
    it: one practice reverted a sourced focus twice and it was re-applied both
    times. Where the focus resolves, the mismatch is now *reported* and left
    alone, so a human sees it without the document being rewritten under them.
    """
    fixes = []
    if not baseline:
        return fixes

    known_focuses = {f.get("name") for f in baseline.get("focuses", []) or []
                     if isinstance(f, dict)}
    known_focuses |= {f.get("name") for f in data.get("focuses", []) or []
                      if isinstance(f, dict)}

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
        if current_focus == expected_focus:
            continue

        if current_focus and current_focus in known_focuses:
            fixes.append({
                "category": "focus-name-differs",
                "path": f"alphas[{alpha['name']}].focusName",
                "old": current_focus,
                "new": current_focus,
                "reason": (
                    f"left alone — '{current_focus}' is a declared focus, so this "
                    f"is an authoring choice, not an error. Parent '{parent}' sits "
                    f"in '{expected_focus}'; change it only if the source says so"
                ),
            })
            continue

        alpha["focusName"] = expected_focus
        fixes.append({
            "category": "focus-name",
            "path": f"alphas[{alpha['name']}].focusName",
            "old": current_focus,
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


_MARKUP_KEYS = (
    "description", "context", "howToUse", "measureDescription", "rationale",
    "given", "when", "then", "note", "content", "summary",
)

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC_RE = re.compile(r"(?<![\*\w])\*(?!\s)([^\*\n]+?)(?<!\s)\*(?![\*\w])")
_CODE_RE = re.compile(r"`([^`\n]+)`")


def _strip_markup(text):
    """Remove Markdown emphasis and code spans from a prose string.

    Phase 3 agents transcribe prose out of a Markdown mapping guide, and the
    guide's ``**bold**``, ``*italic*`` and ``` `code` ``` markers travel into
    JSON string values where nothing renders them. Consumers show the literal
    asterisks and backticks, so they are authoring residue rather than content.
    """
    new = _BOLD_RE.sub(r"\1", text)
    new = _ITALIC_RE.sub(r"\1", new)
    new = _CODE_RE.sub(r"\1", new)
    return new


def fix_prose_markup(data):
    """Strip Markdown emphasis and code spans from prose-bearing fields."""
    fixes = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                here = f"{path}.{key}" if path else key
                if key in _MARKUP_KEYS and isinstance(value, str):
                    new = _strip_markup(value)
                    if new != value:
                        node[key] = new
                        fixes.append({
                            "category": "prose-markup",
                            "path": here,
                            "old": value,
                            "new": new,
                        })
                elif key in _MARKUP_KEYS and isinstance(value, list):
                    for idx, item in enumerate(value):
                        if not isinstance(item, str):
                            continue
                        new = _strip_markup(item)
                        if new != item:
                            value[idx] = new
                            fixes.append({
                                "category": "prose-markup",
                                "path": f"{here}[{idx}]",
                                "old": item,
                                "new": new,
                            })
                else:
                    walk(value, here)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{path}[{idx}]")

    walk(data, "")
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
    """Move top-level narratives to matching element's narratives[] array.

    Ownership is read off the narrative's **name**, not its description. A
    narrative that belongs to an alpha is named for it; a narrative that merely
    *mentions* an alpha is usually the document's own practice narrative, whose
    home is `Practice.narratives` and whose subject is, naturally, the practice's
    primary concern. Matching on description moved a practice narrative called
    "Practice Intent" onto an alpha because its one-line summary contained the
    alpha's name — the move validated, so nothing downstream reported it.

    A description-only match is still evidence of something, so it is reported
    as a skip rather than discarded, in the same shape as the mapsTo naming
    guard: a human can act on a reported skip and cannot act on a silent one.
    """
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
        moved = False
        for elem_name_lower in sorted_names:
            if elem_name_lower in narr_name:
                coll_key, elem = element_map[elem_name_lower]
                elem.setdefault("narratives", []).append(narrative)
                to_remove.append(i)
                fixes.append({
                    "category": "narrative-placement",
                    "path": f"narratives[{i}]",
                    "old": f"top-level narrative '{narrative.get('name', '')}'",
                    "new": f"moved to {coll_key}['{elem.get('name', '')}'].narratives",
                })
                moved = True
                break
        if moved:
            continue
        for elem_name_lower in sorted_names:
            if elem_name_lower in narr_desc:
                coll_key, elem = element_map[elem_name_lower]
                fixes.append({
                    "category": "narrative-placement-skipped",
                    "path": f"narratives[{i}]",
                    "old": f"top-level narrative '{narrative.get('name', '')}'",
                    "new": (f"left in place — only its description mentions "
                            f"{coll_key}['{elem.get('name', '')}'], which is what a "
                            f"practice narrative about that concern looks like"),
                })
                break

    for idx in reversed(to_remove):
        data["narratives"].pop(idx)

    if data.get("narratives") == []:
        del data["narratives"]

    return fixes


def _canonical_state_order(data, file_path=None):
    """{alphaName: [stateName, ...]} from the document and its effective context.

    The context is picked up from the practice directory the way
    `assess-practice.py` does, because a pattern routinely places states of an
    alpha it inherits rather than declares, and without the merge those states
    have no known order.
    """
    order = {}

    def absorb(doc):
        if not isinstance(doc, dict):
            return
        for source in [doc] + [p for p in doc.get("practices", []) if isinstance(p, dict)]:
            for alpha in source.get("alphas", []) or []:
                name = alpha.get("name")
                states = [s.get("name") for s in alpha.get("states", []) or []
                          if s.get("name")]
                if name and states and name not in order:
                    order[name] = states

    absorb(data)
    if file_path:
        context = Path(file_path).parent / "_effective-context.json"
        if context.is_file():
            try:
                with open(context, encoding="utf-8") as fh:
                    absorb(json.load(fh))
            except (OSError, json.JSONDecodeError):
                pass
    return order


def fix_ambiguous_pattern_views(data, state_order=None, collapse=False):
    """One alpha, one state per pattern view.

    Two entries for the same alpha in one view is a schema error the validator
    reports and the assessment never checked, so 57 of them accumulated across
    11 documents. It also makes the walk across views appear to move backwards,
    so the ambiguity gets reported as an ordering defect and the real one is
    never addressed.

    An exact repeat is dropped outright: it says nothing the single entry does
    not. Two *different* states are only collapsed when asked, because the
    prescribed fix is to split the view into sub-views (Pass 4 Constraint 1),
    which needs names, activities and narrative context that no rule supplies.
    Where collapsing is chosen, the later state in the alpha's canonical order
    is kept: a view declares what holds at that point in the lifecycle, which
    is where the phase ends, and passing through the earlier state is implied.
    """
    state_order = state_order or {}
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(p for p in data.get("practices", []) if isinstance(p, dict))

    for source in sources:
        for pi, pattern in enumerate(source.get("patterns", [])):
            pat_name = pattern.get("name", f"pattern[{pi}]")
            for view in pattern.get("patternViews", []) or []:
                view_seq = view.get("seq", "?")
                entries = view.get("alphaStates", []) or []
                by_alpha = {}
                for entry in entries:
                    by_alpha.setdefault(entry.get("alphaName", ""), []).append(entry)

                drop = []
                for alpha, group in by_alpha.items():
                    if len(group) < 2:
                        continue
                    states = [e.get("stateName", "") for e in group]
                    distinct = list(dict.fromkeys(states))

                    if len(distinct) == 1:
                        drop.extend(group[1:])
                        fixes.append({
                            "category": "pattern-view-ambiguity",
                            "path": f"patterns['{pat_name}'].patternViews[{view_seq}]",
                            "old": f"'{alpha}' declared {len(group)} times at '{distinct[0]}'",
                            "new": "duplicate entries removed",
                        })
                        continue

                    order = state_order.get(alpha, [])
                    unknown = [s for s in distinct if s not in order]
                    if not collapse or unknown:
                        fixes.append({
                            "category": "pattern-view-ambiguity",
                            "path": f"patterns['{pat_name}'].patternViews[{view_seq}]",
                            "old": f"'{alpha}' targets {len(distinct)} states: "
                                   f"{', '.join(distinct)}",
                            "new": ("not changed — state order unknown, cannot tell "
                                    "which the view ends at"
                                    if unknown else
                                    "not changed — split the view into sub-views, or "
                                    "pass --collapse-ambiguous-views to keep the last"),
                            "applied": False,
                        })
                        continue

                    keep = max(distinct, key=order.index)
                    drop.extend(e for e in group if e.get("stateName") != keep)
                    # A repeat of the kept state would otherwise survive twice.
                    kept_seen = False
                    for entry in group:
                        if entry.get("stateName") == keep:
                            if kept_seen:
                                drop.append(entry)
                            kept_seen = True
                    fixes.append({
                        "category": "pattern-view-ambiguity",
                        "path": f"patterns['{pat_name}'].patternViews[{view_seq}]",
                        "old": f"'{alpha}' targets {len(distinct)} states: "
                               f"{', '.join(distinct)}",
                        "new": f"collapsed to '{keep}' (the state the view ends at)",
                    })

                if drop:
                    dropped = {id(e) for e in drop}
                    view["alphaStates"] = [e for e in entries if id(e) not in dropped]

    return fixes


def _raise_understated_final_states(views_sorted, final_view, pat_name,
                                    view_seq, state_order):
    """Lift a final-view state that sits below the one the pattern reached."""
    fixes = []
    highest = {}
    for view in views_sorted[:-1]:
        for astate in view.get("alphaStates", []) or []:
            alpha, state = astate.get("alphaName"), astate.get("stateName")
            order = state_order.get(alpha, [])
            if not alpha or state not in order:
                continue
            idx = order.index(state)
            if alpha not in highest or idx > highest[alpha][0]:
                highest[alpha] = (idx, state)

    for astate in final_view.get("alphaStates", []) or []:
        alpha, state = astate.get("alphaName"), astate.get("stateName")
        order = state_order.get(alpha, [])
        if not alpha or state not in order or alpha not in highest:
            continue
        if order.index(state) < highest[alpha][0]:
            astate["stateName"] = highest[alpha][1]
            fixes.append({
                "category": "pattern-completeness",
                "path": f"patterns['{pat_name}'].patternViews[{view_seq}]",
                "old": f"final view restates '{alpha}' at '{state}'",
                "new": f"raised to '{highest[alpha][1]}', the state the pattern reached",
            })
    return fixes


def fix_pattern_completeness(data, state_order=None):
    """Restate each pattern's own alphas in its final view, then compress.

    The final view is a complete end-state snapshot of **the alphas this
    pattern carries** — the ones whose state it actually changes. It is not a
    roll-call of the practice.

    Taking the roll-call reading is what fills closing views with alphas
    belonging to a different pattern, at whichever state came to hand: with no
    appearance anywhere in the pattern there is no state to carry forward, so
    the only candidate is the alpha's first. A pattern that ends by announcing
    three alphas at their opening states is reporting the fixer, not the
    methodology. So an alpha the pattern never advanced is skipped here, per
    `semantics/execution-and-patterns.md` §9.2 rule 1 and the Participation
    Rule in `references/pattern-completeness.md`.
    """
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for source in sources:
        for pi, pattern in enumerate(source.get("patterns", [])):
            pat_name = pattern.get("name", f"pattern[{pi}]")
            views = pattern.get("patternViews", [])
            views_sorted = sorted(views, key=lambda v: v.get("seq", 0))
            loops = any(v.get("loopsBackTo") for v in views_sorted)

            # Pass 1: Restate carried alphas missing from the final view
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
                    # last_state holds exactly the alphas some view advanced,
                    # which is the set the pattern carries.
                    missing = set(last_state) - view_alphas
                    for aname in sorted(missing):
                        carry = last_state.get(aname, "")
                        if not aname or not carry:
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

                    # A closing view that restates an alpha *below* where the
                    # pattern already took it reads as the lifecycle going
                    # backwards, and is the same mistake as omitting it: the
                    # snapshot has to show the end state. Inside a loop the
                    # lower state is a per-pass minimum, so patterns that
                    # declare one are left alone.
                    if not loops and state_order:
                        fixes.extend(_raise_understated_final_states(
                            views_sorted, view, pat_name, view_seq, state_order))

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


def restore_loop_span_states(data):
    """Re-add held alpha states pruned from inside a `loopsBackTo` span.

    The inverse of the compression above, for documents compressed before the
    span was declared — or by a compressor that did not yet know about one.
    Within a span, an alpha carried by the previous view and absent from this
    one was pruned as a held state, so its previous state is restored. Only
    alphas the pattern already carries are touched: nothing new is introduced,
    and an alpha that genuinely enters later still enters later.
    """
    fixes = []
    sources = [data]
    if "practices" in data:
        sources.extend(data.get("practices", []))

    for src in sources:
        for pattern in src.get("patterns", []):
            pat_name = pattern.get("name", "?")
            views = pattern.get("patternViews", [])
            if not views:
                continue
            views_sorted = sorted(views, key=lambda v: v.get("seq", 0))
            in_loop = loop_span_indices(views_sorted)
            if not in_loop:
                continue

            prev_states = {}
            for vi, view in enumerate(views_sorted):
                alpha_states = view.setdefault("alphaStates", [])
                present = {a.get("alphaName", "") for a in alpha_states}

                if vi in in_loop:
                    for aname, sname in sorted(prev_states.items()):
                        if aname in present:
                            continue
                        alpha_states.append(
                            {"alphaName": aname, "stateName": sname}
                        )
                        fixes.append({
                            "category": "loop-span-restore",
                            "path": (
                                f"patterns['{pat_name}']"
                                f".patternViews[{view.get('seq', '?')}]"
                            ),
                            "old": f"'{aname}' absent inside loop span",
                            "new": f"restored held state '{sname}'",
                        })

                for astate in alpha_states:
                    prev_states[astate.get("alphaName", "")] = astate.get("stateName", "")

    return fixes


def loop_span_indices(views_sorted):
    """Indices of views sitting inside a `loopsBackTo` span.

    A view declaring `loopsBackTo` closes a cycle back to a named earlier view;
    every view from that target through the declaring one is re-entered on each
    lap. `pattern-completeness.md` suspends Sequential View Pruning across that
    span: a re-entered view emptied of its held states hides what the iteration
    actually works on, and the states are the minimum that must hold on that
    pass rather than a progression the reader can infer from the previous view.
    """
    by_name = {v.get("name", ""): i for i, v in enumerate(views_sorted)}
    inside = set()

    for i, view in enumerate(views_sorted):
        loops = view.get("loopsBackTo")
        if not isinstance(loops, dict):
            continue
        target = by_name.get(loops.get("patternViewName", ""))
        if target is None or target > i:
            continue  # unresolvable or forward-pointing: not a span we trust
        inside.update(range(target, i + 1))

    return inside


def compress_pattern_states_for_pattern(pattern, pat_name, views_sorted):
    """Remove unchanged carry-forward alpha states from non-final views,
    then remove empty non-final views (merging activities into the next view).

    Views inside a `loopsBackTo` span are left alone — see loop_span_indices.
    """
    fixes = []
    prev_states = {}
    in_loop = loop_span_indices(views_sorted)

    for vi, view in enumerate(views_sorted):
        is_final = (vi == len(views_sorted) - 1)
        view_seq = view.get("seq", "?")
        alpha_states = view.get("alphaStates", [])

        if is_final:
            for astate in alpha_states:
                prev_states[astate.get("alphaName", "")] = astate.get("stateName", "")
            continue

        if vi in in_loop:
            # Carry the states forward for later views to compare against, but
            # remove nothing: this view is re-entered on every lap.
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

    # Remove empty non-final views, merging activities into next view.
    # A view inside a loop span is never removed: it is re-entered each lap, and
    # a loop edge naming a view that no longer exists is worse than an empty one.
    to_remove = []
    for vi in range(len(views_sorted) - 1):
        view = views_sorted[vi]
        if vi in in_loop:
            continue
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


def _element_names(data):
    """Every declared element name in a document, for collision testing."""
    names = set()
    for key in ("alphas", "workProducts", "activities", "patterns", "personas",
                "personaGroups", "activitySpaces", "competencies", "narrativeTypes"):
        for item in data.get(key, []) or []:
            if isinstance(item, dict) and item.get("name"):
                names.add(item["name"])
    return names


def _residue_is_a_name(residue, owner_name, data, baseline):
    """Is the leftover of a mapsTo strip still the name of a thing?

    Stripping the parent type is right when what remains still names something
    — `OpenShift Virtualization Platform` mapsTo `Platform` leaves `OpenShift
    Virtualization`, which is a thing. It is wrong when what remains is the bare
    domain qualifier: `Virtualization Competitive Position` mapsTo `Competitive
    Position` left `Virtualization`, a meaningless element name, and the rename
    was propagated across fourteen references before anyone looked.

    Three mechanical tests, all of which must pass:

    1. The residue must not already be some other element's name. A rename onto
       an occupied name is a collision, not a tidy-up.
    2. The residue must not be the name of the document that declares the alpha
       (or of its baseline, or of a member practice). `IT Operations Efficiency
       Sales Play` mapsTo `Sales Play` strips to `IT Operations Efficiency`,
       which is the practice's own name: every reference to it would then read
       ambiguously as the practice or the alpha. A residue equal to the
       document's subject is the domain word by definition.
    3. The residue must not be the prefix of **any** other element name in the
       same document. A string used to qualify another element is this
       document's domain word, not a name available to one of them.

    The threshold on test 2 was originally two, and that was one too high:
    `Application Platform Competitive Position` strips to `Application Platform`,
    which prefixes exactly one other name (`Application Platform TDP`), so the
    rename went through and rewrote eleven references. Virtualization was spared
    only by happening to have six qualifier matches.

    One is the right threshold because the two failure modes are not
    symmetric. Refusing a legitimate strip leaves a slightly redundant name and
    a reported skip a human can act on; allowing a wrong one destroys an element
    name and rewrites every reference to it. Prefer refusing.
    """
    if not residue:
        return False, "stripping the parent name leaves nothing"

    taken = _element_names(data) | (_element_names(baseline) if baseline else set())
    taken.discard(owner_name)
    if residue in taken:
        return False, f"'{residue}' is already another element's name"

    document_names = {data.get("name", "")}
    for member in data.get("practices", []) or []:
        if isinstance(member, dict):
            document_names.add(member.get("name", ""))
    if baseline:
        document_names.add(baseline.get("name", ""))
    document_names.discard("")
    if residue in document_names:
        return False, (
            f"'{residue}' is the name of the document that declares this alpha, "
            f"so it names the subject of the whole practice, not one element inside it"
        )

    prefixed = [n for n in taken if n != residue and n.startswith(residue + " ")]
    if prefixed:
        noun = "name" if len(prefixed) == 1 else "names"
        return False, (
            f"'{residue}' is the qualifier on {len(prefixed)} other element {noun} "
            f"(e.g. {', '.join(sorted(prefixed)[:2])}), so it names the domain, "
            f"not this alpha"
        )
    return True, ""


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

        ok, why = _residue_is_a_name(new_name, alpha_name, data, baseline)
        if not ok:
            fixes.append({
                "category": "mapsto-naming-skipped",
                "path": f"alphas['{alpha_name}'].name",
                "old": alpha_name,
                "new": alpha_name,
                "note": f"left alone — {why}",
            })
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
    """Replace unknown activitySpaceNames with the closest valid match.

    `baseline` should be the merged vocabulary from `resolve_reference_context`,
    not the leaf baseline: activity spaces are inherited down the chain, and
    checking against the leaf alone treats valid inherited references as
    unknown.

    Only rewrites on a confident keyword match (two or more shared words).
    Anything it cannot resolve is left for the validator to report.
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
            # No confident match. Leave the reference alone: the previous
            # fallbacks picked any space containing "execute"/"play"/"sell",
            # then the alphabetically first one, which silently rewrote valid
            # references to an unrelated space. A reference this tool cannot
            # resolve is for the validator to report, not for it to guess at.
            continue
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


def fix_competency_refs(data, baseline, file_path, apply=False):
    """Fix invalid competency names and levels by delegating to fix-competency-levels.py.

    ``apply`` must mirror the caller's ``--fix``. This fixer is the only one that
    reaches the file through a subprocess rather than by mutating ``data``, and
    the subprocess writes on its own authority — so passing ``--fix`` to it
    unconditionally made a *dry run* rewrite the document on disk while
    reporting ``"mode": "dry-run"``. Verified against a planted invalid
    reference: the file's hash changed under a dry run.
    """
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

    # Hand the subprocess the vocabulary this process already resolved, not a
    # baseline file it has to re-read. Finding the baseline on disk by name
    # threw away every competency the ancestors and dependencies contribute,
    # and the subprocess then "corrected" each unseen name onto its nearest
    # match in the leaf. On one partner practice with three parents that was
    # nine rewrites — `Value Articulation` → `Ecosystem Operations` and the
    # like — all eight of the affected names being perfectly resolvable. Same
    # class as the baseline chain-walk defect, reached through a subprocess
    # boundary rather than a missing property.
    vocab_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(baseline, vocab_file, ensure_ascii=False)
    vocab_file.close()

    cmd = [sys.executable, str(script), str(file_path), vocab_file.name, "--partial"]
    if apply:
        cmd.append("--fix")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        os.unlink(vocab_file.name)

    fixes = []
    # Parse stdout whatever the exit code: fix-competency-levels.py reports its
    # findings as JSON and uses a non-zero exit to mean "issues found", which in
    # a dry run is the normal and expected outcome, not a failure.
    if result.stdout.strip():
        try:
            output = json.loads(result.stdout)
            # Two output shapes. With --fix the tool reports what it did as
            # nameMapping/levelMapping; without it, what it *would* do as
            # invalidNames/invalidLevels carrying a suggestedMapping. Reading
            # only the first made the dry run silent about real findings.
            name_map = dict(output.get("nameMapping", {}))
            level_map = dict(output.get("levelMapping", {}))
            for bad, detail in (output.get("invalidNames") or {}).items():
                suggested = (detail or {}).get("suggestedMapping")
                if suggested and bad not in name_map:
                    name_map[bad] = suggested
            for bad, detail in (output.get("invalidLevels") or {}).items():
                suggested = (detail or {}).get("suggestedMapping")
                if suggested and bad not in level_map:
                    level_map[bad] = suggested
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
            if apply:
                with open(file_path, "r") as f:
                    reloaded = json.load(f)
                data.clear()
                data.update(reloaded)
        except json.JSONDecodeError:
            # Never swallow this. The subprocess may already have written the
            # file, so returning an empty fix list reports "nothing changed"
            # about a document that changed — the single worst thing a fixer
            # can say. One agent only caught it by grepping the output for
            # names it had authored.
            fixes.append({
                "category": "competency-refs-unreported",
                "path": "competencies",
                "old": "fix-competency-levels.py output was not JSON",
                "new": ("changes may have been applied and are NOT itemised above — "
                        "diff the file before trusting this report"),
            })
    elif result.returncode != 0:
        fixes.append({
            "category": "competency-refs-failed",
            "path": "competencies",
            "old": f"fix-competency-levels.py exited {result.returncode} with no output",
            "new": (result.stderr or "").strip()[:200] or "no stderr",
        })
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


def fix_missing_seq(data):
    """Add sequential seq values to checklist items missing them."""
    fixes = []
    containers = [
        ("alphas", "states"),
        ("workProducts", "levelsOfDetail"),
    ]
    for collection_key, sub_key in containers:
        for elem in data.get(collection_key, []):
            for sub in elem.get(sub_key, []):
                checklist = sub.get("checklist", [])
                if not checklist:
                    continue
                missing = [cl for cl in checklist if "seq" not in cl]
                if not missing:
                    continue
                for i, cl in enumerate(checklist, 1):
                    if "seq" not in cl:
                        cl["seq"] = i
                        fixes.append({
                            "category": "missing-seq",
                            "path": f"{collection_key}.{elem['name']}.{sub_key}.{sub['name']}.checklist.{cl['name']}",
                            "old": None,
                            "new": i,
                        })
    for act in data.get("activities", []):
        checklist = act.get("checklist", [])
        if not checklist:
            continue
        missing = [cl for cl in checklist if "seq" not in cl]
        if not missing:
            continue
        for i, cl in enumerate(checklist, 1):
            if "seq" not in cl:
                cl["seq"] = i
                fixes.append({
                    "category": "missing-seq",
                    "path": f"activities.{act['name']}.checklist.{cl['name']}",
                    "old": None,
                    "new": i,
                })
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
    parser.add_argument("--parent", action="append", default=[], metavar="JSON",
                        help="A practice this document depends on, whose declarations "
                             "are part of the vocabulary it resolves against. Repeatable, "
                             "one per practiceDependencyNames entry. Without it the "
                             "competency fixer renames against the baseline alone and "
                             "'corrects' every name a dependency supplies.")
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
        help=(
            "Remove unchanged carry-forward alpha states from non-final pattern "
            "views. Views inside a loopsBackTo span are skipped — pruning is "
            "suspended there (pattern-completeness.md, Cyclical Patterns)"
        )
    )
    parser.add_argument(
        "--restore-loop-states", action="store_true",
        help=(
            "Re-add held alpha states pruned from inside a loopsBackTo span. "
            "For documents compressed before the span was declared. Runs before "
            "--compress-patterns so the two do not fight"
        )
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
        "--fix-missing-seq", action="store_true",
        help="Add sequential seq values to checklist items that are missing them"
    )
    parser.add_argument(
        "--fix-versions", action="store_true",
        help="Add missing version (1.0.0) and schemaVersion (from schema)"
    )
    parser.add_argument(
        "--fix-ambiguous-views", action="store_true",
        help="Drop repeated alphaStates entries from a pattern view. Two "
             "different states for one alpha are reported, not changed — the "
             "prescribed fix is to split the view into sub-views"
    )
    parser.add_argument(
        "--collapse-ambiguous-views", action="store_true",
        help="Also resolve two different states for one alpha by keeping the "
             "later one in the alpha's canonical order — the state the view "
             "ends at. Lossless as to ordering, but loses the hint that the "
             "phase did two steps of work; splitting into sub-views keeps it"
    )
    parser.add_argument(
        "--fix-prose-markup", action="store_true",
        help="Strip Markdown emphasis (**bold**, *italic*) and `code spans` "
             "from prose fields. Transcription residue from a Markdown "
             "mapping guide; consumers render the markers literally"
    )
    parser.add_argument(
        "--fix-reference-evidence-links", action="store_true",
        help="Copy a reference's links onto any of its evidenceBy rows that "
             "carry none. The assessor reports evidence without links as "
             "providing no actionable value, and the reference's own source is "
             "where the evidence is produced from"
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
        # Walk the baseline's own ancestors in. This tool renames against its
        # nearest match, so a vocabulary it cannot see is not a missing warning
        # but a wrong rewrite: against the partner baseline alone it proposed
        # five competency renames and two narrative-type retypes with eight
        # consequent element renames, every one a false positive caused by the
        # root baseline being invisible.
        if baseline:
            merge_ancestor_baselines(baseline, Path(args.baseline))

    all_fixes = []

    all_fixes.extend(fix_kind(data))
    all_fixes.extend(fix_element_kind(data))
    all_fixes.extend(fix_invalid_kind(data))
    all_fixes.extend(fix_narratives(data))
    all_fixes.extend(fix_citations(data))
    all_fixes.extend(fix_contributes_to(data))
    all_fixes.extend(fix_narrative_citations(data))
    all_fixes.extend(fix_relates_to_rationale(data))
    all_fixes.extend(fix_focus_names(data, baseline))

    if args.fix_truncated_names or args.all:
        all_fixes.extend(fix_truncated_names(data))

    if args.fix_prose_markup or args.all:
        all_fixes.extend(fix_prose_markup(data))

    if args.fix_reference_evidence_links or args.all:
        all_fixes.extend(fix_reference_evidence_links(data))

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

    if args.fix_ambiguous_views or args.collapse_ambiguous_views or args.all:
        all_fixes.extend(fix_ambiguous_pattern_views(
            data,
            state_order=_canonical_state_order(data, file_path),
            collapse=args.collapse_ambiguous_views,
        ))

    if args.fix_pattern_completeness or args.all:
        all_fixes.extend(fix_pattern_completeness(
            data, state_order=_canonical_state_order(data, file_path)))

    # Restore before compressing: a span re-expanded here must not then be
    # pruned by the same run.
    if args.restore_loop_states or args.all:
        all_fixes.extend(restore_loop_span_states(data))

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

    if args.fix_nested_narratives or args.all:
        all_fixes.extend(fix_nested_narratives(data))

    # Narrative types and competencies are inherited down the whole baseline
    # chain, so validate them against the merged vocabulary rather than
    # whichever baseline happened to be passed on the command line.
    vocabulary, vocab_source = resolve_reference_context(file_path, baseline, data)

    # A dependency practice declares vocabulary too, and nothing above reaches
    # it: the baseline chain walk climbs ancestors, not siblings. One partner
    # practice with three parents had nine competency references "corrected"
    # onto nearest matches in the leaf baseline, every one of them resolvable
    # through a dependency the tool could not see.
    for parent_path in args.parent:
        parent_data, parent_err = load_json_pair(Path(parent_path))
        if parent_err or not isinstance(parent_data, dict):
            print(f"Warning: --parent {parent_path} not loaded ({parent_err})",
                  file=sys.stderr)
            continue
        for key in ("competencies", "narrativeTypes", "activitySpaces",
                    "focuses", "alphas", "workProducts", "personas"):
            existing = {e.get("name") for e in vocabulary.get(key, [])
                        if isinstance(e, dict)}
            for elem in parent_data.get(key, []) or []:
                if isinstance(elem, dict) and elem.get("name") not in existing:
                    vocabulary.setdefault(key, []).append(elem)
                    existing.add(elem.get("name"))

    # Activity spaces inherit the same way. Checking them against the leaf
    # baseline alone flagged valid references to spaces defined further up the
    # chain, so this runs after the merged vocabulary is resolved.
    if args.fix_unknown_activity_spaces or args.all:
        all_fixes.extend(fix_unknown_activity_spaces(data, vocabulary))

    if args.fix_narrative_types or args.all:
        nt_fixes = fix_narrative_types(data, vocabulary)
        all_fixes.extend(nt_fixes)
        if nt_fixes:
            all_fixes.extend(fix_narrative_element_names(data, vocabulary))

    if args.fix_competency_refs or args.all:
        all_fixes.extend(fix_competency_refs(data, vocabulary, file_path,
                                             apply=args.fix))

    if args.fix_missing_seq or args.all:
        all_fixes.extend(fix_missing_seq(data))

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
