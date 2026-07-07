#!/usr/bin/env python3
"""
Refactor practices to use the new simplified Partner Ecosystem Baseline.

Updates:
- Focus names: Endeavor → Engagement, Solution → Go-to-Market
- Alpha references: Maps old 11 alphas to new 5 alphas
- Competency references: Maps old 8 competencies to new 5
- Activity space contributions: Maps to new baseline states
"""

import json
import sys
from pathlib import Path

# Mapping old baseline alphas to new baseline alphas
ALPHA_MAPPING = {
    "Partner Opportunity": "Partner Value",
    "Partner Revenue Model": "Partner Value",
    "Partner Performance": "Partner Value",
    "Partner Relationship": "Partner Relationship",  # unchanged
    "Partner Program": None,  # removed - absorbed into governance/relationship
    "Partner Enablement": "Partner Capability",
    "Partner Solution": "Partner Capability",
    "Partner Certification": "Partner Capability",
    "Partner Capability": "Partner Capability",  # unchanged
    "Partner Governance": "Partner Governance",  # unchanged
    # Partner Trust is new - no mapping needed
}

# Mapping old baseline competencies to new baseline
COMPETENCY_MAPPING = {
    "Partner Strategic Alignment": "Partner Strategic Alignment",  # unchanged
    "Ecosystem Analysis": "Partner Value Assessment",
    "Partner Relationship Management": "Partner Relationship Management",  # unchanged
    "Partner Co-Sell Orchestration": None,  # removed - not universal
    "Partner Technical Enablement": None,  # removed - not universal
    "Partner Solutions Architecture": None,  # removed - not universal
    "Partner Operations Management": "Partner Governance",
    "Partner Conflict Resolution": "Partner Relationship Management",  # merged
}

# Mapping old baseline states to new baseline states for merged alphas
# Partner Opportunity, Partner Revenue Model, Partner Performance → Partner Value
STATE_MAPPING = {
    # Old Partner Opportunity states → Partner Value states
    ("Partner Opportunity", "Identified"): ("Partner Value", "Identified"),
    ("Partner Opportunity", "Qualified"): ("Partner Value", "Qualified"),
    ("Partner Opportunity", "Valued"): ("Partner Value", "Qualified"),
    ("Partner Opportunity", "Prioritized"): ("Partner Value", "Qualified"),
    ("Partner Opportunity", "Engaged"): ("Partner Value", "Agreed"),
    ("Partner Opportunity", "Realized"): ("Partner Value", "Delivered"),

    # Old Partner Revenue Model states → Partner Value states
    ("Partner Revenue Model", "Defined"): ("Partner Value", "Agreed"),
    ("Partner Revenue Model", "Aligned"): ("Partner Value", "Agreed"),
    ("Partner Revenue Model", "Automated"): ("Partner Value", "Delivered"),
    ("Partner Revenue Model", "Optimized"): ("Partner Value", "Optimized"),

    # Old Partner Performance states → Partner Value states
    ("Partner Performance", "Baselined"): ("Partner Value", "Agreed"),
    ("Partner Performance", "Tracked"): ("Partner Value", "Delivered"),
    ("Partner Performance", "Reviewed"): ("Partner Value", "Delivered"),
    ("Partner Performance", "Optimized"): ("Partner Value", "Optimized"),

    # Old Partner Relationship states → simplified Partner Relationship states
    ("Partner Relationship", "Registered"): ("Partner Relationship", "Initiated"),
    ("Partner Relationship", "Onboarded"): ("Partner Relationship", "Established"),
    ("Partner Relationship", "Activated"): ("Partner Relationship", "Active"),
    ("Partner Relationship", "Engaged"): ("Partner Relationship", "Active"),
    ("Partner Relationship", "Strategic"): ("Partner Relationship", "Strategic"),
    ("Partner Relationship", "Renewing"): ("Partner Relationship", "Renewing"),

    # Old Partner Capability, Partner Enablement, Partner Solution, Partner Certification → Partner Capability
    ("Partner Capability", "Assessed"): ("Partner Capability", "Assessed"),
    ("Partner Capability", "Developing"): ("Partner Capability", "Developing"),
    ("Partner Capability", "Certified"): ("Partner Capability", "Capable"),
    ("Partner Capability", "Specialized"): ("Partner Capability", "Capable"),
    ("Partner Capability", "Scaling"): ("Partner Capability", "Scaling"),

    ("Partner Enablement", "Scoped"): ("Partner Capability", "Assessed"),
    ("Partner Enablement", "Available"): ("Partner Capability", "Developing"),
    ("Partner Enablement", "Delivered"): ("Partner Capability", "Developing"),
    ("Partner Enablement", "Self-Service"): ("Partner Capability", "Capable"),

    ("Partner Solution", "Identified"): ("Partner Capability", "Assessed"),
    ("Partner Solution", "Designed"): ("Partner Capability", "Developing"),
    ("Partner Solution", "Validated"): ("Partner Capability", "Developing"),
    ("Partner Solution", "Certified"): ("Partner Capability", "Capable"),
    ("Partner Solution", "In Market"): ("Partner Capability", "Scaling"),
    ("Partner Solution", "Evolving"): ("Partner Capability", "Scaling"),

    ("Partner Certification", "Initiated"): ("Partner Capability", "Developing"),
    ("Partner Certification", "Testing"): ("Partner Capability", "Developing"),
    ("Partner Certification", "Certified"): ("Partner Capability", "Capable"),
    ("Partner Certification", "Published"): ("Partner Capability", "Capable"),
    ("Partner Certification", "Maintained"): ("Partner Capability", "Scaling"),

    # Old Partner Governance states → simplified Partner Governance states
    ("Partner Governance", "Defined"): ("Partner Governance", "Defined"),
    ("Partner Governance", "Enforced"): ("Partner Governance", "Operating"),
    ("Partner Governance", "Automated"): ("Partner Governance", "Operating"),
    ("Partner Governance", "Optimized"): ("Partner Governance", "Optimized"),

    # Additional Partner Value state mappings (for practices that reference baseline states)
    ("Partner Value", "Valued"): ("Partner Value", "Qualified"),
    ("Partner Value", "Prioritized"): ("Partner Value", "Qualified"),
    ("Partner Value", "Engaged"): ("Partner Value", "Agreed"),
    ("Partner Value", "Realized"): ("Partner Value", "Delivered"),
    ("Partner Value", "Defined"): ("Partner Value", "Agreed"),
    ("Partner Value", "Aligned"): ("Partner Value", "Agreed"),
    ("Partner Value", "Automated"): ("Partner Value", "Delivered"),
    ("Partner Value", "Baselined"): ("Partner Value", "Agreed"),
    ("Partner Value", "Tracked"): ("Partner Value", "Delivered"),
    ("Partner Value", "Reviewed"): ("Partner Value", "Delivered"),
}

# Mapping old activity spaces to new activity spaces
ACTIVITY_SPACE_MAPPING = {
    "Identify Partner Opportunities": "Identify and Qualify Partners",
    "Assess Partner Value": "Identify and Qualify Partners",
    "Track Partner Performance": "Measure Partner Value",
    "Design Revenue Models": "Measure Partner Value",
    "Onboard Partners": "Manage Partner Relationships",
    "Manage Partner Relationships": "Manage Partner Relationships",
    "Orchestrate Co-Sell Activities": "Manage Partner Relationships",
    "Develop Partner Programs": None,  # removed
    "Enable Partner Capabilities": "Build Partner Capabilities",
    "Guide Solution Development": "Build Partner Capabilities",
    "Manage Certification Processes": "Build Partner Capabilities",
    "Execute Joint Go-To-Market": "Manage Partner Relationships",
    "Govern Partner Ecosystem": "Govern Partner Ecosystem",
}

# Focus name updates
FOCUS_MAPPING = {
    "Value": "Value",
    "Endeavor": "Engagement",
    "Solution": "Go-to-Market",
}

def update_focus_names(obj):
    """Recursively update focus names in the object."""
    if isinstance(obj, dict):
        if "focusName" in obj and obj["focusName"] in FOCUS_MAPPING:
            obj["focusName"] = FOCUS_MAPPING[obj["focusName"]]
        for value in obj.values():
            update_focus_names(value)
    elif isinstance(obj, list):
        for item in obj:
            update_focus_names(item)

def update_alpha_references(obj, context=""):
    """Update alpha references to new baseline."""
    if isinstance(obj, dict):
        # Update contributesTo
        if "contributesTo" in obj and isinstance(obj["contributesTo"], str):
            old_alpha = obj["contributesTo"]
            if old_alpha in ALPHA_MAPPING:
                new_alpha = ALPHA_MAPPING[old_alpha]
                if new_alpha:
                    obj["contributesTo"] = new_alpha
                    print(f"  Updated contributesTo: {old_alpha} → {new_alpha}")
                else:
                    print(f"  WARNING: {old_alpha} removed from baseline (contributesTo)")

        # Update alphaName in relatesTo, contributesTo objects
        if "alphaName" in obj and obj["alphaName"] in ALPHA_MAPPING:
            old_alpha = obj["alphaName"]
            new_alpha = ALPHA_MAPPING[old_alpha]
            if new_alpha:
                obj["alphaName"] = new_alpha
                print(f"  Updated alphaName: {old_alpha} → {new_alpha} (in {context})")
            else:
                print(f"  WARNING: {old_alpha} removed from baseline (alphaName in {context})")

        # Recurse
        for key, value in obj.items():
            update_alpha_references(value, context=key)
    elif isinstance(obj, list):
        for item in obj:
            update_alpha_references(item, context)

def update_competency_references(obj):
    """Update competency references."""
    if isinstance(obj, dict):
        # Update requiredCompetencies array
        if "requiredCompetencies" in obj and isinstance(obj["requiredCompetencies"], list):
            updated_comps = []
            for comp in obj["requiredCompetencies"]:
                if comp in COMPETENCY_MAPPING:
                    new_comp = COMPETENCY_MAPPING[comp]
                    if new_comp and new_comp not in updated_comps:
                        updated_comps.append(new_comp)
                        if new_comp != comp:
                            print(f"  Updated competency: {comp} → {new_comp}")
                    elif not new_comp:
                        print(f"  WARNING: Competency {comp} removed from baseline")
                else:
                    # Keep practice-specific competencies
                    updated_comps.append(comp)
            obj["requiredCompetencies"] = updated_comps

        # Update competencyName field (in competency level definitions)
        if "competencyName" in obj and obj["competencyName"] in COMPETENCY_MAPPING:
            old_comp = obj["competencyName"]
            new_comp = COMPETENCY_MAPPING[old_comp]
            if new_comp:
                obj["competencyName"] = new_comp
                print(f"  Updated competencyName: {old_comp} → {new_comp}")
            elif not new_comp:
                print(f"  WARNING: Competency {old_comp} removed from baseline (competencyName)")

        # Recurse
        for value in obj.values():
            update_competency_references(value)
    elif isinstance(obj, list):
        for item in obj:
            update_competency_references(item)

def update_state_references(obj, context=""):
    """Update state references for merged alphas."""
    if isinstance(obj, dict):
        # Update stateName in contributesTo, alphaStates arrays, etc.
        if "alphaName" in obj and "stateName" in obj:
            alpha = obj["alphaName"]
            state = obj["stateName"]
            key = (alpha, state)
            if key in STATE_MAPPING:
                new_alpha, new_state = STATE_MAPPING[key]
                if new_state != state or new_alpha != alpha:
                    print(f"  Updated state: {alpha}.{state} → {new_alpha}.{new_state}")
                    obj["alphaName"] = new_alpha
                    obj["stateName"] = new_state
            # Also try mapping even if alpha name is already updated
            # (handles cases where alpha was updated but state wasn't)
            elif state in [s[1] for s in STATE_MAPPING.keys() if s[0] == alpha]:
                # Find the right mapping for this alpha/state combo
                for (old_alpha, old_state), (new_alpha, new_state) in STATE_MAPPING.items():
                    if old_alpha == alpha and old_state == state:
                        if new_state != state:
                            print(f"  Updated state: {alpha}.{state} → {new_alpha}.{new_state}")
                            obj["alphaName"] = new_alpha
                            obj["stateName"] = new_state
                        break

        # Recurse
        for key, value in obj.items():
            update_state_references(value, context=key)
    elif isinstance(obj, list):
        for item in obj:
            update_state_references(item, context)

def update_activity_space_references(obj):
    """Update activity space names."""
    if isinstance(obj, dict):
        # Update activitySpaceName
        if "activitySpaceName" in obj and obj["activitySpaceName"] in ACTIVITY_SPACE_MAPPING:
            old_name = obj["activitySpaceName"]
            new_name = ACTIVITY_SPACE_MAPPING[old_name]
            if new_name:
                obj["activitySpaceName"] = new_name
                print(f"  Updated activity space: {old_name} → {new_name}")
            else:
                print(f"  WARNING: Activity space {old_name} removed from baseline")

        # Recurse
        for value in obj.values():
            update_activity_space_references(value)
    elif isinstance(obj, list):
        for item in obj:
            update_activity_space_references(item)

def refactor_practice(file_path):
    """Refactor a single practice file."""
    print(f"\nRefactoring {file_path}...")

    with open(file_path, 'r') as f:
        practice = json.load(f)

    # Update focus names
    print("  Updating focus names...")
    update_focus_names(practice)

    # Update alpha references
    print("  Updating alpha references...")
    update_alpha_references(practice)

    # Update competency references
    print("  Updating competency references...")
    update_competency_references(practice)

    # Update state references
    print("  Updating state references...")
    update_state_references(practice)

    # Update activity space references
    print("  Updating activity space references...")
    update_activity_space_references(practice)

    # Update baseline reference if needed
    if "baselinePracticeName" in practice:
        practice["baselinePracticeName"] = "Partner Ecosystem Essentials"

    # Update version and timestamp
    if "version" in practice:
        parts = practice["version"].split(".")
        if len(parts) >= 2:
            major = int(parts[0])
            practice["version"] = f"{major + 1}.0.0"

    practice["updatedAt"] = "2026-06-24"

    # Write back
    with open(file_path, 'w') as f:
        json.dump(practice, f, indent=2)

    print(f"  ✓ Refactored {file_path}")

def main():
    """Main refactoring script."""
    practices_dir = Path(__file__).parent.parent / "practices"

    practice_files = [
        "partner-success-planning/partner-success-planning.json",
        "technical-engagement-planning/technical-engagement-planning.json",
    ]

    method_files = [
        "partnering-initiative/partnering-initiative.json",
        "partner-essentials/partner-ecosystem-excellence.json",
        "asap-alliance-management-lifecycle/asap-alliance-management-lifecycle.json",
    ]

    all_files = practice_files + method_files

    for file_path in all_files:
        full_path = practices_dir / file_path
        if full_path.exists():
            refactor_practice(full_path)
        else:
            print(f"WARNING: File not found: {full_path}")

    print("\n✓ All practices refactored successfully!")

if __name__ == "__main__":
    main()
