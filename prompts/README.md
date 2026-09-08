# Prompts for generate-method

This directory contains the three-phase prompt system for the `generate-method` skill.

## Architecture

The v2 workflow uses a simplified 3-phase pipeline:

```
Phase 1: Analysis → Phase 2: Mapping → Phase 3: JSON
```

## Phase Prompts

### Phase 1: Analysis
**File:** `phase-1-analysis.md`

Analyzes source methodology documentation and structures it into:
- Outcomes and concerns
- Activities and workflows
- Practices and value streams
- Four-perspective analysis (Business, Technology, People, Process)

**Output:** `01-analysis-report.md` (~30-50K words)

### Phase 2: Mapping
**File:** `phase-2-mapping.md`

Maps analyzed elements to the baseline practice using Practice Language semantics:
- Reads `references/semantics/` sub-documents for semantic guidance
- Maps to baseline alphas, states, activities, work products
- Creates citation mappings
- Defines personas and teams

**Output:** `02-mapping-guide.md` (~40-60K words)

### Phase 3: JSON Generation
**File:** `phase-3-json.md`

Generates schema-compliant JSON from the mapping guide:
- Reads mapping guide and baseline practice
- Builds JSON incrementally
- Validates with `utils/validate-practice-json.py`

**Output:** `<practice-name>.json` (schema-compliant)

## Reference Documents

All prompts reference these documents (loaded via Read tool):

- `references/domain-framework.md` - Four-perspective analysis framework
- `references/semantics.md` - Practice Language semantic guidance (hub with table of contents)
- `references/semantics/` - Sub-documents: composition, practice-elements, alphas, work-products, execution-and-patterns, narrative-and-assets
- `references/workproduct-assessment-rubric.csv` - Maturity rubric
- `deps/language.schema.json` - JSON Schema definition
- `deps/platform-adoption-kernel.json` - Baseline framework

## Key Differences from v1

**v1 (Archived):**
- 8-phase pipeline with 9+ modular markdown files
- Embedded knowledge in skill orchestration
- Multiple validation utilities (4+)
- Complex assembly and segmentation

**v2 (Current):**
- Simple 3-phase workflow
- Reference-driven (reads semantics/ sub-documents, schema.json)
- Single validation script
- Direct generation without assembly steps

## Usage

These prompts are orchestrated by the `/generate-method` skill. They can also be used manually:

```bash
# Phase 1: Analysis
# Read prompts/phase-1-analysis.md and apply to source materials

# Phase 2: Mapping
# Read prompts/phase-2-mapping.md and apply to analysis report

# Phase 3: JSON
# Read prompts/phase-3-json.md and apply to mapping guide
# Validate: python3 utils/validate-practice-json.py <practice-name>.json
```

## Modifying Prompts

When modifying prompts:

- **Phase 1:** Changes affect analysis structure, perspective analysis, content extraction
- **Phase 2:** Changes affect mapping strategy, semantic interpretation, baseline alignment
- **Phase 3:** Changes affect JSON structure, validation rules, schema compliance

Always test changes with a complete end-to-end workflow to verify they don't break downstream phases.
