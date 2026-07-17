#!/usr/bin/env python3
"""Validate completeness of Phase 1 analysis reports and Phase 2 mapping guides."""

import argparse
import json
import re
import sys


PHASE_1_REQUIRED_SECTIONS = [
    "## 1. Outcomes",
    "## 2. Concerns",
    "## 3. Progressive States",
    "## 4. Activities",
    "## 5. Competencies",
    "## 6. Personas",
    "## 7. Persona Groups",
    "## 8. Workflows",
]

PHASE_2_REQUIRED_SECTIONS = [
    "## Keywords",
    "## Terminology Aliases",
    "## Alphas",
    "## Work Products",
    "## Activities",
    "## Patterns",
    "## Citations",
]

KNOWN_COMPETENCY_LEVELS = {
    "Basic", "Applies", "Masters", "Adapts", "Innovating",
    "Advanced", "Expert", "Intermediate", "Beginner", "Novice", "Proficient",
}


def validate_phase_1(content, lines):
    checks = []

    h2_lines = [l for l in lines if l.startswith("## ")]
    checks.append({
        "check": "section_count",
        "expected": ">=8",
        "actual": len(h2_lines),
        "pass": len(h2_lines) >= 8,
    })

    for section in PHASE_1_REQUIRED_SECTIONS:
        found = any(l.strip() == section for l in lines)
        checks.append({
            "check": f"section_exists:{section}",
            "pass": found,
        })

    numbered_items = [l for l in lines if re.match(r"^### \d+", l)]
    checks.append({
        "check": "numbered_subsections",
        "description": "Count of ### N. items (concerns, activities, etc.)",
        "actual": len(numbered_items),
        "minimums": ">=5 concerns, >=5 activities, >=3 work products",
        "pass": len(numbered_items) >= 5,
    })

    return checks


def validate_phase_2(content, lines):
    checks = []

    h2_lines = [l for l in lines if l.startswith("## ")]
    checks.append({
        "check": "section_count",
        "expected": "7-9",
        "actual": len(h2_lines),
        "pass": len(h2_lines) >= 7,
    })

    for section in PHASE_2_REQUIRED_SECTIONS:
        found = any(l.strip() == section for l in lines)
        checks.append({
            "check": f"section_exists:{section}",
            "pass": found,
        })

    activity_lines = [l for l in lines if re.match(r"^### Activity", l)]
    checks.append({
        "check": "activity_count",
        "description": "Mapped activities (### Activity...)",
        "actual": len(activity_lines),
        "expected": ">=5",
        "pass": len(activity_lines) >= 5,
    })

    wp_lines = [l for l in lines if re.match(r"^### ", l) and "work product" in l.lower()]
    checks.append({
        "check": "work_product_count",
        "description": "Mapped work products",
        "actual": len(wp_lines),
        "expected": ">=3",
        "pass": len(wp_lines) >= 3,
    })

    alpha_lines = [l for l in lines if re.match(r"^### Alpha:", l)]
    checks.append({
        "check": "alpha_count",
        "description": "Mapped alphas (### Alpha:...)",
        "actual": len(alpha_lines),
        "expected": ">=3",
        "pass": len(alpha_lines) >= 3,
    })

    pattern_lines = [l for l in lines if re.match(r"^### Pattern:", l)]
    checks.append({
        "check": "pattern_count",
        "description": "Mapped patterns (### Pattern:...)",
        "actual": len(pattern_lines),
        "expected": ">=1",
        "pass": len(pattern_lines) >= 1,
    })

    competency_matches = set()
    for line in lines:
        if re.search(r"competency level|recommended.*level", line, re.IGNORECASE):
            for name in KNOWN_COMPETENCY_LEVELS:
                if name in line:
                    competency_matches.add(name)
    if competency_matches:
        checks.append({
            "check": "competency_level_names",
            "description": "Competency level names found in mapping guide (validate against baseline)",
            "found": sorted(competency_matches),
        })

    return checks


def main():
    parser = argparse.ArgumentParser(
        description="Validate Phase 1 analysis report or Phase 2 mapping guide completeness"
    )
    parser.add_argument("file", help="Path to markdown file to validate")
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2],
        required=True,
        help="Phase number (1=analysis report, 2=mapping guide)",
    )
    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(json.dumps({"error": f"File not found: {args.file}"}))
        sys.exit(1)

    lines = content.split("\n")

    if args.phase == 1:
        checks = validate_phase_1(content, lines)
    else:
        checks = validate_phase_2(content, lines)

    passed = sum(1 for c in checks if c.get("pass", True))
    total = sum(1 for c in checks if "pass" in c)
    all_pass = passed == total

    result = {
        "file": args.file,
        "phase": args.phase,
        "valid": all_pass,
        "summary": f"{passed}/{total} checks passed",
        "checks": checks,
    }

    if not all_pass:
        failures = [c for c in checks if c.get("pass") is False]
        result["failures"] = failures

    print(json.dumps(result, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
