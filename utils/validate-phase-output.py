#!/usr/bin/env python3
"""Validate completeness of Phase 1 analysis reports, Phase 1.5 distillation documents, and Phase 2 mapping guides.

Usage:
    # Validate Phase 1 analysis
    python3 utils/validate-phase-output.py report.md --phase 1

    # Validate Phase 2 mapping guide
    python3 utils/validate-phase-output.py guide.md --phase 2

    # Gate mode: exit 0 on pass/warn, exit 1 on critical failures only
    python3 utils/validate-phase-output.py guide.md --phase 2 --gate

    # Validate Phase 2 pattern views (alpha presence & state validity)
    python3 utils/validate-phase-output.py guide.md --phase 2 --validate-patterns

    # Show word/line stats for one or more files
    python3 utils/validate-phase-output.py --stats file1.md file2.md file3.md
"""

import argparse
import json
import re
import sys
from pathlib import Path


PHASE_1_REQUIRED_KEYWORDS = [
    "Outcomes",
    "Concerns",
    "Work Products",
    "Activities",
    "Competencies",
    "Personas",
    "Persona Groups",
    "Workflows",
]

PHASE_1_5_REQUIRED_SECTIONS = [
    "Executive Summary",
    "Focus Areas",
    "Essential Concerns",
    "Activity Types",
    "Competencies",
    "Narrative",
    "Distillation",
]

PHASE_2_REQUIRED_SECTIONS = [
    (["Alpha Mappings", "Alphas"], "alphas"),
    (["Work Product Mappings", "Work Products"], "work_products"),
    (["Activity Mappings", "Activities"], "activities"),
    (["Pattern Mappings", "Patterns"], "patterns"),
    (["Citations"], "citations"),
    (["Outcome Mappings", "Outcomes"], "outcomes"),
]

KNOWN_COMPETENCY_LEVELS = {
    "Basic", "Applies", "Masters", "Adapts", "Innovating",
    "Advanced", "Expert", "Intermediate", "Beginner", "Novice", "Proficient",
}

CRITICAL_CHECKS = {
    "section_count", "numbered_subsections",
    "concern_count", "activity_type_count", "competency_count", "focus_count",
    "activity_count", "work_product_count", "alpha_count", "pattern_count",
    "pattern_views_found",
}

CRITICAL_PREFIXES = ("section_exists:",)


def _is_critical(check_name):
    if check_name in CRITICAL_CHECKS:
        return True
    return any(check_name.startswith(p) for p in CRITICAL_PREFIXES)


def validate_phase_1(content, lines):
    checks = []

    h2_lines = [l for l in lines if l.startswith("## ")]
    checks.append({
        "check": "section_count",
        "expected": ">=8",
        "actual": len(h2_lines),
        "pass": len(h2_lines) >= 8,
    })

    for keyword in PHASE_1_REQUIRED_KEYWORDS:
        found = any(l.startswith("## ") and keyword in l for l in lines)
        checks.append({
            "check": f"section_exists:{keyword}",
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

    citation_patterns = set()
    for line in lines:
        for m in re.finditer(
            r'\(([A-Z][a-z]+(?:\s+(?:&|and)\s+[A-Z][a-z]+)*(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?)\)',
            line,
        ):
            citation_patterns.add(m.group(1).strip())
    source_mentions = set()
    for line in lines:
        for m in re.finditer(
            r'\*\*Source(?:\s+Materials?)?\*\*\s*:?\s*(.+)',
            line, re.IGNORECASE,
        ):
            source_mentions.add(m.group(1).strip()[:80])
    has_citation_section = any(
        re.match(r'^##\s+\d*\.?\s*(?:Citations|References|Sources)', l, re.IGNORECASE)
        for l in lines
    )
    total_refs = len(citation_patterns) + len(source_mentions) + (1 if has_citation_section else 0)
    checks.append({
        "check": "citation_count",
        "description": "Source references (author-date citations + source material mentions)",
        "actual": total_refs,
        "expected": ">=3",
        "pass": total_refs >= 3,
    })

    perspectives = ["Business", "Technology", "People", "Process"]
    found_perspectives = []
    for p in perspectives:
        if re.search(rf'\b{p}\s+Perspective\b', content, re.IGNORECASE):
            found_perspectives.append(p)
    checks.append({
        "check": "perspective_balance",
        "description": "Four-perspective analysis coverage",
        "actual": len(found_perspectives),
        "expected": 4,
        "found": found_perspectives,
        "missing": [p for p in perspectives if p not in found_perspectives],
        "pass": len(found_perspectives) >= 3,
    })

    relationship_lines = sum(
        1 for l in lines
        if re.search(r'relat(?:es?\s+to|ionship)|contribut(?:es?\s+to)|maps?\s+to|depends\s+on|supports', l, re.IGNORECASE)
    )
    checks.append({
        "check": "relationship_documentation",
        "description": "Lines mentioning inter-concern relationships",
        "actual": relationship_lines,
        "expected": ">=5",
        "pass": relationship_lines >= 5,
    })

    return checks


def validate_phase_1_5(content, lines):
    checks = []

    for section in PHASE_1_5_REQUIRED_SECTIONS:
        found = section in content
        checks.append({
            "check": f"section_exists:{section}",
            "pass": found,
        })

    concerns = re.findall(r"^### Concern \d+:\s*(.+)$", content, re.MULTILINE)
    checks.append({
        "check": "concern_count",
        "description": "Essential concerns (future alphas)",
        "actual": len(concerns),
        "expected": "8-15",
        "names": concerns,
        "pass": 8 <= len(concerns) <= 15,
    })

    activity_types = re.findall(
        r"^### Activity Type \d+:\s*(.+)$", content, re.MULTILINE
    )
    checks.append({
        "check": "activity_type_count",
        "description": "Generalizable activity types (future ActivitySpaces)",
        "actual": len(activity_types),
        "expected": "6-12",
        "names": activity_types,
        "pass": 6 <= len(activity_types) <= 12,
    })

    competencies = re.findall(
        r"^### Competency \d+:\s*(.+)$", content, re.MULTILINE
    )
    checks.append({
        "check": "competency_count",
        "description": "Universal competencies",
        "actual": len(competencies),
        "expected": "5-10",
        "names": competencies,
        "pass": 5 <= len(competencies) <= 10,
    })

    std_levels = ["Basic", "Applies", "Masters", "Adapts", "Innovating"]
    for level in std_levels:
        count = len(re.findall(rf"\*\*{level}\*\*:", content))
        checks.append({
            "check": f"competency_level:{level}",
            "description": f"Occurrences of **{level}**: (expect {len(competencies)} — one per competency)",
            "actual": count,
            "expected": len(competencies),
            "pass": count == len(competencies),
        })

    narratives = re.findall(
        r"^### Narrative \d+:\s*(.+)$", content, re.MULTILINE
    )
    checks.append({
        "check": "narrative_count",
        "description": "Narrative frameworks (future NarrativeTypes)",
        "actual": len(narratives),
        "expected": "3-5",
        "names": narratives,
        "pass": 3 <= len(narratives) <= 5,
    })

    focuses = re.findall(r"^### Focus \d+:\s*(.+)$", content, re.MULTILINE)
    checks.append({
        "check": "focus_count",
        "description": "Focus areas",
        "actual": len(focuses),
        "expected": "2-4",
        "names": focuses,
        "pass": 2 <= len(focuses) <= 4,
    })

    has_coverage = "Activity Type Coverage Validation" in content or \
                   "Coverage Validation" in content
    checks.append({
        "check": "coverage_table",
        "description": "Activity type coverage validation table present",
        "pass": has_coverage,
    })

    return checks


def validate_phase_2(content, lines, kind="practice"):
    checks = []

    h2_lines = [l for l in lines if l.startswith("## ")]
    h3_lines = [l for l in lines if l.startswith("### ")]
    checks.append({
        "check": "section_count",
        "expected": ">=3 H2 sections",
        "actual": len(h2_lines),
        "pass": len(h2_lines) >= 3,
    })

    all_headings = h2_lines + h3_lines
    for variants, key in PHASE_2_REQUIRED_SECTIONS:
        if kind == "baseline" and key in ("activities", "work_products", "patterns"):
            continue
        found = any(v in l for v in variants for l in all_headings)
        checks.append({
            "check": f"section_exists:{key}",
            "pass": found,
        })

    if kind == "practice":
        activity_lines = [l for l in lines
                          if re.match(r"^\*\*Activity:\s", l) or re.match(r"^#{3,5} Activity[:\s]", l)]
        checks.append({
            "check": "activity_count",
            "description": "Mapped activities",
            "actual": len(activity_lines),
            "expected": ">=5",
            "pass": len(activity_lines) >= 5,
        })

        wp_lines = [l for l in lines
                    if re.match(r"^\*\*Work Product:\s", l) or re.match(r"^#{3,5} Work Product[:\s]", l)]
        checks.append({
            "check": "work_product_count",
            "description": "Mapped work products",
            "actual": len(wp_lines),
            "expected": ">=3",
            "pass": len(wp_lines) >= 3,
        })

        lod_names = re.findall(
            r'(?:^\s*-\s*\*\*Level:\s*(.+?)\*\*|^#{3,5}\s*LOD:\s*(.+?)(?:\s*\(seq:|\s*$))',
            content, re.MULTILINE,
        )
        lod_names = [n1 or n2 for n1, n2 in lod_names]
        if lod_names:
            lifecycle_terms = re.compile(
                r"\b(?:completed|met|identified|updated|evolved|stated|achieved|"
                r"realized|fulfilled|delivered|driving|enabling|guiding|validating|"
                r"continuously|ongoing|in progress|optimized|performing|established|"
                r"mature|advanced|forming|storming|norming|drafted|reviewed|"
                r"approved|published|enforced)\b",
                re.IGNORECASE,
            )
            flagged = []
            for name in lod_names:
                m = lifecycle_terms.search(name)
                if m:
                    flagged.append(f"{name} ('{m.group()}')")
            checks.append({
                "check": "lod_naming_quality",
                "description": "LOD names describe document fidelity, not concern lifecycle",
                "actual": len(flagged),
                "expected": 0,
                "pass": len(flagged) == 0,
                "flagged": flagged if flagged else None,
                "severity": "advisory",
            })

        pattern_lines = [l for l in lines
                         if re.match(r"^\*\*Pattern:\s", l) or re.match(r"^#{3,5} Pattern[:\s]", l)]
        checks.append({
            "check": "pattern_count",
            "description": "Mapped patterns",
            "actual": len(pattern_lines),
            "expected": ">=1",
            "pass": len(pattern_lines) >= 1,
        })

    alpha_lines = [l for l in lines
                   if re.match(r"^\*\*Alpha:\s", l) or re.match(r"^#{3,5} Alpha[:\s]", l)]
    checks.append({
        "check": "alpha_count",
        "description": "Mapped alphas",
        "actual": len(alpha_lines),
        "expected": ">=3",
        "pass": len(alpha_lines) >= 3,
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

    background_mentions = sum(1 for l in lines if re.search(r'\*\*Background\*\*|\bBackground:\b', l, re.IGNORECASE))
    checks.append({
        "check": "gherkin_background",
        "description": "Background prerequisites mentioned in mapping (states, LODs, activities)",
        "actual": background_mentions,
        "pass": True,  # informational
    })

    test_mentions = sum(1 for l in lines if re.search(r'\*\*Test\*\*|\bTest:\b', l) and not re.search(r'test plan|testing|test case', l, re.IGNORECASE))
    example_mentions = sum(1 for l in lines if re.search(r'\*\*Examples\*\*|\bExamples:\b', l))
    checks.append({
        "check": "gherkin_test_examples",
        "description": "Test/Examples scenarios in mapping (checklists, activities)",
        "actual": {"test": test_mentions, "examples": example_mentions},
        "pass": True,  # informational
    })

    gwt_lines = sum(1 for l in lines if re.search(r'^\s*-\s*(Given|When|Then):', l))
    checks.append({
        "check": "gherkin_gwt_patterns",
        "description": "Given/When/Then structured scenarios found",
        "actual": gwt_lines,
        "pass": True,  # informational
    })

    has_delineation = bool(re.search(
        r'delineation\s+analysis|primary\s+alpha|alpha\s+coverage\s+analysis',
        content, re.IGNORECASE,
    ))
    checks.append({
        "check": "delineation_analysis",
        "description": "Delineation analysis or primary alpha documentation present",
        "pass": has_delineation,
    })

    primary_alpha_match = re.search(
        r'(?:\*\*)?(?:primary\s+alpha|central\s+alpha)\S*(?:\*\*)?\s*[:\-]\s*(.+)',
        content, re.IGNORECASE,
    )
    checks.append({
        "check": "primary_alpha_documented",
        "description": "Primary alpha explicitly identified",
        "actual": primary_alpha_match.group(1).strip()[:60] if primary_alpha_match else None,
        "pass": primary_alpha_match is not None,
    })

    keyword_items = []
    keyword_section = re.search(
        r'^## Keywords\s*\n((?:(?!^## ).*\n)*)', content, re.MULTILINE,
    )
    if keyword_section:
        keyword_items = re.findall(r'^\s*[-*]\s+(.+)', keyword_section.group(1), re.MULTILINE)
        if not keyword_items:
            keyword_items = [
                w.strip() for w in keyword_section.group(1).split(",") if w.strip()
            ]
    if not keyword_items:
        inline_kw = re.search(
            r'\*\*Keywords?:?\*\*\s*:?\s*(.+)', content, re.IGNORECASE,
        )
        if inline_kw:
            keyword_items = [w.strip() for w in inline_kw.group(1).split(",") if w.strip()]
    checks.append({
        "check": "keyword_content",
        "description": "Keywords section has 10-20 items",
        "actual": len(keyword_items),
        "expected": "10-20",
        "pass": len(keyword_items) >= 10,
    })

    four_pass_markers = ["Pass 1", "Pass 2", "Pass 3", "Pass 4"]
    passes_found = sum(1 for marker in four_pass_markers if marker in content)
    has_four_pass = passes_found >= 3 or bool(re.search(
        r'four.pass|4.pass|completeness\s+pass|backfill|gap\s+analysis|alpha.state.activity\s+gap|state\s+distribution',
        content, re.IGNORECASE,
    ))
    checks.append({
        "check": "pattern_construction",
        "description": "Four-pass pattern construction evidence",
        "actual": passes_found,
        "expected": ">=3 pass markers or gap analysis/backfill evidence",
        "pass": has_four_pass,
    })

    narrative_structured = sum(
        1 for l in lines
        if re.search(r'Narrative\s+Type\s+Name\s*:', l, re.IGNORECASE)
    )
    narrative_prose = sum(
        1 for l in lines
        if re.search(r'^Practice\s+Narrative\s*:', l, re.IGNORECASE)
        or re.search(r'^Method\s+Narrative\s*:', l, re.IGNORECASE)
    )
    checks.append({
        "check": "narrative_format",
        "description": "Narratives use structured format with narrativeTypeName",
        "actual": narrative_structured,
        "expected": ">=1 structured narrative",
        "pass": narrative_structured >= 1,
    })

    return checks


def extract_alphas_and_states(content):
    """Extract alpha names and their states from the ## Alphas / ### Alpha Mappings section."""
    alphas = {}
    blocks = re.split(r"\*\*Alpha:\s*", content)
    for block in blocks[1:]:
        name_match = re.match(r"(.+?)\*\*", block)
        if not name_match:
            continue
        alpha_name = name_match.group(1).strip()
        states = re.findall(r"\*\*State:\s*(.+?)\*\*", block)
        if states:
            alphas[alpha_name] = [s.strip() for s in states]
    return alphas


def extract_pattern_views(content):
    """Extract pattern view sections with alpha-state pairs.

    Supports two formats:
      - **View N: Name** (numbered)
      - **View: Name** (seq: N) (named with seq)
    """
    pattern_start = content.find("### Pattern Mappings")
    if pattern_start < 0:
        pattern_start = content.find("#### Pattern Views")
    if pattern_start < 0:
        pattern_start = content.find("- **Pattern Views:**")
    if pattern_start < 0:
        return []

    pattern_section = content[pattern_start:]
    next_section = re.search(r"\n### (?!Pattern)", pattern_section[10:])
    if next_section:
        pattern_section = pattern_section[:next_section.start() + 10]

    views = []

    # Format 1: **View: Name** (seq: N)
    view_splits = re.split(r"\*\*View:\s*", pattern_section)
    if len(view_splits) > 1:
        for block in view_splits[1:]:
            name_match = re.match(r"(.+?)\*\*\s*\(seq:\s*(\d+)\)", block)
            if name_match:
                view_name = name_match.group(1).strip()
                view_num = int(name_match.group(2))
            else:
                name_only = re.match(r"(.+?)\*\*", block)
                view_name = name_only.group(1).strip() if name_only else "?"
                view_num = len(views)

            pairs = re.findall(r"Alpha Name:\s*(.+)\n\s*State Name:\s*(.+)", block)
            alpha_states = [(a.strip(), s.strip()) for a, s in pairs]
            views.append({"seq": view_num, "name": view_name, "alpha_states": alpha_states})
        return views

    # Format 2: **View N: Name**
    view_splits = re.split(r"\*\*View (\d+):", pattern_section)
    for i in range(1, len(view_splits), 2):
        view_num = int(view_splits[i])
        view_text = view_splits[i + 1] if i + 1 < len(view_splits) else ""
        view_name_match = re.match(r"\s*(.+?)\*\*", view_text)
        view_name = view_name_match.group(1).strip() if view_name_match else f"View {view_num}"

        pairs = re.findall(r"Alpha Name:\s*(.+)\n\s*State Name:\s*(.+)", view_text)
        alpha_states = [(a.strip(), s.strip()) for a, s in pairs]
        views.append({"seq": view_num, "name": view_name, "alpha_states": alpha_states})

    return views


def validate_pattern_views(content):
    """Validate pattern view completeness: alpha presence and state validity."""
    checks = []

    alphas = extract_alphas_and_states(content)
    if not alphas:
        checks.append({
            "check": "pattern_validation",
            "description": "No alphas found in mapping guide to validate against",
            "pass": True,
        })
        return checks

    views = extract_pattern_views(content)
    if not views:
        checks.append({
            "check": "pattern_views_found",
            "description": "No pattern views found in mapping guide",
            "pass": False,
        })
        return checks

    checks.append({
        "check": "pattern_views_found",
        "actual": len(views),
        "pass": len(views) >= 2,
    })

    expected_alphas = set(alphas.keys())

    for view in views:
        view_alphas = {a for a, _ in view["alpha_states"]}
        missing = expected_alphas - view_alphas
        extra = view_alphas - expected_alphas

        checks.append({
            "check": f"view_{view['seq']}_alpha_count",
            "description": f"View {view['seq']} ({view['name']}): {len(view_alphas)} alphas",
            "expected": len(expected_alphas),
            "actual": len(view_alphas),
            "pass": not missing,
        })
        if missing:
            checks.append({
                "check": f"view_{view['seq']}_missing_alphas",
                "description": f"View {view['seq']} missing alphas",
                "missing": sorted(missing),
                "pass": False,
            })
        if extra:
            checks.append({
                "check": f"view_{view['seq']}_extra_alphas",
                "description": f"View {view['seq']} has alphas not in mapping guide",
                "extra": sorted(extra),
                "pass": False,
            })

        for alpha_name, state_name in view["alpha_states"]:
            if alpha_name in alphas:
                valid_states = alphas[alpha_name]
                if state_name not in valid_states:
                    checks.append({
                        "check": f"view_{view['seq']}_invalid_state",
                        "description": f"View {view['seq']}: invalid state \"{state_name}\" for alpha \"{alpha_name}\"",
                        "valid_states": valid_states,
                        "pass": False,
                    })

        alpha_counts = {}
        for a, _ in view["alpha_states"]:
            alpha_counts[a] = alpha_counts.get(a, 0) + 1
        for a, count in alpha_counts.items():
            if count > 2:
                checks.append({
                    "check": f"view_{view['seq']}_state_density",
                    "description": f"View {view['seq']}: alpha \"{a}\" has {count} states (max 2)",
                    "pass": False,
                })

    all_states_used = {}
    for view in views:
        for alpha_name, state_name in view["alpha_states"]:
            all_states_used.setdefault(alpha_name, set()).add(state_name)

    for alpha_name, defined_states in alphas.items():
        used = all_states_used.get(alpha_name, set())
        unused = set(defined_states) - used
        if unused:
            checks.append({
                "check": f"alpha_{alpha_name}_unused_states",
                "description": f"Alpha \"{alpha_name}\" has states not used in any pattern view",
                "unused": sorted(unused),
                "pass": True,
            })

    return checks


def print_file_stats(paths):
    """Print word/line counts for each file."""
    for path_str in paths:
        p = Path(path_str)
        if not p.exists():
            print(f"{p.name}: NOT FOUND")
            continue
        content = p.read_text()
        words = len(content.split())
        line_count = content.count("\n")
        size_kb = p.stat().st_size / 1024
        print(f"{p.name}: {words} words, {line_count} lines, {size_kb:.1f} KB")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Phase 1 analysis report or Phase 2 mapping guide completeness"
    )
    parser.add_argument("file", nargs="+", help="Path to markdown file(s) to validate or stat")
    parser.add_argument(
        "--phase",
        type=float,
        choices=[1, 1.5, 2],
        help="Phase number (1=analysis report, 1.5=distillation, 2=mapping guide)",
    )
    parser.add_argument(
        "--validate-patterns",
        action="store_true",
        help="Validate pattern views in Phase 2 mapping guide (alpha presence, state validity)",
    )
    parser.add_argument(
        "--kind",
        choices=["practice", "baseline"],
        default="practice",
        help="Kind of output being validated (default: practice)",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Gate mode: exit 1 only on critical failures, exit 0 on advisory-only failures",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print word/line/size statistics for each input file",
    )
    args = parser.parse_args()

    if args.stats:
        print_file_stats(args.file)
        sys.exit(0)

    if not args.phase:
        print("Error: --phase is required unless using --stats", file=sys.stderr)
        sys.exit(1)

    target = args.file[0]

    try:
        with open(target, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(json.dumps({"error": f"File not found: {target}"}))
        sys.exit(1)

    lines = content.split("\n")

    if args.phase == 1:
        checks = validate_phase_1(content, lines)
    elif args.phase == 1.5:
        checks = validate_phase_1_5(content, lines)
    else:
        checks = validate_phase_2(content, lines, kind=args.kind)

    if args.validate_patterns and args.phase == 2:
        checks.extend(validate_pattern_views(content))

    for c in checks:
        if "pass" in c:
            c["severity"] = "critical" if _is_critical(c["check"]) else "advisory"

    passed = sum(1 for c in checks if c.get("pass", True))
    total = sum(1 for c in checks if "pass" in c)
    all_pass = passed == total

    failures = [c for c in checks if c.get("pass") is False]
    critical_failures = [c for c in failures if c.get("severity") == "critical"]
    advisory_failures = [c for c in failures if c.get("severity") == "advisory"]

    if args.gate:
        if critical_failures:
            gate_result = "fail"
        elif advisory_failures:
            gate_result = "warn"
        else:
            gate_result = "pass"

        result = {
            "file": target,
            "phase": args.phase,
            "gate": gate_result,
            "summary": f"{passed}/{total} checks passed ({len(critical_failures)} critical, {len(advisory_failures)} advisory failures)",
            "criticalFailures": critical_failures,
            "advisoryFailures": advisory_failures,
        }
        print(json.dumps(result, indent=2))
        sys.exit(0 if gate_result != "fail" else 1)

    result = {
        "file": target,
        "phase": args.phase,
        "valid": all_pass,
        "summary": f"{passed}/{total} checks passed",
        "checks": checks,
    }

    if not all_pass:
        result["failures"] = failures

    print(json.dumps(result, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
