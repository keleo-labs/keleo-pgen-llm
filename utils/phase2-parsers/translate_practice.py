#!/usr/bin/env python3
"""
Practice JSON Translator - Main orchestrator for Phase 2 translation

Uses all specialized parsers to build complete schema-compliant practice JSON
"""

import json
import sys
from pathlib import Path
from datetime import date
import re

# Import all parsers
sys.path.insert(0, str(Path(__file__).parent))
from alpha_parser import parse_alpha_files
from workproduct_parser import parse_workproduct_file
from activity_parser import parse_activity_file
from pattern_parser import parse_pattern_file
from alias_parser import parse_alias_file

def load_baseline(baseline_path):
    """Load baseline framework."""
    with open(baseline_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_practice_metadata(practice_details_file):
    """Extract practice metadata from 01-practice-details.md."""
    with open(practice_details_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract practice name
    name_match = re.search(r'#+ Practice: (.+)', content)
    if not name_match:
        name_match = re.search(r'\*\*Practice:\*\* (.+)', content)

    practice_name = name_match.group(1).strip() if name_match else "Unknown Practice"

    # Extract description from Overview section
    desc_match = re.search(r'## Overview\s*\n\s*(.+?)(?=\n\n|\n##)', content, re.DOTALL)
    description = ""
    if desc_match:
        desc_text = desc_match.group(1).strip()
        sentences = desc_text.split('.')
        description = sentences[0].strip() + '.' if sentences else desc_text

    # Extract keywords
    keywords = []
    keywords_match = re.search(r'\*\*Keywords:\*\*\s*(.+)', content)
    if keywords_match:
        keywords = [k.strip() for k in keywords_match.group(1).split(',')]

    # Extract tags
    domain_tags = []
    lifecycle_tags = []
    org_tags = []

    tags_section = re.search(r'## Tags\s*(.+?)(?=\n##|\Z)', content, re.DOTALL)
    if tags_section:
        tags_content = tags_section.group(1)

        domain_match = re.search(r'\*\*Domain Tags:\*\*\s*(.+)', tags_content)
        if domain_match:
            domain_tags = [t.strip() for t in domain_match.group(1).split(',')]

        lifecycle_match = re.search(r'\*\*Lifecycle Tags:\*\*\s*(.+)', tags_content)
        if lifecycle_match:
            lifecycle_tags = [t.strip() for t in lifecycle_match.group(1).split(',')]

        org_match = re.search(r'\*\*Organizational Tags:\*\*\s*(.+)', tags_content)
        if org_match:
            org_tags = [t.strip() for t in org_match.group(1).split(',')]

    return {
        "name": practice_name,
        "description": description,
        "keywords": keywords,
        "domainTags": domain_tags,
        "lifecycleTags": lifecycle_tags,
        "organizationalTags": org_tags
    }

def parse_citations(citations_file):
    """Parse citations from 02-citations.md."""
    citations = []

    if not citations_file.exists():
        return citations

    with open(citations_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple APA7 reference parsing (citations are in a reference list)
    # Look for sections like "References" or "Citations"
    refs_match = re.search(r'###? (?:References|Citations)\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    if not refs_match:
        return citations

    refs_content = refs_match.group(1)

    # Parse each reference line (simplified)
    # Pattern: Author(s). (Year). Title. Publisher/URL.
    # This is simplified - real APA parsing is complex
    lines = refs_content.strip().split('\n\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try to extract year
        year_match = re.search(r'\((\d{4}[a-z]?)\)', line)
        year = year_match.group(1) if year_match else None

        # Try to extract title (usually italicized or after year)
        title_match = re.search(r'\*(.+?)\*', line)
        if not title_match and year:
            # Try after year
            title_match = re.search(r'\(\d{4}[a-z]?\)\.\s+(.+?)\.', line)

        title = title_match.group(1).strip() if title_match else line[:100]

        # Extract authors (before year)
        authors = []
        if year:
            author_text = line.split(f'({year})')[0].strip()
            # Simple split on commas/ampersands
            author_parts = re.split(r',\s*&\s*|\s+&\s+|,\s+', author_text)
            authors = [a.strip().rstrip('.') for a in author_parts if a.strip()]

        citations.append({
            "authors": authors if authors else ["Unknown"],
            "date": year,
            "title": title,
            "narrativeTypeName": "Citation Standard"
        })

    return citations

def translate_practice(practice_dir, baseline_path, output_file):
    """
    Translate a practice from Phase 1 modules to schema-compliant JSON.

    Args:
        practice_dir: Path to practice directory (e.g., report-elements/practice-1/)
        baseline_path: Path to baseline framework JSON
        output_file: Where to save the practice JSON
    """

    print(f"\n{'='*70}")
    print(f"Translating Practice: {practice_dir.name}")
    print(f"{'='*70}\n")

    # Load baseline
    print("Loading baseline framework...")
    baseline = load_baseline(baseline_path)
    print(f"  ✓ Loaded {len(baseline.get('alphas', []))} baseline alphas\n")

    # Step 1: Extract metadata
    print("Step 1: Extracting practice metadata...")
    practice_details_file = practice_dir / "01-practice-details.md"
    metadata = extract_practice_metadata(practice_details_file)
    print(f"  ✓ Practice: {metadata['name']}\n")

    # Step 2: Parse citations
    print("Step 2: Parsing citations...")
    citations_file = practice_dir / "02-citations.md"
    citations = parse_citations(citations_file)
    print(f"  ✓ Parsed {len(citations)} citations\n")

    # Step 3: Parse alphas
    print("Step 3: Parsing alphas...")
    alpha_files = []
    # Check for split files (03a, 03b, 03c) or single file (03-alphas.md)
    for alpha_file in ["03-alphas.md", "03a-alphas-solution.md", "03b-alphas-endeavor.md", "03c-alphas-value.md"]:
        file_path = practice_dir / alpha_file
        if file_path.exists():
            alpha_files.append(str(file_path))

    alphas, alpha_instances = parse_alpha_files(alpha_files)
    print(f"  ✓ Parsed {len(alphas)} alphas, {len(alpha_instances)} instances\n")

    # Step 4: Parse work products
    print("Step 4: Parsing work products...")
    workproducts_file = practice_dir / "04-workproducts.md"
    work_products, wp_instances = parse_workproduct_file(str(workproducts_file))
    print(f"  ✓ Parsed {len(work_products)} work products\n")

    # Step 5: Parse activities
    print("Step 5: Parsing activities...")
    activities_file = practice_dir / "05-activities-roles.md"
    activities, personas, teams = parse_activity_file(str(activities_file))
    print(f"  ✓ Parsed {len(activities)} activities, {len(personas)} personas, {len(teams)} teams\n")

    # Step 6: Parse patterns
    print("Step 6: Parsing patterns...")
    patterns_file = practice_dir / "06-patterns.md"
    patterns, pattern_instances = parse_pattern_file(str(patterns_file))
    print(f"  ✓ Parsed {len(patterns)} patterns with {len(pattern_instances)} instances\n")

    # Step 7: Parse aliases
    print("Step 7: Parsing aliases...")
    aliases_file = practice_dir / "07-aliases.md"
    aliases = []
    if aliases_file.exists():
        aliases = parse_alias_file(str(aliases_file))
    print(f"  ✓ Parsed {len(aliases)} aliases\n")

    # Step 8: Assemble practice JSON
    print("Step 8: Assembling practice JSON...")

    # Merge all alpha instances (from alphas and patterns)
    all_alpha_instances = {}
    for inst in alpha_instances:
        key = (inst["instanceName"], inst["alphaName"])
        all_alpha_instances[key] = inst
    for inst in pattern_instances:
        key = (inst["instanceName"], inst["alphaName"])
        all_alpha_instances[key] = inst

    merged_alpha_instances = list(all_alpha_instances.values())

    practice_json = {
        "name": metadata["name"],
        "description": metadata["description"],
        "baselinePracticeName": "Platform Adoption Essentials",
        "tags": {
            "domainTags": metadata["domainTags"],
            "lifecycleTags": metadata["lifecycleTags"],
            "organizationalTags": metadata["organizationalTags"]
        },
        "practiceDependencyNames": [],
        "authors": ["Claude Code Translation - Phase 2"],
        "createdAt": date.today().strftime('%Y-%m-%d'),
        "updatedAt": date.today().strftime('%Y-%m-%d'),
        "version": "1.0",
        "keywords": metadata["keywords"],
        "alphas": alphas,
        "workProducts": work_products,
        "activities": activities,
        "activitySpaces": [],  # Would need to extract from baseline
        "patterns": patterns,
        "narratives": [],  # Practice-level narratives if any
        "citations": citations,
        "alphaInstances": merged_alpha_instances,
        "workProductInstances": wp_instances,
        "practiceElementAliases": aliases
    }

    # Add personas as personaGroups (simplified)
    if personas:
        practice_json["personaGroups"] = personas

    # Step 9: Save JSON
    print("Step 9: Saving practice JSON...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(practice_json, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved to: {output_file}\n")

    # Print summary
    print(f"\n{'='*70}")
    print(f"Translation Complete!")
    print(f"{'='*70}")
    print(f"  Practice: {metadata['name']}")
    print(f"  Alphas: {len(alphas)} ({len(merged_alpha_instances)} instances)")
    print(f"  Work Products: {len(work_products)} ({len(wp_instances)} instances)")
    print(f"  Activities: {len(activities)}")
    print(f"  Patterns: {len(patterns)}")
    print(f"  Citations: {len(citations)}")
    print(f"  Aliases: {len(aliases)}")
    print(f"  Output: {output_file}")
    print(f"{'='*70}\n")

    return practice_json

def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print("Usage: python translate_practice.py <practice-dir> <baseline-path> <output-file>")
        print("\nExample:")
        print("  python translate_practice.py \\")
        print("    practices/my-practice/report-elements/practice-1 \\")
        print("    deps/platform-adoption-kernel.json \\")
        print("    practices/my-practice/practice-1.json")
        sys.exit(1)

    practice_dir = Path(sys.argv[1])
    baseline_path = Path(sys.argv[2])
    output_file = Path(sys.argv[3])

    if not practice_dir.exists():
        print(f"ERROR: Practice directory not found: {practice_dir}")
        sys.exit(1)

    if not baseline_path.exists():
        print(f"ERROR: Baseline framework not found: {baseline_path}")
        sys.exit(1)

    translate_practice(practice_dir, baseline_path, output_file)

if __name__ == "__main__":
    main()
