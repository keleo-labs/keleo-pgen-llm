#!/usr/bin/env python3
"""Extract Gherkin-style rule scenarios from SKILL.md files into a specs-index.json.

Parses `### Scenario:` blocks with `@rule:<category>-<NNN>` tags and
Given/When/Then steps. Outputs structured JSON for use by the eval harness
(eval-skill-output.py --specs).

Usage:
    # Extract specs from a skill
    python3 utils/extract-specs.py .claude/skills/generate-method/SKILL.md

    # Write to specific output path
    python3 utils/extract-specs.py .claude/skills/generate-method/SKILL.md \
      -o .claude/skills/generate-method/specs/specs-index.json

    # Include stats
    python3 utils/extract-specs.py .claude/skills/generate-method/SKILL.md --stats

    # Read an index back and list the rules no script can check, for a
    # verification agent's brief
    python3 utils/extract-specs.py \
      --list-manual .claude/skills/generate-method/specs/specs-index.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Scenarios sit at h3 in most skills but at h4 in improve-tooling, which nests
# them under an h3 Feature. Matching only h3 silently extracted nothing from
# that skill -- indistinguishable from a skill with no specs. Accept h3-h6, the
# same latitude verify-mapping-against-specs.py already allows for the same
# reason.
SCENARIO_HEADER_RE = re.compile(
    r"^#{3,6}\s+Scenario:\s+(.+?)\s+\(@rule:([a-z]+-\d{3})\)\s*$"
)

STEP_RE = re.compile(
    r"^-\s+(Given|When|Then|And|But):\s+(.+)$"
)

FEATURE_HEADER_RE = re.compile(
    r"^#{2,4}\s+Feature:\s+(.+)$"
)

VALID_CATEGORIES = {
    "structural", "semantic", "naming", "coverage",
    "narrative", "process", "aliasing", "fidelity",
}

ASSESS_CATEGORY_BRIDGE = {
    "semantic-001": ["practice-alpha"],
    "semantic-002": ["integrity"],
    "semantic-003": ["integrity"],
    "semantic-004": ["integrity"],
    "semantic-005": ["redeclaration-compliance"],
    "semantic-006": ["competency-levels"],
    "semantic-007": ["baseline-alpha"],
    "semantic-008": ["integrity"],
    "semantic-009": ["contributes-to-state"],
    "semantic-010": ["mapsto-naming"],
    "semantic-011": ["baseline-ref-focus", "baseline-ref-alpha", "baseline-ref-activityspace", "baseline-ref-competency", "baseline-ref-narrativetype"],
    "naming-001": ["description-length"],
    "naming-002": ["checklist-quality", "checklist-polarity"],
    "naming-003": ["uniqueness"],
    "naming-004": ["lod-naming"],
    "naming-005": ["activity-name-distinctness"],
    "coverage-001": ["alpha-state-minimum"],
    "coverage-002": ["workproduct-lod-minimum"],
    "coverage-003": ["evidence-coverage"],
    "coverage-004": ["pattern-coverage"],
    "coverage-005": ["activity-state-gap"],
    "narrative-001": ["narrative-structure"],
    "narrative-002": ["narrative-placement"],
    "narrative-003": ["narrative-self-reference"],
    "narrative-004": ["narrative-context-length"],
    "narrative-005": ["narrative-self-containment"],
    "narrative-006": ["narrative-citations"],
    "aliasing-001": ["alias-uniqueness"],
    "aliasing-002": ["alias-isolation"],
    "aliasing-003": ["keyword-count"],
    "structural-001": ["structure"],
    "structural-002": ["structure"],
    "structural-003": ["crossref-pattern"],
    "structural-004": ["crossref-activity-alpha"],
    "structural-005": ["crossref-activity-wp"],
    "process-001": [],
    "process-002": [],
    "process-003": [],
    # create-baseline-method (200-399)
    "structural-201": ["structure"],
    "structural-202": ["structure"],
    "structural-203": ["structure"],
    "structural-204": ["structure"],
    "structural-205": ["structure"],
    "structural-206": ["structure"],
    "semantic-201": ["baseline-alpha"],
    "semantic-202": ["baseline-alpha"],
    "semantic-203": ["integrity"],
    "semantic-204": ["crossref-activity-alpha"],
    "coverage-201": ["alpha-state-minimum"],
    "naming-201": [],
    "naming-202": ["competency-levels"],
    "coverage-202": ["gherkin-structure"],
    "process-201": [],
    "process-202": [],
    "process-203": [],
    # update-method (400-599)
    "process-401": [],
    "process-402": [],
    "process-403": [],
    "process-404": [],
    "process-405": [],
    "process-406": [],
    "process-407": [],
    "process-408": [],
}


def parse_skill_md(path):
    """Parse a SKILL.md file and extract Gherkin scenarios.

    Returns:
        dict with 'skill', 'features', 'scenarios', and 'stats' keys.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    skill_name = None
    for line in lines[:20]:
        m = re.match(r"^name:\s+(.+)$", line.strip())
        if m:
            skill_name = m.group(1).strip()
            break

    features = []
    scenarios = []
    current_feature = None
    current_scenario = None
    last_step_kind = None
    errors = []

    for lineno, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip()

        fm = FEATURE_HEADER_RE.match(line)
        if fm:
            current_feature = fm.group(1).strip()
            features.append(current_feature)
            continue

        sm = SCENARIO_HEADER_RE.match(line)
        if sm:
            if current_scenario:
                scenarios.append(current_scenario)
            name = sm.group(1).strip()
            rule_id = sm.group(2)
            category = rule_id.rsplit("-", 1)[0]
            if category not in VALID_CATEGORIES:
                errors.append(
                    f"Line {lineno}: Unknown category '{category}' in @rule:{rule_id}"
                )
            current_scenario = {
                "id": rule_id,
                "name": name,
                "feature": current_feature,
                "given": [],
                "when": [],
                "then": [],
                "line": lineno,
                "assess_categories": ASSESS_CATEGORY_BRIDGE.get(rule_id, []),
                "automatable": rule_id in ASSESS_CATEGORY_BRIDGE and len(ASSESS_CATEGORY_BRIDGE.get(rule_id, [])) > 0,
            }
            last_step_kind = None
            continue

        if current_scenario:
            step_m = STEP_RE.match(line)
            if step_m:
                keyword = step_m.group(1)
                text = step_m.group(2).strip()
                if keyword in ("And", "But"):
                    keyword = last_step_kind or "Given"
                last_step_kind = keyword
                current_scenario[keyword.lower()].append(text)
            elif line.strip() == "" and current_scenario.get("then"):
                scenarios.append(current_scenario)
                current_scenario = None
                last_step_kind = None

    if current_scenario:
        scenarios.append(current_scenario)

    by_category = {}
    for s in scenarios:
        cat = s["id"].rsplit("-", 1)[0]
        by_category.setdefault(cat, []).append(s["id"])

    ids_seen = {}
    for s in scenarios:
        if s["id"] in ids_seen:
            errors.append(
                f"Duplicate @rule:{s['id']} at lines {ids_seen[s['id']]} and {s['line']}"
            )
        ids_seen[s["id"]] = s["line"]

    stats = {
        "total_scenarios": len(scenarios),
        "total_features": len(features),
        "automatable": sum(1 for s in scenarios if s["automatable"]),
        "manual_only": sum(1 for s in scenarios if not s["automatable"]),
        "by_category": {cat: len(ids) for cat, ids in sorted(by_category.items())},
    }

    result = {
        "skill": skill_name,
        "source": str(path),
        "features": features,
        "scenarios": scenarios,
        "stats": stats,
    }
    if errors:
        result["errors"] = errors

    return result


def list_manual(index_path, as_json=False, category=None):
    """Print the scenarios in an index that no script can check.

    Automatable scenarios are already enforced by assess-practice.py and
    eval-skill-output.py. The manual-only ones are precisely the contract a
    verification agent has to carry, so a brief reads them from here rather
    than restating them and drifting.
    """
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    scenarios = [s for s in index.get("scenarios", []) if not s.get("automatable")]
    if category:
        scenarios = [s for s in scenarios if s["id"].rsplit("-", 1)[0] == category]

    if as_json:
        print(json.dumps({
            "skill": index.get("skill"),
            "source": index.get("source"),
            "scenarios": scenarios,
        }, indent=2))
        return

    if not scenarios:
        print(f"No manual-only scenarios in {index_path}")
        return

    print(f"# Manual-only rules — {index.get('skill')} ({len(scenarios)})")
    for s in scenarios:
        print()
        print(f"## {s['id']} — {s['name']}")
        print(f"Feature: {s.get('feature', 'n/a')}")
        for label, key in (("Given", "given"), ("When", "when"), ("Then", "then")):
            for step in s.get(key) or []:
                print(f"  {label}: {step}")


def to_markdown(index_path, category=None):
    """Render an index back into the `## Feature:` / `### Scenario:` block it came from.

    The inverse of extraction. Needed when a SKILL.md is refactored and loses
    its scenario block while the generated index survives — regenerating from
    the stripped SKILL.md would silently delete every rule, so the index has to
    be reconstituted into the source first.
    """
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    scenarios = index.get("scenarios", [])
    if category:
        scenarios = [s for s in scenarios if s["id"].rsplit("-", 1)[0] == category]

    by_feature = {}
    for s in scenarios:
        by_feature.setdefault(s.get("feature", "Uncategorised"), []).append(s)

    blocks = []
    for feature in index.get("features", []) + [
        f for f in by_feature if f not in index.get("features", [])
    ]:
        if feature not in by_feature:
            continue
        lines = [f"## Feature: {feature}", ""]
        for s in by_feature[feature]:
            lines.append(f"### Scenario: {s['name']} (@rule:{s['id']})")
            for label, key in (("Given", "given"), ("When", "when"), ("Then", "then")):
                for step in s.get(key) or []:
                    lines.append(f"- {label}: {step}")
            lines.append("")
        blocks.append("\n".join(lines))

    print("\n".join(blocks).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract Gherkin scenarios from SKILL.md into specs-index.json"
    )
    parser.add_argument("skill_md", nargs="?", help="Path to SKILL.md file")
    parser.add_argument(
        "--list-manual", metavar="INDEX",
        help="Read a specs-index.json and list the scenarios no script can check",
    )
    parser.add_argument(
        "--to-markdown", metavar="INDEX",
        help="Render a specs-index.json back into its SKILL.md scenario block",
    )
    parser.add_argument(
        "--category", metavar="NAME",
        help="With --list-manual or --to-markdown, restrict to one rule category",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="With --list-manual, emit JSON instead of markdown",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output path for specs-index.json (default: <skill-dir>/specs/specs-index.json)",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print stats summary to stderr",
    )
    args = parser.parse_args()

    if args.list_manual:
        index_path = Path(args.list_manual)
        if not index_path.exists():
            print(json.dumps({"error": f"File not found: {index_path}"}))
            sys.exit(1)
        list_manual(index_path, as_json=args.json, category=args.category)
        sys.exit(0)

    if args.to_markdown:
        index_path = Path(args.to_markdown)
        if not index_path.exists():
            print(json.dumps({"error": f"File not found: {index_path}"}))
            sys.exit(1)
        to_markdown(index_path, category=args.category)
        sys.exit(0)

    if not args.skill_md:
        parser.error("skill_md is required unless --list-manual or --to-markdown is given")

    skill_path = Path(args.skill_md)
    if not skill_path.exists():
        print(json.dumps({"error": f"File not found: {skill_path}"}))
        sys.exit(1)

    result = parse_skill_md(skill_path)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = skill_path.parent / "specs" / "specs-index.json"

    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    if args.stats:
        s = result["stats"]
        print(f"Extracted {s['total_scenarios']} scenarios from {s['total_features']} features", file=sys.stderr)
        print(f"  Automatable: {s['automatable']}, Manual-only: {s['manual_only']}", file=sys.stderr)
        for cat, count in sorted(s["by_category"].items()):
            print(f"  {cat}: {count}", file=sys.stderr)
        if result.get("errors"):
            print(f"  Errors: {len(result['errors'])}", file=sys.stderr)
            for e in result["errors"]:
                print(f"    - {e}", file=sys.stderr)
    else:
        print(f"Wrote {out_path}")

    sys.exit(1 if result.get("errors") else 0)


if __name__ == "__main__":
    main()
