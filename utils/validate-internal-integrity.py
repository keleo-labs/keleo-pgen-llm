#!/usr/bin/env python3
"""
Validate internal referential integrity of a Method JSON.

Checks:
1. Activities reference existing alphas (baseline + practice-defined)
2. Activities reference existing states within those alphas
3. Activities reference existing work products
4. Patterns reference existing activities
5. Pattern views reference existing activities
6. All internal symbolic references are valid
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def load_method(method_file):
    """Load the method JSON."""
    with open(method_file) as f:
        return json.load(f)

def build_element_index(method):
    """Build an index of all elements in the method."""
    index = {
        'alphas': {},  # alpha_name -> {states: set(), practice: str}
        'workproducts': {},  # wp_name -> practice
        'activities': {},  # activity_name -> practice
        'patterns': {},  # pattern_name -> practice
        'personas': {},  # persona_name -> practice
        'teams': {},  # team_name -> practice
        'competencies': set(),  # All competencies referenced
        'activitySpaces': set(),  # All activity spaces
        'focuses': set(),  # All focuses
    }

    # Load baseline alphas from platform-adoption-kernel.json
    baseline_path = Path("../../deps/platform-adoption-kernel.json")
    if baseline_path.exists():
        with open(baseline_path) as f:
            baseline = json.load(f)
            for alpha in baseline.get('alphas', []):
                alpha_name = alpha['name']
                index['alphas'][alpha_name] = {
                    'states': set(s['name'] for s in alpha.get('states', [])),
                    'practice': 'baseline'
                }
            for comp in baseline.get('competencies', []):
                index['competencies'].add(comp['name'])
            for space in baseline.get('activitySpaces', []):
                index['activitySpaces'].add(space['name'])
            for focus in baseline.get('focuses', []):
                index['focuses'].add(focus['name'])

    # Index method elements
    for practice in method.get('practices', []):
        practice_name = practice.get('name', 'Unknown')

        # Index alphas (practice-defined or redeclared)
        for alpha in practice.get('alphas', []):
            alpha_name = alpha['name']
            alpha_states = set(s['name'] for s in alpha.get('states', []))

            if alpha_name in index['alphas']:
                # Merge states (redeclaration or extension)
                index['alphas'][alpha_name]['states'].update(alpha_states)
            else:
                # New practice-defined alpha
                index['alphas'][alpha_name] = {
                    'states': alpha_states,
                    'practice': practice_name
                }

        # Index work products
        for wp in practice.get('workProducts', []):
            wp_name = wp.get('name')
            if wp_name:
                index['workproducts'][wp_name] = practice_name

        # Index activities
        for activity in practice.get('activities', []):
            activity_name = activity.get('name')
            if activity_name:
                index['activities'][activity_name] = practice_name

        # Index patterns
        for pattern in practice.get('patterns', []):
            pattern_name = pattern.get('name')
            if pattern_name:
                index['patterns'][pattern_name] = practice_name

        # Index personas
        for persona in practice.get('personas', []):
            persona_name = persona.get('name')
            if persona_name:
                index['personas'][persona_name] = practice_name

        # Index teams
        for team in practice.get('teams', []):
            team_name = team.get('name')
            if team_name:
                index['teams'][team_name] = practice_name

    return index

def validate_method(method, index):
    """Validate internal referential integrity."""
    print("\n=== Internal Referential Integrity Validation ===\n")

    errors = defaultdict(list)
    fixes_made = 0

    print(f"Element Index:")
    print(f"  Alphas: {len(index['alphas'])} ({sum(len(a['states']) for a in index['alphas'].values())} total states)")
    print(f"  Work Products: {len(index['workproducts'])}")
    print(f"  Activities: {len(index['activities'])}")
    print(f"  Patterns: {len(index['patterns'])}")
    print(f"  Personas: {len(index['personas'])}")
    print(f"  Teams: {len(index['teams'])}")

    for practice_idx, practice in enumerate(method.get('practices', []), 1):
        practice_name = practice.get('name', f'Practice {practice_idx}')
        print(f"\n=== Validating Practice {practice_idx}: {practice_name} ===")

        # Validate activities
        for activity in practice.get('activities', []):
            activity_name = activity.get('name', 'Unknown')

            # Check contributesTo references
            for contrib in activity.get('contributesTo', []):
                alpha_name = contrib.get('alphaName')
                state_name = contrib.get('stateName')

                if alpha_name not in index['alphas']:
                    errors['missing_alpha'].append(f"{activity_name}: '{alpha_name}'")
                elif state_name and state_name not in index['alphas'][alpha_name]['states']:
                    errors['missing_state'].append(f"{activity_name}: {alpha_name} → '{state_name}'")

            # Check worksOn references
            for wp_ref in activity.get('worksOn', []):
                # Handle both string and object formats
                if isinstance(wp_ref, str):
                    wp_name = wp_ref
                elif isinstance(wp_ref, dict):
                    wp_name = wp_ref.get('workProductName')
                else:
                    continue

                if wp_name and wp_name not in index['workproducts']:
                    errors['missing_workproduct'].append(f"{activity_name}: '{wp_name}'")

        # Validate patterns
        for pattern in practice.get('patterns', []):
            pattern_name = pattern.get('name', 'Unknown')

            # Check pattern views
            for view in pattern.get('patternViews', []):
                view_name = view.get('name', 'Unknown View')

                # Check activity references
                for activity_name in view.get('activities', []):
                    if activity_name not in index['activities']:
                        errors['missing_pattern_activity'].append(f"{pattern_name}/{view_name}: '{activity_name}'")

                # Check alpha state references
                for alpha_state in view.get('alphaStates', []):
                    alpha_name = alpha_state.get('alphaName')
                    state_name = alpha_state.get('stateName')

                    if alpha_name and alpha_name not in index['alphas']:
                        errors['missing_pattern_alpha'].append(f"{pattern_name}/{view_name}: '{alpha_name}'")
                    elif alpha_name and state_name and state_name not in index['alphas'][alpha_name]['states']:
                        errors['missing_pattern_state'].append(f"{pattern_name}/{view_name}: {alpha_name} → '{state_name}'")

    # Report errors
    if errors:
        print(f"\n=== Issues Found ===")
        total_issues = sum(len(v) for v in errors.values())
        print(f"Total issues: {total_issues}\n")

        for error_type, items in sorted(errors.items()):
            print(f"{error_type}: {len(items)}")
            for item in items[:10]:  # Show first 10
                print(f"  - {item}")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")
            print()
    else:
        print(f"\n✓ No internal referential integrity issues found")

    return errors, fixes_made

def generate_report(method, index, errors):
    """Generate a detailed integrity report."""
    report = []
    report.append("# Internal Referential Integrity Report")
    report.append(f"\n**Method:** {method.get('name', 'Unknown')}")
    report.append(f"**Practices:** {len(method.get('practices', []))}")
    report.append("")

    report.append("## Element Summary")
    report.append("")
    report.append(f"- **Alphas:** {len(index['alphas'])} ({sum(len(a['states']) for a in index['alphas'].values())} total states)")
    report.append(f"- **Work Products:** {len(index['workproducts'])}")
    report.append(f"- **Activities:** {len(index['activities'])}")
    report.append(f"- **Patterns:** {len(index['patterns'])}")
    report.append(f"- **Personas:** {len(index['personas'])}")
    report.append(f"- **Teams:** {len(index['teams'])}")
    report.append("")

    report.append("## Alphas and States")
    report.append("")
    for alpha_name in sorted(index['alphas'].keys()):
        alpha_info = index['alphas'][alpha_name]
        states = sorted(alpha_info['states'])
        practice = alpha_info['practice']
        report.append(f"### {alpha_name} ({practice})")
        report.append(f"States ({len(states)}): {', '.join(states)}")
        report.append("")

    if errors:
        report.append("## Validation Issues")
        report.append("")
        total = sum(len(v) for v in errors.values())
        report.append(f"**Total issues:** {total}")
        report.append("")

        for error_type, items in sorted(errors.items()):
            report.append(f"### {error_type} ({len(items)})")
            report.append("")
            for item in items:
                report.append(f"- {item}")
            report.append("")
    else:
        report.append("## Validation Result")
        report.append("")
        report.append("✅ **All internal references are valid**")
        report.append("")

    return "\n".join(report)

def main():
    method_file = "red-hat-ai-3.json"

    if not Path(method_file).exists():
        print(f"Error: {method_file} not found")
        return 1

    print(f"Loading method from {method_file}...")
    method = load_method(method_file)

    print("Building element index...")
    index = build_element_index(method)

    errors, fixes = validate_method(method, index)

    # Generate report
    report = generate_report(method, index, errors)
    report_file = "INTERNAL-INTEGRITY-REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nDetailed report written to: {report_file}")

    if errors:
        total = sum(len(v) for v in errors.values())
        print(f"\n⚠ {total} issues require review")
        return 1
    else:
        print("\n✓ All internal references validated")
        return 0

if __name__ == "__main__":
    sys.exit(main())
