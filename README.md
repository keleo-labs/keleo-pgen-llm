# Keleo Practice Generation System

An AI-powered system for converting enterprise methodology documentation into standardized, schema-compliant Practice Language JSON — and for generating domain-informed reports, project plans, reference architectures, and decision analyses from the resulting knowledge base.

## What It Does

The system operates across two capability areas:

**Practice Engineering** — Analyze source methodologies (AWS Well-Architected, SAFe, TOGAF, Team Topologies, MEDDPICC, and many others) and transform them into structured, machine-readable Practice Language JSON. Supports both foundational baseline frameworks and extension practices that specialize them.

**Knowledge-Driven Reporting** — Use the domain knowledge encoded in practices and baselines to generate professional reports, reference architectures, project plans, decision analyses, and document reviews — all in plain English with no framework jargon.

## Quick Start

### Prerequisites

- **Claude Code** — [CLI, desktop app, or web](https://claude.ai/code)
- **Python 3.9+** — Validation and utility scripts (standard library only, no pip packages)
- **keleo-language repo** — Cloned at `../../keleo-language/` relative to this project root

### Setup

```bash
# 1. Clone keleo-language alongside this repo
git clone <repo-url> ../../keleo-language

# 2. Verify symlinks resolve
ls -la deps/ references/

# 3. (Optional) Configure remote bundle repository
python3 utils/studio-client.py --configure
```

### Verify

```bash
python3 utils/validate-practice-json.py --help
python3 utils/assess-practice.py --help
```

## Skills

All skills are invoked as slash commands in Claude Code. Each skill plans its work, asks for approval, then executes autonomously.

### Practice Engineering

| Skill | Command | Purpose |
|-------|---------|---------|
| **Create Baseline** | `/create-baseline-method` | Create foundational framework baselines (focuses, root alphas, competencies, activity spaces, narrative types) |
| **Generate Method** | `/generate-method` | Create extension practices/methods that specialize a baseline with concrete alphas, activities, work products, and patterns |
| **Update Method** | `/update-method` | Update existing practice/method JSON to align with latest guidance and baseline changes |

**When to use which:**

- `/create-baseline-method` — Source methodology defines a **universal ontology** for a domain (e.g., Platform Adoption Essentials, Partner Ecosystem Essentials)
- `/generate-method` — Source methodology **implements or specializes** an existing baseline (e.g., AWS Well-Architected extends Platform Adoption)

### Reporting

All reporting skills resolve practice context, extract domain knowledge, and generate standalone markdown reports. The audience sees domain insight, not Keleo internals.

| Skill | Command | Purpose |
|-------|---------|---------|
| **General Report** | `/method-based-report` | Any report type — flexible narrative structure, catch-all |
| **Reference Architecture** | `/reference-architecture` | Topology, component selection, evaluation frameworks, sizing |
| **Project Plan** | `/project-plan` | Project plans, PoC outlines, Statements of Work (T&M) |
| **Decision Analysis** | `/decision-analysis` | Trade-off analysis, option weighting, contextual verdicts |
| **Document Review** | `/document-review` | Review an existing document and recommend improvements |

### System Improvement

| Skill | Command | Purpose |
|-------|---------|---------|
| **Plan from Feedback** | `/plan-from-feedback` | Triage issues from a feedback register, plan and execute fixes across practice, skill, and schema layers |
| **Improve Tooling** | `/improve-tooling` | Create, extend, or consolidate utility scripts; improve skill instructions |

## Pipeline Architecture

### Extension Practices (3-phase)

```
Source Docs → Phase 1: Analysis → Phase 2: Mapping → Phase 3: JSON + Packaging
               (~30-50K words)     (~40-60K words)    (schema-valid .keleo)
```

1. **Analysis** — Four-perspective analysis (Business, Technology, People, Process) of methodology structure
2. **Mapping** — Map to baseline practice using Practice Language semantics; alpha-state-activity gap analysis
3. **JSON + Packaging** — Generate schema-compliant JSON, validate, bundle into `.keleo` package

A delineation gate between phases 1 and 2 determines whether the methodology maps to a single practice (3–7 alphas) or a multi-practice method (8+ alphas).

### Baseline Practices (4-phase)

```
Source Docs → Phase 1: Analysis → Phase 1.5: Distillation → Phase 2: Mapping → Phase 3: JSON
               (~30-50K words)     (~15-25K words)           (~40-60K words)    (schema-valid)
```

The additional **Distillation** phase identifies focus areas, distills 8–15 foundational alphas, generalizes activity spaces, and defines competencies and narrative types.

### Output Packaging

All skills produce `.keleo` packages — ZIP archives containing a manifest, Practice Language JSON documents, and optional assets. Packages can be uploaded to a remote bundle repository for consumption by Keleo Studio.

## Project Structure

```
keleo-pgen-llm/
├── .claude/skills/           # Skill definitions (10 skills + shared reporting foundation)
├── deps/                     # Symlinks to keleo-language (schema, baseline JSONs)
├── references/               # Domain framework, semantic guidance, assessment rubrics
├── prompts/                  # Phase-specific prompt templates
├── practices/                # Extension practice outputs (per-practice subdirectories)
├── baselines/                # Baseline practice outputs (per-baseline subdirectories)
├── bundles/                  # Packaged .keleo output
├── reports/                  # Generated reports (git-ignored)
├── utils/                    # 50+ Python utility scripts (validation, packaging, transforms)
└── CLAUDE.md                 # Full technical documentation
```

### Key Dependencies (symlinked from keleo-language)

| File | Purpose |
|------|---------|
| `deps/language.schema.json` | Practice Language JSON Schema |
| `deps/platform-adoption-kernel.json` | Platform Adoption Essentials baseline |
| `deps/partner-ecosystem-baseline.json` | Partner Ecosystem Essentials baseline |
| `references/semantics.md` | Semantic guidance hub (indexes sub-documents) |
| `references/domain-framework.md` | Enterprise architecture analysis framework |

## Validation

```bash
# Validate an extension practice
python3 utils/validate-practice-json.py practices/<name>/<name>.json

# Validate a baseline
python3 utils/validate-baseline-json.py baselines/<name>/<name>.json

# Inspect a .keleo package
python3 utils/inspect-keleo.py bundles/<name>.keleo

# Assess practice quality
python3 utils/assess-practice.py practices/<name>/<name>.json
```

## Remote Bundle Repository

Packaged `.keleo` bundles can be uploaded to a remote repository for use in Keleo Studio:

```bash
# Configure credentials
python3 utils/studio-client.py --configure

# List remote packages
python3 utils/studio-client.py --list

# Upload a bundle
python3 utils/studio-client.py --upload bundles/<name>.keleo
```

## Learn More

- **[CLAUDE.md](CLAUDE.md)** — Full technical documentation: architecture, schema rules, framework concepts, constraints
- **`.claude/skills/*/SKILL.md`** — Individual skill implementation details
- **`references/`** — Domain framework, semantic guidance, assessment rubrics
- **`prompts/`** — Phase-specific prompt templates
