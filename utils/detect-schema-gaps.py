#!/usr/bin/env python3
"""Detect schema feature gaps in practice JSON files.

When the Practice Language schema evolves, existing practices may be missing
newer features (outcomes, patternGroups, checklist priorities, etc.). This
utility reads a practice JSON, compares its schemaVersion to the current
schema, and reports which features are missing or incomplete.

Usage:
    python3 utils/detect-schema-gaps.py <practice>.json [--schema deps/language.schema.json] [--json]
    python3 utils/detect-schema-gaps.py --dir <dir>/ [--schema deps/language.schema.json] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, detect_kind, get_schema_version


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def parse_semver(version_str):
    """Parse a semver string into (major, minor, patch) tuple."""
    parts = (version_str or "0.0.0").split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return 0, 0, 0


def major_distance(v1, v2):
    """Return the absolute major-version distance between two semver strings."""
    return abs(parse_semver(v1)[0] - parse_semver(v2)[0])


# ---------------------------------------------------------------------------
# Gap detection helpers
# ---------------------------------------------------------------------------

def collect_all_checklists(data):
    """Collect all checklist items from alpha states and work product LODs."""
    items = []
    for alpha in data.get("alphas", []):
        for state in alpha.get("states", []):
            items.extend(state.get("checklist", []))
    for wp in data.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            items.extend(lod.get("checklist", []))
    return items


def get_declared_dependencies(data):
    """Return the set of document names this document depends on."""
    deps = set()
    bpn = data.get("baselinePracticeName")
    if bpn:
        deps.add(bpn)
    for name in data.get("practiceDependencyNames", []):
        deps.add(name)
    for name in data.get("practiceNames", []):
        deps.add(name)
    for name in data.get("baselinePracticeNames", []):
        deps.add(name)
    return deps


def get_covered_dependencies(data):
    """Return the set of document names covered by dependencyVersions."""
    covered = set()
    for entry in data.get("dependencyVersions", []):
        doc_name = entry.get("documentName")
        if doc_name:
            covered.add(doc_name)
    return covered


# ---------------------------------------------------------------------------
# Feature checks — each returns a gap dict or None
# ---------------------------------------------------------------------------

def check_outcomes(data, kind):
    """Check outcomes: present? has objectiveContributions? has metricContributions?"""
    outcomes = data.get("outcomes", [])
    if not outcomes:
        return {
            "feature": "outcomes",
            "status": "missing",
            "detail": "No outcomes array",
        }

    issues = []
    for o in outcomes:
        name = o.get("name", "?")
        has_obj = bool(o.get("objectiveContributions"))
        has_met = bool(o.get("metricContributions"))
        if kind == "practice" and not has_obj and not has_met:
            issues.append(name)

    if issues:
        return {
            "feature": "outcomes",
            "status": "incomplete",
            "detail": f"{len(issues)} outcome(s) lack contribution chains: {', '.join(issues)}",
        }
    return None


def check_pattern_groups(data):
    """Check patternGroups: present? non-empty entries?"""
    pgs = data.get("patternGroups", [])
    if not pgs:
        return {
            "feature": "patternGroups",
            "status": "missing",
            "detail": "No patternGroups array",
        }

    empty = [pg.get("name", "?") for pg in pgs if not pg.get("entries")]
    if empty:
        return {
            "feature": "patternGroups",
            "status": "incomplete",
            "detail": f"{len(empty)} group(s) with empty entries: {', '.join(empty)}",
        }
    return None


def check_checklist_priority(data):
    """Check what percentage of checklist items have a priority field."""
    items = collect_all_checklists(data)
    if not items:
        return None  # No checklists at all — not a gap per se

    with_priority = sum(1 for c in items if c.get("priority"))
    pct = round(with_priority / len(items) * 100, 1)

    if pct == 0:
        return {
            "feature": "checklistPriority",
            "status": "incomplete",
            "detail": f"0% of {len(items)} checklist items have priority",
        }
    if pct < 100:
        return {
            "feature": "checklistPriority",
            "status": "incomplete",
            "detail": f"{pct}% of {len(items)} checklist items have priority ({with_priority}/{len(items)})",
        }
    return None


def check_references(data, kind):
    """Check references: present? has links?"""
    # References are only valid on practice and practiceInMethod, not baseline or method
    if kind not in ("practice",):
        return None

    refs = data.get("references", [])
    if not refs:
        return {
            "feature": "references",
            "status": "missing",
            "detail": "No references array",
        }

    no_links = [r.get("name", "?") for r in refs if not r.get("links")]
    if no_links:
        return {
            "feature": "references",
            "status": "incomplete",
            "detail": f"{len(no_links)} reference(s) without links: {', '.join(no_links[:5])}",
        }
    return None


def check_acknowledgements(data):
    """Check acknowledgements: present?"""
    if not data.get("acknowledgements"):
        return {
            "feature": "acknowledgements",
            "status": "missing",
            "detail": "No acknowledgements array",
        }
    return None


def check_dependency_versions(data):
    """Check dependencyVersions: present? covers all declared dependencies?"""
    declared = get_declared_dependencies(data)
    if not declared:
        return None  # Nothing to declare versions for

    dep_versions = data.get("dependencyVersions", [])
    if not dep_versions:
        return {
            "feature": "dependencyVersions",
            "status": "missing",
            "detail": f"No dependencyVersions array (declared: {', '.join(sorted(declared))})",
        }

    covered = get_covered_dependencies(data)
    missing = declared - covered
    if missing:
        return {
            "feature": "dependencyVersions",
            "status": "incomplete",
            "detail": f"Missing: {', '.join(sorted(missing))}",
        }

    # Check for empty versionRange
    empty_range = [
        e.get("documentName", "?")
        for e in dep_versions
        if not e.get("versionRange")
    ]
    if empty_range:
        return {
            "feature": "dependencyVersions",
            "status": "incomplete",
            "detail": f"Empty versionRange: {', '.join(empty_range)}",
        }
    return None


def check_gherkin_structures(data, kind):
    """Check gherkin structures: states with background, activities with test/examples."""
    issues = []

    # Check state backgrounds
    states_total = 0
    states_with_bg = 0
    for alpha in data.get("alphas", []):
        for state in alpha.get("states", []):
            states_total += 1
            if state.get("background"):
                states_with_bg += 1

    if states_total > 0 and states_with_bg == 0:
        issues.append(f"0/{states_total} states have background")

    # Check activity test/examples (only for practices, not baselines)
    if kind == "practice":
        activities_total = len(data.get("activities", []))
        activities_with_test = sum(
            1 for a in data.get("activities", []) if a.get("test")
        )
        activities_with_examples = sum(
            1 for a in data.get("activities", []) if a.get("examples")
        )

        if activities_total > 0 and activities_with_test == 0:
            issues.append(f"0/{activities_total} activities have test")
        if activities_total > 0 and activities_with_examples == 0:
            issues.append(f"0/{activities_total} activities have examples")

    if issues:
        return {
            "feature": "gherkinStructures",
            "status": "incomplete",
            "detail": "; ".join(issues),
        }
    return None


def check_expected_metrics(data):
    """Check expectedMetrics: present on any work product?"""
    wps = data.get("workProducts", [])
    if not wps:
        return None

    with_metrics = sum(1 for wp in wps if wp.get("expectedMetrics"))
    if with_metrics == 0:
        return {
            "feature": "expectedMetrics",
            "status": "missing",
            "detail": f"0/{len(wps)} work products define expectedMetrics",
        }
    return None


def check_schema_version(data, latest_version):
    """Check schemaVersion: is it set? does it match latest?"""
    current = data.get("schemaVersion", "")
    if not current:
        return {
            "feature": "schemaVersion",
            "status": "missing",
            "detail": f"No schemaVersion set (latest: {latest_version})",
        }
    if current != latest_version:
        return {
            "feature": "schemaVersion",
            "status": "outdated",
            "detail": f"Document: {current}, latest: {latest_version}",
        }
    return None


# ---------------------------------------------------------------------------
# Suggested update mode
# ---------------------------------------------------------------------------

AUTO_FIX_FEATURES = {"checklistPriority", "dependencyVersions", "schemaVersion"}

def suggest_update_mode(gaps, current_version, latest_version):
    """Determine recommended update mode based on gap severity.

    Returns:
        "none"     — no gaps
        "auto-fix" — only mechanical/auto-fixable gaps
        "remap"    — structural gaps requiring re-mapping
    """
    if not gaps:
        return "none"

    # Major version distance >= 2 → remap
    if major_distance(current_version, latest_version) >= 2:
        return "remap"

    gap_features = {g["feature"] for g in gaps}

    # Structural features that need re-mapping
    remap_features = {"outcomes", "patternGroups", "references", "gherkinStructures", "expectedMetrics"}
    if gap_features & remap_features:
        return "remap"

    # Everything else is auto-fixable
    return "auto-fix"


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_gaps(data, latest_version):
    """Run all gap checks and return structured result."""
    kind = detect_kind(data)
    current_version = data.get("schemaVersion", "")

    gaps = []
    for check_fn, args in [
        (check_outcomes, (data, kind)),
        (check_pattern_groups, (data,)),
        (check_checklist_priority, (data,)),
        (check_references, (data, kind)),
        (check_acknowledgements, (data,)),
        (check_dependency_versions, (data,)),
        (check_gherkin_structures, (data, kind)),
        (check_expected_metrics, (data,)),
        (check_schema_version, (data, latest_version)),
    ]:
        gap = check_fn(*args)
        if gap is not None:
            gaps.append(gap)

    return {
        "name": data.get("name", "(unknown)"),
        "kind": kind,
        "currentSchemaVersion": current_version or "(not set)",
        "latestSchemaVersion": latest_version,
        "gaps": gaps,
        "gapCount": len(gaps),
        "suggestedUpdateMode": suggest_update_mode(gaps, current_version, latest_version),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

STATUS_SYMBOLS = {
    "missing": "X",
    "incomplete": "~",
    "outdated": "!",
}


def print_human_readable(result):
    """Print a human-readable gap report."""
    print(f"{result['name']} ({result['kind']})")
    print(f"  schema: {result['currentSchemaVersion']} -> latest {result['latestSchemaVersion']}")
    print()

    if not result["gaps"]:
        print("  No gaps detected.")
    else:
        print(f"  {result['gapCount']} gap(s) found:")
        print()
        for gap in result["gaps"]:
            symbol = STATUS_SYMBOLS.get(gap["status"], "?")
            print(f"  [{symbol}] {gap['feature']} ({gap['status']})")
            print(f"      {gap['detail']}")
        print()

    mode = result["suggestedUpdateMode"]
    label = {
        "none": "No update needed",
        "auto-fix": "Auto-fixable (checklist priority, dependency versions, schema version)",
        "remap": "Re-mapping recommended (structural features missing)",
    }.get(mode, mode)
    print(f"  Suggested update mode: {mode} -- {label}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Detect schema feature gaps in practice JSON files"
    )
    parser.add_argument("json_file", nargs="?", help="Path to practice JSON file")
    parser.add_argument("--dir", help="Process all practice JSON files in directory")
    parser.add_argument(
        "--schema",
        default=None,
        help="Path to language.schema.json (default: deps/language.schema.json)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.json_file and not args.dir:
        parser.error("Either json_file or --dir is required")

    # Resolve schema path
    schema_path = None
    if args.schema:
        schema_path = Path(args.schema)
    else:
        # Default: deps/language.schema.json relative to project root
        project_root = Path(__file__).resolve().parent.parent
        schema_path = project_root / "deps" / "language.schema.json"

    latest_version = get_schema_version(schema_path)
    if not latest_version:
        print(
            json.dumps({"error": f"Could not read schema version from {schema_path}"})
        )
        sys.exit(1)

    # Collect files
    files = []
    if args.dir:
        dir_path = Path(args.dir)
        files = sorted(
            f
            for f in dir_path.glob("*.json")
            if not f.name.startswith("_")
            and not f.name.startswith("change-request")
            and "backup" not in str(f)
        )
    else:
        files = [Path(args.json_file)]

    results = []
    for f in files:
        data = load_json(f)
        kind = detect_kind(data)
        if kind not in ("practice", "method", "practiceBaseline"):
            continue
        result = analyze_gaps(data, latest_version)
        result["_filePath"] = str(f)
        results.append(result)

    if args.json:
        output = results[0] if len(results) == 1 else results
        print(json.dumps(output, indent=2))
    else:
        for i, result in enumerate(results):
            if i > 0:
                print("\n" + "=" * 60 + "\n")
            print_human_readable(result)


if __name__ == "__main__":
    main()
