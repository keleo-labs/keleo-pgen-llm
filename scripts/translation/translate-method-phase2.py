#!/usr/bin/env python3
"""
Phase 2: Modular JSON Translation for Red Hat Ansible Automation Platform Method

This script implements the Phase 2 workflow defined in prompts/phase-2-modular.md.
It builds complete, schema-compliant Method JSON from Phase 1 modular outputs.

WARNING: This is a SIMPLIFIED translation script that creates a valid JSON structure
but does NOT include the full content from every module. A complete Phase 2 translation
requires manual review of all modules to extract:
- Full alpha state checklists
- Complete work product level of detail descriptions
- Activity technique narratives
- Pattern view narratives
- All other detailed content

This script provides the FRAMEWORK. Complete content extraction requires either:
1. Manual Phase 2 execution reading each module carefully
2. Sophisticated markdown parsing with content extraction logic

Usage:
    python3 translate-method-phase2.py

Output:
    practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json
"""

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent
PRACTICES_DIR = PROJECT_ROOT / "practices" / "red-hat-ansible-automation-platform"
REPORT_ELEMENTS_DIR = PRACTICES_DIR / "report-elements"

def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_baseline():
    """Load baseline kernel."""
    return load_json(PROJECT_ROOT / "deps" / "platform-adoption-kernel.json")

def load_cross_ref_index():
    """Load cross-reference index."""
    return load_json(PRACTICES_DIR / "cross-reference-index.json")

def get_baseline_alpha(baseline, alpha_name):
    """Get baseline alpha by name."""
    for alpha in baseline["alphas"]:
        if alpha["name"] == alpha_name:
            return alpha
    return None

def build_practice_1_citations(index):
    """Build citations array for Practice 1 from index."""
    citations = []
    for cit in index["practice1"]["citations"]:
        citation = {
            "name": cit["title"],
            "description": f"Authoritative source for {cit['title']}",
            "authors": cit["authors"],
            "date": cit["date"],
            "source": cit["title"]
        }
        # Add URL if we have one (Red Hat docs)
        if "Red Hat" in cit["title"] and "2.6" in cit["title"]:
            # Construct Red Hat doc URL
            guide_name = cit["title"].split(":")[1].strip().lower().replace(" ", "_")
            citation["url"] = f"https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/{guide_name}/"
        citations.append(citation)
    return citations

def build_practice_1_alphas(baseline, index):
    """Build alphas array for Practice 1."""
    alphas = []

    for alpha_name, alpha_info in index["practice1"]["alphas"].items():
        alpha = {
            "name": alpha_name,
            "description": f"{alpha_name} alpha for AAP platform",
            "focusName": alpha_info["focus"],
            "states": []
        }

        # Handle redeclarations - copy from baseline
        if alpha_info["type"] == "Redeclaration":
            baseline_alpha = get_baseline_alpha(baseline, alpha_name)
            if baseline_alpha:
                alpha["description"] = baseline_alpha["description"]
                # Copy states from baseline
                for state in baseline_alpha["states"]:
                    alpha["states"].append({
                        "name": state["name"],
                        "description": state["description"],
                        "seq": state["seq"],
                        "checklist": []  # Would need to extract from modules
                    })
        else:
            # New/specialized alpha - build states from index
            for state_name in alpha_info["states"]:
                alpha["states"].append({
                    "name": state_name,
                    "description": f"{state_name} state",
                    "seq": alpha_info["states"].index(state_name) + 1,
                    "checklist": []
                })

            # Add contributesTo for specialized alphas
            if alpha_info.get("contributesTo"):
                alpha["contributesTo"] = alpha_info["contributesTo"]

        alphas.append(alpha)

    return alphas

def build_practice_1(baseline, index):
    """Build complete Practice 1 JSON."""
    practice = {
        "name": index["practice1"]["name"],
        "description": "This practice guides platform administrators through the complete lifecycle of establishing, operating, and evolving Red Hat Ansible Automation Platform infrastructure.",
        "baselinePracticeName": "Platform Adoption Essentials",
        "tags": {
            "domainTags": ["Infrastructure Platforms", "Security", "Site Reliability Engineering"],
            "lifecycleTags": ["Planning", "Implementation", "Operations", "Optimization"],
            "organizationalTags": ["Platform Teams", "Enterprise"]
        },
        "authors": ["Generated by Claude Code from Red Hat Ansible Automation Platform 2.6"],
        "createdAt": "2026-05-19",
        "updatedAt": "2026-05-19",
        "version": "1.0",
        "keywords": ["ansible automation platform", "platform administration", "infrastructure topology"],
        "citations": build_practice_1_citations(index),
        "alphas": build_practice_1_alphas(baseline, index),
        "alphaInstances": [],
        "workProducts": [],
        "activities": [],
        "personas": [],
        "personaGroups": [],
        "patterns": []
    }

    # TODO: Add workProducts, activities, personas, personaGroups, patterns
    # This requires parsing the actual module files

    return practice

def build_practice_2(baseline, index):
    """Build complete Practice 2 JSON."""
    practice = {
        "name": index["practice2"]["name"],
        "description": "This practice enables automation engineers to design, develop, test, package, sign, and deliver high-quality automation content using modern software engineering practices.",
        "baselinePracticeName": "Platform Adoption Essentials",
        "tags": {
            "domainTags": ["Automation Engineering", "DevOps", "Software Development"],
            "lifecycleTags": ["Design", "Implementation", "Testing", "Deployment"],
            "organizationalTags": ["Development Teams", "DevOps Teams"]
        },
        "authors": ["Generated by Claude Code from Red Hat Ansible Automation Platform 2.6"],
        "createdAt": "2026-05-20",
        "updatedAt": "2026-05-20",
        "version": "1.0",
        "keywords": ["ansible playbooks", "ansible collections", "automation content development"],
        "citations": [],  # TODO: Build from index
        "alphas": [],  # TODO: Build from index
        "alphaInstances": [],
        "workProducts": [],
        "activities": [],
        "personas": [],
        "personaGroups": [],
        "patterns": []
    }

    return practice

def build_method(baseline, index):
    """Build complete Method JSON."""
    method = {
        "name": index["method"]["name"],
        "description": "A comprehensive enterprise automation methodology enabling organizations to deploy, operate, and govern a scalable automation platform while simultaneously building and delivering high-quality automation content through modern DevOps practices.",
        "baselinePracticeName": index["method"]["baselinePracticeName"],
        "practices": [
            build_practice_1(baseline, index),
            build_practice_2(baseline, index)
        ]
    }

    return method

def main():
    print("Phase 2: Modular JSON Translation")
    print("=" * 60)

    print("\n1. Loading resources...")
    baseline = load_baseline()
    index = load_cross_ref_index()
    print(f"   ✓ Loaded baseline ({len(baseline['alphas'])} alphas)")
    print(f"   ✓ Loaded cross-reference index")

    print("\n2. Building Method JSON...")
    method = build_method(baseline, index)
    print(f"   ✓ Method: {method['name']}")
    print(f"   ✓ Practice 1: {method['practices'][0]['name']}")
    print(f"   ✓ Practice 2: {method['practices'][1]['name']}")

    print("\n3. Writing output...")
    output_path = PRACTICES_DIR / "red-hat-ansible-automation-platform.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(method, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Written to: {output_path}")

    print("\n" + "=" * 60)
    print("WARNING: This is a PARTIAL translation!")
    print("The JSON structure is valid but missing detailed content:")
    print("- Alpha state checklists")
    print("- Work product definitions")
    print("- Activity narratives")
    print("- Pattern views")
    print("\nComplete Phase 2 requires manual extraction from all modules.")
    print("=" * 60)

if __name__ == "__main__":
    main()
