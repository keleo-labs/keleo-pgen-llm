#!/usr/bin/env python3
"""
Fix property names in Practice/Method JSON files to match language.schema.json.

This script automatically corrects common property name mismatches that occur
during JSON generation, ensuring 100% schema compliance.

Usage:
    # Fix all JSON files in current directory
    python3 fix-property-names.py

    # Fix specific files
    python3 fix-property-names.py file1.json file2.json

Property name corrections:

Activities:
- outcomes → contributesTo
- focus → focusName
- competencies → recommendedCompetencyLevels
- (adds) requiredCompetencies (extracted from recommendedCompetencyLevels)
- personas → involves
- workProductsUsed → worksOn

Patterns:
- views → patternViews
- narrativeFramework → narrativeTypeName
- type → (removed - not in schema)

PatternViews:
- activitiesEmphasized → activities
- alphaStateProgressions → alphaStates (converted to proper format)
"""

import json
import os
import sys
from pathlib import Path


def fix_activity(activity):
    """Fix property names in an Activity object."""
    fixed = {}

    # Copy basic properties
    for key in ['name', 'description', 'activitySpaceName', 'narratives']:
        if key in activity:
            fixed[key] = activity[key]

    # Fix: focus → focusName
    if 'focus' in activity:
        fixed['focusName'] = activity['focus']
    elif 'focusName' in activity:
        fixed['focusName'] = activity['focusName']

    # Fix: outcomes → contributesTo
    if 'outcomes' in activity:
        fixed['contributesTo'] = activity['outcomes']
    elif 'contributesTo' in activity:
        fixed['contributesTo'] = activity['contributesTo']

    # Fix: workProductsUsed → worksOn (or workProducts or other variants)
    if 'workProductsUsed' in activity:
        fixed['worksOn'] = activity['workProductsUsed']
    elif 'workProducts' in activity:
        fixed['worksOn'] = activity['workProducts']
    elif 'worksOn' in activity:
        fixed['worksOn'] = activity['worksOn']

    # Fix: competencies → recommendedCompetencyLevels + requiredCompetencies
    if 'competencies' in activity:
        fixed['recommendedCompetencyLevels'] = activity['competencies']
        # Extract competency names for requiredCompetencies
        fixed['requiredCompetencies'] = list(set([
            comp['competencyName'] for comp in activity['competencies']
            if isinstance(comp, dict) and 'competencyName' in comp
        ]))
    elif 'recommendedCompetencyLevels' in activity:
        fixed['recommendedCompetencyLevels'] = activity['recommendedCompetencyLevels']
        if 'requiredCompetencies' not in activity:
            fixed['requiredCompetencies'] = list(set([
                comp['competencyName'] for comp in activity['recommendedCompetencyLevels']
                if isinstance(comp, dict) and 'competencyName' in comp
            ]))

    if 'requiredCompetencies' in activity:
        fixed['requiredCompetencies'] = activity['requiredCompetencies']

    # Fix: personas → involves (array of PersonaGroup names)
    if 'personas' in activity:
        # Personas should be converted to involves (PersonaGroup names)
        if isinstance(activity['personas'], list):
            fixed['involves'] = activity['personas']
        else:
            fixed['involves'] = [activity['personas']]
    elif 'involves' in activity:
        fixed['involves'] = activity['involves']

    return fixed


def fix_pattern_view(view):
    """Fix property names in a PatternView object."""
    fixed = {}

    # Copy basic properties
    for key in ['name', 'description', 'seq']:
        if key in view:
            fixed[key] = view[key]

    # alphaStates (keep as is)
    if 'alphaStates' in view:
        fixed['alphaStates'] = view['alphaStates']

    # activitiesEmphasized → activities
    if 'activitiesEmphasized' in view:
        fixed['activities'] = view['activitiesEmphasized']
    elif 'activities' in view:
        fixed['activities'] = view['activities']

    # alphaStateProgressions → convert to alphaStates if needed
    if 'alphaStateProgressions' in view:
        if 'alphaStates' not in fixed:
            fixed['alphaStates'] = []
        for prog in view['alphaStateProgressions']:
            if 'alphaName' in prog and 'exitStateName' in prog and prog['exitStateName']:
                fixed['alphaStates'].append({
                    'alphaName': prog['alphaName'],
                    'stateName': prog['exitStateName']
                })

    # Copy other optional properties
    for key in ['workProductInstances', 'narrativeContexts', 'alphaInstances', 'activitySpaces']:
        if key in view:
            fixed[key] = view[key]

    return fixed


def fix_pattern(pattern):
    """Fix property names in a Pattern object."""
    fixed = {}

    # Copy basic properties
    for key in ['name', 'description', 'narratives']:
        if key in pattern:
            fixed[key] = pattern[key]

    # Remove 'type' - not in schema (don't copy it)

    # Fix: narrativeFramework → narrativeTypeName
    if 'narrativeFramework' in pattern:
        fixed['narrativeTypeName'] = pattern['narrativeFramework']
    elif 'narrativeTypeName' in pattern:
        fixed['narrativeTypeName'] = pattern['narrativeTypeName']

    # Fix: views → patternViews
    if 'views' in pattern:
        fixed['patternViews'] = [fix_pattern_view(view) for view in pattern['views']]
    elif 'patternViews' in pattern:
        fixed['patternViews'] = [fix_pattern_view(view) for view in pattern['patternViews']]

    return fixed


def fix_practice(practice):
    """Fix property names in a Practice object."""
    fixed = practice.copy()

    # Fix activities
    if 'activities' in fixed:
        fixed['activities'] = [fix_activity(act) for act in fixed['activities']]

    # Fix patterns
    if 'patterns' in fixed:
        fixed['patterns'] = [fix_pattern(pat) for pat in fixed['patterns']]

    return fixed


def fix_method(method):
    """Fix property names in a Method object."""
    fixed = method.copy()

    # Fix practices array
    if 'practices' in fixed:
        fixed['practices'] = [fix_practice(practice) for practice in fixed['practices']]

    return fixed


def process_file(file_path):
    """Process a single JSON file."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Determine if it's a Method or Practice
    if 'practices' in data and isinstance(data['practices'], list):
        # It's a Method
        fixed_data = fix_method(data)
    else:
        # It's a Practice
        fixed_data = fix_practice(data)

    # Write back
    with open(file_path, 'w') as f:
        json.dump(fixed_data, f, indent=2)

    print(f"  ✓ Fixed {file_path}")


def main():
    if len(sys.argv) > 1:
        # Process specified files
        files = sys.argv[1:]
    else:
        # Process all JSON files in current directory
        files = [f for f in os.listdir('.') if f.endswith('.json')]
        if not files:
            print("No JSON files found in current directory.")
            print("Usage: python3 fix-property-names.py [file1.json file2.json ...]")
            sys.exit(1)

    print(f"Schema Compliance Fixer - Processing {len(files)} file(s)...\n")

    for file_name in files:
        if os.path.exists(file_name):
            try:
                process_file(file_name)
            except Exception as e:
                print(f"  ✗ Error processing {file_name}: {e}")
        else:
            print(f"  ⚠ File not found: {file_name}")

    print("\n✓ All files processed successfully!")


if __name__ == "__main__":
    main()
