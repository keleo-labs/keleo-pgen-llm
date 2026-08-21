#!/usr/bin/env python3
"""Evaluate skill output quality by composing existing validators into agentskills.io grading.

Usage:
    # Full eval (auto-discovers --baseline from baselinePracticeName, --schema from deps/)
    python3 utils/eval-skill-output.py practices/<name>/ --summary

    # Show only failed assertions with details
    python3 utils/eval-skill-output.py practices/<name>/ --show-failed

    # Single-line summary (great for scripting / quick checks)
    python3 utils/eval-skill-output.py practices/<name>/ --one-line

    # Explicit baseline/schema (overrides auto-discovery)
    python3 utils/eval-skill-output.py practices/<name>/ \
      --baseline deps/platform-adoption-kernel.json \
      --schema deps/language.schema.json

    # Full eval of baseline
    python3 utils/eval-skill-output.py baselines/<name>/ --schema deps/language.schema.json

    # Baseline extending a parent
    python3 utils/eval-skill-output.py baselines/<name>/ \
      --parent deps/platform-adoption-kernel.json --schema deps/language.schema.json

    # Phase-specific eval
    python3 utils/eval-skill-output.py practices/<name>/ --phase 1
    python3 utils/eval-skill-output.py practices/<name>/ --phase 3

    # Batch eval from evals.json
    python3 utils/eval-skill-output.py --evals .claude/skills/generate-method/evals/evals.json
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, detect_kind

UTILS_DIR = Path(__file__).resolve().parent


def load_specs_index(specs_path):
    """Load specs-index.json and build reverse map: assess_category → list of spec IDs."""
    data = load_json(specs_path, exit_on_error=False)
    cat_to_specs = {}
    for scenario in data.get("scenarios", []):
        for cat in scenario.get("assess_categories", []):
            cat_to_specs.setdefault(cat, []).append(scenario["id"])
    return data, cat_to_specs


def annotate_with_specs(assertion_results, cat_to_specs):
    """Add spec_ids to each assertion result based on its assess categories."""
    for a in assertion_results:
        assertion_id = a["id"]
        categories = ASSESS_CATEGORY_MAP.get(assertion_id, ())
        spec_ids = []
        for cat in categories:
            spec_ids.extend(cat_to_specs.get(cat, []))
        if spec_ids:
            a["spec_ids"] = sorted(set(spec_ids))


ASSESS_CATEGORY_MAP = {
    "structure:kind": ("structure",),
    "structure:sections": ("structure",),
    "structure:counts": ("counts",),
    "structure:uniqueness": ("uniqueness",),
    "rel:alpha-baseline": ("baseline-alpha",),
    "rel:alpha-practice": ("practice-alpha",),
    "rel:integrity": ("integrity",),
    "rel:competency-levels": ("competency-levels",),
    "rel:redeclaration": ("redeclaration-compliance",),
    "xref:activity-alpha": ("crossref-activity-alpha",),
    "xref:activity-wp": ("crossref-activity-wp",),
    "xref:activity-persona": ("crossref-activity-persona",),
    "xref:lod-alpha": ("crossref-lod-alpha",),
    "xref:pattern": ("crossref-pattern",),
    "xref:citation": ("crossref-citation",),
    "xref:narrative-type": ("crossref-narrative-type",),
    "bref:focus": ("baseline-ref-focus",),
    "bref:alpha": ("baseline-ref-alpha",),
    "bref:activityspace": ("baseline-ref-activityspace",),
    "bref:competency": ("baseline-ref-competency",),
    "bref:narrativetype": ("baseline-ref-narrativetype",),
    "bref:alias": ("baseline-ref-alias",),
    "qual:narrative-citations": ("narrative-citations",),
    "qual:narrative-placement": ("narrative-placement",),
    "qual:narrative-self-ref": ("narrative-self-reference",),
    "qual:narrative-context-len": ("narrative-context-length",),
    "qual:narrative-self-contain": ("narrative-self-containment",),
    "qual:checklist-names": ("checklist-quality",),
    "qual:lod-naming": ("lod-naming",),
    "qual:evidence-coverage": ("evidence-coverage",),
    "qual:asset-coverage": ("asset-coverage",),
    "qual:pattern-coverage": ("pattern-coverage",),
    "qual:narrative-uniqueness": ("narrative-uniqueness",),
    "rel:mapsto-naming": ("mapsto-naming",),
    "rel:contributes-to-state": ("contributes-to-state",),
    "qual:narrative-structure": ("narrative-structure",),
    "qual:description-length": ("description-length",),
    "qual:activity-distinctness": ("activity-name-distinctness",),
    "coverage:alpha-states": ("alpha-state-minimum",),
    "coverage:wp-lods": ("workproduct-lod-minimum",),
    "coverage:activity-gap": ("activity-state-gap",),
    "qual:alias-uniqueness": ("alias-uniqueness",),
    "qual:alias-isolation": ("alias-isolation",),
    "qual:keyword-count": ("keyword-count",),
}

ERROR_ASSERTIONS = {
    "structure:kind", "structure:sections", "structure:counts", "structure:uniqueness",
    "rel:alpha-baseline", "rel:alpha-practice", "rel:integrity", "rel:competency-levels",
    "rel:redeclaration",
    "xref:activity-alpha", "xref:activity-wp", "xref:activity-persona", "xref:lod-alpha",
    "xref:pattern", "xref:citation", "xref:narrative-type",
    "bref:focus", "bref:alpha", "bref:activityspace", "bref:competency",
    "bref:narrativetype", "bref:alias",
    "rel:contributes-to-state",
    "schema:valid", "schema:baseline-refs", "schema:integrity",
}

ASSERTION_TEXTS = {
    "files:analysis": "Phase 1 analysis report exists",
    "files:distillation": "Phase 1.5 distillation exists",
    "files:mapping": "Phase 2 mapping guide exists",
    "files:json": "Output JSON exists",
    "phase1:section-count": "Analysis has >= 8 top-level sections",
    "phase1:required-sections": "All 8 required sections present",
    "phase1:subsection-count": ">= 5 numbered subsections",
    "phase1:citations": "Sufficient source references documented",
    "phase1:perspectives": "Four-perspective analysis coverage",
    "phase1:relationships": "Inter-concern relationships documented",
    "phase1.5:required-sections": "All 7 required sections present",
    "phase1.5:focuses": "2-4 focuses defined",
    "phase1.5:concerns": "8-15 essential concerns distilled",
    "phase1.5:activity-types": "6-12 activity types generalized",
    "phase1.5:competencies": "5-10 competencies defined",
    "phase1.5:competency-levels": "Each competency has exactly 5 levels",
    "phase1.5:narratives": "3-5 narrative frameworks defined",
    "phase1.5:coverage-table": "Coverage validation table present",
    "phase2:section-count": "Mapping has >= 7 top-level sections",
    "phase2:required-sections": "All 7 required sections present",
    "phase2:activities": ">= 5 activities mapped",
    "phase2:work-products": ">= 3 work products mapped",
    "phase2:alphas": ">= 3 alphas mapped",
    "phase2:patterns": ">= 1 pattern mapped",
    "phase2:delineation": "Delineation analysis present",
    "phase2:primary-alpha": "Primary alpha documented",
    "phase2:keyword-content": "Keywords section has 10-20 items",
    "phase2:pattern-construction": "Four-pass pattern construction evidence",
    "phase2:narrative-format": "Structured narrative format used",
    "schema:valid": "JSON validates against schema with 0 errors",
    "schema:baseline-refs": "All baseline references resolve",
    "schema:integrity": "Internal cross-reference integrity",
    "structure:kind": "Correct kind discriminator",
    "structure:sections": "All required sections present",
    "structure:counts": "Element counts in valid range",
    "structure:uniqueness": "All element names globally unique",
    "rel:alpha-baseline": "Baseline alphas: no contributesTo, have relatesTo",
    "rel:alpha-practice": "All new alphas have contributesTo",
    "rel:integrity": "relatesTo references resolve",
    "rel:competency-levels": "Competency level names match baseline",
    "rel:redeclaration": "Redeclared alphas preserve baseline structure",
    "xref:activity-alpha": "Activity to alpha/state references resolve",
    "xref:activity-wp": "Activity to work product references resolve",
    "xref:activity-persona": "Activity to persona group references resolve",
    "xref:lod-alpha": "LOD to alpha/state references resolve",
    "xref:pattern": "Pattern view references resolve",
    "xref:citation": "citationNames references resolve",
    "xref:narrative-type": "narrativeTypeName references resolve",
    "bref:focus": "focusName references resolve to baseline",
    "bref:alpha": "contributesTo references resolve to baseline",
    "bref:activityspace": "activitySpaceName references resolve",
    "bref:competency": "competency/competencyLevel names resolve",
    "bref:narrativetype": "narrativeTypeName references resolve",
    "bref:alias": "Alias targets resolve to baseline elements",
    "qual:narrative-citations": "All narratives have citationNames",
    "qual:narrative-placement": "Narratives on correct elements",
    "qual:narrative-self-ref": "No template-type self-referencing",
    "qual:narrative-context-len": "Narrative contexts 1-3 sentences",
    "qual:narrative-self-contain": "No heading-dependent fragments",
    "qual:checklist-names": "No truncated/low-quality checklist names",
    "qual:lod-naming": "Content-maturity LOD names",
    "qual:evidence-coverage": "Alpha states have supporting LODs",
    "qual:asset-coverage": "Elements have icon assets",
    "qual:pattern-coverage": "Patterns cover all practice alphas",
    "qual:narrative-uniqueness": "No duplicate narrative names",
    "rel:mapsto-naming": "mapsTo variant names omit parent type",
    "rel:contributes-to-state": "contributesToState references valid parent states",
    "qual:narrative-structure": "Narratives have narrativeTypeName and narrativeContexts",
    "qual:description-length": "Descriptions within word limits",
    "qual:activity-distinctness": "Activity names differ from ActivitySpace names",
    "coverage:alpha-states": "Each alpha has >= 3 states",
    "coverage:wp-lods": "Each work product has >= 2 LODs",
    "coverage:activity-gap": "Alpha states have supporting activities",
    "qual:alias-uniqueness": "One alias per element maximum",
    "qual:alias-isolation": "Alias names not in structural references",
    "qual:keyword-count": "Keywords count within 10-20 range",
}


def make_assertion(assertion_id, passed, evidence, phase=None):
    severity = "error" if assertion_id in ERROR_ASSERTIONS else "warn"
    return {
        "id": assertion_id,
        "text": ASSERTION_TEXTS.get(assertion_id, assertion_id),
        "phase": phase,
        "passed": passed,
        "severity": severity,
        "evidence": evidence,
    }


def discover_files(directory):
    d = Path(directory)
    files = {
        "analysis": None,
        "distillation": None,
        "mapping": None,
        "json_files": [],
    }
    analysis = d / "01-analysis-report.md"
    if analysis.exists():
        files["analysis"] = str(analysis)
    distillation = d / "01.5-distilled-essentials.md"
    if distillation.exists():
        files["distillation"] = str(distillation)
    mapping = d / "02-mapping-guide.md"
    if mapping.exists():
        files["mapping"] = str(mapping)

    for f in sorted(d.glob("*.json")):
        name = f.name
        if name.startswith("_") or name.startswith("backup-"):
            continue
        if name in ("grading.json", "benchmark.json", "timing.json"):
            continue
        files["json_files"].append(str(f))
    return files


def auto_discover_baseline(json_files):
    """Try to resolve baseline path from practice JSON's baselinePracticeName."""
    import re as _re
    project_root = UTILS_DIR.parent
    for jf in json_files:
        try:
            data = load_json(jf, exit_on_error=False)
            bl_name = data.get("baselinePracticeName")
            if bl_name:
                slug = _re.sub(r'[^a-z0-9]+', '-', bl_name.lower()).strip('-')
                candidate = project_root / "baselines" / slug / f"{slug}.json"
                if candidate.exists():
                    return str(candidate)
        except Exception:
            continue
    return None


def auto_discover_schema():
    """Return schema path if deps/language.schema.json exists."""
    candidate = UTILS_DIR.parent / "deps" / "language.schema.json"
    return str(candidate) if candidate.exists() else None


def word_count(path):
    with open(path, "r") as f:
        return len(f.read().split())


def run_tool(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(UTILS_DIR.parent))
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
    return None


def eval_file_existence(files, kind):
    results = []
    if files["analysis"]:
        wc = word_count(files["analysis"])
        results.append(make_assertion("files:analysis", True,
                                      f"01-analysis-report.md found ({wc:,} words)", phase=1))
    else:
        results.append(make_assertion("files:analysis", False,
                                      "01-analysis-report.md not found", phase=1))

    if kind == "practiceBaseline":
        if files["distillation"]:
            wc = word_count(files["distillation"])
            results.append(make_assertion("files:distillation", True,
                                          f"01.5-distilled-essentials.md found ({wc:,} words)", phase=1.5))
        else:
            results.append(make_assertion("files:distillation", False,
                                          "01.5-distilled-essentials.md not found", phase=1.5))

    if files["mapping"]:
        wc = word_count(files["mapping"])
        results.append(make_assertion("files:mapping", True,
                                      f"02-mapping-guide.md found ({wc:,} words)", phase=2))
    else:
        results.append(make_assertion("files:mapping", False,
                                      "02-mapping-guide.md not found", phase=2))

    if files["json_files"]:
        names = [Path(f).name for f in files["json_files"]]
        results.append(make_assertion("files:json", True,
                                      f"JSON found: {', '.join(names)}", phase=3))
    else:
        results.append(make_assertion("files:json", False,
                                      "No output JSON found", phase=3))

    return results


def eval_phase_1(analysis_path):
    output = run_tool(["python3", "utils/validate-phase-output.py", analysis_path, "--phase", "1"])
    if not output:
        return [make_assertion("phase1:section-count", False, "Phase 1 validation failed to run", phase=1)]

    results = []
    checks = output.get("checks", [])

    section_count = next((c for c in checks if c.get("check") == "section_count"), None)
    if section_count:
        results.append(make_assertion("phase1:section-count", section_count["pass"],
                                      f"{section_count.get('actual', '?')} sections found", phase=1))

    section_checks = [c for c in checks if c.get("check", "").startswith("section_exists:")]
    all_found = all(c.get("pass", False) for c in section_checks)
    found = sum(1 for c in section_checks if c.get("pass", False))
    missing = [c["check"].split(":", 1)[1] for c in section_checks if not c.get("pass", False)]
    evidence = f"{found}/{len(section_checks)} sections found"
    if missing:
        evidence += f"; missing: {', '.join(missing)}"
    results.append(make_assertion("phase1:required-sections", all_found, evidence, phase=1))

    subsection = next((c for c in checks if c.get("check") == "numbered_subsections"), None)
    if subsection:
        results.append(make_assertion("phase1:subsection-count", subsection["pass"],
                                      f"{subsection.get('actual', '?')} numbered subsections", phase=1))

    citation = next((c for c in checks if c.get("check") == "citation_count"), None)
    if citation:
        results.append(make_assertion("phase1:citations", citation["pass"],
                                      f"{citation.get('actual', '?')} source references", phase=1))

    perspective = next((c for c in checks if c.get("check") == "perspective_balance"), None)
    if perspective:
        missing = perspective.get("missing", [])
        evidence = f"{perspective.get('actual', '?')}/4 perspectives"
        if missing:
            evidence += f"; missing: {', '.join(missing)}"
        results.append(make_assertion("phase1:perspectives", perspective["pass"],
                                      evidence, phase=1))

    relationships = next((c for c in checks if c.get("check") == "relationship_documentation"), None)
    if relationships:
        results.append(make_assertion("phase1:relationships", relationships["pass"],
                                      f"{relationships.get('actual', '?')} relationship mentions", phase=1))

    return results


def eval_phase_1_5(distillation_path):
    output = run_tool(["python3", "utils/validate-phase-output.py", distillation_path, "--phase", "1.5"])
    if not output:
        return [make_assertion("phase1.5:required-sections", False,
                               "Phase 1.5 validation failed to run", phase=1.5)]

    results = []
    checks = output.get("checks", [])

    section_checks = [c for c in checks if c.get("check", "").startswith("section_exists:")]
    all_found = all(c.get("pass", False) for c in section_checks)
    found = sum(1 for c in section_checks if c.get("pass", False))
    results.append(make_assertion("phase1.5:required-sections", all_found,
                                  f"{found}/{len(section_checks)} sections found", phase=1.5))

    check_map = {
        "focus_count": ("phase1.5:focuses", "focuses"),
        "concern_count": ("phase1.5:concerns", "concerns"),
        "activity_type_count": ("phase1.5:activity-types", "activity types"),
        "competency_count": ("phase1.5:competencies", "competencies"),
        "narrative_count": ("phase1.5:narratives", "narrative frameworks"),
        "coverage_table": ("phase1.5:coverage-table", "coverage table"),
    }
    for check_name, (assertion_id, label) in check_map.items():
        c = next((c for c in checks if c.get("check") == check_name), None)
        if c:
            actual = c.get("actual", "present" if c.get("pass") else "missing")
            expected = c.get("expected", "")
            evidence = f"{actual} {label}" + (f" (expected {expected})" if expected else "")
            results.append(make_assertion(assertion_id, c["pass"], evidence, phase=1.5))

    level_checks = [c for c in checks if c.get("check", "").startswith("competency_level:")]
    if level_checks:
        all_pass = all(c.get("pass", False) for c in level_checks)
        failures = [c["check"].split(":")[1] for c in level_checks if not c.get("pass", False)]
        evidence = "All levels correct" if all_pass else f"Mismatched levels: {', '.join(failures)}"
        results.append(make_assertion("phase1.5:competency-levels", all_pass, evidence, phase=1.5))

    return results


def eval_phase_2(mapping_path):
    output = run_tool(["python3", "utils/validate-phase-output.py", mapping_path, "--phase", "2"])
    if not output:
        return [make_assertion("phase2:section-count", False,
                               "Phase 2 validation failed to run", phase=2)]

    results = []
    checks = output.get("checks", [])

    section_count = next((c for c in checks if c.get("check") == "section_count"), None)
    if section_count:
        results.append(make_assertion("phase2:section-count", section_count["pass"],
                                      f"{section_count.get('actual', '?')} sections found", phase=2))

    section_checks = [c for c in checks if c.get("check", "").startswith("section_exists:")]
    all_found = all(c.get("pass", False) for c in section_checks)
    found = sum(1 for c in section_checks if c.get("pass", False))
    results.append(make_assertion("phase2:required-sections", all_found,
                                  f"{found}/{len(section_checks)} sections found", phase=2))

    check_map = {
        "activity_count": ("phase2:activities", "activities"),
        "work_product_count": ("phase2:work-products", "work products"),
        "alpha_count": ("phase2:alphas", "alphas"),
        "pattern_count": ("phase2:patterns", "patterns"),
    }
    for check_name, (assertion_id, label) in check_map.items():
        c = next((c for c in checks if c.get("check") == check_name), None)
        if c:
            results.append(make_assertion(assertion_id, c["pass"],
                                          f"{c.get('actual', '?')} {label} mapped", phase=2))

    phase2_check_map = {
        "delineation_analysis": ("phase2:delineation", "Delineation analysis"),
        "primary_alpha_documented": ("phase2:primary-alpha", "Primary alpha"),
        "keyword_content": ("phase2:keyword-content", "keywords"),
        "pattern_construction": ("phase2:pattern-construction", "Pattern construction"),
        "narrative_format": ("phase2:narrative-format", "Structured narratives"),
    }
    for check_name, (assertion_id, label) in phase2_check_map.items():
        c = next((c for c in checks if c.get("check") == check_name), None)
        if c:
            actual = c.get("actual", "present" if c.get("pass") else "missing")
            evidence = f"{actual} {label}" if isinstance(actual, int) else f"{label}: {actual}"
            results.append(make_assertion(assertion_id, c["pass"], evidence, phase=2))

    return results


def eval_phase_3(json_path, baseline=None, schema=None, parents=None):
    results = []

    cmd = ["python3", "utils/assess-practice.py", json_path]
    if baseline:
        cmd.extend(["--baseline", baseline])
    if schema:
        cmd.extend(["--schema", schema])
    if parents:
        for p in parents:
            cmd.extend(["--parent", p])
    output = run_tool(cmd)

    if not output:
        return [make_assertion("schema:valid", False, "Assessment failed to run", phase=3)]

    issues = output.get("issues", [])
    err_cats = Counter(i["category"] for i in issues if i["severity"] == "error")
    warn_cats = Counter(i["category"] for i in issues if i["severity"] == "warning")

    kind = output.get("kind", "practice")

    for assertion_id, categories in ASSESS_CATEGORY_MAP.items():
        if assertion_id.startswith("bref:") and kind == "practiceBaseline":
            continue
        if assertion_id == "rel:alpha-baseline" and kind != "practiceBaseline":
            continue
        if assertion_id == "rel:alpha-practice" and kind == "practiceBaseline":
            continue
        if assertion_id.startswith("bref:") and not baseline:
            continue
        if assertion_id == "rel:competency-levels" and not baseline:
            continue
        if assertion_id == "rel:redeclaration" and not baseline and not parents:
            continue

        error_count = sum(err_cats.get(cat, 0) for cat in categories)
        warn_count = sum(warn_cats.get(cat, 0) for cat in categories)

        if assertion_id in ERROR_ASSERTIONS:
            passed = error_count == 0
            if error_count > 0:
                evidence = f"{error_count} error(s) in {', '.join(categories)}"
            elif warn_count > 0:
                evidence = f"0 errors, {warn_count} warning(s)"
            else:
                evidence = "0 issues"
        else:
            passed = warn_count == 0 and error_count == 0
            total = error_count + warn_count
            evidence = f"{total} issue(s)" if total > 0 else "0 issues"

        results.append(make_assertion(assertion_id, passed, evidence, phase=3))

    schema_report = output.get("schemaValidation")
    if schema and schema_report:
        summary = schema_report.get("summary", {})
        schema_errors = summary.get("error_count", 0)
        results.append(make_assertion("schema:valid",
                                      schema_errors == 0,
                                      f"{schema_errors} schema error(s)", phase=3))
    elif schema:
        results.append(make_assertion("schema:valid", False,
                                      "Schema validation did not run", phase=3))

    return results


def compute_summary(assertion_results):
    total = len(assertion_results)
    passed = sum(1 for a in assertion_results if a["passed"])
    failed = total - passed
    warnings = sum(1 for a in assertion_results if not a["passed"] and a["severity"] == "warn")
    errors = sum(1 for a in assertion_results if not a["passed"] and a["severity"] == "error")

    error_assertions = [a for a in assertion_results if a["severity"] == "error"]
    error_total = len(error_assertions)
    error_passed = sum(1 for a in error_assertions if a["passed"])

    by_phase = {}
    for a in assertion_results:
        p = str(a.get("phase", "?"))
        if p not in by_phase:
            by_phase[p] = {"passed": 0, "total": 0}
        by_phase[p]["total"] += 1
        if a["passed"]:
            by_phase[p]["passed"] += 1

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "warnings": warnings,
        "total": total,
        "pass_rate": round(passed / total, 2) if total else 1.0,
        "error_pass_rate": round(error_passed / error_total, 2) if error_total else 1.0,
        "by_phase": by_phase,
    }


def eval_directory(directory, baseline=None, schema=None, parent=None, phase_filter=None):
    files = discover_files(directory)

    kind = None
    if files["json_files"]:
        for jf in files["json_files"]:
            try:
                data = load_json(jf, exit_on_error=False)
                kind = detect_kind(data)
                name = data.get("name", Path(jf).stem)
                break
            except Exception:
                continue

    if kind is None:
        kind = "practiceBaseline" if "baselines" in str(directory) else "practice"
        name = Path(directory).name

    # Auto-discover baseline and schema if not provided
    if not baseline and files["json_files"]:
        baseline = auto_discover_baseline(files["json_files"])
    if not schema:
        schema = auto_discover_schema()

    phases = set()
    if phase_filter is not None:
        phases.add(phase_filter)
    else:
        if files["analysis"]:
            phases.add(1)
        if files["distillation"] and kind == "practiceBaseline":
            phases.add(1.5)
        if files["mapping"]:
            phases.add(2)
        if files["json_files"]:
            phases.add(3)

    assertion_results = []

    if phase_filter is None or phase_filter in (1, 1.5, 2, 3):
        assertion_results.extend(eval_file_existence(files, kind))

    if 1 in phases and files["analysis"]:
        assertion_results.extend(eval_phase_1(files["analysis"]))
    if 1.5 in phases and files["distillation"]:
        assertion_results.extend(eval_phase_1_5(files["distillation"]))
    if 2 in phases and files["mapping"]:
        assertion_results.extend(eval_phase_2(files["mapping"]))
    if 3 in phases and files["json_files"]:
        for jf in files["json_files"]:
            assertion_results.extend(eval_phase_3(jf, baseline, schema, [parent] if parent else None))

    summary = compute_summary(assertion_results)

    return {
        "directory": str(directory),
        "kind": kind,
        "name": name,
        "phases_evaluated": sorted(phases),
        "assertion_results": assertion_results,
        "summary": summary,
    }


def run_batch_evals(evals_path, eval_id=None):
    evals_data = load_json(evals_path)
    skill_name = evals_data.get("skill_name", "unknown")
    default_baseline = evals_data.get("baseline_default")
    default_schema = evals_data.get("schema")

    test_cases = evals_data.get("evals", [])
    if eval_id is not None:
        test_cases = [t for t in test_cases if t.get("id") == eval_id]
        if not test_cases:
            print(json.dumps({"error": f"No eval with id={eval_id}"}), file=sys.stderr)
            sys.exit(1)

    results = []
    for tc in test_cases:
        directory = tc.get("directory", "")
        baseline = tc.get("baseline", default_baseline)
        schema = tc.get("schema", default_schema)
        parent = tc.get("parent")

        if not Path(directory).is_dir():
            results.append({
                "id": tc.get("id"),
                "name": tc.get("name", "?"),
                "error": f"Directory not found: {directory}",
            })
            continue

        grading = eval_directory(directory, baseline=baseline, schema=schema, parent=parent)
        summary = grading["summary"]
        results.append({
            "id": tc.get("id"),
            "name": tc.get("name", "?"),
            "pass_rate": summary["pass_rate"],
            "error_pass_rate": summary["error_pass_rate"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "errors": summary["errors"],
            "warnings": summary["warnings"],
            "total": summary["total"],
        })

    valid_results = [r for r in results if "error" not in r]
    aggregate = {}
    if valid_results:
        aggregate = {
            "mean_pass_rate": round(sum(r["pass_rate"] for r in valid_results) / len(valid_results), 2),
            "mean_error_pass_rate": round(sum(r["error_pass_rate"] for r in valid_results) / len(valid_results), 2),
        }
        worst = min(valid_results, key=lambda r: r["pass_rate"])
        aggregate["worst_eval"] = worst["name"]

    return {
        "skill": skill_name,
        "eval_count": len(test_cases),
        "results": results,
        "aggregate": aggregate,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate skill output quality using agentskills.io-compatible grading"
    )
    parser.add_argument("directory", nargs="?",
                        help="Output directory to evaluate (practice or baseline)")
    parser.add_argument("--baseline", help="Baseline practice JSON for extension practice validation")
    parser.add_argument("--parent", help="Parent baseline JSON for child baseline validation")
    parser.add_argument("--schema", help="Language schema JSON for schema validation")
    parser.add_argument("--phase", type=float, choices=[1, 1.5, 2, 3],
                        help="Evaluate specific phase only")
    parser.add_argument("--output", "-o", help="Write grading.json to path (default: stdout)")
    parser.add_argument("--summary", action="store_true", help="Compact pass/fail counts only")
    parser.add_argument("--show-failed", action="store_true",
                        help="Show only failed assertions with details")
    parser.add_argument("--one-line", action="store_true",
                        help="Print single-line summary (e.g. PASS 52/56 (100%% errors))")
    parser.add_argument("--evals", metavar="EVALS_JSON",
                        help="Run batch evals from evals.json file")
    parser.add_argument("--eval-id", type=int, help="Run specific eval by ID (with --evals)")
    parser.add_argument("--specs", metavar="SPECS_JSON",
                        help="Annotate assertions with spec IDs from specs-index.json")
    args = parser.parse_args()

    specs_data = None
    cat_to_specs = {}
    if args.specs:
        specs_data, cat_to_specs = load_specs_index(args.specs)

    if args.evals:
        result = run_batch_evals(args.evals, eval_id=args.eval_id)
    elif args.directory:
        if not Path(args.directory).is_dir():
            print(json.dumps({"error": f"Not a directory: {args.directory}"}), file=sys.stderr)
            sys.exit(1)
        result = eval_directory(
            args.directory,
            baseline=args.baseline,
            schema=args.schema,
            parent=args.parent,
            phase_filter=args.phase,
        )
    else:
        parser.print_help()
        sys.exit(1)

    if cat_to_specs and not args.evals:
        annotate_with_specs(result.get("assertion_results", []), cat_to_specs)
        result["specs_source"] = str(args.specs)

    if args.one_line and not args.evals:
        summary = result.get("summary", {})
        passed = summary.get("passed", 0)
        total = summary.get("total", 0)
        error_rate = summary.get("error_pass_rate", 0)
        failed_warns = sum(1 for a in result.get("assertion_results", [])
                          if not a["passed"] and a["severity"] == "warn")
        name = result.get("name", "unknown")
        status = "PASS" if error_rate == 1.0 else "FAIL"
        warn_str = f" ({failed_warns} warnings)" if failed_warns else ""
        print(f"{status} {passed}/{total} ({error_rate:.0%} errors){warn_str} — {name}")
        sys.exit(0 if error_rate == 1.0 else 1)

    if args.show_failed and not args.evals:
        failed = [a for a in result.get("assertion_results", []) if not a["passed"]]
        if not failed:
            output = json.dumps({"status": "all_passed", "total": len(result.get("assertion_results", []))}, indent=2)
        else:
            output = json.dumps({
                "failed_count": len(failed),
                "error_count": sum(1 for a in failed if a["severity"] == "error"),
                "warning_count": sum(1 for a in failed if a["severity"] == "warn"),
                "failed": [
                    {
                        "id": a["id"],
                        "severity": a["severity"],
                        "text": a["text"],
                        "evidence": a["evidence"],
                        "phase": a.get("phase"),
                    }
                    for a in failed
                ],
            }, indent=2)
    elif args.summary and not args.evals:
        summary = result.get("summary", {})
        summary["directory"] = result.get("directory")
        summary["kind"] = result.get("kind")
        summary["name"] = result.get("name")
        failed = [a for a in result.get("assertion_results", []) if not a["passed"]]
        if failed:
            summary["failed_assertions"] = [
                {"id": a["id"], "severity": a["severity"], "evidence": a["evidence"]}
                for a in failed
            ]
        output = json.dumps(summary, indent=2)
    else:
        output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
            f.write("\n")
        print(f"Wrote {args.output}")
    else:
        print(output)

    if not args.evals:
        summary = result.get("summary", {})
        sys.exit(0 if summary.get("error_pass_rate", 0) == 1.0 else 1)


if __name__ == "__main__":
    main()
