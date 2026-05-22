#!/usr/bin/env python3
"""
Automated fixes for schema violations found in Practice Language JSON.

Based on validation results documented in:
- prompts/SCHEMA-VIOLATIONS-COMPLETE.md
- 23 errors found in practice-1-ai-platform-management.json

Usage:
    python3 fix-schema-violations.py <practice-file>.json
"""

import json
import sys
from pathlib import Path

def fix_narrative_structure(narratives):
    """
    Fix narrative objects to include all required fields.

    Schema requires:
    - name, description (from PracticeElement)
    - narrativeName, narrativeTypeName, narrativeContexts (from Narrative)

    WRONG: {narrativeName, narrativeTypeName, narrativeContexts}
    RIGHT: {name, description, narrativeName, narrativeTypeName, narrativeContexts}
    """
    if not narratives:
        return narratives

    fixed = []
    for idx, narrative in enumerate(narratives):
        fixed_narrative = {}

        # Add name (from PracticeElement - required)
        if 'name' in narrative:
            fixed_narrative['name'] = narrative['name']
        elif 'narrativeName' in narrative:
            fixed_narrative['name'] = narrative['narrativeName']
        else:
            # Generate from narrativeTypeName
            type_name = narrative.get('narrativeTypeName', f'Narrative {idx + 1}')
            fixed_narrative['name'] = type_name

        # Add description (from PracticeElement - required)
        if 'description' not in narrative:
            type_name = narrative.get('narrativeTypeName', 'narrative')
            fixed_narrative['description'] = f"Provides {type_name.lower()} context and guidance for this element"
        else:
            fixed_narrative['description'] = narrative['description']

        # NOTE: narrativeName is an old property that has been removed from schema
        # Narratives are PracticeElements, so they use "name" property instead
        # Do NOT include narrativeName

        # Add narrativeTypeName (from Narrative - required)
        fixed_narrative['narrativeTypeName'] = narrative['narrativeTypeName']

        # Add narrativeContexts (from Narrative - required)
        fixed_narrative['narrativeContexts'] = narrative.get('narrativeContexts', [])

        # Add citationNames if present (optional)
        if 'citationNames' in narrative:
            fixed_narrative['citationNames'] = narrative['citationNames']

        fixed.append(fixed_narrative)

    return fixed

def fix_activity_narratives(activity):
    """
    Rename techniqueNarratives to narratives and fix structure.

    WRONG: activity.techniqueNarratives
    RIGHT: activity.narratives (with name/description)
    """
    if 'techniqueNarratives' in activity:
        # Move techniqueNarratives to narratives
        narratives = activity.pop('techniqueNarratives')
        activity['narratives'] = fix_narrative_structure(narratives)
    elif 'narratives' in activity:
        # Fix existing narratives structure
        activity['narratives'] = fix_narrative_structure(activity['narratives'])

    return activity

def fix_tags_structure(practice):
    """
    Nest tags in a tags object.

    WRONG: {domainTags: [...], lifecycleTags: [...], organizationalTags: [...]}
    RIGHT: {tags: {domainTags: [...], lifecycleTags: [...], organizationalTags: [...]}}
    """
    has_domain = 'domainTags' in practice
    has_lifecycle = 'lifecycleTags' in practice
    has_org = 'organizationalTags' in practice

    if has_domain or has_lifecycle or has_org:
        tags = {}

        if has_domain:
            tags['domainTags'] = practice.pop('domainTags')
        if has_lifecycle:
            tags['lifecycleTags'] = practice.pop('lifecycleTags')
        if has_org:
            tags['organizationalTags'] = practice.pop('organizationalTags')

        practice['tags'] = tags

    return practice

def fix_persona_groups(practice):
    """
    Rename teams to personaGroups.

    WRONG: practice.teams
    RIGHT: practice.personaGroups
    """
    if 'teams' in practice:
        practice['personaGroups'] = practice.pop('teams')

    return practice

def fix_persona_properties(personas):
    """
    Fix persona property names.

    WRONG: {personaName, personaDescription, competencies}
    RIGHT: {name, description, competencies}
    """
    if not personas:
        return personas

    for persona in personas:
        if 'personaName' in persona:
            persona['name'] = persona.pop('personaName')
        if 'personaDescription' in persona:
            persona['description'] = persona.pop('personaDescription')

    return personas

def fix_practice_json(file_path):
    """Apply all schema violation fixes to a practice JSON file."""
    print(f"Loading {file_path}...")

    with open(file_path, 'r') as f:
        practice = json.load(f)

    print("\nApplying fixes...")

    # Fix 1: Practice tags structure
    print("  1. Fixing tags structure (nest in tags object)...")
    practice = fix_tags_structure(practice)

    # Fix 2: PersonaGroups property name
    print("  2. Renaming teams → personaGroups...")
    practice = fix_persona_groups(practice)

    # Fix 3: Alpha narratives
    if 'alphas' in practice:
        print(f"  3. Fixing narrative structure in {len(practice['alphas'])} alphas...")
        for alpha in practice['alphas']:
            if 'narratives' in alpha:
                alpha['narratives'] = fix_narrative_structure(alpha['narratives'])

    # Fix 4: Activity narratives
    if 'activities' in practice:
        print(f"  4. Fixing narrative structure in {len(practice['activities'])} activities...")
        for activity in practice['activities']:
            fix_activity_narratives(activity)

    # Fix 5: Work product narratives (if any)
    if 'workProducts' in practice:
        print(f"  5. Checking narrative structure in {len(practice['workProducts'])} work products...")
        for wp in practice['workProducts']:
            if 'narratives' in wp:
                wp['narratives'] = fix_narrative_structure(wp['narratives'])

    # Fix 6: Pattern narratives (if any)
    if 'patterns' in practice:
        print(f"  6. Checking narrative structure in {len(practice['patterns'])} patterns...")
        for pattern in practice['patterns']:
            if 'narratives' in pattern:
                pattern['narratives'] = fix_narrative_structure(pattern['narratives'])

            # Also fix pattern view narratives
            if 'patternViews' in pattern:
                for view in pattern['patternViews']:
                    if 'narratives' in view:
                        view['narratives'] = fix_narrative_structure(view['narratives'])

    # Fix 7: Persona property names
    if 'personas' in practice:
        print(f"  7. Fixing persona property names in {len(practice['personas'])} personas...")
        practice['personas'] = fix_persona_properties(practice['personas'])

    # Save fixed JSON
    print(f"\nSaving fixed JSON to {file_path}...")
    with open(file_path, 'w') as f:
        json.dump(practice, f, indent=2)

    print("✓ All fixes applied successfully")
    return practice

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix-schema-violations.py <practice-file>.json")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    if not file_path.suffix == '.json':
        print(f"Error: File must be a .json file: {file_path}")
        sys.exit(1)

    try:
        fix_practice_json(file_path)
        print(f"\n✓ Successfully fixed schema violations in {file_path}")
        print("\nNext step: Run schema validation to confirm 0 errors:")
        print(f"  node utils/validate-json-schema.js {file_path}")
    except Exception as e:
        print(f"\n✗ Error fixing schema violations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
