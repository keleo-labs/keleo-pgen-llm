#!/usr/bin/env python3
"""
Comprehensive Baseline Practice JSON Validator

Validates Baseline Practice JSON files against:
1. JSON Schema (deps/language.schema.json)
2. Optional parent baseline references (if baseline extends another baseline)
3. Internal cross-reference integrity

Key differences from practice validation:
- Disables "floating alpha" check (baseline alphas are root-level)
- Validates relatesTo completeness (all alphas should have relationships)
- Validates focus/competency/activitySpace definitions (not references)
- Ensures universality (warnings for overly specific terminology)

Outputs structured JSON report for skill consumption.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
from collections import defaultdict
import re

try:
    import jsonschema
    from jsonschema import Draft202012Validator, RefResolver
except ImportError:
    print("ERROR: jsonschema library not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


class BaselineValidator:
    """Validates Baseline Practice JSON against schema and internal refs"""

    def __init__(self, baseline_file: Path, parent_baseline_file: Optional[Path], schema_file: Path):
        self.baseline_file = baseline_file
        self.parent_baseline_file = parent_baseline_file
        self.schema_file = schema_file
        self.errors = []
        self.warnings = []

        # Load files
        self.baseline = self._load_json(baseline_file)
        self.parent_baseline = self._load_json(parent_baseline_file) if parent_baseline_file else None
        self.schema = self._load_json(schema_file)

        # Build parent baseline indexes (if exists)
        self.parent_alphas = {}
        self.parent_alpha_states = defaultdict(set)
        self.parent_competencies = set()
        self.parent_focuses = set()

        if self.parent_baseline:
            self._index_parent_baseline()

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

    def _index_parent_baseline(self):
        """Build indexes of parent baseline elements for validation"""
        if not self.parent_baseline:
            return

        # Index focuses
        for focus in self.parent_baseline.get('focuses', []):
            self.parent_focuses.add(focus['name'])

        # Index alphas and their states
        for alpha in self.parent_baseline.get('alphas', []):
            alpha_name = alpha['name']
            self.parent_alphas[alpha_name] = alpha

            for state in alpha.get('states', []):
                self.parent_alpha_states[alpha_name].add(state['name'])

        # Index competencies
        for comp in self.parent_baseline.get('competencies', []):
            self.parent_competencies.add(comp['name'])

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

            schema_errors = list(validator.iter_errors(self.baseline))

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
                "suggestion": "Check schema file and baseline JSON structure"
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

    def validate_baseline_structure(self) -> bool:
        """Validate baseline-specific structural requirements"""
        has_errors = False

        # Check discriminator
        kind = self.baseline.get('kind')
        if kind not in ['baseline', 'practiceBaseline']:
            self.errors.append({
                "category": "baseline",
                "severity": "error",
                "path": "kind",
                "issue": f"Baseline must have kind='baseline' or 'practiceBaseline', found: {kind}",
                "expected": "baseline or practiceBaseline",
                "actual": kind,
                "suggestion": "Set kind property to 'practiceBaseline'"
            })
            has_errors = True

        # Check required top-level arrays
        required_arrays = ['focuses', 'narrativeTypes', 'alphas', 'activitySpaces', 'competencies']
        for arr_name in required_arrays:
            if arr_name not in self.baseline or not isinstance(self.baseline.get(arr_name), list):
                self.errors.append({
                    "category": "baseline",
                    "severity": "error",
                    "path": arr_name,
                    "issue": f"Baseline must define {arr_name} array",
                    "expected": f"Array of {arr_name}",
                    "actual": type(self.baseline.get(arr_name)).__name__ if arr_name in self.baseline else "missing",
                    "suggestion": f"Add {arr_name} array with foundational elements"
                })
                has_errors = True

        # Check focuses
        focuses = self.baseline.get('focuses', [])
        if len(focuses) < 2 or len(focuses) > 4:
            self.warnings.append({
                "category": "baseline",
                "severity": "warning",
                "path": "focuses",
                "issue": f"Baseline should have 2-4 focuses, found {len(focuses)}",
                "expected": "2-4 focuses",
                "actual": len(focuses),
                "suggestion": "Review focus groupings - typical baselines have 3 focuses"
            })

        return not has_errors

    def validate_alphas(self) -> bool:
        """Validate baseline alpha structure and relationships"""
        has_errors = False
        alphas = self.baseline.get('alphas', [])

        # Build alpha index for relatesTo validation
        alpha_names = {alpha['name'] for alpha in alphas}

        for idx, alpha in enumerate(alphas):
            alpha_name = alpha.get('name', f'<unnamed-{idx}>')
            prefix = f"alphas[{idx}]"

            # Check for contributesTo (should NOT exist in baseline alphas)
            if 'contributesTo' in alpha:
                self.errors.append({
                    "category": "baseline",
                    "severity": "error",
                    "path": f"{prefix}.contributesTo",
                    "issue": f"Baseline alpha '{alpha_name}' has contributesTo property - baseline alphas are root-level",
                    "expected": "No contributesTo property",
                    "actual": alpha.get('contributesTo'),
                    "suggestion": "Remove contributesTo property (baseline alphas are foundational, not specialized)"
                })
                has_errors = True

            # Check for relatesTo (REQUIRED in baseline alphas)
            relates_to = alpha.get('relatesTo', [])
            if not relates_to or len(relates_to) == 0:
                self.warnings.append({
                    "category": "baseline",
                    "severity": "warning",
                    "path": f"{prefix}.relatesTo",
                    "issue": f"Baseline alpha '{alpha_name}' has no relatesTo relationships",
                    "expected": "Array of relatesTo relationships",
                    "actual": "empty or missing",
                    "suggestion": "Document inter-alpha relationships (produces, governed by, uses)"
                })

            # Validate relatesTo references
            for rel_idx, rel in enumerate(relates_to):
                target_alpha = rel.get('alphaName')
                if target_alpha and target_alpha not in alpha_names:
                    # Check if it exists in parent baseline
                    if self.parent_baseline and target_alpha in self.parent_alphas:
                        continue  # Valid reference to parent baseline

                    self.errors.append({
                        "category": "integrity",
                        "severity": "error",
                        "path": f"{prefix}.relatesTo[{rel_idx}].alphaName",
                        "issue": f"relatesTo references unknown alpha: {target_alpha}",
                        "expected": "Alpha name from this baseline or parent baseline",
                        "actual": target_alpha,
                        "suggestion": f"Check spelling or define alpha '{target_alpha}'"
                    })
                    has_errors = True

                # Validate relationship type
                relationship = rel.get('relationship')
                valid_relationships = ['produces', 'governed by', 'uses']
                if relationship and relationship not in valid_relationships:
                    self.warnings.append({
                        "category": "baseline",
                        "severity": "warning",
                        "path": f"{prefix}.relatesTo[{rel_idx}].relationship",
                        "issue": f"Non-standard relationship type: {relationship}",
                        "expected": "produces | governed by | uses",
                        "actual": relationship,
                        "suggestion": "Use standard relationship types for consistency"
                    })

            # Check state count
            states = alpha.get('states', [])
            if len(states) < 5:
                self.warnings.append({
                    "category": "baseline",
                    "severity": "warning",
                    "path": f"{prefix}.states",
                    "issue": f"Alpha '{alpha_name}' has only {len(states)} states",
                    "expected": "5-7 states",
                    "actual": len(states),
                    "suggestion": "Baseline alphas typically have 5-7 progressive states"
                })
            elif len(states) > 7:
                self.warnings.append({
                    "category": "baseline",
                    "severity": "warning",
                    "path": f"{prefix}.states",
                    "issue": f"Alpha '{alpha_name}' has {len(states)} states",
                    "expected": "5-7 states",
                    "actual": len(states),
                    "suggestion": "Consider consolidating states for clarity"
                })

        return not has_errors

    def validate_activity_spaces(self) -> bool:
        """Validate baseline activitySpace structure"""
        has_errors = False
        activity_spaces = self.baseline.get('activitySpaces', [])
        alphas = self.baseline.get('alphas', [])

        # Build alpha-state index
        alpha_states = {}
        for alpha in alphas:
            alpha_name = alpha.get('name')
            if alpha_name:
                alpha_states[alpha_name] = {state.get('name') for state in alpha.get('states', [])}

        # Build competency index
        competencies = {comp.get('name') for comp in self.baseline.get('competencies', [])}

        for idx, asp in enumerate(activity_spaces):
            asp_name = asp.get('name', f'<unnamed-{idx}>')
            prefix = f"activitySpaces[{idx}]"

            # Validate contributesTo references
            contributes_to = asp.get('contributesTo', [])
            for contrib_idx, contrib in enumerate(contributes_to):
                alpha_name = contrib.get('alphaName')
                state_name = contrib.get('stateName')

                if alpha_name and alpha_name not in alpha_states:
                    # Check parent baseline
                    if self.parent_baseline and alpha_name in self.parent_alpha_states:
                        if state_name and state_name not in self.parent_alpha_states[alpha_name]:
                            self.errors.append({
                                "category": "integrity",
                                "severity": "error",
                                "path": f"{prefix}.contributesTo[{contrib_idx}].stateName",
                                "issue": f"Unknown state '{state_name}' for parent alpha '{alpha_name}'",
                                "expected": f"State name from parent alpha '{alpha_name}'",
                                "actual": state_name,
                                "suggestion": f"Check parent baseline alpha '{alpha_name}' states"
                            })
                            has_errors = True
                    else:
                        self.errors.append({
                            "category": "integrity",
                            "severity": "error",
                            "path": f"{prefix}.contributesTo[{contrib_idx}].alphaName",
                            "issue": f"Unknown alpha: {alpha_name}",
                            "expected": "Alpha name from this baseline or parent baseline",
                            "actual": alpha_name,
                            "suggestion": f"Define alpha '{alpha_name}' or check spelling"
                        })
                        has_errors = True
                elif alpha_name and state_name and state_name not in alpha_states.get(alpha_name, set()):
                    self.errors.append({
                        "category": "integrity",
                        "severity": "error",
                        "path": f"{prefix}.contributesTo[{contrib_idx}].stateName",
                        "issue": f"Unknown state '{state_name}' for alpha '{alpha_name}'",
                        "expected": f"State name from alpha '{alpha_name}'",
                        "actual": state_name,
                        "suggestion": f"Check alpha '{alpha_name}' states"
                    })
                    has_errors = True

            # Validate requiredCompetencies references
            required_comps = asp.get('requiredCompetencies', [])
            for comp_name in required_comps:
                if comp_name not in competencies:
                    # Check parent baseline
                    if self.parent_baseline and comp_name in self.parent_competencies:
                        continue  # Valid reference

                    self.errors.append({
                        "category": "integrity",
                        "severity": "error",
                        "path": f"{prefix}.requiredCompetencies",
                        "issue": f"Unknown competency: {comp_name}",
                        "expected": "Competency name from this baseline or parent baseline",
                        "actual": comp_name,
                        "suggestion": f"Define competency '{comp_name}' or check spelling"
                    })
                    has_errors = True

        return not has_errors

    def validate_competencies(self) -> bool:
        """Validate baseline competency structure"""
        has_errors = False
        competencies = self.baseline.get('competencies', [])

        for idx, comp in enumerate(competencies):
            comp_name = comp.get('name', f'<unnamed-{idx}>')
            prefix = f"competencies[{idx}]"

            # Check for 5 levels
            levels = comp.get('levels', [])
            if len(levels) != 5:
                self.errors.append({
                    "category": "baseline",
                    "severity": "error",
                    "path": f"{prefix}.levels",
                    "issue": f"Competency '{comp_name}' has {len(levels)} levels, must have exactly 5",
                    "expected": "5 competency levels",
                    "actual": len(levels),
                    "suggestion": "Baseline competencies must have 5 levels (Basic, Applies, Masters, Adapts, Innovating)"
                })
                has_errors = True
                continue

            # Validate level structure
            expected_levels = [1, 2, 3, 4, 5]
            for level_idx, level in enumerate(levels):
                expected_level_num = expected_levels[level_idx]
                actual_level_num = level.get('level')

                if actual_level_num != expected_level_num:
                    self.errors.append({
                        "category": "baseline",
                        "severity": "error",
                        "path": f"{prefix}.levels[{level_idx}].level",
                        "issue": f"Level number should be {expected_level_num}, found {actual_level_num}",
                        "expected": expected_level_num,
                        "actual": actual_level_num,
                        "suggestion": f"Set level to {expected_level_num}"
                    })
                    has_errors = True

        return not has_errors

    def validate_narrative_types(self) -> bool:
        """Validate baseline narrativeType structure"""
        has_errors = False
        narrative_types = self.baseline.get('narrativeTypes', [])

        for idx, nt in enumerate(narrative_types):
            nt_name = nt.get('name', f'<unnamed-{idx}>')
            prefix = f"narrativeTypes[{idx}]"

            # Check for kind discriminator
            kind = nt.get('kind')
            if kind != 'narrativeType':
                self.errors.append({
                    "category": "baseline",
                    "severity": "error",
                    "path": f"{prefix}.kind",
                    "issue": f"NarrativeType must have kind='narrativeType', found: {kind}",
                    "expected": "narrativeType",
                    "actual": kind,
                    "suggestion": "Set kind property to 'narrativeType'"
                })
                has_errors = True

            # Check for narrative elements
            elements = nt.get('narrativeElements', [])
            if len(elements) < 3:
                self.warnings.append({
                    "category": "baseline",
                    "severity": "warning",
                    "path": f"{prefix}.narrativeElements",
                    "issue": f"NarrativeType '{nt_name}' has only {len(elements)} elements",
                    "expected": "3-7 narrative elements",
                    "actual": len(elements),
                    "suggestion": "Narrative types typically have 3-7 sequential elements"
                })

            # Validate element structure
            for elem_idx, elem in enumerate(elements):
                required_fields = ['name', 'description', 'howToUse']
                for field in required_fields:
                    if field not in elem or not elem.get(field):
                        self.errors.append({
                            "category": "baseline",
                            "severity": "error",
                            "path": f"{prefix}.narrativeElements[{elem_idx}].{field}",
                            "issue": f"Narrative element missing required field: {field}",
                            "expected": "Non-empty string",
                            "actual": elem.get(field, "missing"),
                            "suggestion": f"Add {field} property to narrative element"
                        })
                        has_errors = True

        return not has_errors

    def validate_universality(self) -> None:
        """Check for overly specific terminology (warnings only)"""
        # Patterns indicating vendor/tool-specific naming
        vendor_patterns = [
            r'\b(AWS|Azure|GCP|Google Cloud)\b',
            r'\b(Kubernetes|Docker|Terraform)\b',
            r'\b(Jira|Confluence|ServiceNow)\b',
            r'\b(Jenkins|GitLab|GitHub Actions)\b'
        ]

        alphas = self.baseline.get('alphas', [])
        for idx, alpha in enumerate(alphas):
            alpha_name = alpha.get('name', '')
            for pattern in vendor_patterns:
                if re.search(pattern, alpha_name, re.IGNORECASE):
                    self.warnings.append({
                        "category": "universality",
                        "severity": "warning",
                        "path": f"alphas[{idx}].name",
                        "issue": f"Alpha name contains vendor/tool-specific term: {alpha_name}",
                        "expected": "Vendor-neutral, framework-level terminology",
                        "actual": alpha_name,
                        "suggestion": "Consider more general naming (e.g., 'Container Orchestration' instead of 'Kubernetes')"
                    })

    def validate(self) -> Dict[str, Any]:
        """Run all validations and return structured report"""
        # Clear previous results
        self.errors = []
        self.warnings = []

        # Run validations
        schema_valid = self.validate_schema()
        structure_valid = self.validate_baseline_structure()
        alphas_valid = self.validate_alphas()
        activity_spaces_valid = self.validate_activity_spaces()
        competencies_valid = self.validate_competencies()
        narrative_types_valid = self.validate_narrative_types()

        # Universality is warnings only
        self.validate_universality()

        # Overall validity
        is_valid = (
            schema_valid and
            structure_valid and
            alphas_valid and
            activity_spaces_valid and
            competencies_valid and
            narrative_types_valid
        )

        # Build report
        report = {
            "valid": is_valid,
            "file": str(self.baseline_file),
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "schema_valid": schema_valid,
                "structure_valid": structure_valid,
                "alphas_valid": alphas_valid,
                "activity_spaces_valid": activity_spaces_valid,
                "competencies_valid": competencies_valid,
                "narrative_types_valid": narrative_types_valid
            }
        }

        return report


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: validate-baseline-json.py <baseline.json> [parent-baseline.json] <schema.json>", file=sys.stderr)
        print("\nValidates baseline practice JSON against schema and internal integrity", file=sys.stderr)
        print("\nArguments:", file=sys.stderr)
        print("  baseline.json          : Baseline practice JSON file to validate", file=sys.stderr)
        print("  parent-baseline.json   : (Optional) Parent baseline if this baseline extends another", file=sys.stderr)
        print("  schema.json            : Practice Language JSON schema file", file=sys.stderr)
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) == 3:
        # baseline.json schema.json
        baseline_file = Path(sys.argv[1])
        parent_baseline_file = None
        schema_file = Path(sys.argv[2])
    else:
        # baseline.json parent-baseline.json schema.json
        baseline_file = Path(sys.argv[1])
        parent_baseline_file = Path(sys.argv[2])
        schema_file = Path(sys.argv[3])

    # Validate
    validator = BaselineValidator(baseline_file, parent_baseline_file, schema_file)
    report = validator.validate()

    # Output JSON report
    print(json.dumps(report, indent=2))

    # Exit code
    sys.exit(0 if report['valid'] else 1)


if __name__ == '__main__':
    main()
