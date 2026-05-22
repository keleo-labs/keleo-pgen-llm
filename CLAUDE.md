# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Practice Language Code Generation System** that uses LLMs in a two-phase pipeline to convert enterprise methodology documentation into standardized, schema-compliant JSON. The system analyzes source methodologies (e.g., AWS Well-Architected, SAFe, TOGAF, Team Topologies) and maps them to the Platform Adoption Essentials baseline framework.

## Directory Structure

```
keleo-pgen-llm/
├── .claude/
│   └── skills/
│       └── translate-methodology.md        # Main translation skill (modular)
├── deps/                                   # Symlinks to keleo-studio
│   ├── language.schema.json               # JSON Schema definition
│   └── platform-adoption-kernel.json      # Baseline framework
├── references/                             # Analysis framework documentation
│   ├── domain-framework.md
│   ├── semantics.md
│   └── workproduct-assessment-rubric.csv
├── prompts/                         # Modular prompt system
│   ├── phase-1-modules/                    # Phase 1 modular prompts
│   │   ├── 00-analysis-plan.md            # Practice planning
│   │   ├── 00-method-plan.md              # Method planning (multi-practice)
│   │   ├── 01-practice-details.md         # Practice metadata
│   │   ├── 02-citations.md                # Bibliographic references
│   │   ├── 03-alphas.md                   # Alpha definitions
│   │   ├── 04-workproducts.md             # Work product definitions
│   │   ├── 05-activities-roles.md         # Activities, personas, teams
│   │   ├── 06-patterns.md                 # Pattern orchestrations
│   │   ├── 07-aliases.md                  # Terminology mappings
│   │   └── 08-method-assembly.md          # Method integration layer
│   ├── phase-1-assembly.md                # Phase 1.5: Assembly & validation
│   └── phase-2-modular.md                 # Phase 2: Incremental JSON translation
├── practices/                              # Generated output directory
│   └── <practice-name>/                   # One subdirectory per practice/method
│       ├── report-elements/               # Modular markdown files
│       │   ├── 00-*.md                    # Planning module
│       │   ├── 01-*.md through 07-*.md    # Practice modules
│       │   └── [08-*.md]                  # Method assembly (if method)
│       ├── research-report.md             # Assembled complete report
│       ├── cross-reference-index.json     # Validation index
│       └── <practice-name>.json           # Schema-compliant JSON
└── CLAUDE.md                              # This file
```

### Generated Output Location (Single Practice)

All generated outputs for a practice are in `practices/<practice-name>/`:

- **`report-elements/`** - Modular markdown files (3K-20K words each):
  - `00-analysis-plan.md` - Strategic analysis and planning
  - `01-practice-details.md` - Practice metadata, tags, context
  - `02-citations.md` - Bibliographic references (5-15 sources)
  - `03-alphas.md` - Alpha definitions with states (may split by focus if large)
  - `04-workproducts.md` - Work product definitions with LODs
  - `05-activities-roles.md` - Activities with technique narratives, personas, teams
  - `06-patterns.md` - Pattern definitions with views
  - `07-aliases.md` - Terminology mappings (if source uses different terms)
- **`research-report.md`** - Assembled complete documentation (~50-80K words)
- **`cross-reference-index.json`** - Element index for validation
- **`<practice-name>.json`** - Schema-compliant Practice JSON

### Generated Output Location (Method)

For multi-practice methods in `practices/<method-name>/`:

- **`report-elements/`** - Method and practice modules:
  - `00-method-plan.md` - Method planning and practice composition
  - `practice-1/` - First practice modules (00-07)
  - `practice-2/` - Second practice modules (00-07)
  - `08-method-assembly.md` - Method integration layer
- **`research-report.md`** - Complete method documentation
- **`cross-reference-index.json`** - Aggregated validation index
- **`<method-name>.json`** - Schema-compliant Method JSON (with practices array)

## Architecture

### Modular Three-Phase Pipeline

The system uses a modular workflow to avoid generating unmanageably large documents (80K+ words) in a single step.

**Phase 1: Modular Research Analysis**
- Input: Source methodology documentation
- Process: LLM generates focused modules (3K-20K words each)
- Output: 7-9 modular markdown files per practice
- Prompts: `prompts/phase-1-modules/*.md`

**Phase 1.5: Assembly and Validation**
- Input: All Phase 1 modules
- Process: Concatenate modules, generate cross-reference index, validate
- Output: `research-report.md` (complete documentation) + `cross-reference-index.json` (validation index)
- Prompt: `prompts/phase-1-assembly.md`

**Phase 2: Incremental JSON Translation**
- Input: Phase 1 modules (NOT the 80K report) + cross-reference index
- Process: Read modules sequentially, build JSON incrementally, validate against index
- Output: Schema-compliant JSON
- Prompt: `prompts/phase-2-modular.md`

### Modular Benefits

1. **Manageable Size:** Each module is 3K-20K words (no 80K monoliths)
2. **Incremental Progress:** Generate and validate one section at a time
3. **Iteration-Friendly:** Re-generate individual modules without redoing everything
4. **Clear Dependencies:** Each module knows which previous modules to reference
5. **Quality Control:** Smaller modules are easier to review and correct

### Practice vs Method Handling

**Practice (Single):**
- Single cohesive value stream
- Generates modules 00-07 directly in `report-elements/`
- Produces one Practice JSON object

**Method (Multi-Practice):**
- Multiple distinct value streams or use cases
- Generates `00-method-plan.md` first
- Each practice gets its own subdirectory with modules 00-07
- Generates `08-method-assembly.md` for integration
- Produces one Method JSON object with practices array

### Key Framework Concepts

The system is built around the **Platform Adoption Essentials** baseline framework, which structures methodologies using:

- **Three Focuses**: Value (business), Solution (technical), Endeavor (organizational)
- **Alphas**: Abstract concepts with progressive states (e.g., Platform, Requirements, Team)
- **States**: Discrete maturity levels within each Alpha
- **Activities**: Specific work organized into ActivitySpaces
- **Work Products**: Evidentiary artifacts with Levels of Detail
- **Patterns**: Lifecycle orchestrations coordinating activities
- **Personas & Teams**: Roles with competency requirements
- **Narratives**: Structured storytelling frameworks (STAR, StoryBrand, etc.)

### Four-Perspective Analysis

Content is analyzed through four lenses defined in the Resource Assessment Framework:

1. **Business Perspective**: Value proposition, ROI, stakeholder alignment, risk/compliance → typically maps to Value focus
2. **Technology Perspective**: Architecture, implementation, integration, deployment → typically maps to Solution focus
3. **People Perspective**: Roles, skills, team design, organizational change → typically maps to Endeavor focus
4. **Process Perspective**: Workflows, value realization, strategy → may span multiple focuses

## Critical Files

### Modular Prompts (Phase 1)
- `prompts/phase-1-modules/00-analysis-plan.md` - Practice planning and strategic analysis
- `prompts/phase-1-modules/00-method-plan.md` - Method planning for multi-practice methodologies
- `prompts/phase-1-modules/01-practice-details.md` - Practice metadata, tags, context
- `prompts/phase-1-modules/02-citations.md` - Bibliographic reference extraction
- `prompts/phase-1-modules/03-alphas.md` - Alpha definitions with states and checklists
- `prompts/phase-1-modules/04-workproducts.md` - Work product definitions with LODs
- `prompts/phase-1-modules/05-activities-roles.md` - Activities, personas, teams (includes rich technique narratives)
- `prompts/phase-1-modules/06-patterns.md` - Pattern orchestrations and views
- `prompts/phase-1-modules/07-aliases.md` - Terminology mapping when source uses different terms
- `prompts/phase-1-modules/08-method-assembly.md` - Method integration layer for multi-practice methods

### Assembly and Translation Prompts
- `prompts/phase-1-assembly.md` - Assembles modules, generates validation index
- `prompts/phase-2-modular.md` - Incremental JSON translation from modules

### Reference Documentation
- `references/domain-framework.md` - Modern enterprise architecture perspectives combining Open Agile, SAFe, Gartner CEA, Zachman, TOGAF
- `references/semantics.md` - Comprehensive semantic guidance for the Practice Language JSON Schema
- `references/workproduct-assessment-rubric.csv` - 5-level maturity rubric (Level 0: Non-Existent → Level 4: Comprehensive/Automated)

### Dependencies (Symlinks to keleo-studio)
- `deps/language.schema.json` - JSON Schema definition for Practice Language
- `deps/platform-adoption-kernel.json` - Platform Adoption Essentials baseline framework

## Important Constraints and Patterns

### Alpha Handling
- **Redeclaration**: Enriching baseline alphas with additional checklists/narratives while preserving exact baseline structure
- **Specialization**: Creating new alphas that contribute to baseline alphas (e.g., "Platform Capability" → "Platform")
  - **CRITICAL RULE - NO FLOATING ALPHAS**: ALL new alphas MUST have a `contributesTo` relationship pointing to a baseline alpha
  - Floating alphas (new alphas without `contributesTo`) are **strictly prohibited** by the Practice Language semantics
- **Instances**: Tracking specific occurrences (e.g., "Security Team" and "Platform Team" as instances of "Team")
- When multiple perspectives reference the same alpha, create a SINGLE merged redeclaration, not separate definitions

### Schema Rules
- All symbolic references (alphaName, stateName, activitySpaceName, etc.) must be exact, case-sensitive string matches
- Activity names must be specific and different from their ActivitySpace names
- Minimum requirements: Alphas need ≥3 states, WorkProducts need ≥2 levels of detail
- Narratives use structured frameworks with sequential contexts mapped to narrative elements

### Citations
Every practice must include comprehensive citations using the "Citation Standard" narrative type with Author/Date/Title/Source elements. Prioritize authoritative sources (primary methodology creators).

## Dependencies

This project requires the **keleo-studio** repository to be present at `../../keleo-studio/`. The schema and example files are accessed via symlinks in the `deps/` directory.

## Development Workflow

### Using the Translation Skill

The primary workflow uses the `/translate-methodology` skill:

```
/translate-methodology [source files or URLs]
```

This skill automates the modular three-phase pipeline:

**1. Planning (MANDATORY):**
- Enters plan mode automatically
- Analyzes source materials
- Determines Practice vs Method
- Creates module generation roadmap

**2. Phase 1 - Modular Generation:**
- Generates 7-9 focused modules per practice (3K-20K words each)
- For Practice: Modules 00-07 in `report-elements/`
- For Method: Module 00 (method plan), then practice-1/, practice-2/, etc. with modules 00-07, then module 08 (assembly)
- Modules are self-contained and reference previous modules as needed

**3. Phase 1.5 - Assembly:**
- Concatenates modules into `research-report.md` (~50-80K words total)
- Generates `cross-reference-index.json` for validation
- Runs validation checks on references and completeness

**4. Phase 2 - JSON Translation:**
- Reads modules directly (NOT the 80K report)
- Uses cross-reference index for validation
- Builds JSON incrementally (practice skeleton → citations → alphas → work products → activities → patterns)
- Validates each section as it's built
- Outputs `<practice-name>.json` or `<method-name>.json`

**Output Location**: All files for a practice are co-located in `practices/<practice-name>/`

The skill is defined in `.claude/skills/translate-methodology.md` and orchestrates the modular prompts from `prompts/phase-1-modules/`.

### Manual Workflow

If working manually outside the skill:

**Phase 1 - Module Generation:**
1. **Planning:** Use `prompts/phase-1-modules/00-analysis-plan.md` (or 00-method-plan.md)
2. **Generate modules sequentially:** 01→02→03→04→05→06→07 (each module reads previous ones)
3. For Methods: Generate practice-specific modules in subdirectories, then module 08

**Phase 1.5 - Assembly:**
4. **Assemble:** Use `prompts/phase-1-assembly.md` to concatenate and validate

**Phase 2 - Translation:**
5. **Translate:** Use `prompts/phase-2-modular.md` to read modules and generate JSON

**Validation:**
6. **Validate JSON** against `deps/language.schema.json`

## Working with Prompts

The prompts in `prompts/` have been optimized for use within the `/translate-methodology` skill:

**Optimizations Made:**
- Replaced generic "inputs" sections with explicit repository file paths
- Updated all references to use `deps/platform-adoption-kernel.json` instead of abstract "baseline"
- Added references to `references/domain-framework.md`, `semantics.md`, and `workproduct-assessment-rubric.csv`
- Added execution instructions to use the Read tool for loading resources
- Clarified that prompts operate within the Claude Code skill context

**When modifying prompts:**
- **Phase 1 changes**: Affect report structure, narrative quality, perspective analysis, alpha/activity derivation logic
- **Phase 2 changes**: Affect JSON structure, validation rules, name matching, citation extraction

The prompts are self-contained and comprehensive. Reference files in `references/` provide the analytical framework that guides the analysis.

## Schema Evolution

The Practice Language JSON Schema supports:
- Modular practice composition via dependencies
- Terminology aliasing for vendor-specific names
- Hierarchical alpha relationships (parent/child via contributesTo/supportingAlphas)
- Dynamic state-gating with transition triggers
- Evidence-based progression (WorkProducts proving Alpha states)
- Multi-dimensional tagging (domain/lifecycle/organizational)
