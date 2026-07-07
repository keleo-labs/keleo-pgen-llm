# Practice Language Code Generation System

A Claude-powered system that converts enterprise methodology documentation into standardized, schema-compliant JSON using a three-phase LLM pipeline.

## Purpose

This system analyzes source methodologies (AWS Well-Architected, SAFe, TOGAF, Team Topologies, etc.) and maps them to the **Platform Adoption Essentials** baseline framework, generating machine-readable Practice Language JSON. The output enables:

- Consistent methodology representation across diverse frameworks
- Automated tooling for practice adoption and assessment
- Cross-methodology comparison and integration
- Evidence-based maturity tracking

## Quick Overview

The system uses a three-phase pipeline:

```
Source Docs → Phase 1: Analysis → Phase 2: Mapping → Phase 3: JSON
              (~30-50K words)      (~40-60K words)    (schema-valid)
```

Each phase generates structured output that feeds into the next, with final validation producing schema-compliant Practice Language JSON.

**For detailed architecture, framework concepts, and technical documentation**, see **[CLAUDE.md](CLAUDE.md)**

## Getting Started

### Prerequisites

1. **Claude Code**: [Claude Code](https://claude.ai/code) (CLI, desktop app, or web)
2. **keleo-studio Repository**: Must be at `../keleo-studio/` (one directory up from project root)
3. **Python 3.x**: For validation (optional)

### Verify Setup

```bash
# Check keleo-studio symlinks
ls -l deps/

# In Claude Code, verify skill is loaded
/help
# Should list "generate-method"
```

## Using the Translation Skill

### Basic Usage

The primary workflow uses the `/generate-method` skill in Claude Code:

```
/generate-method [source files or URLs]
```

**Examples:**

```bash
# Single methodology document
/generate-method practice-resources/team-topologies/team-topologies-book.pdf

# Multiple source files
/generate-method practice-resources/partner-demand-generation/*.md

# URLs (Claude will fetch)
/generate-method https://example.com/methodology-guide.pdf
```

### What the Skill Does

The skill automates the complete three-phase pipeline:

**1. Planning Phase (Automatic)**
- Analyzes source materials
- Determines if content is a single Practice or multi-practice Method
- Creates execution roadmap

**2. Phase 1 - Analysis**
- Reads source materials
- Applies four-perspective analysis (Business, Technology, People, Process)
- Generates `01-analysis-report.md` (~30-50K words)

**3. Phase 2 - Mapping**
- Maps analyzed content to baseline practice
- Uses semantic guidance from `references/semantics.md`
- Performs alpha-state-activity gap analysis
- Generates `02-mapping-guide.md` (~40-60K words)

**4. Phase 3 - JSON Generation**
- Generates schema-compliant JSON
- Validates against `deps/language.schema.json`
- Outputs `<practice-name>.json` or `<method-name>.json`

### Output Location

All generated files for a practice are co-located in `practices/<practice-name>/`:

```
practices/<practice-name>/
├── 01-analysis-report.md          # Phase 1 output
├── 02-mapping-guide.md            # Phase 2 output
└── <practice-name>.json           # Phase 3 output (validated)
```

### Validation

The skill automatically validates output. Manual validation:

```bash
python3 utils/validate-practice-json.py practices/<practice-name>/<practice-name>.json
```

## Learn More

- **[CLAUDE.md](CLAUDE.md)** - Complete architecture, framework concepts, schema rules, and technical details
- **`.claude/skills/generate-method/SKILL.md`** - Skill implementation details
- **`references/`** - Domain framework, semantics, and assessment rubrics
- **`prompts/`** - Phase-specific prompt templates

## License

[Add your license information here]

## Contact

[Add contact/support information here]
