#!/usr/bin/env python3
"""
Pattern Parser - Extracts pattern definitions from Phase 1 modules

Parses patterns with views, tracked alphas, and narratives
"""

import re
from typing import Dict, List, Optional

def parse_pattern_file(filepath: str) -> tuple[List[Dict], List[Dict]]:
    """
    Parse patterns from a patterns module file.

    Args:
        filepath: Path to 06-patterns.md

    Returns:
        Tuple of (patterns list, alpha_instances list)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_patterns(content)

def parse_patterns(content: str) -> tuple[List[Dict], List[Dict]]:
    """
    Parse all pattern definitions from content.

    Returns:
        Tuple of (patterns list, alpha_instances list)
    """
    patterns = []
    all_instances = {}  # Dict to track unique instances {(instanceName, alphaName): instance_dict}

    # Find all pattern sections (handles ## Pattern: and ### Pattern:)
    pattern_pattern = r'(^##+ Pattern: .+?)(?=^##+ Pattern:|^## [^P]|^# |\Z)'
    pattern_sections = re.finditer(pattern_pattern, content, re.MULTILINE | re.DOTALL)

    for section_match in pattern_sections:
        pattern_block = section_match.group(1)
        pattern_data, instances = parse_single_pattern(pattern_block)
        if pattern_data:
            patterns.append(pattern_data)
            # Collect unique instances
            for inst in instances:
                key = (inst["instanceName"], inst["alphaName"])
                all_instances[key] = inst

    # Convert instances dict to list
    instances_list = list(all_instances.values())

    return patterns, instances_list

def parse_single_pattern(pattern_block: str) -> tuple[Optional[Dict], List[Dict]]:
    """
    Parse a single pattern definition block.

    Returns:
        Tuple of (pattern_dict, instances_list)
    """

    # Extract pattern name
    name_match = re.search(r'^##+ Pattern: (.+)', pattern_block, re.MULTILINE)
    if not name_match:
        return None, []

    pattern_name = name_match.group(1).strip()

    # Extract type
    type_match = re.search(r'\*\*Type:\*\* (.+)', pattern_block)
    pattern_type = type_match.group(1).strip() if type_match else "Lifecycle"

    # Extract description (first paragraph)
    desc_pattern = r'^##+ Pattern: .+?\n\n(.+?)(?=\n\*\*Type:|\n###|\Z)'
    desc_match = re.search(desc_pattern, pattern_block, re.MULTILINE | re.DOTALL)
    description = ""
    if desc_match:
        desc_text = desc_match.group(1).strip()
        sentences = desc_text.split('.')
        description = sentences[0].strip() + '.' if sentences else desc_text

    # Extract narrative type
    narrative_type_match = re.search(r'\*\*Narrative Type:\*\* (.+)', pattern_block)
    narrative_type = narrative_type_match.group(1).strip() if narrative_type_match else None

    # Parse pattern views and collect instances
    views, instances = parse_pattern_views(pattern_block)

    pattern_data = {
        "name": pattern_name,
        "description": description,
        "type": pattern_type,
        "patternViews": views
    }

    if narrative_type:
        pattern_data["narrativeTypeName"] = narrative_type

    return pattern_data, instances

def parse_pattern_views(pattern_block: str) -> tuple[List[Dict], List[Dict]]:
    """
    Parse pattern views (phases/steps in the pattern).

    Returns:
        Tuple of (views list, instances list)
    """
    views = []
    all_instances = {}  # Track unique instances

    # Find Pattern Views or Views section (including "Pattern Views (Phases)")
    views_section_match = re.search(r'###+ (?:Pattern )?Views(?:\s*\(Phases\))?\s*(.+?)(?=\n## |\Z)', pattern_block, re.DOTALL)
    if not views_section_match:
        # Try alternate: look for View 1, View 2, etc.
        views_section_match = re.search(r'(###+ View \d+:.+?)(?=\n## |\Z)', pattern_block, re.DOTALL)
    if not views_section_match:
        # Try Phase format
        views_section_match = re.search(r'(###+ Phase \d+:.+?)(?=\n## |\Z)', pattern_block, re.DOTALL)

    if not views_section_match:
        return views, []

    views_content = views_section_match.group(0) if views_section_match.group(0).startswith('###') else views_section_match.group(1)

    # Parse individual views - try multiple patterns
    # Pattern 1: ##### Phase N: Name
    view_pattern = r'#{4,5} Phase (\d+): (.+?)\s*\n(.+?)(?=\n#{4,5} Phase \d+:|\n## |\Z)'
    view_matches = list(re.finditer(view_pattern, views_content, re.MULTILINE | re.DOTALL))

    # Pattern 2: ### View N: Name or **View N: Name** (fallback)
    if not view_matches:
        view_pattern = r'(?:###+ View |^\*\*View )(\d+): (.+?)(?:\*\*)?\s*\n(.+?)(?=\n###+ View \d+:|\n\*\*View \d+:|\n## |\Z)'
        view_matches = list(re.finditer(view_pattern, views_content, re.MULTILINE | re.DOTALL))

    for view_match in view_matches:
        view_num = int(view_match.group(1))
        view_name = view_match.group(2).strip()
        view_block = view_match.group(3).strip()

        # Extract view description (first paragraph)
        view_desc_match = re.search(r'^(.+?)(?=\n\n|\n\*\*|\Z)', view_block, re.DOTALL)
        view_description = view_desc_match.group(1).strip() if view_desc_match else ""
        # Clean to first sentence
        if view_description:
            sentences = view_description.split('.')
            view_description = sentences[0].strip() + '.'

        # Parse activities in this view
        activities = parse_view_activities(view_block)

        # Parse alpha states tracked in this view
        alpha_states = parse_view_alpha_states(view_block)

        # Parse alpha instances tracked in this view
        view_instances = parse_view_alpha_instances(view_block)

        # Collect unique instances
        for inst in view_instances:
            key = (inst["instanceName"], inst["alphaName"])
            all_instances[key] = inst

        view_data = {
            "seq": view_num,  # Phase numbering already 0-indexed
            "name": view_name,
            "description": view_description,
            "activities": activities,
            "alphaStates": alpha_states,
            "alphaInstances": [inst["instanceName"] for inst in view_instances]  # Just the names
        }

        views.append(view_data)

    instances_list = list(all_instances.values())
    return views, instances_list

def parse_view_activities(view_block: str) -> List[str]:
    """Parse activities emphasized in this view."""
    activities = []

    # Find Activities section
    activities_match = re.search(r'\*\*Activities(?: Emphasized)?:\*\*\s*\n(.+?)(?=\n\*\*|\Z)', view_block, re.DOTALL)
    if not activities_match:
        return activities

    activities_content = activities_match.group(1)

    # Parse bullet list
    activity_pattern = r'- (.+?)(?:\n|$)'
    activity_matches = re.finditer(activity_pattern, activities_content)

    for activity_match in activity_matches:
        activity_name = activity_match.group(1).strip()
        # Remove any bold markers
        activity_name = re.sub(r'\*\*(.+?)\*\*', r'\1', activity_name)
        activities.append(activity_name)

    return activities

def parse_view_alpha_states(view_block: str) -> List[Dict]:
    """Parse alpha states tracked in this view."""
    alpha_states = []

    # Find Alpha States, Key Milestones, or Areas of Concern section
    states_match = re.search(r'\*\*(?:Alpha States|Key Milestones|Areas of Concern at this Phase):\*\*\s*\n(.+?)(?=\n\*\*|\Z)', view_block, re.DOTALL)
    if not states_match:
        return alpha_states

    states_content = states_match.group(1)

    # Skip intro lines like "By the end of this phase..."
    if "following concepts" in states_content or "following areas" in states_content:
        intro_end = states_content.find('\n\n')
        if intro_end > 0:
            states_content = states_content[intro_end+2:]

    # Parse bullet list - try multiple patterns
    # Pattern 1: - **AlphaName** should reach the **StateName** state
    # Pattern 1a: - **AlphaName** should remain at **StateName** state
    state_pattern = r'- \*\*(.+?)\*\* should (?:reach the |remain at )\*\*(.+?)\*\* state'
    state_matches = list(re.finditer(state_pattern, states_content))

    # Pattern 2: - **AlphaName**: StateName (fallback)
    if not state_matches:
        state_pattern = r'- \*\*(.+?)\*\*[:\s]+(.+?)(?:\n|$)'
        state_matches = list(re.finditer(state_pattern, states_content))

    for state_match in state_matches:
        alpha_name = state_match.group(1).strip()
        state_name = state_match.group(2).strip()
        # Remove "state" suffix if present
        state_name = re.sub(r'\s+state$', '', state_name, flags=re.IGNORECASE)

        alpha_states.append({
            "alphaName": alpha_name,
            "stateName": state_name
        })

    return alpha_states

def parse_view_alpha_instances(view_block: str) -> List[Dict]:
    """Parse alpha instances tracked in this view."""
    instances = []

    # Find Specific Instances Tracked section
    instances_match = re.search(r'\*\*Specific Instances Tracked:\*\*\s*\n(.+?)(?=\n\*\*|\Z)', view_block, re.DOTALL)
    if not instances_match:
        return instances

    instances_content = instances_match.group(1)

    # Pattern: - **InstanceName** (instance of **AlphaName**) should reach/remain at **StateName** state
    instance_pattern = r'- \*\*(.+?)\*\* \(instance of \*\*(.+?)\*\*\)'
    instance_matches = re.finditer(instance_pattern, instances_content)

    for instance_match in instance_matches:
        instance_name = instance_match.group(1).strip()
        alpha_name = instance_match.group(2).strip()

        instances.append({
            "instanceName": instance_name,
            "alphaName": alpha_name
        })

    return instances

if __name__ == "__main__":
    # Test the parser
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python pattern_parser.py <patterns-file.md>")
        sys.exit(1)

    patterns, instances = parse_pattern_file(sys.argv[1])

    print(f"Parsed {len(patterns)} patterns with {len(instances)} unique alpha instances")
    print(json.dumps({"patterns": patterns, "alphaInstances": instances}, indent=2))
