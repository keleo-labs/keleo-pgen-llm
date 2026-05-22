#!/usr/bin/env python3
"""
Method Assembler - Combines multiple practices into a method JSON

Assembles a complete method from individual practice JSON files
"""

import json
import sys
import re
from pathlib import Path
from datetime import date

def extract_method_metadata(method_plan_file):
    """Extract method metadata from 00-method-plan.md."""
    with open(method_plan_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract method name - prefer explicit "Method Name:" over header
    name_match = re.search(r'\*\*Method Name:\*\*\s+(.+)', content)
    if not name_match:
        name_match = re.search(r'\*\*Method:\*\*\s+(.+)', content)
    if not name_match:
        # Fallback to header pattern
        name_match = re.search(r'#+ (.+?) (?:Method Planning|- Method Planning)', content)

    method_name = name_match.group(1).strip() if name_match else "Unknown Method"

    # Extract description - prefer explicit "Description:" in Method Overview section
    desc_match = re.search(r'\*\*Description:\*\*\s+(.+?)(?=\n\n|\n\*\*)', content, re.DOTALL)
    description = ""
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        # Fallback to Executive Summary
        desc_match = re.search(r'## Executive Summary\s*\n\s*(.+?)(?=\n\n|\n##)', content, re.DOTALL)
        if desc_match:
            desc_text = desc_match.group(1).strip()
            sentences = desc_text.split('.')
            description = sentences[0].strip() + '.' if sentences else desc_text

    return {
        "name": method_name,
        "description": description
    }

def assemble_method(method_dir, practice_files, output_file):
    """
    Assemble a method from multiple practice JSON files.

    Args:
        method_dir: Path to method directory
        practice_files: List of paths to practice JSON files
        output_file: Where to save the method JSON
    """

    print(f"\n{'='*70}")
    print(f"Assembling Method from {len(practice_files)} Practices")
    print(f"{'='*70}\n")

    # Load method metadata
    print("Loading method metadata...")
    method_plan_file = method_dir / "report-elements" / "00-method-plan.md"
    metadata = extract_method_metadata(method_plan_file)
    print(f"  ✓ Method: {metadata['name']}\n")

    # Load all practice JSONs
    print("Loading practice JSONs...")
    practices = []
    for i, practice_file in enumerate(practice_files, 1):
        print(f"  Loading Practice {i}: {practice_file.name}")
        with open(practice_file, 'r', encoding='utf-8') as f:
            practice_json = json.load(f)
            practices.append(practice_json)
            print(f"    ✓ {practice_json['name']}")

    print()

    # Aggregate citations (deduplicate by title)
    print("Aggregating citations...")
    all_citations = {}
    for practice in practices:
        for citation in practice.get('citations', []):
            title = citation.get('title', '')
            if title and title not in all_citations:
                all_citations[title] = citation

    citations = list(all_citations.values())
    print(f"  ✓ {len(citations)} unique citations across all practices\n")

    # Assemble method JSON
    print("Assembling method JSON...")
    method_json = {
        "name": metadata["name"],
        "description": metadata["description"],
        "baselinePracticeName": "Platform Adoption Essentials",
        "practices": practices,
        "citations": citations,
        "authors": ["Claude Code Translation - Phase 2"],
        "createdAt": date.today().strftime('%Y-%m-%d'),
        "updatedAt": date.today().strftime('%Y-%m-%d'),
        "version": "1.0"
    }

    # Save method JSON
    print("Saving method JSON...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(method_json, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved to: {output_file}\n")

    # Print summary
    total_alphas = sum(len(p.get('alphas', [])) for p in practices)
    total_activities = sum(len(p.get('activities', [])) for p in practices)
    total_work_products = sum(len(p.get('workProducts', [])) for p in practices)
    total_patterns = sum(len(p.get('patterns', [])) for p in practices)

    print(f"\n{'='*70}")
    print(f"Method Assembly Complete!")
    print(f"{'='*70}")
    print(f"  Method: {metadata['name']}")
    print(f"  Practices: {len(practices)}")
    for i, practice in enumerate(practices, 1):
        print(f"    {i}. {practice['name']}")
    print(f"\n  Total Alphas: {total_alphas}")
    print(f"  Total Work Products: {total_work_products}")
    print(f"  Total Activities: {total_activities}")
    print(f"  Total Patterns: {total_patterns}")
    print(f"  Total Citations: {len(citations)}")
    print(f"\n  Output: {output_file}")
    print(f"{'='*70}\n")

    return method_json

def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print("Usage: python assemble_method.py <method-dir> <output-file> <practice1.json> [<practice2.json> ...]")
        print("\nExample:")
        print("  python assemble_method.py \\")
        print("    practices/red-hat-ansible-automation-platform \\")
        print("    practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json \\")
        print("    practices/red-hat-ansible-automation-platform/practice-1.json \\")
        print("    practices/red-hat-ansible-automation-platform/practice-2.json")
        sys.exit(1)

    method_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    practice_files = [Path(f) for f in sys.argv[3:]]

    if not method_dir.exists():
        print(f"ERROR: Method directory not found: {method_dir}")
        sys.exit(1)

    for practice_file in practice_files:
        if not practice_file.exists():
            print(f"ERROR: Practice file not found: {practice_file}")
            sys.exit(1)

    assemble_method(method_dir, practice_files, output_file)

if __name__ == "__main__":
    main()
