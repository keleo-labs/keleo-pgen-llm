#!/usr/bin/env python3
import json
import re
from pathlib import Path

def build_practice_json(practice_num, practice_name, base_path):
    """Build a simplified but schema-compliant Practice JSON from modules."""
    
    practice_dir = base_path / f"practice-{practice_num}"
    
    # Read practice details
    details = (practice_dir / "01-practice-details.md").read_text()
    
    # Extract description (first paragraph after "**Description:**")
    desc_match = re.search(r'\*\*Description:\*\* (.+?)(?:\n\n|\*\*)', details, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else f"{practice_name} practice"
    
    # Extract keywords
    keywords_match = re.search(r'\*\*Keywords\*\*\n\n(.+?)\n\n', details, re.DOTALL)
    keywords = []
    if keywords_match:
        keywords = [k.strip('- ').strip() for k in keywords_match.group(1).split('\n') if k.strip()]
    
    # Build basic practice structure
    practice = {
        "name": practice_name,
        "description": description,
        "baselinePracticeName": "Platform Adoption Essentials",
        "domainTags": keywords[:5] if keywords else [],
        "alphas": [],
        "workProducts": [],
        "activities": [],
        "personas": [],
        "patterns": []
    }
    
    return practice

# Build all 5 practices
practices_data = [
    (1, "AI Platform Management", "practice-1-platform-management"),
    (2, "Model Lifecycle Operations", "practice-2-model-lifecycle"),
    (3, "Model Development and Customization", "practice-3-model-development"),
    (4, "Production AI Inference", "practice-4-inference"),
    (5, "Agentic AI Development", "practice-5-agentic-ai"),
]

base = Path("practices/red-hat-ai-3/report-elements")

for num, name, dirname in practices_data:
    practice_json = build_practice_json(num, name, base)
    
    # Write to file
    output_path = Path(f"practices/red-hat-ai-3/{dirname}.json")
    with open(output_path, 'w') as f:
        json.dump(practice_json, f, indent=2)
    
    print(f"✓ Created {output_path.name}")

print("\n✓ All practice JSON files created")
