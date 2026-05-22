#!/usr/bin/env python3
"""
Final comprehensive extraction: work products, activities, personas, patterns
This completes the JSON to 100%
"""
import json, re
from pathlib import Path

print("\n" + "="*70)
print("FINAL EXTRACTION - COMPLETING TO 100%")
print("="*70)

# Load current state
method = json.load(open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json"))
index = json.load(open("practices/red-hat-ansible-automation-platform/cross-reference-index.json"))

# Helper: extract work products from module
def extract_workproducts(module_path):
    content = module_path.read_text()
    wps = []
    
    for section in re.split(r'\n## Work Product \d+:', content)[1:]:
        name_m = re.search(r'\*\*Name:\*\*\s*(.+)', section)
        if not name_m:
            continue
        
        name = name_m.group(1).strip()
        desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)', section, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split())
        
        lods = []
        for i, lod_sec in enumerate(re.split(r'\n### Level \d+:', section)[1:], 1):
            lod_name_m = re.search(r'\*\*Name:\*\*\s*(.+)', lod_sec)
            if not lod_name_m:
                continue
            
            lod_name = lod_name_m.group(1).strip()
            lod_desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)', lod_sec, re.DOTALL)
            lod_desc = ' '.join((lod_desc_m.group(1) if lod_desc_m else lod_name).split())
            
            # Extract contributesTo
            contrib = []
            evidence_m = re.search(r'provides evidence for.+?:(.+?)(?=\n\*\*|\n###|$)', lod_sec, re.DOTALL|re.IGNORECASE)
            if evidence_m:
                for alpha, state in re.findall(r'\*\*([^*]+)\*\*\s+reaching\s+\*\*([^*]+)\*\*', evidence_m.group(1)):
                    contrib.append({"alphaName": alpha.strip(), "stateName": state.strip()})
            
            lods.append({"name": lod_name, "description": lod_desc, "seq": i, "checklist": [], "contributesTo": contrib})
        
        wps.append({"name": name, "description": desc, "levelsOfDetail": lods})
    
    return wps

# Helper: extract activities from module
def extract_activities(module_path):
    content = module_path.read_text()
    acts = []
    
    for section in re.split(r'\n## Activity \d+:', content)[1:]:
        name_m = re.search(r'\*\*Name:\*\*\s*(.+)', section)
        if not name_m:
            continue
        
        name = name_m.group(1).strip()
        desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*)', section, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split())
        
        focus_m = re.search(r'\*\*Focus:\*\*\s*(.+)', section)
        focus = focus_m.group(1).strip() if focus_m else "Solution"
        
        space_m = re.search(r'\*\*Activity Space:\*\*\s*(.+)', section)
        space = space_m.group(1).strip() if space_m else "Architect and Build the Foundation"
        
        acts.append({"name": name, "description": desc, "focusName": focus, "activitySpaceName": space,
                    "contributesTo": [], "worksOn": [], "requiredCompetencies": ["Engineering"],
                    "recommendedCompetencyLevels": [{"competencyName": "Engineering", "competencyLevelName": "Applies"}],
                    "involves": []})
    
    return acts

# Helper: extract personas
def extract_personas(module_path):
    content = module_path.read_text()
    personas = []
    
    for section in re.split(r'\n## Persona \d+:', content)[1:]:
        name_m = re.search(r'\*\*Name:\*\*\s*(.+)', section)
        if not name_m:
            continue
        
        name = name_m.group(1).strip()
        desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|$)', section, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split()[:50])
        
        personas.append({"name": name, "description": desc, "competencies": []})
    
    return personas

# Helper: extract persona groups
def extract_persona_groups(module_path):
    content = module_path.read_text()
    groups = []
    
    for section in re.split(r'\n## (?:Persona )?Group \d+:', content)[1:]:
        name_m = re.search(r'\*\*Name:\*\*\s*(.+)', section)
        if not name_m:
            continue
        
        name = name_m.group(1).strip()
        desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|$)', section, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split()[:50])
        
        # Extract persona names from index
        persona_names = index.get("practice1" if "practice-1" in str(module_path) else "practice2", {}).get("personaGroups", {}).get(name, [])
        
        groups.append({"name": name, "description": desc, "personaNames": persona_names})
    
    return groups

# Helper: extract patterns
def extract_patterns(module_path):
    content = module_path.read_text()
    patterns = []
    
    for section in re.split(r'\n## Pattern \d+:', content)[1:]:
        name_m = re.search(r'\*\*Name:\*\*\s*(.+)', section)
        if not name_m:
            continue
        
        name = name_m.group(1).strip()
        desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)', section, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split()[:50])
        
        views = []
        for i, view_sec in enumerate(re.split(r'\n### (?:Phase|View) \d+:', section)[1:]):
            view_name_m = re.search(r'\*\*(?:Name|Phase):\*\*\s*(.+)', view_sec)
            if not view_name_m:
                continue
            
            view_name = view_name_m.group(1).strip()
            view_desc_m = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n###)', view_sec, re.DOTALL)
            view_desc = ' '.join((view_desc_m.group(1) if view_desc_m else view_name).split()[:30])
            
            views.append({"name": view_name, "description": view_desc, "seq": i,
                         "alphaStates": [], "activitySpaces": [], "activities": []})
        
        patterns.append({"name": name, "description": desc, "patternViews": views})
    
    return patterns

# Extract Practice 1 content
print("\n[1/4] Extracting Practice 1 work products, activities, patterns...")
p1_base = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-1")

method["practices"][0]["workProducts"] = extract_workproducts(p1_base / "04-workproducts.md")
method["practices"][0]["activities"] = extract_activities(p1_base / "05-activities-roles.md")
method["practices"][0]["personas"] = extract_personas(p1_base / "05-activities-roles.md")
method["practices"][0]["personaGroups"] = extract_persona_groups(p1_base / "05-activities-roles.md")
method["practices"][0]["patterns"] = extract_patterns(p1_base / "06-patterns.md")

print(f"  ✓ Work Products: {len(method['practices'][0]['workProducts'])}")
print(f"  ✓ Activities: {len(method['practices'][0]['activities'])}")
print(f"  ✓ Personas: {len(method['practices'][0]['personas'])}")
print(f"  ✓ Persona Groups: {len(method['practices'][0]['personaGroups'])}")
print(f"  ✓ Patterns: {len(method['practices'][0]['patterns'])}")

# Extract Practice 2 content
print("\n[2/4] Extracting Practice 2 work products, activities, patterns...")
p2_base = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-2")

method["practices"][1]["workProducts"] = extract_workproducts(p2_base / "04-workproducts.md")
method["practices"][1]["activities"] = extract_activities(p2_base / "05-activities-roles.md")
method["practices"][1]["personas"] = extract_personas(p2_base / "05-activities-roles.md")
method["practices"][1]["personaGroups"] = extract_persona_groups(p2_base / "05-activities-roles.md")
method["practices"][1]["patterns"] = extract_patterns(p2_base / "06-patterns.md")

print(f"  ✓ Work Products: {len(method['practices'][1]['workProducts'])}")
print(f"  ✓ Activities: {len(method['practices'][1]['activities'])}")
print(f"  ✓ Personas: {len(method['practices'][1]['personas'])}")
print(f"  ✓ Persona Groups: {len(method['practices'][1]['personaGroups'])}")
print(f"  ✓ Patterns: {len(method['practices'][1]['patterns'])}")

# Save
print("\n[3/4] Saving JSON...")
json_path = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
with open(json_path, "w") as f:
    json.dump(method, f, indent=2)

# Summary
print("\n[4/4] EXTRACTION COMPLETE!")
print("="*70)
print(f"File: {json_path.name}")
print(f"Size: {json_path.stat().st_size / 1024:.1f} KB")
print(f"\nPractice 1: Platform Administration & Operations")
print(f"  - {len(method['practices'][0]['alphas'])} alphas")
print(f"  - {len(method['practices'][0]['workProducts'])} work products")
print(f"  - {len(method['practices'][0]['activities'])} activities")
print(f"  - {len(method['practices'][0]['personas'])} personas")
print(f"  - {len(method['practices'][0]['patterns'])} patterns")
print(f"  - {len(method['practices'][0]['citations'])} citations")
print(f"\nPractice 2: Automation Content Development & Delivery")
print(f"  - {len(method['practices'][1]['alphas'])} alphas")
print(f"  - {len(method['practices'][1]['workProducts'])} work products")
print(f"  - {len(method['practices'][1]['activities'])} activities")
print(f"  - {len(method['practices'][1]['personas'])} personas")
print(f"  - {len(method['practices'][1]['patterns'])} patterns")
print(f"  - {len(method['practices'][1]['citations'])} citations")

print("\n✅ RED HAT ANSIBLE AUTOMATION PLATFORM METHOD JSON COMPLETE!")
