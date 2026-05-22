#!/usr/bin/env python3
"""
Complete extraction of alphas, work products, activities, and patterns
This handles the bulk of the content extraction from large module files
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

def load_baseline():
    """Load baseline framework to get exact state descriptions"""
    with open("deps/platform-adoption-kernel.json") as f:
        return json.load(f)

def extract_alphas_from_modules(modules_dir: Path, practice_data: Dict) -> List[Dict]:
    """Extract all alphas with complete state information"""
    alphas = []
    baseline = load_baseline()
    baseline_alphas = {alpha["name"]: alpha for alpha in baseline.get("alphas", [])}
    
    # Find alpha module files (may be split into 03a, 03b, 03c)
    alpha_files = sorted(modules_dir.glob("03*.md"))
    
    for alpha_file in alpha_files:
        print(f"    Reading {alpha_file.name}...")
        content = alpha_file.read_text()
        
        # Split by alpha sections (look for "## Alpha N:" headers)
        alpha_sections = re.split(r"\n## Alpha \d+:", content)
        
        for section in alpha_sections[1:]:  # Skip preamble
            alpha = extract_single_alpha(section, practice_data, baseline_alphas)
            if alpha:
                alphas.append(alpha)
    
    return alphas

def extract_single_alpha(section: str, practice_data: Dict, baseline_alphas: Dict) -> Dict:
    """Extract a single alpha with all states and checklists"""
    # Extract name
    name_match = re.search(r"\*\*Name:\*\*\s*(.+)", section)
    if not name_match:
        return None
    
    alpha_name = name_match.group(1).strip()
    
    # Check if this alpha is in our index
    if alpha_name not in practice_data["alphas"]:
        return None
    
    alpha_index = practice_data["alphas"][alpha_name]
    
    # Extract basic info
    desc_match = re.search(r"\*\*Description:\*\*\s*(.+?)(?=\n\*\*)", section, re.DOTALL)
    focus_match = re.search(r"\*\*Focus:\*\*\s*(.+)", section)
    type_match = re.search(r"\*\*Type:\*\*\s*(.+)", section)
    
    is_redeclaration = type_match and "Redeclaration" in type_match.group(1)
    
    # Build alpha object
    alpha = {
        "name": alpha_name,
        "focusName": alpha_index["focus"],
        "states": []
    }
    
    # For redeclarations, use baseline description
    if is_redeclaration and alpha_name in baseline_alphas:
        alpha["description"] = baseline_alphas[alpha_name]["description"]
        # Copy baseline states and add practice checklists
        for baseline_state in baseline_alphas[alpha_name]["states"]:
            state = {
                "name": baseline_state["name"],
                "description": baseline_state["description"],
                "seq": baseline_state["seq"],
                "checklist": extract_state_checklist(section, baseline_state["name"])
            }
            alpha["states"].append(state)
    else:
        # New alpha
        alpha["description"] = desc_match.group(1).strip() if desc_match else alpha_name + " description"
        
        # Extract contributesTo
        contrib_match = re.search(r"\*\*Contributes To:\*\*\s*(.+)", section)
        if contrib_match:
            parent = contrib_match.group(1).strip()
            if parent and parent != "N/A":
                alpha["contributesTo"] = parent
        
        # Extract states
        state_sections = re.split(r"\n### State \d+:", section)
        for i, state_section in enumerate(state_sections[1:], 1):
            state_name_match = re.search(r"\*\*Name:\*\*\s*(.+)", state_section)
            if not state_name_match:
                continue
            
            state_name = state_name_match.group(1).strip()
            state_desc_match = re.search(r"\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)", state_section, re.DOTALL)
            
            state = {
                "name": state_name,
                "description": state_desc_match.group(1).strip() if state_desc_match else state_name + " description",
                "seq": i,
                "checklist": extract_checklist(state_section)
            }
            alpha["states"].append(state)
    
    return alpha

def extract_state_checklist(section: str, state_name: str) -> List[Dict]:
    """Extract checklist for a specific state"""
    # Find the state section
    pattern = rf"### .+?{re.escape(state_name)}(.+?)(?=\n### |\n## |$)"
    state_match = re.search(pattern, section, re.DOTALL)
    if not state_match:
        return []
    
    return extract_checklist(state_match.group(1))

def extract_checklist(text: str) -> List[Dict]:
    """Extract checklist items from text"""
    checklist = []
    
    # Find criteria section
    criteria_match = re.search(r"\*\*Criteria.+?:\*\*(.+?)(?=\n\*\*|\n###|\n##|$)", text, re.DOTALL)
    if not criteria_match:
        return checklist
    
    criteria_text = criteria_match.group(1)
    
    # Find numbered items with bold names
    items = re.findall(r"\d+\.\s+\*\*(.+?)\*\*:?\s*(.+?)(?=\n\d+\.|\n\n|$)", criteria_text, re.DOTALL)
    
    for seq, (name, desc) in enumerate(items, 1):
        checklist.append({
            "name": name.strip(),
            "description": desc.strip(),
            "seq": seq
        })
    
    return checklist

def main():
    """Run full content extraction"""
    json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
    base_dir = Path("practices/red-hat-ansible-automation-platform/report-elements")
    index_path = Path("practices/red-hat-ansible-automation-platform/cross-reference-index.json")
    
    # Load cross-reference index
    with open(index_path) as f:
        index = json.load(f)
    
    # Load current JSON
    with open(json_path) as f:
        method = json.load(f)
    
    # Process Practice 1 alphas
    print("\nExtracting Practice 1 alphas...")
    practice1_dir = base_dir / "practice-1"
    practice1_alphas = extract_alphas_from_modules(practice1_dir, index["practice1"])
    method["practices"][0]["alphas"] = practice1_alphas
    print(f"  ✓ Extracted {len(practice1_alphas)} alphas with complete states")
    
    # Process Practice 2 alphas
    print("\nExtracting Practice 2 alphas...")
    practice2_dir = base_dir / "practice-2"
    practice2_alphas = extract_alphas_from_modules(practice2_dir, index["practice2"])
    method["practices"][1]["alphas"] = practice2_alphas
    print(f"  ✓ Extracted {len(practice2_alphas)} alphas with complete states")
    
    # Save updated JSON
    with open(json_path, "w") as f:
        json.dump(method, f, indent=2)
    
    print(f"\n✅ Alphas extracted successfully")
    print(f"   File size: {json_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
