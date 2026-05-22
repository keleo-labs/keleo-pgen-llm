#!/usr/bin/env python3
"""
Extract cross-reference index from Red Hat Ansible Automation Platform method modules.
This script reads all module files and extracts element names and relationships.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

def extract_citations_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """Extract citations from module 02 citations file."""
    citations = []
    content = file_path.read_text()

    # Extract citations from the References section
    ref_pattern = r'(?:Red Hat.*?|National Institute.*?|Beyer.*?)\(\d{4}[a-z]?\)\.\s*\*([^*]+)\*\.'
    matches = re.findall(ref_pattern, content, re.DOTALL)

    # Parse each reference
    ref_section = content.split('### References')[1].split('---')[0] if '### References' in content else ''
    refs = ref_section.strip().split('\n\n')

    for ref in refs:
        if ref.strip() and not ref.startswith('#'):
            # Extract title, authors, date
            lines = [l.strip() for l in ref.split('\n') if l.strip()]
            if lines:
                citation = {"raw": ref.strip()}
                citations.append(citation)

    return citations

def extract_alphas_from_file(file_path: Path) -> Dict[str, Any]:
    """Extract alpha definitions from module 03 files."""
    alphas = {}
    content = file_path.read_text()

    # Find all alpha definitions
    alpha_pattern = r'## Alpha: ([^\n]+)\n\n\*\*Type:\*\* ([^\n]+)\n\n\*\*Focus:\*\* ([^\n]+)'
    matches = re.findall(alpha_pattern, content)

    for alpha_name, alpha_type, focus in matches:
        alpha_name = alpha_name.strip()
        alpha_type = alpha_type.strip()
        focus = focus.strip()

        # Extract states for this alpha
        states = []
        alpha_section_pattern = rf'## Alpha: {re.escape(alpha_name)}.*?(?=## Alpha:|## Team Instances|$)'
        alpha_section_match = re.search(alpha_section_pattern, content, re.DOTALL)

        if alpha_section_match:
            alpha_section = alpha_section_match.group(0)

            # Extract state names
            state_pattern = r'####? State (\d+): ([^\n]+)'
            state_matches = re.findall(state_pattern, alpha_section)
            states = [{"seq": int(seq), "name": name.strip()} for seq, name in state_matches]

        alphas[alpha_name] = {
            "type": alpha_type,
            "focus": focus,
            "states": states,
            "contributesTo": None,  # Will be extracted separately
            "instances": []
        }

    return alphas

def extract_alpha_instances(content: str) -> List[str]:
    """Extract alpha instance names from Team Instances section."""
    instances = []

    # Find Team Instances section
    instances_pattern = r'\*\*Instance: ([^\n]+)\*\*'
    matches = re.findall(instances_pattern, content)
    instances.extend([m.strip() for m in matches])

    return instances

def extract_work_products(file_path: Path) -> Dict[str, Any]:
    """Extract work product definitions from module 04."""
    work_products = {}
    content = file_path.read_text()

    # Find all work product definitions
    wp_pattern = r'### Work Product: ([^\n]+)'
    matches = re.findall(wp_pattern, content)

    for wp_name in matches:
        wp_name = wp_name.strip()

        # Extract levels of detail for this work product
        levels = []
        wp_section_pattern = rf'### Work Product: {re.escape(wp_name)}.*?(?=### Work Product:|## |$)'
        wp_section_match = re.search(wp_section_pattern, content, re.DOTALL)

        if wp_section_match:
            wp_section = wp_section_match.group(0)

            # Extract level names and sequence
            level_pattern = r'\*\*Level (\d+): ([^\*]+)\*\* \(seq: (\d+)\)'
            level_matches = re.findall(level_pattern, wp_section)
            levels = [{"seq": int(seq), "name": name.strip(), "level_num": int(level_num)}
                     for level_num, name, seq in level_matches]

        work_products[wp_name] = {
            "levels": levels,
            "instances": []
        }

    return work_products

def extract_activities(file_path: Path) -> Dict[str, Any]:
    """Extract activity definitions from module 05."""
    activities = {}
    content = file_path.read_text()

    # Find all activity definitions
    activity_pattern = r'####? Activity: ([^\n]+)\n\n\*\*ActivitySpace:\*\* ([^\n]+)\n\n\*\*Focus:\*\* ([^\n]+)'
    matches = re.findall(activity_pattern, content)

    for activity_name, activity_space, focus in matches:
        activities[activity_name.strip()] = {
            "activitySpace": activity_space.strip(),
            "focus": focus.strip()
        }

    return activities

def extract_personas(file_path: Path) -> List[str]:
    """Extract persona names from module 05."""
    personas = []
    content = file_path.read_text()

    # Find all persona definitions
    persona_pattern = r'### Persona: ([^\n]+)'
    matches = re.findall(persona_pattern, content)
    personas.extend([m.strip() for m in matches])

    return personas

def extract_persona_groups(file_path: Path) -> Dict[str, List[str]]:
    """Extract persona groups (teams) from module 05."""
    groups = {}
    content = file_path.read_text()

    # Find all persona group definitions
    group_pattern = r'### Persona Group: ([^\n]+)'
    matches = re.findall(group_pattern, content)

    for group_name in matches:
        group_name = group_name.strip()

        # Extract team members for this group
        group_section_pattern = rf'### Persona Group: {re.escape(group_name)}.*?(?=### Persona Group:|## |$)'
        group_section_match = re.search(group_section_pattern, content, re.DOTALL)

        members = []
        if group_section_match:
            group_section = group_section_match.group(0)

            # Find Team Members section
            if '**Team Members:**' in group_section:
                members_section = group_section.split('**Team Members:**')[1].split('\n\n')[0]
                member_pattern = r'- \*\*([^\*]+)\*\*'
                member_matches = re.findall(member_pattern, members_section)
                members = [m.strip() for m in member_matches]

        groups[group_name] = members

    return groups

def extract_patterns(file_path: Path) -> Dict[str, Any]:
    """Extract pattern definitions from module 06."""
    patterns = {}
    content = file_path.read_text()

    # Find all pattern definitions
    pattern_pattern = r'### Pattern: ([^\n]+)\n\n\*\*Type:\*\* ([^\n]+)'
    matches = re.findall(pattern_pattern, content)

    for pattern_name, pattern_type in matches:
        pattern_name = pattern_name.strip()

        # Extract views (phases) for this pattern
        views = []
        pattern_section_pattern = rf'### Pattern: {re.escape(pattern_name)}.*?(?=### Pattern:|$)'
        pattern_section_match = re.search(pattern_section_pattern, content, re.DOTALL)

        if pattern_section_match:
            pattern_section = pattern_section_match.group(0)

            # Extract phase/view names
            phase_pattern = r'#####? (?:Phase|View) (\d+): ([^\n]+)'
            phase_matches = re.findall(phase_pattern, pattern_section)
            views = [{"seq": int(seq), "name": name.strip()} for seq, name in phase_matches]

        patterns[pattern_name] = {
            "type": pattern_type.strip(),
            "views": views
        }

    return patterns

def extract_aliases(file_path: Path) -> List[Dict[str, str]]:
    """Extract aliases from module 07."""
    aliases = []
    content = file_path.read_text()

    # Find all alias definitions
    alias_pattern = r'### ([^\n]+) → ([^\n]+)\n\n\*\*Legacy Term:\*\* ([^\n]+)\n\n\*\*Current AAP 2\.6 Term:\*\* ([^\n]+)'
    matches = re.findall(alias_pattern, content)

    for _, _, legacy_term, current_term in matches:
        aliases.append({
            "sourceTerm": legacy_term.strip(),
            "baselineElement": current_term.strip(),
            "elementType": "component"  # Default type
        })

    return aliases

def main():
    """Main extraction function."""
    base_path = Path('practices/red-hat-ansible-automation-platform/report-elements')

    # Initialize structure
    cross_ref = {
        "method": {
            "name": "Red Hat Ansible Automation Platform",
            "baselinePracticeName": "Platform Adoption Essentials",
            "methodType": "Method",
            "practices": [
                "Platform Administration & Operations",
                "Automation Content Development & Delivery"
            ],
            "generatedDate": "2026-05-20"
        },
        "practice1": {
            "name": "Platform Administration & Operations",
            "alphas": {},
            "alphaInstances": [],
            "workProducts": {},
            "workProductInstances": [],
            "activities": {},
            "personas": [],
            "personaGroups": {},
            "patterns": {},
            "aliases": [],
            "citations": []
        },
        "practice2": {
            "name": "Automation Content Development & Delivery",
            "alphas": {},
            "alphaInstances": [],
            "workProducts": {},
            "workProductInstances": [],
            "activities": {},
            "personas": [],
            "personaGroups": {},
            "patterns": {},
            "aliases": [],
            "citations": []
        },
        "baselineReferences": {
            "focuses": ["Value", "Solution", "Endeavor"],
            "activitySpaces": set(),
            "competencies": set(),
            "narrativeTypes": set()
        }
    }

    # Extract Practice 1 elements
    print("Extracting Practice 1 elements...")
    p1_path = base_path / 'practice-1'

    if (p1_path / '02-citations.md').exists():
        cross_ref['practice1']['citations'] = extract_citations_from_file(p1_path / '02-citations.md')

    # Extract alphas from both 03a and 03b files
    for alpha_file in ['03a-alphas-solution.md', '03b-alphas-endeavor.md']:
        if (p1_path / alpha_file).exists():
            alphas = extract_alphas_from_file(p1_path / alpha_file)
            cross_ref['practice1']['alphas'].update(alphas)

            # Extract instances
            content = (p1_path / alpha_file).read_text()
            instances = extract_alpha_instances(content)
            cross_ref['practice1']['alphaInstances'].extend(instances)

    if (p1_path / '04-workproducts.md').exists():
        cross_ref['practice1']['workProducts'] = extract_work_products(p1_path / '04-workproducts.md')

    if (p1_path / '05-activities-roles.md').exists():
        cross_ref['practice1']['activities'] = extract_activities(p1_path / '05-activities-roles.md')
        cross_ref['practice1']['personas'] = extract_personas(p1_path / '05-activities-roles.md')
        cross_ref['practice1']['personaGroups'] = extract_persona_groups(p1_path / '05-activities-roles.md')

        # Extract activity spaces and competencies
        content = (p1_path / '05-activities-roles.md').read_text()
        for activity_data in cross_ref['practice1']['activities'].values():
            cross_ref['baselineReferences']['activitySpaces'].add(activity_data['activitySpace'])

    if (p1_path / '06-patterns.md').exists():
        cross_ref['practice1']['patterns'] = extract_patterns(p1_path / '06-patterns.md')

    if (p1_path / '07-aliases.md').exists():
        cross_ref['practice1']['aliases'] = extract_aliases(p1_path / '07-aliases.md')

    # Extract Practice 2 elements
    print("Extracting Practice 2 elements...")
    p2_path = base_path / 'practice-2'

    if (p2_path / '02-citations.md').exists():
        cross_ref['practice2']['citations'] = extract_citations_from_file(p2_path / '02-citations.md')

    if (p2_path / '03-alphas.md').exists():
        cross_ref['practice2']['alphas'] = extract_alphas_from_file(p2_path / '03-alphas.md')
        content = (p2_path / '03-alphas.md').read_text()
        instances = extract_alpha_instances(content)
        cross_ref['practice2']['alphaInstances'].extend(instances)

    if (p2_path / '04-workproducts.md').exists():
        cross_ref['practice2']['workProducts'] = extract_work_products(p2_path / '04-workproducts.md')

    if (p2_path / '05-activities-roles.md').exists():
        cross_ref['practice2']['activities'] = extract_activities(p2_path / '05-activities-roles.md')
        cross_ref['practice2']['personas'] = extract_personas(p2_path / '05-activities-roles.md')
        cross_ref['practice2']['personaGroups'] = extract_persona_groups(p2_path / '05-activities-roles.md')

        # Extract activity spaces and competencies
        content = (p2_path / '05-activities-roles.md').read_text()
        for activity_data in cross_ref['practice2']['activities'].values():
            cross_ref['baselineReferences']['activitySpaces'].add(activity_data['activitySpace'])

    if (p2_path / '06-patterns.md').exists():
        cross_ref['practice2']['patterns'] = extract_patterns(p2_path / '06-patterns.md')

    if (p2_path / '07-aliases.md').exists():
        cross_ref['practice2']['aliases'] = extract_aliases(p2_path / '07-aliases.md')

    # Convert sets to sorted lists
    cross_ref['baselineReferences']['activitySpaces'] = sorted(list(cross_ref['baselineReferences']['activitySpaces']))
    cross_ref['baselineReferences']['competencies'] = sorted(list(cross_ref['baselineReferences']['competencies']))
    cross_ref['baselineReferences']['narrativeTypes'] = sorted(list(cross_ref['baselineReferences']['narrativeTypes']))

    # Write output
    output_path = Path('practices/red-hat-ansible-automation-platform/cross-reference-index.json')
    with open(output_path, 'w') as f:
        json.dump(cross_ref, f, indent=2)

    print(f"\nExtraction complete!")
    print(f"Practice 1: {len(cross_ref['practice1']['alphas'])} alphas, {len(cross_ref['practice1']['workProducts'])} work products, {len(cross_ref['practice1']['activities'])} activities")
    print(f"Practice 2: {len(cross_ref['practice2']['alphas'])} alphas, {len(cross_ref['practice2']['workProducts'])} work products, {len(cross_ref['practice2']['activities'])} activities")
    print(f"Baseline references: {len(cross_ref['baselineReferences']['activitySpaces'])} activity spaces")
    print(f"\nOutput written to: {output_path}")

if __name__ == '__main__':
    main()
