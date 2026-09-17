#!/usr/bin/env python3
"""
Extract structured element details from practice JSON files for analysis report generation.
"""

import json
import sys
from pathlib import Path


def extract_alphas(practice_data):
    """Extract alpha names, descriptions, states with criteria."""
    alphas = []
    for alpha in practice_data.get('alphas', []):
        alpha_info = {
            'name': alpha['name'],
            'description': alpha['description'],
            'focusName': alpha.get('focusName', ''),
            'contributesTo': alpha.get('contributesTo', ''),
            'mapsTo': alpha.get('mapsTo', ''),
            'states': []
        }
        for state in alpha.get('states', []):
            state_info = {
                'name': state['name'],
                'description': state['description'],
                'seq': state['seq'],
                'criteria_count': len(state.get('checklist', []))
            }
            alpha_info['states'].append(state_info)
        alphas.append(alpha_info)
    return alphas


def extract_activities(practice_data):
    """Extract activity names and descriptions."""
    activities = []
    for activity in practice_data.get('activities', []):
        activities.append({
            'name': activity['name'],
            'description': activity['description'],
            'activitySpaceName': activity.get('activitySpaceName', '')
        })
    return activities


def extract_work_products(practice_data):
    """Extract work product names and LOD counts."""
    work_products = []
    for wp in practice_data.get('workProducts', []):
        work_products.append({
            'name': wp['name'],
            'description': wp['description'],
            'lod_count': len(wp.get('levelsOfDetail', []))
        })
    return work_products


def extract_personas(practice_data):
    """Extract persona names and descriptions."""
    personas = []
    for persona in practice_data.get('personas', []):
        personas.append({
            'name': persona['name'],
            'description': persona['description']
        })
    return personas


def extract_persona_groups(practice_data):
    """Extract persona group names and members."""
    groups = []
    for group in practice_data.get('personaGroups', []):
        groups.append({
            'name': group['name'],
            'description': group['description'],
            'members': group.get('teamMembers', [])
        })
    return groups


def extract_patterns(practice_data):
    """Extract pattern names and view counts."""
    patterns = []
    for pattern in practice_data.get('patterns', []):
        patterns.append({
            'name': pattern['name'],
            'description': pattern['description'],
            'view_count': len(pattern.get('views', []))
        })
    return patterns


def extract_outcomes(practice_data):
    """Extract outcomes."""
    outcomes = []
    for outcome in practice_data.get('outcomes', []):
        outcomes.append({
            'name': outcome['name'],
            'description': outcome['description'],
            'measureDescription': outcome.get('measureDescription', '')
        })
    return outcomes


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract-practice-elements.py <practice-json-path>")
        sys.exit(1)

    practice_path = Path(sys.argv[1])
    if not practice_path.exists():
        print(f"Error: File not found: {practice_path}")
        sys.exit(1)

    with open(practice_path, 'r') as f:
        practice_data = json.load(f)

    # Extract all elements
    result = {
        'practice_name': practice_data.get('name', ''),
        'description': practice_data.get('description', ''),
        'version': practice_data.get('version', ''),
        'outcomes': extract_outcomes(practice_data),
        'alphas': extract_alphas(practice_data),
        'activities': extract_activities(practice_data),
        'work_products': extract_work_products(practice_data),
        'personas': extract_personas(practice_data),
        'persona_groups': extract_persona_groups(practice_data),
        'patterns': extract_patterns(practice_data),
        'citations': [
            {
                'name': c['name'],
                'description': c.get('description', ''),
                'authors': c.get('authors', []),
                'date': c.get('date', ''),
                'source': c.get('source', ''),
                'url': c.get('url', '')
            }
            for c in practice_data.get('citations', [])
        ]
    }

    # Print summary
    print(f"\n=== {result['practice_name']} (v{result['version']}) ===\n")
    print(f"Description: {result['description']}\n")
    print(f"Outcomes: {len(result['outcomes'])}")
    print(f"Alphas: {len(result['alphas'])}")
    for alpha in result['alphas']:
        print(f"  - {alpha['name']}: {len(alpha['states'])} states, contributesTo={alpha['contributesTo'] or 'N/A'}, mapsTo={alpha['mapsTo'] or 'N/A'}")
    print(f"\nActivities: {len(result['activities'])}")
    for activity in result['activities']:
        print(f"  - {activity['name']} ({activity['activitySpaceName']})")
    print(f"\nWork Products: {len(result['work_products'])}")
    for wp in result['work_products']:
        print(f"  - {wp['name']}: {wp['lod_count']} LODs")
    print(f"\nPersonas: {len(result['personas'])}")
    for persona in result['personas']:
        print(f"  - {persona['name']}")
    print(f"\nPersona Groups: {len(result['persona_groups'])}")
    for group in result['persona_groups']:
        print(f"  - {group['name']}: {len(group['members'])} members")
    print(f"\nPatterns: {len(result['patterns'])}")
    for pattern in result['patterns']:
        print(f"  - {pattern['name']}: {pattern['view_count']} views")
    print(f"\nCitations: {len(result['citations'])}")


if __name__ == '__main__':
    main()
