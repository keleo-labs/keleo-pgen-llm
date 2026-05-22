import json, re
from pathlib import Path

baseline = json.load(open("deps/platform-adoption-kernel.json"))
method = json.load(open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json"))
content = Path("practices/red-hat-ansible-automation-platform/report-elements/practice-2/03-alphas.md").read_text()

alphas = []
baseline_alphas = {a["name"]: a for a in baseline.get("alphas", [])}

for section in re.split(r'\n### Alpha: ', content)[1:]:
    name = section.split('\n')[0].strip()
    is_redec = "Redeclaration" in section[:300]
    
    desc = ' '.join([l.strip() for l in section.split('\n')[3:6] if l.strip() and not l.startswith('**')])
    
    alpha = {"name": name, "focusName": "Endeavor" if "Endeavor" in section[:200] else "Solution", "states": []}
    
    if is_redec and name in baseline_alphas:
        alpha["description"] = baseline_alphas[name]["description"]
        for bs in baseline_alphas[name]["states"]:
            alpha["states"].append({"name": bs["name"], "description": bs["description"], "seq": bs["seq"], "checklist": []})
    else:
        alpha["description"] = desc
        contrib = re.search(r'\*\*Contributes To:\*\*\s*(.+)', section)
        if contrib and contrib.group(1).strip() not in ["N/A", "None"]:
            alpha["contributesTo"] = contrib.group(1).strip()
        
        for i, sb in enumerate(re.split(r'\n\*\*State \d+:', section)[1:], 1):
            sn = re.match(r'\s*(.+?)\*\*', sb)
            if sn:
                sd = ' '.join([l.strip() for l in sb.split('\n')[1:3] if l.strip() and not l.startswith('**')])
                alpha["states"].append({"name": sn.group(1).strip(), "description": sd, "seq": i, "checklist": []})
    
    alphas.append(alpha)

method["practices"][1]["alphas"] = alphas

with open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json", "w") as f:
    json.dump(method, f, indent=2)

print(f"✓ Extracted {len(alphas)} Practice 2 alphas")
for a in alphas:
    print(f"  - {a['name']}: {len(a['states'])} states")
print(f"File: {Path('practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json').stat().st_size / 1024:.1f} KB")
