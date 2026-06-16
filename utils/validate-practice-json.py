#!/usr/bin/env python3
"""
Comprehensive Practice Language JSON Validator

Validates Practice/Method JSON files against:
1. JSON Schema (deps/language.schema.json)
2. Baseline practice references (user-provided baseline)
3. Internal cross-reference integrity

Outputs structured JSON report for skill consumption.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

try:
    import jsonschema
    from jsonschema import Draft202012Validator, RefResolver
except ImportError:
    print("ERROR: jsonschema library not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


class PracticeValidator:
    """Validates Practice/Method JSON against schema, baseline, and internal refs"""

    def __init__(self, practice_file: Path, baseline_file: Path, schema_file: Path):
        self.practice_file = practice_file
        self.baseline_file = baseline_file
        self.schema_file = schema_file
        self.errors = []
        self.warnings = []

        # Load files
        self.practice = self._load_json(practice_file)
        self.baseline = self._load_json(baseline_file)
        self.schema = self._load_json(schema_file)

        # Build baseline indexes
        self.baseline_alphas = {}
        self.baseline_alpha_states = defaultdict(set)
        self.baseline_competencies = set()
        self.baseline_activity_spaces = set()
        self.baseline_focuses = set()

        self._index_baseline()

    def _load_json(self, file_path: Path) -> Dict:
        """Load and parse JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

    def _index_baseline(self):
        """Build indexes of baseline elements for validation"""
        # Index focuses
        for focus in self.baseline.get('focuses', []):
            self.baseline_focuses.add(focus['name'])

        # Index alphas and their states
        for alpha in self.baseline.get('alphas', []):
            alpha_name = alpha['name']
            self.baseline_alphas[alpha_name] = alpha

            for state in alpha.get('states', []):
                self.baseline_alpha_states[alpha_name].add(state['name'])

        # Index competencies
        for comp in self.baseline.get('competencies', []):
            self.baseline_competencies.add(comp['name'])

        # Index activity spaces
        for asp in self.baseline.get('activitySpaces', []):
            self.baseline_activity_spaces.add(asp['name'])

    def validate_schema(self) -> bool:
        """Validate against JSON Schema"""
        try:
            # Create resolver for $ref handling
            schema_dir = self.schema_file.parent
            resolver = RefResolver(
                base_uri=f"file://{schema_dir}/",
                referrer=self.schema
            )

            validator = Draft202012Validator(self.schema, resolver=resolver)

            schema_errors = list(validator.iter_errors(self.practice))

            for error in schema_errors:
                # Build path string
                path = "root"
                if error.absolute_path:
                    path = ".".join([str(p) for p in error.absolute_path])

                self.errors.append({
                    "category": "schema",
                    "severity": "error",
                    "path": path,
                    "issue": error.message,
                    "expected": error.validator_value if hasattr(error, 'validator_value') else None,
                    "actual": error.instance if len(str(error.instance)) < 100 else str(error.instance)[:100] + "...",
                    "suggestion": self._suggest_schema_fix(error)
                })

            return len(schema_errors) == 0

        except Exception as e:
            self.errors.append({
                "category": "schema",
                "severity": "error",
                "path": "root",
                "issue": f"Schema validation failed: {str(e)}",
                "expected": None,
                "actual": None,
                "suggestion": "Check schema file and practice JSON structure"
            })
            return False

    def _suggest_schema_fix(self, error: jsonschema.ValidationError) -> str:
        """Generate helpful suggestion for schema errors"""
        if error.validator == 'required':
            return f"Add required property: {error.message}"
        elif error.validator == 'type':
            return f"Change type to {error.validator_value}"
        elif error.validator == 'additionalProperties':
            return f"Remove unevaluated property or check property name spelling"
        elif error.validator == 'oneOf':
            return "Check that object matches one of the allowed schemas"
        else:
            return "Review schema definition and adjust JSON structure"

    def validate_baseline_references(self) -> bool:
        """Validate references to baseline practice elements"""
        has_errors = False

        # Determine if this is a Practice or Method
        is_method = 'practices' in self.practice or 'baselinePractice' in self.practice

        if is_method:
            practices = self.practice.get('practices', [])
        else:
            practices = [self.practice]

        # Build practice-defined elements (alphas, work products, etc.)
        practice_alphas = {}
        practice_alpha_states = defaultdict(set)

        # Index alphas from ALL practices in method (for cross-practice references)
        for practice in practices:
            # Index practice-defined alphas and merge states
            for alpha in practice.get('alphas', []):
                alpha_name = alpha['name']
                practice_alphas[alpha_name] = alpha

                for state in alpha.get('states', []):
                    practice_alpha_states[alpha_name].add(state['name'])

        # Merge baseline + practice alpha states
        merged_alpha_states = defaultdict(set)
        for alpha_name in self.baseline_alpha_states:
            merged_alpha_states[alpha_name].update(self.baseline_alpha_states[alpha_name])
        for alpha_name in practice_alpha_states:
            merged_alpha_states[alpha_name].update(practice_alpha_states[alpha_name])

        # Validate each practice
        for practice_idx, practice in enumerate(practices):
            prefix = f"practices[{practice_idx}]" if is_method else ""

            # Build allowed alphas for THIS practice
            # Includes: baseline + practice-defined + cross-practice dependencies
            allowed_alphas = set(self.baseline_alphas.keys())
            allowed_alphas.update(practice_alphas.keys())

            # For cross-practice dependencies (via practiceDependencyNames),
            # allow alpha references without validation since dependency practices
            # may not be available at validation time
            practice_deps = practice.get('practiceDependencyNames', [])
            has_cross_practice_deps = len(practice_deps) > 0

            # Validate competency references
            has_errors |= self._validate_competencies(practice, prefix)

            # Validate alpha and state references
            has_errors |= self._validate_alphas(
                practice,
                merged_alpha_states,
                prefix,
                allowed_alphas,
                has_cross_practice_deps
            )

            # Validate focus references
            has_errors |= self._validate_focuses(practice, prefix)

            # Validate activity space references
            has_errors |= self._validate_activity_spaces(practice, prefix)

        return not has_errors

    def _validate_competencies(self, practice: Dict, prefix: str) -> bool:
        """Validate competency name references"""
        has_errors = False

        # Check activities
        for idx, activity in enumerate(practice.get('activities', [])):
            path = f"{prefix}.activities[{idx}]" if prefix else f"activities[{idx}]"

            # requiredCompetencies (array of strings)
            for comp_idx, comp_name in enumerate(activity.get('requiredCompetencies', [])):
                if comp_name not in self.baseline_competencies:
                    self.errors.append({
                        "category": "baseline",
                        "severity": "error",
                        "path": f"{path}.requiredCompetencies[{comp_idx}]",
                        "issue": f"Invalid competency name: '{comp_name}'",
                        "expected": f"One of: {sorted(self.baseline_competencies)}",
                        "actual": comp_name,
                        "suggestion": self._suggest_competency(comp_name)
                    })
                    has_errors = True

            # recommendedCompetencyLevels (array of {competencyName, competencyLevelName})
            for clr_idx, clr in enumerate(activity.get('recommendedCompetencyLevels', [])):
                comp_name = clr.get('competencyName')
                if comp_name and comp_name not in self.baseline_competencies:
                    self.errors.append({
                        "category": "baseline",
                        "severity": "error",
                        "path": f"{path}.recommendedCompetencyLevels[{clr_idx}].competencyName",
                        "issue": f"Invalid competency name: '{comp_name}'",
                        "expected": f"One of: {sorted(self.baseline_competencies)}",
                        "actual": comp_name,
                        "suggestion": self._suggest_competency(comp_name)
                    })
                    has_errors = True

        # Check personas
        for idx, persona in enumerate(practice.get('personas', [])):
            path = f"{prefix}.personas[{idx}]" if prefix else f"personas[{idx}]"

            for clr_idx, clr in enumerate(persona.get('competencies', [])):
                comp_name = clr.get('competencyName')
                if comp_name and comp_name not in self.baseline_competencies:
                    self.errors.append({
                        "category": "baseline",
                        "severity": "error",
                        "path": f"{path}.competencies[{clr_idx}].competencyName",
                        "issue": f"Invalid competency name: '{comp_name}'",
                        "expected": f"One of: {sorted(self.baseline_competencies)}",
                        "actual": comp_name,
                        "suggestion": self._suggest_competency(comp_name)
                    })
                    has_errors = True

        return has_errors

    def _suggest_competency(self, comp_name: str) -> str:
        """Suggest correct competency name based on fuzzy matching"""
        # Simple substring matching
        comp_lower = comp_name.lower()

        if any(word in comp_lower for word in ['security', 'compliance', 'govern']):
            return "Use: 'Platform Security And Compliance Enforcement'"
        elif any(word in comp_lower for word in ['strategy', 'strategic', 'align']):
            return "Use: 'Platform Strategic Alignment'"
        elif any(word in comp_lower for word in ['reliability', 'sre', 'site']):
            return "Use: 'Site Reliability'"
        elif any(word in comp_lower for word in ['stakeholder', 'represent']):
            return "Use: 'Stakeholder Representation'"
        elif any(word in comp_lower for word in ['engineer', 'develop', 'build']):
            return "Use: 'Engineering'"
        elif any(word in comp_lower for word in ['analy', 'research']):
            return "Use: 'Analysis'"
        elif any(word in comp_lower for word in ['lead', 'leader']):
            return "Use: 'Leadership'"
        elif any(word in comp_lower for word in ['manage', 'project']):
            return "Use: 'Management'"
        else:
            return f"Check baseline competencies: {sorted(self.baseline_competencies)}"

    def _validate_alphas(self, practice: Dict, merged_alpha_states: Dict, prefix: str,
                         allowed_alphas: set, has_cross_practice_deps: bool) -> bool:
        """Validate alpha and state references"""
        has_errors = False

        # Use provided allowed_alphas set (includes baseline + practice-defined)
        valid_alphas = allowed_alphas

        # Check new alphas have contributesTo (or are from practice dependencies)
        for idx, alpha in enumerate(practice.get('alphas', [])):
            alpha_name = alpha['name']
            path = f"{prefix}.alphas[{idx}]" if prefix else f"alphas[{idx}]"
            contributes_to = alpha.get('contributesTo')

            # If not a baseline alpha, must have contributesTo
            if alpha_name not in self.baseline_alphas:
                if not contributes_to:
                    self.errors.append({
                        "category": "baseline",
                        "severity": "error",
                        "path": f"{path}.contributesTo",
                        "issue": f"New alpha '{alpha_name}' missing contributesTo (floating alpha)",
                        "expected": "Name of baseline alpha this extends (or practice-local alpha)",
                        "actual": None,
                        "suggestion": f"Add contributesTo pointing to one of: {sorted(self.baseline_alphas.keys())} or practice-local alpha defined earlier"
                    })
                    has_errors = True
                elif contributes_to not in self.baseline_alphas and contributes_to not in valid_alphas:
                    # contributesTo references unknown alpha (not baseline, not in this practice/method)
                    # If practice has dependencies, allow reference (may be from external practice)
                    if not has_cross_practice_deps:
                        self.errors.append({
                            "category": "baseline",
                            "severity": "error",
                            "path": f"{path}.contributesTo",
                            "issue": f"contributesTo references unknown alpha: '{contributes_to}'",
                            "expected": f"One of: {sorted(self.baseline_alphas.keys())} or practice-local alpha",
                            "actual": contributes_to,
                            "suggestion": f"Use exact baseline alpha name (case-sensitive) or add to practiceDependencyNames if from external practice"
                        })
                        has_errors = True

        # Validate AlphaContribution references in activities
        for idx, activity in enumerate(practice.get('activities', [])):
            path = f"{prefix}.activities[{idx}]" if prefix else f"activities[{idx}]"

            for contrib_idx, contrib in enumerate(activity.get('contributesTo', [])):
                alpha_name = contrib.get('alphaName')
                state_name = contrib.get('stateName')
                contrib_path = f"{path}.contributesTo[{contrib_idx}]"

                if alpha_name and alpha_name not in valid_alphas:
                    # If practice has cross-practice dependencies, allow reference (may be from external practice)
                    if not has_cross_practice_deps:
                        self.errors.append({
                            "category": "baseline",
                            "severity": "error",
                            "path": f"{contrib_path}.alphaName",
                            "issue": f"Unknown alpha: '{alpha_name}'",
                            "expected": f"One of: {sorted(valid_alphas)}",
                            "actual": alpha_name,
                            "suggestion": "Use exact alpha name (case-sensitive) or add to practiceDependencyNames if from external practice"
                        })
                        has_errors = True

                if alpha_name and state_name:
                    # Only validate state if alpha is known (in merged_alpha_states)
                    if alpha_name in merged_alpha_states:
                        if state_name not in merged_alpha_states.get(alpha_name, set()):
                            self.errors.append({
                                "category": "baseline",
                                "severity": "error",
                                "path": f"{contrib_path}.stateName",
                                "issue": f"Unknown state '{state_name}' for alpha '{alpha_name}'",
                                "expected": f"One of: {sorted(merged_alpha_states.get(alpha_name, set()))}",
                                "actual": state_name,
                                "suggestion": f"Check state names defined in {alpha_name} alpha"
                            })
                            has_errors = True
                    elif not has_cross_practice_deps:
                        # Alpha unknown and no cross-practice deps - error
                        self.errors.append({
                            "category": "baseline",
                            "severity": "error",
                            "path": f"{contrib_path}.alphaName",
                            "issue": f"Cannot validate state for unknown alpha: '{alpha_name}'",
                            "expected": f"Define alpha in practice or add to practiceDependencyNames",
                            "actual": alpha_name,
                            "suggestion": "Add alpha definition or declare practice dependency"
                        })
                        has_errors = True

        # Validate AlphaContribution in work product LODs
        for wp_idx, wp in enumerate(practice.get('workProducts', [])):
            wp_path = f"{prefix}.workProducts[{wp_idx}]" if prefix else f"workProducts[{wp_idx}]"

            for lod_idx, lod in enumerate(wp.get('levelsOfDetail', [])):
                lod_path = f"{wp_path}.levelsOfDetail[{lod_idx}]"

                for contrib_idx, contrib in enumerate(lod.get('contributesTo', [])):
                    alpha_name = contrib.get('alphaName')
                    state_name = contrib.get('stateName')
                    contrib_path = f"{lod_path}.contributesTo[{contrib_idx}]"

                    if alpha_name and alpha_name not in valid_alphas:
                        # If practice has cross-practice dependencies, allow reference (may be from external practice)
                        if not has_cross_practice_deps:
                            self.errors.append({
                                "category": "baseline",
                                "severity": "error",
                                "path": f"{contrib_path}.alphaName",
                                "issue": f"Unknown alpha: '{alpha_name}'",
                                "expected": f"One of: {sorted(valid_alphas)}",
                                "actual": alpha_name,
                                "suggestion": "Use exact alpha name (case-sensitive) or add to practiceDependencyNames if from external practice"
                            })
                            has_errors = True

                    if alpha_name and state_name:
                        # Only validate state if alpha is known (in merged_alpha_states)
                        if alpha_name in merged_alpha_states:
                            if state_name not in merged_alpha_states.get(alpha_name, set()):
                                self.errors.append({
                                    "category": "baseline",
                                    "severity": "error",
                                    "path": f"{contrib_path}.stateName",
                                    "issue": f"Unknown state '{state_name}' for alpha '{alpha_name}'",
                                    "expected": f"One of: {sorted(merged_alpha_states.get(alpha_name, set()))}",
                                    "actual": state_name,
                                    "suggestion": f"Check state names defined in {alpha_name} alpha"
                                })
                                has_errors = True
                        elif not has_cross_practice_deps:
                            # Alpha unknown and no cross-practice deps - error
                            self.errors.append({
                                "category": "baseline",
                                "severity": "error",
                                "path": f"{contrib_path}.alphaName",
                                "issue": f"Cannot validate state for unknown alpha: '{alpha_name}'",
                                "expected": f"Define alpha in practice or add to practiceDependencyNames",
                                "actual": alpha_name,
                                "suggestion": "Add alpha definition or declare practice dependency"
                            })
                            has_errors = True

        return has_errors

    def _validate_focuses(self, practice: Dict, prefix: str) -> bool:
        """Validate focus references"""
        has_errors = False

        # Check alpha focus references
        for idx, alpha in enumerate(practice.get('alphas', [])):
            focus_name = alpha.get('focusName')
            if focus_name and focus_name not in self.baseline_focuses:
                path = f"{prefix}.alphas[{idx}].focusName" if prefix else f"alphas[{idx}].focusName"
                self.errors.append({
                    "category": "baseline",
                    "severity": "error",
                    "path": path,
                    "issue": f"Unknown focus: '{focus_name}'",
                    "expected": f"One of: {sorted(self.baseline_focuses)}",
                    "actual": focus_name,
                    "suggestion": "Use: 'Value', 'Solution', or 'Endeavor'"
                })
                has_errors = True

        # Check activity focus references
        for idx, activity in enumerate(practice.get('activities', [])):
            focus_name = activity.get('focusName')
            if focus_name and focus_name not in self.baseline_focuses:
                path = f"{prefix}.activities[{idx}].focusName" if prefix else f"activities[{idx}].focusName"
                self.errors.append({
                    "category": "baseline",
                    "severity": "error",
                    "path": path,
                    "issue": f"Unknown focus: '{focus_name}'",
                    "expected": f"One of: {sorted(self.baseline_focuses)}",
                    "actual": focus_name,
                    "suggestion": "Use: 'Value', 'Solution', or 'Endeavor'"
                })
                has_errors = True

        return has_errors

    def _validate_activity_spaces(self, practice: Dict, prefix: str) -> bool:
        """Validate activity space references and required activity properties"""
        has_errors = False

        # Check activity references to activity spaces
        for idx, activity in enumerate(practice.get('activities', [])):
            # Required properties for Activity (per schema)
            required_activity_props = {
                'activitySpaceName': 'string (references ActivitySpace.name)',
                'focusName': 'string (references Focus.name)',
                'contributesTo': 'array of AlphaContribution',
                'worksOn': 'array of WorkProductContribution',
                'requiredCompetencies': 'array of Competency.name strings',
                'recommendedCompetencyLevels': 'array of CompetencyLevelReference'
            }

            # Check for missing required properties
            for prop, prop_type in required_activity_props.items():
                if prop not in activity:
                    path = f"{prefix}.activities[{idx}]" if prefix else f"activities[{idx}]"
                    self.errors.append({
                        "category": "schema",
                        "severity": "error",
                        "path": path,
                        "issue": f"Missing required Activity property: '{prop}'",
                        "expected": f"Activity must have '{prop}' ({prop_type})",
                        "actual": f"Activity '{activity.get('name', 'unnamed')}' missing '{prop}'",
                        "suggestion": f"Add '{prop}' property to activity. According to schema, Activity extends ActivitySpaceCore which requires: activitySpaceName (for flat Practice.activities), focusName, contributesTo, requiredCompetencies. Activity also requires: worksOn, recommendedCompetencyLevels."
                    })
                    has_errors = True

            # Validate activitySpaceName reference if present
            asp_name = activity.get('activitySpaceName')
            if asp_name and asp_name not in self.baseline_activity_spaces:
                path = f"{prefix}.activities[{idx}].activitySpaceName" if prefix else f"activities[{idx}].activitySpaceName"
                self.errors.append({
                    "category": "baseline",
                    "severity": "warning",
                    "path": path,
                    "issue": f"Unknown activity space: '{asp_name}'",
                    "expected": f"One of baseline: {sorted(self.baseline_activity_spaces)}",
                    "actual": asp_name,
                    "suggestion": "Verify activity space name or define it in practice"
                })
                has_errors = True

        return has_errors

    def validate_internal_integrity(self) -> bool:
        """Validate internal cross-references within practice/method"""
        has_errors = False

        # Determine if this is a Practice or Method
        is_method = 'practices' in self.practice or 'baselinePractice' in self.practice

        if is_method:
            practices = self.practice.get('practices', [])
        else:
            practices = [self.practice]

        # Build element indexes across all practices
        all_alphas = set()
        all_alpha_states = defaultdict(set)
        all_work_products = set()
        all_activities = set()

        # Track which practices have cross-practice dependencies
        practices_with_deps = {}
        for practice in practices:
            practice_name = practice.get('name')
            practice_deps = practice.get('practiceDependencyNames', [])
            if practice_deps:
                practices_with_deps[practice_name] = practice_deps

        # Index baseline elements
        for alpha in self.baseline.get('alphas', []):
            all_alphas.add(alpha['name'])
            for state in alpha.get('states', []):
                all_alpha_states[alpha['name']].add(state['name'])

        # Index practice-defined elements
        for practice in practices:
            for alpha in practice.get('alphas', []):
                alpha_name = alpha['name']
                all_alphas.add(alpha_name)
                for state in alpha.get('states', []):
                    all_alpha_states[alpha_name].add(state['name'])

            for wp in practice.get('workProducts', []):
                all_work_products.add(wp['name'])

            for activity in practice.get('activities', []):
                all_activities.add(activity['name'])

        # Validate each practice
        for practice_idx, practice in enumerate(practices):
            prefix = f"practices[{practice_idx}]" if is_method else ""
            practice_name = practice.get('name')
            has_cross_practice_deps = practice_name in practices_with_deps

            # Validate activity -> work product references
            for act_idx, activity in enumerate(practice.get('activities', [])):
                path = f"{prefix}.activities[{act_idx}]" if prefix else f"activities[{act_idx}]"

                for wp_idx, wp_contrib in enumerate(activity.get('worksOn', [])):
                    wp_name = wp_contrib.get('workProductName')
                    if wp_name and wp_name not in all_work_products:
                        self.errors.append({
                            "category": "integrity",
                            "severity": "error",
                            "path": f"{path}.worksOn[{wp_idx}].workProductName",
                            "issue": f"Activity references undefined work product: '{wp_name}'",
                            "expected": f"One of: {sorted(all_work_products)}",
                            "actual": wp_name,
                            "suggestion": "Define work product or correct reference"
                        })
                        has_errors = True

            # Validate pattern view -> activity/alpha references
            for pattern_idx, pattern in enumerate(practice.get('patterns', [])):
                pattern_path = f"{prefix}.patterns[{pattern_idx}]" if prefix else f"patterns[{pattern_idx}]"

                for view_idx, view in enumerate(pattern.get('patternViews', [])):
                    view_path = f"{pattern_path}.patternViews[{view_idx}]"

                    # Check activity references
                    for act_idx, act_name in enumerate(view.get('activities', [])):
                        if act_name not in all_activities:
                            self.errors.append({
                                "category": "integrity",
                                "severity": "error",
                                "path": f"{view_path}.activities[{act_idx}]",
                                "issue": f"Pattern view references undefined activity: '{act_name}'",
                                "expected": f"One of: {sorted(all_activities)}",
                                "actual": act_name,
                                "suggestion": "Define activity or correct reference"
                            })
                            has_errors = True

                    # Check alpha/state references
                    for as_idx, alpha_state in enumerate(view.get('alphaStates', [])):
                        if isinstance(alpha_state, dict):
                            alpha_name = alpha_state.get('alphaName')
                            state_name = alpha_state.get('stateName')

                            if alpha_name and alpha_name not in all_alphas:
                                # If practice has cross-practice deps, allow reference (may be from dependency)
                                if not has_cross_practice_deps:
                                    self.errors.append({
                                        "category": "integrity",
                                        "severity": "error",
                                        "path": f"{view_path}.alphaStates[{as_idx}].alphaName",
                                        "issue": f"Pattern view references undefined alpha: '{alpha_name}'",
                                        "expected": f"One of: {sorted(all_alphas)}",
                                        "actual": alpha_name,
                                        "suggestion": "Define alpha or add to practiceDependencyNames if from external practice"
                                    })
                                    has_errors = True

                            if alpha_name and state_name:
                                # Only validate state if alpha is known
                                if alpha_name in all_alpha_states:
                                    if state_name not in all_alpha_states.get(alpha_name, set()):
                                        self.errors.append({
                                            "category": "integrity",
                                            "severity": "error",
                                            "path": f"{view_path}.alphaStates[{as_idx}].stateName",
                                            "issue": f"Pattern view references undefined state: '{state_name}' for alpha '{alpha_name}'",
                                            "expected": f"One of: {sorted(all_alpha_states.get(alpha_name, set()))}",
                                            "actual": state_name,
                                            "suggestion": "Define state or correct reference"
                                        })
                                        has_errors = True
                                elif not has_cross_practice_deps:
                                    # Alpha unknown and no cross-practice deps
                                    self.errors.append({
                                        "category": "integrity",
                                        "severity": "error",
                                        "path": f"{view_path}.alphaStates[{as_idx}].alphaName",
                                        "issue": f"Cannot validate state for unknown alpha: '{alpha_name}'",
                                        "expected": f"Define alpha in practice or add to practiceDependencyNames",
                                        "actual": alpha_name,
                                        "suggestion": "Add alpha definition or declare practice dependency"
                                    })
                                    has_errors = True

        return not has_errors

    def generate_report(self) -> Dict:
        """Generate structured validation report"""
        return {
            "practice_file": str(self.practice_file),
            "baseline_file": str(self.baseline_file),
            "schema_file": str(self.schema_file),
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "schema": sum(1 for e in self.errors if e['category'] == 'schema'),
                "baseline": sum(1 for e in self.errors if e['category'] == 'baseline'),
                "integrity": sum(1 for e in self.errors if e['category'] == 'integrity'),
                "semantic": sum(1 for w in self.warnings if w['category'] == 'semantic')
            }
        }

    def validate_semantic_alignment(self) -> bool:
        """
        Validate semantic appropriateness of contributesTo relationships.

        Uses state alignment heuristic to detect potentially incorrect contributesTo choices.
        Generates warnings (not errors) since semantic fit can be subjective.
        """
        practices = self.practice.get('practices', [self.practice])

        for practice in practices:
            practice_name = practice.get('name', 'Unknown')

            for alpha in practice.get('alphas', []):
                alpha_name = alpha.get('name', 'Unknown')
                contributes_to = alpha.get('contributesTo')

                # Only validate new alphas with contributesTo
                if not contributes_to:
                    continue

                # Get baseline parent alpha
                if contributes_to not in self.baseline_alphas:
                    continue  # Already flagged by baseline validation

                parent_alpha = self.baseline_alphas[contributes_to]
                parent_states = [s['name'] for s in parent_alpha.get('states', [])]
                child_states = [s['name'] for s in alpha.get('states', [])]

                # Calculate state alignment
                alignment_score, matches = self._calculate_state_alignment(child_states, parent_states)

                # Warn if alignment is weak
                if alignment_score < 0.5:  # <50% alignment
                    self.warnings.append({
                        'category': 'semantic',
                        'severity': 'warning',
                        'practice': practice_name,
                        'alpha': alpha_name,
                        'contributesTo': contributes_to,
                        'issue': f'Weak state alignment ({alignment_score:.0%}) between child and parent alpha',
                        'details': {
                            'child_states': child_states,
                            'parent_states': parent_states,
                            'matches': matches,
                            'alignment_score': f'{alignment_score:.0%}'
                        },
                        'suggestion': 'Review contributesTo decision using state alignment heuristic (references/semantics.md Section 9.2.5). Consider if different parent alpha is more semantically appropriate, or if this should be a redeclaration instead of specialization.'
                    })

                # Info if alignment is moderate (50-70%)
                elif alignment_score < 0.7:
                    self.warnings.append({
                        'category': 'semantic',
                        'severity': 'info',
                        'practice': practice_name,
                        'alpha': alpha_name,
                        'contributesTo': contributes_to,
                        'issue': f'Moderate state alignment ({alignment_score:.0%}) - verify semantic fit',
                        'details': {
                            'child_states': child_states,
                            'parent_states': parent_states,
                            'matches': matches,
                            'alignment_score': f'{alignment_score:.0%}'
                        },
                        'suggestion': 'State alignment is moderate. Verify that alpha description also aligns with parent description to confirm correct contributesTo choice.'
                    })

        return True  # Semantic validation never fails, only warns

    def _calculate_state_alignment(self, child_states: List[str], parent_states: List[str]) -> Tuple[float, List[str]]:
        """
        Calculate state alignment score using fuzzy matching.

        Returns (alignment_score, list_of_matches)
        alignment_score = matches / len(child_states)
        """
        if not child_states or not parent_states:
            return 0.0, []

        matches = []

        for child_state in child_states:
            # Exact match
            if child_state in parent_states:
                matches.append(f'{child_state} = {child_state} (exact)')
                continue

            # Fuzzy match (case-insensitive substring)
            child_lower = child_state.lower()
            for parent_state in parent_states:
                parent_lower = parent_state.lower()

                # Check for substring matches or common synonyms
                if (child_lower in parent_lower or parent_lower in child_lower or
                    self._are_synonyms(child_lower, parent_lower)):
                    matches.append(f'{child_state} ~ {parent_state} (semantic)')
                    break

        alignment_score = len(matches) / len(child_states) if child_states else 0.0
        return alignment_score, matches

    def _are_synonyms(self, state1: str, state2: str) -> bool:
        """Check if two state names are conceptual synonyms"""
        synonyms = [
            {'deployed', 'available', 'provisioned', 'operational'},
            {'scoped', 'defined', 'bounded'},
            {'optimized', 'evolved', 'mature', 'optimised'},
            {'functional', 'working', 'active', 'operational'},
            {'ready', 'prepared', 'enabled'},
            {'identified', 'recognized', 'discovered'},
        ]

        state1_words = set(state1.lower().split())
        state2_words = set(state2.lower().split())

        for synonym_set in synonyms:
            if state1_words & synonym_set and state2_words & synonym_set:
                return True

        return False

    def validate_redeclaration_vs_new(self) -> bool:
        """
        Validate that alphas are correctly classified as redeclaration vs new.

        Errors:
        - Alpha has contributesTo but name matches baseline (should be redeclaration)
        - Alpha doesn't have contributesTo and name doesn't match baseline (should have contributesTo)

        This is a CRITICAL validation that prevents the "Platform Governance" error class.
        """
        practices = self.practice.get('practices', [self.practice])
        has_errors = False

        for practice_idx, practice in enumerate(practices):
            practice_name = practice.get('name', 'Unknown')
            prefix = f"practices[{practice_idx}]" if 'practices' in self.practice else ""

            for alpha_idx, alpha in enumerate(practice.get('alphas', [])):
                alpha_name = alpha.get('name')
                has_contributes_to = 'contributesTo' in alpha

                path = f"{prefix}.alphas[{alpha_idx}]" if prefix else f"alphas[{alpha_idx}]"

                # Check if this alpha name exactly matches a baseline alpha name
                is_baseline_alpha = alpha_name in self.baseline_alphas

                if is_baseline_alpha:
                    # This is a baseline alpha - should be REDECLARATION
                    if has_contributes_to:
                        contributes_to = alpha.get('contributesTo')
                        self.errors.append({
                            'category': 'baseline',
                            'severity': 'error',
                            'practice': practice_name,
                            'path': path,
                            'alpha': alpha_name,
                            'issue': f'Alpha "{alpha_name}" exists in baseline but has contributesTo property',
                            'expected': 'No contributesTo property (baseline alphas are redeclared, not specialized)',
                            'actual': f'contributesTo: "{contributes_to}"',
                            'suggestion': f'Remove contributesTo property. "{alpha_name}" should be a REDECLARATION (enrichment) of the baseline alpha, not a new specialized alpha. Preserve baseline name, description, and state structure exactly. Only add practice-specific checklists to existing states.'
                        })
                        has_errors = True

                    # Additionally check if states match baseline (redeclarations MUST preserve baseline states)
                    baseline_alpha = self.baseline_alphas[alpha_name]
                    baseline_state_names = {s['name'] for s in baseline_alpha.get('states', [])}
                    practice_state_names = {s['name'] for s in alpha.get('states', [])}

                    if baseline_state_names != practice_state_names:
                        missing_states = baseline_state_names - practice_state_names
                        extra_states = practice_state_names - baseline_state_names

                        issue_parts = []
                        if missing_states:
                            issue_parts.append(f'missing baseline states: {sorted(missing_states)}')
                        if extra_states:
                            issue_parts.append(f'has extra states not in baseline: {sorted(extra_states)}')

                        self.errors.append({
                            'category': 'baseline',
                            'severity': 'error',
                            'practice': practice_name,
                            'path': f'{path}.states',
                            'alpha': alpha_name,
                            'issue': f'Redeclared alpha "{alpha_name}" state mismatch: {"; ".join(issue_parts)}',
                            'expected': f'Exact baseline states: {sorted(baseline_state_names)}',
                            'actual': f'Practice states: {sorted(practice_state_names)}',
                            'suggestion': f'Redeclarations MUST preserve baseline state names exactly. Use baseline states: {sorted(baseline_state_names)}. You can only ADD checklists to existing states, not modify state names or add/remove states.'
                        })
                        has_errors = True

                else:
                    # This is a new alpha - MUST have contributesTo
                    if not has_contributes_to:
                        self.errors.append({
                            'category': 'baseline',
                            'severity': 'error',
                            'practice': practice_name,
                            'path': path,
                            'alpha': alpha_name,
                            'issue': f'New alpha "{alpha_name}" missing contributesTo property',
                            'expected': 'contributesTo: "<BaselineAlphaName>"',
                            'actual': 'No contributesTo property',
                            'suggestion': f'Add contributesTo property pointing to a baseline alpha. All new alphas MUST contribute to a baseline alpha (NO FLOATING ALPHAS). Common mappings: infrastructure → "Platform", consumption interface → "Platform Consumption Interface", workloads → "Platform Asset", governance → "Platform Governance", risk/compliance → "Platform Risk And Compliance".'
                        })
                        has_errors = True

        return not has_errors


def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: validate-practice-json.py <practice.json> <baseline.json> <schema.json>", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print("  validate-practice-json.py practices/my-practice/my-practice.json \\", file=sys.stderr)
        print("                            deps/platform-adoption-kernel.json \\", file=sys.stderr)
        print("                            deps/language.schema.json", file=sys.stderr)
        sys.exit(1)

    practice_file = Path(sys.argv[1])
    baseline_file = Path(sys.argv[2])
    schema_file = Path(sys.argv[3])

    # Validate
    validator = PracticeValidator(practice_file, baseline_file, schema_file)

    # Run all validations
    print("Validating schema...", file=sys.stderr)
    schema_valid = validator.validate_schema()

    print("Validating baseline references...", file=sys.stderr)
    baseline_valid = validator.validate_baseline_references()

    print("Validating redeclaration vs new alpha classification...", file=sys.stderr)
    redeclaration_valid = validator.validate_redeclaration_vs_new()

    print("Validating internal integrity...", file=sys.stderr)
    integrity_valid = validator.validate_internal_integrity()

    print("Validating semantic alignment...", file=sys.stderr)
    semantic_valid = validator.validate_semantic_alignment()

    # Generate report
    report = validator.generate_report()

    # Output JSON report
    print(json.dumps(report, indent=2))

    # Exit code
    sys.exit(0 if report['valid'] else 1)


if __name__ == '__main__':
    main()
