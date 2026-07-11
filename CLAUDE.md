# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Practice Language Code Generation System** that uses LLMs to convert enterprise methodology documentation into standardized, schema-compliant JSON. The system supports two types of artifacts:

1. **Baseline Practices** (foundational frameworks) - Created with `/create-baseline-method`
2. **Extension Practices** (specialized implementations) - Created with `/generate-method`

Extension practices analyze source methodologies (e.g., AWS Well-Architected, SAFe, TOGAF, Team Topologies) and map them to baseline frameworks like Platform Adoption Essentials.

## Directory Structure

```
keleo-pgen-llm/
├── .claude/
│   └── skills/
│       ├── generate-method/              # Extension practice creation skill
│       │   └── SKILL.md
│       └── create-baseline-method/       # Baseline practice creation skill
│           └── SKILL.md
├── deps/                                   # Symlinks to keleo-studio
│   ├── language.schema.json               # JSON Schema definition
│   ├── platform-adoption-kernel.json      # Baseline framework (Platform Adoption)
│   └── partner-ecosystem-baseline.json    # Baseline framework (Partner Ecosystem)
├── references/                             # Analysis framework documentation
│   ├── domain-framework.md
│   ├── semantics.md
│   └── workproduct-assessment-rubric.csv
├── prompts/                                # Prompt system (extension practices)
│   ├── phase-1-analysis.md                # Phase 1: Analysis
│   ├── phase-2-mapping.md                 # Phase 2: Mapping
│   ├── phase-3-json.md                    # Phase 3: JSON generation
│   ├── phase-1-baseline-analysis.md       # Phase 1: Baseline analysis
│   ├── phase-1.5-baseline-distillation.md # Phase 1.5: Baseline distillation (NEW)
│   ├── phase-2-baseline-mapping.md        # Phase 2: Baseline mapping
│   └── phase-3-baseline-json.md           # Phase 3: Baseline JSON generation
├── practices/                              # Extension practices output
│   └── <practice-name>/
│       ├── 01-analysis-report.md
│       ├── 02-mapping-guide.md
│       └── <practice-name>.json
├── baselines/                              # Baseline practices output
│   └── <baseline-name>/
│       ├── 01-analysis-report.md
│       ├── 01.5-distilled-essentials.md   # NEW: Distillation phase
│       ├── 02-mapping-guide.md
│       └── <baseline-name>.json
├── utils/
│   ├── validate-practice-json.py          # Extension practice validation
│   └── validate-baseline-json.py          # Baseline practice validation
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
- Process: LLM analyzes methodology structure, outcomes, concerns, activities, workflows
- Output: `01-analysis-report.md` (~30-50K words)
- Prompt: `prompts/phase-1-analysis.md`
- **Note:** Phase 1 does NOT determine practice boundaries - extracts concerns without baseline context

**Phase 2: Mapping** ⬅️ **PRACTICE DELINEATION HAPPENS HERE**
- Input: Analysis report + baseline practice + semantic guidance
- Process: 
  - **FIRST:** Map Phase 1 concerns to baseline alphas
  - **THEN:** Identify primary alpha(s) and determine practice boundaries based on baseline coverage
  - **FINALLY:** Map elements to baseline practice using Practice Language semantics
- Output: `02-mapping-guide.md` (~40-60K words)
- Prompt: `prompts/phase-2-mapping.md`
- Key Steps: 
  - Primary alpha identification using baseline relatesTo relationships
  - Practice vs Method decision based on alpha coverage (3-7 alphas = practice, 8+ = method)
  - Alpha-state-activity gap analysis ensures every alpha state has supporting activities

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
- `deps/partner-ecosystem-baseline.json` - Partner Ecosystem Essentials baseline framework

## Baseline Practices (Foundational Frameworks)

### What are Baseline Practices?

Baseline practices are **foundational frameworks** that define the core ontology for a domain. They establish:
- **Focuses**: High-level groupings of concerns (e.g., Value, Solution, Endeavor OR custom groupings)
- **Root-Level Alphas**: Core concerns with no parent (have `relatesTo` relationships, NOT `contributesTo`)
- **ActivitySpaces**: Generalizable execution boundaries (not specific activities)
- **Competencies**: Universal skill categories with 5-level progressions
- **NarrativeTypes**: Reusable storytelling frameworks

**Extension practices** (created with `/generate-method`) then specialize baselines by adding:
- New alphas with `contributesTo` (specializations of baseline alphas)
- Concrete activities (mapped to baseline activitySpaces)
- Work products with levels of detail
- Lifecycle patterns coordinating alphas

### Four-Phase Baseline Creation Pipeline

**Use `/create-baseline-method` to create baseline practices:**

**Phase 1: Analysis** (Same as extension practices)
- Extract comprehensive methodology structure (~30-50K words)
- Emphasize universal, framework-level concepts
- Output: `baselines/<name>/01-analysis-report.md`

**Phase 1.5: Distillation** (NEW - CRITICAL)
- **Identify Focus Areas**: Analyze concern patterns to discover natural groupings (2-4 focuses)
  - **Default**: Value, Solution, Endeavor (from Platform Adoption Kernel)
  - **Custom**: Domain-specific groupings (e.g., Partner Ecosystem → Value, Engagement, Go-to-Market)
- **Distill Essential Concerns**: Reduce Phase 1 concerns to 8-15 foundational alphas
- **Generalize Activity Types**: Abstract activities to 6-12 high-level execution boundaries
- **Identify Universal Competencies**: Extract 5-10 skill categories with 5 levels
- **Define Narrative Frameworks**: Identify 3-5 reusable storytelling structures
- Output: `baselines/<name>/01.5-distilled-essentials.md` (~15-25K words)

**Phase 2: Baseline Mapping**
- Transform Phase 1.5 distilled essentials into baseline structures
- Map essential concerns → alphas (with `relatesTo`, NO `contributesTo`)
- Map activity types → activitySpaces (with `contributesTo` to alpha states)
- Define competencies with 5-level progressions
- Define narrativeTypes with narrative elements
- Output: `baselines/<name>/02-mapping-guide.md` (~40-60K words)

**Phase 3: Baseline JSON**
- Generate `"kind": "practiceBaseline"` JSON
- Include top-level definitions: focuses, competencies, activitySpaces, narrativeTypes
- Alphas have NO `contributesTo`, all have `relatesTo` arrays
- Validate with `utils/validate-baseline-json.py`
- Output: `baselines/<name>/<name>.json`

### Baseline vs Extension Practice Decision

**Use `/create-baseline-method` when:**
- ✓ Creating a **foundational framework** for a domain
- ✓ Defining **root-level concerns** (no parent baseline to extend)
- ✓ Establishing **focuses, competencies, narrative types** for a domain
- ✓ Source methodology defines **universal ontology**

**Use `/generate-method` when:**
- ✓ Creating a **practice that extends** an existing baseline
- ✓ Defining **specialized alphas** with `contributesTo`
- ✓ Adding **activities, work products, patterns** (not in baselines)
- ✓ Source methodology is an **implementation** of a framework

**Examples:**

| Source Methodology | Skill to Use | Rationale |
|-------------------|--------------|-----------|
| Platform Adoption Essentials | `/create-baseline-method` | Foundational framework for platform engineering |
| AWS Well-Architected (specific practices) | `/generate-method` | Extends Platform Adoption baseline |
| Partner Ecosystem Essentials | `/create-baseline-method` | Foundational framework for partner management |
| Specific Partner Demand Gen practice | `/generate-method` | Extends Partner Ecosystem baseline |
| Team Topologies | `/create-baseline-method` | Foundational framework for team design |
| Specific SDLC practice | `/generate-method` | Extends appropriate baseline |

### Key Structural Differences

| Element | Extension Practice | Baseline Practice |
|---------|-------------------|-------------------|
| **kind property** | `"practice"` or `"method"` | `"practiceBaseline"` |
| **baselinePracticeName** | REQUIRED (references parent) | OPTIONAL (may reference parent baseline) |
| **Focuses** | Referenced from baseline | DEFINED in baseline (2-4 focuses) |
| **Alpha contributesTo** | REQUIRED on new alphas | NOT PRESENT (root-level) |
| **Alpha relatesTo** | Optional | REQUIRED (show interconnections) |
| **Competencies** | Referenced from baseline | DEFINED with 5 levels |
| **ActivitySpaces** | Referenced from baseline | DEFINED in baseline |
| **NarrativeTypes** | Referenced from baseline | DEFINED in baseline |
| **Activities** | Defined in practice | NOT PRESENT |
| **WorkProducts** | Defined in practice | NOT PRESENT |
| **Patterns** | Defined in practice | NOT PRESENT |

### Baseline Output Location

All files for a baseline are co-located in `baselines/<baseline-name>/`:

- **`01-analysis-report.md`** - Phase 1 output: Comprehensive analysis (~30-50K words)
- **`01.5-distilled-essentials.md`** - Phase 1.5 output: Essential elements (~15-25K words) **[NEW]**
- **`02-mapping-guide.md`** - Phase 2 output: Baseline mapping (~40-60K words)
- **`<baseline-name>.json`** - Phase 3 output: Schema-compliant baseline JSON

## Important Constraints and Patterns

### Extension Practice Constraints

These constraints apply to **extension practices** created with `/generate-method`:

### Alpha Handling
- **Redeclaration**: Enriching baseline alphas with additional checklists/narratives while preserving exact baseline structure
- **Specialization**: Creating new alphas that contribute to baseline alphas (e.g., "Platform Capability" → "Platform")
  - **CRITICAL RULE - NO FLOATING ALPHAS**: ALL new alphas MUST have a `contributesTo` relationship pointing to a baseline alpha, practice-local alpha, OR external practice alpha
  - Floating alphas (new alphas without `contributesTo`) are **strictly prohibited** by the Practice Language semantics
  - **Cross-Practice References**: Alphas can contribute to alphas from other practices using `practiceDependencyNames`
- **Instances**: Tracking specific occurrences (e.g., "Security Team" and "Platform Team" as instances of "Team")
- When multiple perspectives reference the same alpha, create a SINGLE merged redeclaration, not separate definitions

### Practice Structure - Primary Alpha Focus

**Core Principle:** Each practice should focus around ONE primary alpha, with secondary coverage of that alpha's directly related alphas (via `relatesTo` relationships). This creates focused, coherent practices with broad coverage of loosely related concerns.

**Practice Composition:**
- **Primary Alpha**: ONE central baseline alpha that is the main focus (e.g., Platform, Team, Requirements)
- **Related Alphas**: 2-6 alphas directly related to primary via `relatesTo` relationships (1-level deep)
- **Total Coverage**: 3-7 alphas per practice (broad, loosely related coverage)
- **Coherence**: All content should relate back to the primary alpha's value proposition

**Example - Platform-Focused Practice:**
- Primary: Platform
- Related (from Platform.relatesTo): Platform Asset (hosts), Platform Consumption Interface (exposes), Platform Governance (governed by), Team (built by)
- Result: 5 alphas with broad coverage of platform infrastructure concerns

**Example - Team-Focused Practice:**
- Primary: Team  
- Related (from Team.relatesTo): Work (performs), Way Of Working (applies), Platform (built by reversed), Organizational Change (enabled by)
- Result: 5 alphas with broad coverage of team and organizational concerns

**Anti-Pattern:** "Everything else" catch-all practices without identifiable primary alpha

### Orchestration Practices (Exception)

**When to Create:** Source methodology describes an overarching lifecycle or coordination framework that ties together multiple domain practices

**Structure:**
- **Purpose**: Cross-practice coordination, NOT content duplication
- **Dependencies**: Lists all practices it coordinates via `practiceDependencyNames`
- **Content**:
  - **Aliases**: Unifying terminology across dependent practices
  - **Patterns**: Lifecycle patterns referencing alphas from multiple dependent practices
  - **Minimal Alphas**: ONLY if coordination requires new tracking concepts
- **No Redeclaration**: Does NOT redefine alphas from dependent practices
- **Example**: SDLC Orchestration practice coordinating Development, Deployment, Operations practices

**Orchestration vs Regular Practice:**
- Regular Practice: Primary alpha + related alphas (content-focused)
- Orchestration Practice: Dependencies + patterns + aliases (coordination-focused)

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

### Creating Baseline Practices

Use the `/create-baseline-method` skill to create foundational frameworks:

```
/create-baseline-method [source files or URLs]
```

This skill automates the four-phase baseline creation pipeline:

**1. Planning (MANDATORY):**
- Enters plan mode automatically
- Analyzes source materials for baseline appropriateness
- Identifies potential custom Focuses
- Creates execution roadmap

**2. Phase 1 - Analysis:**
- Extracts comprehensive methodology structure
- Emphasizes universal, framework-level concepts
- Outputs `baselines/<name>/01-analysis-report.md` (~30-50K words)

**3. Phase 1.5 - Distillation (CRITICAL NEW PHASE):**
- Identifies Focus areas (default or custom)
- Distills essential concerns to 8-15 foundational alphas
- Generalizes activity types to 6-12 execution boundaries
- Identifies universal competencies (5-10 with 5 levels)
- Defines narrative frameworks (3-5)
- Outputs `baselines/<name>/01.5-distilled-essentials.md` (~15-25K words)

**4. Phase 2 - Baseline Mapping:**
- Maps distilled essentials to baseline structures
- Transforms concerns → alphas (with `relatesTo`, NO `contributesTo`)
- Defines focuses, competencies, activitySpaces, narrativeTypes
- Outputs `baselines/<name>/02-mapping-guide.md` (~40-60K words)

**5. Phase 3 - Baseline JSON:**
- Generates `"kind": "practiceBaseline"` JSON
- Validates with `utils/validate-baseline-json.py`
- Outputs `baselines/<name>/<name>.json`

**Output Location**: All files for a baseline are co-located in `baselines/<baseline-name>/`

The skill is defined in `.claude/skills/create-baseline-method/SKILL.md` and uses baseline-specific prompts from `prompts/`.

### Creating Extension Practices

Use the `/generate-method` skill to create practices that extend baselines:

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
- Outputs `practices/<name>/01-analysis-report.md` (~30-50K words)

**3. Phase 2 - Mapping:**
- Maps analyzed elements to baseline practice
- Uses semantic guidance from `references/semantics.md`
- Outputs `practices/<name>/02-mapping-guide.md` (~40-60K words)

**4. Phase 3 - JSON Generation:**
- Generates schema-compliant JSON from mapping guide
- Validates with `utils/validate-practice-json.py`
- Outputs `practices/<name>/<practice-name>.json` or `<method-name>.json`

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
