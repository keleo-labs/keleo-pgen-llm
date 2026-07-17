#!/usr/bin/env python3
"""
Generate complete horticulture-essentials baseline JSON from mapping guide.
Reads the partial JSON and mapping guide, then generates all remaining elements.
"""

import json
import re
from pathlib import Path

def parse_mapping_guide():
    """Parse the mapping guide to extract structured data."""
    guide_path = Path('baselines/horticulture-essentials/02-mapping-guide.md')
    with open(guide_path, 'r') as f:
        content = f.read()

    return content

def extract_alpha_section(content, alpha_name):
    """Extract a complete alpha section from the mapping guide."""
    # Find the alpha section
    pattern = rf'### Alpha: {re.escape(alpha_name)}\n\n(.*?)(?=\n### Alpha: |\n## ActivitySpaces|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None
    return match.group(1)

def parse_alpha_from_section(section_text, alpha_name):
    """Parse alpha structure from section text."""
    alpha = {
        "name": alpha_name,
        "description": "",
        "focusName": "",
        "relatesTo": [],
        "states": []
    }

    # Extract description
    desc_match = re.search(r'\*\*Description\*\*: (.+)', section_text)
    if desc_match:
        alpha["description"] = desc_match.group(1).strip()

    # Extract focus
    focus_match = re.search(r'\*\*Focus\*\*: (.+)', section_text)
    if focus_match:
        alpha["focusName"] = focus_match.group(1).strip()

    # Extract relatesTo relationships
    relates_section = re.search(r'\*\*relatesTo\*\*:\n(.*?)(?=\n\*\*States\*\*:|\Z)', section_text, re.DOTALL)
    if relates_section:
        for line in relates_section.group(1).split('\n'):
            if '|' in line and line.strip().startswith('- **'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    rel_type = parts[0].replace('- **', '').replace('**', '').strip()
                    target_alpha = parts[1].strip()
                    rationale = parts[2].strip()
                    alpha["relatesTo"].append({
                        "relationship": rel_type,
                        "alphaName": target_alpha,
                        "rationale": rationale
                    })

    # Extract states
    states_section = re.search(r'\*\*States\*\*:\n(.*?)(?=\n- \*\*Narrative\*\*:|\Z)', section_text, re.DOTALL)
    if states_section:
        state_blocks = re.findall(r'(\d+)\. \*\*(.+?)\*\*\n\s+- \*\*Description\*\*: (.+?)\n\s+- \*\*Checklists\*\*:\n(.*?)(?=\n\s+\d+\. \*\*|\Z)', states_section.group(1), re.DOTALL)

        for seq, state_name, state_desc, checklist_text in state_blocks:
            checklist_items = []
            for item in re.findall(r'- \[ \] (.+)', checklist_text):
                checklist_items.append({
                    "name": item.split('|')[0].strip() if '|' in item else item[:50].strip(),
                    "description": item.strip(),
                    "seq": len(checklist_items) + 1
                })

            alpha["states"].append({
                "name": state_name.strip(),
                "description": state_desc.strip(),
                "seq": int(seq),
                "checklist": checklist_items
            })

    return alpha

def extract_activity_spaces(content):
    """Extract all activity spaces from mapping guide."""
    activity_spaces = []

    # Find ActivitySpaces section
    section_match = re.search(r'## ActivitySpaces\n\n.*?\n\n(.*?)(?=\n## Competencies|\Z)', content, re.DOTALL)
    if not section_match:
        return activity_spaces

    section_text = section_match.group(1)

    # Extract each activity space
    as_blocks = re.findall(r'### ActivitySpace: (.+?)\n\n- \*\*Description\*\*: (.+?)\n- \*\*Focus\*\*: (.+?)\n- \*\*contributesTo\*\*:\n(.*?)- \*\*requiredCompetencies\*\*:\n(.*?)(?=\n- \*\*Narrative\*\*:|\n### ActivitySpace:|\Z)', section_text, re.DOTALL)

    for name, desc, focus, contributes_text, comps_text in as_blocks:
        contributes_to = []
        for line in contributes_text.split('\n'):
            if '→' in line and line.strip().startswith('- '):
                parts = line.strip('- ').split('→')
                alpha_name = parts[0].strip()
                states = parts[1].strip() if len(parts) > 1 else ""
                for state in states.split(','):
                    state = state.strip()
                    if state:
                        contributes_to.append({
                            "alphaName": alpha_name,
                            "stateName": state
                        })

        required_comps = []
        for line in comps_text.split('\n'):
            if line.strip().startswith('- '):
                comp = line.strip('- ').strip()
                if comp:
                    required_comps.append(comp)

        activity_spaces.append({
            "name": name.strip(),
            "description": desc.strip(),
            "focusName": focus.strip(),
            "contributesTo": contributes_to,
            "requiredCompetencies": required_comps
        })

    return activity_spaces

def extract_citations(content):
    """Extract citations from mapping guide."""
    citations = []

    # Find Citations section
    section_match = re.search(r'## Citations\n\n.*?\n\n(.*?)(?=\n## Assets|\Z)', content, re.DOTALL)
    if not section_match:
        return citations

    section_text = section_match.group(1)

    # Extract each citation
    cit_blocks = re.findall(r'### Citation: (.+?)\n\n.*?\*\*Element Mapping\*\*:\n\s+- \*\*Author\*\*: (.+?)\n\s+- \*\*Date\*\*: (.+?)\n\s+- \*\*Title\*\*: (.+?)\n\s+- \*\*Source\*\*: (.+?)(?=\n---|\n### Citation:|\Z)', section_text, re.DOTALL)

    for title_ref, author, date, title, source in cit_blocks:
        citations.append({
            "author": author.strip(),
            "date": date.strip(),
            "title": title.strip(),
            "source": source.strip()
        })

    return citations

def extract_assets(content):
    """Extract assets from mapping guide."""
    assets = []

    # Find Assets section
    section_match = re.search(r'## Assets\n\n.*?\n\n(.*?)(?=\n## Mapping Statistics|\Z)', content, re.DOTALL)
    if not section_match:
        return assets

    section_text = section_match.group(1)

    # Extract font-character assets
    asset_blocks = re.findall(r'### Asset: (.+?)\n\n- \*\*Type\*\*: font-character\n- \*\*Description\*\*: (.+?)\n- \*\*Font Family\*\*: (.+?)\n- \*\*Font Character\*\*: (.+?)\n- \*\*Font Weight\*\*: (.+?)\n', section_text, re.DOTALL)

    for name, desc, font_family, font_char, font_weight in asset_blocks:
        assets.append({
            "name": name.strip(),
            "type": "font-character",
            "description": desc.strip(),
            "fontFamily": font_family.strip(),
            "fontCharacter": font_char.strip(),
            "fontWeight": font_weight.strip()
        })

    return assets

def main():
    """Main generation function."""
    print("Loading partial baseline JSON...")
    baseline_path = Path('baselines/horticulture-essentials/horticulture-essentials.json')
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)

    print("Parsing mapping guide...")
    content = parse_mapping_guide()

    # Remove Citation Standard from narrativeTypes
    print("Removing Citation Standard from narrativeTypes...")
    baseline["narrativeTypes"] = [nt for nt in baseline["narrativeTypes"] if nt["name"] != "Citation Standard"]

    # Add remaining alphas
    print("Extracting remaining alphas...")
    remaining_alphas = [
        "Crop Protection",
        "Biosecurity & Ecosystem Health",
        "Sustainability & Environmental Stewardship",
        "Production System Architecture",
        "Technical Infrastructure",
        "Resource Management",
        "Digital Integration",
        "Business Operations & Governance",
        "Regulatory Compliance & Standards"
    ]

    for alpha_name in remaining_alphas:
        print(f"  Processing alpha: {alpha_name}")
        section = extract_alpha_section(content, alpha_name)
        if section:
            alpha = parse_alpha_from_section(section, alpha_name)
            baseline["alphas"].append(alpha)
        else:
            print(f"  WARNING: Could not find section for {alpha_name}")

    # Add activity spaces
    print("Extracting activity spaces...")
    baseline["activitySpaces"] = extract_activity_spaces(content)
    print(f"  Found {len(baseline['activitySpaces'])} activity spaces")

    # Add baseline narrative
    print("Adding baseline narrative...")
    baseline["narratives"] = [
        {
            "targetElementName": "Horticulture Essentials",
            "narrativeTypeName": "Hero's Journey",
            "narrativeContexts": [
                {
                    "narrativeElementName": "Ordinary World",
                    "contextText": "Horticulture has historically operated through fragmented knowledge domains—plant science, engineering, business—with limited integration. Practitioners learned through apprenticeship and experience, facing environmental unpredictability, pest pressure, resource scarcity, and market volatility. Traditional methods often degraded ecosystems (soil depletion, water pollution, biodiversity loss) while failing to achieve economic viability for many operations."
                },
                {
                    "narrativeElementName": "Call to Adventure",
                    "contextText": "Modern challenges demand a unified framework: climate change intensifies weather extremes; consumers demand sustainable production; technological advances (CEA, IoT, AI) create new opportunities; regulatory requirements tighten; global competition forces innovation. The 'Horticulture Essentials' baseline emerges as a comprehensive ontology integrating biological systems, production operations, and professional practice—a common language for the profession."
                },
                {
                    "narrativeElementName": "Challenges & Trials",
                    "contextText": "Mastering plant physiology while deploying precision agriculture technologies; balancing productivity with environmental stewardship; navigating complex regulatory frameworks; managing business viability amid volatile markets; building competency across biological, engineering, and management domains; coordinating multi-stakeholder ecosystems (growers, suppliers, regulators, customers, communities)."
                },
                {
                    "narrativeElementName": "Transformation",
                    "contextText": "Horticulture evolves from a craft-based, extractive industry to a science-driven, regenerative profession. Practitioners integrate deep plant science knowledge with advanced engineering systems and strategic business management. Operations achieve triple-bottom-line success (economic viability, environmental regeneration, social contribution). The profession attracts talent, earns public respect, and becomes recognized as essential to food security, climate mitigation, and urban well-being."
                },
                {
                    "narrativeElementName": "Return with Knowledge",
                    "contextText": "Chartered professionals mentor the next generation through formal apprenticeships and continuing professional development programs. Industry leaders contribute to policy development, standard-setting, and public education. Research advances shared through peer-reviewed publications, industry conferences, and open-source platforms. The Horticulture Essentials baseline becomes the foundation for specialized extension practices (e.g., 'Vertical Farming Operations,' 'Heritage Garden Restoration,' 'Urban Greening Programs') that build upon this shared ontology."
                }
            ]
        }
    ]

    # Add citations
    print("Extracting citations...")
    baseline["citations"] = extract_citations(content)
    print(f"  Found {len(baseline['citations'])} citations")

    # Add assets
    print("Extracting assets...")
    baseline["assets"] = extract_assets(content)
    print(f"  Found {len(baseline['assets'])} assets")

    # Write complete baseline
    print("Writing complete baseline JSON...")
    with open(baseline_path, 'w') as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print("\n=== Generation Complete ===")
    print(f"Total alphas: {len(baseline['alphas'])}")
    print(f"Total activitySpaces: {len(baseline['activitySpaces'])}")
    print(f"Total competencies: {len(baseline['competencies'])}")
    print(f"Total narrativeTypes: {len(baseline['narrativeTypes'])}")
    print(f"Total narratives: {len(baseline['narratives'])}")
    print(f"Total citations: {len(baseline['citations'])}")
    print(f"Total assets: {len(baseline['assets'])}")
    print(f"\nBaseline JSON written to: {baseline_path}")

if __name__ == "__main__":
    main()
