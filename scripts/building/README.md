# Building Scripts

Scripts for constructing Practice JSON structures from extracted components during early pipeline development.

## Overview

These scripts represent early experiments in building schema-compliant Practice JSONs from Phase 1 modules. They use simplified extraction and construction logic to create "good enough" JSONs quickly.

**Note:** The current workflow uses the comprehensive Phase 2 modular prompt (`prompts/phase-2-modular.md`) which produces higher-quality, fully-validated JSONs.

## Scripts

### build-practice-json.py

**Purpose:** Build a simplified but schema-compliant Practice JSON from Phase 1 modules.

**Approach:**
- Reads practice details from `01-practice-details.md`
- Extracts basic metadata (name, description, keywords)
- Creates minimal Practice structure with:
  - Practice metadata
  - Empty or stub arrays for alphas, work products, activities
  - Basic citation extraction

**Usage:**
```python
from build_practice_json import build_practice_json

practice = build_practice_json(
    practice_num=1,
    practice_name="Platform Management",
    base_path=Path("practices/my-method/report-elements")
)
```

**Limitations:**
- Creates incomplete JSONs (missing most elements)
- Minimal validation
- Requires manual completion
- Not suitable for production use

**When It's Useful:**
- Quick scaffolding for a Practice JSON structure
- Testing schema structure without full content
- Starting point for manual JSON authoring

### build-complete-practice.py

**Purpose:** Build a more complete Practice JSON with extracted components.

**Approach:**
- Uses extraction scripts to pull alphas, work products, activities
- Assembles components into full Practice structure
- Performs basic validation against cross-reference index
- Attempts to resolve relationships between elements

**Key Features:**
- Orchestrates multiple extraction steps
- Handles both redeclared and new alphas
- Extracts work products with LODs
- Creates activity structures with competencies
- Basic persona and team extraction

**Hardcoded Assumptions:**
- Specific practice directory structure
- Fixed module file naming
- Particular cross-reference index format
- Red Hat Ansible Automation Platform method structure

**Usage:**
```bash
# Edit script to set practice paths and names
python3 build-complete-practice.py
```

**Output:**
- Schema-compliant Practice JSON
- Console output with extraction progress
- Validation warnings for missing references

**Limitations:**
- Still requires manual review and fixes
- May miss complex relationships
- Hardcoded to specific practice structures
- Less comprehensive than LLM-based Phase 2

## Evolution to Current Approach

These building scripts informed the development of the modular Phase 2 prompt:

**What We Learned:**
1. **Incremental construction** - Build JSON section by section (citations → alphas → work products → activities → patterns)
2. **Validation at each step** - Check references before moving to next section
3. **Cross-reference index** - Essential for validating element relationships
4. **Schema compliance** - Property names and structure must be exact

**Current Approach:**
The Phase 2 modular prompt (`prompts/phase-2-modular.md`) uses these insights but with LLM-based assembly:
- Reads modules directly (not extracted components)
- Builds JSON incrementally with validation
- Uses semantic understanding for relationships
- Self-corrects based on schema violations

## When to Use These Scripts

Consider using these scripts when:
- **Rapid prototyping** - Need a quick JSON structure for testing
- **Manual authoring** - Want a scaffold to fill in manually
- **Understanding structure** - Learning how Practice JSON is organized
- **Debugging** - Comparing script output to LLM output

For production use, rely on the `/translate-methodology` skill with Phase 2 modular translation.

## Comparison: Script vs LLM Approach

| Aspect | Building Scripts | Phase 2 LLM Prompt |
|--------|------------------|-------------------|
| **Extraction** | Regex-based, brittle | Semantic, robust |
| **Relationships** | Basic pattern matching | Contextual understanding |
| **Narratives** | Often incomplete | Full technique narratives |
| **Validation** | Basic reference checks | Multi-stage validation |
| **Completeness** | 60-80% complete | 95%+ complete |
| **Manual fixes** | Extensive | Minimal |
| **Speed** | Fast (seconds) | Slower (minutes) |
| **Quality** | Good enough for testing | Production-ready |
