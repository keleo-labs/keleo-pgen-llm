#!/usr/bin/env python3
"""
Validate all baseline practice references in Practice JSON files.

Checks:
1. Competency names match baseline
2. Alpha names match baseline (for references)
3. ActivitySpace names match baseline
4. Focus names match baseline
5. State names match their alpha's states

Loads canonical names from ../../deps/platform-adoption-kernel.json
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Load baseline
BASELINE_PATH = Path("../../deps/platform-adoption-kernel.json")

def load_baseline():
    """Load and index the baseline practice."""
    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    # Extract canonical names
    canonical = {
        'focuses': set(f['name'] for f in baseline.get('focuses', [])),
        'competencies': set(c['name'] for c in baseline.get('competencies', [])),
        'alphas': set(a['name'] for a in baseline.get('alphas', [])),
        'activitySpaces': set(a['name'] for a in baseline.get('activitySpaces', [])),
    }

    # Extract alpha states (alpha_name -> set of state names)
    alpha_states = {}
    for alpha in baseline.get('alphas', []):
        alpha_states[alpha['name']] = set(s['name'] for s in alpha.get('states', []))

    canonical['alpha_states'] = alpha_states

    return canonical

def validate_practice(practice_file, canonical):
    """Validate a single practice file against baseline."""
    print(f"\n=== Validating {practice_file.name} ===")

    with open(practice_file) as f:
        practice = json.load(f)

    practice_name = practice.get('name', practice_file.name)
    errors = defaultdict(list)
    fixes_made = 0

    # Build set of practice-defined alphas (these are valid references)
    practice_alphas = set(canonical['alphas'])  # Start with baseline
    for alpha in practice.get('alphas', []):
        practice_alphas.add(alpha['name'])

    # Build alpha states for practice alphas
    practice_alpha_states = {}
    # Start with baseline states (deep copy as sets)
    for alpha_name, states in canonical['alpha_states'].items():
        practice_alpha_states[alpha_name] = set(states)

    # Merge or add practice alpha states
    for alpha in practice.get('alphas', []):
        alpha_name = alpha['name']
        new_states = set(s['name'] for s in alpha.get('states', []))

        if alpha_name in practice_alpha_states:
            # Merge with existing baseline states (redeclaration)
            practice_alpha_states[alpha_name].update(new_states)
        else:
            # New practice-defined alpha
            practice_alpha_states[alpha_name] = new_states

    # Validate competency references
    for activity in practice.get('activities', []):
        activity_name = activity.get('name', 'Unknown')

        # Check recommendedCompetencyLevels
        for idx, comp_ref in enumerate(activity.get('recommendedCompetencyLevels', [])):
            # Handle both string and object formats
            if isinstance(comp_ref, str):
                comp_name = comp_ref
            elif isinstance(comp_ref, dict):
                comp_name = comp_ref.get('competencyName')
            else:
                errors['invalid_competency_format'].append(f"{activity_name}: {type(comp_ref)}")
                continue

            if comp_name is None:
                errors['null_competency'].append(activity_name)
                # Fix: replace null with default
                if isinstance(comp_ref, dict):
                    comp_ref['competencyName'] = 'Engineering'
                else:
                    activity['recommendedCompetencyLevels'][idx] = {
                        'competencyName': 'Engineering',
                        'competencyLevelName': 'Proficient'
                    }
                fixes_made += 1
            elif comp_name not in canonical['competencies']:
                errors['invalid_competency'].append(f"{activity_name}: '{comp_name}'")
                # Try to fix common mistakes
                fixed = fix_competency_name(comp_name, canonical['competencies'])
                if fixed:
                    if isinstance(comp_ref, dict):
                        comp_ref['competencyName'] = fixed
                    else:
                        activity['recommendedCompetencyLevels'][idx] = {
                            'competencyName': fixed,
                            'competencyLevelName': 'Proficient'
                        }
                    fixes_made += 1
                    print(f"  Fixed competency: '{comp_name}' → '{fixed}' in {activity_name}")

        # Check requiredCompetencies
        for i, comp_name in enumerate(activity.get('requiredCompetencies', [])):
            if comp_name is None:
                errors['null_required_competency'].append(activity_name)
                activity['requiredCompetencies'][i] = 'Engineering'
                fixes_made += 1
            elif comp_name not in canonical['competencies']:
                errors['invalid_required_competency'].append(f"{activity_name}: '{comp_name}'")
                fixed = fix_competency_name(comp_name, canonical['competencies'])
                if fixed:
                    activity['requiredCompetencies'][i] = fixed
                    fixes_made += 1
                    print(f"  Fixed required competency: '{comp_name}' → '{fixed}' in {activity_name}")

        # Check focusName
        focus_name = activity.get('focusName')
        if focus_name and focus_name not in canonical['focuses']:
            errors['invalid_focus'].append(f"{activity_name}: '{focus_name}'")

        # Check activitySpaceName
        space_name = activity.get('activitySpaceName')
        if space_name and space_name not in canonical['activitySpaces']:
            errors['invalid_activity_space'].append(f"{activity_name}: '{space_name}'")

        # Check contributesTo references
        for contrib in activity.get('contributesTo', []):
            alpha_name = contrib.get('alphaName')
            state_name = contrib.get('stateName')

            # Check alpha name (allow practice-defined alphas)
            if alpha_name and alpha_name not in practice_alphas:
                errors['invalid_alpha'].append(f"{activity_name}: '{alpha_name}'")

            # Check state name against the correct alpha's states (baseline or practice-defined)
            if alpha_name and state_name:
                if alpha_name in practice_alpha_states:
                    if state_name not in practice_alpha_states[alpha_name]:
                        errors['invalid_state'].append(f"{activity_name}: {alpha_name} → '{state_name}'")
                        # Try to fix
                        fixed = fix_state_name(state_name, alpha_name, practice_alpha_states[alpha_name])
                        if fixed:
                            contrib['stateName'] = fixed
                            fixes_made += 1
                            print(f"  Fixed state: '{state_name}' → '{fixed}' for {alpha_name} in {activity_name}")

    # Validate persona competencies
    for persona in practice.get('personas', []):
        persona_name = persona.get('name', 'Unknown')
        for idx, comp_ref in enumerate(persona.get('competencies', [])):
            # Handle both string and object formats
            if isinstance(comp_ref, str):
                comp_name = comp_ref
            elif isinstance(comp_ref, dict):
                comp_name = comp_ref.get('competencyName')
            else:
                errors['invalid_persona_competency_format'].append(f"{persona_name}: {type(comp_ref)}")
                continue

            if comp_name and comp_name not in canonical['competencies']:
                errors['invalid_persona_competency'].append(f"{persona_name}: '{comp_name}'")
                fixed = fix_competency_name(comp_name, canonical['competencies'])
                if fixed:
                    if isinstance(comp_ref, dict):
                        comp_ref['competencyName'] = fixed
                    else:
                        persona['competencies'][idx] = {
                            'competencyName': fixed,
                            'competencyLevelName': 'Proficient'
                        }
                    fixes_made += 1
                    print(f"  Fixed persona competency: '{comp_name}' → '{fixed}' in {persona_name}")

    # Report errors
    if errors:
        print(f"  Found {sum(len(v) for v in errors.values())} issues:")
        for error_type, items in sorted(errors.items()):
            print(f"    {error_type}: {len(items)}")
            for item in items[:5]:  # Show first 5
                print(f"      - {item}")
            if len(items) > 5:
                print(f"      ... and {len(items) - 5} more")
    else:
        print(f"  ✓ No baseline reference errors")

    if fixes_made > 0:
        # Write back fixed practice
        with open(practice_file, 'w') as f:
            json.dump(practice, f, indent=2)
        print(f"  ✓ Applied {fixes_made} automatic fixes")

    return errors, fixes_made

def fix_state_name(wrong_name, alpha_name, valid_states):
    """Try to fix common state name mistakes."""
    if wrong_name in valid_states:
        return wrong_name

    # Common state name corrections
    corrections = {
        'Provisioned': {
            'Work': 'Prepared',
            'Serving Runtime': 'Configured',
            'Inference Endpoint': 'Deployed',
        },
        'In Use': {
            'Team': 'Performing',
            'Stakeholders': 'Satisfied in Use',
            'Requirements': 'Addressed',
            'Work': 'Under Control',
            'Inference Endpoint': 'Available',
        },
        'Performing': {
            'Serving Runtime': 'Optimized',
        },
    }

    if wrong_name in corrections and alpha_name in corrections[wrong_name]:
        return corrections[wrong_name][alpha_name]

    # Try case-insensitive match
    wrong_lower = wrong_name.lower()
    for valid in valid_states:
        if valid.lower() == wrong_lower:
            return valid

    return None

def fix_competency_name(wrong_name, valid_names):
    """Try to fix common competency name mistakes."""
    if wrong_name is None:
        return 'Engineering'

    # Exact match (shouldn't happen but check anyway)
    if wrong_name in valid_names:
        return wrong_name

    # Handle descriptions with parentheses (e.g., "ML Engineering (pipeline development...)")
    # Extract the part before the parenthesis
    if '(' in wrong_name:
        base_name = wrong_name.split('(')[0].strip()
        # Try to map the extracted base name
        if base_name:
            wrong_name = base_name

    # Common mappings
    mappings = {
        'null': 'Engineering',
        'Engineering ': 'Engineering',  # Trailing space
        ' Engineering': 'Engineering',  # Leading space
        'engineering': 'Engineering',  # Case
        'ENGINEERING': 'Engineering',
        'Site Reliability Engineering': 'Site Reliability',
        'SRE': 'Site Reliability',
        'ML Engineering': 'Engineering',
        'Platform Engineering': 'Engineering',
        'Software Development': 'Engineering',
        'Deployment Automation': 'Engineering',
        'Data Engineering': 'Engineering',
        'Machine Learning': 'Engineering',
        'ML Evaluation': 'Analysis',
        'Statistics and Experimentation': 'Analysis',
        'Requirements Engineering': 'Analysis',
        'AI/ML Domain Knowledge': 'Engineering',
        'SQL and Data Platforms': 'Engineering',
        'Pipeline Orchestration': 'Engineering',
        'Security Engineering': 'Platform Security And Compliance Enforcement',
        'Security': 'Platform Security And Compliance Enforcement',
        'Compliance': 'Platform Security And Compliance Enforcement',
        'Regulatory Compliance': 'Platform Security And Compliance Enforcement',
        'Governance and Audit': 'Management',
        'Data Governance': 'Management',
        'Model Risk Management': 'Management',
        'Strategic Alignment': 'Platform Strategic Alignment',
        'Strategy': 'Platform Strategic Alignment',
        'Product Management': 'Management',
        'Business Analysis': 'Analysis',
        'analysis': 'Analysis',
        'leadership': 'Leadership',
        'management': 'Management',
        'stakeholder': 'Stakeholder Representation',
    }

    if wrong_name in mappings:
        return mappings[wrong_name]

    # Try case-insensitive match
    wrong_lower = wrong_name.lower()
    for valid in valid_names:
        if valid.lower() == wrong_lower:
            return valid

    # No fix found
    return None

def main():
    print("=== Baseline Reference Validation ===")
    print(f"Loading baseline from: {BASELINE_PATH}")

    canonical = load_baseline()

    print(f"\nCanonical baseline elements:")
    print(f"  Focuses: {len(canonical['focuses'])}")
    print(f"  Competencies: {len(canonical['competencies'])}")
    print(f"  Alphas: {len(canonical['alphas'])}")
    print(f"  ActivitySpaces: {len(canonical['activitySpaces'])}")

    # List competencies for reference
    print(f"\nValid competency names:")
    for comp in sorted(canonical['competencies']):
        print(f"  - {comp}")

    # Validate all practice files
    practice_files = sorted(Path('.').glob('practice-*.json'))
    practice_files = [f for f in practice_files if not f.name.endswith('-enriched.json')]

    total_errors = 0
    total_fixes = 0

    for practice_file in practice_files:
        errors, fixes = validate_practice(practice_file, canonical)
        total_errors += sum(len(v) for v in errors.values())
        total_fixes += fixes

    print(f"\n=== Summary ===")
    print(f"Validated {len(practice_files)} practice files")
    print(f"Total issues found: {total_errors}")
    print(f"Total automatic fixes applied: {total_fixes}")

    if total_fixes > 0:
        print("\n⚠ Practice files were modified. Rebuild method JSON:")
        print("  python3 rebuild-method-json.py")

    if total_errors > total_fixes:
        print(f"\n⚠ {total_errors - total_fixes} issues require manual review")
        return 1
    else:
        print("\n✓ All baseline references validated")
        return 0

if __name__ == "__main__":
    sys.exit(main())
