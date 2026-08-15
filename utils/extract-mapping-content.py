#!/usr/bin/env python3
"""
Extract structured content from mapping guide markdown for JSON generation.

Usage:
    python3 extract-mapping-content.py <mapping-guide-path> <section-name>

Sections:
    work-products, personas, persona-groups, activities, pattern
"""

import sys
import re
import json

def extract_work_products(content):
    """Extract work products with levels of detail from mapping guide."""
    # Implementation would parse the work products section
    # For now, return skeleton
    return []

def extract_personas(content):
    """Extract personas with competencies and narratives."""
    # Find personas section
    personas_match = re.search(r'## Personas and Persona Groups\s*\n(.*?)(?=\n## |$)', content, re.DOTALL)
    if not personas_match:
        return []

    personas_text = personas_match.group(1)
    personas = []

    # Extract each persona section
    persona_pattern = r'### Persona: (.+?)\n\n\*\*Description:\*\* (.+?)\n\n\*\*Competencies:\*\*\s*\n(.*?)\n\n\*\*Narrative'
    persona_matches = re.finditer(persona_pattern, personas_text, re.DOTALL)

    for match in persona_matches:
        name = match.group(1).strip()
        description = match.group(2).strip()
        competencies_text = match.group(3).strip()

        # Parse competencies
        competencies = []
        for comp_line in competencies_text.split('\n'):
            comp_match = re.match(r'- (.+?) \(Level (\d+)\)', comp_line.strip())
            if comp_match:
                competencies.append({
                    'competencyName': comp_match.group(1).strip(),
                    'level': int(comp_match.group(2))
                })

        personas.append({
            'name': name,
            'description': description,
            'competencies': competencies
        })

    return personas

def extract_activities(content):
    """Extract activities from mapping guide."""
    return []

def extract_pattern(content):
    """Extract pattern with views from mapping guide."""
    return {}

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    mapping_guide_path = sys.argv[1]
    section = sys.argv[2]

    with open(mapping_guide_path, 'r') as f:
        content = f.read()

    if section == 'work-products':
        result = extract_work_products(content)
    elif section == 'personas':
        result = extract_personas(content)
    elif section == 'persona-groups':
        result = []  # TODO
    elif section == 'activities':
        result = extract_activities(content)
    elif section == 'pattern':
        result = extract_pattern(content)
    else:
        print(f"Unknown section: {section}")
        sys.exit(1)

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
