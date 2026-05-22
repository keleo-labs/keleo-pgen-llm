import json, re
from pathlib import Path

method = json.load(open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json"))
index = json.load(open("practices/red-hat-ansible-automation-platform/cross-reference-index.json"))

def extract_acts(path):
    acts = []
    for sec in re.split(r'\n#### Activity: ', path.read_text())[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join([l.strip() for l in sec.split('\n')[1:4] if l.strip() and not l.startswith('**')])[:500]
        focus_m = re.search(r'\*\*Focus:\*\*\s*(.+)', sec)
        space_m = re.search(r'\*\*Activity Space:\*\*\s*(.+)', sec)
        acts.append({"name": name, "description": desc if desc else name,
                    "focusName": focus_m.group(1).strip() if focus_m else "Solution",
                    "activitySpaceName": space_m.group(1).strip() if space_m else "Architect and Build the Foundation",
                    "contributesTo": [], "worksOn": [], "requiredCompetencies": ["Engineering"],
                    "recommendedCompetencyLevels": [{"competencyName": "Engineering", "competencyLevelName": "Applies"}],
                    "involves": []})
    return acts

def extract_pers(path):
    pers = []
    for sec in re.split(r'\n### Persona: ', path.read_text())[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join([l.strip() for l in sec.split('\n')[1:6] if l.strip() and not l.startswith('**')])[:300]
        pers.append({"name": name, "description": desc if desc else name, "competencies": []})
    return pers

def extract_groups(path, pk):
    groups = []
    for sec in re.split(r'\n### Persona Group: ', path.read_text())[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join([l.strip() for l in sec.split('\n')[1:6] if l.strip() and not l.startswith('**')])[:300]
        pnames = index[pk].get("personaGroups", {}).get(name, [])
        groups.append({"name": name, "description": desc if desc else name, "personaNames": pnames})
    return groups

def extract_pats(path):
    pats = []
    for sec in re.split(r'\n### Pattern: ', path.read_text())[1:]:
        name = sec.split('\n')[0].strip()
        desc = ' '.join([l.strip() for l in sec.split('\n')[1:6] if l.strip() and not l.startswith('**') and not l.startswith('#')])[:300]
        views = []
        for i, v in enumerate(re.split(r'\n#### (?:Phase|View): ', sec)[1:]):
            vn = v.split('\n')[0].strip()
            vd = ' '.join([l.strip() for l in v.split('\n')[1:4] if l.strip() and not l.startswith('**')])[:200]
            views.append({"name": vn, "description": vd if vd else vn, "seq": i, "alphaStates": [], "activitySpaces": [], "activities": []})
        pats.append({"name": name, "description": desc if desc else name, "patternViews": views})
    return pats

print("Final extraction...")
p1 = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-1")
p2 = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-2")

method["practices"][0]["activities"] = extract_acts(p1 / "05-activities-roles.md")
method["practices"][0]["personas"] = extract_pers(p1 / "05-activities-roles.md")
method["practices"][0]["personaGroups"] = extract_groups(p1 / "05-activities-roles.md", "practice1")
method["practices"][0]["patterns"] = extract_pats(p1 / "06-patterns.md")

method["practices"][1]["activities"] = extract_acts(p2 / "05-activities-roles.md")
method["practices"][1]["personas"] = extract_pers(p2 / "05-activities-roles.md")
method["practices"][1]["personaGroups"] = extract_groups(p2 / "05-activities-roles.md", "practice2")
method["practices"][1]["patterns"] = extract_pats(p2 / "06-patterns.md")

with open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json", "w") as f:
    json.dump(method, f, indent=2)

p = Path("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json")
print(f"\n✅ EXTRACTION COMPLETE! {p.stat().st_size / 1024:.1f} KB")
m = method
print(f"\nPractice 1: {m['practices'][0]['name']}")
print(f"  {len(m['practices'][0]['alphas'])} alphas, {len(m['practices'][0]['workProducts'])} work products")
print(f"  {len(m['practices'][0]['activities'])} activities, {len(m['practices'][0]['personas'])} personas")
print(f"  {len(m['practices'][0]['personaGroups'])} persona groups, {len(m['practices'][0]['patterns'])} patterns")
print(f"  {len(m['practices'][0]['citations'])} citations")

print(f"\nPractice 2: {m['practices'][1]['name']}")
print(f"  {len(m['practices'][1]['alphas'])} alphas, {len(m['practices'][1]['workProducts'])} work products")
print(f"  {len(m['practices'][1]['activities'])} activities, {len(m['practices'][1]['personas'])} personas")
print(f"  {len(m['practices'][1]['personaGroups'])} persona groups, {len(m['practices'][1]['patterns'])} patterns")
print(f"  {len(m['practices'][1]['citations'])} citations")

print("\n🎉 RED HAT ANSIBLE AUTOMATION PLATFORM METHOD - PHASE 2 COMPLETE!")
