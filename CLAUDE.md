# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Practice Language Code Generation System** that uses LLMs in a three-phase pipeline to convert enterprise methodology documentation into standardized, schema-compliant JSON. The system analyzes source methodologies (e.g., AWS Well-Architected, SAFe, TOGAF, Team Topologies) and maps them to the Platform Adoption Essentials baseline framework.

## Directory Structure

```
keleo-pgen-llm/
├── .claude/
│   └── skills/
│       └── generate-method/      # Main translation skill
│           └── SKILL.md
├── deps/                                   # Symlinks to keleo-studio
│   ├── language.schema.json               # JSON Schema definition
│   └── platform-adoption-kernel.json      # Baseline framework
├── references/                             # Analysis framework documentation
│   ├── domain-framework.md
│   ├── semantics.md
│   └── workproduct-assessment-rubric.csv
├── prompts/                                # Three-phase prompt system
│   ├── phase-1-analysis.md                # Phase 1: Analysis
│   ├── phase-2-mapping.md                 # Phase 2: Mapping
│   └── phase-3-json.md                    # Phase 3: JSON generation
├── practices/                              # Generated output directory
│   └── <practice-name>/                   # One subdirectory per practice/method
│       ├── 01-analysis-report.md          # Phase 1 output (~30-50K words)
│       ├── 02-mapping-guide.md            # Phase 2 output (~40-60K words)
│       └── <practice-name>.json           # Phase 3 output (schema-compliant JSON)
├── utils/
│   └── validate-practice-json.py          # Unified validation script
└── CLAUDE.md                              # This file
```

### Generated Output Location (Single Practice)

All generated outputs for a practice are in `practices/<practice-name>/`:

- **`01-analysis-report.md`** - Phase 1 output: Structured analysis of methodology (~30-50K words)
- **`02-mapping-guide.md`** - Phase 2 output: Mapping to baseline practice (~40-60K words)
- **`<practice-name>.json`** - Phase 3 output: Schema-compliant Practice JSON

### Generated Output Location (Method)

For multi-practice methods in `practices/<method-name>/`:

- **`01-analysis-report.md`** - Phase 1 output covering all practices
- **`02-mapping-guide.md`** - Phase 2 output mapping all practices
- **`<method-name>.json`** - Phase 3 output: Schema-compliant Method JSON (with practices array)

## Architecture

### Three-Phase Pipeline

The system uses a simplified three-phase workflow that is reference-driven rather than embedding rules.

**Phase 1: Analysis**
- Input: Source methodology documentation
- Process: LLM analyzes methodology structure, outcomes, concerns, activities, workflows, practices
- Output: `01-analysis-report.md` (~30-50K words)
- Prompt: `prompts/phase-1-analysis.md`

**Phase 2: Mapping**
- Input: Analysis report + baseline practice + semantic guidance
- Process: Map analyzed elements to baseline practice using Practice Language semantics, including alpha-state-activity gap analysis
- Output: `02-mapping-guide.md` (~40-60K words)
- Prompt: `prompts/phase-2-mapping.md`
- Key Step: Step 7.5 - Alpha-state-activity gap analysis ensures every alpha state has supporting activities

**Phase 3: JSON Generation**
- Input: Mapping guide + schema + baseline practice
- Process: Generate schema-compliant JSON with programmatic validation
- Output: `<practice-name>.json` (schema-compliant)
- Prompt: `prompts/phase-3-json.md`
- Validation: `utils/validate-practice-json.py` (single unified validation script)

### Key Improvements Over v1

1. **Simplified Architecture:** 3 phases instead of 8-phase pipeline
2. **Reference-Driven:** Reads semantics.md, schema.json, domain-framework.md explicitly
3. **Single Validation:** One unified validation script instead of 4+ separate utilities
4. **Cleaner Output:** 3 files per practice instead of 8+ modules
5. **Better for Parallelism:** Suitable for multi-agent parallel execution

### Practice vs Method Handling

**Practice (Single):**
- Single cohesive value stream
- Generates 3 files in `practices/<practice-name>/`
- Produces one Practice JSON object

**Method (Multi-Practice):**
- Multiple distinct value streams or use cases
- Each practice analyzed and mapped in single documents
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

### Phase Prompts

- `prompts/phase-1-analysis.md` - Phase 1: Analyze methodology structure and content
- `prompts/phase-2-mapping.md` - Phase 2: Map to baseline practice using semantics
- `prompts/phase-3-json.md` - Phase 3: Generate schema-compliant JSON

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
  - **CRITICAL RULE - NO FLOATING ALPHAS**: ALL new alphas MUST have a `contributesTo` relationship pointing to a baseline alpha, practice-local alpha, OR external practice alpha
  - Floating alphas (new alphas without `contributesTo`) are **strictly prohibited** by the Practice Language semantics
  - **Cross-Practice References**: Alphas can contribute to alphas from other practices using `practiceDependencyNames`
- **Instances**: Tracking specific occurrences (e.g., "Security Team" and "Platform Team" as instances of "Team")
- When multiple perspectives reference the same alpha, create a SINGLE merged redeclaration, not separate definitions

### Orchestration Practices
- When source methodology describes an **overarching lifecycle pattern** spanning multiple domains:
  - **Divide** content into separate practices by domain/concern/focus
  - **Create orchestration practice** that coordinates via patterns using `practiceDependencyNames`
  - Orchestration practice focuses on **pattern coordination**, NOT alpha redefinition
  - Use `practiceDependencyNames` to load alphas from other practices for pattern references

### Schema Rules
- All symbolic references (alphaName, stateName, activitySpaceName, etc.) must be exact, case-sensitive string matches
- Activity names must be specific and different from their ActivitySpace names
- Minimum requirements: Alphas need ≥3 states, WorkProducts need ≥2 levels of detail
- Narratives use structured frameworks with sequential contexts mapped to narrative elements

### Citations
Every practice must include comprehensive citations using the "Citation Standard" narrative type with Author/Date/Title/Source elements. Prioritize authoritative sources (primary methodology creators).

### Assets
Visual assets (diagrams, templates, icons) can be referenced in practices and methods using the AssetReference structure:

- **Top-level `assets` array**: Defines available assets with metadata
- **Element-level `assetNames` property**: Array of AssetReference objects linking practice elements to assets with semantic type classification
- **AssetReference structure**: Each reference includes:
  - `assetName`: Symbolic reference to Asset.name in top-level assets array
  - `type`: Semantic classification (`icon`, `illustrative`, `template`, `diagram`)
- **Asset types in top-level assets array**:
  - **File-based**: `image`, `diagram`, `template`, `icon` with `path`, `mimeType`, optional `checksum`
  - **Font characters**: `font-character` with `fontFamily`, `fontCharacter`, `fontWeight` (e.g., Font Awesome icons)
  - **Remote**: Assets can use `url` for external hosting or `dataUri` for embedded data

**AssetReference Type Semantics**:

- **icon**: UI markers, visual identity (alpha icons, competency badges, activity type indicators)
- **illustrative**: Documentation diagrams, architecture visualizations, workflow charts
- **template**: Reusable documents, forms, decision records, ADR templates
- **diagram**: Technical architecture, state progression, pattern orchestration

**Example**:
```json
{
  "alphas": [
    {
      "name": "Platform",
      "assetNames": [
        {
          "assetName": "platform-icon",
          "type": "icon"
        },
        {
          "assetName": "platform-states-diagram",
          "type": "diagram"
        }
      ]
    }
  ],
  "assets": [
    {
      "name": "platform-icon",
      "type": "font-character",
      "fontFamily": "Font Awesome 6 Free",
      "fontCharacter": "fa-cubes",
      "fontWeight": "900"
    },
    {
      "name": "platform-states-diagram",
      "type": "diagram",
      "path": "assets/diagrams/platform.svg",
      "mimeType": "image/svg+xml"
    }
  ]
}
```

## Dependencies

This project requires the **keleo-studio** repository to be present at `../../keleo-studio/`. The schema and example files are accessed via symlinks in the `deps/` directory.

## Development Workflow

### Using the Translation Skill

The primary workflow uses the `/generate-method` skill:

```
/generate-method [source files or URLs]
```

This skill automates the three-phase pipeline:

**1. Planning (MANDATORY):**
- Enters plan mode automatically
- Analyzes source materials
- Determines Practice vs Method
- Creates execution roadmap

**2. Phase 1 - Analysis:**
- Analyzes methodology structure: outcomes, concerns, activities, workflows, practices
- Outputs `01-analysis-report.md` (~30-50K words)

**3. Phase 2 - Mapping:**
- Maps analyzed elements to baseline practice
- Uses semantic guidance from `references/semantics.md`
- Outputs `02-mapping-guide.md` (~40-60K words)

**4. Phase 3 - JSON Generation:**
- Generates schema-compliant JSON from mapping guide
- Validates with `utils/validate-practice-json.py`
- Outputs `<practice-name>.json` or `<method-name>.json`

**Output Location**: All files for a practice are co-located in `practices/<practice-name>/`

The skill is defined in `.claude/skills/generate-method/SKILL.md` and uses the phase prompts from `prompts/`.

### Manual Workflow

If working manually outside the skill:

**Phase 1 - Analysis:**
1. Use `prompts/phase-1-analysis.md` to analyze methodology structure
2. Read source materials and reference documents (`references/domain-framework.md`)
3. Output: `01-analysis-report.md`

**Phase 2 - Mapping:**
4. Use `prompts/phase-2-mapping.md` to map to baseline practice
5. Read `references/semantics.md` for semantic guidance
6. Output: `02-mapping-guide.md`

**Phase 3 - JSON Generation:**
7. Use `prompts/phase-3-json.md` to generate JSON
8. Validate with `python3 utils/validate-practice-json.py <practice-name>.json`

## Working with Prompts

The prompts in `prompts/` are optimized for the `/generate-method` skill:

**Key Features:**
- Reference-driven: Explicitly read semantics.md, schema.json, domain-framework.md
- Self-contained: Each phase prompt includes all necessary instructions
- Operate within Claude Code skill context with Read tool for loading resources

**When modifying prompts:**
- **Phase 1 changes**: Affect analysis structure, perspective analysis, content extraction
- **Phase 2 changes**: Affect mapping strategy, semantic interpretation, baseline alignment
- **Phase 3 changes**: Affect JSON structure, validation rules, schema compliance

Reference files in `references/` provide the analytical framework and semantic guidance.

## Schema Evolution

The Practice Language JSON Schema supports:
- Modular practice composition via dependencies
- Terminology aliasing for vendor-specific names
- Hierarchical alpha relationships (parent/child via contributesTo/supportingAlphas)
- Dynamic state-gating with transition triggers
- Evidence-based progression (WorkProducts proving Alpha states)
- Multi-dimensional tagging (domain/lifecycle/organizational)
