## Keleo Practice Generation System

An AI-powered system for converting enterprise methodology documentation into standardized, schema-compliant Practice Language JSON — and for generating domain-informed reports, project plans, reference architectures, and decision analyses from the resulting knowledge base.

## What it does

The system operates across two capability areas:

**Practice Engineering** — Analyze source methodologies (AWS Well-Architected, SAFe, TOGAF, Team Topologies, MEDDPICC, and many others) and transform them into structured, machine-readable Practice Language JSON. Supports both foundational baseline frameworks and extension practices that specialize them.

**Knowledge-Driven Reporting** — Use the domain knowledge encoded in practices and baselines to generate professional reports, reference architectures, project plans, decision analyses, and document reviews — all in plain English with no framework jargon.

## Get started

### Prerequisites

Use Codex, Claude Code, or Cursor with this checkout. Install Git and Python 3.9 or later. To run the local Studio MCP server, install Node.js 20 or later and obtain access to the [Keleo Studio MCP repository](https://gitlab.cee.redhat.com/planify/keleo-studio-mcp) and a Studio deployment. No content repository or baseline file is required.

```bash
git clone https://github.com/keleo-labs/keleo-pgen-llm.git
cd keleo-pgen-llm
python3 --version
node --version
```

### 1. Connect the language specification

Clone `keleo-language` beside this project. The tracked links in `deps/`, `references/`, and `utils/` resolve to that exact location.

```bash
# Run from the keleo-pgen-llm project root.
git clone https://github.com/keleo-labs/keleo-language.git ../keleo-language
test -f deps/language.schema.json
test -f deps/schemas/language.schema.json
test -f references/semantics.md
python3 utils/validate-practice-json.py --help
python3 utils/validate-baseline-json.py --help
```

If you already have `keleo-language`, place it at `../keleo-language` or point the tracked links to its location in your own checkout. The validators create their own virtual environment when needed; do not install packages into the system Python.

### 2. Install and connect Studio MCP

If `keleo-studio-mcp` is already connected, continue to authentication. Otherwise, clone the [MCP server](https://gitlab.cee.redhat.com/planify/keleo-studio-mcp) to any directory and install its Node dependencies. The example below uses `~/tools`; GitLab access is required. Set `KELEO_STUDIO_URL` to your Studio Apps Script deployment URL ending in `/exec`.

```bash
mkdir -p "$HOME/tools"
git clone https://gitlab.cee.redhat.com/planify/keleo-studio-mcp.git "$HOME/tools/keleo-studio-mcp"
cd "$HOME/tools/keleo-studio-mcp"
npm install
pwd -P  # Use this absolute directory in the client configuration below.
```

In **Codex**, run the command below, then restart or reload its MCP connection. Confirm the server appears with `codex mcp list`. The [official Codex MCP guidance](https://developers.openai.com/learn/docs-mcp) also describes configuration and verification.

```bash
codex mcp add keleo-studio --env KELEO_STUDIO_URL=YOUR_STUDIO_EXEC_URL -- node /absolute/path/to/keleo-studio-mcp/src/server.js
codex mcp list
```

In **Claude Code**, put the following in a local `.mcp.json` for this project. In **Cursor**, put the same server entry under `mcpServers` in `~/.cursor/mcp.json`. Replace the path and URL, then restart the client. Keep any existing server entries when you edit either file.

```json
{
  "mcpServers": {
    "keleo-studio": {
      "command": "node",
      "args": ["/absolute/path/to/keleo-studio-mcp/src/server.js"],
      "env": {
        "KELEO_STUDIO_URL": "YOUR_STUDIO_EXEC_URL"
      }
    }
  }
}
```

### 3. Authenticate and verify access

Ask your agent to call `keleo-studio` `start_auth`. Complete Google sign-in in the browser it opens. Ask it to call `auth_status` until it reports `authenticated`, then call `list_documents` with `kind: baseline` and retrieve one listed document with `get_document` using that entry's bundle slug and path. This confirms both authentication and document access without a local baseline file.

If the Studio deployment has no browser token bridge, ask the agent to call `start_auth_manual`. The token stays in the MCP process and expires after about 50 minutes. Repeat authentication after the MCP server restarts or the token expires.

### 4. Run a skill

Try: “Use `/generate-method` to turn this methodology into a practice. Find the relevant published baseline in Studio, confirm your choice with me, and plan the work.” Provide the methodology source, but no baseline path. The skill reads published content through Studio MCP and uses local files only for working output and validation.

Shared workflows live in `skills/`. Claude Code discovers `.claude/skills/`; Codex and Cursor discover `.agents/skills/`. Cursor may need third-party skill discovery disabled to avoid duplicate Claude adapters. Project hooks are tracked, while personal settings belong in your agent configuration. After editing a canonical skill, run `python3 utils/vendor-skills.py --fix` and then `python3 utils/vendor-skills.py --check`.

### Troubleshooting

If a language link is broken, check that `../keleo-language` exists and rerun the `test -f` commands above. If MCP tools are missing, check `node --version`, the absolute server path, `KELEO_STUDIO_URL`, and the client connection after a restart. If `auth_status` is unauthenticated, call `start_auth` again. If a document is missing or access is denied, confirm that your Google account can open the Studio deployment and that `list_documents` includes the expected name. Do not substitute a sibling content repository for missing Studio access.

### Optional content repositories

You may mount selected practices, baselines, or reports from separate repositories to manage private authorship and versioning. Follow the [content repository guide](docs/content-repos.md). Mounts are optional; a fresh checkout uses Studio MCP for published content.

### Migrating from the REST client

Replace `utils/studio-client.py` and the `--remote` or `--auto-pull` discovery flags with the Studio MCP steps above. Published documents now come from `list_documents` and `get_document`; the agent converts them for local validation with `utils/materialize-studio-document.py`. Publish bundles with `upload_package`. Remove any old `keleoStudioGasToken` from your ignored `config/user-config.json`; MCP keeps its token in process memory. Existing local and mounted workspaces stay in place.

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

Team-meeting (`/team-meeting`) adds a shared team briefing with a summary, working
agreement, last-meeting retrospective, News, discussion agenda and supporting
analysis. Configure each series under `reports/<series-slug>/series.json`; dated
subfolders retain each meeting's report and evidence. Signals combine the project
list at `config/team-meeting/signals.json` with additional series definitions.
Use `python3 utils/team-meeting.py --help` and the skill's workspace reference.

### Presentations

Deck skills author **Slidev** markdown and publish to Google Slides and PDF. They share `skills/deck-foundation/` (pipeline, layouts, conversion constraints, the Red Hat theme and the publishing scripts). By default a deck follows the structure of its source document rather than re-arguing the material.

| Skill | Command | Purpose |
|-------|---------|---------|
| **Slide Deck** | `/slide-deck` | Any deck not covered below — talks, training, overviews, workshops |
| **Pitch Deck** | `/pitch-deck` | Value propositions, partner/GSI pitches, solution proposals, business cases |
| **Exec Readout** | `/exec-readout` | Status reports, findings, review outcomes, programme updates |

Requires Node.js 18+ (Slidev), Playwright chromium (pptx export) and the global Codex `gws` skill backed by Google Workspace MCP (Drive import). See `skills/deck-foundation/DECK-FOUNDATION.md`.

### System Improvement

| Skill | Command | Purpose |
|-------|---------|---------|
| **Report Issue** | `/report-issue` | Record issues, enhancements, or questions in the feedback register for later triage |
| **Plan from Feedback** | `/plan-from-feedback` | Triage issues from a feedback register, plan and execute fixes across practice, skill, and schema layers |
| **Improve Tooling** | `/improve-tooling` | Create, extend, or consolidate utility scripts; improve skill instructions |
| **Content Repos** | `/content-repos` | Create and manage separate git repositories for selected practices, baselines, and reports |

`/report-issue` and `/plan-from-feedback` are two ends of the same register: the first files rows (input columns, Status `New`), the second triages them and writes back the resolution. Both share the register configured in `config/user-config.json`.

## Pipeline Architecture

### Local research catalogs

Generation keeps two local authoring indexes. `source-catalogs/` holds reusable,
versioned source snapshots with section text and locators. Each generated practice
or baseline workspace holds `practice-catalog.json`, an index of its elements and
their supporting source sections. Run `python3 utils/catalog.py --help` to add a
source, inspect its outline or search sections, then build and check a practice
catalog. A changed or unreachable source remains available as a stale snapshot;
verify a current source before using it for a new claim. Both catalogs are ignored
by Git and excluded from `.keleo` packages. Citations and references remain in
the practice JSON.

This section-based navigation takes its cue from [Kumar et al., *STAIR:
STructure Aware Information Retriever* (2026)](https://arxiv.org/html/2609.03874v1).
Their reported results concern a fine-tuned retriever on the SearchTome benchmark;
this project uses document structure for local lookup and does not reproduce that
model or claim its retrieval accuracy.

### Extension Practices (3-phase)

```
Source Docs → Phase 1: Analysis → Phase 2: Mapping → Phase 3: JSON + Packaging
               (~30-50K words)     (~40-60K words)    (schema-valid .keleo)
                     ↓                   ↓                    ↓
                   gate                gate                 gate
```

1. **Analysis** — Four-perspective analysis (Business, Technology, People, Process) of methodology structure
2. **Mapping** — Map to baseline practice using Practice Language semantics; alpha-state-activity gap analysis
3. **JSON + Packaging** — Generate schema-compliant JSON, validate, bundle into `.keleo` package

A delineation gate between phases 1 and 2 determines whether the methodology maps to a single practice (3–7 alphas) or a multi-practice method (8+ alphas).

### Baseline Practices (4-phase)

```
Source Docs → Phase 1: Analysis → Phase 1.5: Distillation → Phase 2: Mapping → Phase 3: JSON
               (~30-50K words)     (~15-25K words)           (~40-60K words)    (schema-valid)
                     ↓                     ↓                        ↓                ↓
                   gate                  gate                     gate             gate
```

The additional **Distillation** phase identifies focus areas, distills 8–15 foundational alphas, generalizes activity spaces, and defines competencies and narrative types.

### Why the pipeline has gates

The pipeline is a loop wrapped around a probabilistic model, and a model cannot grade its own output. Producing fluent text that corresponds to nothing in the source is not a bug in these systems — it is how they work — so every phase ends with a check the generating agent does not get to make. Frank Coyle sets out the general argument in [Why agentic systems need ontologies](https://www.youtube.com/watch?v=Sir59K8ZDPU); the Practice Language is the ontology this pipeline checks against.

Each gate has three parts:

```
producing agent(s) → mechanical validation → verification gate → user review gate → next phase
```

**Mechanical validation** checks structure, counts and cross-references — the things a script can settle. **Verification** checks meaning: agents reread the source material and establish that the output traces back to it, that citations support what they are attached to, and that nothing was invented between phases. Confirmed errors block the phase; warnings flow into the **user review gate**, where a person decides.

Nothing is packaged or uploaded before those pass. The `.keleo` archive is the side effect, and it is withheld until the document is sound — a practice that fails validation never becomes a bundle anyone can consume.

| Stage | Verifiers |
|-------|-----------|
| 1 — Analysis | `source-fidelity`, `source-coverage`, `citation-integrity` |
| 1.5 — Distillation (baseline only) | `distillation-fidelity`, `focus-coherence` |
| 2 — Mapping | `source-fidelity`, `alpha-semantics`, `coverage`, `naming-consistency` |
| 3 — JSON generation | `generation-drift`, `reference-citation-fidelity` |
| Reports — single gate | `source-fidelity`, `citation-integrity`, `domain-grounding`, `register-and-style` |

The protocol and the per-phase agent briefs live in [`skills/verification-foundation/`](skills/verification-foundation/). Findings are consolidated by `utils/verification-gate.py`. The gate costs real tokens — roughly 12 verifier agents for a single practice, 30 for a four-practice method — so `VERIFY-FOUNDATION.md` §11 sets the sampling, concurrency and effort controls that keep it proportionate.

### Output Packaging

Practice engineering skills produce `.keleo` packages: ZIP archives containing a manifest, Practice Language JSON documents and optional assets. Publish an approved package through Studio MCP.

## Project Structure

```
keleo-pgen-llm/
├── skills/                   # Canonical skills and shared foundations
├── .agents/skills/           # Codex and Cursor skill entrypoints
├── .claude/skills/           # Claude Code skill entrypoints
├── .cursor/                  # Cursor instructions and hooks
├── deps/                     # Symlinks to keleo-language; legacy local baseline link
├── references/               # Domain framework, semantic guidance, assessment rubrics
├── prompts/                  # Phase-specific prompt templates
├── practices/                # Extension practice outputs (per-practice subdirectories)
├── baselines/                # Baseline practice outputs (per-baseline subdirectories)
├── bundles/                  # Packaged .keleo output
├── reports/                  # Generated reports (optional content repo mounts)
├── utils/                    # ~80 Python utility scripts (validation, packaging, transforms)
└── AGENTS-ALL.md             # Shared project guidance
```

### Key dependencies

| File | Purpose |
|------|---------|
| `deps/schemas/` | Modular Practice Language schema sources and separate catalog schemas |
| `deps/language.schema.json` | Generated compatibility schema for existing validators |
| `deps/platform-adoption-kernel.json` | Legacy link to an optional local Platform Adoption baseline; fresh checkouts resolve it through Studio MCP |
| `references/semantics.md` | Semantic guidance hub (indexes sub-documents) |
| `references/domain-framework.md` | Enterprise architecture analysis framework |

## Validation

```bash
# Validate an extension practice against its selected baseline
python3 utils/validate-practice-json.py practices/<name>/<name>.json <baseline.json> deps/language.schema.json --brief

# Validate a baseline
python3 utils/validate-baseline-json.py baselines/<name>/<name>.json deps/language.schema.json

# Inspect a .keleo package
python3 utils/inspect-keleo.py bundles/<name>.keleo

# Assess practice quality
python3 utils/assess-practice.py practices/<name>/<name>.json
```

## Publish a bundle

Validate and package the documents locally. To publish an approved `.keleo` bundle, ask your agent to call Studio MCP `upload_package` with its absolute file path. Studio checks your account's create permission. Use `list_packages` to confirm the upload.

## Learn More

- **[AGENTS-ALL.md](AGENTS-ALL.md)** — Shared technical guidance: architecture, schema rules, framework concepts and constraints
- **`skills/*/SKILL.md`** — Individual skill implementation details
- **`references/`** — Domain framework, semantic guidance, assessment rubrics
- **`prompts/`** — Phase-specific prompt templates
- **[keleo-language](https://github.com/keleo-labs/keleo-language)** — The Practice Language schema and semantics, including the constraint model this pipeline validates against

### References

- Coyle, F. (n.d.). *Why agentic systems need ontologies* [Video]. https://www.youtube.com/watch?v=Sir59K8ZDPU
- Gruber, T. R. (1993). A translation approach to portable ontology specifications. *Knowledge Acquisition, 5*(2), 199–220. https://doi.org/10.1006/knac.1993.1008
- Garcez, A. d'Avila, & Lamb, L. C. (2023). Neurosymbolic AI: the 3rd wave. *Artificial Intelligence Review, 56*, 12387–12406. https://doi.org/10.1007/s10462-023-10448-w
- Agrawal, G., Kumarage, T., Alghamdi, Z., & Liu, H. (2024). Can knowledge graphs reduce hallucinations in LLMs? A survey. *NAACL 2024*, 3947–3960. https://aclanthology.org/2024.naacl-long.219/
