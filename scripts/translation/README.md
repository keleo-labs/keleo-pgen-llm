# Translation Scripts

Early experiments in translating Phase 1 markdown modules to schema-compliant JSON.

## Overview

These scripts represent **early approaches** to Phase 2 translation before the current modular LLM-based approach was developed. They combine regex extraction with template-based JSON construction.

**Note:** These scripts are superseded by `prompts/phase-2-modular.md`, which uses LLM-based semantic translation instead of regex parsing.

## Scripts

### translate-method-to-json.py

**Purpose:** Translate complete Red Hat Ansible Automation Platform method from Phase 1 modules to Method JSON.

**Context:**
- First multi-practice method translation
- Handles 2 practices in a single Method object
- Combines extraction + assembly + validation

**Approach:**

**1. Load Resources:**
```python
BASE_DIR = Path("practices/red-hat-ansible-automation-platform")
PRACTICE_1_DIR = BASE_DIR / "report-elements" / "practice-1"
PRACTICE_2_DIR = BASE_DIR / "report-elements" / "practice-2"
DEPS_DIR = Path("deps")
```

**2. Extract Practice Metadata:**
- Read `01-practice-details.md` for each practice
- Parse name, description, authors, dates, version
- Extract domain tags, lifecycle phases, organizational scopes

**3. Extract Components:**
- Citations from `02-citations.md`
- Alphas from `03-alphas.md`
- Work Products from `04-workproducts.md`
- Activities, Personas, Teams from `05-activities-roles.md`
- Patterns from `06-patterns.md`

**4. Assemble Method:**
```python
method = {
    "name": "Red Hat Ansible Automation Platform",
    "practiceNames": [practice1["name"], practice2["name"]],
    "practices": [practice1, practice2],
    ...
}
```

**5. Validate and Write:**
- Check cross-references
- Validate against baseline
- Write `red-hat-ansible-automation-platform.json`

**Hardcoded Paths:**
- Specific to Red Hat Ansible Automation Platform method
- Fixed practice directory structure
- Assumes particular module naming

### translate-method-phase2.py

**Purpose:** Phase 2 translation with enhanced extraction logic and validation.

**Improvements Over First Version:**

**Better Extraction:**
- More robust regex patterns
- Handles split alpha files (03a, 03b, 03c)
- Better narrative extraction
- Improved persona/team parsing

**Enhanced Validation:**
- Cross-reference index checking
- Baseline alpha verification
- State name validation
- Competency matching

**Incremental Assembly:**
- Build JSON section by section
- Validate each section before proceeding
- Report progress and issues
- Better error messages

**Key Features:**

**1. Modular Extraction:**
```python
def extract_practice_metadata(practice_dir: Path) -> Dict[str, Any]:
    """Extract practice metadata from 01-practice-details.md"""
    
def extract_citations(practice_dir: Path) -> List[Dict[str, Any]]:
    """Extract citations from 02-citations.md"""
    
def extract_alphas(practice_dir: Path, baseline: Dict) -> List[Dict[str, Any]]:
    """Extract alphas from 03-*.md with baseline merging"""
```

**2. Cross-Reference Validation:**
```python
def validate_references(practice: Dict, index: Dict) -> List[str]:
    """Validate all element references against index"""
    issues = []
    for activity in practice["activities"]:
        for ref in activity["contributesTo"]:
            if ref["alphaName"] not in index["alphas"]:
                issues.append(f"Unknown alpha: {ref['alphaName']}")
    return issues
```

**3. Progressive Assembly:**
- Extract citations → validate
- Extract alphas → validate against baseline
- Extract work products → validate alpha/state refs
- Extract activities → validate all refs
- Extract patterns → validate activity refs
- Assemble complete practice
- Final validation pass

## Evolution to Current Approach

These scripts informed the development of the current Phase 2 approach:

### What Worked

**Incremental Assembly:**
- Building JSON section by section
- Validating after each section
- Reporting progress

**Cross-Reference Validation:**
- Using index for validation
- Checking baseline references
- Verifying state names

**Modular Extraction:**
- Separate functions for each component
- Clean separation of concerns
- Reusable extraction logic

### What Didn't Work

**Regex-Based Parsing:**
- Brittle with format variations
- Missed complex narratives
- Hard to maintain
- Poor error messages

**Template-Based Assembly:**
- Couldn't handle unexpected structures
- Required extensive hardcoding
- Difficult to adapt to new practices

**Linear Processing:**
- Couldn't iterate on ambiguities
- No semantic understanding
- Couldn't make contextual decisions

### Current LLM-Based Approach

The current `prompts/phase-2-modular.md` combines the best patterns with LLM capabilities:

**Keeps from Scripts:**
- ✓ Incremental section-by-section assembly
- ✓ Validation after each section
- ✓ Cross-reference index checking
- ✓ Baseline reference verification
- ✓ Progress reporting

**Improves via LLM:**
- ✓ Semantic understanding vs regex
- ✓ Contextual decision making
- ✓ Robust to format variations
- ✓ Rich narrative extraction
- ✓ Self-correction based on validation

## Architecture Insights

### Translation Pipeline Pattern

Both scripts follow this pattern:

```
Phase 1 Modules
      ↓
[Read Module Files]
      ↓
[Extract Components] ← Baseline Framework
      ↓
[Build JSON Structure] ← Schema Template
      ↓
[Validate References] ← Cross-Reference Index
      ↓
[Write JSON File]
      ↓
Schema-Compliant JSON
```

This pattern is preserved in the current LLM-based approach.

### Validation Stages

Multiple validation stages proved essential:

1. **Component-Level:** Validate each alpha/work product as extracted
2. **Section-Level:** Validate citations, then alphas, then work products, etc.
3. **Cross-Reference:** Validate references between elements
4. **Baseline:** Validate baseline alpha/competency references
5. **Schema:** Validate final JSON against schema

Current workflow maintains all five stages.

### Incremental Construction Benefits

Building incrementally proved superior to all-at-once:

- Easier to debug issues
- Can stop and fix problems early
- Better progress visibility
- Smaller context windows per step
- Validation failures are more specific

Current Phase 2 prompt uses the same incremental approach.

## When to Reference These Scripts

Use these scripts as reference when:

**Understanding Translation Logic:**
- See how components map from markdown to JSON
- Understand validation requirements
- Learn section assembly order

**Debugging Extraction:**
- Compare regex patterns to your module format
- Understand what data is needed from each module
- See how baseline merging works

**Developing Custom Translation:**
- Starting point for non-standard methodologies
- Adapting extraction for different formats
- Building custom validation logic

**Not for Production:**
These scripts should **not** be used for normal translation. Use the `/translate-methodology` skill instead.

## Historical Value

These scripts represent important milestones:

1. **First successful multi-practice method translation**
2. **Proof that modular approach works**
3. **Validation that incremental assembly is superior**
4. **Evidence that cross-reference index is essential**

They validated the architecture before committing to the LLM-based implementation.

## Lessons for Future Development

If developing new translation capabilities:

**Do:**
- ✓ Validate incrementally
- ✓ Use cross-reference index
- ✓ Check baseline references
- ✓ Report progress clearly
- ✓ Build section by section

**Don't:**
- ✗ Try to extract everything at once
- ✗ Skip validation between sections
- ✗ Ignore baseline framework
- ✗ Hard-code practice-specific logic
- ✗ Assume markdown format is fixed

These principles apply whether using scripts or LLM prompts.
