#!/usr/bin/env python3
"""Extract work products with LODs, checklists, and contributesTo relationships"""

import json
import re
from pathlib import Path

def extract_work_products(module_path: Path, practice_data: Dict) -> List[Dict]:
    """Extract all work products from Module 04"""
    content = module_path.read_text()
    work_products = []
    
    # Split by work product sections
    wp_sections = re.split(r'\n## Work Product \d+:', content)
    
    for section in wp_sections[1:]:
        wp = extract_single_wp(section, practice_data)
        if wp:
            work_products.append(wp)
    
    return work_products

def extract_single_wp(section: str, practice_data: Dict) -> Dict:
    """Extract a single work product"""
    name_match = re.search(r'\*\*Name:\*\*\s*(.+)', section)
    if not name_match:
        return None
    
    wp_name = name_match.group(1).strip()
    
    # Check against index
    if wp_name not in practice_data["workProducts"]:
        return None
    
    desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)', section, re.DOTALL)
    
    wp = {
        "name": wp_name,
        "description": desc_match.group(1).strip() if desc_match else wp_name + " description",
        "levelsOfDetail": []
    }
    
    # Extract LODs
    lod_sections = re.split(r'\n### Level \d+:', section)
    
    for i, lod_section in enumerate(lod_sections[1:], 1):
        lod_name_match = re.search(r'\*\*Name:\*\*\s*(.+)', lod_section)
        if not lod_name_match:
            continue
        
        lod_name = lod_name_match.group(1).strip()
        lod_desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)', lod_section, re.DOTALL)
        
        # Extract checklist
        checklist = extract_checklist(lod_section)
        
        # Extract contributesTo
        contrib = extract_contributions(lod_section)
        
        lod = {
            "name": lod_name,
            "description": lod_desc_match.group(1).strip() if lod_desc_match else lod_name + " description",
            "seq": i,
            "checklist": checklist,
            "contributesTo": contrib
        }
        
        wp["levelsOfDetail"].append(lod)
    
    return wp

def extract_checklist(text: str) -> List[Dict]:
    """Extract checklist items"""
    checklist = []
    
    criteria_match = re.search(r'\*\*(?:Characteristics|Criteria).+?:\*\*(.+?)(?=\n\*\*|\n###|$)', text, re.DOTALL)
    if not criteria_match:
        return checklist
    
    criteria_text = criteria_match.group(1)
    items = re.findall(r'\d+\.\s+\*\*(.+?)\*\*:?\s*(.+?)(?=\n\d+\.|\n\n|$)', criteria_text, re.DOTALL)
    
    for seq, (name, desc) in enumerate(items, 1):
        checklist.append({
            "name": name.strip(),
            "description": desc.strip(),
            "seq": seq
        })
    
    return checklist

def extract_contributions(text: str) -> List[Dict]:
    """Extract alpha contributions"""
    contributions = []
    
    evidence_match = re.search(r'provides evidence for.+?:(.+?)(?=\n\*\*|\n###|$)', text, re.DOTALL | re.IGNORECASE)
    if not evidence_match:
        return contributions
    
    evidence_text = evidence_match.group(1)
    pairs = re.findall(r'\*\*([^*]+)\*\*\s+reaching\s+\*\*([^*]+)\*\*', evidence_text)
    
    for alpha_name, state_name in pairs:
        contributions.append({
            "alphaName": alpha_name.strip(),
            "stateName": state_name.strip()
        })
    
    return contributions

def main():
    json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
    base_dir = Path("practices/red-hat-ansible-automation-platform/report-elements")
    index_path = Path("practices/red-hat-ansible-automation-platform/cross-reference-index.json")
    
    with open(index_path) as f:
        index = json.load(f)
    
    with open(json_path) as f:
        method = json.load(f)
    
    # Practice 1
    print("\nExtracting Practice 1 work products...")
    wp1_path = base_dir / "practice-1" / "04-workproducts.md"
    method["practices"][0]["workProducts"] = extract_work_products(wp1_path, index["practice1"])
    print(f"  ✓ Extracted {len(method['practices'][0]['workProducts'])} work products")
    
    # Practice 2
    print("\nExtracting Practice 2 work products...")
    wp2_path = base_dir / "practice-2" / "04-workproducts.md"
    method["practices"][1]["workProducts"] = extract_work_products(wp2_path, index["practice2"])
    print(f"  ✓ Extracted {len(method['practices'][1]['workProducts'])} work products")
    
    with open(json_path, "w") as f:
        json.dump(method, f, indent=2)
    
    print(f"\n✅ Work products extracted")
    print(f"   File size: {json_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
