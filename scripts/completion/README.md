# Completion Scripts

Scripts for completing, finalizing, and enriching partial Practice JSONs during iterative development.

## Overview

These scripts were used to fill in missing elements in partially-generated Practice JSONs. They represent different approaches to completing JSONs when the initial generation was incomplete or when specific elements needed to be added or fixed.

**Note:** The current `/translate-methodology` skill produces complete JSONs in a single pass. These scripts are primarily historical artifacts from iterative development.

## Scripts

### complete-all.py

**Purpose:** Complete all missing components in a Method JSON with multiple practices.

**Context:**
- Hardcoded for Red Hat Ansible Automation Platform method
- Fills in activities, personas, and teams across practices
- Uses extraction from Phase 1 modules to add missing elements

**Key Operations:**
- Extracts activities from `05-activities-roles.md`
- Extracts personas and competencies
- Extracts teams with composition
- Merges with existing partial JSON

**Hardcoded Paths:**
```python
method = json.load(open("practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json"))
```

**Limitations:**
- Specific to one method
- Assumes particular module structure
- No validation of merged results
- May create duplicate elements

### complete-extraction.py

**Purpose:** Complete extraction of activities and roles from Phase 1 modules.

**Approach:**
- Reads `05-activities-roles.md` comprehensively
- Extracts full activity definitions with:
  - Technique narratives
  - Competency requirements
  - Persona involvement
  - Work product relationships

**Features:**
- More thorough than initial extraction
- Handles complex activity descriptions
- Attempts to infer contributesTo relationships
- Extracts embedded personas

**Use Case:**
When initial Phase 2 generation produced minimal activities, this script re-extracted them from the Phase 1 source with more detail.

### final-complete.py

**Purpose:** Final completion pass for Red Hat Ansible Automation Platform method.

**Operations:**
- Loads existing method JSON
- Loads cross-reference index
- Adds missing activities to specific practices
- Fills in activity relationships (contributesTo, worksOn)
- Completes persona competency mappings

**Approach:**
- Targeted fixes rather than full re-extraction
- Preserves existing correct elements
- Adds only what's missing
- Uses cross-reference index for validation

**Typical Workflow:**
1. Generate initial JSON via Phase 2
2. Identify missing activities/personas
3. Run this script to fill gaps
4. Manually review and adjust
5. Validate against schema

### final-extraction.py

**Purpose:** Final extraction pass with comprehensive activity and persona details.

**Distinguishing Features:**
- Most comprehensive extraction logic
- Handles nested persona descriptions
- Extracts full technique narratives (STAR/StoryBrand/etc.)
- Better inference of alpha state progressions

**Extraction Improvements:**
- Multi-line description handling
- Better regex patterns for complex formats
- Competency level extraction from narratives
- Team composition parsing

**When It Was Used:**
- Final quality pass before declaring a practice "complete"
- After identifying specific extraction gaps
- To add rich narratives that were missing

## Common Patterns

All completion scripts follow similar patterns:

**1. Load Existing JSON:**
```python
method = json.load(open("path/to/method.json"))
```

**2. Load Cross-Reference Index:**
```python
index = json.load(open("path/to/cross-reference-index.json"))
```

**3. Extract Missing Elements:**
```python
activities = extract_acts(module_path)
personas = extract_pers(module_path)
teams = extract_groups(module_path, practice_key)
```

**4. Merge into Existing Structure:**
```python
practice["activities"].extend(new_activities)
practice["personas"].extend(new_personas)
```

**5. Write Updated JSON:**
```python
with open("path/to/method.json", "w") as f:
    json.dump(method, f, indent=2)
```

## Why Multiple Completion Scripts?

During development, we encountered different incompleteness scenarios:

1. **complete-all.py** - Initial attempt, added everything broadly
2. **complete-extraction.py** - More targeted, better extraction logic
3. **final-complete.py** - Surgical fixes for specific gaps
4. **final-extraction.py** - Ultimate version with best extraction

Each script represents learning and refinement of the completion approach.

## Lessons Learned

These completion scripts taught us:

**1. One-Pass Generation is Better**
- Iterative completion is error-prone
- Better to generate complete JSON initially
- Led to improved Phase 2 prompt

**2. Validation is Essential**
- Must validate after each merge
- Cross-reference index is critical
- Schema validation catches structural issues

**3. Preserve Existing Work**
- Don't regenerate what's already correct
- Merge carefully to avoid duplicates
- Use element names for deduplication

**4. Module Quality Matters**
- Complete Phase 1 modules → complete Phase 2 JSON
- Gaps in modules → gaps in JSON
- Better to improve module generation

## Current Workflow

The current `/translate-methodology` skill avoids needing these scripts by:

1. **Comprehensive Phase 1** - Modular prompts ensure complete coverage
2. **Incremental Phase 2** - Build JSON section by section with validation
3. **Self-Contained Prompts** - Each phase has all context it needs
4. **Multi-Stage Validation** - Catch incompleteness early

**Result:** These completion scripts are rarely needed anymore.

## When to Use These Scripts

Consider using these scripts when:
- **Recovery** - Phase 2 failed partway through, have partial JSON
- **Incremental fixes** - Know exactly what's missing, want surgical addition
- **Reference** - Understanding how to merge extracted elements
- **Debugging** - Comparing different extraction approaches

For normal workflow, regenerate via `/translate-methodology` instead of patching incomplete JSONs.
