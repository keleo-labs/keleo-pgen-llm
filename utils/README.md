# Practice Language Utilities

Utility scripts for working with Practice Language JSON files.

## fix-property-names.py

**Purpose:** Automatically fix property name mismatches to ensure schema compliance.

**Usage:**
```bash
# Fix all JSON files in current directory
python3 fix-property-names.py

# Fix specific files
python3 fix-property-names.py practice-1.json practice-2.json
```

**What it fixes:**

| Component | Incorrect Property | Correct Property |
|-----------|-------------------|------------------|
| Activity | `outcomes` | `contributesTo` |
| Activity | `focus` | `focusName` |
| Activity | `competencies` | `recommendedCompetencyLevels` |
| Activity | (missing) | `requiredCompetencies` (auto-generated) |
| Activity | `personas` | `involves` |
| Activity | `workProductsUsed` | `worksOn` |
| Pattern | `views` | `patternViews` |
| Pattern | `narrativeFramework` | `narrativeTypeName` |
| Pattern | `type` | (removed - not in schema) |
| PatternView | `activitiesEmphasized` | `activities` |
| PatternView | `alphaStateProgressions` | `alphaStates` |

**When to use:**
- Automatically run by `/generate-method` skill after Phase 2
- After manual edits to JSON files that may have introduced naming issues
- Before schema validation

---

## validate-baseline-references.py

**Purpose:** Validate all baseline practice references and automatically fix incorrect competency/state/alpha names.

**Usage:**
```bash
# Validate all practice JSON files in current directory
python3 validate-baseline-references.py

# Script auto-discovers practice-*.json files (excluding *-enriched.json)
```

**What it validates:**

| Component | Validation |
|-----------|------------|
| Competencies | Must use canonical baseline names (8 total) |
| Alphas | Must reference baseline or practice-defined alphas (13 baseline) |
| States | Must exist in target alpha's state list |
| Focuses | Must be Value, Solution, or Endeavor |
| ActivitySpaces | Must match baseline names (20 total) |

**What it fixes automatically:**

| Issue Type | Fix Example |
|------------|-------------|
| Competency descriptions | `"Machine Learning (model dev...)"` → `"Engineering"` |
| Invalid competency terms | `"Model Risk Management"` → `"Management"` |
| Invalid state names | `"Provisioned"` → `"Configured"` (for Serving Runtime) |
| Invalid state names | `"In Use"` → `"Performing"` (for Team) |

**Competency mappings:**
- Machine Learning, ML Engineering, Platform Engineering, Software Development → Engineering
- Statistics and Experimentation, ML Evaluation, Requirements Engineering → Analysis
- Model Risk Management, Data Governance, Governance and Audit → Management
- Regulatory Compliance, Security → Platform Security And Compliance Enforcement

**State mappings:**
- Context-aware (varies by alpha)
- Example: "Provisioned" → "Configured" for Serving Runtime, "Prepared" for Work
- Example: "In Use" → "Performing" for Team, "Available" for Inference Endpoint

**When to use:**
- Automatically run by `/generate-method` skill after Phase 2.5
- After manual edits to JSON files
- Before schema validation
- When adding new personas or activities

**Output:**
- Modifies practice JSON files in-place
- Reports all fixes applied
- Suggests running `rebuild-method-json.py` if changes were made

---

## validate-internal-integrity.py

**Purpose:** Validate internal referential integrity of a Method JSON, ensuring all cross-references between elements are valid.

**Usage:**
```bash
# Validate method JSON in current directory
python3 validate-internal-integrity.py

# Looks for red-hat-ai-3.json (or modify script for other method files)
```

**What it validates:**

| Reference Type | Validation |
|----------------|------------|
| Activity → Alpha/State | `contributesTo` references existing alphas and their states |
| Activity → Work Product | `worksOn` references existing work products |
| Pattern View → Activity | Pattern views reference existing activities |
| Pattern View → Alpha/State | Pattern views reference valid alpha states |

**Element Index Built:**
- All alphas (baseline + practice-defined) with their states
- All work products across all practices
- All activities across all practices
- All patterns across all practices
- All personas and teams

**Cross-Practice Validation:**
- Merges elements across all practices in a method
- Validates references can cross practice boundaries
- Ensures pattern views correctly reference activities from all practices

**When to use:**
- Automatically run by `/generate-method` skill after Phase 2.6
- After manually modifying a method JSON
- Before publishing or sharing a method
- To diagnose broken references
- As a quality assurance check

**Output:**
- Console report with validation results
- `INTERNAL-INTEGRITY-REPORT.md` with detailed element inventory and any issues found
- Exit code 0 if all references valid, 1 if issues found

**Example Output:**
```
Element Index:
  Alphas: 27 (134 total states)
  Work Products: 37
  Activities: 57
  Patterns: 14
  Personas: 17
  Teams: 1

✓ All internal references validated
```

---

## validate-cross-practice-integrity.py

**Purpose:** Validate cross-practice referential integrity for multi-practice methods, ensuring all references between practices are consistent and valid.

**Usage:**
```bash
# Run from method directory (e.g., practices/red-hat-ai-3/)
cd practices/my-method/
python3 ../../utils/validate-cross-practice-integrity.py

# Or run from repo root
cd /path/to/keleo-pgen-llm
python3 utils/validate-cross-practice-integrity.py
```

**What it validates:**

| Validation Type | Description |
| --------------- | ----------- |
| **Method-Practice Alignment** | Method's `practiceNames` matches actual practice JSON names |
| **Cross-Practice Alpha References** | Activities in one practice can reference alphas from other practices |
| **Cross-Practice Work Product References** | Activities can reference work products from other practices |
| **Baseline References** | All baseline alpha/competency/activity space references are valid |
| **State Consistency** | Referenced states exist in their target alphas |
| **Element Uniqueness** | No duplicate alphas, work products, or activities across practices |

**Method Structure Validated:**
```json
{
  "name": "Method Name",
  "practiceNames": ["Practice 1", "Practice 2", "Practice 3"],
  "practices": [
    { "name": "Practice 1", "alphas": [...], "activities": [...] },
    { "name": "Practice 2", "alphas": [...], "activities": [...] },
    { "name": "Practice 3", "alphas": [...], "activities": [...] }
  ]
}
```

**Validation Process:**

1. **Load Method JSON** - Read method file and all practice files
2. **Build Global Index** - Create unified index of all elements across all practices
3. **Validate Baseline** - Check all baseline references (alphas, competencies, activity spaces)
4. **Validate Cross-References** - Check activity → alpha/state, activity → work product, pattern → activity
5. **Check Uniqueness** - Ensure no duplicate element names across practices
6. **Report Issues** - Detailed report of any violations found

**Example Output:**
```
=== Cross-Practice Referential Integrity Validation ===

Method: Red Hat AI 3
Practice Names: Platform Management, Model Lifecycle, Model Development, Inference, Agentic AI

Aggregated Element Counts:
  Baseline Alphas: 13
  Practice Alphas: 27 (across 5 practices)
  Total States: 134
  Work Products: 37
  Activities: 57
  Patterns: 14
  Personas: 17
  Teams: 1

✓ All baseline alpha references valid (13 baseline alphas found)
✓ All baseline competency references valid (8 competencies)
✓ All baseline activity space references valid (20 spaces)
✓ All cross-practice alpha/state references valid
✓ All cross-practice work product references valid
✓ No duplicate element names found

=== VALIDATION PASSED ===
All cross-practice references are valid!
```

**When to use:**

- After generating a multi-practice method
- Before publishing or sharing a method
- When troubleshooting cross-practice reference errors
- As final validation step in method development

**Differences from validate-internal-integrity.py:**

| Feature | validate-internal-integrity.py | validate-cross-practice-integrity.py |
| ------- | ------------------------------ | ------------------------------------ |
| **Scope** | Single method JSON (all-in-one) | Method + separate practice JSON files |
| **Input** | One JSON file | Method JSON + multiple practice JSONs |
| **Validation** | Internal references only | Cross-practice + baseline references |
| **Use Case** | After Phase 2.7 in skill | Manual multi-file validation |

**Typical Workflow:**
```bash
# 1. Generate method via skill
/generate-method [sources]

# 2. If you have separate practice files (not typical), validate cross-practice integrity
cd practices/my-method/
python3 ../../utils/validate-cross-practice-integrity.py

# 3. Fix any issues reported
# 4. Rebuild method JSON if needed
python3 ../../utils/rebuild-method-json.py
```

**Note:** This utility is primarily for development scenarios where practices are maintained as separate files. The `/generate-method` skill typically produces a single unified method JSON, which is validated by `validate-internal-integrity.py` instead.

---

## check-floating-alphas.py

**Purpose:** Check for floating alphas (new alphas without `contributesTo` relationships), which are strictly prohibited by the Practice Language semantics.

**Usage:**
```bash
# Check a practice or method JSON file
python3 check-floating-alphas.py practices/my-practice/my-practice.json

# Or run from the project root
python3 utils/check-floating-alphas.py practices/my-method/my-method.json
```

**What it checks:**

**CRITICAL RULE - NO FLOATING ALPHAS:**
According to `references/semantics.md`, all new alphas introduced in a Practice MUST logically refine a parent concept by explicitly declaring a `contributesTo` relationship. This must match a canonical Alpha name from the baseline practice.

**Baseline Alphas (13 total):**
- Opportunity, Organizational Change, Platform, Platform Asset
- Platform Consumption Interface, Platform Governance
- Platform Risk And Compliance, Platform Value And Economics
- Requirements, Stakeholders, Team, Way Of Working, Work

**Validation Logic:**
1. Load all 13 baseline alpha names from `deps/platform-adoption-kernel.json`
2. For each alpha in the practice/method:
   - If alpha name is NOT in baseline alphas
   - AND alpha has no `contributesTo` or empty `contributesTo`
   - THEN it's a floating alpha (violation)

**Example Output:**
```
Found 13 baseline alphas

Checking Method: Red Hat Ansible Automation Platform

Practice: Platform Administration & Operations
  ❌ FLOATING ALPHAS (new alphas without contributesTo):
     - Automation Platform
     - Automation Mesh
     - Execution Environment Repository
     - Platform Performance
```

**How to Fix Floating Alphas:**

If floating alphas are found, update the practice JSON to add appropriate `contributesTo` relationships:

- Technology/infrastructure alphas → `"Platform"`
- Content/artifact alphas → `"Platform Asset"`
- Process/workflow alphas → `"Work"`
- Governance alphas → `"Platform Governance"`
- Risk/compliance alphas → `"Platform Risk And Compliance"`
- Value/economics alphas → `"Platform Value And Economics"`

**Example Fix:**
```json
{
  "name": "Automation Platform",
  "description": "...",
  "focusName": "Solution",
  "contributesTo": [
    {
      "alphaName": "Platform",
      "stateName": "Architecture Selected"
    }
  ],
  "states": [...]
}
```

**When to use:**
- Before publishing a practice or method
- After generating JSON to verify compliance
- When troubleshooting why a practice doesn't match baseline expectations
- As a quality assurance check

---

## rebuild-method-json.py

**Purpose:** Rebuild complete Method JSON from individual practice JSON files.

**Usage:**
```bash
# Auto-discover method and practice files in current directory
python3 rebuild-method-json.py

# Specify files explicitly
python3 rebuild-method-json.py method-name.json practice-1.json practice-2.json
```

**What it does:**
1. Reads method-level metadata from the method JSON file
2. Reads all individual practice JSON files
3. Assembles complete Method object with `practices` array
4. Writes complete Method JSON

**When to use:**
- After running `fix-property-names.py` on individual practice files
- After manually editing individual practice JSON files
- When the Method JSON needs to be regenerated from its components

**Expected files:**
- One method JSON file (e.g., `red-hat-ai-3.json`)
- Multiple practice JSON files (e.g., `practice-1-platform.json`, `practice-2-lifecycle.json`)

---

## Typical Workflow

For a Method with multiple practices:

```bash
# 1. Generate JSON via /generate-method skill
# (Phases 1, 1.5, 2, 2.5, 2.6, and 2.7 complete - all automatic)

# 2. If manual edits are needed, re-run validation:
cd practices/my-method/
python3 fix-property-names.py
python3 validate-baseline-references.py
python3 rebuild-method-json.py
python3 validate-internal-integrity.py

# 3. Validate against schema (if ajv-cli installed)
ajv validate -s ../../deps/language.schema.json -d my-method.json

# 4. Use the fully validated JSON
```

For a single Practice:

```bash
# 1. Generate JSON via /generate-method skill
# (Phases 1, 1.5, 2, 2.5, 2.6, and 2.7 complete - all automatic)

# 2. If manual edits are needed, re-run validation:
cd practices/my-practice/
python3 fix-property-names.py
python3 validate-baseline-references.py
python3 validate-internal-integrity.py

# 3. Validate against schema (if ajv-cli installed)
ajv validate -s ../../deps/language.schema.json -d my-practice.json

# 4. Use the fully validated JSON
```

---

## Integration with /generate-method Skill

These utilities are automatically integrated into the `/generate-method` skill:

**Phase 2.5 (Schema Compliance):**
1. The skill copies utility scripts to the practice directory
2. Runs `fix-property-names.py` on all generated JSON files
3. For Methods, runs `rebuild-method-json.py` to assemble complete Method JSON
4. Verifies schema compliance

**Phase 2.6 (Baseline Validation):**
1. Runs `validate-baseline-references.py` on all practice files
2. Automatically fixes competency descriptions, invalid state names, incorrect references
3. For Methods, runs `rebuild-method-json.py` after validation fixes
4. Verifies all baseline references are correct

**Phase 2.7 (Internal Integrity):**
1. Runs `validate-internal-integrity.py` on the method JSON
2. Validates all internal cross-references
3. Generates `INTERNAL-INTEGRITY-REPORT.md` with detailed diagnostics
4. Reports success or issues to user (manual fixes needed if issues found)

This ensures that all generated JSON is:
- 100% schema-compliant (correct property names and structure)
- 100% baseline-validated (correct competency/alpha/state references)
- 100% internally consistent (all cross-references valid)
- Ready for immediate use without manual intervention
