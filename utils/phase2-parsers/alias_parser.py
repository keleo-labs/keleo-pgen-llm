#!/usr/bin/env python3
"""
Alias Parser - Extracts practice element aliases from Phase 1 alias modules

Parses terminology mappings from 07-aliases.md
"""

import re
import sys
from typing import Dict, List, Optional

def parse_alias_file(filepath: str) -> List[Dict]:
    """
    Parse aliases from an alias module file.

    Args:
        filepath: Path to 07-aliases.md

    Returns:
        List of alias dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_aliases(content)

def parse_aliases(content: str) -> List[Dict]:
    """Parse all alias definitions from content."""
    aliases = []

    # Pattern 1: Legacy → Current (with arrow in header)
    # The section has header with arrow, then **Legacy Term:** and **Current Term:** fields
    arrow_pattern = r'###\s+(.+?)\s+→\s+(.+?)\s*\n(.*?)(?=\n---|(?=\n###)|(?=\n##)|\Z)'
    arrow_matches = re.finditer(arrow_pattern, content, re.DOTALL)

    for section_match in arrow_matches:
        header_legacy = section_match.group(1).strip()
        header_current = section_match.group(2).strip()
        alias_block = section_match.group(3)

        # Extract legacy term from body (may have multiple comma-separated)
        legacy_match = re.search(r'\*\*Legacy(?:/Alternative)? Term[s]?:\*\*\s+(.+?)(?=\n\n|\n\*\*)', alias_block, re.DOTALL)
        if legacy_match:
            legacy_terms_text = legacy_match.group(1).strip()
            # Split by comma for multiple aliases
            legacy_terms = [t.strip() for t in legacy_terms_text.split(',')]
        else:
            # Fall back to header
            legacy_terms = [header_legacy]

        # Extract current term from body (take first term before comma if multiple)
        current_match = re.search(r'\*\*Current (?:AAP 2\.6 )?Term:\*\*\s+(.+?)(?=\n\n|\n\*\*|\()', alias_block, re.DOTALL)
        if current_match:
            current_term_text = current_match.group(1).strip()
            # Take only the first term if comma-separated
            current_term = current_term_text.split(',')[0].strip()
        else:
            # Fall back to header
            current_term = header_current

        # Clean quotes from current term
        current_term = current_term.strip('"\'')

        # Determine the element type from context
        element_type = infer_element_type(alias_block, current_term, header_legacy)

        # Create an alias entry for each legacy term
        for legacy_term in legacy_terms:
            alias_data = {
                "practiceElementType": element_type,
                "practiceElementName": current_term,
                "aliasName": legacy_term.strip()
            }
            aliases.append(alias_data)

    # Pattern 2: Alternative Terms (no arrow in header)
    # Header has current term, body has **Alternative Terms:** field
    alt_pattern = r'###\s+([^→\n]+?)\s*\n(.*?)\*\*Alternative Terms:\*\*\s+(.+?)(?=\n\n|\n\*\*)'
    alt_matches = re.finditer(alt_pattern, content, re.DOTALL)

    for section_match in alt_matches:
        header_term = section_match.group(1).strip()
        context_block = section_match.group(2)
        alternative_terms_text = section_match.group(3).strip()

        # Extract current term from **Current AAP 2.6 Term:** field
        current_match = re.search(r'\*\*Current (?:AAP 2\.6 )?Term:\*\*\s+(.+?)(?=\n\n|\n\*\*)', context_block, re.DOTALL)
        if current_match:
            current_term_text = current_match.group(1).strip()
            # Take only the first term if comma-separated
            current_term = current_term_text.split(',')[0].strip()
        else:
            # Fall back to header
            current_term = header_term

        # Clean quotes
        current_term = current_term.strip('"\'')

        # Split alternative terms by comma
        alternative_terms = [t.strip() for t in alternative_terms_text.split(',')]

        # Determine element type
        element_type = infer_element_type(context_block, current_term, header_term)

        # Create alias entry for each alternative term
        for alt_term in alternative_terms:
            alias_data = {
                "practiceElementType": element_type,
                "practiceElementName": current_term,
                "aliasName": alt_term.strip()
            }
            aliases.append(alias_data)

    # Pattern 3: Table format
    # | Source Term | Baseline Element Name | Element Type | Usage Context |
    table_pattern = r'\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|'
    table_matches = re.finditer(table_pattern, content)

    for row_match in table_matches:
        source_term = row_match.group(1).strip()
        baseline_name = row_match.group(2).strip()
        element_type_str = row_match.group(3).strip()
        usage_context = row_match.group(4).strip()

        # Skip header and separator rows
        if source_term in ['Source Term', ':---', '---', '']:
            continue
        if source_term.startswith(':'):
            continue

        # Map element type string to schema type
        element_type = element_type_str
        if element_type not in ['Alpha', 'Activity', 'ActivitySpace', 'WorkProduct', 'Pattern']:
            # Default mapping for common types
            if element_type.lower() in ['tool', 'toolset']:
                element_type = 'WorkProduct'
            else:
                element_type = 'Alpha'

        alias_data = {
            "practiceElementType": element_type,
            "practiceElementName": baseline_name,
            "aliasName": source_term
        }
        aliases.append(alias_data)

    return aliases

def infer_element_type(context: str, current_term: str, legacy_term: str) -> str:
    """
    Infer the practice element type from context.

    Returns one of: Alpha, Activity, ActivitySpace, Focus, WorkProduct,
    Pattern, PatternView, Competency, Persona, PersonaGroup, Narrative
    """
    context_lower = context.lower()

    # Work products - check first as they're very specific
    if any(term in current_term.lower() for term in ['template', 'rulebook', 'project', 'credential', 'inventory']):
        return "WorkProduct"

    if "job template" in context_lower or "workflow" in context_lower or "playbook" in context_lower:
        return "WorkProduct"

    # Deployment/architecture patterns
    if "topology" in current_term.lower() or "deployment" in context_lower:
        return "Pattern"

    # Execution environment is a work product
    if "execution environment" in current_term.lower() or "container image" in context_lower:
        return "WorkProduct"

    # APIs and services - these are typically interfaces to alphas
    if "api" in current_term.lower() or "service" in context_lower:
        return "Alpha"

    # Installation/deployment methods could be patterns
    if "installation" in current_term.lower():
        return "Pattern"

    # Components, platforms, systems - these are alphas
    if any(term in context_lower for term in ['component', 'platform', 'controller', 'hub', 'mesh', 'gateway']):
        return "Alpha"

    # Analytics and monitoring tools
    if "analytics" in context_lower or "insights" in context_lower or "monitoring" in context_lower:
        return "Alpha"

    # Command-line tools
    if "command" in context_lower or "cli" in context_lower or "utility" in context_lower:
        return "WorkProduct"

    # RBAC and auth concepts
    if "rbac" in context_lower or "authentication" in context_lower or "authorization" in context_lower:
        return "Alpha"

    # Default to Alpha for infrastructure/technology components
    return "Alpha"

if __name__ == "__main__":
    # Test the parser
    import json

    if len(sys.argv) < 2:
        print("Usage: python alias_parser.py <aliases-file.md>", file=sys.stderr)
        sys.exit(1)

    aliases = parse_alias_file(sys.argv[1])

    print(f"Parsed {len(aliases)} aliases", file=sys.stderr)
    print(json.dumps(aliases, indent=2))
