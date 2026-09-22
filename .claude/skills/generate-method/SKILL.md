---
name: generate-method
description: Generate Practice Language JSON from methodology documentation using clean 3-phase workflow (Analysis → Mapping → JSON)
triggerPatterns:
  - "generate.*method"
  - "generate.*practice"
  - "create.*method"
  - "analyze.*methodology"
  - "map.*methodology"
---

# Method Generation Skill (3-Phase)

This skill transforms enterprise methodology documentation into schema-compliant Practice Language JSON using a clean three-phase workflow that delegates to reference documents rather than embedding knowledge.

## Workflow Overview

**Phase 1: Analysis** → Structure methodology into outcomes, concerns, activities, workflows, practices  
**Phase 2: Mapping** → Map to baseline practice using semantic guidance  
**Phase 3: JSON** → Generate schema-compliant JSON with programmatic validation

Each phase is delegated to a subagent that reads a **phase skill document** in `phases/`. The orchestrator (this file) handles planning, context resolution, delineation, and subagent dispatch.

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — these are prohibited; use reusable utils instead |
| Creating or extending a utility script | §7.4 — follow the Utils Self-Extension Protocol |
| Needing functionality that no existing util covers | §7.4 — create/extend, don't work around it |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |
| Writing prose rules that have a clear pass/fail criterion | §9 — convert to Gherkin scenarios instead |
| Adding or modifying Gherkin scenarios in any SKILL.md | §1–6 — rule structure, categories, and triple-duty |
| Adding a new validation check to assess/validate scripts | §7.2 — follow the Adding New Checks protocol |

**How to read:** `Read .claude/skills/SKILL-STANDARD.md` — then navigate to the relevant `## N.` heading.

---

## Critical Process: ALWAYS Use EnterPlanMode

**MANDATORY FIRST STEP:** Before starting ANY phase, you MUST use EnterPlanMode to:

1. Analyze source materials thoroughly
2. Determine if this is a Practice or Method (multiple practices)
3. Plan phase execution strategy
4. Identify baseline practice to use
5. Create execution roadmap

**Do NOT proceed without planning.**

---

## Directory Structure

### Output Location

All generated outputs for a practice go in `practices/<practice-name>/`:

```text
practices/
└── <practice-name>/
    ├── 01-analysis-report.md      (Phase 1 output, ~30-50K words)
    ├── 02-mapping-guide.md         (Phase 2 output, scales with alpha count: ~5-6K words/alpha)
    └── <practice-name>.json        (Phase 3 output, schema-compliant JSON)

bundles/
└── <practice-name>.keleo           (Package: practice + baseline bundled)
```

For methods with multiple practices:

```text
practices/
└── <method-name>/
    ├── 01-analysis-report.md       (Covers all practices)
    ├── 02-mapping-guide.md         (Maps all practices)
    └── <practice-name>.json        (Per-practice standalone JSONs)

bundles/
└── <method-name>.keleo             (Package: method + practices + baseline)
```

---

## Reference Documents

This skill relies on reference documents (READ via Read tool, NOT embedded):

### Required References

1. **references/domain-framework.md** - Four-perspective analysis framework
2. **references/semantics/** — Practice Language semantic guidance (sub-documents):
   - `semantics/composition.md` — aliasing, alpha hierarchies, dependencies (§4)
   - `semantics/practice-elements.md` — PracticeElement foundations, Gherkin guidance (§5)
   - `semantics/alphas.md` — alpha-state semantics, references/instances (§6)
   - `semantics/work-products.md` — work product rules (§7)
   - `semantics/execution-and-patterns.md` — patterns, outcomes, activities (§8-9)
   - `semantics/narrative-and-assets.md` — narrative management, assets (§10-11)
3. **deps/language.schema.json** - JSON Schema definition
4. **Baseline Practice JSON** - User-provided (e.g., `deps/platform-adoption-kernel.json`)

### Phase Skill Documents

Subagents read these instead of the phase prompts. Each is a self-contained orchestration document with reading plans, output format requirements, and validation commands:

- **phases/phase-1-skill.md** - Analysis phase subagent instructions
- **phases/phase-2-skill.md** - Mapping phase subagent instructions
- **phases/phase-3-skill.md** - JSON generation phase subagent instructions

---

## Execution Workflow

### Step 0: EnterPlanMode (REQUIRED)

**YOU MUST DO THIS FIRST.**

In plan mode:

1. **Read source materials completely**
   - All provided PDFs, URLs, markdown files
   - Take comprehensive notes

2. **Identify context sources (baselines, practices, methods, .keleo bundles):**
   - Ask user which baseline, parent practice/method, or `.keleo` bundle(s) to use
   - User can provide **file paths** (`.json` or `.keleo`), **names**, or a mix
   - **Auto-discover by name:** If user provides a name (no `/`, doesn't end in `.json`/`.keleo`), resolve it:
     ```bash
     python3 utils/discover-dependencies.py --resolve "Name Provided By User"
     ```
     - `found` → use the resolved path
     - `ambiguous` → present candidates to user, let them choose (filesystem entries preferred over bundle copies)
     - `not_found` → attempt remote download:
       ```bash
       python3 utils/studio-client.py --pull "Name Provided By User"
       ```
       If pull succeeds, re-resolve. If pull fails (auth error, not found remotely), ask user for the file path.
   - **`.keleo` bundles:** Accepted directly — all documents inside are extracted and classified
   - **Classify all inputs:**
     ```bash
     python3 utils/resolve-context.py <input1> [<input2> ...] --check-only
     ```
     Reports tiers (baselines, practices, methods) and document count. Review with user.
   - Report detected context sources and tiers to user

3. **Initial structure assessment (preliminary only):**
   - **Note:** Final practice delineation happens in Step 1.5 (Delineation Gate) before Phase 2 delegation
   - Check for obvious separation signals from source:
     - Multiple distinct use-cases? Different stakeholder journeys? Clearly separate capability domains?
   - **If obvious separation:** Plan for method with multiple practices
   - **If unified framework:** Plan for single practice (subject to Phase 2 validation)
   - **Key principle:** Don't determine primary alphas or practice boundaries yet — you need baseline context first

4. **Reference strategy (present to user):**
   - Estimate reference yield from source materials
   - **Few candidates** (0-2) → recommend secondary research (Step 2.5)
   - **Moderate** (3-5) → optional, user decides
   - **Many** (6+) → skip secondary research

5. **Plan execution:**
   - Tentative practice/method name (kebab-case)
   - Phase execution sequence
   - Expected complexity and size
   - Whether secondary reference research (Step 2.5) will be performed

6. **Exit plan mode** with clear execution roadmap

---

### Step 0.5: Unified Context Resolution

**Objective:** Produce a single `_effective-context.json` containing all inherited elements from baselines, parent practices, and methods, with provenance annotations (`_contributingPracticeName`) on every element.

**Process:**

1. **Collect all context sources** from Step 0:
   - The baseline practice (`.json` file or discovered by name)
   - Any parent practices/methods the user wants to extend (`.json` or `.keleo` files)
   - `.keleo` bundles are accepted directly — all documents inside are extracted

2. **Run unified context resolution:**
   ```bash
   python3 utils/resolve-context.py \
     <baseline.json> [<parent-practice.json>] [<bundle.keleo>] \
     --transitive \
     -o <output-dir>/_effective-context.json
   ```
   
   The utility:
   - Accepts `.json` and `.keleo` files (extracts all documents from bundles)
   - Classifies documents into three tiers: baselines, practices, methods
   - Resolves transitive baseline dependencies automatically (`--transitive`)
   - Merges in hierarchy order: baselines (root-first topo sort) → practices → methods
   - Stamps `_contributingPracticeName` on **every element** (provenance)
   - Applies unified `_aliasContext` and `_domainAlias` annotations
   - Builds `_provenance` manifest (merge order, tier membership, element-to-source mapping)
   
   Report the effective context composition to the user (tiers, alpha count, merge order, etc.).

3. **Identify the validation baseline:**
   The `_provenance.tiers.baselines` array shows which baselines were merged. For **validation**, always use the **leaf baseline file** (the most specific baseline in the chain).
   
   Record:
   - `effectiveContextPath` = `<output-dir>/_effective-context.json`
   - `validationBaselinePath` = path to the leaf baseline JSON (for validation only)

4. **How the mapping agent uses `_contributingPracticeName`:**
   - **Baseline elements** (source in `_provenance.tiers.baselines`): Ontology-level concepts. Can redeclare or specialize.
   - **Practice elements** (source in `_provenance.tiers.practices`): Came from parent practices. `contributesTo`/`mapsTo` targets create `practiceDependencyNames` entries.
   - **Method elements** (source in `_provenance.tiers.methods`): Coordination-level concepts.

**User Feedback:**
- "Context resolution complete: N baselines, M practices, K methods merged"
- "Using _effective-context.json for analysis/mapping. Leaf baseline '<name>' for validation."

**CRITICAL:** All structural references in generated JSON MUST use canonical names. Aliases inform semantic understanding only — they do NOT appear in generated JSON output.

**CRITICAL:** If context resolution fails (unresolved dependencies, missing files), STOP and discuss alternatives.

---

## Token Budget Management

**CRITICAL:** To avoid token budget exhaustion, use the multi-agent approach for ALL translations.

**ALWAYS use Agent tool** for Phase 1, Phase 2, and Phase 3. Each agent:
- Reads its phase skill document (`phases/phase-N-skill.md`)
- Has an isolated token budget (no context window pressure)
- Produces consistent quality (no degeneration from long conversations)

The main agent handles: Step 0 (planning), Step 0.5 (context resolution), Step 1.5 (delineation gate), Step 2.5 (reference research), and post-completion review.

**For multi-practice methods:** Launch parallel agents (one per practice) for Phase 2 and Phase 3. Each agent is self-contained — launch them in a single message with multiple Agent tool calls for concurrent execution.

### Why This Works

Each phase is **stateless** and **file-driven**:
- Phase 1 reads: source materials, domain-framework.md
- Phase 2 reads: 01-analysis-report.md, effective context JSON, semantics sub-documents
- Phase 3 reads: 02-mapping-guide.md, effective context JSON, language.schema.json

No conversational context required — only file contents.

---

### Step 1: Phase 1 — Analysis

**Objective:** Extract and organize methodology into structured analysis.

**Dispatch to subagent:**

1. Read `phases/phase-1-skill.md` to understand what the subagent will do
2. Launch Agent with prompt including:
   - Practice name and source material file paths
   - Instruction to read `phases/phase-1-skill.md` first
   - Output location: `practices/<practice-name>/01-analysis-report.md`

3. After agent completes, validate:
   ```bash
   python3 utils/eval-skill-output.py practices/<name>/ --phase 1 --summary
   ```

Fix any FAIL assertions before proceeding to Step 1.5.

### Step 1.5: Practice Delineation Gate (Main Agent Only)

**Objective:** Determine practice structure BEFORE delegating Phase 2 mapping.

**CRITICAL:** This step MUST be performed by the main agent, not delegated to subagents. The delegation strategy (single agent vs parallel agents) depends on this step's outcome.

**Process:**

1. **Load baseline practice JSON** (use effective context from Step 0.5):
   ```bash
   python3 utils/extract-reference-names.py <effective-context-or-baseline.json> --sections focuses alphas activitySpaces competencies narrativeTypes --alpha-details
   ```
   
   If the effective context has `_aliasContext`, review domain aliases for semantic understanding. Use canonical names for structural decisions.

   **Parent Practice Mode:** Use `_contributingPracticeName` to distinguish baseline-level alphas from practice-level alphas.

2. **Map Phase 1 concerns to alphas:**
   - Which baseline alphas does the content enrich (redeclarations)?
   - Which need specialization (`contributesTo`) or variant mapping (`mapsTo`)?
   - Count total baseline alpha coverage

3. **Analyze coverage pattern:**
   - **Focused** (3-7 alphas in 1-2 focuses) → Likely single practice
   - **Broad** (8+ alphas across all 3 focuses) → Likely method requiring subdivision

4. **If focused (3-7 alphas):**
   - Identify ONE primary alpha from content
   - Use baseline `relatesTo` to find related alphas (1-level deep)
   - **Decision: Single Practice** ✓

5. **If broad (8+ alphas):**
   - Identify multiple potential primary alphas
   - For each: what content clusters around it? What related alphas (via `relatesTo`) does it pull in?
   - **Decision: Method with 2+ Practices** ✓

6. **If unclear:** Ask user for guidance.

**GATE DECISION:**
- **Single Practice** → Step 2 delegates to one agent
- **Multi-Practice Method** → Step 2 launches parallel agents, one per practice

**Pass delineation results to Phase 2 agents:** primary alpha, alpha coverage list, practice boundaries.

For the full Primary Alpha Focus Strategy with worked examples, read `references/practice-method-strategy.md`.

### Step 2: Phase 2 — Mapping

**Objective:** Map Phase 1 analysis to baseline practice framework.

**Prerequisite:** Step 1.5 delineation gate must be complete.

**Dispatch to subagent(s):**

1. Read `phases/phase-2-skill.md` to understand what the subagent will do
2. Launch Agent(s) with prompt including:
   - Instruction to read `phases/phase-2-skill.md` first
   - Practice name, description, and file paths:
     - `practices/<name>/01-analysis-report.md` (analysis report)
     - `<effective-context-path>` (from Step 0.5)
     - Leaf baseline path (for validation)
   - Delineation context from Step 1.5 (primary alpha, alpha coverage, practice boundaries)
   - If `_aliasContext` present: note that aliases inform semantic understanding but all structural references use canonical names

**For multi-practice methods:** Launch parallel agents (one per practice) in a single message.

3. **After all agents complete:**
   - **Check for placeholder sections:**
     ```bash
     grep -n '\[\.\.\..*\]' practices/<method-name>/02-mapping-guide-practice-*.md
     ```
     If placeholders found, resume the agent to complete them.
   - **Assemble mapping guides** (methods only):
     ```bash
     python3 utils/assemble-mapping-guide.py \
       --name "<method-name>" \
       --baseline-name "<baseline-name>" \
       --guides practices/<method-name>/02-mapping-guide-practice-*.md \
       -o practices/<method-name>/02-mapping-guide.md \
       --stats
     ```
   - **Validate:**
     ```bash
     python3 utils/eval-skill-output.py practices/<name>/ --phase 2 --summary
     ```

Fix any FAIL assertions before proceeding to Phase 3.

### Step 2.5: Secondary Reference Research (Opt-In)

**Skip if Step 0 determined secondary research is not needed.**

**Objective:** Discover additional reference content to supplement source materials, using Phase 2 alpha/state/work-product mappings as a search framework.

**Process:**

1. Review the "Reference Content Mappings" section of `02-mapping-guide.md` — identify coverage gaps
2. Search for additional references (templates, tools, reference implementations, case studies)
3. Map discovered references following `references/semantics/alphas.md` §6.6:
   - Concept-oriented names (pattern: `"Standard [Qualifier] <AlphaName>"`)
   - `evidenceBy` as full WorkProductInstance objects with `name`, `description`, `workProductName`, `levelOfDetailName`, and `links`
   - Instance names scope to the **example**, not the state/LOD
   - Merge same-name instances (key on instance `name`, keep highest state/LOD, aggregate links)
   - Drop candidates without links
4. Present findings to user for approval
5. Append approved references to mapping guide

### Step 3: Phase 3 — JSON Generation

**Objective:** Generate schema-compliant Practice or Method JSON.

**Dispatch to subagent(s):**

1. Read `phases/phase-3-skill.md` to understand what the subagent will do
2. Launch Agent(s) with prompt including:
   - Instruction to read `phases/phase-3-skill.md` first
   - All required inputs (see phase skill's Inputs table):
     - Practice name and directory path
     - Effective context path, leaf baseline path, schema path
     - `baselinePracticeName` value
     - `practiceDependencyNames` array
     - Whether in parent practice mode
     - Whether effective context has `_aliasContext`
   - Output location: `practices/<name>/<name>.json`

**For multi-practice methods:** Launch parallel agents (one per practice) in a single message.

3. **After all practice JSONs complete (methods only):**
   - Review Phase 1 analysis for method-level overarching narrative
   - Create method narrative file: Write to `practices/<method-name>/_method-narrative.json`
   - Audit cross-practice references:
     ```bash
     python3 utils/audit-method-references.py bundles/<method-name>.keleo --baseline <effective-context.json>
     ```

4. **Validation (all):**
   ```bash
   python3 utils/eval-skill-output.py practices/<name>/ --summary
   ```
   Quick check: `--one-line`. Failed only: `--show-failed`.

   Fix all FAIL assertions with `error` severity. Re-run until `error_pass_rate: 1.0`.

5. **ChangeRequest (if updating existing):** If a prior version exists, generate a ChangeRequest:
   ```bash
   python3 utils/generate-change-request.py <old>.json <new>.json --author "<git user>" --status accepted -o practices/<name>/<name>.changerequest.json
   ```
   Then discover downstream dependents:
   ```bash
   python3 utils/discover-dependencies.py --dependents "<Practice Name>"
   ```
   Present a Downstream Impact Report. See `update-method` SKILL.md for the full report format.

---

## Key Principles

### No Inline Scripts + Utils Self-Extension

**All programmatic actions use reusable scripts in `utils/`, never `python3 -c` or `bash -c`.**
Use the Write tool to create intermediate files, then call utility scripts. This rule applies to subagents too.

**No compound bash scripts.** Avoid `TARGET=... && grep ...` or `for f in ...; do ... done` — use separate tool calls.

**When you need functionality that doesn't exist yet**, read `.claude/skills/SKILL-STANDARD.md` §7.4, then extend/create the utility and continue processing.

### Key Utilities

**Canonical registry:** `utils/README.md` — read this for the full, current list of all utilities.

### Reference-Driven Architecture

This skill does NOT embed domain knowledge. Instead:

- **Phase 1:** Reads `references/domain-framework.md` for perspectives
- **Phase 2:** Reads semantics sub-documents for mapping rules
- **Phase 3:** Reads `deps/language.schema.json` for structure
- **All phases:** Read phase skills in `phases/` for orchestration

Phase skills point to reference documents — they don't duplicate them. If a reference document changes, phase skills pick up the change automatically.

### User-Provided Baseline

The skill does NOT assume a specific baseline practice. Auto-discovery scans `baselines/`, `practices/`, and `deps/` directories to resolve names to paths.

---

## Cross-Practice Dependencies

Alpha hierarchies and cross-practice dependencies are covered in `references/semantics/composition.md` §4.4-4.5 and `references/practice-method-strategy.md`.

**Key rules:**
- **Practice-local chains**: Referenced alpha must be defined earlier in the mapping guide
- **Cross-practice references**: Set `practiceDependencyNames` array + `dependencies` array
- **Orchestration practices**: Use `practiceDependencyNames` to load alphas, create patterns that coordinate across them
- **Validation**: `python3 utils/assess-practice.py <file>.json --baseline <baseline>.json --parent <dep>.json`

---

## Practice vs Method Handling

Full delineation strategy with worked examples: `references/practice-method-strategy.md`.

| Signal | Decision | Alpha Range |
|---|---|---|
| 3-7 baseline alphas, one primary | Single Practice | 1 primary + 2-6 related |
| 8+ alphas, multiple primaries | Method (multi-practice) | 3-7 per practice |
| Cross-practice coordination | Orchestration Practice | Minimal (coordination only) |

**Core principle:** Each practice focuses on ONE primary alpha + directly related alphas (via `relatesTo`, 1-level deep).

**Cross-baseline methods:** Use `bindings.alphaBindings` (see `references/semantics/composition.md` §4.8).

---

## Final Deliverables

1. **`practices/<name>/01-analysis-report.md`** — Complete structured analysis (~30-50K words)
2. **`practices/<name>/02-mapping-guide.md`** — Complete mapping specification
3. **`bundles/<name>.keleo`** — `.keleo` package (primary deliverable)
4. **`practices/<name>/<practice-name>.json`** — Individual practice JSONs (intermediate)

### Assets

- **REQUIRED**: Every alpha and activity MUST have an icon-type AssetReference (Font Awesome 6 Free preferred)
- **RECOMMENDED**: Pattern views with icon references
- **OPTIONAL**: Diagrams, templates

---

## Success Criteria

1. All three phases complete, validation passes with 0 errors
2. All source methodology content mapped — no omissions
3. Rich narratives with citations, distinct observable criteria, orthogonal tags

---

## Post-Completion Review (MANDATORY)

**After completing the skill workflow OR after completing planning**, read `.claude/skills/SKILL-STANDARD.md` §11 for the full Post-Completion Review protocol, then:

1. **Utils remediation (apply immediately)**: Audit session for inline scripts or workarounds → extend/create utilities
2. **Permission gaps (propose to user)**: Bash commands that triggered prompts but could be auto-allowed
3. **Skill improvements (propose to user)**: Instruction gaps that led to wrong output or repeated corrections
4. **Report**: Tell the user what was remediated and what is proposed
