#!/usr/bin/env python3
"""Comprehensive assessment of practice/method/baseline JSON in a single invocation.

Consolidates inspection, structure checks, relationship validation, competency
validation, and schema validation into one report. Designed to replace the
multi-step manual assessment in the update-method skill.

Usage:
    # Basic assessment (detects kind, counts, structure, relationships)
    python3 utils/assess-practice.py <file.json>

    # With baseline validation (competency levels, alpha references)
    python3 utils/assess-practice.py <file.json> --baseline <baseline.json>

    # With schema validation
    python3 utils/assess-practice.py <file.json> --schema <schema.json>

    # Full assessment
    python3 utils/assess-practice.py <file.json> --baseline <baseline.json> --schema <schema.json>

Output: Structured JSON to stdout. Exit 0 if no errors, 1 if errors found.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json_pair


STANDARD_RELATIONSHIP_TYPES = {"produces", "governed by", "uses"}

BASELINE_REQUIRED_SECTIONS = [
    "focuses", "activitySpaces", "competencies", "narrativeTypes", "alphas"
]

PRACTICE_REQUIRED_SECTIONS = [
    "alphas", "activities", "workProducts", "patterns", "citations"
]

PRACTICE_MINIMUMS = {
    "alphas": 3,
    "workProducts": 3,
    "activities": 5,
    "patterns": 1,
    "citations": 3,
}

BASELINE_MINIMUMS = {
    "alphas": 3,
    "activitySpaces": 3,
    "competencies": 3,
    "narrativeTypes": 1,
    "citations": 3,
}


def count_elements(data, kind):
    counts = {}
    arrays = [
        "alphas", "workProducts", "activities", "patterns", "citations",
        "activitySpaces", "competencies", "narrativeTypes", "aliases",
        "assets", "focuses", "narratives", "personas",
    ]

    if kind == "method":
        for key in arrays:
            total = len(data.get(key, []))
            for p in data.get("practices", []):
                total += len(p.get(key, []))
            counts[key] = total
    else:
        for key in arrays:
            counts[key] = len(data.get(key, []))

    return counts


def check_uniqueness(data, kind):
    names = Counter()
    cross_practice_allowed = set()
    sources = [("root", data)]
    if kind == "method":
        for i, p in enumerate(data.get("practices", [])):
            sources.append((p.get("name", f"practice[{i}]"), p))

    element_types = [
        "alphas", "workProducts", "activities", "patterns", "personas",
        "activitySpaces", "assets",
    ]

    # For methods, track which element types allow cross-practice duplicates.
    # Alphas (baseline redeclarations), personas, personaGroups, and assets
    # can legitimately appear in multiple practices.
    cross_practice_types = {"alphas", "personas", "personaGroups", "assets"}

    for source_name, source in sources:
        for etype in element_types:
            for elem in source.get(etype, []):
                name = elem.get("name")
                if name:
                    names[name] += 1
                    if kind == "method" and etype in cross_practice_types and source_name != "root":
                        cross_practice_allowed.add(name)

    duplicates = [
        {"name": name, "count": count}
        for name, count in names.items()
        if count > 1 and name not in cross_practice_allowed
    ]
    return duplicates


def check_baseline_structure(data):
    results = {}
    issues = []

    has_focuses = len(data.get("focuses", [])) > 0
    results["focuses"] = has_focuses
    if not has_focuses:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "focuses",
            "message": "Baseline missing focuses array (need 2-4 focus areas)",
            "autoFixable": False,
        })

    has_activity_spaces = len(data.get("activitySpaces", [])) > 0
    results["activitySpaces"] = has_activity_spaces
    if not has_activity_spaces:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "activitySpaces",
            "message": "Baseline missing activitySpaces (need 6-12)",
            "autoFixable": False,
        })

    competencies = data.get("competencies", [])
    has_competencies = len(competencies) > 0
    results["competencies"] = has_competencies
    if not has_competencies:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "competencies",
            "message": "Baseline missing competencies (need 5-10 with 5 levels each)",
            "autoFixable": False,
        })
    else:
        for i, comp in enumerate(competencies):
            levels = comp.get("competencyLevels", comp.get("levels", []))
            if len(levels) != 5:
                issues.append({
                    "severity": "warning",
                    "category": "structure",
                    "path": f"competencies[{i}]",
                    "message": f"Competency '{comp.get('name')}' has {len(levels)} levels (expected 5)",
                    "autoFixable": False,
                })

    has_narrative_types = len(data.get("narrativeTypes", [])) > 0
    results["narrativeTypes"] = has_narrative_types
    if not has_narrative_types:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "narrativeTypes",
            "message": "Baseline missing narrativeTypes (need 3-5)",
            "autoFixable": False,
        })

    has_alphas = len(data.get("alphas", [])) > 0
    results["alphas"] = has_alphas

    results["narratives"] = len(data.get("narratives", [])) > 0
    results["citations"] = len(data.get("citations", [])) > 0
    results["kind"] = data.get("kind") == "practiceBaseline"
    if not results["kind"]:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "kind",
            "message": f"Expected kind='practiceBaseline', got '{data.get('kind')}'",
            "autoFixable": True,
        })

    return results, issues


def check_practice_structure(data, kind):
    results = {}
    issues = []

    results["kind"] = data.get("kind") in ("practice", "method")
    if not results["kind"]:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "kind",
            "message": f"Missing or invalid kind property (got '{data.get('kind')}')",
            "autoFixable": True,
        })

    has_baseline_name = bool(data.get("baselinePracticeName"))
    results["baselinePracticeName"] = has_baseline_name
    if not has_baseline_name:
        issues.append({
            "severity": "error",
            "category": "structure",
            "path": "baselinePracticeName",
            "message": "Missing baselinePracticeName property",
            "autoFixable": False,
        })

    sources = [("root", data)]
    if kind == "method":
        for i, p in enumerate(data.get("practices", [])):
            sources.append((p.get("name", f"practice[{i}]"), p))

    for source_name, source in sources:
        for key, minimum in PRACTICE_MINIMUMS.items():
            count = len(source.get(key, []))
            results[f"{source_name}.{key}"] = count >= minimum
            if count < minimum and source_name == "root" and kind != "method":
                issues.append({
                    "severity": "warning" if count > 0 else "error",
                    "category": "counts",
                    "path": key,
                    "message": f"{key}: {count} found (minimum {minimum})",
                    "autoFixable": False,
                })

    return results, issues


def check_alpha_relationships(data, kind):
    issues = []
    is_baseline = kind == "practiceBaseline"
    alphas = data.get("alphas", [])
    alpha_names = {a.get("name") for a in alphas}

    for idx, alpha in enumerate(alphas):
        alpha_name = alpha.get("name", f"<unnamed-{idx}>")
        prefix = f"alphas[{idx}]"

        if is_baseline:
            contributes_to = alpha.get("contributesTo")
            if contributes_to:
                issues.append({
                    "severity": "error",
                    "category": "baseline-alpha",
                    "path": f"{prefix}.contributesTo",
                    "message": f"Baseline alpha '{alpha_name}' has contributesTo (baseline alphas are root-level)",
                    "autoFixable": False,
                })

            relates_to = alpha.get("relatesTo", [])
            if not relates_to:
                issues.append({
                    "severity": "warning",
                    "category": "baseline-alpha",
                    "path": f"{prefix}.relatesTo",
                    "message": f"Baseline alpha '{alpha_name}' has no relatesTo relationships",
                    "autoFixable": False,
                })

            for rel_idx, rel in enumerate(relates_to):
                target = rel.get("alphaName")
                if target and target not in alpha_names:
                    issues.append({
                        "severity": "error",
                        "category": "integrity",
                        "path": f"{prefix}.relatesTo[{rel_idx}].alphaName",
                        "message": f"relatesTo references unknown alpha: {target}",
                        "autoFixable": False,
                    })

                relationship = rel.get("relationship", "")
                if relationship and relationship not in STANDARD_RELATIONSHIP_TYPES:
                    issues.append({
                        "severity": "warning",
                        "category": "relationship-type",
                        "path": f"{prefix}.relatesTo[{rel_idx}].relationship",
                        "message": f"Non-standard relationship type: {relationship}",
                        "autoFixable": True,
                    })
        else:
            contributes_to = alpha.get("contributesTo")
            is_redeclaration = alpha.get("_isRedeclaration", False)
            if not contributes_to and not is_redeclaration:
                issues.append({
                    "severity": "warning",
                    "category": "practice-alpha",
                    "path": f"{prefix}.contributesTo",
                    "message": f"New alpha '{alpha_name}' may be missing contributesTo (floating alpha)",
                    "autoFixable": False,
                })

    return issues


def check_competency_levels(data, baseline_data, kind):
    issues = []
    valid_levels = set()
    for comp in baseline_data.get("competencies", []):
        for level in comp.get("competencyLevels", comp.get("levels", [])):
            name = level.get("name")
            if name:
                valid_levels.add(name)

    if not valid_levels:
        return issues

    sources = [("root", data)]
    if kind == "method":
        for i, p in enumerate(data.get("practices", [])):
            sources.append((p.get("name", f"practice[{i}]"), p))

    invalid_count = 0
    for source_name, source in sources:
        for act in source.get("activities", []):
            for rcl in act.get("recommendedCompetencyLevels", []):
                name = rcl.get("competencyLevelName")
                if name and name not in valid_levels:
                    invalid_count += 1
        for persona in source.get("personas", []):
            for comp in persona.get("competencies", []):
                name = comp.get("competencyLevelName")
                if name and name not in valid_levels:
                    invalid_count += 1

    if invalid_count > 0:
        issues.append({
            "severity": "error",
            "category": "competency-levels",
            "path": "activities/personas",
            "message": f"{invalid_count} invalid competency level names (not in baseline)",
            "autoFixable": True,
        })

    return issues


def check_narrative_structure(data):
    issues = []
    for i, narrative in enumerate(data.get("narratives", [])):
        if "name" not in narrative:
            issues.append({
                "severity": "error",
                "category": "narrative-structure",
                "path": f"narratives[{i}]",
                "message": "Narrative missing 'name' property (PracticeElement requirement)",
                "autoFixable": True,
            })
        if "description" not in narrative:
            issues.append({
                "severity": "error",
                "category": "narrative-structure",
                "path": f"narratives[{i}]",
                "message": "Narrative missing 'description' property (PracticeElement requirement)",
                "autoFixable": True,
            })
    return issues


_AUTHOR_DATE_RE = re.compile(
    r'^[A-Z][a-z]+(?:(?:\s+(?:&|and)\s+[A-Z][a-z]+)+)?(?:\s+et\s+al\.?)?\s*\(\d{4}[a-z]?\)$'
)


def check_citation_structure(data):
    issues = []
    for i, citation in enumerate(data.get("citations", [])):
        if "name" not in citation:
            issues.append({
                "severity": "warning",
                "category": "citation-structure",
                "path": f"citations[{i}]",
                "message": "Citation missing 'name' property (PracticeElement requirement)",
                "autoFixable": True,
            })
            continue
        name = citation["name"]
        if _AUTHOR_DATE_RE.match(name):
            issues.append({
                "severity": "warning",
                "category": "citation-name-format",
                "path": f"citations[{i}]",
                "message": (
                    f"Citation name '{name}' uses author-date format "
                    f"— should be the work title. "
                    f"Fix with: python3 utils/fix-citation-names.py <file> "
                    f"--rename \"{name}=<Correct Title>\""
                ),
                "autoFixable": False,
            })
    return issues


def _collect_all_narratives(data):
    """Collect all narratives from top-level and element-embedded locations."""
    narrs = []
    for i, n in enumerate(data.get("narratives", [])):
        narrs.append((f"narratives[{i}]", n))
    for coll_key in ("alphas", "activitySpaces", "competencies"):
        for ei, elem in enumerate(data.get(coll_key, [])):
            for ni, n in enumerate(elem.get("narratives", [])):
                narrs.append((f"{coll_key}[{ei}].narratives[{ni}]", n))
    return narrs


def check_narrative_citations(data):
    issues = []
    citations = data.get("citations", [])
    if not citations:
        return issues

    citation_names = [c.get("name") for c in citations if c.get("name")]
    if not citation_names:
        return issues

    for path, narrative in _collect_all_narratives(data):
        existing = narrative.get("citationNames")
        if not existing or len(existing) == 0:
            issues.append({
                "severity": "warning",
                "category": "narrative-citations",
                "path": path,
                "message": (
                    f"Narrative '{narrative.get('name', '<unnamed>')}' has no "
                    f"citationNames but {len(citation_names)} citation(s) exist"
                ),
                "autoFixable": True,
            })
    return issues


def check_narrative_placement(data):
    """Warn when top-level narratives appear to belong to specific elements."""
    issues = []
    element_names = set()
    for coll_key in ("alphas", "activitySpaces", "competencies"):
        for elem in data.get(coll_key, []):
            element_names.add(elem.get("name", "").lower())

    for i, narrative in enumerate(data.get("narratives", [])):
        narr_name = narrative.get("name", "").lower()
        narr_desc = narrative.get("description", "").lower()
        for elem_name in sorted(element_names, key=len, reverse=True):
            if elem_name in narr_name or elem_name in narr_desc:
                issues.append({
                    "severity": "warning",
                    "category": "narrative-placement",
                    "path": f"narratives[{i}]",
                    "message": (
                        f"Top-level narrative '{narrative.get('name', '')}' appears to "
                        f"belong to element '{elem_name}' — should be embedded on the "
                        f"element's narratives[] property instead"
                    ),
                    "autoFixable": True,
                })
                break
    return issues


def check_narrative_self_reference(data):
    """Warn when narrative names or descriptions reference their template type."""
    import re
    issues = []
    type_patterns = [
        (r"\bSTAR\b", "STAR"),
        (r"\bThree-Act\b", "Three-Act"),
        (r"\bHero'?s Journey\b", "Hero's Journey"),
        (r"\bABT\b", "ABT"),
        (r"\bStoryBrand\b", "StoryBrand"),
        (r"\bmicro-narrative\b", "micro-narrative"),
    ]
    desc_patterns = [
        r"^The \w+ narrative for ",
        r"^The \w+ \w+ narrative for ",
        r"^The transformation journey narrative for ",
        r"narrative for the .+ alpha",
        r"narrative for the .+ competency",
        r"narrative for the .+ activity space",
    ]

    for path, narrative in _collect_all_narratives(data):
        name = narrative.get("name", "")
        desc = narrative.get("description", "")
        matched = None

        for pattern, label in type_patterns:
            if re.search(pattern, f"{name} {desc}", re.IGNORECASE):
                matched = label
                break

        if not matched:
            for pattern in desc_patterns:
                if re.search(pattern, desc, re.IGNORECASE):
                    matched = "self-referencing description"
                    break

        if matched:
            issues.append({
                "severity": "warning",
                "category": "narrative-self-reference",
                "path": path,
                "message": (
                    f"Narrative '{name}' name or description references narrative "
                    f"type mechanics ('{matched}'). Names and descriptions should "
                    f"describe subject matter, not expose template structure."
                ),
                "autoFixable": False,
            })
    return issues


def check_checklist_quality(data, kind):
    issues = []
    total = 0
    truncated_count = 0
    echo_count = 0
    duplicate_count = 0

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        for alpha in source.get("alphas", []):
            for state in alpha.get("states", []):
                for cl in state.get("checklist", []):
                    total += 1
                    name = cl.get("name", "")
                    desc = cl.get("description", "")

                    if not name or not desc:
                        continue

                    if name == desc:
                        duplicate_count += 1
                    elif len(name) == 50 and desc.startswith(name):
                        truncated_count += 1
                    elif desc.startswith(name) and len(name) < len(desc):
                        echo_count += 1

    if truncated_count > 0:
        issues.append({
            "severity": "warning",
            "category": "checklist-quality",
            "path": "alphas[*].states[*].checklist",
            "message": (
                f"{truncated_count}/{total} checklist names are exactly 50 characters "
                f"and truncated (cut mid-word from description)"
            ),
            "autoFixable": True,
        })

    if echo_count > 0:
        issues.append({
            "severity": "warning",
            "category": "checklist-quality",
            "path": "alphas[*].states[*].checklist",
            "message": (
                f"{echo_count}/{total} checklist names echo their description "
                f"(name is a prefix of description, should be a noun-phrase label)"
            ),
            "autoFixable": False,
        })

    if duplicate_count > 0:
        issues.append({
            "severity": "warning",
            "category": "checklist-quality",
            "path": "alphas[*].states[*].checklist",
            "message": (
                f"{duplicate_count}/{total} checklist names are identical "
                f"to their description"
            ),
            "autoFixable": False,
        })

    return issues


GENERIC_LOD_NAMES = {
    "basic", "basic setup", "initial", "simple", "standard",
    "level 1", "level 2", "level 3", "level 4", "level 5",
    "lod 1", "lod 2", "lod 3", "lod 4", "lod 5",
}

CONCERN_DESCRIPTIVE_TERMS = [
    "optimized", "performing", "established", "mature", "advanced",
    "forming", "storming", "norming", "drafted", "reviewed",
    "approved", "published", "enforced",
]


def check_lod_naming(data, kind):
    """Flag LOD names that are generic labels or describe concern progression
    rather than artifact content maturity (see semantics.md Section 4.6)."""
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    generic_count = 0
    concern_count = 0
    total = 0

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        for wp in source.get("workProducts", []):
            wp_name = wp.get("name", "?")
            for lod in wp.get("levelsOfDetail", []):
                total += 1
                name = lod.get("name", "")
                lower = name.lower().strip()

                if lower in GENERIC_LOD_NAMES:
                    generic_count += 1
                    issues.append({
                        "severity": "warning",
                        "category": "lod-naming",
                        "path": f"{pfx}workProducts[{wp_name}].levelsOfDetail[{name}]",
                        "message": (
                            f"LOD '{name}' on '{wp_name}' is a generic label. "
                            f"Use a content-descriptive name (e.g., 'Outlined', "
                            f"'Detailed Specification', 'Tested Templates')"
                        ),
                        "autoFixable": False,
                    })

                for term in CONCERN_DESCRIPTIVE_TERMS:
                    if term in lower:
                        concern_count += 1
                        issues.append({
                            "severity": "warning",
                            "category": "lod-naming",
                            "path": f"{pfx}workProducts[{wp_name}].levelsOfDetail[{name}]",
                            "message": (
                                f"LOD '{name}' on '{wp_name}' may describe concern "
                                f"progression rather than artifact content maturity "
                                f"(contains '{term}')"
                            ),
                            "autoFixable": False,
                        })
                        break

    return issues


def check_evidence_coverage(data, kind, baseline_alpha_names=None):
    """Check that alpha states are covered by at least one LOD contributesTo.

    Orphaned states (no work product LOD contributes to them) may indicate
    missing work products or incorrect alpha/work-product classification
    (see semantics.md Section 4.6).
    """
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        lod_targets = set()
        for wp in source.get("workProducts", []):
            for lod in wp.get("levelsOfDetail", []):
                for ct in lod.get("contributesTo", []):
                    alpha_name = ct.get("alphaName", "")
                    state_name = ct.get("stateName", "")
                    if alpha_name and state_name:
                        lod_targets.add((alpha_name, state_name))

        for alpha in source.get("alphas", []):
            a_name = alpha.get("name", "")
            if baseline_alpha_names and a_name in baseline_alpha_names:
                continue

            for state in alpha.get("states", []):
                s_name = state.get("name", "")
                if (a_name, s_name) not in lod_targets:
                    issues.append({
                        "severity": "warning",
                        "category": "evidence-coverage",
                        "path": f"{pfx}alphas[{a_name}].states[{s_name}]",
                        "message": (
                            f"Alpha '{a_name}' state '{s_name}' has no work product "
                            f"LOD contributing to it (no evidence)"
                        ),
                        "autoFixable": False,
                    })

    return issues


def check_internal_crossrefs(data, kind, baseline_data=None):
    """Validate all internal symbolic cross-references within a practice/method."""
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    all_alpha_names = set()
    all_alpha_states = {}
    all_wp_names = set()
    all_wp_lods = {}
    all_activity_names = set()
    all_persona_names = set()
    all_persona_group_names = set()
    all_citation_names = set()
    all_narrative_type_names = set()

    if baseline_data:
        for nt in baseline_data.get("narrativeTypes", []):
            name = nt.get("name", "")
            if name:
                all_narrative_type_names.add(name)

    for source in sources:
        for alpha in source.get("alphas", []):
            name = alpha.get("name", "")
            if name:
                all_alpha_names.add(name)
                all_alpha_states[name] = {
                    s.get("name") for s in alpha.get("states", []) if s.get("name")
                }

        for wp in source.get("workProducts", []):
            name = wp.get("name", "")
            if name:
                all_wp_names.add(name)
                all_wp_lods[name] = {
                    lod.get("name") for lod in wp.get("levelsOfDetail", [])
                    if lod.get("name")
                }

        for act in source.get("activities", []):
            name = act.get("name", "")
            if name:
                all_activity_names.add(name)

        for persona in source.get("personas", []):
            name = persona.get("name", "")
            if name:
                all_persona_names.add(name)

        for pg in source.get("personaGroups", []):
            name = pg.get("name", "")
            if name:
                all_persona_group_names.add(name)

        for cit in source.get("citations", []):
            name = cit.get("name", "")
            if name:
                all_citation_names.add(name)

        for nt in source.get("narrativeTypes", []):
            name = nt.get("name", "")
            if name:
                all_narrative_type_names.add(name)

    def _check_source(source, prefix):
        src_issues = []

        for ai, act in enumerate(source.get("activities", [])):
            act_path = f"{prefix}activities[{ai}]" if prefix else f"activities[{ai}]"
            act_name = act.get("name", f"<unnamed-{ai}>")

            for ci, contrib in enumerate(act.get("contributesTo", [])):
                aname = contrib.get("alphaName")
                sname = contrib.get("stateName")
                if aname and aname not in all_alpha_names:
                    src_issues.append({
                        "severity": "error",
                        "category": "crossref-activity-alpha",
                        "path": f"{act_path}.contributesTo[{ci}].alphaName",
                        "message": f"Activity '{act_name}' references unknown alpha '{aname}'",
                        "autoFixable": False,
                    })
                elif aname and sname and aname in all_alpha_states:
                    if sname not in all_alpha_states[aname]:
                        src_issues.append({
                            "severity": "error",
                            "category": "crossref-activity-alpha",
                            "path": f"{act_path}.contributesTo[{ci}].stateName",
                            "message": (
                                f"Activity '{act_name}' references unknown state "
                                f"'{sname}' for alpha '{aname}'"
                            ),
                            "autoFixable": False,
                        })

            for wi, wref in enumerate(act.get("worksOn", [])):
                wpname = wref.get("workProductName")
                lodname = wref.get("levelOfDetailName")
                if wpname and wpname not in all_wp_names:
                    src_issues.append({
                        "severity": "error",
                        "category": "crossref-activity-wp",
                        "path": f"{act_path}.worksOn[{wi}].workProductName",
                        "message": f"Activity '{act_name}' references unknown work product '{wpname}'",
                        "autoFixable": False,
                    })
                elif wpname and lodname and wpname in all_wp_lods:
                    if lodname not in all_wp_lods[wpname]:
                        src_issues.append({
                            "severity": "error",
                            "category": "crossref-activity-wp",
                            "path": f"{act_path}.worksOn[{wi}].levelOfDetailName",
                            "message": (
                                f"Activity '{act_name}' references unknown LOD "
                                f"'{lodname}' for work product '{wpname}'"
                            ),
                            "autoFixable": False,
                        })

            for ii, inv in enumerate(act.get("involves", [])):
                pgname = inv if isinstance(inv, str) else inv.get("personaGroupName", "")
                if pgname and pgname not in all_persona_group_names:
                    src_issues.append({
                        "severity": "error",
                        "category": "crossref-activity-persona",
                        "path": f"{act_path}.involves[{ii}]",
                        "message": f"Activity '{act_name}' involves unknown persona group '{pgname}'",
                        "autoFixable": False,
                    })

        for wi, wp in enumerate(source.get("workProducts", [])):
            wp_path = f"{prefix}workProducts[{wi}]" if prefix else f"workProducts[{wi}]"
            wp_name = wp.get("name", f"<unnamed-wp-{wi}>")
            for li, lod in enumerate(wp.get("levelsOfDetail", [])):
                for ci, contrib in enumerate(lod.get("contributesTo", [])):
                    aname = contrib.get("alphaName")
                    sname = contrib.get("stateName")
                    if aname and aname not in all_alpha_names:
                        src_issues.append({
                            "severity": "error",
                            "category": "crossref-lod-alpha",
                            "path": f"{wp_path}.levelsOfDetail[{li}].contributesTo[{ci}].alphaName",
                            "message": (
                                f"LOD '{lod.get('name','')}' of work product '{wp_name}' "
                                f"references unknown alpha '{aname}'"
                            ),
                            "autoFixable": False,
                        })
                    elif aname and sname and aname in all_alpha_states:
                        if sname not in all_alpha_states[aname]:
                            src_issues.append({
                                "severity": "error",
                                "category": "crossref-lod-alpha",
                                "path": f"{wp_path}.levelsOfDetail[{li}].contributesTo[{ci}].stateName",
                                "message": (
                                    f"LOD '{lod.get('name','')}' of work product '{wp_name}' "
                                    f"references unknown state '{sname}' for alpha '{aname}'"
                                ),
                                "autoFixable": False,
                            })

        for pi, pattern in enumerate(source.get("patterns", [])):
            pat_path = f"{prefix}patterns[{pi}]" if prefix else f"patterns[{pi}]"
            pat_name = pattern.get("name", f"<unnamed-pattern-{pi}>")
            for vi, view in enumerate(pattern.get("patternViews", [])):
                view_path = f"{pat_path}.patternViews[{vi}]"
                for axi, aref in enumerate(view.get("activities", [])):
                    aname = aref if isinstance(aref, str) else aref.get("activityName", "")
                    if aname and aname not in all_activity_names:
                        src_issues.append({
                            "severity": "error",
                            "category": "crossref-pattern",
                            "path": f"{view_path}.activities[{axi}]",
                            "message": (
                                f"Pattern '{pat_name}' view references "
                                f"unknown activity '{aname}'"
                            ),
                            "autoFixable": False,
                        })
                for asi, astate in enumerate(view.get("alphaStates", [])):
                    if isinstance(astate, dict):
                        aname = astate.get("alphaName")
                        sname = astate.get("stateName")
                        if aname and aname not in all_alpha_names:
                            src_issues.append({
                                "severity": "error",
                                "category": "crossref-pattern",
                                "path": f"{view_path}.alphaStates[{asi}].alphaName",
                                "message": (
                                    f"Pattern '{pat_name}' view references "
                                    f"unknown alpha '{aname}'"
                                ),
                                "autoFixable": False,
                            })
                        elif aname and sname and aname in all_alpha_states:
                            if sname not in all_alpha_states[aname]:
                                src_issues.append({
                                    "severity": "error",
                                    "category": "crossref-pattern",
                                    "path": f"{view_path}.alphaStates[{asi}].stateName",
                                    "message": (
                                        f"Pattern '{pat_name}' view references "
                                        f"unknown state '{sname}' for alpha '{aname}'"
                                    ),
                                    "autoFixable": False,
                                })
                for evi, ev in enumerate(view.get("evidenceBy", [])):
                    wpn = ev.get("workProductName", "")
                    lodn = ev.get("levelOfDetailName", "")
                    if wpn and wpn not in all_wp_names:
                        src_issues.append({
                            "severity": "error",
                            "category": "crossref-pattern",
                            "path": f"{view_path}.evidenceBy[{evi}].workProductName",
                            "message": (
                                f"Pattern '{pat_name}' view references "
                                f"unknown work product '{wpn}'"
                            ),
                            "autoFixable": False,
                        })
                    elif wpn and lodn and wpn in all_wp_lods:
                        if lodn not in all_wp_lods[wpn]:
                            src_issues.append({
                                "severity": "error",
                                "category": "crossref-pattern",
                                "path": f"{view_path}.evidenceBy[{evi}].levelOfDetailName",
                                "message": (
                                    f"Pattern '{pat_name}' view references "
                                    f"unknown LOD '{lodn}' for work product '{wpn}' "
                                    f"(available: {sorted(all_wp_lods[wpn])})"
                                ),
                                "autoFixable": False,
                            })

        for pgi, pg in enumerate(source.get("personaGroups", [])):
            pg_path = f"{prefix}personaGroups[{pgi}]" if prefix else f"personaGroups[{pgi}]"
            pg_name = pg.get("name", f"<unnamed-pg-{pgi}>")
            for pni, pname in enumerate(pg.get("personaNames", [])):
                if pname not in all_persona_names:
                    src_issues.append({
                        "severity": "error",
                        "category": "crossref-persona",
                        "path": f"{pg_path}.personaNames[{pni}]",
                        "message": (
                            f"PersonaGroup '{pg_name}' references "
                            f"unknown persona '{pname}'"
                        ),
                        "autoFixable": False,
                    })

        def _check_narrative_citations(narrs, base_path):
            for ni, narr in enumerate(narrs):
                for cni, cname in enumerate(narr.get("citationNames", [])):
                    if cname not in all_citation_names:
                        src_issues.append({
                            "severity": "error",
                            "category": "crossref-citation",
                            "path": f"{base_path}[{ni}].citationNames[{cni}]",
                            "message": (
                                f"Narrative '{narr.get('name', '')}' references "
                                f"unknown citation '{cname}'"
                            ),
                            "autoFixable": False,
                        })

        narr_prefix = f"{prefix}narratives" if prefix else "narratives"
        _check_narrative_citations(source.get("narratives", []), narr_prefix)
        for coll_key in ("alphas", "workProducts", "activities",
                         "patterns", "activitySpaces", "competencies"):
            for ei, elem in enumerate(source.get(coll_key, [])):
                elem_prefix = (
                    f"{prefix}{coll_key}[{ei}].narratives"
                    if prefix else f"{coll_key}[{ei}].narratives"
                )
                _check_narrative_citations(elem.get("narratives", []), elem_prefix)

        def _check_narrative_types(narrs, base_path):
            for ni, narr in enumerate(narrs):
                nt = narr.get("narrativeTypeName")
                if nt and nt not in all_narrative_type_names:
                    src_issues.append({
                        "severity": "error",
                        "category": "crossref-narrative-type",
                        "path": f"{base_path}[{ni}].narrativeTypeName",
                        "message": (
                            f"Narrative '{narr.get('name', '')}' uses "
                            f"unknown narrative type '{nt}'"
                        ),
                        "autoFixable": False,
                    })

        _check_narrative_types(source.get("narratives", []), narr_prefix)
        for coll_key in ("alphas", "workProducts", "activities",
                         "patterns", "activitySpaces", "competencies"):
            for ei, elem in enumerate(source.get(coll_key, [])):
                elem_prefix = (
                    f"{prefix}{coll_key}[{ei}].narratives"
                    if prefix else f"{coll_key}[{ei}].narratives"
                )
                _check_narrative_types(elem.get("narratives", []), elem_prefix)

        return src_issues

    for si, source in enumerate(sources):
        if si == 0:
            pfx = ""
        else:
            pfx = f"practices[{si - 1}]."
        issues.extend(_check_source(source, pfx))

    return issues


def check_baseline_references(data, baseline_data, kind):
    """Validate that practice references to baseline elements resolve correctly."""
    issues = []

    bl_focus_names = {f.get("name") for f in baseline_data.get("focuses", []) if f.get("name")}
    bl_alpha_names = {a.get("name") for a in baseline_data.get("alphas", []) if a.get("name")}
    bl_as_names = {s.get("name") for s in baseline_data.get("activitySpaces", []) if s.get("name")}
    bl_comp_names = {c.get("name") for c in baseline_data.get("competencies", []) if c.get("name")}
    bl_nt_names = {nt.get("name") for nt in baseline_data.get("narrativeTypes", []) if nt.get("name")}

    bl_comp_levels = set()
    for comp in baseline_data.get("competencies", []):
        for level in comp.get("competencyLevels", comp.get("levels", [])):
            name = level.get("name")
            if name:
                bl_comp_levels.add(name)

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    practice_alpha_names = set()
    practice_nt_names = set()
    for source in sources:
        for a in source.get("alphas", []):
            if a.get("name"):
                practice_alpha_names.add(a["name"])
        for nt in source.get("narrativeTypes", []):
            if nt.get("name"):
                practice_nt_names.add(nt["name"])

    all_alpha_names = bl_alpha_names | practice_alpha_names
    all_nt_names = bl_nt_names | practice_nt_names

    for si, source in enumerate(sources):
        if si == 0:
            pfx = ""
        else:
            pfx = f"practices[{si - 1}]."

        for ai, alpha in enumerate(source.get("alphas", [])):
            alpha_name = alpha.get("name", "")
            focus = alpha.get("focusName")
            if focus and focus not in bl_focus_names:
                issues.append({
                    "severity": "error",
                    "category": "baseline-ref-focus",
                    "path": f"{pfx}alphas[{ai}].focusName",
                    "message": f"Alpha '{alpha_name}' has unknown focusName '{focus}'",
                    "autoFixable": False,
                })

            ct = alpha.get("contributesTo")
            if ct and ct not in all_alpha_names:
                issues.append({
                    "severity": "error",
                    "category": "baseline-ref-alpha",
                    "path": f"{pfx}alphas[{ai}].contributesTo",
                    "message": (
                        f"Alpha '{alpha_name}' contributesTo unknown "
                        f"baseline alpha '{ct}'"
                    ),
                    "autoFixable": False,
                })

        for ai, act in enumerate(source.get("activities", [])):
            act_name = act.get("name", "")

            focus = act.get("focusName")
            if focus and focus not in bl_focus_names:
                issues.append({
                    "severity": "error",
                    "category": "baseline-ref-focus",
                    "path": f"{pfx}activities[{ai}].focusName",
                    "message": f"Activity '{act_name}' has unknown focusName '{focus}'",
                    "autoFixable": False,
                })

            asn = act.get("activitySpaceName")
            if asn and asn not in bl_as_names:
                issues.append({
                    "severity": "error",
                    "category": "baseline-ref-activityspace",
                    "path": f"{pfx}activities[{ai}].activitySpaceName",
                    "message": (
                        f"Activity '{act_name}' has unknown "
                        f"activitySpaceName '{asn}'"
                    ),
                    "autoFixable": False,
                })

            for ri, rc in enumerate(act.get("requiredCompetencies", [])):
                if rc not in bl_comp_names:
                    issues.append({
                        "severity": "error",
                        "category": "baseline-ref-competency",
                        "path": f"{pfx}activities[{ai}].requiredCompetencies[{ri}]",
                        "message": (
                            f"Activity '{act_name}' requiredCompetency "
                            f"'{rc}' not in baseline"
                        ),
                        "autoFixable": False,
                    })

            for ri, rcl in enumerate(act.get("recommendedCompetencyLevels", [])):
                cn = rcl.get("competencyName")
                cl = rcl.get("competencyLevelName")
                if cn and cn not in bl_comp_names:
                    issues.append({
                        "severity": "error",
                        "category": "baseline-ref-competency",
                        "path": f"{pfx}activities[{ai}].recommendedCompetencyLevels[{ri}].competencyName",
                        "message": (
                            f"Activity '{act_name}' recommendedCompetency "
                            f"'{cn}' not in baseline"
                        ),
                        "autoFixable": False,
                    })
                if cl and cl not in bl_comp_levels:
                    issues.append({
                        "severity": "error",
                        "category": "baseline-ref-competency",
                        "path": f"{pfx}activities[{ai}].recommendedCompetencyLevels[{ri}].competencyLevelName",
                        "message": (
                            f"Activity '{act_name}' competencyLevel "
                            f"'{cl}' not in baseline"
                        ),
                        "autoFixable": False,
                    })

        for pi, persona in enumerate(source.get("personas", [])):
            pname = persona.get("name", "")
            for ci, comp in enumerate(persona.get("competencies", [])):
                cn = comp.get("competencyName")
                cl = comp.get("competencyLevelName")
                if cn and cn not in bl_comp_names:
                    issues.append({
                        "severity": "error",
                        "category": "baseline-ref-competency",
                        "path": f"{pfx}personas[{pi}].competencies[{ci}].competencyName",
                        "message": (
                            f"Persona '{pname}' competency "
                            f"'{cn}' not in baseline"
                        ),
                        "autoFixable": False,
                    })
                if cl and cl not in bl_comp_levels:
                    issues.append({
                        "severity": "error",
                        "category": "baseline-ref-competency",
                        "path": f"{pfx}personas[{pi}].competencies[{ci}].competencyLevelName",
                        "message": (
                            f"Persona '{pname}' competencyLevel "
                            f"'{cl}' not in baseline"
                        ),
                        "autoFixable": False,
                    })

        def _check_nt_refs(narrs, base_path):
            nt_issues = []
            for ni, narr in enumerate(narrs):
                nt = narr.get("narrativeTypeName")
                if nt and nt not in all_nt_names:
                    nt_issues.append({
                        "severity": "error",
                        "category": "baseline-ref-narrativetype",
                        "path": f"{base_path}[{ni}].narrativeTypeName",
                        "message": (
                            f"Narrative '{narr.get('name', '')}' uses unknown "
                            f"narrative type '{nt}'"
                        ),
                        "autoFixable": False,
                    })
            return nt_issues

        narr_pfx = f"{pfx}narratives" if pfx else "narratives"
        issues.extend(_check_nt_refs(source.get("narratives", []), narr_pfx))
        for coll_key in ("alphas", "workProducts", "activities", "patterns"):
            for ei, elem in enumerate(source.get(coll_key, [])):
                e_pfx = f"{pfx}{coll_key}[{ei}].narratives" if pfx else f"{coll_key}[{ei}].narratives"
                issues.extend(_check_nt_refs(elem.get("narratives", []), e_pfx))

        for ali, alias in enumerate(source.get("practiceElementAliases", [])):
            target = alias.get("practiceElementName", "")
            etype = alias.get("practiceElementType", "")
            if etype == "Alpha" and target:
                if target not in all_alpha_names:
                    issues.append({
                        "severity": "error",
                        "category": "baseline-ref-alias",
                        "path": f"{pfx}practiceElementAliases[{ali}]",
                        "message": f"Alias targets unknown alpha '{target}'",
                        "autoFixable": False,
                    })

    return issues


def check_redeclaration_compliance(data, baseline_data, kind):
    """Check that redeclared alphas preserve baseline structure.

    Redeclared alphas (practice alphas whose name matches a baseline alpha)
    MUST NOT change: focusName, state names, state sequence.
    They CAN enrich descriptions, add checklist items to states, and add
    narratives/tags. Description enrichment is the purpose of redeclaration.
    """
    issues = []

    bl_alphas = {a["name"]: a for a in baseline_data.get("alphas", []) if a.get("name")}

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        for pi, pa in enumerate(source.get("alphas", [])):
            pa_name = pa.get("name", "")
            if pa_name not in bl_alphas:
                continue

            ba = bl_alphas[pa_name]
            path = f"{pfx}alphas[{pa_name}]"

            if pa.get("description") and ba.get("description"):
                if pa["description"] != ba["description"]:
                    issues.append({
                        "severity": "warning",
                        "category": "redeclaration-compliance",
                        "path": f"{path}.description",
                        "message": (
                            f"Redeclared alpha '{pa_name}' enriched baseline description. "
                            f"Baseline: \"{ba['description'][:80]}...\" "
                            f"Practice: \"{pa['description'][:80]}...\""
                        ),
                        "autoFixable": True,
                    })

            if pa.get("focusName") and ba.get("focusName"):
                if pa["focusName"] != ba["focusName"]:
                    issues.append({
                        "severity": "error",
                        "category": "redeclaration-compliance",
                        "path": f"{path}.focusName",
                        "message": (
                            f"Redeclared alpha '{pa_name}' changed focusName "
                            f"from '{ba['focusName']}' to '{pa['focusName']}'"
                        ),
                        "autoFixable": True,
                    })

            ba_states = [(s["name"], s.get("seq")) for s in ba.get("states", [])]
            pa_states = [(s["name"], s.get("seq")) for s in pa.get("states", [])]

            if [name for name, _ in pa_states] != [name for name, _ in ba_states]:
                issues.append({
                    "severity": "error",
                    "category": "redeclaration-compliance",
                    "path": f"{path}.states",
                    "message": (
                        f"Redeclared alpha '{pa_name}' changed state names. "
                        f"Baseline: {[n for n,_ in ba_states]} "
                        f"Practice: {[n for n,_ in pa_states]}"
                    ),
                    "autoFixable": False,
                })
            else:
                ba_state_map = {s["name"]: s for s in ba.get("states", [])}
                for ps in pa.get("states", []):
                    bs = ba_state_map.get(ps["name"])
                    if not bs:
                        continue

                    if ps.get("description") and bs.get("description"):
                        if ps["description"] != bs["description"]:
                            issues.append({
                                "severity": "warning",
                                "category": "redeclaration-compliance",
                                "path": f"{path}.states[{ps['name']}].description",
                                "message": (
                                    f"Redeclared state '{pa_name}.{ps['name']}' enriched description. "
                                    f"Baseline: \"{bs['description'][:60]}...\" "
                                    f"Practice: \"{ps['description'][:60]}...\""
                                ),
                                "autoFixable": True,
                            })

                    bc = len(bs.get("checklist", []))
                    pc = len(ps.get("checklist", []))
                    if pc > bc:
                        issues.append({
                            "severity": "info",
                            "category": "redeclaration-compliance",
                            "path": f"{path}.states[{ps['name']}].checklist",
                            "message": (
                                f"Alpha '{pa_name}' state '{ps['name']}': "
                                f"{pc - bc} checklist(s) added (baseline: {bc}, practice: {pc})"
                            ),
                            "autoFixable": False,
                        })

    return issues


def check_asset_coverage(data):
    issues = []
    assets = data.get("assets", [])
    asset_names = {a.get("name") for a in assets}

    coverage_checks = [
        ("alphas", "Alphas"),
        ("competencies", "Competencies"),
        ("activitySpaces", "ActivitySpaces"),
        ("narrativeTypes", "NarrativeTypes"),
        ("focuses", "Focuses"),
        ("narratives", "Narratives"),
    ]

    missing_types = []

    for key, label in coverage_checks:
        elements = data.get(key, [])
        if not elements:
            continue
        with_assets = sum(1 for e in elements if e.get("assetNames"))
        total = len(elements)

        if with_assets == 0 and total > 0 and key in ("narrativeTypes", "focuses"):
            missing_types.append(f"{label} ({total} elements, 0% coverage)")

    if missing_types:
        issues.append({
            "severity": "warning",
            "category": "asset-coverage",
            "path": "assetNames",
            "message": (
                f"Asset coverage gaps: {'; '.join(missing_types)}. "
                f"These element types should have icon assets."
            ),
            "autoFixable": False,
        })

    for key, label in coverage_checks:
        for i, elem in enumerate(data.get(key, [])):
            for ref in elem.get("assetNames", []):
                ref_name = ref.get("assetName") if isinstance(ref, dict) else ref
                if ref_name and ref_name not in asset_names:
                    issues.append({
                        "severity": "error",
                        "category": "asset-coverage",
                        "path": f"{key}[{i}].assetNames",
                        "message": (
                            f"AssetReference '{ref_name}' on {label} "
                            f"'{elem.get('name', '')}' not found in assets array"
                        ),
                        "autoFixable": False,
                    })

    return issues


def check_asset_urls(assets):
    import urllib.request
    import urllib.error

    issues = []
    for i, asset in enumerate(assets):
        url = asset.get("url")
        if not url or not url.startswith("http"):
            continue
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "PracticeValidator/1.0")
            urllib.request.urlopen(req, timeout=5)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            issues.append({
                "severity": "warning",
                "category": "asset-coverage",
                "path": f"assets[{i}].url",
                "message": f"Asset '{asset.get('name')}' URL unreachable: {url} ({e})",
                "autoFixable": True,
            })
    return issues


def run_schema_validation(file_path, schema_path, kind, baseline_path=None):
    if kind == "practiceBaseline":
        cmd = ["python3", "utils/validate-baseline-json.py", str(file_path)]
        if baseline_path:
            cmd.append(str(baseline_path))
        cmd.append(str(schema_path))
    else:
        if not baseline_path:
            return None, "Schema validation for practices requires --baseline"
        cmd = [
            "python3", "utils/validate-practice-json.py",
            str(file_path), str(baseline_path), str(schema_path),
        ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        stdout = result.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout), None
            except json.JSONDecodeError:
                return None, f"Validator output not valid JSON: {stdout[:200]}"
        return None, f"Validator produced no output (exit {result.returncode})"
    except subprocess.TimeoutExpired:
        return None, "Schema validation timed out"
    except FileNotFoundError:
        return None, "Validator script not found"


def detect_dependencies(data):
    deps = data.get("baselinePracticeNames", [])
    if not deps:
        single = data.get("baselinePracticeName", "")
        if single:
            deps = [single]
    return deps


def check_narrative_name_uniqueness(data, kind):
    """Check that narrative names are unique across all elements."""
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        all_narrs = []

        for n in source.get("narratives", []):
            all_narrs.append((f"{pfx}narratives", "practice", n.get("name", "")))

        for a in source.get("alphas", []):
            for n in a.get("narratives", []):
                all_narrs.append((
                    f"{pfx}alphas[{a['name']}].narratives",
                    a["name"], n.get("name", ""),
                ))
            for s in a.get("states", []):
                for n in s.get("narratives", []):
                    all_narrs.append((
                        f"{pfx}alphas[{a['name']}].states[{s['name']}].narratives",
                        f"{a['name']}.{s['name']}", n.get("name", ""),
                    ))

        for act in source.get("activities", []):
            for n in act.get("narratives", []):
                all_narrs.append((
                    f"{pfx}activities[{act['name']}].narratives",
                    act["name"], n.get("name", ""),
                ))

        for wp in source.get("workProducts", []):
            for n in wp.get("narratives", []):
                all_narrs.append((
                    f"{pfx}workProducts[{wp['name']}].narratives",
                    wp["name"], n.get("name", ""),
                ))

        for pat in source.get("patterns", []):
            for n in pat.get("narratives", []):
                all_narrs.append((
                    f"{pfx}patterns[{pat['name']}].narratives",
                    pat["name"], n.get("name", ""),
                ))

        name_counts = {}
        for path, elem, name in all_narrs:
            if not name:
                continue
            name_counts.setdefault(name, []).append((path, elem))

        for name, locations in name_counts.items():
            if len(locations) > 1:
                elems = [elem for _, elem in locations]
                issues.append({
                    "severity": "warning",
                    "category": "narrative-uniqueness",
                    "path": locations[0][0],
                    "message": (
                        f"Narrative name '{name}' appears {len(locations)} times "
                        f"(on: {', '.join(elems)})"
                    ),
                    "autoFixable": False,
                })

    return issues


def check_pattern_alpha_coverage(data, kind):
    """Check that patterns cover all practice alphas."""
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        alpha_names = {a["name"] for a in source.get("alphas", []) if a.get("name")}
        if len(alpha_names) < 2:
            continue

        for pi, pat in enumerate(source.get("patterns", [])):
            pat_name = pat.get("name", f"<unnamed-{pi}>")
            covered = set()
            for view in pat.get("patternViews", []):
                for astate in view.get("alphaStates", []):
                    covered.add(astate.get("alphaName", ""))

            missing = alpha_names - covered
            if missing:
                issues.append({
                    "severity": "warning",
                    "category": "pattern-coverage",
                    "path": f"{pfx}patterns[{pat_name}]",
                    "message": (
                        f"Pattern '{pat_name}' covers {len(covered)}/{len(alpha_names)} "
                        f"alphas. Missing: {sorted(missing)}"
                    ),
                    "autoFixable": False,
                })

    return issues


def check_narrative_context_length(data, kind):
    """Flag narrative contexts that exceed 3 sentences."""
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    long_count = 0
    total = 0

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        def _check_narratives(narrs, base_path):
            nonlocal long_count, total
            for ni, narr in enumerate(narrs):
                for nc in narr.get("narrativeContexts", []):
                    total += 1
                    ctx = nc.get("context", "")
                    sentences = ctx.count(". ") + ctx.count("? ") + (
                        1 if ctx.endswith(".") or ctx.endswith("?") else 0
                    )
                    if sentences > 3:
                        long_count += 1

        _check_narratives(source.get("narratives", []), f"{pfx}narratives")
        for coll in ("alphas", "activities", "workProducts", "patterns"):
            for elem in source.get(coll, []):
                _check_narratives(
                    elem.get("narratives", []),
                    f"{pfx}{coll}[{elem.get('name', '?')}].narratives",
                )
                if coll == "alphas":
                    for state in elem.get("states", []):
                        _check_narratives(
                            state.get("narratives", []),
                            f"{pfx}alphas[{elem.get('name', '?')}].states[{state.get('name', '?')}].narratives",
                        )

    if long_count > 0:
        issues.append({
            "severity": "warning",
            "category": "narrative-context-length",
            "path": "narrativeContexts",
            "message": (
                f"{long_count}/{total} narrative contexts exceed 3 sentences "
                f"(target: 1-3 sentences per context)"
            ),
            "autoFixable": False,
        })

    return issues


_BARE_GERUND_RE = re.compile(
    r'^(?:Failing|Overlooking|Not |Ignoring|Skipping|Omitting|Attempting|Avoiding'
    r'|Forgetting|Missing|Neglecting|Using |Running |Setting )\b'
)

_BARE_LIST_RE = re.compile(
    r'^(?:[A-Z][a-z]+ing .*?\. [A-Z][a-z]+ing .*?\. [A-Z][a-z]+ing )'
)


def check_narrative_context_self_containment(data, kind):
    """Flag narrative contexts that appear heading-dependent.

    Contexts must be readable as prose without the narrative element name
    as a heading (see semantics.md Section 10). Bare gerund lists and
    sentence-fragment enumerations typically fail this test.
    """
    issues = []

    sources = [data]
    if kind == "method":
        sources.extend(data.get("practices", []))

    flagged = []

    for source in sources:
        pfx = ""
        if kind == "method" and source is not data:
            pfx = f"practice[{source.get('name', '?')}]."

        def _check_narrs(narrs, base_path):
            for ni, narr in enumerate(narrs):
                narr_name = narr.get("name", "?")
                contexts = narr.get("narrativeContexts", [])
                if len(contexts) < 2:
                    continue
                for nc in contexts:
                    ctx = nc.get("context", "").strip()
                    elem_name = nc.get("narrativeElementName", "")
                    if not ctx:
                        continue
                    if _BARE_GERUND_RE.match(ctx):
                        flagged.append((
                            f"{base_path}[{ni}]",
                            narr_name,
                            elem_name,
                            ctx[:80],
                        ))
                    elif _BARE_LIST_RE.match(ctx):
                        flagged.append((
                            f"{base_path}[{ni}]",
                            narr_name,
                            elem_name,
                            ctx[:80],
                        ))

        _check_narrs(source.get("narratives", []), f"{pfx}narratives")
        for coll in ("alphas", "activities", "workProducts", "patterns"):
            for elem in source.get(coll, []):
                _check_narrs(
                    elem.get("narratives", []),
                    f"{pfx}{coll}[{elem.get('name', '?')}].narratives",
                )

    if flagged:
        for path, narr_name, elem_name, snippet in flagged:
            issues.append({
                "severity": "warning",
                "category": "narrative-self-containment",
                "path": path,
                "message": (
                    f"Narrative '{narr_name}' context for '{elem_name}' "
                    f"may be heading-dependent (starts with bare gerund/list): "
                    f"\"{snippet}...\""
                ),
                "autoFixable": False,
            })

    return issues


REMAP_WARNING_CATEGORIES = {"checklist-quality", "asset-coverage", "citation-name-format"}


def suggest_update_mode(issues, counts, kind):
    errors = [i for i in issues if i["severity"] == "error"]
    auto_fixable = [i for i in issues if i.get("autoFixable")]
    manual_fix = [i for i in errors if not i.get("autoFixable")]

    remap_warnings = [
        i for i in issues
        if i["severity"] == "warning"
        and not i.get("autoFixable")
        and i["category"] in REMAP_WARNING_CATEGORIES
    ]

    if not issues:
        return "none", "No issues found"

    if not manual_fix and not remap_warnings and auto_fixable:
        return "auto-fix", "All issues are auto-fixable"

    structural_errors = [i for i in errors if i["category"] == "structure"]
    if structural_errors:
        return "full-reanalysis", f"{len(structural_errors)} structural errors require full reanalysis"

    remap_count = len(manual_fix) + len(remap_warnings)
    reasons = []
    if manual_fix:
        reasons.append(f"{len(manual_fix)} error(s)")
    if remap_warnings:
        reasons.append(f"{len(remap_warnings)} quality warning(s)")
    return "remap", f"{remap_count} issue(s) require remapping: {', '.join(reasons)}"


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive assessment of practice/method/baseline JSON"
    )
    parser.add_argument("file", help="Practice, method, or baseline JSON file")
    parser.add_argument(
        "--baseline", help="Baseline practice JSON for competency/reference validation"
    )
    parser.add_argument(
        "--schema", help="Language schema JSON for schema validation"
    )
    parser.add_argument(
        "--parent", action="append", default=[],
        help="Parent/dependency practice JSON(s) whose alphas and narrativeTypes are merged into the baseline for validation (repeatable)"
    )
    parser.add_argument(
        "--online", action="store_true",
        help="Enable network checks (URL reachability for assets)"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Output concise summary (counts by severity and category) instead of full report"
    )
    parser.add_argument(
        "--errors-only", action="store_true",
        help="Filter issues to only include severity='error' items"
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    data, err = load_json_pair(file_path)
    if err:
        print(json.dumps({"error": err}))
        sys.exit(1)

    kind = data.get("kind", "practice")
    name = data.get("name", "<unnamed>")

    all_issues = []

    counts = count_elements(data, kind)

    duplicates = check_uniqueness(data, kind)
    if duplicates:
        all_issues.append({
            "severity": "error",
            "category": "uniqueness",
            "path": "PracticeElement names",
            "message": f"{len(duplicates)} duplicate name(s): {', '.join(d['name'] for d in duplicates)}",
            "autoFixable": False,
        })

    if kind == "practiceBaseline":
        structure, struct_issues = check_baseline_structure(data)
    else:
        structure, struct_issues = check_practice_structure(data, kind)
    all_issues.extend(struct_issues)

    all_issues.extend(check_alpha_relationships(data, kind))
    all_issues.extend(check_narrative_structure(data))
    all_issues.extend(check_citation_structure(data))
    all_issues.extend(check_narrative_citations(data))
    all_issues.extend(check_narrative_placement(data))
    all_issues.extend(check_narrative_self_reference(data))
    all_issues.extend(check_checklist_quality(data, kind))
    all_issues.extend(check_lod_naming(data, kind))
    all_issues.extend(check_narrative_name_uniqueness(data, kind))
    all_issues.extend(check_pattern_alpha_coverage(data, kind))
    all_issues.extend(check_narrative_context_length(data, kind))
    all_issues.extend(check_narrative_context_self_containment(data, kind))
    all_issues.extend(check_asset_coverage(data))

    if args.online:
        all_issues.extend(check_asset_urls(data.get("assets", [])))

    baseline_data = None
    if args.baseline:
        baseline_path = Path(args.baseline)
        baseline_data, berr = load_json_pair(baseline_path)
        if berr:
            all_issues.append({
                "severity": "warning",
                "category": "baseline",
                "path": "baseline",
                "message": f"Could not load baseline: {berr}",
                "autoFixable": False,
            })

    if baseline_data and args.parent:
        bl_alpha_set = {a["name"] for a in baseline_data.get("alphas", []) if a.get("name")}
        bl_nt_set = {nt["name"] for nt in baseline_data.get("narrativeTypes", []) if nt.get("name")}
        bl_comp_names = {c["name"] for c in baseline_data.get("competencies", []) if c.get("name")}
        bl_asp_names = {s["name"] for s in baseline_data.get("activitySpaces", []) if s.get("name")}

        def _merge_elements(source):
            nonlocal bl_alpha_set, bl_nt_set, bl_comp_names, bl_asp_names
            for alpha in source.get("alphas", []):
                if alpha.get("name") and alpha["name"] not in bl_alpha_set:
                    baseline_data.setdefault("alphas", []).append(alpha)
                    bl_alpha_set.add(alpha["name"])
            for nt in source.get("narrativeTypes", []):
                if nt.get("name") and nt["name"] not in bl_nt_set:
                    baseline_data.setdefault("narrativeTypes", []).append(nt)
                    bl_nt_set.add(nt["name"])
            for comp in source.get("competencies", []):
                if comp.get("name") and comp["name"] not in bl_comp_names:
                    baseline_data.setdefault("competencies", []).append(comp)
                    bl_comp_names.add(comp["name"])
            for asp in source.get("activitySpaces", []):
                if asp.get("name") and asp["name"] not in bl_asp_names:
                    baseline_data.setdefault("activitySpaces", []).append(asp)
                    bl_asp_names.add(asp["name"])

        for parent_path in args.parent:
            parent_data, perr = load_json_pair(Path(parent_path))
            if perr:
                all_issues.append({
                    "severity": "warning",
                    "category": "parent",
                    "path": f"parent:{parent_path}",
                    "message": f"Could not load parent: {perr}",
                    "autoFixable": False,
                })
                continue
            _merge_elements(parent_data)
            if parent_data.get("kind") == "method":
                for practice in parent_data.get("practices", []):
                    _merge_elements(practice)

    all_issues.extend(check_internal_crossrefs(data, kind, baseline_data))

    if baseline_data and kind != "practiceBaseline":
        all_issues.extend(check_competency_levels(data, baseline_data, kind))
        all_issues.extend(check_baseline_references(data, baseline_data, kind))
        all_issues.extend(check_redeclaration_compliance(data, baseline_data, kind))
        bl_alpha_names = {a["name"] for a in baseline_data.get("alphas", []) if a.get("name")}
        all_issues.extend(check_evidence_coverage(data, kind, baseline_alpha_names=bl_alpha_names))
    elif kind != "practiceBaseline":
        all_issues.extend(check_evidence_coverage(data, kind))

    if kind == "practiceBaseline" and args.parent:
        parent_merged = None
        for parent_path in args.parent:
            pd, perr = load_json_pair(Path(parent_path))
            if perr:
                continue
            if parent_merged is None:
                parent_merged = pd
            else:
                for alpha in pd.get("alphas", []):
                    parent_merged.setdefault("alphas", []).append(alpha)
        if parent_merged:
            all_issues.extend(check_redeclaration_compliance(data, parent_merged, kind))

    schema_report = None
    if args.schema:
        schema_path = Path(args.schema)
        schema_report, schema_err = run_schema_validation(
            file_path, schema_path, kind,
            baseline_path=Path(args.baseline) if args.baseline else None,
        )
        if schema_err:
            all_issues.append({
                "severity": "warning",
                "category": "schema",
                "path": "schema",
                "message": f"Schema validation skipped: {schema_err}",
                "autoFixable": False,
            })
        elif schema_report and not schema_report.get("valid", True):
            error_count = schema_report.get("summary", {}).get("error_count", 0)
            all_issues.append({
                "severity": "error",
                "category": "schema",
                "path": "schema-validation",
                "message": f"Schema validation failed with {error_count} error(s)",
                "autoFixable": False,
            })

    if args.errors_only:
        all_issues = [i for i in all_issues if i["severity"] == "error"]

    dependencies = detect_dependencies(data)

    auto_fixable = [i for i in all_issues if i.get("autoFixable")]
    manual_fix = [i for i in all_issues if not i.get("autoFixable") and i["severity"] == "error"]

    auto_fix_summary = {}
    for issue in auto_fixable:
        cat = issue["category"]
        auto_fix_summary[cat] = auto_fix_summary.get(cat, 0) + 1
    auto_fix_descriptions = [
        f"{count} {cat} issue(s)" for cat, count in auto_fix_summary.items()
    ]

    manual_fix_summary = {}
    for issue in manual_fix:
        cat = issue["category"]
        manual_fix_summary[cat] = manual_fix_summary.get(cat, 0) + 1
    manual_fix_descriptions = [
        f"{count} {cat} issue(s)" for cat, count in manual_fix_summary.items()
    ]

    suggested_mode, mode_reason = suggest_update_mode(all_issues, counts, kind)

    error_count = sum(1 for i in all_issues if i["severity"] == "error")
    warning_count = sum(1 for i in all_issues if i["severity"] == "warning")

    report = {
        "file": str(file_path),
        "kind": kind,
        "name": name,
        "valid": error_count == 0,
        "counts": counts,
        "structureComplete": structure,
        "dependencies": dependencies,
        "issues": all_issues,
        "schemaValidation": schema_report,
        "recommendations": {
            "autoFixable": auto_fix_descriptions,
            "manualFix": manual_fix_descriptions,
            "suggestedUpdateMode": suggested_mode,
            "modeReason": mode_reason,
        },
        "summary": f"{error_count} error(s), {warning_count} warning(s). Suggested mode: {suggested_mode}",
    }

    if args.summary:
        from collections import Counter
        errors = [i for i in all_issues if i["severity"] == "error"]
        warnings = [i for i in all_issues if i["severity"] == "warning"]
        err_cats = Counter(i["category"] for i in errors)
        warn_cats = Counter(i["category"] for i in warnings)
        summary = {
            "file": str(file_path),
            "kind": kind,
            "name": name,
            "valid": error_count == 0,
            "errors": error_count,
            "warnings": warning_count,
            "errorCategories": dict(err_cats.most_common()),
            "warningCategories": dict(warn_cats.most_common()),
            "schemaErrors": schema_report.get("summary", {}).get("error_count", 0) if schema_report else None,
            "suggestedUpdateMode": suggested_mode,
            "modeReason": mode_reason,
        }
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(report, indent=2))
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
