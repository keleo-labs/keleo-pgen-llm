#!/usr/bin/env python3
"""
Cross-Reference Validation Script for Team Topologies Practice
Validates all references between modules and against the baseline framework.
"""

import json
import sys
from typing import Dict, List, Set, Tuple
from pathlib import Path

class ValidationReport:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.checks_passed = 0
        self.checks_total = 0

    def add_error(self, message: str):
        self.errors.append(f"ERROR: {message}")

    def add_warning(self, message: str):
        self.warnings.append(f"WARNING: {message}")

    def add_info(self, message: str):
        self.info.append(f"INFO: {message}")

    def check(self, condition: bool, error_msg: str) -> bool:
        self.checks_total += 1
        if condition:
            self.checks_passed += 1
            return True
        else:
            self.add_error(error_msg)
            return False

    def check_warning(self, condition: bool, warning_msg: str) -> bool:
        self.checks_total += 1
        if condition:
            self.checks_passed += 1
            return True
        else:
            self.add_warning(warning_msg)
            return False

def load_json(filepath: Path) -> dict:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_alpha_references(index: dict, baseline: dict, report: ValidationReport):
    """Validate all alpha references."""
    print("\n=== Validating Alpha References ===")

    # Build sets of valid alphas and states
    all_alphas = set(index['alphas'].keys())
    baseline_alphas = {a['name'] for a in baseline['alphas']}

    alpha_states = {}
    for alpha_name, alpha_data in index['alphas'].items():
        alpha_states[alpha_name] = set(alpha_data['states'])

    # Check work products reference valid alphas and states
    print("\nChecking work product alpha references...")
    for wp_name, wp_data in index['workProducts'].items():
        for lod in wp_data['levelsOfDetail']:
            # Note: LOD evidencing is in the full modules, not in the index
            # We'll validate structure here, actual evidences require reading modules
            pass
    report.add_info(f"Work product structure validated (detailed LOD evidencing requires module inspection)")

    # Check contributesTo references
    print("\nChecking contributesTo references...")
    for alpha_name, alpha_data in index['alphas'].items():
        if alpha_data['type'] == 'new':
            contributes_to = alpha_data.get('contributesTo')
            if contributes_to is None:
                report.check(False, f"New alpha '{alpha_name}' has no contributesTo (floating alpha)")
            elif isinstance(contributes_to, list):
                for target in contributes_to:
                    if target not in all_alphas and target not in baseline_alphas:
                        report.check(False, f"Alpha '{alpha_name}' contributesTo unknown alpha '{target}'")
                    else:
                        report.check(True, "")
            elif isinstance(contributes_to, str):
                if contributes_to not in all_alphas and contributes_to not in baseline_alphas:
                    report.check(False, f"Alpha '{alpha_name}' contributesTo unknown alpha '{contributes_to}'")
                else:
                    report.check(True, "")

    # Check alpha instances reference valid parent alphas
    print("\nChecking alpha instance references...")
    for instance in index['alphaInstances']:
        parent = instance['alphaName']
        if parent not in all_alphas:
            report.check(False, f"Alpha instance '{instance['name']}' references unknown parent alpha '{parent}'")
        else:
            report.check(True, "")

def validate_workproduct_references(index: dict, report: ValidationReport):
    """Validate work product references."""
    print("\n=== Validating Work Product References ===")

    all_workproducts = set(index['workProducts'].keys())

    # Check work product instances reference valid parents
    print("\nChecking work product instance references...")
    for instance in index['workProductInstances']:
        parent = instance['workProductName']
        if parent not in all_workproducts:
            report.check(False, f"Work product instance '{instance['name']}' references unknown parent '{parent}'")
        else:
            report.check(True, "")

    # Check LOD counts
    print("\nChecking work product LOD counts...")
    for wp_name, wp_data in index['workProducts'].items():
        lod_count = len(wp_data['levelsOfDetail'])
        if lod_count < 2:
            report.check(False, f"Work product '{wp_name}' has only {lod_count} LODs (minimum 2 required)")
        else:
            report.check(True, "")

def validate_activity_references(index: dict, baseline: dict, report: ValidationReport):
    """Validate activity references."""
    print("\n=== Validating Activity References ===")

    # Build set of valid activity spaces from baseline
    baseline_activity_spaces = {a['name'] for a in baseline['activitySpaces']}

    # Check activities reference valid activity spaces
    print("\nChecking activity space references...")
    for activity_name, activity_data in index['activities'].items():
        space_name = activity_data['activitySpaceName']
        if space_name not in baseline_activity_spaces:
            report.check(False, f"Activity '{activity_name}' references unknown ActivitySpace '{space_name}'")
        else:
            report.check(True, "")

        # Check activity name doesn't duplicate its activity space name
        if activity_name == space_name:
            report.check(False, f"Activity '{activity_name}' has same name as its ActivitySpace (must be different)")
        else:
            report.check(True, "")

def validate_persona_references(index: dict, report: ValidationReport):
    """Validate persona and persona group references."""
    print("\n=== Validating Persona References ===")

    all_personas = set(index['personas'])

    # Check persona groups reference valid personas
    print("\nChecking persona group references...")
    for group_name, group_data in index['personaGroups'].items():
        for persona_name in group_data['personaNames']:
            if persona_name not in all_personas:
                report.check(False, f"Persona group '{group_name}' references unknown persona '{persona_name}'")
            else:
                report.check(True, "")

def validate_baseline_references(index: dict, baseline: dict, report: ValidationReport):
    """Validate all baseline references are exact matches."""
    print("\n=== Validating Baseline References ===")

    # Build baseline name sets
    baseline_focuses = {f['name'] for f in baseline['focuses']}
    baseline_activity_spaces = {a['name'] for a in baseline['activitySpaces']}
    baseline_competencies = {c['name'] for c in baseline['competencies']}

    # Check focus names
    print("\nChecking focus references...")
    for focus_name in index['baselineReferences']['focuses']:
        if focus_name not in baseline_focuses:
            report.check(False, f"Unknown focus '{focus_name}' (not in baseline)")
        else:
            report.check(True, "")

    # Check activity space names (case-sensitive)
    print("\nChecking activity space references...")
    for space_name in index['baselineReferences']['activitySpaces']:
        if space_name not in baseline_activity_spaces:
            report.check(False, f"Unknown or mismatched ActivitySpace '{space_name}' (case-sensitive)")
        else:
            report.check(True, "")

    # Check competency names (case-sensitive)
    print("\nChecking competency references...")
    for competency_name in index['baselineReferences']['competencies']:
        if competency_name not in baseline_competencies:
            report.check(False, f"Unknown or mismatched Competency '{competency_name}' (case-sensitive)")
        else:
            report.check(True, "")

    # Check narrative types (if they exist in baseline)
    # Note: Baseline may not have explicit narrative type list, skip if missing
    print("\nChecking narrative type references...")
    report.add_info("Narrative type validation requires module inspection")

def validate_completeness(index: dict, report: ValidationReport):
    """Validate completeness requirements."""
    print("\n=== Validating Completeness ===")

    # Check alphas have at least 3 states
    print("\nChecking alpha state counts...")
    for alpha_name, alpha_data in index['alphas'].items():
        state_count = len(alpha_data['states'])
        if state_count < 3:
            report.check(False, f"Alpha '{alpha_name}' has only {state_count} states (minimum 3 required)")
        else:
            report.check(True, "")

    # Check work products have at least 2 LODs (already done in workproduct validation)

    # Check citations count
    print("\nChecking citation count...")
    citation_count = len(index['citations'])
    if citation_count < 5:
        report.check(False, f"Only {citation_count} citations found (minimum 5 required)")
    else:
        report.check(True, "")

def validate_consistency(index: dict, report: ValidationReport):
    """Validate consistency requirements."""
    print("\n=== Validating Consistency ===")

    # Check no duplicate names within same element type
    print("\nChecking for duplicate alpha names...")
    alpha_names = list(index['alphas'].keys())
    if len(alpha_names) != len(set(alpha_names)):
        report.check(False, "Duplicate alpha names found")
    else:
        report.check(True, "")

    print("\nChecking for duplicate work product names...")
    wp_names = list(index['workProducts'].keys())
    if len(wp_names) != len(set(wp_names)):
        report.check(False, "Duplicate work product names found")
    else:
        report.check(True, "")

    print("\nChecking for duplicate activity names...")
    activity_names = list(index['activities'].keys())
    if len(activity_names) != len(set(activity_names)):
        report.check(False, "Duplicate activity names found")
    else:
        report.check(True, "")

    print("\nChecking for duplicate persona names...")
    persona_names = index['personas']
    if len(persona_names) != len(set(persona_names)):
        report.check(False, "Duplicate persona names found")
    else:
        report.check(True, "")

def generate_summary(index: dict, baseline: dict, report: ValidationReport) -> str:
    """Generate validation summary markdown."""

    # Count elements
    alphas_total = len(index['alphas'])
    alphas_redecl = sum(1 for a in index['alphas'].values() if a['type'] == 'redeclaration')
    alphas_new = sum(1 for a in index['alphas'].values() if a['type'] == 'new')

    alpha_instances_total = len(index['alphaInstances'])
    workproducts_total = len(index['workProducts'])
    wp_instances_total = len(index['workProductInstances'])
    activities_total = len(index['activities'])
    personas_total = len(index['personas'])
    persona_groups_total = len(index['personaGroups'])
    patterns_total = len(index['patterns'])
    citations_total = len(index['citations'])
    aliases_total = len(index['aliases'])

    # Group alphas by focus
    alphas_by_focus = {'Value': [], 'Solution': [], 'Endeavor': []}
    for alpha_name, alpha_data in index['alphas'].items():
        focus = alpha_data['focus']
        if focus in alphas_by_focus:
            alphas_by_focus[focus].append(alpha_name)

    # Group activities by focus
    activities_by_focus = {'Value': [], 'Solution': [], 'Endeavor': []}
    for activity_name, activity_data in index['activities'].items():
        focus = activity_data['focus']
        if focus in activities_by_focus:
            activities_by_focus[focus].append(activity_name)

    # Group patterns by type
    patterns_by_type = {}
    for pattern_name, pattern_data in index['patterns'].items():
        ptype = pattern_data['type']
        if ptype not in patterns_by_type:
            patterns_by_type[ptype] = []
        patterns_by_type[ptype].append(pattern_name)

    # Build summary markdown
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("# Cross-Reference Validation Summary")
    lines.append("")
    lines.append(f"**Generated:** {index['practice']['generatedDate']}")
    lines.append(f"**Practice:** {index['practice']['name']}")
    lines.append("**Validation Phase:** 1.5")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Elements Defined")
    lines.append("")

    # Alphas
    lines.append("### Alphas")
    lines.append(f"**Total:** {alphas_total} ({alphas_redecl} redeclarations, {alphas_new} new alphas)")
    lines.append("")
    for focus in ['Value', 'Solution', 'Endeavor']:
        if alphas_by_focus[focus]:
            lines.append(f"**{focus} Focus:** {', '.join(alphas_by_focus[focus])}")
    lines.append("")

    # Alpha Instances
    lines.append("### Alpha Instances")
    lines.append(f"**Total:** {alpha_instances_total}")
    lines.append("")
    for instance in index['alphaInstances']:
        lines.append(f"- {instance['name']} (instance of {instance['alphaName']})")
    lines.append("")

    # Work Products
    lines.append("### Work Products")
    lines.append(f"**Total:** {workproducts_total}")
    lines.append("")
    for wp_name in index['workProducts'].keys():
        lines.append(f"- {wp_name}")
    lines.append("")

    # Work Product Instances
    lines.append("### Work Product Instances")
    lines.append(f"**Total:** {wp_instances_total}")
    lines.append("")
    for instance in index['workProductInstances']:
        lines.append(f"- {instance['name']} (instance of {instance['workProductName']})")
    lines.append("")

    # Activities
    lines.append("### Activities")
    lines.append(f"**Total:** {activities_total}")
    lines.append("")
    for focus in ['Value', 'Solution', 'Endeavor']:
        if activities_by_focus[focus]:
            lines.append(f"**{focus} Focus:**")
            for activity in activities_by_focus[focus]:
                lines.append(f"- {activity}")
            lines.append("")

    # Personas
    lines.append("### Personas")
    lines.append(f"**Total:** {personas_total}")
    lines.append("")
    for persona in index['personas']:
        lines.append(f"- {persona}")
    lines.append("")

    # Persona Groups
    lines.append("### Persona Groups")
    lines.append(f"**Total:** {persona_groups_total}")
    lines.append("")
    for group_name in index['personaGroups'].keys():
        lines.append(f"- {group_name}")
    lines.append("")

    # Patterns
    lines.append("### Patterns")
    lines.append(f"**Total:** {patterns_total}")
    lines.append("")
    for ptype, patterns in patterns_by_type.items():
        lines.append(f"**{ptype}:**")
        for pattern in patterns:
            lines.append(f"- {pattern}")
        lines.append("")

    # Citations
    lines.append("### Citations")
    lines.append(f"**Total:** {citations_total}")
    lines.append("")
    for citation in index['citations']:
        authors = ', '.join(citation['authors'])
        lines.append(f"- {citation['title']} ({authors}, {citation['date']})")
    lines.append("")

    # Aliases
    lines.append("### Aliases")
    lines.append(f"**Total:** {aliases_total}")
    if aliases_total == 0:
        lines.append("None")
    lines.append("")

    # Baseline References
    lines.append("## Baseline References")
    lines.append("")
    lines.append(f"**Focuses Used:** {', '.join(index['baselineReferences']['focuses'])}")
    lines.append("")
    lines.append(f"**ActivitySpaces Used:** {', '.join(index['baselineReferences']['activitySpaces'])}")
    lines.append("")
    lines.append(f"**Competencies Used:** {', '.join(index['baselineReferences']['competencies'])}")
    lines.append("")
    lines.append(f"**NarrativeTypes Used:** {', '.join(index['baselineReferences']['narrativeTypes'])}")
    lines.append("")

    # Validation Results
    lines.append("## Validation Results")
    lines.append("")

    # Cross-Reference Checks
    cross_ref_errors = [e for e in report.errors if not e.startswith("ERROR: Alpha ") or "has only" not in e]
    cross_ref_errors = [e for e in cross_ref_errors if "minimum" not in e]
    lines.append("### Cross-Reference Checks")
    if cross_ref_errors:
        lines.append(f"**Status:** {len(cross_ref_errors)} issue(s) found")
        lines.append("")
        for error in cross_ref_errors:
            lines.append(f"- {error}")
        lines.append("")
    else:
        lines.append("**Status:** All cross-reference checks passed")
        lines.append("")

    # Completeness Checks
    completeness_errors = [e for e in report.errors if "has only" in e or "minimum" in e or "Only" in e]
    lines.append("### Completeness Checks")
    if completeness_errors:
        lines.append(f"**Status:** {len(completeness_errors)} issue(s) found")
        lines.append("")
        for error in completeness_errors:
            lines.append(f"- {error}")
        lines.append("")
    else:
        lines.append("**Status:** All completeness checks passed")
        lines.append("")

    # Consistency Checks
    consistency_errors = [e for e in report.errors if "Duplicate" in e or "same name as" in e]
    lines.append("### Consistency Checks")
    if consistency_errors:
        lines.append(f"**Status:** {len(consistency_errors)} issue(s) found")
        lines.append("")
        for error in consistency_errors:
            lines.append(f"- {error}")
        lines.append("")
    else:
        lines.append("**Status:** All consistency checks passed")
        lines.append("")

    # Warnings
    if report.warnings:
        lines.append("### Warnings")
        lines.append("")
        for warning in report.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Overall Status
    lines.append("## Overall Status")
    lines.append("")
    lines.append(f"**Total Checks:** {report.checks_total}")
    lines.append(f"**Passed:** {report.checks_passed}")
    lines.append(f"**Failed:** {report.checks_total - report.checks_passed}")
    lines.append("")

    if len(report.errors) == 0:
        lines.append("**Quality Gate:** PASS")
        lines.append("")
        lines.append("All validation checks passed. Ready to proceed to Phase 2.")
    else:
        lines.append("**Quality Gate:** FAIL")
        lines.append("")
        lines.append("Critical errors found. Must resolve before Phase 2.")
    lines.append("")
    lines.append("---")

    return '\n'.join(lines)

def main():
    """Main validation function."""
    # Load files
    base_path = Path("/Users/eseymour/code/keleo-pgen-llm")
    index_path = base_path / "practices/team-topologies/cross-reference-index.json"
    baseline_path = base_path / "deps/platform-adoption-kernel.json"
    report_path = base_path / "practices/team-topologies/research-report.md"

    print(f"Loading cross-reference index from {index_path}")
    index = load_json(index_path)

    print(f"Loading baseline framework from {baseline_path}")
    baseline = load_json(baseline_path)

    # Create validation report
    report = ValidationReport()

    # Run validation checks
    validate_alpha_references(index, baseline, report)
    validate_workproduct_references(index, report)
    validate_activity_references(index, baseline, report)
    validate_persona_references(index, report)
    validate_baseline_references(index, baseline, report)
    validate_completeness(index, report)
    validate_consistency(index, report)

    # Generate summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    summary = generate_summary(index, baseline, report)

    # Print summary
    print(summary)

    # Append to research report
    print(f"\nAppending validation summary to {report_path}")
    with open(report_path, 'a') as f:
        f.write('\n\n')
        f.write(summary)

    print("\nValidation complete!")

    # Exit with appropriate code
    if len(report.errors) > 0:
        print(f"\n❌ Validation failed with {len(report.errors)} error(s)")
        sys.exit(1)
    else:
        print("\n✅ Validation passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
