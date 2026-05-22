#!/usr/bin/env python3
"""
Work Product Parser - Extracts work product definitions from Phase 1 modules

Parses work products with levels of detail, contributions to alphas, and instances
"""

import re
from typing import Dict, List, Optional, Tuple

def parse_workproduct_file(filepath: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse work products from a work products module file.

    Args:
        filepath: Path to 04-workproducts.md

    Returns:
        Tuple of (work_products, work_product_instances)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_workproduct_content(content)

def parse_workproduct_content(content: str) -> Tuple[List[Dict], List[Dict]]:
    """Parse work product definitions from module content."""
    work_products = []
    work_product_instances = []

    # Find all work product sections (handles ## Work Product: and ### Work Product:)
    wp_pattern = r'(^##+ Work Product: .+?)(?=^##+ Work Product:|^## [^W]|^# |\Z)'
    wp_sections = re.finditer(wp_pattern, content, re.MULTILINE | re.DOTALL)

    for section_match in wp_sections:
        wp_block = section_match.group(1)
        wp_data = parse_single_workproduct(wp_block)
        if wp_data:
            work_products.append(wp_data)

    return work_products, work_product_instances

def parse_single_workproduct(wp_block: str) -> Optional[Dict]:
    """Parse a single work product definition block."""

    # Extract work product name
    name_match = re.search(r'^##+ Work Product: (.+)', wp_block, re.MULTILINE)
    if not name_match:
        return None

    wp_name = name_match.group(1).strip()

    # Extract description (first paragraph after name)
    desc_pattern = r'^##+ Work Product: .+?\n\n(.+?)(?=\n\n|\n####|\n###|\Z)'
    desc_match = re.search(desc_pattern, wp_block, re.MULTILINE | re.DOTALL)
    description = ""
    if desc_match:
        desc_text = desc_match.group(1).strip()
        # Take first sentence
        sentences = desc_text.split('.')
        description = sentences[0].strip() + '.' if sentences else desc_text

    # Parse levels of detail
    levels = parse_levels_of_detail(wp_block)

    # Parse usage narrative (simplified)
    usage_narrative = parse_usage_narrative(wp_block)

    wp_data = {
        "name": wp_name,
        "description": description,
        "levelsOfDetail": levels
    }

    if usage_narrative:
        wp_data["narratives"] = [usage_narrative]

    return wp_data

def parse_levels_of_detail(wp_block: str) -> List[Dict]:
    """Parse all levels of detail for a work product."""
    levels = []

    # Find Levels of Detail section
    lod_section_match = re.search(r'###+ Levels of Detail\s*(.+?)(?=\n## |\Z)', wp_block, re.DOTALL)
    if not lod_section_match:
        return levels

    lod_content = lod_section_match.group(1)

    # Parse individual levels
    # Pattern: **Level N: Name** (seq: N)
    level_pattern = r'\*\*Level (\d+): (.+?)\*\* \(seq: (\d+)\)\s*\n\s*(.+?)(?=\n---|\n\*\*Level \d+:|\Z)'
    level_matches = re.finditer(level_pattern, lod_content, re.DOTALL)

    for level_match in level_matches:
        level_num = int(level_match.group(1))
        level_name = level_match.group(2).strip()
        seq = int(level_match.group(3))
        level_block = level_match.group(4)

        # Extract level description (first paragraph)
        level_desc_match = re.search(r'^(.+?)(?=\n\n|\n\*\*Characteristics|\Z)', level_block, re.DOTALL)
        level_description = level_desc_match.group(1).strip() if level_desc_match else ""

        # Parse characteristics
        characteristics = parse_lod_characteristics(level_block)

        # Parse contributesTo (which alphas this LOD evidences)
        contributes_to = parse_lod_contributions(level_block)

        level_data = {
            "name": level_name,
            "description": level_description,
            "seq": seq,
            "characteristics": characteristics
        }

        if contributes_to:
            level_data["contributesTo"] = contributes_to

        levels.append(level_data)

    return levels

def parse_lod_characteristics(level_block: str) -> List[Dict]:
    """Parse characteristics for a level of detail."""
    characteristics = []

    # Find Characteristics section
    char_match = re.search(r'\*\*Characteristics:\*\*\s*\n(.+?)(?=\n\*\*This level provides|\Z)', level_block, re.DOTALL)
    if not char_match:
        return characteristics

    char_content = char_match.group(1)

    # Parse numbered characteristics
    # Pattern: 1. **Name:** Description
    char_pattern = r'(\d+)\.\s+\*\*(.+?):\*\*\s+(.+?)(?=\n\d+\.|\Z)'
    char_matches = re.finditer(char_pattern, char_content, re.DOTALL)

    for char_match in char_matches:
        seq = int(char_match.group(1))
        name = char_match.group(2).strip()
        description = char_match.group(3).strip()
        # Clean up multi-line
        description = ' '.join(description.split())

        characteristics.append({
            "name": name,
            "description": description,
            "seq": seq
        })

    return characteristics

def parse_lod_contributions(level_block: str) -> List[Dict]:
    """Parse which alpha states this LOD evidences."""
    contributions = []

    # Find "This level provides evidence for:" section
    evidence_match = re.search(r'\*\*This level provides evidence for:\*\*\s*\n(.+?)(?=\n---|\n\*\*|\Z)', level_block, re.DOTALL)
    if not evidence_match:
        return contributions

    evidence_content = evidence_match.group(1)

    # Parse bullet points: - **AlphaName** reaching **StateName** state
    contribution_pattern = r'- \*\*(.+?)\*\* reaching \*\*(.+?)\*\* state'
    contribution_matches = re.finditer(contribution_pattern, evidence_content)

    for contrib_match in contribution_matches:
        alpha_name = contrib_match.group(1).strip()
        state_name = contrib_match.group(2).strip()

        contributions.append({
            "alphaName": alpha_name,
            "stateName": state_name
        })

    return contributions

def parse_usage_narrative(wp_block: str) -> Optional[Dict]:
    """Parse Usage and Context narrative for a work product."""

    # Look for Usage and Context section
    usage_match = re.search(r'###+ Usage and Context\s*\n(.+?)(?=\n###+ |\n## |\Z)', wp_block, re.DOTALL)
    if not usage_match:
        return None

    content = usage_match.group(1).strip()

    # Parse into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    if not paragraphs:
        return None

    narrative_contexts = []
    for i, para in enumerate(paragraphs, 1):
        # Simple mapping to Essay elements
        element_name = "Body"
        if i == 1:
            element_name = "Introduction"
        elif i == len(paragraphs):
            element_name = "Conclusion"

        narrative_contexts.append({
            "seq": i,
            "narrativeElementName": element_name,
            "context": para
        })

    return {
        "narrativeTypeName": "Essay",
        "narrativeContexts": narrative_contexts
    }

if __name__ == "__main__":
    # Test the parser
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python workproduct_parser.py <workproducts-file.md>")
        sys.exit(1)

    work_products, instances = parse_workproduct_file(sys.argv[1])

    print(f"Parsed {len(work_products)} work products")
    print(json.dumps(work_products, indent=2))
