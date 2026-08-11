#!/usr/bin/env python3
"""
Assemble per-practice mapping guide files into a single method mapping guide.

Auto-generates a method header with practice summary table by parsing each
practice guide's metadata, then concatenates all guides with separators.

Usage:
    python3 utils/assemble-mapping-guide.py \\
        --name "Programme Management Foundations" \\
        --baseline-name "Programme Essentials" \\
        --guides practices/pmf/02-mapping-guide-practice-1.md \\
                 practices/pmf/02-mapping-guide-practice-2.md \\
        -o practices/pmf/02-mapping-guide.md

    # With parent practice
    python3 utils/assemble-mapping-guide.py \\
        --name "Programme Management Foundations" \\
        --baseline-name "Programme Essentials" \\
        --parent-name "Project Management Foundations" \\
        --guides g1.md g2.md g3.md g4.md g5.md \\
        -o output.md

    # Include word/line stats
    python3 utils/assemble-mapping-guide.py ... --stats
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path


def extract_practice_metadata(content):
    """Extract metadata from a practice mapping guide."""
    meta = {
        "name": None,
        "focus": None,
        "primary_alpha": None,
        "alpha_count": 0,
        "redecl_count": 0,
        "new_count": 0,
        "activity_count": 0,
        "wp_count": 0,
        "new_alphas": [],
    }

    name_match = re.search(r"\*\*Name:\*\*\s*(.+)", content)
    if name_match:
        meta["name"] = name_match.group(1).strip()
    else:
        h1_match = re.search(r"^# .+:\s*(.+?)(?:\s*\(Practice \d+\))?$", content, re.MULTILINE)
        if h1_match:
            meta["name"] = h1_match.group(1).strip()

    primary_match = re.search(r"\*\*Primary Alpha\*\*:\s*(.+?)(?:\s*[—–-]|$)", content)
    if primary_match:
        meta["primary_alpha"] = primary_match.group(1).strip()

    total_match = re.search(r"\*\*Total Alphas\*\*:\s*(\d+)\s*\((\d+)\s*redecl[a-z]*\s*\+\s*(\d+)\s*(?:new|special)", content)
    if total_match:
        meta["alpha_count"] = int(total_match.group(1))
        meta["redecl_count"] = int(total_match.group(2))
        meta["new_count"] = int(total_match.group(3))
    else:
        redecl_blocks = re.findall(r"\*\*Alpha:\s*.+?\*\*\s*\(Redeclaration", content)
        new_blocks = re.findall(r"\*\*Alpha:\s*.+?\*\*\s*\((?:Specialization|New)", content)
        meta["redecl_count"] = len(redecl_blocks)
        meta["new_count"] = len(new_blocks)
        meta["alpha_count"] = meta["redecl_count"] + meta["new_count"]

    focus_match = re.search(r"\*\*Focus Distribution\*\*:\s*(.+)", content)
    if focus_match:
        dist = focus_match.group(1)
        focuses = re.findall(r"(\w[\w\s]*?):\s*(\d+)", dist)
        max_focus = max(focuses, key=lambda x: int(x[1]), default=None)
        if max_focus:
            meta["focus"] = max_focus[0].strip()

    new_alpha_match = re.search(r"\*\*New Specialized Alphas\*\*:\s*\d+\s*\((.+?)\)", content)
    if new_alpha_match:
        pairs = re.findall(r"([\w\s]+?)\s*→\s*([\w\s]+?)(?:,|$)", new_alpha_match.group(1))
        meta["new_alphas"] = [{"name": n.strip(), "contributesTo": c.strip()} for n, c in pairs]

    activity_headers = re.findall(r"^####\s*Activity\s*\d", content, re.MULTILINE)
    if not activity_headers:
        activity_headers = re.findall(r"^\*\*Activity:\s", content, re.MULTILINE)
    meta["activity_count"] = len(activity_headers)

    wp_headers = re.findall(r"^####\s*Work Product\s*\d", content, re.MULTILINE)
    if not wp_headers:
        wp_headers = re.findall(r"^\*\*Work Product:\s", content, re.MULTILINE)
    meta["wp_count"] = len(wp_headers)

    decision_match = re.search(r"\*\*Decision\*\*:\s*(.+)", content)
    if decision_match:
        decision = decision_match.group(1).strip().lower()
        if "orchestrat" in decision:
            meta["focus"] = meta.get("focus") or "Orchestration"
            if meta["alpha_count"] == 0:
                pass

    return meta


def extract_new_alpha_states(content):
    """Extract state counts for new/specialized alphas."""
    results = []
    blocks = re.split(r"\*\*Alpha:\s*", content)
    for block in blocks[1:]:
        name_match = re.match(r"(.+?)\*\*\s*\((?:Specialization|New)", block)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        contributes_match = re.search(r"\*\*contributesTo:\*\*\s*(.+)", block)
        contributes_to = contributes_match.group(1).strip() if contributes_match else "?"
        state_count = len(re.findall(r"\*\*State:\s", block))
        results.append({"name": name, "contributesTo": contributes_to, "states": state_count})
    return results


def generate_header(name, baseline_name, parent_name, practice_metas, new_alphas_detail):
    """Generate method header with summary tables."""
    lines = []
    lines.append(f"# Phase 2 Mapping Guide: {name} (Method)")
    lines.append("")
    lines.append("## Method Metadata")
    lines.append(f"- **Mapping Date**: {date.today()}")
    lines.append(f"- **Method Name**: {name}")
    lines.append(f"- **Method Kind**: method")
    lines.append(f"- **Baseline Practice**: {baseline_name}")
    if parent_name:
        lines.append(f"- **Parent Practice**: {parent_name}")

    domain_count = sum(1 for m in practice_metas if (m.get("focus") or "").lower() not in ("orchestration",))
    orch_count = sum(1 for m in practice_metas if (m.get("focus") or "").lower() == "orchestration")
    parts = []
    if domain_count:
        parts.append(f"{domain_count} domain")
    if orch_count:
        parts.append(f"{orch_count} orchestration")
    lines.append(f"- **Practice Count**: {len(practice_metas)} ({' + '.join(parts)})")
    lines.append("")

    lines.append("## Practice Summary")
    lines.append("")
    lines.append("| # | Practice Name | Focus | Primary Alpha | Alphas | Activities | Work Products |")
    lines.append("|---|--------------|-------|--------------|--------|-----------|---------------|")

    total_alphas = 0
    total_activities = 0
    total_wps = 0
    for i, m in enumerate(practice_metas, 1):
        pname = m.get("name") or f"Practice {i}"
        focus = m.get("focus") or "—"
        primary = m.get("primary_alpha") or "—"
        ac = m["alpha_count"]
        rc = m["redecl_count"]
        nc = m["new_count"]
        alpha_desc = f"{ac} ({rc} redecl + {nc} new)" if ac > 0 else "0"
        act = m["activity_count"]
        wp = m["wp_count"]
        lines.append(f"| {i} | {pname} | {focus} | {primary} | {alpha_desc} | {act} | {wp} |")
        total_alphas += ac
        total_activities += act
        total_wps += wp

    lines.append(f"| **Total** | | | | **{total_alphas}** | **{total_activities}** | **{total_wps}** |")
    lines.append("")

    if new_alphas_detail:
        lines.append("## New Specialized Alphas")
        lines.append("")
        lines.append("| Alpha | contributesTo | Practice | States |")
        lines.append("|-------|--------------|---------|--------|")
        for na in new_alphas_detail:
            lines.append(f"| {na['name']} | {na['contributesTo']} | {na['practice_idx']} | {na['states']} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Assemble per-practice mapping guides into a method mapping guide"
    )
    parser.add_argument("--name", required=True, help="Method name")
    parser.add_argument("--baseline-name", required=True, help="Baseline practice name")
    parser.add_argument("--parent-name", help="Parent practice name (if extending)")
    parser.add_argument("--guides", nargs="+", required=True, help="Practice mapping guide file paths (order matters)")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--stats", action="store_true", help="Print word/line statistics for each input file")
    args = parser.parse_args()

    practice_metas = []
    all_new_alphas = []
    guide_contents = []

    for i, path in enumerate(args.guides, 1):
        p = Path(path)
        if not p.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)

        content = p.read_text()
        guide_contents.append(content)

        meta = extract_practice_metadata(content)
        practice_metas.append(meta)

        new_alphas = extract_new_alpha_states(content)
        for na in new_alphas:
            na["practice_idx"] = i
        all_new_alphas.extend(new_alphas)

        if args.stats:
            words = len(content.split())
            line_count = content.count("\n")
            print(f"Practice {i} ({meta.get('name', p.name)}): {words} words, {line_count} lines")

    header = generate_header(args.name, args.baseline_name, args.parent_name, practice_metas, all_new_alphas)

    combined = header
    for i, content in enumerate(guide_contents):
        combined += content
        if i < len(guide_contents) - 1:
            combined += "\n\n---\n\n"

    Path(args.output).write_text(combined)

    total_words = len(combined.split())
    total_lines = combined.count("\n")
    print(f"\nMethod mapping guide assembled: {args.output}")
    print(f"  Practices: {len(practice_metas)}")
    print(f"  Total words: {total_words}")
    print(f"  Total lines: {total_lines}")
    for i, m in enumerate(practice_metas, 1):
        print(f"  Practice {i}: {m.get('name', '?')} — {m['alpha_count']} alphas, {m['activity_count']} activities, {m['wp_count']} work products")


if __name__ == "__main__":
    main()
