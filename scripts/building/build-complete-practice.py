#!/usr/bin/env python3
"""
Complete Practice JSON Builder - Extracts ALL content from modules
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_resources():
    """Load cross-reference index and baseline"""
    with open("practices/red-hat-ansible-automation-platform/cross-reference-index.json") as f:
        index = json.load(f)
    with open("deps/platform-adoption-kernel.json") as f:
        baseline = json.load(f)
    return index, baseline

def extract_alphas_complete(modules_dir: Path, practice_data: Dict, baseline: Dict) -> List[Dict]:
    """Extract complete alpha data from modules"""
    alphas = []
    baseline_alphas = {alpha["name"]: alpha for alpha in baseline.get("alphas", [])}
    
    # Find alpha module files
    alpha_files = sorted(modules_dir.glob("03*.md"))
    
    for alpha_file in alpha_files:
        content = alpha_file.read_text()
        
        # Split by ## Alpha: pattern
        sections = re.split(r'\n## Alpha: ', content)
        
        for section in sections[1:]:  # Skip preamble
            # Extract alpha name from first line
            first_line = section.split('\n')[0]
            alpha_name = first_line.strip()
            
            # Check if in index
            if alpha_name not in practice_data["alphas"]:
                continue
            
            alpha_index = practice_data["alphas"][alpha_name]
            
            # Extract type
            type_match = re.search(r'\*\*Type:\*\*\s*(.+)', section)
            is_redeclaration = type_match and "Redeclaration" in type_match.group(1)
            
            # Extract description (first paragraph after focus)
            desc_paragraphs = []
            lines = section.split('\n')
            in_desc = False
            for line in lines:
                if '**Focus:**' in line:
                    in_desc = True
                    continue
                if in_desc and line.strip() and not line.startswith('**') and not line.startswith('#'):
                    desc_paragraphs.append(line.strip())
                if in_desc and (line.startswith('###') or line.startswith('**State')):
                    break
            
            description = ' '.join(desc_paragraphs[:3]) if desc_paragraphs else alpha_name + " alpha"
            
            # Build alpha
            alpha = {
                "name": alpha_name,
                "focusName": alpha_index["focus"],
                "states": []
            }
            
            # For redeclarations, use baseline description
            if is_redeclaration and alpha_name in baseline_alphas:
                alpha["description"] = baseline_alphas[alpha_name]["description"]
                
                # Extract practice-specific checklists for baseline states
                for baseline_state in baseline_alphas[alpha_name]["states"]:
                    checklist = extract_checklist_for_state(section, baseline_state["name"])
                    state = {
                        "name": baseline_state["name"],
                        "description": baseline_state["description"],
                        "seq": baseline_state["seq"],
                        "checklist": checklist
                    }
                    alpha["states"].append(state)
            else:
                # New alpha
                alpha["description"] = description
                
                # Extract contributesTo
                contrib_match = re.search(r'\*\*Contributes To:\*\*\s*(.+)', section)
                if contrib_match:
                    parent = contrib_match.group(1).strip()
                    if parent and parent not in ["N/A", "None"]:
                        alpha["contributesTo"] = parent
                
                # Extract states from Progressive States section
                states_section = re.search(r'### Progressive States(.+?)(?=###|$)', section, re.DOTALL)
                if states_section:
                    state_text = states_section.group(1)
                    # Split by **State N:
                    state_blocks = re.split(r'\*\*State \d+:', state_text)
                    
                    for i, state_block in enumerate(state_blocks[1:], 1):
                        # Extract state name from first line
                        state_line_match = re.match(r'\s*(.+?)\*\*', state_block)
                        if not state_line_match:
                            continue
                        state_name = state_line_match.group(1).strip()
                        
                        # Extract description (line after state name, before criteria)
                        desc_match = re.search(r'\*\*\s*\n\n(.+?)(?=\n\n\*\*Criteria)', state_block, re.DOTALL)
                        state_desc = desc_match.group(1).strip() if desc_match else state_name
                        
                        # Extract checklist
                        checklist = extract_checklist_from_text(state_block)
                        
                        state = {
                            "name": state_name,
                            "description": state_desc,
                            "seq": i,
                            "checklist": checklist
                        }
                        alpha["states"].append(state)
            
            alphas.append(alpha)
    
    return alphas

def extract_checklist_for_state(section: str, state_name: str) -> List[Dict]:
    """Extract checklist for a specific state in a redeclaration"""
    # Find state section
    state_pattern = rf'\*\*State \d+: {re.escape(state_name)}\*\*(.+?)(?=\*\*State \d+:|###|$)'
    state_match = re.search(state_pattern, section, re.DOTALL)
    
    if not state_match:
        return []
    
    return extract_checklist_from_text(state_match.group(1))

def extract_checklist_from_text(text: str) -> List[Dict]:
    """Extract numbered checklist items from text"""
    checklist = []
    
    # Find criteria section
    criteria_match = re.search(r'\*\*Criteria.+?:\*\*(.+?)(?=\n\*\*(?![\w\s]*:)|###|$)', text, re.DOTALL)
    if not criteria_match:
        return checklist
    
    criteria_text = criteria_match.group(1)
    
    # Find numbered items with bold names
    # Pattern: 1. **Name:** Description
    items = re.findall(r'\n\d+\.\s+\*\*(.+?)\*\*:?\s*(.+?)(?=\n\d+\.|$)', criteria_text, re.DOTALL)
    
    for seq, (name, desc) in enumerate(items, 1):
        # Clean up description (remove extra whitespace, newlines)
        clean_desc = ' '.join(desc.split())
        checklist.append({
            "name": name.strip(),
            "description": clean_desc.strip(),
            "seq": seq
        })
    
    return checklist

def main():
    print("=" * 60)
    print("COMPLETE PRACTICE JSON BUILDER")
    print("=" * 60)
    
    # Load resources
    print("\n[1/5] Loading resources...")
    index, baseline = load_resources()
    
    # Load current JSON
    json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
    with open(json_path) as f:
        method = json.load(f)
    
    # Extract Practice 1 alphas
    print("\n[2/5] Extracting Practice 1 alphas...")
    practice1_dir = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-1")
    practice1_alphas = extract_alphas_complete(practice1_dir, index["practice1"], baseline)
    method["practices"][0]["alphas"] = practice1_alphas
    print(f"  ✓ Extracted {len(practice1_alphas)} alphas")
    for alpha in practice1_alphas:
        print(f"    - {alpha['name']}: {len(alpha['states'])} states")
    
    # Extract Practice 2 alphas  
    print("\n[3/5] Extracting Practice 2 alphas...")
    practice2_dir = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-2")
    practice2_alphas = extract_alphas_complete(practice2_dir, index["practice2"], baseline)
    method["practices"][1]["alphas"] = practice2_alphas
    print(f"  ✓ Extracted {len(practice2_alphas)} alphas")
    for alpha in practice2_alphas:
        print(f"    - {alpha['name']}: {len(alpha['states'])} states")
    
    # Save
    print("\n[4/5] Saving JSON...")
    with open(json_path, "w") as f:
        json.dump(method, f, indent=2)
    
    print("\n[5/5] Summary:")
    print(f"  File: {json_path.name}")
    print(f"  Size: {json_path.stat().st_size / 1024:.1f} KB")
    print(f"  Practice 1: {len(practice1_alphas)} alphas with states and checklists")
    print(f"  Practice 2: {len(practice2_alphas)} alphas with states and checklists")
    
    print("\n✅ Alpha extraction complete!")

if __name__ == "__main__":
    main()
