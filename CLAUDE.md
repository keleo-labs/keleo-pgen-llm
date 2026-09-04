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
│       ├── create-baseline-method/       # Baseline practice creation skill
│       │   └── SKILL.md
│       ├── method-based-report/          # Plain English report generation skill
│       │   └── SKILL.md
│       └── plan-from-feedback/          # Issue register triage and resolution skill
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
│       └── <practice-name>.json           # Intermediate practice JSON
├── baselines/                              # Baseline practices output
│   └── <baseline-name>/
│       ├── 01-analysis-report.md
│       ├── 01.5-distilled-essentials.md   # Distillation phase
│       ├── 02-mapping-guide.md
│       └── <baseline-name>.json           # Intermediate baseline JSON
├── reports/                                # Generated reports output (git-ignored contents)
│   └── <report-name>.md                   # Plain English reports from /method-based-report
├── bundles/                                # Packaged .keleo output
│   └── <name>.keleo                       # ZIP archive with manifest + documents
├── utils/
│   ├── resolve-context.py                 # Unified context resolver (baselines + practices + .keleo → _effective-context.json)
│   ├── validate-practice-json.py          # Extension practice validation
│   └── validate-baseline-json.py          # Baseline practice validation
└── CLAUDE.md                              # This file
```

### Generated Output Location (Single Practice)

All generated outputs for a practice are in `practices/<practice-name>/`:

- **`01-analysis-report.md`** - Phase 1 output: Structured analysis of methodology (~30-50K words)
- **`02-mapping-guide.md`** - Phase 2 output: Mapping to baseline practice (~40-60K words)
- **`<practice-name>.json`** - Phase 3 output: Schema-compliant Practice JSON (intermediate)
- **`bundles/<practice-name>.keleo`** - Packaged output: Practice + baseline bundled in `.keleo` archive

### Generated Output Location (Method)

For multi-practice methods in `practices/<method-name>/`:

- **`01-analysis-report.md`** - Phase 1 output covering all practices
- **`02-mapping-guide.md`** - Phase 2 output mapping all practices
- **`<practice-name>.json`** - Per-practice standalone JSONs (intermediate)
- **`bundles/<method-name>.keleo`** - Packaged output: Externalized method + practices + baseline in `.keleo` archive

## Architecture

### Three-Phase Pipeline

The system uses a simplified three-phase workflow that is reference-driven rather than embedding rules.

**Phase 1: Analysis**
- Input: Source methodology documentation
- Process: LLM analyzes methodology structure, outcomes, concerns, activities, workflows
- Output: `01-analysis-report.md` (~30-50K words)
- Prompt: `prompts/phase-1-analysis.md`
- **Note:** Phase 1 does NOT determine practice boundaries - extracts preliminary structural observations without baseline context

**Step 1.5: Delineation Gate** ⬅️ **PRACTICE DELINEATION HAPPENS HERE**
- Performed by main agent BEFORE delegating Phase 2
- Process: Load baseline JSON, map Phase 1 concerns to baseline alphas, count coverage
- Decision: 3-7 alphas = single practice, 8+ alphas = likely method requiring subdivision
- Gate determines delegation strategy (one agent vs parallel agents)
- See SKILL.md Step 1.5 for full algorithm

**Phase 2: Mapping**
- Input: Analysis report + baseline practice + semantic guidance + delineation results from Step 1.5
- Process: 
  - **FIRST:** Validate delineation decision (Step 0 of phase-2-mapping.md)
  - **THEN:** Map elements to baseline practice using Practice Language semantics
- Output: `02-mapping-guide.md` (~40-60K words) with Delineation Analysis section
- Prompt: `prompts/phase-2-mapping.md`
- Key Steps: 
  - Delineation validation (Step 0) with alpha coverage analysis and justification
  - Primary alpha identification using baseline relatesTo relationships
  - Alpha-state-activity gap analysis ensures every alpha state has supporting activities

**Phase 3: JSON Generation + Packaging**
- Input: Mapping guide + schema + baseline practice
- Process: Generate schema-compliant JSON with programmatic validation, then package into `.keleo`
- Output: `<practice-name>.keleo` (`.keleo` package bundling practice + baseline)
- For methods: Externalized method JSON with `practiceNames` string references (no embedded objects)
- Prompt: `prompts/phase-3-json.md`
- Validation: `utils/validate-practice-json.py` (individual JSONs before packaging)
- Packaging: `utils/package-keleo.py` (creates `.keleo` archive with `manifest.json`)

### Key Improvements Over v1

1. **Simplified Architecture:** 3 phases instead of 8-phase pipeline
2. **Reference-Driven:** Reads semantics.md, schema.json, domain-framework.md explicitly
3. **Single Validation:** One unified validation script instead of 4+ separate utilities
4. **Cleaner Output:** 3 files per practice instead of 8+ modules
5. **Better for Parallelism:** Suitable for multi-agent parallel execution

### Practice vs Method Handling

**Practice (Single):**
- Single cohesive value stream
- Generates analysis, mapping, JSON, and `.keleo` package in `practices/<practice-name>/`
- `.keleo` package in `bundles/` bundles practice JSON + baseline JSON

**Method (Multi-Practice):**
- Multiple distinct value streams or use cases
- Each practice analyzed and mapped in single documents
- `.keleo` package in `bundles/` bundles externalized method JSON (with `practiceNames` string references) + individual practice JSONs + baseline JSON
- Methods spanning multiple baselines can declare `alphaBindings` for cross-baseline contribution relationships

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
- New alphas with `contributesTo` (specializations with distinct state progression) or `mapsTo` (named variants with same states)
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
- ✓ Defining **specialized alphas** with `contributesTo` or **variant alphas** with `mapsTo`
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
| **Alpha contributesTo / mapsTo** | REQUIRED on new alphas (mutually exclusive) | NOT PRESENT (root-level) |
| **Alpha relatesTo** | Optional (new alphas only) | REQUIRED (show interconnections) |
| **AlphaRelationship direction** | Required on all relatesTo entries | Required on all relatesTo entries |
| **State contributesToState** | Optional (maps child state → parent state) | NOT PRESENT |
| **Method alphaBindings** | N/A (practice) / Optional (method) | NOT PRESENT |
| **Acknowledgements** | Optional | Optional |
| **Competencies** | Referenced from baseline | DEFINED with 5 levels |
| **ActivitySpaces** | Referenced from baseline | DEFINED in baseline |
| **NarrativeTypes** | Referenced from baseline | DEFINED in baseline |
| **Activities** | Defined in practice | NOT PRESENT |
| **WorkProducts** | Defined in practice | NOT PRESENT |
| **WorkProduct partOf / mapsTo** | Optional on WPs (mutually exclusive) | NOT PRESENT |
| **Patterns** | Defined in practice | NOT PRESENT |
| **PatternGroups** | Optional (adopt baseline groups, add patterns; novel groups need justification) | Optional (define canonical groups with empty entries as templates for extensions) |
| **Activity ledBy** | Optional (single Persona.name accountable for leading) | Optional (on ActivitySpace) |
| **References** | Optional array of AlphaInstance (curated external content) | NOT PRESENT |
| **Gherkin (background/test/examples)** | Full use on states, checklists, LODs, activities | Minimal use (practice layer adds detail) |
| **schemaVersion** | Optional (auto-set by skills) | Optional (auto-set by skills) |
| **dependencyVersions** | Entries for baselinePracticeName + practiceDependencyNames | Entries for baselinePracticeNames (if any) |

### Baseline Output Location

All files for a baseline are co-located in `baselines/<baseline-name>/`:

- **`01-analysis-report.md`** - Phase 1 output: Comprehensive analysis (~30-50K words)
- **`01.5-distilled-essentials.md`** - Phase 1.5 output: Essential elements (~15-25K words) **[NEW]**
- **`02-mapping-guide.md`** - Phase 2 output: Baseline mapping (~40-60K words)
- **`<baseline-name>.json`** - Phase 3 output: Schema-compliant baseline JSON (intermediate)
- **`bundles/<baseline-name>.keleo`** - Packaged output: Baseline bundled in `.keleo` archive

## Important Constraints and Patterns

### Extension Practice Constraints

These constraints apply to **extension practices** created with `/generate-method`. Full details in `references/semantics.md` Sections 4.1-4.5, 6.1-6.2, 7.4-7.5.

### Alpha Handling
- **Redeclaration**: Enrich baseline alphas with checklists/narratives; preserve baseline structure
- **Specialization** (`contributesTo`): New alphas with distinct state progression contributing to parent
- **Variant** (`mapsTo`): Named variants with exact same states as parent (IS-A semantics). `mapsTo` and `contributesTo` are mutually exclusive. Variant names MUST NOT repeat parent type name.
- **NO FLOATING ALPHAS**: All new alphas MUST have `contributesTo` OR `mapsTo`
- **`relatesTo`**: Required on new alphas. Fields: `relationship`, `alphaName`, `direction` (`outgoing`|`incoming`|`mutual`)

### Practice Structure
Each practice focuses on ONE primary alpha + related alphas (via `relatesTo`, 1-level deep), 3-7 total. See `references/practice-method-strategy.md` for full strategy and worked examples.

### Schema Rules
- All symbolic references are exact, case-sensitive string matches
- Minimums: ≥3 states per alpha, ≥2 LODs per work product
- WorkProduct `mapsTo` and `partOf` are mutually exclusive (see semantics.md §7.4-7.5)

### Versioning

The Practice Language uses three versioning mechanisms:

**Schema Version (`schemaVersion`):**
- The schema declares its version in `$comment: "schemaVersion:X.Y.Z"` at root level
- Documents declare which schema version they target via optional `schemaVersion` property (pattern `^\d+\.\d+\.\d+$`)
- Available on Practice, PracticeBaseline, Method, ChangeRequest, ChangeSet, Project
- **Required** on PackageManifest
- Skills auto-read the schema version and set it on generated documents

**Document Version (`version`):**
- Required on Practice and PracticeBaseline; optional on Method and Project
- Recommended format: three-part semver (`1.0.0`); shortened forms (`1.0`) are valid but discouraged
- New documents start at `1.0.0`
- Updates increment based on scope: patch (auto-fix), minor (remap/reanalysis)

**Dependency Version Constraints (`dependencyVersions`):**
- Optional array of `DocumentVersionConstraint` on Practice, PracticeBaseline, Method, Project
- Each entry: `{"documentName": "<name>", "versionRange": "<semver range>"}`
- `documentName` must match a declared dependency (`baselinePracticeName`, `practiceDependencyNames` entry, `practiceNames` entry, `baselinePracticeNames` entry)
- `versionRange` uses npm/node-semver syntax (`^2.0.0`, `>=1.0.0 <3.0.0`, `~1.2.0`)
- Version mismatches produce **warnings** by default, not errors
- Skills auto-populate from resolved dependency versions using caret ranges

**Package Dependencies (`PackageDependency`):**
- Package-level dependencies in `PackageManifest.dependencies`
- Each entry: `{"packageName": "<name>", "versionRange": "<range>", "documentNames": [...]}`
- Auto-built by `package-keleo.py` from document-level `dependencyVersions`

### Gherkin-Inspired Structured Guidance

The schema supports optional Gherkin-inspired properties for structured verification and execution scenarios (see `references/semantics.md` Section 5.3 and 8.1.1):

- **`background`** (on State, LevelOfDetail, ActivitySpace, Activity): Shared prerequisites — object with optional `given` (string[]), `alphaStates` (AlphaContribution[]), `workProductLevels` (WorkProductContribution[])
- **`test`** (on Checklist, Activity): Structured Given/When/Then verification scenario — extends PracticeElement (has `name`, `description`) plus optional `given`, `when`, `then` (string[])
- **`examples`** (on Checklist, Activity): Array of Test objects providing concrete scenarios
- **Activity semantics**: `test.when` captures triggers/decision points; `test.then` complements structural `contributesTo`/`worksOn`
- **Baseline guidance**: Use sparingly in baselines — the practice layer is the natural place for detailed Gherkin structure
- **Incremental adoption**: Any combination can be used independently; partial use is valid

### Citations
Every practice must include comprehensive citations using the "Citation Standard" narrative type with Author/Date/Title/Source elements. Prioritize authoritative sources (primary methodology creators).

### Acknowledgements
Optional `acknowledgements` array on Practice, PracticeBaseline, and Method. Recognizes individuals, groups, or institutions that contributed to the methodology. Distinct from citations — attributes human contributions rather than published works. Each entry has `name`, `description`, and optional `url`.

### References (Curated External Content)
Optional `references` array on Practice and PracticeInMethod (NOT on PracticeBaseline or Method). Contains `AlphaInstance` objects — curated external content illustrating alphas at specific states. Every reference MUST have at least one `links` entry. See `references/semantics.md` §6.6 for naming conventions, instance naming, merge rules, and two-level link architecture.

### Assets
Visual assets use `AssetReference` objects (`{assetName, type}`) on elements, resolved against a top-level `assets` array. Types: `icon`, `illustrative`, `template`, `diagram`. Asset formats: `font-character`, `image`, `diagram`, `template` (with `path`/`url`/`dataUri`). See `deps/language.schema.json` `$defs/Asset` and `$defs/AssetReference` for schema.

### `.keleo` Packaging

All skills output `.keleo` packages as their primary deliverable. A `.keleo` file is a ZIP archive (MIME: `application/vnd.keleo.package+zip`) containing:

- **`manifest.json`** — Package manifest conforming to `language.schema.json#/$defs/PackageManifest`
- **`documents/`** — Flat directory of Practice Language JSON files (baselines, practices, methods)
- **`assets/`** — Optional directory for file-based assets (diagrams, templates, icons)

Methods in `.keleo` packages use **externalized references**: `baselinePracticeName` (string) and `practiceNames` (string array) instead of embedded objects. The package's document inventory provides name resolution.

**Packaging utility:** `utils/package-keleo.py` creates `.keleo` archives from constituent JSON files.

### Schema Constructs Not Used by Current Skills

The Practice Language schema includes constructs that are not directly relevant to the current skills but may inform future work:

- **Project**: Root type for tracking real-world execution against a practice/method (team, plan, current/target state, checklists)
- **ChangeRequest / ChangeSet**: PR-like change proposals for modifying practices/baselines/methods with review lifecycle

See `references/semantics.md` Sections 12-13 for details.

## Dependencies

This project requires the **keleo-language** repository to be present at `../../keleo-language/`. The schema, validation scripts, and semantic reference files are accessed via symlinks in the `deps/`, `references/`, and `utils/` directories.

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

**5. Phase 3 - Baseline JSON + Packaging:**
- Generates `"kind": "practiceBaseline"` JSON
- Validates with `utils/validate-baseline-json.py`
- Packages into `.keleo` archive with `utils/package-keleo.py`
- Outputs `bundles/<name>.keleo` (primary) and `baselines/<name>/<name>.json` (intermediate)

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

**4. Phase 3 - JSON Generation + Packaging:**
- Generates schema-compliant JSON from mapping guide
- Validates with `utils/validate-practice-json.py`
- Packages into `.keleo` archive with `utils/package-keleo.py`
- For methods: externalized method JSON with `practiceNames` string references (not embedded)
- Outputs `bundles/<name>.keleo` (primary) and individual JSON files in `practices/<name>/` (intermediate)

**Output Location**: All files for a practice are co-located in `practices/<practice-name>/`

The skill is defined in `.claude/skills/generate-method/SKILL.md` and uses the phase prompts from `prompts/`.

### Generating Reports

Use the `/method-based-report` skill to create plain English reports structured by practice/method narrative frameworks:

```
/method-based-report
```

The user provides a practice/method/baseline and a subject to report on. The skill:

1. **Plans** — Identifies practice context, subject, audience, and narrative strategy
2. **Loads Context** — Resolves the practice via `utils/resolve-context.py --transitive`
3. **Analyzes & Selects** — Extracts domain knowledge (alphas, activities, patterns, narratives) and selects baseline narrative structures that fit the report purpose
4. **Generates Report** — Writes a standalone markdown report to `reports/<report-name>.md`

The report uses narrative types from the baseline (Report Narrative, Essay Narrative, STAR, etc.) to organize content, and practice domain knowledge to inform the analysis — but presents everything in plain English with no Keleo terminology.

**Output Location**: `reports/<report-name>.md` (git-ignored — ephemeral deliverables)

The skill is defined in `.claude/skills/method-based-report/SKILL.md`.

### Processing Feedback

Use the `/plan-from-feedback` skill to triage and resolve issues from a feedback register:

```
/plan-from-feedback
```

The skill reads an issue register (Google Sheet) and for each "New" item:

1. **Triages** — Assesses the issue and determines the resolution approach
2. **Plans** — Identifies changes needed at up to three levels:
   - **L1: Practice/Method** — Direct fix to the reported document
   - **L2: keleo-pgen-llm** — Skill/utility improvement to prevent recurrence
   - **L3: keleo-language** — Schema/semantics improvement for systemic issues
3. **Executes** — Makes the changes, validates, and rebundles as needed
4. **Updates** — Writes status, rationale, and change details back to the register

The issue register URL is stored per-user in `.claude/user-config.json` (git-ignored). On first use, the skill prompts for the URL.

The skill is defined in `.claude/skills/plan-from-feedback/SKILL.md`.

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

**Phase 3 - JSON Generation + Packaging:**
7. Use `prompts/phase-3-json.md` to generate JSON
8. Validate with `python3 utils/validate-practice-json.py <practice-name>.json`
9. Package with `python3 utils/package-keleo.py --name <name> --version 1.0.0 --description "..." --documents <baseline>.json <practice>.json -o bundles/<name>.keleo`

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
- Gherkin-inspired structured guidance (background, test, examples) for verification and execution scenarios
