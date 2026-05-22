"""
Citation Parser: Extract citation metadata including URLs.
"""
import re
from pathlib import Path
from typing import Dict, Optional, List, Any


def parse_citation_block(citation_text: str) -> Dict[str, Any]:
    """
    Parse a single citation block from module 02.

    Expected format:
    ### Citation N: [Title]
    **Authors:** [List]
    **Date Published:** [YYYY]
    **Title:** [Full title]
    **Source:** [Publisher]
    **URL:** [URL or N/A]
    **Description:** [Text]

    Args:
        citation_text: Text of citation block

    Returns:
        Dict with citation fields
    """
    citation = {}

    # Extract title from header
    title_match = re.search(r'### Citation \d+: (.+?)$', citation_text, re.MULTILINE)
    if title_match:
        citation["name"] = title_match.group(1).strip()

    # Extract authors
    authors_match = re.search(r'\*\*Authors:\*\* (.+?)$', citation_text, re.MULTILINE)
    if authors_match:
        authors_text = authors_match.group(1).strip()
        # Split by comma, ampersand, or "and"
        citation["authors"] = [a.strip() for a in re.split(r',|&| and ', authors_text) if a.strip()]

    # Extract date
    date_match = re.search(r'\*\*Date Published:\*\* (.+?)$', citation_text, re.MULTILINE)
    if date_match:
        citation["date"] = date_match.group(1).strip()

    # Extract title (may differ from header)
    title_field_match = re.search(r'\*\*Title:\*\* (.+?)$', citation_text, re.MULTILINE)
    if title_field_match:
        citation["title_full"] = title_field_match.group(1).strip()

    # Extract source
    source_match = re.search(r'\*\*Source:\*\* (.+?)$', citation_text, re.MULTILINE)
    if source_match:
        citation["source"] = source_match.group(1).strip()

    # Extract URL
    url_match = re.search(r'\*\*URL:\*\* (.+?)$', citation_text, re.MULTILINE)
    if url_match:
        url_text = url_match.group(1).strip()
        if url_text and url_text.lower() not in ["n/a", "none", "not available"]:
            citation["url"] = url_text

    # Extract description
    desc_match = re.search(r'\*\*Description:\*\* (.+?)(?:\n\n|\Z)', citation_text, re.DOTALL)
    if desc_match:
        citation["description"] = desc_match.group(1).strip()

    return citation


def extract_citations_from_module(module_path: Path) -> List[Dict]:
    """
    Extract all citations from module 02 file.

    Args:
        module_path: Path to 02-citations.md

    Returns:
        List of citation dicts
    """
    content = module_path.read_text()

    # Split by citation headers
    citation_blocks = re.split(r'(?=### Citation \d+:)', content)

    citations = []
    for block in citation_blocks:
        if block.strip() and "### Citation" in block:
            citation = parse_citation_block(block)
            if citation:
                citations.append(citation)

    return citations


def format_citation_json(parsed: Dict) -> Dict:
    """
    Convert parsed citation to JSON schema format.

    Args:
        parsed: Dict from parse_citation_block()

    Returns:
        Schema-compliant citation dict
    """
    json_citation = {
        "name": parsed.get("name", ""),
        "description": parsed.get("description", ""),
        "authors": parsed.get("authors", []),
        "date": parsed.get("date", ""),
        "source": parsed.get("source", ""),
    }

    # Add URL only if present
    if "url" in parsed:
        json_citation["url"] = parsed["url"]

    return json_citation


if __name__ == "__main__":
    # Test with sample citation block
    sample_citation = """
### Citation 1: AWS Well-Architected Framework

**Authors:** Amazon Web Services
**Date Published:** 2024
**Title:** AWS Well-Architected Framework
**Source:** Amazon Web Services Documentation
**URL:** https://aws.amazon.com/architecture/well-architected/
**Description:** Provides architectural best practices for cloud platforms, informing alpha state criteria and activity guidance.
"""

    parsed = parse_citation_block(sample_citation)
    print("Parsed citation:")
    print(f"  Name: {parsed.get('name')}")
    print(f"  Authors: {parsed.get('authors')}")
    print(f"  Date: {parsed.get('date')}")
    print(f"  Source: {parsed.get('source')}")
    print(f"  URL: {parsed.get('url')}")
    print(f"  Description: {parsed.get('description')}")

    json_citation = format_citation_json(parsed)
    print("\nJSON formatted citation:")
    import json
    print(json.dumps(json_citation, indent=2))
