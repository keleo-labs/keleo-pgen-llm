#!/usr/bin/env python3
"""
Complete extraction of all remaining content
Handles all alpha formats, work products, activities, patterns
"""
import json
import re
from pathlib import Path
from typing import Dict, List

def load_resources():
    with open("practices/red-hat-ansible-automation-platform/cross-reference-index.json") as f:
        index = json.load(f)
    with open("deps/platform-adoption-kernel.json") as f:
        baseline = json.load(f)
    with open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json") as f:
        method = json.load(f)
    return index, baseline, method

def extract_remaining_practice1_alphas(modules_dir: Path, baseline: Dict) -> List[Dict]:
    """Extract Security Posture and Disaster Recovery Capability"""
    alphas = []
    baseline_alphas = {alpha["name"]: alpha for alpha in baseline.get("alphas", [])}
    
    content = (modules_dir / "03a-alphas-solution.md").read_text()
    
    # Find Security Posture (uses ## Alpha 7: format)
    sp_match = re.search(r'## Alpha 7: Security Posture(.+?)(?=\n## Alpha|$)', content, re.DOTALL)
    if sp_match:
        alpha = parse_numbered_alpha(sp_match.group(1), "Security Posture", "Solution")
        if alpha:
            alphas.append(alpha)
    
    # Find Disaster Recovery Capability
    dr_match = re.search(r'## Alpha 8: Disaster Recovery Capability(.+?)(?=\n## |$)', content, re.DOTALL)
    if dr_match:
        alpha = parse_numbered_alpha(dr_match.group(1), "Disaster Recovery Capability", "Solution")
        if alpha:
            alphas.append(alpha)
    
    return alphas

def parse_numbered_alpha(section: str, name: str, focus: str) -> Dict:
    """Parse alpha with numbered header format"""
    # Extract description (first paragraphs)
    desc_paragraphs = []
    for line in section.split('\n'):
        if line.strip() and not line.startswith('**') and not line.startswith('#') and not line.startswith('###'):
            desc_paragraphs.append(line.strip())
            if len(desc_paragraphs) >= 2:
                break
    
    description = ' '.join(desc_paragraphs) if desc_paragraphs else name + " alpha"
    
    alpha = {
        "name": name,
        "description": description,
        "focusName": focus,
        "states": []
    }
    
    # Extract contributesTo if present
    contrib_match = re.search(r'\*\*Contributes To:\*\*\s*(.+)', section)
    if contrib_match:
        parent = contrib_match.group(1).strip()
        if parent and parent not in ["N/A", "None"]:
            alpha["contributesTo"] = parent
    
    # Extract states
    state_blocks = re.split(r'\n\*\*State \d+:', section)
    
    for i, state_block in enumerate(state_blocks[1:], 1):
        state_line_match = re.match(r'\s*(.+?)\*\*', state_block)
        if not state_line_match:
            continue
        
        state_name = state_line_match.group(1).strip()
        
        # Extract description
        desc_match = re.search(r'\*\*\s*\n\n(.+?)(?=\n\n\*\*Criteria|$)', state_block, re.DOTALL)
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
    
    return alpha

def extract_checklist_from_text(text: str) -> List[Dict]:
    """Extract numbered checklist items"""
    checklist = []
    
    criteria_match = re.search(r'\*\*Criteria.+?:\*\*(.+?)(?=\n\*\*(?![\w\s]*:)|###|$)', text, re.DOTALL)
    if not criteria_match:
        return checklist
    
    criteria_text = criteria_match.group(1)
    items = re.findall(r'\n\d+\.\s+\*\*(.+?)\*\*:?\s*(.+?)(?=\n\d+\.|$)', criteria_text, re.DOTALL)
    
    for seq, (name, desc) in enumerate(items, 1):
        clean_desc = ' '.join(desc.split())
        checklist.append({
            "name": name.strip(),
            "description": clean_desc.strip(),
            "seq": seq
        })
    
    return checklist

def main():
    print("\n" + "="*70)
    print("COMPLETE EXTRACTION - CONTINUING TO 100%")
    print("="*70)
    
    index, baseline, method = load_resources()
    
    # Extract remaining Practice 1 alphas
    print("\n[Step 1] Extracting remaining Practice 1 alphas...")
    modules_dir = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-1")
    remaining_alphas = extract_remaining_practice1_alphas(modules_dir, baseline)
    
    # Add to existing alphas
    method["practices"][0]["alphas"].extend(remaining_alphas)
    print(f"  ✓ Added {len(remaining_alphas)} alphas")
    for alpha in remaining_alphas:
        print(f"    - {alpha['name']}: {len(alpha['states'])} states, {sum(len(s['checklist']) for s in alpha['states'])} checklist items")
    
    # Save progress
    json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
    with open(json_path, "w") as f:
        json.dump(method, f, indent=2)
    
    print(f"\n✅ Practice 1 alphas: {len(method['practices'][0]['alphas'])}/9 complete")
    print(f"   File size: {json_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
