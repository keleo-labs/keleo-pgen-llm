# Extraction Scripts

Scripts for extracting specific components from Phase 1 markdown modules during pipeline development.

## Overview

These scripts were used to develop and test component extraction logic before it was integrated into the modular Phase 2 translation prompt. They read Phase 1 markdown modules and extract structured data for specific Practice Language elements.

**Note:** The current `/translate-methodology` skill uses LLM-based extraction via `prompts/phase-2-modular.md`, which is more robust than these regex-based approaches.

## Scripts

### extract-alphas.py

**Purpose:** Extract alpha definitions with states and checklists from `03-alphas.md` (or split files like `03a-*.md`, `03b-*.md`).

**Key Features:**
- Parses alpha sections with regex
- Extracts name, description, focus, states
- Handles baseline redeclarations vs new alphas
- Validates state checklists

**Limitations:**
- Hardcoded paths to specific practices
- Regex-based parsing is brittle with format variations
- Doesn't handle contributesTo relationships well

**Usage:**
```python
from extract_alphas import extract_alphas_from_modules

alphas = extract_alphas_from_modules(
    modules_dir=Path("practices/my-practice/report-elements"),
    practice_data=cross_reference_index
)
```

### extract-workproducts.py

**Purpose:** Extract work product definitions with Levels of Detail from `04-workproducts.md`.

**Key Features:**
- Parses work product sections
- Extracts LOD levels (0-4 based on rubric)
- Maps work products to alphas/states

**Limitations:**
- Assumes specific markdown format
- May miss complex LOD narratives
- Hardcoded to specific rubric interpretation

**Usage:**
```python
from extract_workproducts import extract_workproducts_from_module

work_products = extract_workproducts_from_module(
    module_path=Path("practices/my-practice/report-elements/04-workproducts.md"),
    practice_data=cross_reference_index
)
```

### extract-practice-json.py

**Purpose:** Complete extraction of all Practice elements into a JSON structure (executable script).

**Key Features:**
- Orchestrates extraction of all components
- Builds complete Practice object
- Validates cross-references against index
- Writes schema-compliant JSON

**Hardcoded Assumptions:**
- Specific practice directory structure
- Fixed module naming conventions
- Particular cross-reference index format

**Usage:**
```bash
# Edit script to set practice paths
./extract-practice-json.py
```

### extract-p2-alphas.py

**Purpose:** Extract alphas specifically for Practice 2 of a multi-practice method.

**Context:**
- Used during Red Hat Ansible Automation Platform method development
- Handles practice-specific subdirectory structure
- Similar to `extract-alphas.py` but for practice-2/ subdirectory

### extract-cross-ref-index.py

**Purpose:** Generate cross-reference validation index from Phase 1 modules.

**Key Features:**
- Scans all Phase 1 modules
- Extracts element names and relationships
- Creates index for validation during Phase 2
- Validates element counts and coverage

**Output:**
- `cross-reference-index.json` with:
  - All alpha names and state names
  - All work product names
  - All activity names
  - All persona and team names
  - Element counts for validation

**Current Status:**
This functionality is now integrated into `prompts/phase-1-assembly.md`, which generates the cross-reference index as part of Phase 1.5.

## Why These Scripts Exist

During pipeline development, we needed to:
1. **Test extraction logic** - Validate that components could be extracted from markdown
2. **Iterate on formats** - Refine module structure based on what could be reliably parsed
3. **Debug issues** - Manually extract specific elements when the pipeline failed
4. **Develop incrementally** - Build component extraction before integrating into LLM prompts

## Migration to LLM-Based Approach

The current system uses **LLM-based extraction** via Phase 2 prompts instead of regex parsing:

**Advantages:**
- More robust to format variations
- Better semantic understanding
- Handles complex narratives and relationships
- Self-correcting with validation feedback

**Result:**
These scripts are now primarily **reference implementations** showing what needs to be extracted, rather than production tools.

## When to Use These Scripts

Consider using these scripts when:
- **Debugging extraction issues** - Understand what data is in the modules
- **Recovering from failures** - Manually extract a specific section if Phase 2 fails
- **Developing new extractors** - Starting point for custom extraction logic
- **Understanding the data model** - See how components map from markdown to JSON

For normal workflow, use the `/translate-methodology` skill instead.
