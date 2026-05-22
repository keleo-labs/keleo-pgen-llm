#!/usr/bin/env python3
"""
Alpha Parser - Extracts alpha definitions from Phase 1 alpha modules

Handles both single files (03-alphas.md) and split files (03a, 03b, 03c)
Parses alpha metadata, states, checklists, narratives, and instances
"""

import re
from typing import Dict, List, Optional, Tuple

def parse_alpha_files(alpha_files: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse one or more alpha module files.

    Args:
        alpha_files: List of file paths to alpha modules

    Returns:
        Tuple of (alphas, alpha_instances)
    """
    alphas = []
    alpha_instances = []

    for filepath in alpha_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        file_alphas, file_instances = parse_alpha_content(content)
        alphas.extend(file_alphas)
        alpha_instances.extend(file_instances)

    return alphas, alpha_instances

def parse_alpha_content(content: str) -> Tuple[List[Dict], List[Dict]]:
    """Parse alpha definitions from module content."""
    alphas = []
    alpha_instances = []

    # Find all alpha sections (handles both ## Alpha: and ### Alpha:)
    alpha_pattern = r'(^##+ Alpha: .+?)(?=^##+ Alpha:|^## [^A]|^# |\Z)'
    alpha_sections = re.finditer(alpha_pattern, content, re.MULTILINE | re.DOTALL)

    for section_match in alpha_sections:
        alpha_block = section_match.group(1)
        alpha_data = parse_single_alpha(alpha_block)
        if alpha_data:
            alphas.append(alpha_data)

    # Extract alpha instances (simplified - would need more context)
    instance_pattern = r'### Alpha Instances?: (.+?)\n\n(.+?)(?=\n##+ |\Z)'
    instance_matches = re.finditer(instance_pattern, content, re.DOTALL)

    for instance_match in instance_matches:
        alpha_name = instance_match.group(1).strip()
        instances_text = instance_match.group(2)

        # Parse individual instances
        inst_pattern = r'\*\*Instance: (.+?)\*\*\s*\n\s*(.+?)(?=\n\n|\*\*Instance:|\Z)'
        for inst_match in re.finditer(inst_pattern, instances_text, re.DOTALL):
            instance_name = inst_match.group(1).strip()
            instance_desc = inst_match.group(2).strip()

            alpha_instances.append({
                "name": instance_name,
                "description": instance_desc,
                "alphaName": alpha_name
            })

    return alphas, alpha_instances

def parse_single_alpha(alpha_block: str) -> Optional[Dict]:
    """Parse a single alpha definition block."""

    # Extract alpha name
    name_match = re.search(r'^##+ Alpha: (.+)', alpha_block, re.MULTILINE)
    if not name_match:
        return None

    alpha_name = name_match.group(1).strip()

    # Extract type
    type_match = re.search(r'\*\*Type:\*\* (.+)', alpha_block)
    if type_match:
        type_text = type_match.group(1)
        if "Redeclaration" in type_text or "enriches baseline" in type_text:
            alpha_type = "redeclaration"
        elif "New Alpha" in type_text or "Specialization" in type_text:
            alpha_type = "new"
        else:
            alpha_type = "baseline"
    else:
        alpha_type = "redeclaration"  # Default assumption

    # Extract focus
    focus_match = re.search(r'\*\*Focus:\*\* (Value|Solution|Endeavor)', alpha_block)
    focus = focus_match.group(1) if focus_match else None

    # Extract description (first paragraph after alpha header, before Type/Focus)
    desc_pattern = r'^##+ Alpha: .+?\n\n(.+?)(?=\n\*\*Type:\*\*|\n\*\*Focus:\*\*|\n###|\n##|\Z)'
    desc_match = re.search(desc_pattern, alpha_block, re.MULTILINE | re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    # Clean up - take first sentence if multi-sentence
    if description:
        sentences = description.split('.')
        description = sentences[0].strip() + '.'

    # Extract contributesTo (for new alphas)
    contributes_match = re.search(r'\*\*Contributes To:\*\* (.+)', alpha_block)
    contributes_to = contributes_match.group(1).strip() if contributes_match else None

    # Parse states
    states = parse_alpha_states(alpha_block)

    # Parse narratives (simplified)
    narratives = parse_alpha_narratives(alpha_block)

    alpha_data = {
        "name": alpha_name,
        "description": description,
        "focusName": focus,
        "states": states
    }

    if alpha_type == "new" and contributes_to:
        alpha_data["contributesTo"] = contributes_to

    if narratives:
        alpha_data["narratives"] = narratives

    return alpha_data

def parse_alpha_states(alpha_block: str) -> List[Dict]:
    """Parse all states for an alpha."""
    states = []

    # Find Progressive States section
    states_section_match = re.search(r'###+ Progressive States\s*(.+?)(?=\n## |\Z)', alpha_block, re.DOTALL)
    if not states_section_match:
        # Try alternate header
        states_section_match = re.search(r'###+ States\s*(.+?)(?=\n## |\Z)', alpha_block, re.DOTALL)

    if not states_section_match:
        return states

    states_content = states_section_match.group(1)

    # Parse individual states
    state_pattern = r'\*\*State (\d+): (.+?)\*\* \(seq: (\d+)\)\s*\n\s*(.+?)(?=\n---|\n\*\*State \d+:|\Z)'
    state_matches = re.finditer(state_pattern, states_content, re.DOTALL)

    for state_match in state_matches:
        state_num = int(state_match.group(1))
        state_name = state_match.group(2).strip()
        seq = int(state_match.group(3))
        state_block = state_match.group(4)

        # Extract state description (first paragraph)
        state_desc_match = re.search(r'^(.+?)(?=\n\n|\n\*\*Criteria|\Z)', state_block, re.DOTALL)
        state_description = state_desc_match.group(1).strip() if state_desc_match else ""

        # Parse checklist
        checklist = parse_state_checklist(state_block)

        state_data = {
            "name": state_name,
            "description": state_description,
            "seq": seq,
            "checklist": checklist
        }

        states.append(state_data)

    return states

def parse_state_checklist(state_block: str) -> List[Dict]:
    """Parse checklist items for a state."""
    checklist = []

    # Find criteria section
    criteria_match = re.search(r'\*\*Criteria for achieving this state:\*\*\s*\n(.+?)(?=\n---|\n\*\*|\Z)', state_block, re.DOTALL)
    if not criteria_match:
        return checklist

    criteria_content = criteria_match.group(1)

    # Parse numbered criteria
    # Pattern: 1. **Name:** Description
    criteria_pattern = r'(\d+)\.\s+\*\*(.+?):\*\*\s+(.+?)(?=\n\d+\.|\Z)'
    criteria_matches = re.finditer(criteria_pattern, criteria_content, re.DOTALL)

    for criteria_match in criteria_matches:
        seq = int(criteria_match.group(1))
        name = criteria_match.group(2).strip()
        description = criteria_match.group(3).strip()
        # Clean up multi-line descriptions
        description = ' '.join(description.split())

        checklist.append({
            "name": name,
            "description": description,
            "seq": seq
        })

    return checklist

def parse_alpha_narratives(alpha_block: str) -> List[Dict]:
    """Parse narratives for an alpha (simplified)."""
    narratives = []

    # Look for common narrative sections
    narrative_sections = [
        ("Context and Rationale", "Essay"),
        ("Research and Industry Practice", "Essay"),
        ("Application Guidance", "Essay"),
        ("Common Challenges", "Essay")
    ]

    for section_name, narrative_type in narrative_sections:
        section_pattern = rf'###+ {section_name}\s*\n(.+?)(?=\n###+ |\n## |\Z)'
        section_match = re.search(section_pattern, alpha_block, re.DOTALL)

        if section_match:
            content = section_match.group(1).strip()

            # Parse into paragraphs as narrative contexts
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            narrative_contexts = []
            for i, para in enumerate(paragraphs, 1):
                # Map to narrative elements (simplified - would need proper element mapping)
                element_name = "Body" if narrative_type == "Essay" else "Context"
                if i == 1 and narrative_type == "Essay":
                    element_name = "Introduction"
                elif i == len(paragraphs) and narrative_type == "Essay":
                    element_name = "Conclusion"

                narrative_contexts.append({
                    "seq": i,
                    "narrativeElementName": element_name,
                    "context": para
                })

            if narrative_contexts:
                narratives.append({
                    "narrativeTypeName": narrative_type,
                    "narrativeContexts": narrative_contexts
                })

    return narratives

def validate_alpha_against_baseline(alpha: Dict, baseline_alphas: Dict) -> List[str]:
    """
    Validate alpha against baseline framework.

    Returns list of validation errors (empty if valid)
    """
    errors = []

    alpha_name = alpha.get("name", "")

    # Check if redeclaration matches baseline
    if alpha_name in baseline_alphas:
        baseline_alpha = baseline_alphas[alpha_name]

        # Validate states match baseline
        baseline_states = {s["name"] for s in baseline_alpha.get("states", [])}
        practice_states = {s["name"] for s in alpha.get("states", [])}

        # All baseline states should be present
        missing_states = baseline_states - practice_states
        if missing_states:
            errors.append(f"Alpha '{alpha_name}' missing baseline states: {missing_states}")

    # Check contributesTo exists if specified
    if "contributesTo" in alpha:
        contributes_to = alpha["contributesTo"]
        if contributes_to and contributes_to not in baseline_alphas:
            errors.append(f"Alpha '{alpha_name}' contributesTo '{contributes_to}' which doesn't exist in baseline")

    return errors

if __name__ == "__main__":
    # Test the parser
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python alpha_parser.py <alpha-file.md> [<alpha-file2.md> ...]")
        sys.exit(1)

    alphas, instances = parse_alpha_files(sys.argv[1:])

    print(f"Parsed {len(alphas)} alphas and {len(instances)} instances")
    print(json.dumps(alphas, indent=2))
