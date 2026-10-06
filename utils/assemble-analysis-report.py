#!/usr/bin/env python3
"""
Assemble partial Phase 1 analysis reports into a single 01-analysis-report.md.

Large source corpora (dozens of documentation guides) exceed what one Phase 1
subagent can read without quality degradation. The orchestrator splits the
corpus into clusters, runs one analyst per cluster against the standard Phase 1
section template, then merges the partials here.

Merging is purely mechanical: sections are matched to the canonical Phase 1
section list by keyword, subsections are renumbered sequentially across
partials, and citations are deduplicated by title. No content is rewritten --
semantic synthesis stays in the LLM layer.

Usage:
    python3 utils/assemble-analysis-report.py \\
        --name "Red Hat Developer Hub 1.10" \\
        --partials practices/rhdh/_phase1-cluster-*.md \\
        -o practices/rhdh/01-analysis-report.md --stats

    # Record the sources line and the preliminary structure verdict
    python3 utils/assemble-analysis-report.py ... \\
        --sources "36 Red Hat Developer Hub 1.10 documentation guides" \\
        --structure "Likely Multiple Practices"
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

#: Canonical Phase 1 sections, in report order. Each entry is
#: (section number, canonical title, keywords matched against a partial's
#: ``## N. Title`` heading after lowercasing).
CANONICAL_SECTIONS = [
    (1, "Outcomes", ("outcome",)),
    (2, "Concerns (Areas of Attention)", ("concern",)),
    (3, "Work Products", ("work product",)),
    (4, "Activities", ("activit",)),
    (5, "Competencies", ("competenc",)),
    (6, "Personas", ("persona",)),            # checked after persona groups
    (7, "Persona Groups (Teams)", ("persona group", "team")),
    (8, "Workflows and Patterns", ("workflow", "pattern")),
    (9, "Practices", ("practice",)),
    (10, "Reference Content Candidates", ("reference",)),
    (11, "Citations", ("citation",)),
]

#: Match order matters -- "Persona Groups" must win over "Personas".
MATCH_ORDER = [7, 6, 2, 3, 1, 4, 5, 8, 9, 10, 11]

HEADING_RE = re.compile(r"^(#{2,3})\s+(.*?)\s*$", re.MULTILINE)
#: Leading numbering on a heading, e.g. "2.3 " or "10.1. " -- stripped so the
#: assembler can renumber consistently.
NUMBER_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")


def classify_heading(title):
    """Map a partial's ``## `` heading text to a canonical section number.

    Returns None when the heading matches nothing, so the caller can preserve
    it in an appendix rather than silently dropping content.
    """
    lowered = NUMBER_PREFIX_RE.sub("", title).lower()
    for num in MATCH_ORDER:
        _, _, keywords = next(s for s in CANONICAL_SECTIONS if s[0] == num)
        if any(kw in lowered for kw in keywords):
            return num
    return None


def split_sections(content):
    """Split a partial into ``## `` sections.

    Returns:
        tuple[str, list[dict]]: Preamble text before the first ``## `` heading,
        and a list of {"title", "body"} dicts in document order.
    """
    matches = [m for m in HEADING_RE.finditer(content) if len(m.group(1)) == 2]
    if not matches:
        return content, []

    preamble = content[: matches[0].start()]
    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections.append({"title": m.group(2), "body": content[m.end():end]})
    return preamble, sections


def split_subsections(body):
    """Split a section body into leading text plus ``### `` subsections."""
    matches = [m for m in HEADING_RE.finditer(body) if len(m.group(1)) == 3]
    if not matches:
        return body.strip(), []

    lead = body[: matches[0].start()].strip()
    subs = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        subs.append({
            "title": NUMBER_PREFIX_RE.sub("", m.group(2)).strip(),
            "body": body[m.end():end].strip(),
        })
    return lead, subs


def citation_key(title):
    """Normalise a citation subsection title for duplicate detection."""
    stripped = re.sub(r"^\[\d+\]\s*", "", title)
    return re.sub(r"[^a-z0-9]+", " ", stripped.lower()).strip()


def collect(partial_paths):
    """Read partials and bucket their subsections by canonical section number.

    Returns:
        tuple[dict, list, list]: section number -> list of subsection dicts
        (each carrying its originating cluster), unmatched sections preserved
        for the appendix, and per-file statistics.
    """
    buckets = {num: {"lead": [], "subs": []} for num, _, _ in CANONICAL_SECTIONS}
    unmatched = []
    stats = []

    for path_str in partial_paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Error: partial not found: {path}", file=sys.stderr)
            sys.exit(1)
        content = path.read_text(encoding="utf-8")
        cluster = path.stem
        _, sections = split_sections(content)
        if not sections:
            print(f"Warning: no '## ' sections found in {path}", file=sys.stderr)

        matched_count = 0
        for section in sections:
            num = classify_heading(section["title"])
            lead, subs = split_subsections(section["body"])
            if num is None:
                unmatched.append({"cluster": cluster,
                                  "title": NUMBER_PREFIX_RE.sub("", section["title"]).strip(),
                                  "lead": lead, "subs": subs})
                continue
            matched_count += 1
            if lead:
                buckets[num]["lead"].append((cluster, lead))
            for sub in subs:
                sub["cluster"] = cluster
                buckets[num]["subs"].append(sub)

        stats.append({
            "file": str(path),
            "words": len(content.split()),
            "lines": content.count("\n") + 1,
            "sections": len(sections),
            "matched": matched_count,
        })

    return buckets, unmatched, stats


def render(name, buckets, unmatched, partial_paths, sources, structure, analyst):
    """Render the merged report.

    Returns:
        tuple[str, dict]: The rendered markdown, and section number -> count of
        subsections actually written (post-deduplication).
    """
    written = {}
    out = [
        f"# Phase 1 Analysis Report: {name}",
        "",
        "## Metadata",
        f"- **Analysis Date**: {date.today().isoformat()}",
        f"- **Source Materials**: {sources}",
        f"- **Preliminary Structure**: {structure}",
        f"- **Analyst**: {analyst}",
        f"- **Assembled From**: {len(partial_paths)} cluster analyses "
        f"({', '.join(Path(p).stem for p in partial_paths)})",
        "",
    ]

    for num, title, _ in CANONICAL_SECTIONS:
        bucket = buckets[num]
        out.append(f"## {num}. {title}")
        out.append("")
        for cluster, lead in bucket["lead"]:
            out.append(lead)
            out.append("")

        seen_citations = set()
        index = 0
        for sub in bucket["subs"]:
            if num == 11:
                key = citation_key(sub["title"])
                if key in seen_citations:
                    continue
                seen_citations.add(key)
            index += 1
            out.append(f"### {num}.{index} {sub['title']}")
            out.append("")
            if sub["body"]:
                out.append(sub["body"])
                out.append("")
        written[num] = index
        if index == 0 and not bucket["lead"]:
            out.append(f"_No {title.lower()} were identified across the analysed clusters._")
            out.append("")

    if unmatched:
        out.append("## 12. Additional Cluster Findings")
        out.append("")
        out.append(
            "Sections from cluster analyses that fall outside the standard "
            "Phase 1 structure, preserved verbatim."
        )
        out.append("")
        for i, section in enumerate(unmatched, start=1):
            out.append(f"### 12.{i} {section['title']} ({section['cluster']})")
            out.append("")
            if section["lead"]:
                out.append(section["lead"])
                out.append("")
            for sub in section["subs"]:
                out.append(f"#### {sub['title']}")
                out.append("")
                out.append(sub["body"])
                out.append("")

    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n", written


#: Sub-blocks within a concern that carry cross-cluster wiring. Matched
#: case-insensitively against `#### ` headings inside Section 2.
RELATIONSHIP_HEADINGS = ("concern relationship", "relationship")


def render_digest(partial_paths):
    """Render a compact cross-cluster digest from the partials.

    Parallel Phase 2 agents each need to know what the *other* clusters found
    without reading the whole assembled report, which for a large corpus can run
    to tens of thousands of words. This pulls just the concern names, their
    one-line descriptions, and the relationship blocks each analyst wrote.
    """
    out = [
        "# Cross-Cluster Digest",
        "",
        "Concern inventory and relationship map across all clusters, extracted from the "
        "Phase 1 partials. Read this for cross-practice awareness; read your own cluster's "
        "partial for depth.",
        "",
    ]

    for path_str in partial_paths:
        path = Path(path_str)
        content = path.read_text(encoding="utf-8")
        _, sections = split_sections(content)
        concerns = next((s for s in sections if classify_heading(s["title"]) == 2), None)
        if not concerns:
            continue

        out.append(f"## {path.stem}")
        out.append("")
        _, subs = split_subsections(concerns["body"])
        for sub in subs:
            out.append(f"**{sub['title']}** — {_first_description(sub['body'])}")
            out.append("")
            for heading, block in _nested_blocks(sub["body"]):
                if any(k in heading.lower() for k in RELATIONSHIP_HEADINGS):
                    out.append(block.strip())
                    out.append("")

    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def _first_description(body):
    """Pull the first Description field, or the first non-empty line."""
    match = re.search(r"\*\*Description:?\*\*:?\s*(.+)", body)
    if match:
        return match.group(1).strip()
    for line in body.splitlines():
        if line.strip() and not line.startswith("#"):
            return line.strip()
    return "(no description)"


#: HEADING_RE deliberately caps at `###` so section splitting ignores deeper
#: levels; nested-block extraction needs its own pattern for `#### `.
SUBHEADING_RE = re.compile(r"^(#{4})\s+(.*?)\s*$", re.MULTILINE)


def _nested_blocks(body):
    """Yield (heading, block) pairs for ``#### `` headings inside a subsection."""
    matches = list(SUBHEADING_RE.finditer(body))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        yield m.group(2), body[m.end():end]


def build_parser():
    parser = argparse.ArgumentParser(
        description="Assemble partial Phase 1 analysis reports into one report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", required=True, help="Methodology name for the report title")
    parser.add_argument("--partials", nargs="+", required=True,
                        help="Partial analysis file paths (order matters)")
    parser.add_argument("-o", "--output", required=True, help="Output report path")
    parser.add_argument("--sources", default="See cluster analyses",
                        help="Text for the Source Materials metadata line")
    parser.add_argument("--structure", default="Likely Multiple Practices",
                        help="Text for the Preliminary Structure metadata line")
    parser.add_argument("--analyst", default="Phase 1 cluster analysts",
                        help="Text for the Analyst metadata line")
    parser.add_argument("--stats", action="store_true",
                        help="Print per-partial word/line/section statistics")
    parser.add_argument("--digest", metavar="FILE",
                        help=(
                            "Also write a compact cross-cluster digest to FILE: each "
                            "cluster's concern names, descriptions and relationship blocks. "
                            "For parallel Phase 2 agents that need cross-practice awareness "
                            "without the full report."
                        ))
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    buckets, unmatched, stats = collect(args.partials)
    report, counts = render(args.name, buckets, unmatched, args.partials,
                            args.sources, args.structure, args.analyst)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    if args.stats:
        print(f"{'file':<70} {'words':>8} {'lines':>7} {'sects':>6} {'matched':>8}")
        for s in stats:
            print(f"{s['file']:<70} {s['words']:>8} {s['lines']:>7} "
                  f"{s['sections']:>6} {s['matched']:>8}")
        print()

    if args.digest:
        digest = render_digest(args.partials)
        digest_path = Path(args.digest)
        digest_path.parent.mkdir(parents=True, exist_ok=True)
        digest_path.write_text(digest, encoding="utf-8")
        print(f"Wrote {digest_path} ({len(digest.split())} words, digest)")

    print(f"Wrote {out_path} ({len(report.split())} words)")
    for num, title, _ in CANONICAL_SECTIONS:
        print(f"  {num:>2}. {title:<32} {counts[num]:>3} subsections")
    if unmatched:
        print(f"  12. Additional Cluster Findings      {len(unmatched):>3} sections")


if __name__ == "__main__":
    main()
