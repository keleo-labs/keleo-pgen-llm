#!/usr/bin/env python3
"""
Phase 2: Complete Module Content Extraction
Systematically extracts ALL content from modules to build complete Practice JSON
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

def extract_practice_metadata(module_path: Path) -> Dict[str, Any]:
    """Extract complete metadata from Module 01"""
    content = module_path.read_text()

    # Extract basic fields
    name = re.search(r'\*\*Name:\*\*\s*(.+)', content)
    desc = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*)', content, re.DOTALL)
    created = re.search(r'\*\*Created:\*\*\s*(\d{4}-\d{2}-\d{2})', content)
    updated = re.search(r'\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})', content)
    version = re.search(r'\*\*Version:\*\*\s*(.+)', content)

    # Extract authors
    authors_section = re.search(r'\*\*Authors:\*\*\s*\n(.+?)(?=\n\*\*)', content, re.DOTALL)
    authors = []
    if authors_section:
        for line in authors_section.group(1).split('\n'):
            if line.strip().startswith('-'):
                authors.append(line.strip('- ').strip())

    # Extract keywords
    keywords_section = re.search(r'### Keywords\s*\n(.+?)(?=\n###)', content, re.DOTALL)
    keywords = []
    if keywords_section:
        for line in keywords_section.group(1).split('\n'):
            if line.strip().startswith('-'):
                keywords.append(line.strip('- ').strip())

    # Extract tags
    def extract_tags(tag_name):
        pattern = rf'\*\*{tag_name}:\*\*\s*\n(.+?)(?=\n\*\*|\n###)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return [t.strip('- ').strip() for t in match.group(1).split('\n') if t.strip() and t.strip().startswith('-')]
        return []

    domain_tags = extract_tags('Domain Tags')
    lifecycle_tags = extract_tags('Lifecycle Tags')
    org_tags = extract_tags('Organizational Tags')

    # Extract dependencies
    dep_match = re.search(r'\*\*Dependencies:\*\*\s*(.+?)(?=\n\*\*|\n###)', content, re.DOTALL)
    dependencies = []
    if dep_match and 'None' not in dep_match.group(1):
        dep_text = dep_match.group(1)
        if 'Platform Administration' in dep_text:
            dependencies.append('Platform Administration & Operations')

    return {
        "name": name.group(1).strip() if name else "",
        "description": desc.group(1).strip() if desc else "",
        "authors": authors,
        "createdAt": created.group(1) if created else "2026-05-20",
        "updatedAt": updated.group(1) if updated else "2026-05-20",
        "version": version.group(1).strip() if version else "1.0",
        "keywords": keywords,
        "tags": {
            "domainTags": domain_tags,
            "lifecycleTags": lifecycle_tags,
            "organizationalTags": org_tags
        },
        "practiceDependencyNames": dependencies
    }

def extract_citations(module_path: Path) -> List[Dict[str, Any]]:
    """Extract complete citations from Module 02"""
    content = module_path.read_text()
    citations = []

    # Find citation details section
    citation_section = re.search(r'## Citation Details(.+?)(?=\n## |$)', content, re.DOTALL)
    if not citation_section:
        return citations

    # Split by numbered citations
    citation_blocks = re.split(r'\n\*\*\d+\.\s+', citation_section.group(1))

    for block in citation_blocks[1:]:
        # Extract title from first line
        title_match = re.match(r'(.+?)\*\*', block)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        # Extract fields
        authors_match = re.search(r'\*\*Authors?:\*\*\s*(.+?)(?=\n\*\*)', block, re.DOTALL)
        date_match = re.search(r'\*\*Date Published:\*\*\s*(\d{4})', block)
        source_match = re.search(r'\*\*Source:\*\*\s*(.+?)(?=\n\*\*)', block, re.DOTALL)
        url_match = re.search(r'\*\*URL:\*\*\s*(.+?)(?=\n\*\*)', block, re.DOTALL)
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', block, re.DOTALL)

        # Parse authors
        authors = []
        if authors_match:
            authors_text = authors_match.group(1).strip()
            if ',' in authors_text and 'Inc' not in authors_text:
                authors = [a.strip() for a in authors_text.split(',')]
            else:
                authors = [authors_text]

        # Build citation
        citation = {
            "name": title,
            "description": desc_match.group(1).strip() if desc_match else "",
            "authors": authors,
            "date": date_match.group(1) if date_match else "2026",
            "source": source_match.group(1).strip() if source_match else ""
        }

        # Add URL if present
        if url_match:
            url_text = url_match.group(1).strip()
            if url_text and 'N/A' not in url_text:
                citation["url"] = url_text

        citations.append(citation)

    return citations

def enrich_json_from_modules(practice_num: int, json_path: Path, modules_dir: Path):
    """Enrich Practice JSON with complete module content"""

    # Load current JSON
    with open(json_path) as f:
        method = json.load(f)

    practice = method['practices'][practice_num - 1]

    print(f"\n{'='*60}")
    print(f"Enriching Practice {practice_num}: {practice['name']}")
    print(f"{'='*60}")

    # Module 01: Metadata
    print("\n[1/7] Extracting metadata from Module 01...")
    metadata_path = modules_dir / "01-practice-details.md"
    if metadata_path.exists():
        metadata = extract_practice_metadata(metadata_path)
        practice.update(metadata)
        print(f"  ✓ Updated: description, {len(metadata['keywords'])} keywords, {len(metadata['tags']['domainTags'])} domain tags")

    # Module 02: Citations
    print("\n[2/7] Extracting citations from Module 02...")
    citations_path = modules_dir / "02-citations.md"
    if citations_path.exists():
        citations = extract_citations(citations_path)
        practice['citations'] = citations
        print(f"  ✓ Extracted {len(citations)} complete citations")

    # Module 03: Alphas (may be split)
    print("\n[3/7] Extracting alphas from Module 03...")
    # Will implement full extraction in next iteration
    print(f"  ⚠ Placeholder: {len(practice['alphas'])} alphas need full extraction")

    # Module 04: Work Products
    print("\n[4/7] Extracting work products from Module 04...")
    print(f"  ⚠ Placeholder: {len(practice['workProducts'])} work products need full extraction")

    # Module 05: Activities, Personas
    print("\n[5/7] Extracting activities and personas from Module 05...")
    print(f"  ⚠ Placeholder: {len(practice['activities'])} activities need full extraction")

    # Module 06: Patterns
    print("\n[6/7] Extracting patterns from Module 06...")
    print(f"  ⚠ Placeholder: {len(practice['patterns'])} patterns need full extraction")

    # Module 07: Aliases
    print("\n[7/7] Extracting aliases from Module 07...")
    aliases_path = modules_dir / "07-aliases.md"
    if aliases_path.exists():
        content = aliases_path.read_text()
        if 'No Aliases' not in content:
            # Extract from table
            table_match = re.search(r'\|.+Source Term.+\|(.+?)(?=\n\n|$)', content, re.DOTALL)
            if table_match:
                aliases = []
                rows = [r.strip() for r in table_match.group(1).split('\n') if '|' in r and '---' not in r]
                for row in rows:
                    cells = [c.strip() for c in row.split('|') if c.strip()]
                    if len(cells) >= 3:
                        aliases.append({
                            "practiceElementType": cells[2],
                            "practiceElementName": cells[1],
                            "aliasName": cells[0]
                        })
                practice['practiceElementAliases'] = aliases
                print(f"  ✓ Extracted {len(aliases)} aliases")
        else:
            print(f"  ✓ No aliases required")

    # Save updated JSON
    with open(json_path, 'w') as f:
        json.dump(method, f, indent=2)

    print(f"\n✓ Practice {practice_num} partially enriched")
    return practice

def main():
    """Main extraction workflow"""
    json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
    base_dir = Path("practices/red-hat-ansible-automation-platform/report-elements")

    # Enrich Practice 1
    practice1_dir = base_dir / "practice-1"
    enrich_json_from_modules(1, json_path, practice1_dir)

    # Enrich Practice 2
    practice2_dir = base_dir / "practice-2"
    enrich_json_from_modules(2, json_path, practice2_dir)

    # Load final JSON for summary
    with open(json_path) as f:
        method = json.load(f)

    print(f"\n{'='*60}")
    print(f"ENRICHMENT SUMMARY")
    print(f"{'='*60}")
    print(f"\nFile: {json_path.name}")
    print(f"Size: {json_path.stat().st_size / 1024:.1f} KB")

    for i, practice in enumerate(method['practices'], 1):
        print(f"\nPractice {i}: {practice['name']}")
        print(f"  Citations: {len(practice['citations'])} (enriched)")
        print(f"  Alphas: {len(practice['alphas'])} (needs extraction)")
        print(f"  Work Products: {len(practice['workProducts'])} (needs extraction)")
        print(f"  Activities: {len(practice['activities'])} (needs extraction)")
        print(f"  Patterns: {len(practice['patterns'])} (needs extraction)")
        print(f"  Aliases: {len(practice['practiceElementAliases'])} (enriched)")

if __name__ == "__main__":
    main()
