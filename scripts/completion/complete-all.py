import json, re
from pathlib import Path

method = json.load(open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json"))
index = json.load(open("practices/red-hat-ansible-automation-platform/cross-reference-index.json"))

# Extract work products
def extract_wps(path):
    content = path.read_text()
    wps = []
    for sec in re.split(r'\n### Work Product: ', content)[1:]:
        name = sec.split('\n')[0].strip()
        desc_m = re.search(r'^\n(.+?)\n\n####', sec, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split())
        lods = []
        for i, lod_sec in enumerate(re.split(r'\n\*\*Level \d+:', sec)[1:], 1):
            lod_m = re.match(r'\s*(.+?)\*\*', lod_sec)
            if lod_m:
                lods.append({"name": lod_m.group(1).strip(), "description": name + " level", "seq": i, "checklist": [], "contributesTo": []})
        wps.append({"name": name, "description": desc, "levelsOfDetail": lods})
    return wps

# Extract activities
def extract_acts(path):
    content = path.read_text()
    acts = []
    for sec in re.split(r'\n### Activity: ', content)[1:]:
        name = sec.split('\n')[0].strip()
        desc_m = re.search(r'^\n(.+?)\n\n\*\*', sec, re.DOTALL)
        desc = ' '.join((desc_m.group(1) if desc_m else name).split())
        focus_m = re.search(r'\*\*Focus:\*\*\s*(.+)', sec)
        space_m = re.search(r'\*\*Activity Space:\*\*\s*(.+)', sec)
        acts.append({"name": name, "description": desc,
                    "focusName": focus_m.group(1).strip() if focus_m else "Solution",
                    "activitySpaceName": space_m.group(1).strip() if space_m else "Architect and Build the Foundation",
                    "contributesTo": [], "worksOn": [], "requiredCompetencies": ["Engineering"],
                    "recommendedCompetencyLevels": [{"competencyName": "Engineering", "competencyLevelName": "Applies"}],
                    "involves": []})
    return acts

# Extract personas
def extract_pers(path):
    content = path.read_text()
    pers = []
    for sec in re.split(r'\n### Persona: ', content)[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join(sec.split('\n')[1:5])[:200]
        pers.append({"name": name, "description": desc, "competencies": []})
    return pers

# Extract persona groups  
def extract_groups(path, practice_key):
    content = path.read_text()
    groups = []
    for sec in re.split(r'\n### (?:Persona )?Group: ', content)[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join(sec.split('\n')[1:5])[:200]
        pnames = index[practice_key].get("personaGroups", {}).get(name, [])
        groups.append({"name": name, "description": desc, "personaNames": pnames})
    return groups

# Extract patterns
def extract_pats(path):
    content = path.read_text()
    pats = []
    for sec in re.split(r'\n## Pattern: ', content)[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join(sec.split('\n')[1:5])[:200]
        views = []
        for i, v_sec in enumerate(re.split(r'\n### (?:Phase|View): ', sec)[1:]):
            v_name = v_sec.split('\n')[0].strip()
            v_desc = ' '.join(v_sec.split('\n')[1:3])[:100]
            views.append({"name": v_name, "description": v_desc, "seq": i, "alphaStates": [], "activitySpaces": [], "activities": []})
        pats.append({"name": name, "description": desc, "patternViews": views})
    return pats

print("Extracting all remaining content...")
p1 = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-1")
p2 = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-2")

method["practices"][0]["workProducts"] = extract_wps(p1 / "04-workproducts.md")
method["practices"][0]["activities"] = extract_acts(p1 / "05-activities-roles.md")
method["practices"][0]["personas"] = extract_pers(p1 / "05-activities-roles.md")
method["practices"][0]["personaGroups"] = extract_groups(p1 / "05-activities-roles.md", "practice1")
method["practices"][0]["patterns"] = extract_pats(p1 / "06-patterns.md")

method["practices"][1]["workProducts"] = extract_wps(p2 / "04-workproducts.md")
method["practices"][1]["activities"] = extract_acts(p2 / "05-activities-roles.md")
method["practices"][1]["personas"] = extract_pers(p2 / "05-activities-roles.md")
method["practices"][1]["personaGroups"] = extract_groups(p2 / "05-activities-roles.md", "practice2")
method["practices"][1]["patterns"] = extract_pats(p2 / "06-patterns.md")

with open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json", "w") as f:
    json.dump(method, f, indent=2)

p = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
print(f"\n✅ COMPLETE! {p.stat().st_size / 1024:.1f} KB")
print(f"P1: {len(method['practices'][0]['alphas'])} alphas, {len(method['practices'][0]['workProducts'])} WPs, {len(method['practices'][0]['activities'])} acts, {len(method['practices'][0]['patterns'])} patterns")
print(f"P2: {len(method['practices'][1]['alphas'])} alphas, {len(method['practices'][1]['workProducts'])} WPs, {len(method['practices'][1]['activities'])} acts, {len(method['practices'][1]['patterns'])} patterns")
