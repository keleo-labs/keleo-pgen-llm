#!/usr/bin/env python3
"""
Activity Parser - Extracts activity definitions from Phase 1 modules

Parses activities with competencies, work products, alpha progressions, and technique narratives
"""

import re
from typing import Dict, List, Optional, Tuple

def parse_activity_file(filepath: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Parse activities, personas, and teams from activities module.

    Args:
        filepath: Path to 05-activities-roles.md

    Returns:
        Tuple of (activities, personas, teams)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    activities = parse_activities(content)
    personas = parse_personas(content)
    teams = parse_teams(content)

    return activities, personas, teams

def parse_activities(content: str) -> List[Dict]:
    """Parse all activity definitions from content."""
    activities = []

    # Find all activity sections (handles #### Activity: and ### Activity:)
    activity_pattern = r'(^###+ Activity: .+?)(?=^###+ Activity:|^## [^A]|^# |\Z)'
    activity_sections = re.finditer(activity_pattern, content, re.MULTILINE | re.DOTALL)

    for section_match in activity_sections:
        activity_block = section_match.group(1)
        activity_data = parse_single_activity(activity_block)
        if activity_data:
            activities.append(activity_data)

    return activities

def parse_single_activity(activity_block: str) -> Optional[Dict]:
    """Parse a single activity definition block."""

    # Extract activity name
    name_match = re.search(r'^###+ Activity: (.+)', activity_block, re.MULTILINE)
    if not name_match:
        return None

    activity_name = name_match.group(1).strip()

    # Extract ActivitySpace
    space_match = re.search(r'\*\*ActivitySpace:\*\* (.+)', activity_block)
    activity_space = space_match.group(1).strip() if space_match else None

    # Extract Focus
    focus_match = re.search(r'\*\*Focus:\*\* (Value|Solution|Endeavor)', activity_block)
    focus = focus_match.group(1) if focus_match else None

    # Extract description (paragraph after Focus, before Outcomes)
    # Description comes after the metadata lines (ActivitySpace, Focus)
    desc_pattern = r'\*\*Focus:\*\* (?:Value|Solution|Endeavor)\s*\n\s*(.+?)(?=\n\*\*Outcomes|\Z)'
    desc_match = re.search(desc_pattern, activity_block, re.MULTILINE | re.DOTALL)
    description = ""
    if desc_match:
        desc_text = desc_match.group(1).strip()
        # Take first sentence only
        sentences = desc_text.split('.')
        description = sentences[0].strip() + '.' if sentences else desc_text

    # Parse outcomes (alpha progressions)
    outcomes = parse_activity_outcomes(activity_block)

    # Parse work products
    work_products = parse_activity_workproducts(activity_block)

    # Parse competencies
    competencies = parse_activity_competencies(activity_block)

    # Parse team involvement
    teams = parse_activity_teams(activity_block)

    # Parse technique narrative
    technique_narrative = parse_technique_narrative(activity_block)

    activity_data = {
        "name": activity_name,
        "description": description,
        "activitySpaceName": activity_space,
        "focusName": focus,
        "contributesTo": outcomes,
        "worksOn": work_products,
        "recommendedCompetencyLevels": competencies,
        "involves": teams
    }

    if technique_narrative:
        activity_data["narratives"] = [technique_narrative]

    return activity_data

def parse_activity_outcomes(activity_block: str) -> List[Dict]:
    """Parse alpha state progressions from activity outcomes."""
    outcomes = []

    # Find Outcomes section
    outcomes_match = re.search(r'\*\*Outcomes and Alpha Progression:\*\*\s*\n(.+?)(?=\n\*\*Work Products|\n\*\*Required|\n\*\*Team|\Z)', activity_block, re.DOTALL)
    if not outcomes_match:
        return outcomes

    outcomes_content = outcomes_match.group(1)

    # Parse bullet points: - Progresses **AlphaName** toward **StateName** state
    outcome_pattern = r'- Progresses \*\*(.+?)\*\* toward \*\*(.+?)\*\* state'
    outcome_matches = re.finditer(outcome_pattern, outcomes_content)

    for outcome_match in outcome_matches:
        alpha_name = outcome_match.group(1).strip()
        state_name = outcome_match.group(2).strip()

        outcomes.append({
            "alphaName": alpha_name,
            "stateName": state_name
        })

    return outcomes

def parse_activity_workproducts(activity_block: str) -> List[Dict]:
    """Parse work products created/refined by activity."""
    work_products = []

    # Find Work Products section
    wp_match = re.search(r'\*\*Work Products Created/Refined:\*\*\s*\n(.+?)(?=\n\*\*Required|\n\*\*Team|\Z)', activity_block, re.DOTALL)
    if not wp_match:
        return work_products

    wp_content = wp_match.group(1)

    # Parse bullet points: - **WorkProductName** to **Level X** level
    wp_pattern = r'- \*\*(.+?)\*\* to \*\*(.+?)\*\* level'
    wp_matches = re.finditer(wp_pattern, wp_content)

    for wp_match in wp_matches:
        wp_name = wp_match.group(1).strip()
        level_name = wp_match.group(2).strip()

        work_products.append({
            "workProductName": wp_name,
            "levelOfDetailName": level_name
        })

    return work_products

def parse_activity_competencies(activity_block: str) -> List[Dict]:
    """Parse required competencies and levels."""
    competencies = []

    # Find Required Capabilities section
    comp_match = re.search(r'\*\*Required Capabilities:\*\*\s*\n(.+?)(?=\n\*\*Team|\n\*\*How to|\Z)', activity_block, re.DOTALL)
    if not comp_match:
        return competencies

    comp_content = comp_match.group(1)

    # Parse bullet points: - **CompetencyName** at **LevelName** level
    comp_pattern = r'- \*\*(.+?)\*\* at \*\*(.+?)\*\* level'
    comp_matches = re.finditer(comp_pattern, comp_content)

    for comp_match in comp_matches:
        competency_name = comp_match.group(1).strip()
        level_name = comp_match.group(2).strip()

        competencies.append({
            "competencyName": competency_name,
            "competencyLevelName": level_name
        })

    return competencies

def parse_activity_teams(activity_block: str) -> List[str]:
    """Parse team/persona involvement."""
    teams = []

    # Find Team Involvement section
    team_match = re.search(r'\*\*Team Involvement:\*\*\s*\n(.+?)(?=\n---|\n\*\*How to|\Z)', activity_block, re.DOTALL)
    if not team_match:
        return teams

    team_content = team_match.group(1).strip()

    # Simple comma-separated parsing
    team_parts = [t.strip() for t in team_content.split(',')]
    teams = team_parts

    return teams

def parse_technique_narrative(activity_block: str) -> Optional[Dict]:
    """Parse 'How to Perform This Activity' technique narrative."""

    # Find How to Perform section
    technique_match = re.search(r'\*\*How to Perform This Activity:\*\*\s*\n(.+?)(?=\n###+ Activity:|\n## |\Z)', activity_block, re.DOTALL)
    if not technique_match:
        return None

    technique_content = technique_match.group(1)

    # Extract technique name
    technique_name_match = re.search(r'\*\*Technique: (.+?)\*\*', technique_content)
    technique_name = technique_name_match.group(1).strip() if technique_name_match else "How-To Guide"

    # Extract narrative type
    narrative_type_match = re.search(r'\*\*Narrative Type: (.+?)\*\*', technique_content)
    narrative_type = narrative_type_match.group(1).strip() if narrative_type_match else "How-To Guide"

    # Parse steps
    narrative_contexts = []

    # Find all Step sections
    step_pattern = r'\*\*Step (\d+): (.+?)\*\*\s*\n\s*(.+?)(?=\n\*\*Step \d+:|\n\*\*Completion Criteria:|\Z)'
    step_matches = re.finditer(step_pattern, technique_content, re.DOTALL)

    for step_match in step_matches:
        step_num = int(step_match.group(1))
        step_name = step_match.group(2).strip()
        step_content = step_match.group(3).strip()

        # Clean up content
        step_content = ' '.join(step_content.split())

        narrative_contexts.append({
            "seq": step_num,
            "narrativeElementName": f"Step {step_num}",
            "context": f"{step_name}. {step_content}"
        })

    # Add completion criteria if present
    completion_match = re.search(r'\*\*Completion Criteria:\*\*\s*\n(.+?)(?=\n\*\*Citations|\Z)', technique_content, re.DOTALL)
    if completion_match:
        completion_content = completion_match.group(1).strip()
        completion_content = ' '.join(completion_content.split())

        narrative_contexts.append({
            "seq": len(narrative_contexts) + 1,
            "narrativeElementName": "Completion",
            "context": completion_content
        })

    if not narrative_contexts:
        return None

    return {
        "narrativeTypeName": narrative_type,
        "narrativeContexts": narrative_contexts
    }

def parse_personas(content: str) -> List[Dict]:
    """Parse persona definitions from content."""
    personas = []

    # Find Personas section
    personas_section_match = re.search(r'^## Personas\s*(.+?)(?=^## Teams|^## |\Z)', content, re.MULTILINE | re.DOTALL)
    if not personas_section_match:
        return personas

    personas_content = personas_section_match.group(1)

    # Parse individual personas
    persona_pattern = r'###? Persona: (.+?)\s*\n\s*\*\*Description:\*\*\s+(.+?)(?=\n\n|\n###|\Z)'
    persona_matches = re.finditer(persona_pattern, personas_content, re.DOTALL)

    for persona_match in persona_matches:
        persona_name = persona_match.group(1).strip()
        description = persona_match.group(2).strip()
        # Clean to first sentence
        sentences = description.split('.')
        description = sentences[0].strip() + '.'

        personas.append({
            "name": persona_name,
            "description": description
        })

    return personas

def parse_teams(content: str) -> List[Dict]:
    """Parse team definitions from content."""
    teams = []

    # Find Teams section
    teams_section_match = re.search(r'^## Teams\s*(.+?)(?=^## |\Z)', content, re.MULTILINE | re.DOTALL)
    if not teams_section_match:
        return teams

    teams_content = teams_section_match.group(1)

    # Parse individual teams
    team_pattern = r'###? Team: (.+?)\s*\n\s*\*\*Description:\*\*\s+(.+?)(?=\n\n|\n###|\Z)'
    team_matches = re.finditer(team_pattern, teams_content, re.DOTALL)

    for team_match in team_matches:
        team_name = team_match.group(1).strip()
        description = team_match.group(2).strip()
        # Clean to first sentence
        sentences = description.split('.')
        description = sentences[0].strip() + '.'

        teams.append({
            "name": team_name,
            "description": description
        })

    return teams

if __name__ == "__main__":
    # Test the parser
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python activity_parser.py <activities-file.md>")
        sys.exit(1)

    activities, personas, teams = parse_activity_file(sys.argv[1])

    print(f"Parsed {len(activities)} activities, {len(personas)} personas, {len(teams)} teams")
    print(json.dumps(activities[:2], indent=2))  # Print first 2 activities as sample
