# Migration Scripts

One-off scripts for fixing specific issues in generated JSONs or migrating between schema versions.

## Overview

These scripts address specific problems discovered in generated Practice JSONs. They are **highly context-specific** and often hardcoded to particular practices or issues.

**Important:** These are one-off fixes, not reusable utilities. They represent specific problems encountered and solved during development.

## Scripts

### fix-remaining-alphas.py

**Purpose:** Fix specific alpha-related issues in a Method JSON.

**Context:**
- Specific to Red Hat Ansible Automation Platform method
- Addresses alpha definition problems discovered after initial generation

**Typical Issues Fixed:**
- Missing `contributesTo` relationships
- Floating alphas (new alphas without baseline connections)
- Incorrect focus assignments
- Duplicate alpha definitions across practices
- State checklist incompleteness

**Approach:**
```python
# Load method JSON
method = load_json("practices/my-method/my-method.json")

# Fix specific alphas
for practice in method["practices"]:
    for alpha in practice["alphas"]:
        if alpha["name"] == "Specific Alpha":
            # Apply specific fix
            alpha["contributesTo"] = [...]
```

**Hardcoded Assumptions:**
- Specific method structure
- Known alpha names
- Particular issue patterns

**When It Was Used:**
- After discovering floating alphas via `check-floating-alphas.py`
- When schema validation revealed alpha relationship issues
- During manual QA of generated method

### generate-practice-2-complete.py

**Purpose:** Generate complete Practice 2 JSON for Red Hat AI 3 method with all components.

**Context:**
- Specific to Red Hat AI 3 "Model Lifecycle" practice
- Practice 2 of a 5-practice method
- Complete end-to-end generation for this one practice

**Operations:**
1. Extract practice metadata from `01-practice-details.md`
2. Extract citations from `02-citations.md`
3. Extract alphas from `03-alphas.md` (or split files)
4. Extract work products from `04-workproducts.md`
5. Extract activities, personas, teams from `05-activities-roles.md`
6. Extract patterns from `06-patterns.md`
7. Assemble into complete Practice JSON
8. Validate against cross-reference index
9. Write `practice-2-model-lifecycle.json`

**Why It Exists:**
- Practice 2 had complex module structure (split alphas)
- Initial generation was incomplete
- Needed custom extraction logic for this specific practice
- Served as test case for multi-file alpha handling

**Hardcoded Paths:**
```python
PRACTICE_DIR = Path("practices/red-hat-ai-3/report-elements/practice-2")
OUTPUT_FILE = "practice-2-model-lifecycle.json"
```

**Lessons Applied to Future Work:**
- Handle split alpha modules (03a, 03b, 03c)
- Better inference of contributesTo relationships
- More robust work product LOD extraction
- Improved pattern view activity mapping

## Common Migration Patterns

### Fixing Floating Alphas

**Problem:** New alphas without `contributesTo` relationships.

**Pattern:**
```python
baseline_alphas = {a["name"] for a in baseline["alphas"]}

for alpha in practice["alphas"]:
    if alpha["name"] not in baseline_alphas:
        if "contributesTo" not in alpha or not alpha["contributesTo"]:
            # Add appropriate contributesTo
            alpha["contributesTo"] = [
                {
                    "alphaName": determine_parent_alpha(alpha),
                    "stateName": determine_entry_state(alpha)
                }
            ]
```

### Schema Version Migration

**Problem:** Schema changes require JSON updates.

**Pattern:**
```python
# Old schema
activity["personas"] = [...]

# New schema (property renamed)
activity["involves"] = activity.pop("personas")
```

This pattern is now automated in `utils/fix-property-names.py`.

### Cross-Practice Deduplication

**Problem:** Same element defined in multiple practices.

**Pattern:**
```python
seen_alphas = set()

for practice in method["practices"]:
    unique_alphas = []
    for alpha in practice["alphas"]:
        if alpha["name"] not in seen_alphas:
            unique_alphas.append(alpha)
            seen_alphas.add(alpha["name"])
    practice["alphas"] = unique_alphas
```

## Why These Scripts Are One-Offs

Migration scripts are inherently **non-reusable** because:

1. **Specific Issues** - Each script fixes a particular problem
2. **Hardcoded Paths** - Tied to specific practices/methods
3. **Manual Review** - Require human verification after running
4. **Schema-Specific** - Work with particular schema versions
5. **Historical** - Address problems that no longer occur

**Better Approach:**
When you discover a systematic issue:
1. Fix it in the prompts (Phase 1 or Phase 2)
2. Create a general utility in `utils/` if reusable
3. Document the pattern for future reference
4. Regenerate affected practices from scratch

## From Migration to Prevention

Many issues these scripts fix are now **prevented** by:

**Improved Phase 1 Prompts:**
- Better guidance on alpha relationships
- Explicit contributesTo requirements
- Clearer work product LOD instructions

**Enhanced Phase 2 Prompts:**
- Incremental validation during construction
- Cross-reference index enforcement
- Schema compliance checks at each step

**Permanent Utilities:**
- `fix-property-names.py` - Automates schema property fixes
- `validate-baseline-references.py` - Catches baseline mismatches
- `check-floating-alphas.py` - Detects contributesTo issues

**Result:** Fewer one-off migration scripts needed.

## When to Create Migration Scripts

Create a migration script when:
- **Specific Issue** - Problem is unique to one practice/method
- **Not Generalizable** - Fix logic is too specific for a utility
- **One-Time Fix** - Won't need to run again after fixing
- **Faster Than Regenerating** - Practice is otherwise complete

Create a utility in `utils/` when:
- **Systematic Issue** - Problem affects multiple practices
- **Generalizable** - Fix logic works across different JSONs
- **Recurring** - Will need to run multiple times
- **Schema-Related** - Addresses schema compliance

## Reference Value

These migration scripts serve as **documentation** of:
- Problems encountered during development
- Solutions that worked
- Patterns for fixing JSON issues
- Evolution of the schema and generation approach

Keep them for reference, but **don't use them** for new practices unless facing identical issues.
