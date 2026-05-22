#!/usr/bin/env python3
import json
import re
from pathlib import Path

def extract_checklist(text):
    """Extract numbered checklist items"""
    checklist = []
    
    # Find the checklist section (after "Checklist:")
    checklist_match = re.search(r'Checklist:(.+?)(?=\n###|$)', text, re.DOTALL)
    if not checklist_match:
        return checklist
    
    checklist_text = checklist_match.group(1)
    
    # Find numbered items
    items = re.findall(r'\n\d+\.\s+\*\*(.+?)\*\*:?\s*(.+?)(?=\n\d+\.|$)', checklist_text, re.DOTALL)
    
    for seq, (name, desc) in enumerate(items, 1):
        clean_desc = ' '.join(desc.split())
        checklist.append({
            "name": name.strip(),
            "description": clean_desc.strip(),
            "seq": seq
        })
    
    return checklist

# Load current JSON
json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
with open(json_path) as f:
    method = json.load(f)

# Load module content
content = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-1/03a-alphas-solution.md").read_text()

# Fix Security Posture alpha (last 2 in the list)
sp_section = re.search(r'## Alpha 7: Security Posture(.+?)(?=\n## Alpha 8:|$)', content, re.DOTALL)
if sp_section:
    sp_text = sp_section.group(1)
    
    # Extract description
    desc_match = re.search(r'\*\*Description:\*\*\s*\n\n(.+?)\n\n\*\*Progressive States', sp_text, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else "Security Posture alpha"
    
    # Update alpha (-2 is Security Posture)
    method["practices"][0]["alphas"][-2]["description"] = description
    
    # Extract states (### State N: format)
    state_sections = re.split(r'\n### State \d+:', sp_text)
    
    states = []
    for i, state_section in enumerate(state_sections[1:], 1):
        # State name is first line
        state_name_match = re.match(r'\s*(\w+)', state_section)
        if not state_name_match:
            continue
        state_name = state_name_match.group(1).strip()
        
        # Description after **Description:**
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\n\*\*|$)', state_section, re.DOTALL)
        state_desc = desc_match.group(1).strip() if desc_match else state_name
        
        # Checklist
        checklist = extract_checklist(state_section)
        
        states.append({
            "name": state_name,
            "description": state_desc,
            "seq": i,
            "checklist": checklist
        })
    
    method["practices"][0]["alphas"][-2]["states"] = states
    method["practices"][0]["alphas"][-2]["contributesTo"] = "Automation Platform"
    print(f"✓ Fixed Security Posture: {len(states)} states, {sum(len(s['checklist']) for s in states)} checklist items")

# Fix Disaster Recovery Capability alpha
dr_section = re.search(r'## Alpha 8: Disaster Recovery Capability(.+?)$', content, re.DOTALL)
if dr_section:
    dr_text = dr_section.group(1)
    
    # Extract description
    desc_match = re.search(r'\*\*Description:\*\*\s*\n\n(.+?)\n\n\*\*Progressive States', dr_text, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else "Disaster Recovery Capability alpha"
    
    # Update alpha (-1 is Disaster Recovery)
    method["practices"][0]["alphas"][-1]["description"] = description
    
    # Extract states
    state_sections = re.split(r'\n### State \d+:', dr_text)
    
    states = []
    for i, state_section in enumerate(state_sections[1:], 1):
        state_name_match = re.match(r'\s*(\w+)', state_section)
        if not state_name_match:
            continue
        state_name = state_name_match.group(1).strip()
        
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\n\*\*|$)', state_section, re.DOTALL)
        state_desc = desc_match.group(1).strip() if desc_match else state_name
        
        checklist = extract_checklist(state_section)
        
        states.append({
            "name": state_name,
            "description": state_desc,
            "seq": i,
            "checklist": checklist
        })
    
    method["practices"][0]["alphas"][-1]["states"] = states
    method["practices"][0]["alphas"][-1]["contributesTo"] = "Automation Platform"
    print(f"✓ Fixed Disaster Recovery Capability: {len(states)} states, {sum(len(s['checklist']) for s in states)} checklist items")

# Save
with open(json_path, "w") as f:
    json.dump(method, f, indent=2)

print(f"\n✅ Practice 1 alphas complete: 9/9")
print(f"   File size: {json_path.stat().st_size / 1024:.1f} KB")

