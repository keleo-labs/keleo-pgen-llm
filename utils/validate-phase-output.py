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

    # Check every source document is drawn on (all files searched, not just the first)
    python3 utils/validate-phase-output.py _phase1-cluster-*.md --phase 1 \\
        --source-manifest /tmp/corpus/_manifest.json
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


def validate_source_coverage(contents, manifest_path):
    """Check every source document is actually drawn on by the phase output.

    When a large corpus is split across parallel cluster analysts, guides can
    fall between cluster boundaries because each analyst only claims what its
    own prompt listed. This compares the extraction manifest produced by
    ``extract-html-text.py`` (or a plain newline-delimited list of sources)
    against the combined phase output, matching on each source's stem.

    Args:
        contents: Combined text of all phase output files to search.
        manifest_path: Path to an extract-html-text.py JSON manifest, or a
            newline-delimited list of source URLs/paths.

    Returns:
        list[dict]: One summary check plus one entry naming any uncited stems.
    """
    path = Path(manifest_path)
    if not path.exists():
        return [{"check": "source_coverage", "pass": False,
                 "detail": f"Manifest not found: {manifest_path}"}]

    raw = path.read_text(encoding="utf-8")
    stems = []
    if raw.lstrip().startswith("{"):
        manifest = json.loads(raw)
        stems = [e["stem"] for e in manifest.get("entries", []) if "stem" in e]
    else:
        for line in raw.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                stems.append(_source_stem(line))

    if not stems:
        return [{"check": "source_coverage", "pass": False,
                 "detail": f"No sources found in {manifest_path}"}]

    haystack = contents.lower()
    uncited = [s for s in stems if s.lower() not in haystack]
    checks = [{
        "check": "source_coverage",
        "pass": not uncited,
        "detail": f"{len(stems) - len(uncited)}/{len(stems)} source documents cited",
    }]
    if uncited:
        checks.append({
            "check": "source_coverage_gaps",
            "detail": "Sources never referenced in the phase output: " + ", ".join(uncited),
        })
    return checks


def _source_stem(source):
    """Derive the identifying stem from a URL or path (mirrors extract-html-text.py)."""
    generic = {"", "index", "index.html", "index.htm"}
    segments = [s for s in re.split(r"[/\\]", source.split("?")[0].split("#")[0]) if s]
    for seg in reversed(segments):
        if seg.lower() not in generic:
            return re.sub(r"\.(x?html?|htm)$", "", seg, flags=re.IGNORECASE)
    return source


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

    # Matches `**Alpha: X**`, `#### Alpha: X` and `##### **Alpha: X**`.
    alpha_lines = [l for l in lines if re.match(r"^(?:#{0,6}\s*)?\*{0,2}Alpha:\s", l)]
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


#: An alpha block opener, in either the bold form (`**Alpha: Name**`) or the
#: heading form the phase skill prescribes (`#### Alpha: Name`). Guides written
#: to the phase skill use headings, so matching only the bold form silently
#: finds zero alphas and turns pattern validation into a no-op that still
#: reports a pass.
#: Three conventions are in use across guides written to the same phase skill:
#: `#### Alpha: Name`, `**Alpha: Name**`, and `##### **Alpha: Name** (qualifier)`.
#: Optional leading hashes are allowed before the bold form.
ALPHA_ANCHOR_RE = re.compile(
    r"^(?:#{0,6}\s*\*\*Alpha:\s*(?P<b>.+?)\*\*.*|#{3,6}\s*Alpha:\s*(?P<h>.+?)\s*)$",
    re.MULTILINE,
)

#: A state within an alpha block: `**State: Name**`, `**State 3: Name**` or
#: `**State 3 — Name**`, optionally followed by `(seq 3, type: Progression)`.
#: Guides use colons and dashes interchangeably as the separator.
STATE_RE = re.compile(r"\*\*State(?:\s+\d+)?\s*[:—–-]\s*(.+?)\*\*")

#: Words that mark a trailing parenthetical on an alpha heading as a mapping
#: qualifier rather than part of the name, e.g.
#: "#### Alpha: Git Provider Integration (Specialization - contributesTo X)".
#: Alpha names may legitimately contain brackets ("Platform Engineering (CNCF)"),
#: so only qualifier-looking parentheses are stripped.
ALPHA_QUALIFIER_WORDS = (
    "contributesto", "mapsto", "specialization", "specialisation",
    "redeclaration", "redeclared", "variant", "new alpha", "inherited",
)


def _clean_alpha_name(name):
    """Strip a trailing mapping qualifier from an alpha heading."""
    match = re.search(r"\s*\(([^()]*)\)\s*$", name)
    if match and any(w in match.group(1).lower() for w in ALPHA_QUALIFIER_WORDS):
        return name[: match.start()].strip().strip("`").strip()
    return name.strip().strip("`").strip()


def extract_alphas_and_states(content):
    """Extract alpha names and their states from a Phase 2 mapping guide.

    Tolerates both the bold (`**Alpha: Name**`) and heading (`#### Alpha: Name`)
    conventions, and both unnumbered and numbered state labels, because guides
    in the wild use all four combinations.
    """
    anchors = list(ALPHA_ANCHOR_RE.finditer(content))
    alphas = {}
    for i, match in enumerate(anchors):
        name = _clean_alpha_name(match.group("h") or match.group("b") or "")
        if not name:
            continue
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(content)
        states = STATE_RE.findall(content[match.end():end])
        if states:
            alphas[name] = [s.strip() for s in states]
    return alphas


def extract_pattern_views(content):
    """Extract pattern view sections with alpha-state pairs.

    Supports two formats:
      - **View N: Name** (numbered)
      - **View: Name** (seq: N) (named with seq)
    """
    # Locate the pattern section without assuming a heading depth: guides write
    # "## Pattern Mappings", "### Pattern Mappings" or "#### Pattern Views"
    # depending on how the practice nests its sections. Matching one fixed depth
    # silently returns no views, which reads as a structural failure in the guide
    # rather than a parser miss.
    header = re.search(r"^(#{2,5})\s*Pattern (?:Mappings|Views)\b.*$", content, re.MULTILINE)
    if header:
        pattern_start = header.start()
        depth = len(header.group(1))
        # End at the next heading of the same or shallower depth that is not
        # itself a pattern heading.
        tail = content[header.end():]
        boundary = re.search(
            rf"^#{{1,{depth}}}\s+(?!Pattern\b).*$", tail, re.MULTILINE
        )
        pattern_section = tail[:boundary.start()] if boundary else tail
    else:
        # The label is written as a list item in a mapping guide and as a bare
        # bold run in an analysis report. Matching only the list form returns no
        # views for the report, which reads as the report declaring none.
        marker = re.search(r"^\s*(?:-\s*)?\*\*Pattern Views:?\*\*", content, re.MULTILINE)
        if not marker:
            return []
        pattern_section = content[marker.start():]

    views = []
    _pairs = extract_alpha_state_pairs

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

            views.append({"seq": view_num, "name": view_name, "alpha_states": _pairs(block)})
        return views

    # Format 2: **View N: Name**, or **View N — Name** / **View N - Name**.
    # Guides separate the number from the title with a colon or a dash; matching
    # only the colon drops every view in a dash-style guide.
    view_splits = re.split(r"\*\*View (\d+)\s*[:—–-]", pattern_section)
    if len(view_splits) == 1:
        # Format 3: a plain `View N:` line with the name on an indented
        # `Name:` line beneath it.
        view_splits = re.split(r"^View (\d+):\s*$", pattern_section, flags=re.MULTILINE)
        for i in range(1, len(view_splits), 2):
            view_num = int(view_splits[i])
            view_text = view_splits[i + 1] if i + 1 < len(view_splits) else ""
            name_match = re.search(r"^\s*Name:\s*(.+)$", view_text, re.MULTILINE)
            views.append({
                "seq": view_num,
                "name": name_match.group(1).strip() if name_match else f"View {view_num}",
                "alpha_states": _pairs(view_text),
            })
        if views:
            return views
        view_splits = []
    for i in range(1, len(view_splits), 2):
        view_num = int(view_splits[i])
        view_text = view_splits[i + 1] if i + 1 < len(view_splits) else ""
        view_name_match = re.match(r"\s*(.+?)\*\*", view_text)
        view_name = view_name_match.group(1).strip() if view_name_match else f"View {view_num}"

        views.append({"seq": view_num, "name": view_name, "alpha_states": _pairs(view_text)})

    return views


_HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)
#: A heading may be numbered by its section ("8.1 Deal Qualification Journey").
_SECTION_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
#: The marker that makes a subsection a pattern rather than a note about one:
#: "Pattern Views" as a label introducing a list, not a mention in prose. A
#: checklist item reading "pattern views complete" is about patterns and is not
#: one, so a bare substring search reads validation sections as patterns.
_PATTERN_VIEWS_MARKER_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?Pattern Views?(?:\*\*)?\s*:", re.IGNORECASE | re.MULTILINE
)


def _heading_blocks(content):
    """Yield (depth, title, body) for every heading, body ending at the next
    heading of the same or shallower depth."""
    headings = list(_HEADING_RE.finditer(content))
    for i, m in enumerate(headings):
        depth = len(m.group(1))
        end = len(content)
        for later in headings[i + 1:]:
            if len(later.group(1)) <= depth:
                end = later.start()
                break
        yield depth, m.group(2).strip(), content[m.end():end]


def extract_alpha_state_pairs(block):
    """Extract (alpha, state) pairs from a block of guide prose.

    Several conventions are in use, and a parser that knows only one returns
    nothing for the others — which reads as a guide declaring no states rather
    than as a parser miss. The verbose form lists each pair over two lines; the
    compact one puts them on a single "Alpha States:" line with arrows or
    commas; and the schema-shaped one writes keyed braces.

    Shared by pattern views and by state Background blocks, which use the same
    conventions for the same thing.
    """
    found = [
        (a.strip(), s.strip())
        for a, s in re.findall(r"Alpha Name:\s*(.+)\n\s*State Name:\s*(.+)", block)
    ]
    # Same-line variant: "Alpha Name: X, State Name: Y"
    found += [
        (a.strip(), s.strip())
        for a, s in re.findall(r"Alpha Name:\s*([^,\n]+?)\s*,\s*State Name:\s*(.+)", block)
    ]
    if found:
        return found

    # Keyed-brace form, bare or JSON-quoted keys, on one line or many:
    #   - {alphaName: Portal Identity Federation, stateName: Guest Access Only}
    #   - alphaStates: [{"alphaName": "Platform", "stateName": "Ready"}]
    keyed = re.findall(
        r"\{\s*\"?alphaName\"?\s*:\s*\"?([^,{}\"]+?)\"?\s*,"
        r"\s*\"?stateName\"?\s*:\s*\"?([^{}\"]+?)\"?\s*\}",
        block, re.IGNORECASE,
    )
    if keyed:
        return [(a.strip().strip("`"), s.strip().strip("`")) for a, s in keyed]

    # The label may carry a qualifier ("Alpha States (changed only):") and
    # may be written as prose or as the schema's camelCase property name.
    line = re.search(
        r"(?:Alpha States?|alphaStates)\s*(?:\([^)]*\))?\s*:\s*(.+)", block
    )
    if not line:
        return []
    raw = line.group(1)

    # Brace-tuple form: [{Alpha Name, State Name}, {Alpha Name, State Name}]
    braced = re.findall(r"\{\s*([^,{}]+?)\s*,\s*([^{}]+?)\s*\}", raw)
    if braced:
        return [(a.strip().strip("`"), s.strip().strip("`")) for a, s in braced]

    # Arrow form: Alpha → State; Alpha → State
    for entry in raw.split(";"):
        parts = re.split(r"\s*(?:→|->|=>)\s*", entry.strip(), maxsplit=1)
        if len(parts) == 2 and parts[0] and parts[1]:
            found.append((parts[0].strip().strip("`"), parts[1].strip().strip("`")))
    return found


def _background_block(body):
    """The text of a state's Background block, or "".

    Taken by indentation rather than by looking for the next bullet: the block
    nests `Given:` and `Alpha States:` beneath itself, so a terminator matching
    any following list item ends it on its own first child and the alpha states
    are never seen.
    """
    match = re.search(r"^(\s*)-?\s*\*{0,2}Background\*{0,2}\s*:(.*)$",
                      body, re.MULTILINE)
    if not match:
        return ""
    indent = len(match.group(1))
    collected = [match.group(2)]
    for line in body[match.end():].splitlines():
        if not line.strip():
            collected.append(line)
            continue
        if len(line) - len(line.lstrip()) <= indent:
            break
        collected.append(line)
    return "\n".join(collected)


def extract_state_prerequisites(content):
    """{(alpha, state): [(alpha, state), ...]} from each state's Background block.

    A state's `background.alphaStates` are the cross-concern conditions that
    must hold before it is reached. They are authored in the alpha step and the
    views in the pattern step, and until Pass 5 nothing compared the two — so a
    view could assert a state several views before the pattern went anywhere
    near its prerequisites, and the guide would pass.
    """
    prereqs = {}
    anchors = list(ALPHA_ANCHOR_RE.finditer(content))
    for i, match in enumerate(anchors):
        alpha = _clean_alpha_name(match.group("h") or match.group("b") or "")
        if not alpha:
            continue
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(content)
        block = content[match.end():end]

        states = list(STATE_RE.finditer(block))
        for j, state_match in enumerate(states):
            state = state_match.group(1).strip()
            state_end = states[j + 1].start() if j + 1 < len(states) else len(block)
            background = _background_block(block[state_match.end():state_end])
            if not background:
                continue
            pairs = extract_alpha_state_pairs(background)
            if pairs:
                prereqs[(alpha, state)] = pairs
    return prereqs


def validate_prerequisite_order(content):
    """Pass 5 — a view may not assert a state the pattern reaches later.

    The same rule `check-pattern-prerequisites.py` applies to generated JSON,
    applied to the mapping guide instead, so the ordering is settled before
    Phase 3 spends tokens rendering it. The guide cannot see the effective
    context, so only prerequisites naming alphas the guide itself declares are
    judged; the rest wait for the JSON.
    """
    checks = []
    prereqs = extract_state_prerequisites(content)
    if not prereqs:
        return checks

    alphas = extract_alphas_and_states(content)
    failures = []
    for pattern_name, body in iter_pattern_sections(content):
        views = extract_pattern_views(body)
        if len(views) < 2:
            continue
        views.sort(key=lambda v: v["seq"])

        # Earliest view declaring each (alpha, state), plus the implication
        # that a later state of an alpha means the earlier ones were passed.
        reached = {}
        for idx, view in enumerate(views):
            for pair in view["alpha_states"]:
                reached.setdefault(pair, idx)

        def earliest(alpha, state):
            order = alphas.get(alpha, [])
            if state not in order:
                return reached.get((alpha, state))
            hits = [reached[(alpha, s)] for s in order[order.index(state):]
                    if (alpha, s) in reached]
            return min(hits) if hits else None

        for idx, view in enumerate(views):
            if idx == 0:
                continue  # entry view: conditions met before the pattern begins
            for alpha, state in view["alpha_states"]:
                for req_alpha, req_state in prereqs.get((alpha, state), []):
                    if req_alpha not in alphas:
                        continue  # inherited; resolvable only against the JSON
                    at = earliest(req_alpha, req_state)
                    if at is None or at > idx:
                        failures.append(
                            f"{pattern_name or 'pattern'} view {view['seq']} "
                            f"({view['name']}) asserts {alpha}.{state}, which "
                            f"requires {req_alpha}.{req_state} — "
                            + (f"reached only at view {views[at]['seq']}"
                               if at is not None else "never reached")
                        )

    checks.append({
        "check": "pattern_prerequisite_order",
        "description": (
            "Each view reaches the prerequisites of the states it asserts "
            "(pattern-completeness.md Pass 5)"
        ),
        "expected": 0,
        "actual": len(failures),
        "failures": failures[:20],
        "pass": not failures,
    })
    return checks


def iter_pattern_sections(content):
    """Yield (pattern name, section body) for every pattern the guide describes.

    A subsection counts as a pattern when its body carries a "Pattern Views"
    block. That is structural rather than a guess from the title, so a section
    *about* patterns — an orchestration note, an overarching lifecycle summary —
    is not mistaken for one.
    """
    for _, title, body in _heading_blocks(content):
        # Only the section's own prose counts. A body runs to the next heading
        # of the same depth, so it contains its children — and without this a
        # parent section such as "Workflows and Patterns" reads as a pattern
        # because one of its subsections is.
        nested = _HEADING_RE.search(body)
        own = body[:nested.start()] if nested else body
        if not _PATTERN_VIEWS_MARKER_RE.search(own):
            continue
        name = _SECTION_NUMBER_RE.sub("", title).strip().strip("*`")
        # A guide may title the heading "Pattern: <name>"; the label is not part
        # of the name, and dropping the whole heading for carrying it loses a
        # real pattern.
        name = re.sub(r"^Pattern\s*[:—–-]\s*", "", name, flags=re.IGNORECASE).strip()
        if not name or _norm(name) in ("patterns", "pattern views", "pattern mappings"):
            continue
        yield name, body


def extract_described_patterns(content):
    """Patterns the phase output describes, as {name: [view names]}."""
    return {
        name: [v["name"] for v in extract_pattern_views(body) if v.get("name")]
        for name, body in iter_pattern_sections(content)
    }


def _norm(name):
    return re.sub(r"\s+", " ", (name or "")).strip().lower()


def _view_keys(name):
    """The forms a view name may be written in, for comparison.

    A report titles a view with a label and a gloss, and which half the JSON
    kept varies: "Prerequisites (Initial State)" became `Prerequisites`, while
    "Crawl (Basic Mapping)" became `Basic Mapping`. The label is sometimes a
    prefix instead — "Plan - Account Assessment" became `Account Assessment`.
    Every reading is accepted, so what is reported is a genuine difference in
    the inventory rather than a difference in titling convention.
    """
    name = name or ""
    keys = {_norm(name)}
    outer = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", name)
    if outer:
        keys.add(_norm(outer.group(1)))
        keys.add(_norm(outer.group(2)))
    for key in list(keys):
        prefixed = re.match(r"^\S[^:—–-]*\s*[:—–-]\s*(.+)$", key)
        if prefixed:
            keys.add(_norm(prefixed.group(1)))
    return {k for k in keys if k}


def compare_phase_output_with_json(content, data):
    """Report where the phase markdown and the generated JSON disagree.

    The markdown is what anyone reads to understand why a practice looks the
    way it does; the JSON is what ships. When they part company — a pattern
    described and never generated, a view generated and never described —
    anything authored against the prose will not resolve, and nothing else
    reports it.

    Findings are advisory. The prose legitimately describes candidates that
    were later rejected, so an exact match is the wrong bar; what is worth
    knowing is that the difference exists and was not recorded.
    """
    described = extract_described_patterns(content)
    sources = [data] + [p for p in data.get("practices", []) if isinstance(p, dict)]

    generated = {}
    for source in sources:
        for pattern in source.get("patterns", []):
            pname = pattern.get("name")
            if pname:
                generated[pname] = [
                    v.get("name") for v in pattern.get("patternViews", []) if v.get("name")
                ]

    findings = []
    gen_by_norm = {_norm(n): n for n in generated}
    for name, views in sorted(described.items()):
        match = gen_by_norm.get(_norm(name))
        if match is None:
            findings.append({
                "kind": "pattern-not-generated",
                "pattern": name,
                "message": (
                    f"Pattern '{name}' is described in the phase output but the "
                    f"JSON declares no pattern of that name"
                ),
            })
            continue
        # No views parsed is a parser miss, not a disagreement. Reporting every
        # generated view as undescribed would bury the cases that are real.
        if not views:
            continue
        gen_keys = set().union(*(_view_keys(v) for v in generated[match])) \
            if generated[match] else set()
        prose_keys = set().union(*(_view_keys(v) for v in views)) if views else set()
        for original in views:
            if not (_view_keys(original) & gen_keys):
                findings.append({
                    "kind": "view-not-generated",
                    "pattern": match,
                    "view": original,
                    "message": (
                        f"Pattern '{match}' view '{original}' is described in the "
                        f"phase output but not present in the JSON"
                    ),
                })
        for gen_view in generated[match]:
            if not (_view_keys(gen_view) & prose_keys):
                findings.append({
                    "kind": "view-not-described",
                    "pattern": match,
                    "view": gen_view,
                    "message": (
                        f"Pattern '{match}' view '{gen_view}' is in the JSON but "
                        f"not described in the phase output"
                    ),
                })

    described_by_norm = {_norm(n) for n in described}
    # Only report an undescribed pattern where the output describes some, so a
    # guide that covers patterns in a shape this parser does not know is not
    # reported as describing none of them.
    if described:
        for name in sorted(generated):
            if _norm(name) not in described_by_norm and _norm(name) not in _norm(content):
                findings.append({
                    "kind": "pattern-not-described",
                    "pattern": name,
                    "message": (
                        f"Pattern '{name}' is in the JSON but the phase output "
                        f"does not describe it"
                    ),
                })
    return findings


#: An assembled method guide concatenates per-practice guides, each keeping its
#: own `# Phase 2 Mapping Guide: ...` H1 under the method's.
_PRACTICE_SEGMENT_RE = re.compile(r"^#\s+Phase 2 Mapping Guide:", re.MULTILINE)


def validate_pattern_views(content):
    """Validate pattern view completeness: alpha presence and state validity.

    An assembled method guide holds several practices. Validating it as one
    document pools every practice's alphas and views, so the highest-numbered
    view is judged against all 30 alphas in the method and fails for alphas
    that belong to a different practice. Segment first, then validate each
    practice on its own terms.
    """
    segments = [m.start() for m in _PRACTICE_SEGMENT_RE.finditer(content)]
    if len(segments) > 2:  # method header + 2 or more practice guides
        checks = []
        for i, start in enumerate(segments[1:], start=1):
            end = segments[i + 1] if i + 1 < len(segments) else len(content)
            for check in validate_pattern_views(content[start:end]):
                check["check"] = f"p{i}_{check['check']}"
                checks.append(check)
        return checks

    checks = []
    alphas = extract_alphas_and_states(content)
    if not alphas:
        checks.append({
            "check": "pattern_validation",
            "description": "No alphas found in mapping guide to validate against",
            "pass": True,
        })
        return checks

    # Each pattern is judged on its own views and its own alphas. Pooling them
    # makes every pattern's closing view the final view of all of them — two
    # patterns ending at seq 4 both count as "final" — and demands that each
    # carry every alpha in the guide, including alphas belonging to a different
    # lifecycle. Guides that satisfy that demand are how closing views come to
    # hold alphas the pattern never advanced, parked at their opening state.
    sections = list(iter_pattern_sections(content))
    if not sections:
        sections = [(None, content)]

    views = []
    for pattern_name, body in sections:
        section_views = extract_pattern_views(body)
        if not section_views:
            continue
        views.extend(section_views)
        checks.extend(_validate_one_pattern(pattern_name, section_views, alphas))

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

    all_states_used = {}
    for view in views:
        for alpha_name, state_name in view["alpha_states"]:
            all_states_used.setdefault(alpha_name, set()).add(state_name)

    # Practice-level coverage: an alpha should take part in some pattern, not
    # in every pattern (references/pattern-completeness.md, Participation Rule).
    uncovered = sorted(set(alphas) - set(all_states_used))
    checks.append({
        "check": "alpha_pattern_coverage",
        "description": (
            f"{len(alphas) - len(uncovered)}/{len(alphas)} alphas take part in "
            f"at least one pattern"
        ),
        "missing": uncovered,
        "pass": not uncovered,
    })

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


def _validate_one_pattern(pattern_name, views, alphas):
    """Checks for a single pattern's views, judged against the alphas it carries."""
    checks = []
    label = f"{pattern_name}: " if pattern_name else ""
    prefix = f"{_slug(pattern_name)}_" if pattern_name else ""
    expected_alphas = set(alphas.keys())

    # The alphas this pattern carries are the ones it names, not the ones the
    # practice declares. The final view is a snapshot of those.
    carried = {a for v in views for a, _ in v["alpha_states"]}
    # phase-2-skill.md "State Compression Rule": non-final views carry ONLY the
    # alpha states that change from the previous view; unchanged states are
    # implicit carry-forward. Only the final view must be a complete snapshot.
    # Requiring every alpha in every view contradicts that rule and fails
    # correctly-compressed guides.
    final_seq = max(v["seq"] for v in views)

    for view in views:
        view_alphas = {a for a, _ in view["alpha_states"]}
        is_final = view["seq"] == final_seq
        missing = carried - view_alphas
        extra = view_alphas - expected_alphas

        if is_final:
            checks.append({
                "check": f"{prefix}view_{view['seq']}_alpha_count",
                "description": (
                    f"{label}final view {view['seq']} ({view['name']}) is a "
                    f"complete snapshot of the {len(carried)} alphas this "
                    f"pattern carries"
                ),
                "expected": len(carried),
                "actual": len(view_alphas),
                "pass": not missing,
            })
            if missing:
                checks.append({
                    "check": f"{prefix}view_{view['seq']}_missing_alphas",
                    "description": (
                        f"{label}final view {view['seq']} omits alphas this "
                        f"pattern advances"
                    ),
                    "missing": sorted(missing),
                    "pass": False,
                })
        else:
            # A compressed view may legitimately carry a subset, but an empty
            # one should have been eliminated and its activities merged.
            checks.append({
                "check": f"{prefix}view_{view['seq']}_alpha_count",
                "description": (
                    f"{label}view {view['seq']} ({view['name']}): "
                    f"{len(view_alphas)} changed alphas (compressed)"
                ),
                "expected": ">=1",
                "actual": len(view_alphas),
                "pass": len(view_alphas) >= 1,
            })
        if extra:
            # Informational, not scored. A pattern view may legitimately place
            # an *inherited* alpha (redeclared, or merely related) alongside the
            # practice's own. This parser reads only the markdown, so it cannot
            # see the effective context and must not call that a defect.
            checks.append({
                "check": f"{prefix}view_{view['seq']}_alphas_not_declared_here",
                "description": (
                    f"{label}view {view['seq']} names alphas not declared in "
                    f"this guide (expected if they are inherited)"
                ),
                "names": sorted(extra),
            })

        for alpha_name, state_name in view["alpha_states"]:
            if alpha_name in alphas:
                valid_states = alphas[alpha_name]
                if state_name not in valid_states:
                    checks.append({
                        "check": f"{prefix}view_{view['seq']}_invalid_state",
                        "description": (
                            f"{label}view {view['seq']}: invalid state "
                            f"\"{state_name}\" for alpha \"{alpha_name}\""
                        ),
                        "valid_states": valid_states,
                        "pass": False,
                    })

        alpha_counts = {}
        for a, _ in view["alpha_states"]:
            alpha_counts[a] = alpha_counts.get(a, 0) + 1
        for a, count in alpha_counts.items():
            if count > 1:
                # One alpha, one target state per view. Two make the view
                # ambiguous about what it is asking for, and make the walk
                # across views look as though it moves backwards.
                checks.append({
                    "check": f"{prefix}view_{view['seq']}_state_density",
                    "description": (
                        f"{label}view {view['seq']}: alpha \"{a}\" has {count} "
                        f"states (max 1 — split into sub-views)"
                    ),
                    "pass": False,
                })

    return checks


def _slug(name):
    """A check-name fragment from a pattern title."""
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")[:40]


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
    parser.add_argument(
        "--one-line",
        action="store_true",
        help="Print a single-line verdict instead of the full JSON check list",
    )
    parser.add_argument(
        "--check",
        action="append",
        metavar="NAME",
        help=(
            "Report only these checks; repeatable, prefix match. Without it a "
            "single check's findings have to be dug out of the full list."
        ),
    )
    parser.add_argument(
        "--against-json",
        metavar="FILE",
        help=(
            "Compare the phase output's pattern and view inventory against the "
            "generated JSON, and report where they disagree. Advisory: the prose "
            "legitimately describes candidates that were later rejected, so what "
            "matters is that the difference exists and was not recorded."
        ),
    )
    parser.add_argument(
        "--source-manifest",
        metavar="FILE",
        help=(
            "Check every source document is drawn on by the output. Takes an "
            "extract-html-text.py JSON manifest or a newline-delimited source list. "
            "Searches all given files, not just the first."
        ),
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
        checks.extend(validate_prerequisite_order(content))

    if args.source_manifest:
        combined = "\n".join(
            Path(f).read_text(encoding="utf-8", errors="replace")
            for f in args.file if Path(f).exists()
        )
        checks.extend(validate_source_coverage(combined, args.source_manifest))

    if args.against_json:
        combined = "\n".join(
            Path(f).read_text(encoding="utf-8", errors="replace")
            for f in args.file if Path(f).exists()
        )
        try:
            generated = json.loads(Path(args.against_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append({
                "check": "json_agreement",
                "pass": False,
                "detail": f"Could not read {args.against_json}: {exc}",
            })
        else:
            drift = compare_phase_output_with_json(combined, generated)
            checks.append({
                "check": "json_agreement",
                "pass": not drift,
                "detail": (
                    "Phase output and generated JSON agree on the pattern inventory"
                    if not drift
                    else f"{len(drift)} disagreement(s) between the phase output and the JSON"
                ),
                "findings": drift,
            })

    if args.check:
        wanted = tuple(args.check)
        checks = [c for c in checks if c["check"].startswith(wanted)]

    for c in checks:
        if "pass" in c:
            c["severity"] = "critical" if _is_critical(c["check"]) else "advisory"

    # Only checks that actually carry a "pass" key are scored. Informational
    # entries (e.g. competency_level_names) have no verdict and must be excluded
    # from both numerator and denominator, or passed can exceed total.
    passed = sum(1 for c in checks if "pass" in c and c["pass"])
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

    if args.one_line:
        verdict = "PASS" if all_pass else "FAIL"
        names = ", ".join(c["check"] for c in failures)
        detail = f" | failed: {names}" if names else ""
        print(f"{verdict} {passed}/{total} {target}{detail}")
        sys.exit(0 if all_pass else 1)

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
