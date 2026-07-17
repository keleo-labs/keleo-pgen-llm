#!/usr/bin/env python3
"""
Fix validation errors in horticulture-essentials baseline JSON.
"""

import json
from pathlib import Path

def fix_narratives(narratives):
    """Fix narrative structure to match schema."""
    fixed = []
    for i, narrative in enumerate(narratives):
        # Narratives are PracticeElements - need name and description
        fixed_narrative = {
            "name": f"Horticulture Essentials Baseline Narrative",
            "description": "The transformational journey of horticulture from fragmented craft to integrated science-driven profession",
            "narrativeTypeName": narrative["narrativeTypeName"],
            "narrativeContexts": []
        }

        # Fix narrative contexts
        for j, context in enumerate(narrative.get("narrativeContexts", [])):
            fixed_context = {
                "seq": j + 1,
                "narrativeElementName": context["narrativeElementName"],
                "context": context.get("contextText", context.get("context", ""))
            }
            fixed_narrative["narrativeContexts"].append(fixed_context)

        fixed.append(fixed_narrative)

    return fixed

def fix_citations(citations):
    """Fix citation structure to match schema."""
    fixed = []
    for i, citation in enumerate(citations):
        # Citations are PracticeElements with specific required fields
        # Extract author names - handle both string and already-parsed formats
        author_text = citation.get("author", "")
        if isinstance(author_text, str):
            # Parse author text into array
            authors = [author_text]
        else:
            authors = author_text

        fixed_citation = {
            "name": citation.get("title", f"Citation {i+1}")[:100],  # Use title as name (truncated)
            "description": f"Citation for {citation.get('title', 'source material')}",
            "authors": authors,
            "date": citation.get("date", ""),
            "title": citation.get("title", ""),
            "source": citation.get("source", "")
        }

        fixed.append(fixed_citation)

    return fixed

def main():
    """Main fix function."""
    print("Loading baseline JSON...")
    baseline_path = Path('baselines/horticulture-essentials/horticulture-essentials.json')
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)

    print("Fixing narratives...")
    if "narratives" in baseline and baseline["narratives"]:
        baseline["narratives"] = fix_narratives(baseline["narratives"])
        print(f"  Fixed {len(baseline['narratives'])} narrative(s)")

    print("Fixing citations...")
    if "citations" in baseline and baseline["citations"]:
        baseline["citations"] = fix_citations(baseline["citations"])
        print(f"  Fixed {len(baseline['citations'])} citation(s)")

    print("Writing fixed baseline JSON...")
    with open(baseline_path, 'w') as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print("\n=== Fixes Complete ===")
    print(f"Baseline JSON written to: {baseline_path}")

if __name__ == "__main__":
    main()
