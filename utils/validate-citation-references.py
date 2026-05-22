#!/usr/bin/env python3
"""
Validate citation references in Practice Language JSON.

Ensures all citationNames in narratives exactly match Citation.name values
from the citations array.

Usage:
    python3 validate-citation-references.py <practice-json-file>

Exit codes:
    0 - All citation references valid
    1 - Validation errors found
    2 - File not found or invalid JSON
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import difflib


def load_json(file_path: Path) -> dict:
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {file_path}: {e}")
        sys.exit(2)


def extract_valid_citations(practice: dict) -> Set[str]:
    """Extract all valid Citation.name values from practice."""
    citations = practice.get('citations', [])
    return {c['name'] for c in citations if 'name' in c}


def find_narrative_citations(element: dict, element_type: str, element_name: str) -> List[Tuple[str, str, List[str]]]:
    """
    Extract all citationNames from narratives in an element.

    Returns list of (context, narrative_name, [citation_names]) tuples.
    """
    results = []

    # Check narratives array
    narratives = element.get('narratives', [])
    for narrative in narratives:
        narrative_name = narrative.get('name', 'unnamed narrative')
        citation_names = narrative.get('citationNames', [])
        if citation_names:
            context = f"{element_type}[{element_name}].narratives[{narrative_name}]"
            results.append((context, narrative_name, citation_names))

    # Check techniqueNarratives (for Activities)
    technique_narratives = element.get('techniqueNarratives', [])
    for narrative in technique_narratives:
        narrative_name = narrative.get('name', 'unnamed technique narrative')
        citation_names = narrative.get('citationNames', [])
        if citation_names:
            context = f"{element_type}[{element_name}].techniqueNarratives[{narrative_name}]"
            results.append((context, narrative_name, citation_names))

    return results


def validate_practice(practice: dict) -> Tuple[int, int]:
    """
    Validate all citation references in practice.

    Returns (total_checked, error_count) tuple.
    """
    # Get valid citation names
    valid_citations = extract_valid_citations(practice)

    if not valid_citations:
        print("WARNING: No citations found in practice")
        print("  If practice has narratives with citationNames, this will fail")
        print()

    print(f"Valid citations: {len(valid_citations)}")
    print()

    total_checked = 0
    error_count = 0

    # Check all element types that can have narratives
    element_types = [
        ('alphas', 'Alpha'),
        ('workProducts', 'WorkProduct'),
        ('activities', 'Activity'),
        ('patterns', 'Pattern')
    ]

    for elements_key, element_type in element_types:
        elements = practice.get(elements_key, [])

        for element in elements:
            element_name = element.get('name', 'unnamed')

            # Extract all citation references from this element
            narrative_citations = find_narrative_citations(element, element_type, element_name)

            # Validate each citation reference
            for context, narrative_name, citation_names in narrative_citations:
                for citation_name in citation_names:
                    total_checked += 1

                    if citation_name not in valid_citations:
                        error_count += 1
                        print(f"ERROR: Invalid citation reference")
                        print(f"  Location: {context}")
                        print(f"  Citation: '{citation_name}'")

                        # Suggest close matches
                        close_matches = difflib.get_close_matches(
                            citation_name, valid_citations, n=3, cutoff=0.6
                        )
                        if close_matches:
                            print(f"  Did you mean:")
                            for match in close_matches:
                                print(f"    - '{match}'")
                        print()

    return total_checked, error_count


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-citation-references.py <practice-json-file>")
        sys.exit(2)

    practice_file = Path(sys.argv[1])

    print("="*70)
    print("CITATION REFERENCE VALIDATOR")
    print("="*70)
    print(f"Practice: {practice_file.name}")
    print()

    # Load practice JSON
    practice = load_json(practice_file)

    # Validate citation references
    total_checked, error_count = validate_practice(practice)

    # Report results
    print("="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    print(f"Total citation references checked: {total_checked}")
    print(f"Invalid references found: {error_count}")
    print()

    if error_count == 0:
        print("✅ All citation references valid")
        return 0
    else:
        print(f"❌ {error_count} invalid citation reference(s) found")
        print()
        print("ACTION REQUIRED:")
        print("1. Check citations array for correct Citation.name values")
        print("2. Fix citationNames to exactly match Citation.name")
        print("3. Or add missing citations to citations array")
        return 1


if __name__ == '__main__':
    sys.exit(main())
