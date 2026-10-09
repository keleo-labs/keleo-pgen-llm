---
name: generate-method
version: 1.1.0
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
| Working around a defect in a baseline or dependency practice | §13 — accommodate it, then file it with `/report-issue` |
| Writing prose rules that have a clear pass/fail criterion | §9 — convert to Gherkin scenarios instead |
| Adding or modifying Gherkin scenarios in any SKILL.md | §1–6 — rule structure, categories, and triple-duty |
| Adding a new validation check to assess/validate scripts | §7.2 — follow the Adding New Checks protocol |

**How to read:** `Read .claude/skills/SKILL-STANDARD.md` — then navigate to the relevant `## N.` heading.

---

## External Dependencies

| Dependency | Required? | Role |
|---|---|---|
| Baseline practice JSON | Yes | Target framework that the generated practice extends (e.g., `deps/platform-adoption-kernel.json`) |
| Playwright MCP | Optional | Content sourcing from web-based methodology documentation when `WebFetch` fails |
| Remote bundle repository | Optional | Downloads dependency `.keleo` bundles not available locally (via `studio-client.py`) |

The baseline JSON is the only hard requirement — it defines the alphas, competencies, and activity spaces that the generated practice maps to. Playwright is a content sourcing fallback for JavaScript-heavy methodology sites. Remote bundle access is used during dependency resolution when referenced practices aren't found locally.

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
    ├── 00-prompt-history.md        (Session provenance: prompt, interactions, sources, decisions, phases)
    ├── 01-analysis-report.md       (Phase 1 output, ~30-50K words)
    ├── 02-mapping-guide.md         (Phase 2 output, scales with alpha count: ~5-6K words/alpha)
    └── <practice-name>.json        (Phase 3 output, schema-compliant JSON)

bundles/
└── <practice-name>.keleo           (Package: practice + baseline bundled)
```

For methods with multiple practices:

```text
practices/
└── <method-name>/
    ├── 00-prompt-history.md        (Session provenance: prompt, interactions, sources, decisions, phases)
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

### Verification Foundation

`.claude/skills/verification-foundation/` holds the verification protocol shared with
`create-baseline-method` and `update-method`. Read `VERIFY-FOUNDATION.md` once per
session, then only `verifiers/phase-<N>.md` at the gate you reach — the briefs are
literal prompt text to pass through to verification agents.

### Utility Quick Reference

Use these utilities instead of ad-hoc `python3 -c` scripts for common inspection tasks:

| Need | Utility | Command |
|---|---|---|
| Practice metadata (kind, name, version, deps) | `practice-summary.py` | `<file> [--json]` |
| Alpha hierarchy with provenance | `extract-reference-names.py` | `--hierarchy` |
| Alpha flat list with details + provenance | `extract-reference-names.py` | `--sections alphas --alpha-details` |
| Bundle contents | `inspect-keleo.py` | `<file> [--json]` |
| Find related/sibling practices | `discover-dependencies.py` | `--related <file> [--json]` |

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

3. **Discover related practices**
   After identifying the parent method or practice, discover siblings that share dependencies:
   ```bash
   python3 utils/discover-dependencies.py --related <parent-method-or-practice.json> --json
   ```
   Review the results against the source material content:
   - For each related practice, assess whether the source material covers that practice's domain
   - Present relevant matches to the user with rationale (e.g., "Source covers virtualization — Red Hat OpenShift Virtualization may be relevant")
   - User confirms which (if any) to include in the effective context
   - Add confirmed practices to the context source list for Step 0.5

4. **Initial structure assessment (preliminary only):**
   - **Note:** Final practice delineation happens in Step 1.5 (Delineation Gate) before Phase 2 delegation
   - Check for obvious separation signals from source:
     - Multiple distinct use-cases? Different stakeholder journeys? Clearly separate capability domains?
   - **If obvious separation:** Plan for method with multiple practices
   - **If unified framework:** Plan for single practice (subject to Phase 2 validation)
   - **Key principle:** Don't determine primary alphas or practice boundaries yet — you need baseline context first

5. **Reference strategy (present to user):**
   - Estimate reference yield from source materials
   - **Few candidates** (0-2) → recommend secondary research (Step 2.5)
   - **Moderate** (3-5) → optional, user decides
   - **Many** (6+) → skip secondary research

6. **Plan execution:**
   - Tentative practice/method name (kebab-case)
   - Phase execution sequence
   - Expected complexity and size
   - Whether secondary reference research (Step 2.5) will be performed

7. **Exit plan mode** with clear execution roadmap

8. **Initialise prompt history:**
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --init \
     --type <practice|method> --name "<Practice Name>" \
     --prompt "<user's original prompt text>"
   ```
   Then record each source material identified during planning:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-source \
     --source-type <file|url|google-doc|google-slides> \
     --source-path "<path or URL>" --source-desc "<brief description>"
   ```

   **`--init` activates the prompt-history hooks.** From this point until `--finalize`, every
   user turn and every `AskUserQuestion` exchange in this session is appended to the
   Interaction Log automatically — you do not need to record those. You DO need to record,
   manually, any question you put to the user in plain prose (outside `AskUserQuestion`),
   because the hook captures only the answer:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-interaction \
     --interaction-label "<context, e.g. 'Baseline selection'>" \
     --interaction-question "<the question you asked>" \
     --interaction-answer "<the user's reply, verbatim>"
   ```
   If you are resuming a practice in a new session, re-arm the hooks first:
   `python3 utils/prompt-history.py practices/<practice-name>/ --activate`

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

5. **Record dependencies in prompt history:**
   For each resolved context source (baseline, parent practice, bundle):
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-dependency \
     --dep-type <baseline|practice|method|bundle> --dep-name "<Name>" \
     --dep-path "<resolved-path>" --dep-version "<version>"
   ```

### Defects in Inherited Content

The baseline and the dependency practices are **inputs**, not your output — you do not
edit them here. When one of them is defective (an alpha with no viable
`contributesTo` target, a competency whose levels you have to work around, a state
progression the baseline contradicts elsewhere), accommodate it and carry on mapping,
then record it:

```bash
python3 utils/issue-register.py --add-draft /tmp/keleo-defects-<practice-slug>.json \
  --type Issue --summary "<title>" --description "<observed / expected / what you did instead>" \
  --document "<Baseline or Dependency Name>" --document-version <version> \
  --document-kind <practiceBaseline|practice|method> \
  --element "<Element Name>" --element-type <type>
```

File against the document that **owns** the defect, with its own name, version and kind
— not the practice you are authoring. Defects in your own output are fixed in Phase 3,
never filed. Keep drafting through Phases 1–3 and file the batch once at handover by
invoking `report-issue` in mid-execution mode. Gate and routing: `SKILL-STANDARD.md` §13.

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

1. Record phase start:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --start-phase --phase "Phase 1: Analysis"
   ```
2. Read `phases/phase-1-skill.md` to understand what the subagent will do
3. Launch Agent with prompt including:
   - Practice name and source material file paths
   - Instruction to read `phases/phase-1-skill.md` first
   - Output location: `practices/<practice-name>/01-analysis-report.md`

4. After agent completes, validate:
   ```bash
   python3 utils/eval-skill-output.py practices/<name>/ --phase 1 --summary
   ```

5. Record phase completion:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --end-phase \
     --phase "Phase 1: Analysis" --phase-output "01-analysis-report.md" \
     --phase-validation "<PASS or FAIL summary>"
   ```

Fix any FAIL assertions before proceeding.

#### Verification Gate — Analysis

Mechanical validation checks the report's shape. It cannot tell you whether the content
traces to the sources. Read `.claude/skills/verification-foundation/verifiers/phase-1.md`
and launch its three verifiers in a single message.

```bash
python3 utils/verification-gate.py practices/<name>/ --phase 1 --gate --summary \
  --expect source-fidelity,source-coverage,citation-integrity
```

Exit 1 means a blocking error survived — follow the remediation loop in
`VERIFY-FOUNDATION.md` §8 before continuing. Record the verdict:

```bash
python3 utils/prompt-history.py practices/<practice-name>/ --add-decision \
  --decision-label "Phase 1 Verification Gate" \
  --decision-text "<verdict>: <N> errors, <M> warnings. <What was fixed or dismissed, and on what evidence>"
```

#### User Review Gate — Analysis

**Present the Phase 1 output for user review before proceeding.**

1. Inform the user: "Phase 1 (Analysis) is complete. The output is at `practices/<practice-name>/01-analysis-report.md`. Please review it and let me know if you'd like any changes, or confirm to proceed."
2. **Wait for user response.** Do not proceed until the user explicitly confirms.
3. If the user requests changes:
   - Make the requested edits to the analysis report
   - Re-run validation: `python3 utils/eval-skill-output.py practices/<name>/ --phase 1 --summary`
   - Present the updated output and ask again
   - Repeat until the user confirms
4. Record the outcome — what the user asked for, not just that they accepted. Their words are
   already in the Interaction Log via the hook; this records what you did about them:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-decision \
     --decision-label "Phase 1 Review Gate" \
     --decision-text "Accepted after <N> revision rounds. Changes made: <summary, or 'none'>"
   ```
5. Proceed to Step 1.5.

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
   - **Produce a concern-to-alpha consolidation map** showing how N Phase 1 concerns map to M alphas (concerns often consolidate — e.g., 12 concerns → 7 alphas). This map is passed to Phase 2 agents as part of the delineation context.

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

7. **Record delineation decision:**
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-decision \
     --decision-label "Delineation Gate" \
     --decision-text "<Single practice|Method with N practices>: M alphas across K focuses. Primary alpha: <name>"
   ```

For the full Primary Alpha Focus Strategy with worked examples, read `references/practice-method-strategy.md`.

### Step 2: Phase 2 — Mapping

**Objective:** Map Phase 1 analysis to baseline practice framework.

**Prerequisite:** Step 1.5 delineation gate must be complete.

**Dispatch to subagent(s):**

1. Record phase start:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --start-phase --phase "Phase 2: Mapping"
   ```
2. Read `phases/phase-2-skill.md` to understand what the subagent will do
3. Launch Agent(s) with prompt including:
   - Instruction to read `phases/phase-2-skill.md` first
   - Practice name, description, and file paths:
     - `practices/<name>/01-analysis-report.md` (analysis report)
     - `<effective-context-path>` (from Step 0.5)
     - Leaf baseline path (for validation)
   - Delineation context from Step 1.5 (primary alpha, alpha coverage, practice boundaries)
   - If `_aliasContext` present: note that aliases inform semantic understanding but all structural references use canonical names

**For multi-practice methods:** Launch parallel agents (one per practice) in a single message.

4. **After all agents complete:**
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

5. Record phase completion:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --end-phase \
     --phase "Phase 2: Mapping" --phase-output "02-mapping-guide.md" \
     --phase-validation "<PASS or FAIL summary>"
   ```

Fix any FAIL assertions before proceeding.

#### Verification Gate — Mapping

Read `.claude/skills/verification-foundation/verifiers/phase-2.md`. Launch the four
practice-scoped verifiers; for a method, run them **per practice** (four agents at a
time) plus `cross-practice-consistency` once.

```bash
python3 utils/verification-gate.py practices/<name>/ --phase 2 --gate --summary \
  --expect source-fidelity,alpha-semantics,coverage,naming-consistency
```

For methods, list every per-practice verifier slug in `--expect`. Follow the
remediation loop in `VERIFY-FOUNDATION.md` §8 on exit 1, then record the verdict with
`prompt-history.py --add-decision` as at Phase 1.

#### User Review Gate — Mapping

**Present the Phase 2 output for user review before proceeding.**

1. Inform the user: "Phase 2 (Mapping) is complete. The output is at `practices/<practice-name>/02-mapping-guide.md`. Please review it and let me know if you'd like any changes, or confirm to proceed to Phase 3."
2. **Wait for user response.** Do not proceed until the user explicitly confirms.
3. If the user requests changes:
   - Make the requested edits to the mapping guide
   - Re-run validation: `python3 utils/eval-skill-output.py practices/<name>/ --phase 2 --summary`
   - Present the updated output and ask again
   - Repeat until the user confirms
4. Record the outcome — what the user asked for, not just that they accepted:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-decision \
     --decision-label "Phase 2 Review Gate" \
     --decision-text "Accepted after <N> revision rounds. Changes made: <summary, or 'none'>"
   ```
5. Proceed to Phase 3.

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

1. Record phase start:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --start-phase --phase "Phase 3: JSON Generation"
   ```
2. Read `phases/phase-3-skill.md` to understand what the subagent will do
3. Launch Agent(s) with prompt including:
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

4. **Validation (trust-but-verify):**

   Phase 3 agents run their own fix-validate chain internally. After they complete, verify rather than re-run:

   ```bash
   python3 utils/eval-skill-output.py practices/<name>/ --summary
   ```
   Quick check: `--one-line`. Failed only: `--show-failed`.

   - If `error_pass_rate: 1.0` → agents handled it, proceed to step 5.
   - If `error_pass_rate < 1.0` → run the batch fix pipeline:
     ```bash
     python3 utils/post-validate-method.py practices/<name>/ --fix --one-line
     ```
     Re-run `eval-skill-output.py` to confirm. Fix remaining issues manually if needed.

4.5 **Verification Gate — JSON Generation**

   Phase 3 is largely mechanical and the steps above cover the mechanical part. What
   they do not cover is the judgement Phase 3 exercises where the mapping guide is
   silent — outcome `measureDescription` and forecast weights, narrative type choice
   and context prose, alias coining, reference actionability, icon and competency
   level selection. Read
   `.claude/skills/verification-foundation/verifiers/phase-3.md` and launch its two
   verifiers (per practice for methods).

   ```bash
   python3 utils/verification-gate.py practices/<name>/ --phase 3 --gate --summary \
     --expect generation-drift,reference-citation-fidelity
   ```

   On exit 1, follow the remediation loop in `VERIFY-FOUNDATION.md` §8. **Any fix to a
   practice JSON means rebundling** — re-run `package-keleo.py`, since the subagent
   packaged before this gate ran. Record the verdict with
   `prompt-history.py --add-decision` as at Phase 1.

5. Record phase completion:
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --end-phase \
     --phase "Phase 3: JSON Generation" --phase-output "<practice-name>.json" \
     --phase-validation "<PASS or FAIL summary>"
   ```

6. **ChangeRequest (if updating existing):** If a prior version exists, generate a ChangeRequest:
   ```bash
   python3 utils/generate-change-request.py <old>.json <new>.json --author "<git user>" --status accepted -o practices/<name>/<name>.changerequest.json
   ```
   Then discover downstream dependents:
   ```bash
   python3 utils/discover-dependencies.py --dependents "<Practice Name>"
   ```
   Present a Downstream Impact Report. See `update-method` SKILL.md for the full report format.

7. **Record deliverables and finalise prompt history:**
   ```bash
   python3 utils/prompt-history.py practices/<practice-name>/ --add-deliverable \
     --deliverable-path "bundles/<name>.keleo" --deliverable-desc "Packaged practice bundle"
   python3 utils/prompt-history.py practices/<practice-name>/ --finalize
   ```
   `--finalize` stands the hooks down — later turns in this session are no longer appended to
   the Interaction Log. If the user reopens the work, run `--activate` before continuing.

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

1. **`practices/<name>/00-prompt-history.md`** — Session provenance (prompt, interactions, sources, decisions, phases)
2. **`practices/<name>/01-analysis-report.md`** — Complete structured analysis (~30-50K words)
3. **`practices/<name>/02-mapping-guide.md`** — Complete mapping specification
4. **`bundles/<name>.keleo`** — `.keleo` package (primary deliverable)
5. **`practices/<name>/<practice-name>.json`** — Individual practice JSONs (intermediate)

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

1. **Content defects (file immediately)**: If any defects in inherited content were drafted, invoke `report-issue` in mid-execution mode with the drafts path and report the row numbers (§13)
2. **Utils remediation (apply immediately)**: Audit session for inline scripts or workarounds → extend/create utilities
3. **Permission gaps (propose to user)**: Bash commands that triggered prompts but could be auto-allowed
4. **Skill improvements (propose to user)**: Instruction gaps that led to wrong output or repeated corrections
5. **Report**: Tell the user what was filed, what was remediated, and what is proposed

---

## Rules

Gherkin scenarios serving triple duty — agent instruction, eval assertion, and
verification contract (SKILL-STANDARD.md §3). Regenerate the specs index after any
change here:

```bash
python3 utils/extract-specs.py .claude/skills/generate-method/SKILL.md --stats
```

## Feature: Source Fidelity

### Scenario: Structural claims trace to a source (@rule:fidelity-001)
- Given: A phase has produced an analysis report or mapping guide
- When: The verification gate for that phase runs
- Then: Every alpha, state, outcome, work product, activity and persona traces to a named span in a source material or in the preceding phase output
- Then: Claims that cannot be traced after directed searching are reported as errors
- Then: Claims traceable in substance but overstated relative to the source are reported as warnings

### Scenario: Citations support the claims attached to them (@rule:fidelity-002)
- Given: A document declares citations
- When: The citation verifier runs
- Then: Each citation `name` is the work title, not an author-date label
- Then: Each cited work exists and its authors, date and publisher are correct
- Then: Each citation URL resolves and points at the cited work rather than a site root
- Then: Each claim attributed to a citation is supported by the cited work

### Scenario: No generation drift between mapping guide and JSON (@rule:fidelity-003)
- Given: Phase 3 has generated a practice, method or baseline JSON
- When: The Phase 3 verification gate runs
- Then: Every element in the JSON is derivable from the mapping guide or the baseline
- Then: Outcome `measureDescription` asserts no metric or target the mapping guide does not state
- Then: Every element specified in the mapping guide is present in the JSON

### Scenario: Verification gate precedes each user review gate (@rule:process-004)
- Given: A phase has completed and passed mechanical validation
- When: The output is presented to the user for review
- Then: The phase verification gate has been run with `--expect` naming every verifier launched
- Then: No blocking error survives reconciliation
- Then: The verdict is recorded in the prompt history as a decision


## Feature: Alpha Relationship Integrity

### Scenario: No floating alphas (@rule:semantic-001)
- Given: A new alpha is defined that does not exist in the baseline
- When: Phase 3 generates the alpha JSON
- Then: The alpha has exactly one of `contributesTo` or `mapsTo`
- Then: The target resolves to a baseline, practice-local, or dependency alpha

### Scenario: contributesTo and mapsTo may coexist on different targets (@rule:semantic-002)
- Given: A new alpha declares a parent relationship
- When: The alpha JSON is generated
- Then: If both `contributesTo` and `mapsTo` are present, they reference different alphas

### Scenario: mapsTo variants match parent states exactly (@rule:semantic-003)
- Given: A new alpha has `mapsTo` pointing to a parent alpha
- When: The alpha's states are generated
- Then: The state names and sequence exactly match the parent alpha's states

### Scenario: mapsTo variant names may include or omit parent type (@rule:semantic-010)
- Given: A new alpha has `mapsTo` pointing to a parent alpha
- When: The alpha name is chosen
- Then: The alpha name may include or omit the parent alpha's type name

### Scenario: Redeclared alphas have no contributesTo or mapsTo (@rule:semantic-005)
- Given: An alpha name matches a baseline or parent practice alpha
- When: The alpha is included in the practice JSON
- Then: The alpha has neither `contributesTo` nor `mapsTo`
- Then: Only practice-specific checklists, narratives, and Gherkin guidance are added

### Scenario: Competency level names match baseline exactly (@rule:semantic-006)
- Given: An activity or persona references a competency level
- When: The `competencyLevelName` value is set
- Then: The value exactly matches a CompetencyLevel.name from the baseline for that competency
- Then: Level names are extracted with `python3 utils/extract-reference-names.py <baseline>.json --sections competencies`

### Scenario: relatesTo only on new alphas (@rule:semantic-007)
- Given: An alpha is a redeclaration of a baseline alpha
- When: The alpha JSON is generated
- Then: No `relatesTo` array is added (baseline relationships are inherited)

### Scenario: relatesTo entries have required fields (@rule:semantic-008)
- Given: A new alpha defines `relatesTo` relationships
- When: The relatesTo array is generated
- Then: Every entry has `relationship`, `alphaName`, and `direction` fields
- Then: `direction` is one of `outgoing`, `incoming`, or `mutual`

### Scenario: contributesToState references valid parent state (@rule:semantic-009)
- Given: A state on a new alpha declares `contributesToState`
- When: The state JSON is generated
- Then: The `contributesToState` value is a valid state name on the parent alpha referenced by `contributesTo` or `mapsTo`

### Scenario: Baseline references are case-sensitive (@rule:semantic-011)
- Given: The practice references baseline elements (alphas, focuses, activitySpaces, competencies)
- When: Symbolic reference values are set
- Then: Every reference exactly matches the baseline element's `name` (case-sensitive)

## Feature: Narrative Quality

### Scenario: Narratives are structured objects (@rule:narrative-001)
- Given: A narrative is defined on any element or at practice level
- When: The narrative JSON is generated
- Then: The narrative has `narrativeTypeName` and `narrativeContexts` array
- Then: Each context has `seq`, `narrativeElementName`, and `context` fields

### Scenario: Narrative names describe subject matter (@rule:narrative-003)
- Given: A narrative has a `name` and `description`
- When: The narrative JSON is generated
- Then: The name describes the subject matter, not the template type
- Then: The description explains what the narrative covers, not the framework structure
- Then: Contexts contain direct story content without mentioning the narrative type

### Scenario: Narrative contexts are self-contained (@rule:narrative-005)
- Given: A narrative has contexts with `narrativeElementName` labels
- When: The context strings are generated
- Then: Each context is coherent without its element heading visible
- Then: Bare lists include a framing introduction sentence

### Scenario: Narratives placed on correct elements (@rule:narrative-002)
- Given: A narrative describes a specific alpha, activity, or work product
- When: The narrative is attached in the JSON
- Then: Element-specific narratives are on the element's `narratives[]` property
- Then: Only practice/method-level narratives go in the top-level `narratives[]` array

### Scenario: All narratives have citation references (@rule:narrative-006)
- Given: A narrative is defined
- When: The narrative JSON is generated
- Then: The narrative includes a `citationNames` array with at least one citation reference

## Feature: Element Naming

### Scenario: Descriptions are single sentences under word limit (@rule:naming-001)
- Given: An element has a `description` field
- When: The description is generated
- Then: Element descriptions are at most 20 words
- Then: State and LOD descriptions are at most 12 words

### Scenario: Checklist names are noun-phrase labels (@rule:naming-002)
- Given: A checklist item on an alpha state has `name` and `description`
- When: The checklist JSON is generated
- Then: The name is a short noun phrase (not truncated from the description)
- Then: The name is not identical to the description

### Scenario: Global name uniqueness across element types (@rule:naming-003)
- Given: Multiple PracticeElement types are defined (alphas, workProducts, activities, personas, patterns)
- When: All element names are collected
- Then: No name appears in more than one element type

### Scenario: LOD names describe content maturity (@rule:naming-004)
- Given: A work product has levels of detail
- When: LOD names are chosen
- Then: Names describe artifact content maturity (e.g., "Outline", "Comprehensive", "Automated")
- Then: Names do not use generic labels ("Level 1", "Basic") or concern progression terms ("Established", "Optimized")

### Scenario: Activity names differ from ActivitySpace names (@rule:naming-005)
- Given: An activity is assigned to an ActivitySpace
- When: The activity name is chosen
- Then: The activity name is distinct from the ActivitySpace name

## Feature: Coverage Completeness

### Scenario: Alpha state minimum (@rule:coverage-001)
- Given: An alpha is defined in the practice
- When: States are assigned to the alpha
- Then: The alpha has at least 3 states

### Scenario: Work product LOD minimum (@rule:coverage-002)
- Given: A work product is defined in the practice
- When: Levels of detail are assigned
- Then: The work product has at least 2 levels of detail

### Scenario: Alpha states have supporting LODs (@rule:coverage-003)
- Given: An alpha state exists on a new (non-baseline) alpha
- When: Work product LODs are checked
- Then: At least one LOD has `contributesTo` targeting the alpha state

### Scenario: Patterns cover all practice alphas (@rule:coverage-004)
- Given: A pattern is defined in the practice
- When: PatternViews are checked
- Then: Every practice alpha appears in at least one PatternView
- Then: Each alpha appears in every view (backfilled if needed)

### Scenario: Alpha states have supporting activities (@rule:coverage-005)
- Given: An alpha state beyond the initial state exists on a new alpha
- When: Activity contributesTo references are checked
- Then: At least one activity has `contributesTo` targeting the alpha state

## Feature: Terminology Aliasing

### Scenario: One alias per element maximum (@rule:aliasing-001)
- Given: The practice defines terminology aliases
- When: Aliases are assigned to baseline elements
- Then: Each baseline element has at most one alias

### Scenario: Alias names excluded from structural references (@rule:aliasing-002)
- Given: An alias maps a baseline name to a domain-specific name
- When: The practice JSON uses symbolic references (alphaName, contributesTo, activitySpaceName, etc.)
- Then: Only canonical baseline names appear in structural reference fields
- Then: Alias names never appear in structural reference fields

### Scenario: Keyword count within range (@rule:aliasing-003)
- Given: The practice defines a keywords array
- When: Keywords are generated
- Then: The array contains between 10 and 20 keywords

## Feature: Structural Integrity

### Scenario: JSON has correct kind discriminator (@rule:structural-001)
- Given: Phase 3 generates a JSON file
- When: The JSON is validated
- Then: The `kind` property is "practice" for single practices, "method" for multi-practice methods

### Scenario: All required sections present in JSON (@rule:structural-002)
- Given: Phase 3 generates a practice JSON
- When: The JSON is validated
- Then: alphas, activities, workProducts, patterns, and citations arrays are present and non-empty

### Scenario: Pattern cross-references resolve (@rule:structural-003)
- Given: A pattern references alpha names and state names in patternViews
- When: Phase 3 generates the JSON
- Then: Every alphaName in patternViews.alphaStates resolves to an alpha in the practice or baseline
- Then: Every stateName resolves to a valid state on that alpha

### Scenario: Activity-alpha cross-references resolve (@rule:structural-004)
- Given: An activity has contributesTo entries referencing alphas and states
- When: Phase 3 generates the JSON
- Then: Every alphaName and stateName in activity contributesTo resolves to a defined alpha and state

### Scenario: Activity-work product cross-references resolve (@rule:structural-005)
- Given: An activity has worksOn entries referencing work products and LODs
- When: Phase 3 generates the JSON
- Then: Every workProductName and levelOfDetailName in worksOn resolves to defined elements

## Feature: Process Compliance

### Scenario: Phase 1 completed before Phase 2 (@rule:process-001)
- Given: The three-phase pipeline is being executed
- When: Phase 2 mapping begins
- Then: 01-analysis-report.md exists with all 8 required sections
- Then: Analysis has sufficient depth (5+ numbered subsections and 3+ source references)

### Scenario: Phase 2 completed before Phase 3 (@rule:process-002)
- Given: The three-phase pipeline is being executed
- When: Phase 3 JSON generation begins
- Then: 02-mapping-guide.md exists with all 7 required sections
- Then: At least 3 alphas, 5 activities, and 1 pattern are mapped

### Scenario: Validation run after JSON generation (@rule:process-003)
- Given: Phase 3 has generated a JSON file
- When: The phase is marked complete
- Then: validate-practice-json.py has been run with 0 schema errors
- Then: assess-practice.py has been run with 0 error-severity issues
