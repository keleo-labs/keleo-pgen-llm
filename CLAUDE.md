# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Practice Language Code Generation System** that uses LLMs in a two-phase pipeline to convert enterprise methodology documentation into standardized, schema-compliant JSON. The system analyzes source methodologies (e.g., AWS Well-Architected, SAFe, TOGAF, Team Topologies) and maps them to the Platform Adoption Essentials baseline framework.

## Directory Structure

```
keleo-pgen-llm/
├── .claude/
│   └── skills/
│       └── translate-methodology.md    # Main translation skill
├── deps/                               # Symlinks to keleo-studio
│   ├── language.schema.json           # JSON Schema definition
│   └── platform-adoption-kernel.json  # Baseline framework
├── references/                         # Analysis framework documentation
│   ├── domain-framework.md
│   ├── semantics.md
│   └── workproduct-assessment-rubric.csv
├── gemini-prompts/                     # Phase instructions (optimized for Claude)
│   ├── phase 1 gem.md
│   └── phase 2 gem.md
├── practices/                          # Generated output directory
│   └── <practice-name>/               # One subdirectory per practice/method
│       ├── research-report.md         # Phase 1: Human-readable analysis
│       └── <practice-name>.json       # Phase 2: Schema-compliant JSON
└── CLAUDE.md                          # This file
```

### Generated Output Location

All generated practices are stored in `practices/<practice-name>/`:
- **Phase 1** creates the subdirectory and writes `research-report.md`
- **Phase 2** writes `<practice-name>.json` in the same directory
- Practice names use kebab-case (e.g., `aws-well-architected`, `team-topologies`)

## Architecture

### Two-Phase LLM Pipeline

**Phase 1: Research Analysis**
- Input: Source methodology documentation
- Process: LLM acts as Practice Research Analyst
- Output: Human-readable structured research report
- Prompt: `gemini-prompts/phase 1 gem.md`

**Phase 2: JSON Translation**
- Input: Structured research report from Phase 1
- Process: LLM acts as Data Translation Engine
- Output: Schema-compliant JSON
- Prompt: `gemini-prompts/phase 2 gem.md`

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

### Prompts
- `gemini-prompts/phase 1 gem.md` - Research analyst prompt (82KB, comprehensive methodology translation instructions)
- `gemini-prompts/phase 2 gem.md` - JSON translation prompt (44KB, schema mapping and validation rules)

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

This skill automates the two-phase pipeline:
1. **Enters plan mode** to analyze sources and create execution plan
2. **Phase 1**: 
   - Analyzes source methodology using four-perspective framework
   - Determines practice/method name early in analysis
   - Creates `practices/<practice-name>/` subdirectory
   - Generates human-readable research report
   - Writes to `practices/<practice-name>/research-report.md`
3. **Phase 2**: 
   - Reads Phase 1 report from the practice subdirectory
   - Translates report into schema-compliant JSON
   - Writes to `practices/<practice-name>/<practice-name>.json`
4. **Validates** output against schema (optional)

**Output Location**: All files for a practice are co-located in `practices/<practice-name>/`

The skill is defined in `.claude/skills/translate-methodology.md` and comprehensively implements the prompts from `gemini-prompts/`.

### Manual Workflow

If working manually (e.g., with external LLM like Gemini):

1. **Gather source methodology** documentation (whitepapers, frameworks, guides)
2. **Feed to Phase 1 prompt** along with baseline framework and references
3. **Review generated report** for completeness and accuracy
4. **Feed report to Phase 2 prompt** to generate schema-compliant JSON
5. **Validate JSON** against `deps/language.schema.json`

## Working with Prompts

The prompts in `gemini-prompts/` have been optimized for use within the `/translate-methodology` skill:

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
