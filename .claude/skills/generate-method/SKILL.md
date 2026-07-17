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

**Key Differences from v1:**

- ✓ Simpler 3-phase structure (vs 8-phase pipeline)
- ✓ Reference-driven (reads semantics.md, not embedded rules)
- ✓ User-provided baseline (not hardcoded)
- ✓ Single validation script (not 4+ separate utilities)
- ✓ Cleaner output (3 files vs 8+ modules)

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
    ├── 02-mapping-guide.md         (Phase 2 output, ~40-60K words)
    └── <practice-name>.json        (Phase 3 output, schema-compliant JSON)
```

For methods with multiple practices:

```text
practices/
└── <method-name>/
    ├── 01-analysis-report.md       (Covers all practices)
    ├── 02-mapping-guide.md         (Maps all practices)
    └── <method-name>.json          (Method JSON with embedded practices)
```

---

## Reference Documents

This skill relies on reference documents (READ via Read tool, NOT embedded):

### Required References

1. **references/domain-framework.md** - Four-perspective analysis framework
2. **references/semantics.md** - Practice Language semantic guidance
3. **deps/language.schema.json** - JSON Schema definition
4. **Baseline Practice JSON** - User-provided (e.g., `deps/platform-adoption-kernel.json`)

### Phase Prompts

- **prompts/phase-1-analysis.md** - Analysis phase instructions
- **prompts/phase-2-mapping.md** - Mapping phase instructions
- **prompts/phase-3-json.md** - JSON generation instructions

---

## Execution Workflow

### Step 0: EnterPlanMode (REQUIRED)

**YOU MUST DO THIS FIRST.**

In plan mode:

1. **Read source materials completely**
   - All provided PDFs, URLs, markdown files
   - Take comprehensive notes

2. **Identify baseline or parent practice:**
   - Ask user which baseline OR parent practice/method to use
   - Default suggestion: `deps/platform-adoption-kernel.json` (baseline)
   - Validate file exists and is valid JSON
   - **Detect input type:**
     ```bash
     python3 utils/resolve-parent-practice.py <file.json> --check-only
     ```
     - If `inputKind: "practiceBaseline"` → Standard baseline flow (proceed to Step 0.5)
     - If `inputKind: "practice"` or `"method"` → **Parent practice mode** (proceed to Step 0.25)
   - Report detected input type and key details to user

3. **Initial structure assessment (preliminary only):**
   - **Note:** Final practice delineation happens in Step 1.5 (Delineation Gate) before Phase 2 delegation
   - Check for obvious separation signals from source:
     - Multiple distinct use-cases mentioned? (e.g., greenfield vs brownfield)
     - Different stakeholder journeys? (e.g., builders vs consumers)
     - Clearly separate capability domains? (e.g., security chapter + deployment chapter)
   - **If obvious separation:** Plan for method with multiple practices
   - **If unified framework:** Plan for single practice (subject to Phase 2 validation)
   - **Key principle:** Don't determine primary alphas or practice boundaries yet - you need baseline context first

4. **Plan execution:**
   - Tentative practice/method name (kebab-case)
   - Phase execution sequence
   - Expected complexity and size
   - Potential challenges
   - **Note:** Practice boundaries will be finalized in Step 1.5 (Delineation Gate) before Phase 2 delegation

5. **Exit plan mode** with clear execution roadmap

---

### Step 0.25: Parent Practice Resolution (Parent Practice Mode Only)

**Objective:** When the user provides an existing practice or method (instead of a baseline), resolve it into an effective parent and locate the actual baseline.

**When this step is needed:** Only when Step 0 detected `inputKind: "practice"` or `"method"`. If the input is a `practiceBaseline`, skip this step entirely.

**Process:**

1. **Extract baseline practice name from the parent:**
   The `--check-only` output from Step 0 includes `baselinePracticeName`. This is the actual baseline that the parent practice extends.

2. **Locate the actual baseline file:**
   - Ask user for the baseline file path corresponding to the reported `baselinePracticeName`
   - Default suggestion: check `deps/` directory for matching files
   - Validate the baseline file exists and its `name` property matches `baselinePracticeName`

3. **Create effective parent:**
   ```bash
   python3 utils/resolve-parent-practice.py <parent.json> -o <output-dir>/_effective-parent.json
   ```
   
   The utility:
   - For a **practice**: Outputs the practice directly as the effective parent
   - For a **method**: Unions all embedded practices' elements (alphas, activitySpaces, workProducts, patterns, etc.) using name-keyed merge
   - Applies `practiceElementAliases` as `_aliasContext` annotations (canonical names preserved in all structural positions)
   
   Report the effective parent composition to the user (alpha count, practice names, etc.).

4. **Record key variables for subsequent steps:**
   - `parentPracticePath` = path to user-provided practice/method
   - `effectiveParentPath` = `<output-dir>/_effective-parent.json`
   - `parentPracticeNames` = list from report's `parentPracticeNames` (candidate pool for `practiceDependencyNames` — filtered later based on actual references)
   - `actualBaselinePath` = path to the actual baseline JSON (for Step 0.5 and validation)

5. **Proceed to Step 0.5** with `actualBaselinePath` — the actual baseline still needs dependency resolution.

**User Feedback:**
- "Detected parent practice: '<name>' (extends baseline '<baselinePracticeName>')"
- "Parent practice contains N alphas, M activitySpaces, K workProducts"
- "For methods: Merged N practices into composite parent: [practice name list]"
- "Using effective parent for analysis/mapping. Actual baseline '<name>' for validation."
- "practiceDependencyNames will be determined per-practice based on actual element references (not all parent practice names)"

**CRITICAL:** All structural references in the generated JSON (`contributesTo`, `alphaName`, `stateName`, etc.) MUST use canonical names. If the effective parent has `_aliasContext`, aliases inform semantic understanding only — they do NOT appear in generated JSON output.

---

### Step 0.5: Baseline Dependency Resolution

**Objective:** Detect and resolve baseline dependencies to create a complete "effective baseline" that contains all inherited elements with domain-specific alias context.

**When this step is needed:** Only when the baseline JSON has a non-empty `baselinePracticeNames` array. If the baseline has no dependencies, skip this step and use the baseline file as-is for all subsequent steps.

**Note:** In parent practice mode, this step operates on `actualBaselinePath` (the baseline referenced by the parent practice), not the user-provided file.

**Process:**

1. **Check for dependencies:**
   ```bash
   python3 utils/resolve-baseline.py <baseline-practice.json> --check-only -o /dev/null
   ```
   This reports whether the baseline has `baselinePracticeNames` and lists any dependencies and aliases.
   - If `hasDependencies: false`: **Skip this step.** Use the provided baseline file directly.
   - If `hasDependencies: true`: Continue to step 2.

2. **Report dependencies and ask user for files:**
   The check-only output lists `dependencyNames`. Present them to the user:
   ```
   The baseline practice "<name>" declares dependencies on other baselines:
   - <dependency-name-1>
   - <dependency-name-2>
   
   Since there is no practice library, I need the JSON files for each dependency.
   Please provide the file path for each:
   1. <dependency-name-1>: ?
   2. <dependency-name-2>: ?
   ```
   
   **Wait for user to provide file paths before proceeding.**

3. **Recursively check transitive dependencies:**
   For each dependency file the user provides, run `--check-only` to see if it has its own `baselinePracticeNames`. If so, ask the user for those files too. Continue until all baselines in the chain have no further dependencies.

4. **Create effective baseline using the resolver utility:**
   ```bash
   python3 utils/resolve-baseline.py \
     <baseline-practice.json> \
     <dependency-1.json> [<dependency-2.json> ...] \
     -o <output-dir>/_effective-baseline.json
   ```
   
   The utility programmatically:
   - Determines merge order (root-first, leaf-last)
   - Merges baselines using name-keyed union (child overrides parent where element names match)
   - Applies `practiceElementAliases` as `_aliasContext` annotations on elements (adds `_domainAlias` to each aliased element and a top-level `_aliasContext` section)
   - Preserves canonical names in all structural positions
   - Writes the effective baseline to the output path
   
   The stdout JSON report shows the effective baseline composition (alpha count, alias count, etc.). Report this to the user.

5. **Set effective baseline path:**
   For ALL subsequent steps (Step 1.5 through Step 3), use `<output-dir>/_effective-baseline.json` wherever the baseline file path is referenced for analysis and mapping. For **validation** (running `validate-practice-json.py`), always use the **original user-provided baseline file** — canonical names in the generated JSON must match the actual baseline, not the effective baseline annotations.

**User Feedback:**
- "Checking baseline for dependencies..."
- "Baseline '<name>' depends on: [list]. Please provide file paths for each."
- "Resolved dependency chain: Root → Layer1 → Leaf"
- "Created effective baseline with N alphas (K aliased), M activitySpaces, J competencies"
- "Domain terminology: 'Platform' → 'Automation Platform', 'Engineering' → 'Automation Engineering', etc."
- "Using effective baseline for analysis/mapping phases. Canonical names will be used in generated JSON."

**CRITICAL:** If ANY dependency file cannot be provided by the user, STOP and discuss alternatives. Do NOT proceed with an incomplete baseline — this will cause mapping errors and validation failures.

**CRITICAL:** Extension practices MUST use canonical element names (from `practiceElementName`) in all structural references (`contributesTo`, `alphaName`, `stateName`, `competencyName`, etc.), not alias names (`aliasName`). The alias context helps the LLM understand domain semantics during analysis and mapping, but the generated JSON output always uses canonical names.

---

## Token Budget Management: Phase Compaction Pattern

**CRITICAL:** To avoid token budget exhaustion during long translations, use conversation compaction between phases.

### When to Compact

**Inter-phase compaction** (between major phases):

1. **After Planning (before Phase 1):** Compact to clear planning discussion
2. **After Phase 1 (before Phase 2):** Compact to clear analysis generation
3. **After Phase 2 (before Phase 3):** Compact to clear mapping generation

**Multi-agent approach** (for multi-practice methods - RECOMMENDED):

4. **Use Agent tool for parallelism** (for methods with 2+ practices):
   - **Phase 2**: Launch one agent per practice (parallel execution)
     - Each agent reads: analysis report, baseline JSON, semantics.md
     - Each agent generates: complete practice mapping (alphas + work products + activities)
     - Write to separate files or sections
     - Agents run concurrently (no token budget sharing)
   - **Phase 3**: Launch one agent per practice (parallel execution)
     - Each agent reads: practice mapping section, baseline JSON, schema
     - Each agent generates: practice JSON (standalone, not method JSON)
     - Agents run concurrently
   - **Phase 3.5**: Assembly and validation
     - Combine practice JSONs into method structure
     - Validate method JSON against schema
     - Fix any cross-practice reference issues
   - **Benefits**: No token limits, no degeneration, concurrent execution, quality consistency

### How to Implement Multi-Agent Approach

**For Single-Practice translations:**
- User can manually compact between phases
- Tell user: "Phase N complete. [Optional: Compact before Phase N+1 for optimal token budget]"
- Don't wait - continue working

**For Multi-Practice methods (2+ practices):**
- **Always use Agent tool** (don't ask user to compact)
- Launch agents in parallel using single message with multiple Agent tool calls
- Each agent is self-contained with complete prompt and file paths

**Example: Phase 2 with 4 practices**
```
Send single message with 4 Agent tool calls:
- Agent 1: Generate Practice 1 mapping
- Agent 2: Generate Practice 2 mapping  
- Agent 3: Generate Practice 3 mapping
- Agent 4: Generate Practice 4 mapping
All run concurrently, no shared token budget
```

**Example: Phase 3 with 4 practices**
```
Send single message with 4 Agent tool calls:
- Agent 1: Generate Practice 1 JSON
- Agent 2: Generate Practice 2 JSON
- Agent 3: Generate Practice 3 JSON
- Agent 4: Generate Practice 4 JSON
Then combine into method JSON and validate
```

### Why This Works

Each phase is designed to be **stateless** and **file-driven**:

- Phase 1 reads: source materials, domain-framework.md
- Phase 2 reads: 01-analysis-report.md, baseline JSON, semantics.md
- Phase 3 reads: 02-mapping-guide.md, baseline JSON, language.schema.json

No conversational context is required - only file contents.

### Example Flow: Single Practice

```text
[Planning complete]
→ Compact conversation
→ Phase 1: Read prompts/phase-1-analysis.md, generate 01-analysis-report.md
[Phase 1 complete]
→ Compact conversation  
→ Phase 2: Read prompts/phase-2-mapping.md + 01-analysis-report.md, generate 02-mapping-guide.md
[Phase 2 complete]
→ Compact conversation
→ Phase 3: Read prompts/phase-3-json.md + 02-mapping-guide.md, generate JSON
[Phase 3 complete]
```

### Example Flow: Multi-Practice Method (4 practices) - Multi-Agent Approach

```text
[Planning complete]
→ Phase 1: Generate 01-analysis-report.md (covers all 4 practices)
[Phase 1 complete]

→ Phase 2: Launch 4 parallel agents in single message
  - Agent 1: Generate Practice 1 mapping (alphas + work products + activities)
  - Agent 2: Generate Practice 2 mapping (alphas + work products + activities)
  - Agent 3: Generate Practice 3 mapping (alphas + work products + activities)
  - Agent 4: Generate Practice 4 mapping (alphas + work products + activities)
  [All agents run concurrently]
→ Combine practice mappings into 02-mapping-guide.md
[Phase 2 complete]

→ Phase 3A: Launch 4 parallel agents in single message
  - Agent 1: Generate practice-1.json
  - Agent 2: Generate practice-2.json
  - Agent 3: Generate practice-3.json
  - Agent 4: Generate practice-4.json
  [All agents run concurrently]
→ Phase 3B: Assemble method JSON
  - Combine 4 practice JSONs into method structure
  - Merge citations
  - Write method-name.json
→ Phase 3C: Validate and fix
  - Run validation script
  - Fix errors until 0 errors
[Phase 3 complete]
```

**Benefits of Multi-Agent Approach:**
- ✅ **No token budget issues** (each agent has independent budget)
- ✅ **No quality degeneration** (Practice 4 gets same quality as Practice 1)
- ✅ **4x faster** (concurrent execution vs sequential)
- ✅ **Simpler prompts** (each agent focuses on one practice)
- ✅ **No manual compaction needed** (agents handle it automatically)

---

### Step 1: Phase 1 - Analysis

**Objective:** Extract and organize methodology into structured analysis

**BEFORE STARTING:** Consider compacting conversation if context is large (see Token Budget Management above).

**Process:**

1. **Read prompt:** `prompts/phase-1-analysis.md`
   - This prompt contains complete instructions for Phase 1
   - Follow all steps exactly as specified

2. **Load domain framework:** Read `references/domain-framework.md`
   - Understand four perspectives: Business, Technology, People, Process

3. **Analyze source materials:**
   - Extract outcomes, concerns, progressive states, work products
   - **Identify concern relationships and interactions:**
     - Production flows: Which concerns produce/generate/create other concerns?
     - Enablement patterns: Which concerns enable/support/facilitate others?
     - Governance structures: Which concerns guide/constrain/govern others?
     - Information flows: Which concerns provide data to/inform/validate others?
     - Dependencies: Which concerns require/depend on others?
   - Identify activities, competencies, personas, teams
   - Map workflows and patterns
   - **Note on practice boundaries:**
     - Phase 1 extracts concerns WITHOUT determining practice boundaries
     - Phase 1 does NOT identify primary alphas (need baseline context first)
     - Phase 1 does NOT decide practice vs method (need baseline alpha mapping first)
     - **Practice delineation happens in Step 1.5** (Delineation Gate) before Phase 2 delegation
     - If source has obvious separate sections (chapters/domains), note them, but don't finalize boundaries yet

4. **Generate output:** Write to `practices/<practice-name>/01-analysis-report.md`
   - Follow exact format from phase-1-analysis.md prompt
   - ~30-50K words structured markdown
   - Complete, no placeholders

**Quality Gates:**
- ✓ All four perspectives represented
- ✓ Clear traceability: Outcomes → Concerns → States → Work Products → Activities
- ✓ **Concern relationships documented:** Production, enablement, governance, information flows identified
- ✓ Progressive states reflect source's natural maturity (not forced template)
- ✓ Rich activity narratives with citations
- ✓ Preliminary practice structure noted (final boundaries deferred to Phase 2)

**User Feedback:** Brief progress updates

- "Analyzing source materials using four-perspective framework..."
- "Extracted N concerns across M perspectives..."
- "Phase 1 complete: Analysis report generated at practices/<name>/01-analysis-report.md"

**CRITICAL: Phase 1 Completion Validation (REQUIRED)**

After generating `01-analysis-report.md`, IMMEDIATELY validate completeness before proceeding to Phase 2:

```bash
python3 utils/validate-phase-output.py practices/<name>/01-analysis-report.md --phase 1
```

This checks: 8 required sections exist (Outcomes through Workflows), section count ≥8, numbered subsection count ≥5. Output is structured JSON with pass/fail per check.

**If ANY section is missing:**
1. Identify which sections are incomplete
2. Review Phase 1 prompt requirements  
3. Re-read source materials for missing content
4. Generate missing sections BEFORE proceeding to Phase 2

**Common Phase 1 Omissions:**
- Activities section empty or with only 1-2 activities (should have 5-15)
- Work products section missing or incomplete (should have 5-10)
- Competencies section sparse (should have 5-10 domain-specific competencies)
- Workflows section empty (should have 2-5 workflow patterns)

### Step 1.5: Practice Delineation Gate (Main Agent Only)

**Objective:** Determine practice structure BEFORE delegating Phase 2 mapping.

**CRITICAL:** This step MUST be performed by the main agent, not delegated to subagents. The delegation strategy (single agent vs parallel agents) depends on this step's outcome. Phase 2 subagents will independently validate this decision via Step 0 of `phase-2-mapping.md`.

**Process:**

1. **Load baseline practice JSON** (use effective baseline from Step 0.5 if dependencies were resolved, otherwise use the user-provided baseline directly):
   ```bash
   python3 utils/inspect-practice-json.py <effective-baseline-or-baseline.json> --extract alphas
   ```
   If the effective baseline has `_aliasContext`, review domain aliases to understand the baseline's domain-specific terminology. Use canonical names for structural decisions, but let domain aliases inform your semantic understanding of each alpha's role.

   **Parent Practice Mode:** Also load the effective parent JSON:
   ```bash
   python3 utils/inspect-practice-json.py <effective-parent.json> --extract alphas
   ```
   Build a combined alpha index: parent practice alphas are the **primary mapping targets**; baseline alphas provide ontology context and support redeclarations of baseline-level concepts.

2. **Map Phase 1 concerns to alphas:**
   
   **Standard baseline mode:**
   - Which baseline alphas does the content enrich (redeclarations)?
   - Which baseline alphas need specialization (new alphas with `contributesTo`)?
   - Count total baseline alpha coverage (both redeclarations + contributesTo targets)
   
   **Parent practice mode:**
   - Which **parent practice** alphas does the content enrich (redeclarations of parent practice alphas)?
   - Which **parent practice** alphas need further specialization (new alphas with `contributesTo` pointing to parent practice alphas)?
   - Which **baseline** alphas are directly relevant but NOT already covered by the parent practice? (these can still be redeclared or specialized directly)
   - Count total alpha coverage using parent practice alphas as the primary set

3. **Analyze coverage pattern:**
   - **Focused** (3-7 alphas in 1-2 focuses) → Likely single practice
   - **Broad** (8+ alphas across all 3 focuses) → Likely method requiring subdivision

4. **If focused (3-7 alphas):**
   - Identify ONE primary alpha from content
   - Use baseline `relatesTo` to find related alphas (1-level deep)
   - Validate: Does content naturally organize around this primary alpha?
   - **Decision: Single Practice** ✓

5. **If broad (8+ alphas):**
   - Identify multiple potential primary alphas from content
   - For each candidate primary alpha:
     - What content clusters around it?
     - What related alphas (via `relatesTo`) does it pull in?
     - Does this create a coherent 3-7 alpha practice?
   - Check for natural separation from source material
   - **Decision: Method with 2+ Practices** ✓
     - Create one practice per primary alpha cluster
     - Each practice: 1 primary + 2-6 related = 3-7 total

6. **If practice boundaries unclear:**
   - **Ask user** for guidance
   - Present analysis of alpha coverage and potential primary alpha options
   - Get confirmation before proceeding

**GATE DECISION:**

- **Single Practice** → Step 2 delegates to one agent (or main agent proceeds directly)
- **Multi-Practice Method** → Step 2 launches parallel agents, one per practice

**Pass delineation results to Phase 2 agents:** Include the primary alpha decision, alpha coverage list, and practice boundaries in each agent's prompt so they can validate via Step 0 of `phase-2-mapping.md`.

For the full Primary Alpha Focus Strategy with worked examples, see the **Practice vs Method Handling** reference section below.

### Step 2: Phase 2 - Mapping

**Objective:** Map Phase 1 analysis to baseline practice framework

**Prerequisite:** Step 1.5 delineation gate must be complete.

**APPROACH DECISION (from Step 1.5):**

- **Single Practice**: Generate mapping guide directly (one step)
- **Multi-Practice Method (2+ practices)**: Use parallel Agent tool approach

**Process for Single Practice:**

1. Read `prompts/phase-2-mapping.md`, analysis report, effective baseline JSON (from Step 0.5, or user-provided baseline if no dependencies), semantics.md
   - **Parent practice mode:** Also read the effective parent JSON (`_effective-parent.json`). During mapping, `contributesTo` targets should primarily reference parent practice alphas using canonical names. The effective parent's alphas are the primary mapping targets; baseline alphas provide ontology context. If the effective parent has `_aliasContext`, use aliases for semantic understanding but always use canonical names in structural references.
2. **Document primary alpha decision** at top of mapping guide (Delineation Analysis section)
   - **Parent practice mode:** Document which parent practice alphas are being extended and which (if any) baseline alphas are being addressed directly.
3. Map concerns to alphas (redeclaration vs specialization)
3. **CRITICAL: Ensure global name uniqueness across all PracticeElements:**
   - As you name Alphas, WorkProducts, Activities, Personas, Patterns, Assets: verify each name is GLOBALLY UNIQUE
   - **NO name may appear in more than one element type** (e.g., cannot have Alpha "Platform Configuration" AND WorkProduct "Platform Configuration")
   - When naming elements, choose distinct names:
     - Alphas: Abstract concepts (e.g., "Platform Configuration", "Inference Service Configuration")
     - WorkProducts: Artifacts with specificity (e.g., "Platform Configuration File", "Inference Service Configuration File")
     - Activities: Action-oriented with verbs (e.g., "Configure Platform", "Deploy Inference Service")
   - If you find a name collision during mapping, rename immediately before proceeding
4. **Identify terminology aliases and keywords:**
   - Review source methodology for domain canonical terms
   - Apply decision tree: variant→alias, instance→use instance, specialization→alias new alpha, synonym/acronym→keyword
   - **ONE alias per element** (no duplicates for same baseline element)
   - **Use keywords for synonyms/acronyms** (10-20 search/discovery terms)
   - Target: 3-8 aliases + 10-20 keywords
   - Document in "Keywords" and "Terminology Aliases" sections
4. **Map concern relationships to alpha relatesTo arrays:**
   - Review Phase 1 concern interactions
   - For each NEW alpha, identify what it provides/enables/produces/guides/validates for other alphas
   - Use active voice from provider perspective (directionality pattern)
   - Document relationships in mapping guide
5. **Generate patterns using FOUR-PASS construction:**
   - Pass 1: Extract pattern structure from source (phases, explicitly mentioned states)
   - Pass 2: Backfill missing alpha states for complete matrix (REQUIRED)
   - Pass 3: Consider related alphas from practice/dependencies (OPTIONAL)
   - Pass 4: State distribution validation (REQUIRED - max 2 states per alpha per view, backfill late-appearing alphas)
6. Generate complete `02-mapping-guide.md` with terminology aliases, all alphas (including relatesTo), work products, activities, complete patterns

**Process for Multi-Practice Method:**

1. **Launch parallel agents** (one per practice) in single message:
   
   ```
   Agent(description="Map Practice 1", prompt="...")
   Agent(description="Map Practice 2", prompt="...")  
   Agent(description="Map Practice 3", prompt="...")
   Agent(description="Map Practice 4", prompt="...")
   ```

2. **Each agent prompt must include:**
   - **Delineation context from Step 1.5:** "You are mapping Practice N of M in a method. Your primary alpha is [X], covering alphas [list]. Validate this delineation in your Step 0 of phase-2-mapping.md."
   - File paths to read: `practices/<method-name>/01-analysis-report.md` (practice-specific section), `<effective-baseline-path>` (from Step 0.5, or user-provided baseline if no dependencies), `references/semantics.md`, `prompts/phase-2-mapping.md`
   - **Parent practice mode:** Also include the effective parent JSON path (`_effective-parent.json`). Add to agent prompt: "You are extending a parent practice, not mapping directly to the baseline. The effective parent's alphas are your primary `contributesTo` targets. Use canonical names for all structural references. The actual baseline provides ontology context and validation targets. IMPORTANT: `practiceDependencyNames` must only include parent practices whose unique alphas (those NOT in the effective baseline) are actually referenced via `contributesTo`. Do NOT include a parent practice just because its redeclared baseline alphas are referenced."
   - If the effective baseline has `_aliasContext`, include in the agent prompt: "The baseline includes domain-specific aliases (e.g., 'Platform' is known as 'Automation Platform' in this domain). Use domain terms for semantic understanding but always use canonical names in structural references."
   - What to generate: Complete practice mapping with metadata, terminology aliases, alphas (with relatesTo), work products, activities, patterns
   - Output location: Write to `practices/<method-name>/02-mapping-guide-practice-N.md` OR append to shared file with clear section markers
   - Explicit instruction: "Generate COMPLETE mapping including: (0) Delineation Analysis section validating your practice boundaries; (1) Keywords section with 10-20 domain terms/acronyms; (2) Terminology Aliases section identifying 3-8 domain canonical terms (ONE alias per element - use keywords for synonyms/acronyms, use instances for multiple variants); (3) Alphas (if any) WITH relatesTo relationships; (4) Work products; (5) Activities; (6) PATTERNS with complete matrix coverage. CRITICAL: Map concern interactions from Phase 1 to alpha relatesTo arrays using directionality pattern. Every practice MUST have at least ONE pattern coordinating multiple alphas/concerns (see semantics.md Section 8.1.1)."

3. **After all agents complete:**
   - Combine practice mapping files into single `02-mapping-guide.md` (if using separate files)
   - Add method-level metadata (citations, method narrative)
   - Validate completeness: every practice has alphas + work products + activities

**Critical: Multi-Agent Benefits**
- ✅ No token budget sharing between agents
- ✅ Concurrent execution (4 practices finish in time of 1)
- ✅ No quality degeneration (Practice 4 gets same quality as Practice 1)
- ✅ Each agent focuses on single practice (cleaner, more focused)
   - Complete mapping specification
   - Validation checklist satisfied

**CRITICAL: Terminology Aliasing for Domain Alignment**

**Aliases bridge the gap between baseline practice terminology and source methodology vocabulary.**

From `references/semantics.md` Section 9.2:

**When to Create Aliases:**
- Source methodology uses different term for same baseline concept
- Baseline term is abstract/generic, source uses domain-specific term
- Domain-specific terminology represents element differently
- **ONE alias per PracticeElement** - if multiple terms exist, choose most canonical/common one

**CRITICAL: One Alias Per Element**
- Do NOT create multiple aliases for the same element (e.g., Platform → "AAP", Platform → "Automation Controller", Platform → "Automation Platform")
- If you have multiple distinct terms, determine what they represent:
  - **Synonyms/acronyms** → Use keywords, not aliases
  - **Different facets/components** → Use specializations (e.g., Automation Controller, Execution Environment are specialized alphas)
  - **Different deployments** → Use instances (e.g., Sandbox Platform, Production Platform)
- Example WRONG: Platform → "Automation Controller" (Controller is a facet/specialization, not an alias!)
- Example CORRECT: Create specialized alpha "Automation Controller" with contributesTo: Platform, then add keywords ["AAP", "Ansible Automation Platform", "automation platform"] to practice

**Alias Priority (where to apply aliases):**
1. **Work products**: When domain uses distinctly different canonical term (e.g., Deployment Documentation → "Playbook")
2. **Activities**: When domain uses different operation names (e.g., Deploy System → "Run Playbook")
3. **Personas**: When domain uses different role titles (e.g., Platform Engineer → "Automation Architect")
4. **Specialized alphas**: OPTIONAL - only if shortened form is canonical (e.g., Execution Environment → "EE")
5. **Baseline elements**: RARELY - only if domain uses completely different term

**Understanding Instances vs Specializations:**
- **Instances** = Same type, different deployments (Sandbox Platform, Non-Prod Platform, Production Platform)
  - Same behavior, same states, different tracking
  - Used for environment-specific tracking (dev/test/prod)
  - Aliases on instances are rare (instances already have distinct names)
  
- **Specializations** = Different facets/components with specialized behavior
  - New alpha with contributesTo pointing to parent
  - Different states/lifecycle than parent
  - Example: Automation Controller, Execution Environment, Automation Mesh are specialized facets of Platform
  - May have aliases if domain uses shortened forms

**Alias can be combined with:**
- Redeclaration (enriching baseline element - rarely needs alias unless domain term differs significantly)
- Specialization (new alpha representing facet/component + optional alias for shortened form)

**PracticeElementAlias Structure:**
```json
{
  "elementType": "Alpha | WorkProduct | Activity | Persona | PersonaGroup",
  "name": "canonical baseline name",
  "aliasName": "domain-specific alternative term"
}
```

**CRITICAL RULE: Strict Alias Isolation**
- Aliases are PRESENTATION-LAYER ONLY
- **NEVER use aliasName in structural references** (alphaName, activitySpaceName, contributesTo, etc.)
- ALL structural references MUST use canonical baseline names
- Aliases enable user-facing terminology without breaking validation

**Example: Ansible Automation Platform Aliases (CORRECT)**

```markdown
## Terminology Aliases

**Alpha Specializations with Aliases:**
- Execution Environment → "EE" (common abbreviation for specialized alpha)
- Automation Mesh → "Mesh" (shortened domain term)
- Event Rulebook → "Rulebook" (domain canonical term)

**Alpha Instance Aliases:**
- Automation Controller (instance of Platform) → "Controller" (shortened)
- Execution Node Pool (instance of Platform) → "Execution Nodes" (domain term)

**WorkProduct Aliases:**
- Deployment Documentation → "Playbook" (canonical Ansible term)
- Architecture Definition → "Inventory" (Ansible-specific)
- Credential → "Vault Credential" (domain-specific type)

**Activity Aliases:**
- Deploy System → "Run Playbook" (canonical Ansible operation)
- Build Container Image → "Build EE" (domain shorthand)

**Persona Aliases:**
- Platform Engineer → "Automation Architect" (domain job title)
- Developer → "Content Developer" (Ansible-specific role)
```

**Anti-Pattern Examples (WRONG):**

**Example 1 - Ansible: Multiple aliases for one element**
```markdown
❌ WRONG:
- Platform → "Automation Platform"
- Platform → "AAP"
- Platform → "Ansible Automation Platform"
- Platform → "Automation Controller"

Problems:
1. "AAP", "Automation Platform" are SYNONYMS → use keywords!
2. "Automation Controller" is a COMPONENT → use specialization!
```

**Example 2 - OpenShift: Confusing instances with specializations**
```markdown
❌ WRONG:
- Platform → "Production Cluster" (instance, not alias!)
- Platform → "OCP" (synonym → keyword!)
- Platform → "OpenShift Container Platform" (synonym → keyword!)

Problems:
1. "Production Cluster" is a deployment → use instance!
2. "OCP", "OpenShift Container Platform" are synonyms → use keywords!
```

**Example 3 - Team Topologies: Confusing instances with aliases**
```markdown
❌ WRONG:
- Team → "Stream-Aligned Team"
- Team → "Platform Team"
- Team → "Enabling Team"
- Team → "Complicated Subsystem Team"

Problem: These are TEAM TYPES → use instances, not aliases!
- Stream-Aligned Team, Platform Team, etc. are instances of Team
- Each team type has same behavior/states, different classification
- Do NOT alias baseline Team multiple times
```

**CORRECT Alternatives:**

```markdown
## Ansible (CORRECT)
Keywords: ["AAP", "ansible automation platform", "ansible", "controller", "EE"]
Aliases: Platform → "Automation Platform", Deployment Documentation → "Playbook"
Specializations: Execution Environment (component with unique build→publish lifecycle)
Instances: Production Automation Platform, Staging Automation Platform (deployments)

## OpenShift (CORRECT)
Keywords: ["OCP", "openshift", "k8s", "kubernetes", "container platform"]
Aliases: Infrastructure Definition → "Operator Manifest"
Specializations: Application Scalability (capability with unique scaling states)
Instances: Production OCP Cluster, Dev OCP Cluster (deployments)

## Team Topologies (CORRECT)
Keywords: ["stream-aligned", "platform team", "enabling team", "cognitive load"]
Aliases: Activity → "Team Interaction Design" (minimal aliases needed)
Specializations: Team Topology Design, Cognitive Load (concepts with unique states)
Instances: Stream-Aligned Team, Platform Team, Enabling Team (team types)
Instances: Platform Engineering Team Alpha, Payments Team (specific named teams)
```

**Alias Identification Heuristics:**

**Decision Tree for Each Domain Term:**

1. **Is this term a canonical alternative to a baseline element?**
   - YES → Consider alias (e.g., "Playbook" for "Deployment Documentation")
   - NO → Go to step 2

2. **Does this term represent a different deployment of same type?**
   - YES → Use **instance** (e.g., "Sandbox Platform", "Production Platform")
   - Instances = same behavior, different tracking (dev/test/prod environments)
   - NO → Go to step 3

3. **Does this term represent a facet/component with specialized behavior?**
   - YES → Use **specialization** (e.g., "Automation Controller", "Execution Environment" are facets of Platform with unique lifecycles)
   - Specializations = new alpha with contributesTo, different states/behavior
   - Optional: alias the specialized alpha if domain uses shortened form
   - NO → Go to step 4

4. **Is this an acronym/abbreviation/synonym?**
   - YES → Add to **keywords** array (e.g., "AAP", "automation platform", "EE")
   - NO → Skip

**Three-Way Distinction:**
- **Alias (1 per element):** "Playbook" replaces "Deployment Documentation" in presentation
- **Keywords (10-20 per practice):** ["AAP", "ansible", "automation", "controller", "EE"] for search
- **Specialization:** "Automation Controller" is new alpha (facet of Platform with unique states)
- **Instance:** "Production Platform" is deployment tracking (same states as Platform)

**Examples Across Domains:**

**Ansible Automation:**
- "Automation Platform" vs "Platform" → **Alias** (canonical domain term) ✓
- "Playbook" vs "Deployment Documentation" → **Alias** ✓
- "Production Automation Platform" vs "Staging Automation Platform" → **Instances** (deployments) ✓
- "Execution Environment" has unique build→publish lifecycle → **Specialization** (component/facet) ✓
- "AAP", "ansible", "controller", "EE" → **Keywords** ✓

**OpenShift:**
- "Deployment Config" vs "Deployment Documentation" → **Alias** ✓
- "Production OCP Cluster" vs "Dev OCP Cluster" → **Instances** (deployments) ✓
- "Application Scalability" has unique states → **Specialization** (capability) ✓
- "OCP", "openshift", "k8s", "container platform" → **Keywords** ✓

**Team Topologies:**
- "Stream-Aligned Team", "Platform Team", "Enabling Team" → **Instances** (team types) ✓
- "Platform Engineering Team Alpha", "Payments Team" → **Instances** (specific teams) ✓
- "Cognitive Load", "Team Interaction Mode" → **Specializations** (organizational concepts) ✓
- "stream-aligned", "enabling team", "cognitive load" → **Keywords** ✓

**Complete Example - Multi-Domain Pattern:**
```markdown
## Example 1: Ansible Automation Practice

### Keywords (search/discovery)
["AAP", "ansible automation platform", "ansible", "automation", "controller", 
 "EE", "execution environment", "playbook", "inventory", "mesh", "hub", 
 "event-driven", "rulebook", "RBAC"]

### Alphas (specializations = facets/components)
- **Execution Environment** (specialization of Platform)
  - contributesTo: Platform
  - States: Default Available → Custom Built → Governed → Optimized

### Alpha Instances (deployments)
- Production Automation Platform (instance of Platform)
- Staging Automation Platform (instance of Platform)

### Terminology Aliases (3-5 canonical terms)
- Platform → "Automation Platform" (canonical Ansible term for platform)
- Deployment Documentation → "Playbook"
- Deploy System → "Run Playbook"
- Platform Engineer → "Automation Architect"

---

## Example 2: OpenShift Platform Practice

### Keywords (search/discovery)
["OCP", "openshift", "kubernetes", "k8s", "container platform", "pods", 
 "operators", "routes", "deployment", "imagestream"]

### Alphas (specializations)
- **Application Scalability** (specialization of Software System)
  - contributesTo: Software System
  - States: Manual Scaling → HPA Configured → Custom Metrics → Predictive

### Alpha Instances (deployments)
- Production OCP Cluster (instance of Platform)
- Non-Prod OCP Cluster (instance of Platform)

### Terminology Aliases (3-5 canonical terms)
- Deployment Documentation → "Deployment Config"
- Infrastructure Definition → "Operator Manifest"
- Deploy System → "oc apply"

---

## Example 3: Team Topologies Practice

### Keywords (search/discovery)
["stream-aligned", "enabling team", "platform team", "complicated subsystem",
 "cognitive load", "team interaction", "conway's law", "inverse conway",
 "team types", "interaction modes"]

### Alphas (specializations = organizational concepts)
- **Team Topology Design** (specialization of Team)
  - contributesTo: Team
  - States: Static Structure → Four Types Defined → Explicit Modes → Sensing & Evolving

- **Cognitive Load** (new alpha)
  - contributesTo: Team
  - States: Unmanaged → Load Awareness → Domain Boundaries → Active Reduction

### Alpha Instances (team types as instances of Team)
- Stream-Aligned Team (instance of Team - team type)
- Platform Team (instance of Team - team type)
- Enabling Team (instance of Team - team type)
- Complicated Subsystem Team (instance of Team - team type)

### Alpha Instances (specific named teams)
- Platform Engineering Team Alpha (instance of Team - specific team)
- Payments Stream Team (instance of Team - specific team)
- Data Platform Team (instance of Team - specific team)

### Terminology Aliases (3-5 canonical terms)
- Activity → "Team Interaction Design"
- Way Of Working → "Team Working Agreement"
```

**Quality Target:** 3-8 aliases per practice (focused on genuinely different canonical terms)

**Phase 2 Mapping Template:**

```markdown
## Keywords

**Purpose:** Synonyms, acronyms, abbreviations, search terms for discoverability

[List 10-20 domain-specific terms, acronyms, product names, abbreviations from source methodology]

**General Pattern:** Include:
- Product/vendor names and acronyms
- Domain-specific terminology and jargon
- Component/feature names
- Common abbreviations
- Alternative terms for baseline concepts

## Terminology Aliases

**CRITICAL RULE: ONE alias per element. Use keywords for multiple synonyms.**

### WorkProduct Aliases
- [Baseline WorkProduct] → "[Domain Term]" (canonical domain equivalent)

### Activity Aliases  
- [Baseline Activity] → "[Domain Operation]" (domain-specific operation name)

### Persona Aliases
- [Baseline Persona] → "[Domain Role]" (job title in this domain)

### Specialized Alpha Aliases (OPTIONAL - only if aliasing the NEW alpha)
- [New Alpha Name] → "[Domain Short Form]" (shortened/alternative term)

**Total: 3-8 aliases** (focus on genuinely different canonical terms)
**Total Keywords: 10-20 terms** (all synonyms, acronyms, search terms)
```

**Critical Mapping Rules:**

From `references/semantics.md`:

- **EXACT COMPETENCY LEVEL NAMES:** All `competencyLevelName` values MUST exactly match CompetencyLevel.name from baseline practice for the specific competency
  - **Level names vary by competency** - each competency defines its own level progression
  - **Extract baseline competency levels:** `python3 utils/inspect-practice-json.py <baseline-practice.json> --check competencies`
  - Example (Platform Adoption Essentials - Analysis competency): "Basic", "Applies", "Masters", "Adapts", "Innovating"
  - Common errors: "Advanced" (check baseline for actual name), "Expert" (check baseline), "Intermediate" (check baseline), "Beginner" (check baseline)
  - **Validate all competencyLevelName values in Phase 2 mapping guide against baseline competency levels**
  - Validation command: For each competencyLevelName in mapping, verify it exists in that competency's levels array
- **NO FLOATING ALPHAS:** All new alphas MUST have `contributesTo` (Section 4.1)
  - Valid targets: baseline alphas, practice-local alphas (internal hierarchy), or external practice alphas (creates dependency)
  - Practice-local references create multi-level specialization chains (Alpha C → B → A → Baseline)
  - External practice references require explicit practice dependency declaration
- **SEMANTIC RELATIONSHIPS:** Use baseline `relatesTo` for analysis; define new relationships for new alphas (Section 4.1 - Semantic Relationships)
  - **For baseline alpha analysis**: Read existing `relatesTo` relationships from baseline and dependent practices to understand how the alpha functions within the framework
  - **For new alphas ONLY**: Define domain-specific `relatesTo` relationships using appropriate relationship verbs
  - **Do NOT** add `relatesTo` to redeclarations - these inherit baseline relationships
  - **DIRECTIONALITY PATTERN (CRITICAL)**: The alpha declaring `relatesTo` is the SOURCE imparting something to the target alphas
    - Read as: `[Alpha with relatesTo] [relationship verb] [target alphaName]`
    - Example: Platform has `relatesTo: [{relationship: "enables", alphaName: "Software System"}]` → "Platform enables Software System"
    - This is a "reverse dependency" pattern: declare what you provide/influence, not what you depend on
    - Benefits: Localized declarations, producer/provider pattern, new alphas don't require modifying existing ones
  - **IDENTIFYING RELATIONSHIPS**: Look for interactions between concerns in Phase 1 analysis where one concern provides/influences another:
    - Production: "Alpha A produces B", "Alpha A generates B", "Alpha A creates B"
      - → A.relatesTo = [{relationship: "produces", alphaName: "B"}]
    - Enablement: "Alpha A enables B", "Alpha A supports B", "Alpha A facilitates B"
      - → A.relatesTo = [{relationship: "enables", alphaName: "B"}]
    - Guidance: "Alpha A guides B", "Alpha A constrains B", "Alpha A governs B"
      - → A.relatesTo = [{relationship: "guides", alphaName: "B"}]
    - Information flow: "Alpha A provides data to B", "Alpha A informs B"
      - → A.relatesTo = [{relationship: "provides", alphaName: "B"}]
    - Validation: "Alpha A validates B", "Alpha A verifies B", "Alpha A evidences B"
      - → A.relatesTo = [{relationship: "validates", alphaName: "B"}]
    - Impact: "Alpha A influences B", "Alpha A justifies B"
      - → A.relatesTo = [{relationship: "influences", alphaName: "B"}]
    - Hosting/Consumption: "Alpha A hosts B", "Alpha A contains B"
      - → A.relatesTo = [{relationship: "hosts", alphaName: "B"}]
  - **REVERSE DEPENDENCIES**: For dependency relationships, flip the direction:
    - Source says "X requires Y" → Y.relatesTo = [{relationship: "required by", alphaName: "X"}] OR X.relatesTo = [{relationship: "depends on", alphaName: "Y"}]
    - Prefer active voice from provider perspective: "Y enables X" over "X depends on Y"
- **Exact name matching:** All baseline references are case-sensitive (Section 3)
- **Orthogonal tags:** Use {domainTags, lifecycleTags, organizationalTags} (Section 3.1.2)
- **Redeclaration vs Specialization:** Follow decision framework (Section 9.2.5)
- **Competency names:** Use EXACT baseline names, not descriptions (Section 6.2)
- **Single sentences:** Descriptions max 20 words, states/LODs max 12 (Section 3.1)

**CRITICAL: Narrative Structure Requirements**

**ALL narratives MUST be structured objects with narrativeTypeName and narrativeContexts arrays. NEVER use prose paragraphs.**

**CRITICAL: Narrative Content Rules**

- **NEVER reference the narrative name, type, or framework within the narrative itself**
- Narrative name/description are metadata - they identify the narrative structure externally
- Narrative contexts contain the actual story content - they should NOT mention the narrative type
- **WRONG**: "In this Hero's Journey narrative, organizations embark on..." or "This narrative describes..."
- **CORRECT**: "Organizations operate with fragmented infrastructure..." (direct story content)

From `prompts/phase-2-mapping.md` (lines 87-89, 525-530):

1. **Practice/Method Narratives** - REQUIRED structured format:
   ```
   Practice Narrative:
   - Narrative Type Name: STAR | Hero's Journey | Three-Act Structure | Essay
   - Narrative Contexts:
     - Seq: 1, Narrative Element Name: [Situation], Context: [1-3 sentences]
     - Seq: 2, Narrative Element Name: [Task], Context: [1-3 sentences]
     - Seq: 3, Narrative Element Name: [Action], Context: [1-3 sentences]
     - Seq: 4, Narrative Element Name: [Result], Context: [1-3 sentences]
   ```

2. **Alpha Narratives** - REQUIRED for new alphas, RECOMMENDED for redeclarations:
   ```
   Narrative:
   - Narrative Type Name: Essay
   - Narrative Contexts:
     - Seq: 1, Narrative Element Name: Introduction, Context: Why this alpha matters
     - Seq: 2, Narrative Element Name: Body, Context: Key considerations and relationships
     - Seq: 3, Narrative Element Name: Conclusion, Context: Success factors
   - Citation Names: [citation references]
   ```

3. **Activity Narratives** - REQUIRED for all activities:
   ```
   Narrative:
   - Narrative Type Name: Technique
   - Narrative Contexts:
     - Seq: 1, Narrative Element Name: Overview, Context: What this activity accomplishes
     - Seq: 2, Narrative Element Name: Technique, Context: Step-by-step how-to guidance
     - Seq: 3, Narrative Element Name: Common Pitfalls, Context: What to avoid
   - Citation Names: [authoritative source references]
   ```

4. **Pattern Narratives** - Already structured in pattern views (keep as-is)

5. **Work Product Narratives** - OPTIONAL but recommended for complex work products

**Narrative Content Examples:**

**WRONG (Self-Referential):**
```
- Context: "In this Hero's Journey narrative, platform engineering organizations embark on a transformation..."
- Context: "This Essay-type narrative explores how Platform Capabilities evolve..."
- Context: "The following narrative describes the maturation journey..."
```

**CORRECT (Direct Content):**
```
- Context: "Organizations operate with fragmented infrastructure managed by siloed teams..."
- Context: "Platform Capabilities evolve from tactical solutions to strategic enablers..."
- Context: "Teams mature from reactive firefighting to proactive platform stewardship..."
```

**WRONG (Prose Paragraph):**
```
Practice Narrative:
OpenShift Administration addresses the foundational infrastructure and operational 
concerns for enterprise container platforms. Organizations adopting OpenShift must...
```

**CORRECT (Structured Object):**
```
Practice Narrative:
- Narrative Type Name: STAR
- Narrative Contexts:
  - Seq: 1
    Narrative Element Name: Situation
    Context: Organizations face infrastructure challenges requiring enterprise container platforms.
  - Seq: 2
    Narrative Element Name: Task
    Context: Platform teams must establish secure, resilient OpenShift infrastructure.
  - Seq: 3
    Narrative Element Name: Action
    Context: Implement progressive maturity states from architecture to automated compliance.
  - Seq: 4
    Narrative Element Name: Result
    Context: Secure self-service container infrastructure delivered to development teams.
```

**Quality Check During Mapping:**
- [ ] Practice narrative uses structured format (NOT prose)
- [ ] Method narrative uses structured format (NOT prose)
- [ ] All new alphas have narrative objects with narrativeTypeName
- [ ] All activities have Technique narrative objects
- [ ] All narrative contexts are 1-3 sentences (NOT paragraphs)
- [ ] **Narrative contexts contain direct content (NO self-references to narrative type/name)**
- [ ] Citations referenced in citationNames arrays

**CRITICAL: Pattern Completeness Requirements**

**Patterns MUST show complete alpha state progressions across all PatternViews.**

Common anti-pattern: Patterns only include alpha states explicitly mentioned in source content, resulting in sparse/incomplete pattern matrices with missing cells.

**FOUR-PASS PATTERN CONSTRUCTION:**

**Pass 1: Source-Driven Pattern Structure**
- Extract pattern structure from source methodology
- Identify phases/stages (PatternViews) from source content
- Map explicitly mentioned alpha states to PatternViews
- Result: Initial pattern structure with explicit source mappings

**Pass 2: Alpha-Driven Completeness (REQUIRED)**
- **For each alpha in the pattern:**
  - Review ALL states of the alpha
  - For EACH PatternView, determine appropriate state:
    - **First View (Prerequisites/Initial):** Starting state or "not yet started" state
    - **Middle Views:** Progressive states showing maturation
    - **Last View (Target/Final):** Advanced/optimized state
  - **Backfill missing alpha states** using these heuristics:
    - If alpha doesn't appear in a view, identify which state is appropriate for that lifecycle phase
    - States should progress logically across views (earlier states → later states)
    - **CRITICAL RULE:** If an alpha's state doesn't change from previous view, STILL include it in the final PatternView
    - Only omit unchanged states in non-final views (compression), NEVER in the last view

**Pass 3: Related Alpha Discovery (OPTIONAL but RECOMMENDED)**
- **Identify candidate alphas from:**
  - Other alphas in same practice (not yet in pattern)
  - Alphas from practice dependencies (excluding baseline unless explicitly relevant)
  - Alphas related via `relatesTo` relationships
- **For each candidate alpha, evaluate:**
  - Does this alpha's progression support the pattern narrative?
  - Would including this alpha states provide meaningful insights into the lifecycle?
  - Is there a natural state progression across the pattern views?
- **Add relevant alphas** with complete state progressions

**Pass 4: State Distribution Validation (REQUIRED)**

**CRITICAL QUALITY CONSTRAINTS:**

**Constraint 1: Alpha State Count Per PatternView**
- **Preference:** 1 alpha state per alpha per PatternView (one state progresses to next)
- **Maximum:** 2 alpha states per alpha per PatternView (initial + achieved in single view)
- **Anti-pattern:** 3+ states per alpha in single view → **Pattern views are too coarse-grained**

**When 3+ states appear for an alpha in a PatternView:**
- **Root Cause:** PatternView represents too broad a lifecycle phase (e.g., "Implement" covering design → build → test → deploy)
- **Fix:** Subdivide the pattern into finer-grained PatternViews
- **Example:**
  - **Before:** View 2 "Implement" has Platform states: Architecture Designed → Built → Deployed → Monitored (4 states!)
  - **After:** Split into:
    - View 2 "Design": Architecture Designed
    - View 3 "Build": Built
    - View 4 "Deploy": Deployed
    - View 5 "Operate": Monitored

**Constraint 2: Late-Appearing Alphas with Advanced States**
- **Anti-pattern:** Alpha first appears in PatternView N with state "Achieved" or other advanced state, but was NOT in PatternViews 1 to N-1
- **Problem:** Creates discontinuity - "How did we get to 'Achieved' when alpha wasn't tracked before?"
- **Fix: Backfill earlier PatternViews with alpha's progression**

**Backfill Heuristics:**
1. **Identify the "sudden appearance":**
   - Alpha X first appears in PatternView N
   - Alpha X is at state Y (not the initial state)
   - PatternViews 1 to N-1 do NOT include Alpha X

2. **Determine backfill states:**
   - Review Alpha X's state sequence: S1 → S2 → S3 → ... → Y
   - Distribute earlier states across PatternViews 1 to N-1
   - Follow natural progression: earlier views get earlier states

3. **Backfill strategy:**
   - **If N = 2 (appears in second view):** Add initial state to View 1
   - **If N = 3 (appears in third view):** Add S1 to View 1, S2 to View 2
   - **If N = 4+:** Distribute intermediate states across prior views
   - **Guideline:** 1-2 states per view (prefer 1)

4. **Validate progression coherence:**
   - Does the backfilled state align with that PatternView's narrative?
   - Does the state sequence make logical sense across views?
   - If misalignment detected, adjust PatternView granularity (may need to split views)

**Example - Late-Appearing Alpha (WRONG):**
```
Pattern: Platform Evolution Journey (5 views)
| View | Platform        | Platform Asset | Platform Capability | Platform Governance |
|------|----------------|----------------|---------------------|---------------------|
| 0    | Conceived      | [none]         | [none]              | [none]             |
| 1    | Architecture   | [none]         | [none]              | [none]             |
| 2    | Development    | [none]         | Identified          | [none]             |
| 3    | Operational    | Available      | Governed            | [SUDDEN: Compliant!]|
| 4    | Optimizing     | Optimized      | Optimized           | Automated          |
```

**Problem:** Platform Governance suddenly appears at "Compliant" in View 3 (advanced state)

**Example - Late-Appearing Alpha (FIXED with Backfill):**
```
Pattern: Platform Evolution Journey (5 views)
| View | Platform        | Platform Asset | Platform Capability | Platform Governance |
|------|----------------|----------------|---------------------|---------------------|
| 0    | Conceived      | [none]         | [none]              | Undefined          | ← BACKFILL
| 1    | Architecture   | [none]         | Identified          | Established        | ← BACKFILL
| 2    | Development    | [none]         | Governed            | Enforced           | ← BACKFILL
| 3    | Operational    | Available      | Optimized           | Compliant          | ← NOW logical!
| 4    | Optimizing     | Optimized      | [same]              | Automated          |
```

**Analysis:**
- Platform Governance backfilled into Views 0-2 with progressive states
- Now shows natural maturation: Undefined → Established → Enforced → Compliant → Automated
- No "sudden appearance" - governance is tracked from the beginning

**Validation Checklist for Pass 4:**
- [ ] Count alpha states per alpha per PatternView
- [ ] If any alpha has 3+ states in a single view → **Subdivide pattern into finer PatternViews**
- [ ] Identify any alphas appearing first in non-initial PatternView with advanced state
- [ ] For each late-appearing alpha → **Backfill earlier PatternViews with progressive states**
- [ ] Verify state sequences are logically coherent across all views
- [ ] Final PatternView includes ALL alphas (previous rule from Pass 2)

**Pattern Completeness Matrix Example:**

**BAD (Sparse Pattern - Missing Cells):**
```
| View | Team Topology Design | Cognitive Load | Team Interaction Mode | Organizational Sensing |
|------|---------------------|----------------|----------------------|----------------------|
| 0    | Static Structure    | Unmanaged Load | [MISSING]            | [MISSING]           |
| 1    | Four Types Defined  | Load Awareness | Mode Awareness       | [MISSING]           |
| 2    | Explicit Modes      | [MISSING]      | Explicit Assignment  | Sensors Established |
| 3    | Sensing & Evolving  | [MISSING]      | Strategic Evolution  | Trigger-Based       |
| 4    | Self-Steering Org   | Continuous Opt | [MISSING]            | Cybernetic Steering |
```

**GOOD (Complete Pattern - Full Coverage):**
```
| View | Team Topology Design | Cognitive Load | Team Interaction Mode | Organizational Sensing |
|------|---------------------|----------------|----------------------|----------------------|
| 0    | Static Structure    | Unmanaged Load | Undefined Interact.  | Static Organization |
| 1    | Four Types Defined  | Load Awareness | Mode Awareness       | Ad Hoc Adjustments  |
| 2    | Explicit Modes      | Domain Bounds  | Explicit Assignment  | Sensors Established |
| 3    | Sensing & Evolving  | Active Reduction| Strategic Evolution | Trigger-Based Evol. |
| 4    | Self-Steering Org   | Continuous Opt | Optimized Patterns   | Cybernetic Steering |
```

**Pattern Construction Workflow:**

1. **Extract from source:** Identify pattern name, description, phases
2. **Map explicit references:** Add alpha states mentioned in source
3. **Alpha completeness pass:**
   - List all alphas that appear in ANY PatternView
   - For each alpha, create state progression table
   - Backfill missing cells using state progression logic
4. **Related alpha discovery:**
   - Review practice alphas not yet in pattern
   - Review dependency practice alphas
   - Add alphas with meaningful progressions
5. **State distribution validation (CRITICAL):**
   - Count states per alpha per PatternView (max 2, prefer 1)
   - If 3+ states in any view → subdivide pattern into finer views
   - Identify late-appearing alphas with advanced states
   - Backfill earlier views with progressive states for late alphas
6. **Validate completeness:**
   - Every alpha has entry in every PatternView (no missing cells)
   - States progress logically from early to late
   - Final PatternView includes ALL alphas (even if state unchanged from previous view)
   - No alpha has more than 2 states in a single view
   - No alpha suddenly appears late with advanced state (backfill complete)

**Pattern Completeness Checklist (Phase 2 Mapping):**
- [ ] Pattern identifies all participating alphas upfront
- [ ] Each alpha has state progression documented across all views
- [ ] Missing cells backfilled using state sequence analysis
- [ ] Final PatternView includes ALL alphas (mandatory completeness rule)
- [ ] Related alphas from dependencies considered for inclusion
- [ ] Pattern narrative explains lifecycle progression coherently
- [ ] **State distribution quality (Pass 4):**
  - [ ] No alpha has more than 2 states in a single PatternView (prefer 1)
  - [ ] If 3+ states detected, pattern views subdivided into finer granularity
  - [ ] All alphas appearing in pattern are present from View 0 OR have clear justification
  - [ ] No alphas suddenly appear in late views with advanced states (backfill complete)

**Worked Example: Team Topology Evolution Journey**

**Pass 1 (Source-Driven):** Extract from Team Topologies book
- Pattern Name: "Team Topology Evolution Journey"
- 5 Views: Prerequisites, Crawl, Walk, Run, Fly
- Explicitly mentioned states:
  - View 0: Team Topology Design (Static), Cognitive Load (Unmanaged)
  - View 1: Team Topology Design (Four Types), Cognitive Load (Awareness), Team Interaction Mode (Awareness)
  - View 2: Team Topology Design (Explicit), Team Interaction Mode (Explicit Assignment), Org Sensing (Sensors)
  - View 3: Team Topology Design (Sensing), Org Sensing (Trigger-Based), Team Interaction Mode (Strategic)
  - View 4: Team Topology Design (Self-Steering), Org Sensing (Cybernetic), Cognitive Load (Continuous)

**Identified Alphas:** Team Topology Design, Cognitive Load, Team Interaction Mode, Organizational Sensing

**Pass 2 (Backfill Missing States):**

*Team Interaction Mode - Missing in View 0:*
- Review states: Undefined Interactions, Mode Awareness, Explicit Mode Assignment, Strategic Mode Evolution, Optimized Interaction Patterns
- View 0 (Prerequisites): "Undefined Interactions" (before awareness exists)
- **Add:** {alphaName: "Team Interaction Mode", stateName: "Undefined Interactions"}

*Organizational Sensing - Missing in View 0 and View 1:*
- Review states: Static Organization, Ad Hoc Adjustments, Teams as Sensors Established, Trigger-Based Evolution, Cybernetic Self-Steering
- View 0 (Prerequisites): "Static Organization" (traditional hierarchy)
- View 1 (Crawl): "Ad Hoc Adjustments" (starting to respond but not systematic)
- **Add:** View 0: {alphaName: "Organizational Sensing", stateName: "Static Organization"}
- **Add:** View 1: {alphaName: "Organizational Sensing", stateName: "Ad Hoc Adjustments"}

*Cognitive Load - Missing in View 2 and View 3:*
- Review states: Unmanaged Load, Load Awareness, Domain Boundaries Established, Active Load Reduction, Continuous Optimization
- View 2 (Walk): "Domain Boundaries Established" (aligns with "Explicit Interaction Modes")
- View 3 (Run): "Active Load Reduction" (proactive management)
- **Add:** View 2: {alphaName: "Cognitive Load", stateName: "Domain Boundaries Established"}
- **Add:** View 3: {alphaName: "Cognitive Load", stateName: "Active Load Reduction"}

*Team Interaction Mode - Missing in View 4:*
- **FINAL VIEW RULE:** Must include even if state unchanged
- View 4 (Fly): "Optimized Interaction Patterns" (final state)
- **Add:** View 4: {alphaName: "Team Interaction Mode", stateName: "Optimized Interaction Patterns"}

**Result:** Complete 4×5 matrix (20 alphaState entries)

**Pass 3 (Related Alpha Discovery):**
- Review practice alphas: Team, Work, Way of Working
- Review baseline alphas related to Team
- Evaluate: Would "Team" alpha state progression add value to pattern?
  - Team states: Seeded → Formed → Collaborating → Performing → Adjourned
  - Conclusion: Focus is on topology/interaction patterns, not team lifecycle - SKIP
- Evaluate: Would "Way of Working" add value?
  - Way of Working states: Principles Established → Foundation Established → In Use → In Place → Retired
  - Conclusion: Topology pattern is about structure, not process - SKIP
- **Decision:** Keep pattern focused on 4 topology-specific alphas (no additions from Pass 3)

**Pass 4 (State Distribution Validation):**

**Check 1: States per alpha per view**
- Count states for each alpha in each view:
  - Team Topology Design: 1 state per view ✓
  - Cognitive Load: 1 state per view ✓
  - Team Interaction Mode: 1 state per view ✓
  - Organizational Sensing: 1 state per view ✓
- **Result:** All alphas have exactly 1 state per view (IDEAL - no subdivision needed)

**Check 2: Late-appearing alphas**
- Team Topology Design: Present from View 0 ✓
- Cognitive Load: Present from View 0 ✓
- Team Interaction Mode: Present from View 0 (after Pass 2 backfill) ✓
- Organizational Sensing: Present from View 0 (after Pass 2 backfill) ✓
- **Result:** No late-appearing alphas (Pass 2 backfill resolved them)

**Final Validation:**
- 4 alphas × 5 views = 20 alphaState entries ✓
- No view has >2 states per alpha ✓
- All alphas present from View 0 ✓
- Natural progression across all views ✓
- **PASS - Pattern is complete and well-distributed**

**Quality Gates:**
- ✓ All Phase 1 concerns mapped to alphas
- ✓ All new alphas have contributesTo
- ✓ **Keywords identified (target: 10-20 terms)**
  - ✓ Synonyms, acronyms, abbreviations, search terms
  - ✓ Domain-specific product names and jargon
- ✓ **Terminology aliases identified (target: 3-8 aliases)**
  - ✓ ONE alias per PracticeElement (no duplicates for same element)
  - ✓ Aliases prioritize specialized alphas and instances
  - ✓ Domain canonical terms mapped (not multiple synonyms/acronyms)
  - ✓ Synonyms/acronyms in keywords, not aliases
  - ✓ Rationale provided for each alias
- ✓ **All Phase 1 concern relationships mapped to alpha relatesTo arrays**
- ✓ **relatesTo relationships use directionality pattern (provider perspective)**
- ✓ All baseline references are exact canonical names
- ✓ Tags use orthogonal structure
- ✓ **Alpha-state-activity coverage validated:**
  - ✓ Every alpha state (beyond initial) has ≥1 activity with contributesTo
  - ✓ Gap analysis matrix created showing 100% coverage
  - ✓ Inferred activities documented with rationale (source, parent alpha, or baseline pattern)
  - ✓ Inferred activities have complete properties (contributesTo, worksOn, competencies, narrative)
- ✓ **Pattern completeness validated:**
  - ✓ Each alpha in pattern has state in EVERY PatternView (complete matrix)
  - ✓ Final PatternView includes ALL pattern alphas (no omissions)
  - ✓ States progress logically across views (early → late)
  - ✓ Pattern matrix dimensions: N alphas × M views = N×M total alphaState entries
  - ✓ **State distribution quality (Pass 4):**
    - ✓ No alpha has more than 2 states in a single PatternView (prefer 1)
    - ✓ If 3+ states detected → pattern views subdivided into finer granularity
    - ✓ No alpha suddenly appears late with advanced state
    - ✓ Late-appearing alphas backfilled with progressive states in earlier views
- ✓ Validation checklist completely satisfied

**User Feedback:**
- "Reading analysis report and loading baseline practice..."
- "Identifying terminology aliases for domain alignment..."
- "Mapping N concerns to alphas using redeclaration/specialization framework..."
- "Conducting alpha-state-activity gap analysis..."
- "Evaluating initial states: A null-point, B prepared positions requiring bootstrap activities..."
- "Identified X alpha states requiring activities, Y covered, Z gaps - inferring missing activities..."
- "Gap analysis complete: 100% alpha state coverage achieved (including B bootstrap activities)"
- "Constructing patterns using four-pass approach..."
- "Pass 1: Extracted pattern structure from source (M views, N alphas)"
- "Pass 2: Backfilled missing alpha states for complete matrix"
- "Pass 3: Evaluated related alphas from practice/dependencies"
- "Pass 4: Validated state distribution - detected K alphas with excessive states, subdivided views"
- "Pass 4: Backfilled L late-appearing alphas with progressive states in earlier views"
- "Pattern validation complete: N×M matrix with 1-2 states per alpha per view"
- "Phase 2 complete: Mapping guide generated at practices/<name>/02-mapping-guide.md (includes N aliases, Z inferred activities, complete patterns)"

**CRITICAL: Phase 2 Completion Validation (REQUIRED)**

After generating `02-mapping-guide.md`, IMMEDIATELY validate completeness before proceeding to Phase 3:

```bash
python3 utils/validate-phase-output.py practices/<name>/02-mapping-guide.md --phase 2
```

This checks: 7 required sections exist (Keywords, Terminology Aliases, Alphas, Work Products, Activities, Patterns, Citations), element counts (activities ≥5, work products ≥3, alphas ≥3, patterns ≥1), and extracts competency level names found in the mapping guide. Output is structured JSON with pass/fail per check.

**If competency level names are reported**, validate them against the baseline:
```bash
python3 utils/inspect-practice-json.py <baseline-practice.json> --check competencies
```

**If ANY section is missing or incomplete:**
1. Identify which sections are missing
2. Review Phase 2 prompt requirements
3. Read Phase 1 analysis for content that wasn't mapped
4. Generate missing sections BEFORE proceeding to Phase 3

**If competency level name mismatches found:**
1. Extract valid level names for each competency from baseline
2. Review mapping guide and replace invalid level names with correct baseline names
3. Common fixes:
   - "Advanced" → "Masters" (for most competencies in Platform Adoption Essentials)
   - "Expert" → "Innovating"
   - "Intermediate" → "Applies"
   - "Beginner" or "Novice" → "Basic"

**Common Phase 2 Omissions:**
- **Activities section missing entirely** (CRITICAL - causes Phase 3 JSON to have 0 activities)
- **Work Products section incomplete** (missing new work products beyond baseline)
- Keywords or Terminology Aliases sections empty
- Patterns section with incomplete matrices
- Activities section with only 2-3 activities when Phase 1 identified 10+

**Phase 2 Recovery Actions:**
- If Activities missing: Generate complete Activities section from Phase 1 activities list
- If Work Products incomplete: Generate New Work Products section from Phase 1 work products
- If Patterns incomplete: Apply THREE-PASS pattern construction for complete matrix
- If Keywords/Aliases empty: Review source terminology and apply decision tree

**Post-Assembly Verification Checklist (for methods):**

After assembling method JSON, verify BEFORE full validation:

```bash
python3 utils/inspect-practice-json.py practices/<method-name>/<method-name>.json --check kind,required
```

This checks: `kind: "method"` at root, `kind: "practice"` in each embedded practice, and required root properties (name, description, baselinePracticeName, narratives).

If `kind` is missing, add it using the Edit tool to insert `"kind": "method"` at the root level of the JSON file.

If `narratives` is missing, review Phase 1 analysis for overarching lifecycle and add method narrative.

### Step 3: Phase 3 - JSON Generation

**Objective:** Generate schema-compliant Practice or Method JSON

**APPROACH DECISION:**

- **Single Practice**: Generate JSON directly (one step)
- **Multi-Practice Method (2+ practices)**: Use parallel Agent tool approach + assembly

**Process for Single Practice:**

1. Read `prompts/phase-3-json.md`, mapping guide, schema, effective baseline JSON (from Step 0.5, or user-provided baseline if no dependencies). If the effective baseline has `_aliasContext`, note that all structural references MUST use canonical names.
2. Generate complete practice JSON with **REQUIRED discriminator property**:
   ```json
   {
     "kind": "practice",  // CRITICAL: Required at root level
     "name": "Practice Name",
     "description": "...",
     "baselinePracticeName": "...",  // Inherited from parent practice in parent practice mode
     "practiceDependencyNames": ["..."],  // Only parent practices with actually-referenced unique alphas
     ...
   }
   ```
   - **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice's `baselinePracticeName` (NOT the parent practice name). Set `practiceDependencyNames` using the filtering rule (see "Determining practiceDependencyNames" below).
3. Include aliases array from mapping guide
4. Validate and fix until 0 errors (always validate against the **actual baseline**, not the parent practice)

**Process for Multi-Practice Method:**

**Step 3A: Parallel Practice JSON Generation**

1. **Launch parallel agents** (one per practice) in single message:
   
   ```
   Agent(description="Generate Practice 1 JSON", prompt="...")
   Agent(description="Generate Practice 2 JSON", prompt="...")
   Agent(description="Generate Practice 3 JSON", prompt="...")
   Agent(description="Generate Practice 4 JSON", prompt="...")
   ```

2. **Each agent prompt must include:**
   - File paths: `practices/<method-name>/02-mapping-guide.md` (practice section), `deps/language.schema.json`, `<effective-baseline-path>` (from Step 0.5, or user-provided baseline if no dependencies)
   - **Parent practice mode:** Include in the agent prompt: "Set `baselinePracticeName` to '<inherited baseline name>' (inherited from parent practice). `contributesTo` targets reference parent practice alphas using canonical names. Set `practiceDependencyNames` to ONLY those parent practices whose unique alphas (not in baseline) are actually referenced via `contributesTo` — see 'Determining practiceDependencyNames' section."
   - If the effective baseline has `_aliasContext`, include in the agent prompt: "The baseline uses domain aliases for semantic context. All structural references in the JSON (contributesTo, alphaName, stateName, etc.) MUST use canonical names, not alias names."
   - What to generate: **Practice JSON** (NOT method JSON) - single practice object
   - Output location: `practices/<method-name>/<practice-name>.json`
   - Schema compliance: all required properties (aliases, alphas, activities, work products, **patterns**, etc.)
   - Explicit instruction: "Generate STANDALONE practice JSON, not embedded in method. CRITICAL REQUIREMENTS: (1) MUST include 'kind': 'practice' property at root level (required discriminator). (2) MUST include aliases array from mapping guide terminology section. (3) MUST include patterns array from mapping guide - minimum 1 pattern per practice with 2+ PatternViews showing alpha progression."

3. **Agents run concurrently**, each producing one practice JSON file

**Step 3B: Method Assembly**

4. **After all practice JSONs complete:**
   - Read all 4 practice JSON files
   - **Review Phase 1 analysis** for method-level overarching narrative (e.g., "The Cycle", SDLC mapping, value stream)
   - Create method structure with **REQUIRED kind property AND method narrative**:
     ```json
     {
       "kind": "method",
       "name": "Method Name",
       "description": "...",
       "baselinePracticeName": "Platform Adoption Essentials",  // In parent practice mode: inherited from parent's baselinePracticeName
       "practiceDependencyNames": ["..."],  // In parent practice mode: only parent practices with referenced unique alphas (see "Determining practiceDependencyNames")
       "narratives": [
         {
           "name": "Method Lifecycle Narrative",
           "description": "Overarching journey across all practices",
           "narrativeTypeName": "The Cycle | STAR | Hero's Journey",
           "narrativeContexts": [
             {"seq": 1, "narrativeElementName": "...", "context": "..."},
             ...
           ],
           "citationNames": [...]
         }
       ],
       "tags": {...},
       "citations": [...],
       "practices": [
         <practice-1-json-content>,
         <practice-2-json-content>,
         <practice-3-json-content>,
         <practice-4-json-content>
       ]
     }
     ```
   - **CRITICAL:** Ensure `"kind": "method"` is at root level (required discriminator property)
   - **CRITICAL:** Add method-level narrative from Phase 1 analysis (usually "The Cycle" or similar framework)
   - Merge citations from all practices (deduplicate)
   - **CRITICAL:** Ensure EVERY embedded practice has `"kind": "practice"` - check with: `python3 utils/inspect-practice-json.py <file>.json --check kind`
   - If any practice has `"kind": null`, the individual practice JSON generation omitted it - add it during assembly

**Step 3C: Validation and Fixes**

5. **Pre-validation checks (BEFORE running validator):**
   - ✓ Verify `"kind": "method"` exists at root level
   - ✓ Verify `"kind": "practice"` exists in each embedded practice
   - ✓ Verify `name` and `description` exist at root level
   - ✓ Verify `baselinePracticeName` exists at root level
   - ✓ Verify `practices` array exists and has expected count
   - ✓ **Verify `narratives` array exists with method-level narrative** (from Phase 1 overarching lifecycle)
   - ✓ **Verify `citationNames` match actual citation `name` values** (use exact citation names, not kebab-case IDs)
   
6. **Validate method JSON** (always use the **original user-provided baseline**, not the effective baseline — generated JSON uses canonical names):
   ```bash
   python3 utils/validate-practice-json.py \
     practices/<method-name>/<method-name>.json \
     <original-baseline-practice.json> \
     deps/language.schema.json
   ```

7. **Fix errors:**
   - Schema violations (property names, types)
   - **Missing `kind` property** (add "kind": "method" at root, "kind": "practice" in practices)
   - **Citation name mismatches** (replace kebab-case IDs with exact citation names from citations array)
   - Cross-practice references (if any)
   - Missing properties
   - Iterate until 0 errors

**Critical: Multi-Agent Benefits for Phase 3**
- ✅ Each practice generated independently (no shared token budget)
- ✅ Concurrent execution (4x faster)
- ✅ Simpler prompts (each agent focuses on one practice)
- ✅ Easier debugging (one practice per file initially)
- ✅ Clean assembly step combines everything

**Critical JSON Rules:**

From `deps/language.schema.json`:

- **Discriminator property:** `"kind": "practice"` REQUIRED at root level of every practice JSON (enables type discrimination)
- **Checklist format:** Objects {name, description, seq}, NOT strings
- **Competency references:** {competencyName, competencyLevelName}, NOT {competencyName, level}
- **Persona property:** `competencies`, NOT `requiredCompetencies`
- **Activity competencies:** BOTH `requiredCompetencies` (strings) AND `recommendedCompetencyLevels` (objects)
- **PatternView properties:** `alphaStates` NOT `alphas`, `patternViews` NOT `views`, NO `workProducts`
- **LOD contributesTo:** REQUIRED on every LevelOfDetail
- **Tags structure:** Nested object {domainTags, lifecycleTags, organizationalTags}, NOT flat array

**Quality Gates:**
- ✓ Valid JSON syntax (jq empty passes)
- ✓ **Required discriminator properties (CHECK FIRST, BEFORE schema validation):**
  - ✓ Practice JSON: `"kind": "practice"` at root level
  - ✓ Method JSON: `"kind": "method"` at root level AND `"kind": "practice"` in each practices array element
  - ✓ Verify with: `python3 utils/inspect-practice-json.py <file>.json --check kind`
- ✓ Schema validation: 0 errors
- ✓ Baseline validation: 0 errors
- ✓ Internal integrity: 0 errors
- ✓ All Phase 2 content in JSON
- ✓ No floating alphas
- ✓ **PracticeElement name global uniqueness (CRITICAL - Run BEFORE schema validation):**
  - ✓ **All PracticeElement names MUST be globally unique across the entire practice**
  - ✓ This includes: Alphas, WorkProducts, Activities, Personas, Patterns, PatternViews, ActivitySpaces, Assets
  - ✓ **NO name may appear in more than one element type** (e.g., cannot have both Alpha "Platform Configuration" AND WorkProduct "Platform Configuration")
  - ✓ Verify with: `python3 utils/inspect-practice-json.py <file>.json --check uniqueness`
  - ✓ **If duplicates found:** Rename elements to disambiguate
    - Common pattern: Add element-type suffix to most specific element
    - Example: Alpha "Inference Service Configuration" + WorkProduct "Inference Service Configuration" → rename WorkProduct to "Inference Service Configuration File"
    - Example: Alpha "Platform" + Activity "Platform" → rename Activity to "Build Platform" or "Deploy Platform"
    - Update ALL references to renamed element (alphaName, workProductName, activityName in contributesTo/worksOn/etc.)
- ✓ **Aliases array populated from mapping guide:**
  - ✓ 3-8 aliases (ONE per element, no duplicates)
  - ✓ Aliases prioritize specialized alphas and instances
  - ✓ elementType and name use canonical baseline names
  - ✓ aliasName contains domain-specific canonical term
  - ✓ Aliases NOT used in structural references (alphaName, activitySpaceName, etc.)
- ✓ **Pattern matrix completeness:**
  - ✓ Count pattern dimensions: N alphas appearing across all views
  - ✓ Verify total alphaState entries = N × M (where M = number of PatternViews)
  - ✓ Check final PatternView contains all N alphas
  - ✓ No missing cells in pattern matrix
- ✓ **Competency level names match baseline (CRITICAL - Run BEFORE schema validation):**
  - ✓ **All competencyLevelName values MUST exactly match CompetencyLevel.name from baseline practice**
  - ✓ Validate with: `python3 utils/inspect-practice-json.py <file>.json --baseline <baseline>.json --check competencies`
  - ✓ Common errors: "Advanced" (not in baseline), "Expert" (not in baseline), "Intermediate" (not in baseline)
  - ✓ **If mismatches found:** Fix with: `python3 utils/fix-competency-levels.py <file>.json <baseline>.json --fix`

**User Feedback:**
- "Generating JSON from mapping guide..."
- "Validating competency level names against baseline..."
- "Verifying discriminator property: kind='practice'..."
- "Verifying required properties (name, description, baselinePracticeName)..."
- "Running validation (schema, baseline, integrity)..."
- "Found N errors in category X, applying fixes..."
- "Validation passed! Generated schema-compliant JSON at practices/<name>/<name>.json"

**CRITICAL: Phase 3 Completion Validation (REQUIRED)**

After generating `<name>.json`, IMMEDIATELY validate completeness before reporting success:

```bash
python3 utils/inspect-practice-json.py practices/<name>/<name>.json --baseline <baseline-practice.json>
```

This runs all quality gate checks in a single command:
- **kind**: Discriminator property present (`practice`/`method`); for methods, checks each embedded practice
- **counts**: Element counts meet minimums (alphas ≥3, workProducts ≥3, activities ≥5, patterns ≥1, citations ≥3)
- **uniqueness**: PracticeElement names globally unique across all element types (no name collisions)
- **competencies**: All `competencyLevelName` values match baseline competency levels
- **properties**: Activities have required properties (activitySpaceName, assetNames, contributesTo); alphas have icon assets
- **required**: Root-level required properties present (name, description, baselinePracticeName, narratives)

Output is structured JSON with pass/fail per check and details on failures.

To run a specific check only:
```bash
python3 utils/inspect-practice-json.py practices/<name>/<name>.json --baseline <baseline-practice.json> --check competencies
```

**If validation reveals missing content:**

**CRITICAL ERROR: activities.length = 0**
- Go back to Phase 2 mapping guide
- Read Activities section (should have 5-15 activities)
- Generate activities JSON array from mapping guide
- Insert activities array into JSON
- Re-validate

**CRITICAL ERROR: workProducts.length = 0**
- Go back to Phase 2 mapping guide  
- Read Work Products section
- Generate work products JSON array from mapping guide
- Insert work products array into JSON
- Re-validate

**CRITICAL ERROR: Missing activity properties**
- All activities MUST have: activitySpaceName, focusName, assetNames, contributesTo, worksOn, requiredCompetencies, recommendedCompetencyLevels
- If any missing, regenerate activity objects with complete structure

**CRITICAL ERROR: Alphas missing icon assets**
- Every alpha MUST have at least one icon-type AssetReference
- Add Font Awesome icon AssetReferences to alphas
- Add corresponding font-character Asset definitions to assets array

**CRITICAL ERROR: PracticeElement name collisions**
- The uniqueness check found duplicate names across element types
- Example: Alpha "Platform Configuration" AND WorkProduct "Platform Configuration" (INVALID)
- **Fix procedure:**
  1. Identify which element types share the name (from `inspect-practice-json.py --check uniqueness` output)
  2. Determine which element is most abstract/fundamental (usually Alpha)
  3. Rename the more specific element with disambiguating suffix
     - WorkProducts: Add "File", "Document", "Specification", "Template" suffix
     - Activities: Add verb prefix like "Build", "Deploy", "Configure", "Validate"
     - Patterns: Add "Pattern", "Journey", "Lifecycle" suffix
  4. Update ALL references to renamed element throughout JSON:
     - workProductName in activities.worksOn
     - activityName in various references
     - patternName in references
     - assetName in assetNames arrays
  5. Re-run uniqueness check to verify fix

**CRITICAL ERROR: Invalid competency level names**
- The competency level validation found level names not in baseline practice
- Example: Using "Advanced" when baseline has "Masters", or "Expert" when baseline has "Innovating"
- **Fix procedure:**
  1. Dry run to see invalid levels and suggested replacements:
     ```bash
     python3 utils/fix-competency-levels.py <file>.json <baseline>.json
     ```
  2. Apply fixes (common mappings like "Advanced"→"Masters" are applied automatically):
     ```bash
     python3 utils/fix-competency-levels.py <file>.json <baseline>.json --fix
     ```
     For unmapped levels, provide explicit mappings: `--map "CustomLevel=ValidLevel"`
  3. Re-run competency level validation to verify all names now match baseline:
     ```bash
     python3 utils/inspect-practice-json.py <file>.json --baseline <baseline>.json --check competencies
     ```

**DO NOT report Phase 3 complete until:**
- ✓ activities.length matches Phase 2 Activity count (typically 5-15)
- ✓ workProducts.length matches Phase 2 Work Product count (typically 3-10)  
- ✓ All activities have complete properties (activitySpaceName, assetNames, contributesTo)
- ✓ All alphas have icon AssetReferences
- ✓ Validation passes with 0 errors

---

## Validation Script

**Location:** `utils/validate-practice-json.py`

**Purpose:** Comprehensive validation combining:
1. JSON Schema compliance
2. Baseline practice reference checking
3. Internal cross-reference integrity

**Usage:**
```bash
python3 utils/validate-practice-json.py \
  <practice-or-method.json> \
  <baseline-practice.json> \
  <language-schema.json>
```

**Output:** JSON report with categorized errors:
```json
{
  "valid": false,
  "error_count": 5,
  "summary": {
    "schema": 2,
    "baseline": 2,
    "integrity": 1
  },
  "errors": [
    {
      "category": "schema",
      "severity": "error",
      "path": "alphas[0].states[0].checklist[0]",
      "issue": "Expected object, got string",
      "expected": "{name, description, seq}",
      "actual": "Checklist item",
      "suggestion": "Convert to object format"
    }
  ]
}
```

**Error Categories:**

- **schema:** Property name mismatches, type errors, missing required fields
- **baseline:** Invalid competency/alpha/state references against baseline
- **integrity:** Broken cross-references within practice/method

**Skill Response to Errors:**

Read validation output and apply fixes:

1. **Schema errors:**
   - Correct property names (e.g., `outcomes` → `contributesTo`)
   - Fix data types (e.g., string checklist → object checklist)
   - Add missing required fields (e.g., contributesTo on LODs)

2. **Baseline errors:**
   - Map competency descriptions to exact baseline names
   - Correct state names to match alpha definitions
   - Add contributesTo to floating alphas
   - Use exact case-sensitive baseline references

3. **Integrity errors:**
   - Create missing work products, activities, alphas
   - Fix broken symbolic references
   - Correct cross-practice references (for methods)

**Auto-fixable vs Manual:**

- **Auto-fix:** Schema violations, baseline reference corrections
- **Ask user:** Structural ambiguities, missing elements that need domain knowledge

---

## Key Principles

### Reference-Driven Architecture

This skill does NOT embed knowledge. Instead:

- **Phase 1:** Reads `references/domain-framework.md` for perspectives
- **Phase 2:** Reads `references/semantics.md` for mapping rules
- **Phase 3:** Reads `deps/language.schema.json` for structure
- **All phases:** Use prompts in `prompts/` directory for instructions

**Benefits:**
- Skill stays thin (orchestration only)
- Reference docs are single source of truth
- Updates to semantics don't require skill changes
- Clear separation of concerns

### User-Provided Baseline

The skill does NOT assume a specific baseline practice. Instead:

- User provides baseline practice file path
- Example provided: `deps/platform-adoption-kernel.json`
- Validation script validates against provided baseline
- Works with any baseline following Practice Language schema

**Baseline Dependency Resolution (Step 0.5):**

If the provided baseline declares `baselinePracticeNames` (an array of other baseline names it depends on), the skill resolves the dependency chain:

- Asks user for dependent baseline file paths (there is no practice library/registry)
- Recursively resolves transitive dependencies until root baselines are reached
- Merges baselines in dependency order (root-first, leaf-last overlay)
- Creates `_effective-baseline.json` in the output directory with merged elements
- Surfaces `practiceElementAliases` from child baselines as `_aliasContext` annotations for semantic understanding
- Uses the effective baseline for analysis and mapping phases
- Validation always uses the **original** user-provided baseline (canonical names)

**Alias Context:**

Child baselines often define `practiceElementAliases` that map generic parent terms to domain-specific terminology (e.g., "Platform" → "Automation Platform"). These aliases are surfaced in the effective baseline so agents understand the domain vocabulary during analysis and mapping. Extension practices always use canonical names in structural references — aliases inform semantic reasoning, not JSON output.

**Benefits:**
- Flexibility to use different baselines
- No hardcoded assumptions
- Baseline can evolve independently
- Baseline dependency chains are resolved automatically
- Domain-specific terminology improves semantic quality of analysis and mapping

### Parent Practice Extension Mode

As an alternative to providing a baseline practice, users can provide an existing **practice** or **method** as the mapping target. The skill treats the provided practice/method as a "parent practice" — the new practice extends the parent's alphas rather than mapping directly to the baseline.

**When to use:**
- Creating a practice that builds on top of an existing practice (e.g., a specialized deployment practice extending a general platform engineering practice)
- Creating a practice that extends a method's capabilities (e.g., adding AI inference to an OpenShift method)
- The source methodology is a specialization or extension of content already captured in an existing practice

**How it works:**

1. **Detection:** `utils/resolve-parent-practice.py --check-only` classifies the input as `practiceBaseline`, `practice`, or `method`
2. **Parent Resolution:** For methods, all embedded practices are merged into a composite "effective parent" via name-keyed union
3. **Baseline Inheritance:** The actual baseline is inherited from the parent's `baselinePracticeName`
4. **Mapping:** During analysis and mapping, parent practice alphas are the primary `contributesTo` targets
5. **JSON Output:** The generated practice sets:
   - `baselinePracticeName` = inherited from parent (NOT the parent practice name)
   - `practiceDependencyNames` = only those parent practices whose unique alphas are actually referenced (see "Determining practiceDependencyNames")
   - Alpha `contributesTo` targets = parent practice alphas (or baseline alphas where appropriate)

**Alpha hierarchy:**

```
Baseline Alpha (e.g., "Platform")
  └── Parent Practice Alpha (e.g., "Platform Infrastructure")
       └── New Practice Alpha (e.g., "AI Inference Platform")
           contributesTo: "Platform Infrastructure"  (parent practice alpha)
```

**Canonical names:** All structural references use canonical names. If the parent practice has `practiceElementAliases`, they are surfaced as `_aliasContext` annotations for semantic understanding — they do NOT appear in generated JSON output.

**Worked example:**

```
Input: practices/red-hat-openshift-foundations/red-hat-openshift-foundations.json (method)
  → inputKind: "method"
  → baselinePracticeName: "Platform Adoption Essentials"
  → parentPracticeNames: ["Platform Operations", "Security & Compliance", ...]

Output practice:
  {
    "kind": "practice",
    "name": "OpenShift AI Inference",
    "baselinePracticeName": "Platform Adoption Essentials",  // inherited
    "practiceDependencyNames": ["Observability"],  // ONLY practices with referenced unique alphas
    "alphas": [
      {
        "name": "Inference Endpoint",
        "contributesTo": "Platform"  // baseline alpha — does NOT create a dependency
      },
      {
        "name": "Inference Monitoring",
        "contributesTo": "Observability Stack"  // unique to Observability practice — DOES create dependency
      }
    ]
  }
```

### Determining practiceDependencyNames (Parent Practice Mode)

**Rule:** A practice should only declare a dependency on a parent practice if it actually references an alpha that is **uniquely defined** in that parent practice — i.e., an alpha that exists in the parent but NOT in the effective baseline. Baseline alphas that are merely **redeclared** by a parent practice do NOT create a dependency.

**Algorithm (apply per practice after Phase 3 JSON generation):**

1. **Collect `contributesTo` targets** from all alphas in the practice
2. **Filter out practice-local targets** (alphas defined within the same practice)
3. **For each remaining target**, classify it:
   - **Baseline alpha**: exists in the effective baseline → no dependency created
   - **Parent-only alpha**: exists in the effective parent but NOT in the effective baseline → creates dependency on whichever parent practice defines it
4. **Map parent-only alphas to their owning parent practice** (for methods: check which embedded practice defines the alpha)
5. **Set `practiceDependencyNames`** to the deduplicated list of parent practices that own at least one referenced parent-only alpha. If no parent-only alphas are referenced, set to `[]`.

**Verification command:**
```bash
# Show parent-only alphas and their owning practices
python3 utils/resolve-practice-dependencies.py \
  --parent _effective-parent.json \
  --baseline _effective-baseline.json \
  --parent-method <parent-method.json>

# Also compute dependencies for a specific practice
python3 utils/resolve-practice-dependencies.py \
  --parent _effective-parent.json \
  --baseline _effective-baseline.json \
  --parent-method <parent-method.json> \
  --practice <practice.json>
```

**Why this matters:** Blindly including all parent practice names inflates the dependency graph and creates false coupling. A practice that only contributes to baseline alphas (e.g., "Platform", "Way Of Working") has no structural dependency on the parent practices that redeclare those alphas.

**Example:**
- Practice alpha "AI Model" has `contributesTo: "Platform Asset"` → "Platform Asset" is a baseline alpha → no dependency
- Practice alpha "Inference Monitoring" has `contributesTo: "Observability Stack"` → "Observability Stack" is NOT in baseline, defined in parent's "Observability" practice → dependency on "Observability"
- Result: `practiceDependencyNames: ["Observability"]`

### Clean Three-Phase Structure

Unlike the complex v1 pipeline (Phase 1 → 1.5 → 2 → 2.5 → 2.6 → 2.7 → 2.8), this uses:

**Phase 1: Analysis** (one step)
- Organize methodology into structured analysis
- Output: Single markdown file

**Phase 2: Mapping** (one step)
- Map analysis to baseline using semantics
- Output: Single markdown file

**Phase 3: JSON** (one step with iterative validation)
- Generate JSON, validate, fix, repeat until clean
- Output: Schema-compliant JSON

**Benefits:**
- Easier to understand and explain
- Clear phase boundaries
- Simpler resumption if interrupted

### Programmatic Validation

Single validation script replaces multiple utilities:

**Old approach (v1):**
- fix-property-names.py
- validate-baseline-references.py
- validate-internal-integrity.py
- Manual review and iteration

**New approach (v2):**
- validate-practice-json.py (all-in-one)
- Skill interprets results and applies fixes
- Automated iteration until clean

**Benefits:**
- Single command validates everything
- Structured JSON output for skill consumption
- Clear error categorization and suggestions

---

## Common Pitfalls to Avoid

### General Workflow Pitfalls

- ❌ **Not compacting between phases** (leads to token budget exhaustion and incomplete content)
- ❌ **Generating "example" or partial content** (all activities, alphas, patterns must be complete)
- ❌ Skipping phases or combining them (each phase has distinct purpose)

### Phase 1 Pitfalls
- ❌ Skipping EnterPlanMode
- ❌ Not reading domain-framework.md before analyzing
- ❌ Forcing template patterns instead of discovering source's natural progression
- ❌ Multi-sentence descriptions (violates conciseness standards)
- ❌ Insufficient citations (need 5-15 authoritative sources)
- ❌ **Incomplete activity coverage** (must include ALL activities identified, not just 1-2 examples)
- ❌ **Not identifying concern relationships** - Missing production flows, enablement patterns, governance structures, information flows between concerns
  - **Fix:** Explicitly analyze how concerns interact: what produces what, what enables what, what governs what
  - Document these relationships in concern analysis for Phase 2 mapping

### Phase 2 Pitfalls

- ❌ Not reading semantics.md before mapping
- ❌ Creating floating alphas (missing contributesTo)
- ❌ **Missing or insufficient terminology aliases** - Saying "no aliases needed" when source uses domain-specific vocabulary
  - **Fix:** Review source for domain canonical terms differing from baseline
  - Examples: "Playbook" (vs Deployment Documentation), "Execution Environment" (specialized alpha)
  - Target: 3-8 aliases per practice
  - **ONE alias per element** - if multiple terms exist, use instances/specializations instead
- ❌ **Multiple aliases for same element** - Creating Platform → "AAP", Platform → "Automation Controller", Platform → "Automation Platform"
  - **Fix:** Distinguish synonyms vs facets vs deployments
  - **Synonyms/acronyms** → keywords: "AAP", "automation platform", "ansible automation platform"
  - **Facets/components** → specializations: "Automation Controller", "Automation Hub", "Execution Environment" (new alphas with contributesTo)
  - **Different deployments** → instances: "Production AAP", "Staging AAP", "Development AAP" (same behavior, different tracking)
  - Do NOT create multiple aliases for one baseline element
- ❌ **CRITICAL: contributesTo only references baseline** - Forgetting that contributesTo can reference practice-local alphas (internal hierarchy) or external practice alphas (cross-practice dependency)
  - **Fix:** Consider all three contributesTo options: baseline, practice-local, external practice
  - Use State Alignment Heuristic to find best parent across all three sources
  - Document practice dependencies when using external practice references
- ❌ **Not using baseline relatesTo for alpha analysis** - Ignoring existing semantic relationships when analyzing baseline alphas
  - **Fix:** Read baseline alpha's `relatesTo` array to understand dependencies, production, governance patterns
  - Use relationships to inform how the alpha fits in the practice's value stream
  - Example: "Platform" is "governed by" Platform Governance → include governance activities in practice
- ❌ **Adding relatesTo to redeclarations** - Enriching baseline alphas should NOT add new relationships
  - **Fix:** Only define `relatesTo` on NEW alphas (specializations), not redeclarations
  - Redeclarations inherit baseline relationships automatically
- ❌ **Missing relatesTo on new alphas** - New specialized alphas lack semantic relationships to peer alphas
  - **Fix:** Review Phase 1 concern interactions and map to relatesTo arrays
  - Define domain-specific relationships using appropriate verbs from semantics.md Section 4.1
  - Use directionality pattern: alpha declares what it provides/enables/produces (not what it depends on)
  - Example: New alpha "Platform Capability" should relate to "Platform Asset" (produces), "Requirements" (validates), etc.
- ❌ **Using vague relationship verbs** - Generic "relates to" instead of specific relationship types
  - **Fix:** Use domain-appropriate verbs: "produces", "enables", "guides", "validates", "constrains", "provides", "hosts"
  - Prefer active voice from provider perspective
- ❌ **Wrong relationship directionality** - Alpha declares dependencies instead of provisions
  - **Fix:** Flip perspective - alpha should declare what it provides TO others, not what it needs FROM others
  - "Platform enables Software System" not "Software System depends on Platform"
- ❌ **Using invalid competency level names** - Using descriptive names instead of exact baseline CompetencyLevel.name values
  - **Fix:** Extract valid level names from baseline: `python3 utils/inspect-practice-json.py <baseline>.json --check competencies`
  - Use EXACT level names from baseline (case-sensitive)
  - Common errors: "Advanced" (check baseline), "Expert" (check baseline), "Intermediate" (check baseline)
  - For Platform Adoption Essentials: use "Basic", "Applies", "Masters", "Adapts", "Innovating"
  - **Validate BEFORE Phase 3:** Check all competencyLevelName values in mapping guide against baseline
- ❌ Using competency descriptions instead of exact baseline names
- ❌ Using alias names in structural references (use canonical names)
- ❌ Wrong alpha approach (should use redeclaration vs specialization framework)
- ❌ Flat tags array instead of orthogonal structure
- ❌ **CRITICAL: Writing prose paragraphs instead of structured narrative objects**
- ❌ **Missing narrativeTypeName and narrativeContexts in narratives**
- ❌ **Self-referential narrative content** - Mentioning narrative type/name/framework within contexts
  - **Fix:** Write direct story content without meta-references
  - **WRONG:** "In this Hero's Journey, organizations embark..." or "This narrative explores..."
  - **CORRECT:** "Organizations operate with fragmented infrastructure..." (direct content)
- ❌ **Omitting alpha narratives (required for new alphas)**
- ❌ **Omitting activity narratives (required for all activities)**
- ❌ **Missing alpha-state-activity coverage** - Alpha states lack supporting activities to progress to those states
  - **Fix:** Conduct alpha-state-activity gap analysis (Phase 2 Step 7.5)
  - Every alpha state beyond initial MUST have ≥1 activity with contributesTo
  - Infer missing activities from: (1) source material, (2) parent alpha patterns, (3) baseline ActivitySpace patterns
  - Document gap analysis matrix and inferred activities with rationale
- ❌ **CRITICAL: Degeneration in multi-practice methods** - Practice 1 gets full alpha/work product/activity coverage, but later practices only get activities (missing alphas and work products)
  - **Fix:** Use multi-agent approach (Phase 2 and Phase 3)
  - Each practice MUST have: metadata, alphas (if any), work products, activities, **patterns**
  - Don't skip alpha/work product/pattern sections just because you're on Practice 3 or 4
- ❌ **Missing patterns** - Practices have 2+ alphas but no pattern coordinating them
  - **Fix:** Every multi-alpha practice MUST have at least one pattern
  - Pattern should have 3-5 PatternViews showing how alphas progress together
  - Use external lifecycle narratives (SDLC, PDCA, etc.) when appropriate
- ❌ **Incomplete patterns (sparse matrices)** - Patterns only include alpha states explicitly mentioned in source, resulting in missing cells in pattern matrix
  - **Fix:** Use FOUR-PASS pattern construction (see Pattern Completeness Requirements section):
    - Pass 1: Extract source-driven structure
    - Pass 2: Backfill missing alpha states for complete progression (REQUIRED)
    - Pass 3: Consider related alphas from practice/dependencies (OPTIONAL)
    - Pass 4: State distribution validation (REQUIRED)
  - Every alpha in pattern MUST have state in EVERY PatternView
  - Final PatternView MUST include ALL alphas (even if state unchanged from previous view)
  - Example: Pattern with 4 alphas and 5 views = 20 alphaState entries (4×5 complete matrix)
- ❌ **Too many states per alpha in single PatternView** - Alpha has 3+ states in one view (e.g., Platform: Conceived → Architected → Built in "Design Phase")
  - **Root Cause:** PatternView is too coarse-grained, covering multiple lifecycle phases
  - **Fix:** Subdivide pattern into finer-grained PatternViews
  - **Example:**
    - **Before:** "Implementation" view has Platform: Architected → Built → Deployed (3 states)
    - **After:** Split into "Design" (Architected), "Build" (Built), "Deploy" (Deployed) views
  - **Guideline:** Prefer 1 state per alpha per view, maximum 2
- ❌ **Late-appearing alphas with advanced states** - Alpha suddenly appears in PatternView 3 at state "Achieved" but wasn't in Views 1-2
  - **Root Cause:** Pattern mapping only included explicit mentions from source, missing progressive buildup
  - **Fix:** Backfill earlier PatternViews with progressive states
  - **Example:**
    - **Before:** Platform Governance appears in View 3 with "Compliant" (advanced state)
    - **After:** Backfill View 0: "Undefined", View 1: "Established", View 2: "Enforced", View 3: "Compliant"
  - **Detection:** Review first appearance of each alpha - if not in initial view AND not at initial state, backfill needed
  - **Guideline:** All alphas should appear from View 0 or have clear justification for delayed introduction

### Phase 3 Pitfalls

- ❌ Not reading language.schema.json before generating
- ❌ **PracticeElement name collisions** - CRITICAL ERROR - Using same name for different element types
  - **Problem:** Alpha "Platform Configuration" + WorkProduct "Platform Configuration" = INVALID (names must be globally unique)
  - **Detection:** Run `python3 utils/inspect-practice-json.py <file>.json --check uniqueness`
  - **Fix:** Rename more specific element with disambiguating suffix:
    - WorkProduct collision: Add "File", "Document", "Template" (e.g., "Platform Configuration" → "Platform Configuration File")
    - Activity collision: Add verb prefix (e.g., "Platform" → "Configure Platform")
    - Pattern collision: Add "Pattern", "Journey" (e.g., "Delivery" → "Delivery Journey")
  - **Update references:** Search and replace all references to renamed element (workProductName, activityName, etc.)
  - **Common culprit:** Alphas and WorkProducts sharing names (alpha is usually concept, work product is the artifact)
- ❌ **Missing `kind` property at root level** - MOST COMMON ERROR
  - **Fix Practice JSON:** Add `"kind": "practice"` at root level (conventionally first property for readability)
  - **Fix Method JSON:** Add `"kind": "method"` at root level
  - **Check EVERY practice in method:** `python3 utils/inspect-practice-json.py <file>.json --check kind` - ALL must show "practice", not null
  - This MUST be checked BEFORE schema validation (some schemas allow it to be missing but consumers fail)
  - **Note:** Property order doesn't affect JSON validity, but discriminators are conventionally placed first
- ❌ Checklist items as strings instead of objects
- ❌ **Empty or missing aliases array** - Omitting aliases when mapping guide identified them
  - **Fix:** Copy aliases from "Terminology Aliases" section of mapping guide to JSON aliases array
  - Verify 3-8 entries (ONE per element, no duplicates)
- ❌ **Using aliasName in structural references** - Using domain term instead of canonical name in alphaName, contributesTo, etc.
  - **Fix:** ALL structural references MUST use canonical baseline names
  - Aliases are presentation-layer only (for UI/documentation)
  - Example: Use "Platform" in alphaName, not "Automation Platform" (even if alias exists)
- ❌ **Invalid competency level names in JSON** - Using level names not in baseline practice
  - **Problem:** competencyLevelName values don't match baseline CompetencyLevel.name values
  - **Detection:** `python3 utils/fix-competency-levels.py <file>.json <baseline>.json` (dry run shows invalid levels and suggested replacements)
  - **Fix:** `python3 utils/fix-competency-levels.py <file>.json <baseline>.json --fix`
    - For unmapped levels, provide explicit mappings: `--map "Advanced=Masters" --map "Expert=Innovating"`
    - Common replacements for Platform Adoption Essentials: "Advanced"→"Masters", "Expert"→"Innovating", "Intermediate"→"Applies", "Beginner"→"Basic"
  - **Validate:** `python3 utils/inspect-practice-json.py <file>.json --baseline <baseline>.json --check competencies`
- ❌ Wrong competency reference format ({competencyName, level} instead of {competencyName, competencyLevelName})
- ❌ Using `requiredCompetencies` on personas (should be `competencies`)
- ❌ Missing BOTH `requiredCompetencies` AND `recommendedCompetencyLevels` on activities
- ❌ **Missing `activitySpaceName` property on activities** (required for flat Practice.activities)
- ❌ **Missing `kind` property** (required discriminator for type discrimination)
  - **Fix:** Add `"kind": "practice"` at root level for practice JSON
  - **Fix:** Add `"kind": "method"` at root level for method JSON
  - **Fix:** Ensure each practice in method's practices array has `"kind": "practice"`
  - This is a CRITICAL property - schema validation may pass without it, but consumers will fail
- ❌ Wrong PatternView property names (`alphas` instead of `alphaStates`, `views` instead of `patternViews`)
- ❌ Missing contributesTo on LODs
- ❌ **Adding relatesTo to redeclarations** - JSON includes relatesTo on baseline alpha redeclarations
  - **Fix:** Remove relatesTo from any alpha that is a redeclaration (same name as baseline alpha)
  - Only include relatesTo on NEW alphas (those with contributesTo to baseline)
- ❌ **Invalid alphaName in relatesTo** - Relationship references non-existent alpha
  - **Fix:** Validate every relatesTo.alphaName against defined alphas in baseline and practice
  - Use exact, case-sensitive alpha names
- ❌ **Missing relatesTo on new alphas from mapping guide** - Mapping specifies relationships but JSON omits them
  - **Fix:** Copy relatesTo array from mapping guide to JSON for all new alphas
- ❌ **Wrong relationship directionality** - Declaring dependencies instead of provisions
  - **Fix:** Alpha A should declare what it provides/enables/produces for other alphas, not what it depends on
  - Use active voice from provider perspective: "enables", "produces", "guides" rather than "depends on", "requires"
  - Exception: "depends on" is valid when explicitly modeling a dependency relationship from the dependent's side
- ❌ **Missing relationships on interconnected alphas** - Phase 1 analysis shows concern interactions but Phase 3 JSON has no relatesTo
  - **Fix:** Review Phase 1 concern interactions and Phase 2 mapping for relationship opportunities
  - Look for production flows, enablement patterns, governance structures, information flows
- ❌ Markdown or metadata in JSON strings
- ❌ **Generating only 1-2 example activities** (must generate ALL activities from mapping guide)
- ❌ **Empty patterns array** when mapping guide has patterns
  - **Fix:** Verify patterns array populated with minimum 1 pattern per practice
  - Each pattern must have 2+ PatternViews with alphaStates showing progression
- ❌ **Incomplete pattern matrices in JSON** - Pattern has 4 alphas but some PatternViews only have 2-3 alphaStates
  - **Fix:** Complete the pattern matrix using state progression analysis
  - Count: If pattern has N alphas and M PatternViews, JSON should have N×M alphaState entries total
  - Validate final PatternView includes ALL alphas (mandatory completeness rule)
  - Use alpha state sequences to backfill missing states for each view
- ❌ **Using `assetName` (singular string) instead of `assetNames` (array of AssetReference objects)**
  - **Fix:** Replace `"assetName": "icon-name"` with `"assetNames": [{"assetName": "icon-name", "type": "icon"}]`
- ❌ **Missing AssetReference `type` property**
  - **Fix:** Every AssetReference object must have both `assetName` and `type` properties
  - Valid types: "icon", "illustrative", "template", "diagram"
- ❌ **Alphas/activities without icon AssetReferences**
  - **Fix:** Every alpha and activity MUST have at least one icon-type AssetReference
  - Use Font Awesome 6 Free icons for zero distribution overhead
- ❌ **Referenced assetName not in top-level assets array**
  - **Fix:** Every assetName in AssetReference objects must match an Asset.name in the assets array

---

## Cross-Practice Dependencies and Alpha Hierarchies

### Internal Alpha Hierarchies (Practice-Local)

Practices can create multi-level alpha specialization chains where new alphas contribute to other new alphas within the same practice:

**Example:**

```text
Platform Service → Platform Capability → Platform (baseline)
```

**Requirements:**

- Referenced alpha must be defined EARLIER in the mapping guide
- Referenced alpha must have its own valid contributesTo chain
- Creates hierarchical rollup: child states influence parent progression

**Use When:**

- Building domain-specific maturity models with multiple specialization levels
- Source methodology has nested concern hierarchies
- Need fine-grained tracking at multiple abstraction levels

### External Practice Dependencies (Cross-Practice)

Practices can reference alphas from other practices, creating explicit dependencies:

**Example:**
```json
{
  "name": "Platform Team Topology",
  "contributesTo": "Team Interaction",  // from Team Topologies practice
  "practiceDependencyNames": ["Team Topologies"],
  "dependencies": [
    {
      "practiceName": "Team Topologies",
      "reason": "Extends team interaction patterns for platform context"
    }
  ]
}
```

**Requirements:**

- **Phase 2:** Document dependency in practice metadata section of mapping guide
- **Phase 3:** Add to JSON:
  - `practiceDependencyNames` array: list of practice names providing alphas
  - `dependencies` array with practiceName and reason (detailed explanations)
- External practice must be available for validation (or validation must skip external references)
- Reference must use exact, case-sensitive alpha name from external practice

**Use When:**

- Source methodology builds on concepts from another well-known practice
- Avoiding duplication of alphas already defined elsewhere
- Creating practice compositions (e.g., Platform Engineering practice depends on Team Topologies)
- **Creating orchestration practices** that coordinate activities across multiple practices via patterns

### Orchestration Practice Pattern

**When to Use:**

Source methodology describes an **overarching lifecycle pattern** that cuts across multiple domains/concerns, leading to a temptation to create one very large practice.

**Correct Approach:**

1. **Divide content logically** into separate practices (by domain/concern/focus)
2. **Create a dedicated orchestration practice** that:
   - Describes the overarching lifecycle pattern
   - Uses `practiceDependencyNames` to load alphas from other practices
   - Creates patterns that coordinate across loaded alphas
   - Does NOT redefine alphas already in other practices
   - Focuses on **pattern orchestration**, not alpha definition

**Example:**

**Source:** SAFe methodology with "The Cycle" lifecycle coordinating across multiple value streams

**Wrong Approach:** Create one giant "SAFe" practice with 20+ alphas

**Correct Approach:**
- Practice 1: "Portfolio Management" (defines Portfolio, Epic, Value Stream alphas)
- Practice 2: "Team Delivery" (defines Team, Iteration, Story alphas)
- Practice 3: "Solution Delivery" (defines Solution, Architecture alphas)
- **Practice 4: "SAFe Cycle Orchestration"** (orchestration practice)
  - `practiceDependencyNames: ["Portfolio Management", "Team Delivery", "Solution Delivery"]`
  - Defines 1-2 overarching patterns using alphas from dependencies
  - Pattern views coordinate state progression across all loaded alphas
  - Minimal or no alpha definitions (relies on loaded alphas)

**Validation Considerations:**

1. **During Phase 2 Mapping:**
   - Identify external practice references
   - Read external practice JSON if available to verify alpha exists
   - Document dependency rationale in mapping guide
   - Use State Alignment Heuristic to validate semantic fit
   - **For orchestration practices:** Clearly identify which alphas come from dependencies vs defined locally

2. **During Phase 3 JSON Generation:**
   - Populate `practiceDependencyNames` array with practice names (simple list)
   - Populate `dependencies` array with detailed {practiceName, reason} objects
   - Ensure contributesTo references are exact matches (case-sensitive)
   - Document in practice description or narrative that it extends another practice
   - **For orchestration practices:** Ensure patterns reference alphas from dependencies without redefining them

3. **During Validation:**
   - **If external practice JSON is available:** validate alpha name exists in dependency
   - **If external practice JSON is NOT available:** skip cross-practice alpha validation (allow references via practiceDependencyNames)
   - Check for circular dependencies (Practice A → Practice B → Practice A)
   - **For methods:** Validate cross-practice references across embedded practices

**Multi-Practice Method Considerations:**

When generating a method with multiple practices:

- Practices within the method can reference each other's alphas
- Use `practiceDependencyNames` to declare which practices provide alphas
- Method assembly (Phase 3B) should validate cross-practice references across embedded practices
- Validator should recognize `practiceDependencyNames` and allow alpha references from those practices

---

## Practice vs Method Handling

**CRITICAL: Practice delineation is performed in Step 1.5 (Delineation Gate) by the main agent**, then each Phase 2 subagent independently validates it via Step 0 of `phase-2-mapping.md`.

**Why:** You need baseline practice context to:
- Map Phase 1 concerns to baseline alphas
- Identify primary alpha(s) from baseline alpha coverage
- Use baseline `relatesTo` relationships to determine related alphas
- Make informed practice boundary decisions based on semantic alignment

### When This Decision Happens

**Planning Phase:** Preliminary assessment only
- Note obvious source separations (chapters, domains, use-cases)
- Don't determine primary alphas or practice boundaries

**Phase 1 Analysis:** Extract concerns without boundaries
- Identify all concerns from source material
- Don't map to baseline alphas yet (no baseline context)
- Don't decide practice vs method

**Step 1.5 (Delineation Gate):** **PRACTICE DELINEATION DECISION POINT** ⬅️ **HERE**
- Main agent maps Phase 1 concerns to baseline alphas
- Identify baseline alpha coverage (3-7 alphas? 8+ alphas?)
- Determine primary alpha(s) using source content + baseline relatesTo
- Decide: Single practice OR Method with multiple practices
- Gate decision determines Phase 2 delegation strategy

**Phase 2 Mapping (Step 0 validates):**
- Each Phase 2 subagent independently validates delineation via Step 0 of `phase-2-mapping.md`
- Document Delineation Analysis at top of mapping guide

### Practice (Single Value Stream)

**When:** 
- Source content maps to 3-7 baseline alphas
- ONE clear primary alpha identifiable
- Related alphas cluster around primary (via relatesTo)
- Cohesive value proposition

**Structure:**
- One analysis report (covers entire practice)
- One mapping guide (maps to baseline, documents primary alpha decision)
- One Practice JSON

**Example:** "Team Topologies" - if content focused on Team (primary) + 2-6 related alphas

### Method (Multiple Practices)

**When:** 
- Source content maps to 8+ baseline alphas across multiple focuses
- Multiple potential primary alphas identified
- Natural separation signals from source (use-cases, value-streams, domains)
- Each practice cluster has 3-7 alphas

**Structure:**
- One analysis report (covers all concerns)
- One mapping guide per practice (each documents its primary alpha + related alphas)
- One Method JSON with embedded practices array

**Example:** "AWS Well-Architected Framework" - 6 pillars each with own primary alpha

**CRITICAL: Primary Alpha Focus Strategy (Applied in Phase 2)**

**Core Principle:** Each practice should focus around ONE primary alpha, with secondary coverage of that alpha's directly related alphas (via `relatesTo` relationships). This creates focused, coherent practices with broad coverage of loosely related concerns.

**Step 1: Check for natural separation signals**
- Different use-cases? → Separate practices (each with own primary alpha)
- Different value-streams? → Separate practices
- Different stakeholder journeys? → Separate practices  
- Different capability domains? → Separate practices

**Step 2: If no natural separation evident, identify primary alphas from source content**

Analyze the source material to determine which baseline alphas are central themes:

- What are the main conceptual focuses? (e.g., "platform infrastructure", "team design", "value delivery")
- Which alphas have the most content dedicated to them?
- What are the key outcomes the methodology is trying to achieve?

**For each identified primary alpha:**

1. **Read baseline alpha's `relatesTo` array** to understand its relationships
2. **Include directly related alphas** (1-level deep from primary)
   - Production relationships (produces, generates, creates)
   - Enablement relationships (enables, supports, facilitates)
   - Governance relationships (governed by, constrains, guides)
   - Information flow relationships (provides, informs, validates)
3. **Stop at 1 level** - related alphas' further relationships belong to their own practices
4. **Expected coverage:** 1 primary alpha + 3-6 related alphas = **broad, loosely related coverage**

**Example: Platform-Focused Practice**
```
Primary Alpha: Platform
Related Alphas (from Platform.relatesTo):
├─ built by → Team (include - enablement)
├─ hosts → Platform Asset (include - production)
├─ exposes → Platform Consumption Interface (include - production)
├─ governed by → Platform Governance (include - governance)
└─ requires → Requirements (OPTIONAL - if source has significant requirements content)

Result: Practice covers 4-6 alphas with Platform as coherent center
```

**Example: Team-Focused Practice**
```
Primary Alpha: Team
Related Alphas (from Team.relatesTo):
├─ performs → Work (include - production)
├─ applies → Way Of Working (include - enablement)
├─ manages → Platform Risk And Compliance (include - governance)
└─ built from → Stakeholders (OPTIONAL - if source covers recruitment/formation)

Result: Practice covers 3-5 alphas with Team as coherent center
```

**Step 3: Validate practice coherence**

Each practice should:
- ✓ Have ONE clear primary alpha focus
- ✓ Cover 3-7 alphas total (1 primary + 2-6 related)
- ✓ Show broad coverage of loosely related concerns (not narrow specialization)
- ✓ Have coherent value proposition centered on primary alpha
- ✓ Can be adopted independently
- ✗ NOT be "everything else" catch-all (must have identifiable primary alpha)

**Step 4: Cross-practice coordination**

When practices need coordination:

**Option A: Method-level patterns** (if coordination is simple)
- Define patterns in method JSON that reference multiple practice alphas
- Use `practiceDependencyNames` to load alphas from other practices

**Option B: Orchestration Practice** (if coordination is complex - see Orchestration Exception below)
- Create separate practice focused on coordination
- Lists other practices as dependencies
- Contains primarily: aliases (unifying terminology), patterns (coordinating lifecycle), minimal alphas
- Does NOT redefine alphas from dependent practices
- Focuses on integration, not content duplication

**ORCHESTRATION PRACTICE EXCEPTION:**

**When to Create:** Source methodology describes an overarching lifecycle or coordination framework that ties together multiple domain practices

**Structure:**
- **Primary Focus:** Coordination and integration patterns
- **Dependencies:** Lists all practices it coordinates via `practiceDependencyNames`
- **Content:**
  - **Aliases:** Unifying terminology across dependent practices
  - **Patterns:** Lifecycle patterns referencing alphas from multiple dependent practices
  - **Minimal Alphas:** ONLY if coordination requires new tracking concepts (e.g., "Integration Checkpoint", "Cross-Team Dependency")
  - **NO redeclaration:** Does NOT redefine alphas from dependent practices
- **Example:** SDLC Orchestration practice coordinating Development, Deployment, Operations practices

**Orchestration vs Regular Practice:**
- **Regular Practice:** Primary alpha + related alphas (content-focused)
- **Orchestration Practice:** Dependencies + patterns + aliases (coordination-focused)

**Anti-Pattern:**
- ❌ Orchestration practice with 20+ alphas and no dependencies (should be regular practices)
- ❌ Orchestration practice duplicating content from dependent practices
- ❌ Creating orchestration practice when simple method-level patterns would suffice

**Examples:**

**Example 1: Platform-Focused Practice (CORRECT)**
- **Source:** OpenShift Platform Administration
- **Primary Alpha:** Platform (Solution focus)
- **Related Alphas (from Platform.relatesTo):** 
  - Platform Asset (hosts)
  - Platform Consumption Interface (exposes)
  - Platform Governance (governed by)
  - Team (built by)
- **Total Coverage:** 5 alphas (1 primary + 4 related)
- **Coherence:** All content centers on platform infrastructure with broad coverage of related concerns
- **Decision:** ✓ **Single Practice** - Platform is clear primary, related alphas provide broad loosely-related coverage

**Example 2: Team-Focused Practice (CORRECT)**
- **Source:** Team Topologies
- **Primary Alpha:** Team (Endeavor focus)
- **Related Alphas (from Team.relatesTo):**
  - Work (performs)
  - Way Of Working (applies)
  - Platform (built by relationship reversed - Team builds Platform)
  - Organizational Change (enabled by)
- **Total Coverage:** 5 alphas (1 primary + 4 related)
- **Coherence:** Team design as primary with broad coverage of team context (work, practices, change)
- **Decision:** ✓ **Single Practice** - Team is clear primary, covers loosely-related organizational concerns

**Example 3: Multi-Practice Method (CORRECT)**
- **Source:** SAFe Agile Framework
- **Analysis:** Broad coverage without single primary alpha focus
- **Decision:** Method with 3 focused practices + 1 orchestration practice

  **Practice 1: Portfolio Management** (Value focus)
  - Primary Alpha: Opportunity
  - Related: Platform Value And Economics (justifies), Stakeholders (identified by), Requirements (drives)
  - Coverage: 4 alphas focused on business value and investment
  
  **Practice 2: Solution Delivery** (Solution focus)
  - Primary Alpha: Platform Asset
  - Related: Requirements (addresses), Platform (consumes), Platform Consumption Interface (deployed via)
  - Coverage: 4 alphas focused on solution development
  
  **Practice 3: Agile Team Operations** (Endeavor focus)
  - Primary Alpha: Team
  - Related: Work (performs), Way Of Working (applies), Organizational Change (enabled by)
  - Coverage: 4 alphas focused on team execution
  
  **Practice 4: SAFe Lifecycle Orchestration** (Orchestration)
  - Dependencies: Portfolio Management, Solution Delivery, Agile Team Operations
  - Content: Aliases (SAFe terminology), Patterns (PI Planning cycle coordinating all practices)
  - Minimal Alphas: Only if unique coordination concepts needed
  - NO redeclaration of practice alphas

**Example 4: "Everything Else" Anti-Pattern (INCORRECT)**
- **Source:** Platform Engineering Handbook
- **Attempted Structure:**
  - Practice 1: Platform Infrastructure (Platform primary + Platform Asset, Platform Governance)
  - Practice 2: Platform Adoption (Stakeholders primary + Requirements, Opportunity)
  - Practice 3: Everything Else (Team, Work, Way Of Working, Organizational Change, Platform Consumption Interface, Platform Value And Economics)
  
- **Problem:** Practice 3 has NO clear primary alpha - it's a catch-all for leftover content
- **Fix:** Identify primary alphas for Practice 3 content:
  - Is there significant team/org content? → Create "Team & Organization" practice with Team as primary
  - Is there consumption interface content? → Merge into Practice 1 (Platform.exposes relationship)
  - Is there value/economics content? → Merge into Practice 2 (Opportunity.justifies relationship)

**Example 5: Orchestration Practice (CORRECT)**
- **Source:** DevOps Lifecycle Framework
- **Structure:** Method with 4 practices
  - Development Practice (Platform Asset primary)
  - Deployment Practice (Platform Consumption Interface primary)
  - Operations Practice (Platform primary)
  - **DevOps Orchestration Practice (Orchestration)**
    - Dependencies: Development, Deployment, Operations practices
    - Aliases: "Continuous Delivery" → Deployment workflows, "SRE" → Operations personas
    - Patterns: "DevOps Infinity Loop" pattern coordinating alphas from all 3 dependent practices
    - Minimal Alphas: "Deployment Pipeline" (new coordination concept not in dependents)

**Key Decision Principles:**

1. **Primary Alpha Focus** - Every regular practice MUST have ONE identifiable primary alpha
2. **Broad Loosely-Related Coverage** - Include related alphas (3-7 total) for comprehensive value delivery
3. **1-Level Relationship Depth** - Use `relatesTo` to determine related alphas, stop at 1 level
4. **Avoid Catch-Alls** - If you can't identify a primary alpha, the practice needs restructuring
5. **Orchestration Exception** - Use orchestration practices for cross-practice coordination (aliases, patterns, dependencies)
6. **Independent Value** - Each practice should deliver standalone value when adopted

---

## User Interaction Patterns

### Initial Request

When user provides source materials:

"I'll translate this methodology using a three-phase workflow (Analysis → Mapping → JSON). Let me first analyze the source materials and create an execution plan."

**Then:** EnterPlanMode

### Before Phase 2

Request baseline practice:

"I need the baseline practice file to proceed with Phase 2 mapping. Please provide:
- File path to your baseline practice JSON
- OR: Confirm use of the example at deps/platform-adoption-kernel.json

The baseline defines the standardized framework (alphas, activity spaces, competencies) that your methodology will be mapped to."

### During Phases

Provide brief progress updates:
- "Phase 1: Analyzing source using four-perspective framework..."
- "Phase 2: Mapping concerns to alphas using semantic guidance..."
- "Phase 3: Generating JSON and running validation..."

### After Validation Errors

Report findings and fixes:
- "Validation found 5 schema errors, 3 baseline mismatches. Applying fixes..."
- "Re-running validation... 0 errors. JSON is schema-compliant!"

### Final Output

Report completion with file paths:

"Translation complete! Generated files:
 ✓ practices/<name>/01-analysis-report.md (~40K words)
 ✓ practices/<name>/02-mapping-guide.md (~50K words)
 ✓ practices/<name>/<name>.json (schema-compliant)

Validation summary:
 ✓ Schema compliance: PASS
 ✓ Baseline references: PASS
 ✓ Internal integrity: PASS

JSON is ready for use in Practice Language consuming systems."

---

## Troubleshooting

### If Phase 1 fails:
- Check that domain-framework.md is accessible
- Verify source materials are readable
- Ensure sufficient context for large documents
- Review for extremely complex methodologies (may need chunking)

### If Phase 2 fails:
- Verify baseline practice file exists and is valid JSON
- Check that semantics.md is accessible
- Review for missing content in Phase 1 analysis
- Ensure mapping decisions follow semantic guidance

### If Phase 3 validation fails repeatedly:
- Re-read schema.json to understand exact structure
- Check validation error suggestions carefully
- Review common schema violations in phase-3-json.md prompt
- Consider regenerating problematic sections from Phase 2 mapping

### If validation script errors:
- Ensure Python 3.8+ installed
- Install jsonschema: `pip install jsonschema`
- Check file paths are correct (absolute or relative to working directory)
- Verify all three files (practice, baseline, schema) are valid JSON

---

## Final Deliverables

For successful translation, user receives:

1. **`practices/<name>/01-analysis-report.md`**
   - Complete structured analysis (~30-50K words)
   - Human-readable, organized by perspectives

2. **`practices/<name>/02-mapping-guide.md`**
   - Complete mapping specification (~40-60K words)
   - Human-readable, ready for review
   - Includes assets section identifying visual artifacts

3. **`practices/<name>/<name>.json`**
   - Schema-compliant Practice or Method JSON
   - Validated against schema, baseline, internal integrity
   - Ready for consumption by Practice Language tools
   - Includes `assets` array if visual artifacts identified

4. **`practices/<name>/assets/`** (optional, if visual artifacts present)
   - Diagrams, templates, charts extracted from source materials
   - Organized by type: diagrams/, templates/, icons/
   - Referenced by JSON via relative paths

### Asset References and Visual Enhancement

**Asset Strategy:**

Visual assets enhance practice comprehension and adoption. The Practice Language supports flexible asset references prioritizing externally-referenceable assets (URLs, font characters) over bundled files.

**Asset Type Priority (Descending):**

1. **Font Characters** - Icon fonts (Font Awesome, Material Icons, etc.)
   - Zero distribution overhead
   - Universally accessible
   - Scalable and accessible
   - USE FOR: Icons, simple visual markers, UI elements

2. **External URLs** - Direct links to hosted resources
   - No bundling required
   - Single source of truth
   - Easy updates
   - USE FOR: Official diagrams, methodology documentation, templates, reference architectures

3. **Bundled Files** - Assets included with practice
   - Full control over content
   - Offline availability
   - Requires file management
   - USE FOR: Custom diagrams, practice-specific visualizations when no external URL available

**Asset Workflow:**

**Phase 2 (Mapping)**: Identify and catalog visual artifacts

Document in a dedicated "Assets" section of the mapping guide using the new AssetReference structure:

```markdown
## Assets

### Icons and Visual Markers (REQUIRED - Minimum Coverage)

**CRITICAL: All alphas, activities, and pattern views MUST have icon asset references.**

Icons use web fonts (Font Awesome 6 Free, Material Icons) for zero distribution overhead and universal accessibility.

#### Practice-Level Icons

- **practice-icon**: Main practice icon
  - Asset Type (top-level): font-character
  - Reference Type: icon
  - Font: Font Awesome 6 Free
  - Character: fa-server (or fa-cloud, fa-network-wired, etc.)
  - Usage: Practice visual identity

#### Alpha Icons (REQUIRED for ALL alphas)

- **platform-icon**: Platform alpha icon
  - Asset Type (top-level): font-character
  - Reference Type: icon
  - Font: Font Awesome 6 Free
  - Character: fa-cubes
  - Usage: Platform alpha UI marker

- **team-icon**: Team alpha icon
  - Asset Type (top-level): font-character
  - Reference Type: icon
  - Font: Font Awesome 6 Free
  - Character: fa-users
  - Usage: Team alpha UI marker

[Additional alpha icons for each alpha in practice...]

#### Activity Icons (REQUIRED for ALL activities)

- **design-activity-icon**: Design activity type icon
  - Asset Type (top-level): font-character
  - Reference Type: icon
  - Font: Font Awesome 6 Free
  - Character: fa-pencil-ruler
  - Usage: Design activities UI marker

- **implement-activity-icon**: Implementation activity type icon
  - Asset Type (top-level): font-character
  - Reference Type: icon
  - Font: Font Awesome 6 Free
  - Character: fa-code
  - Usage: Implementation activities UI marker

[Additional activity type icons for each activity space/type...]

#### Pattern View Icons (RECOMMENDED)

- **pattern-view-1-icon**: First pattern view icon
  - Asset Type (top-level): font-character
  - Reference Type: icon
  - Font: Font Awesome 6 Free
  - Character: fa-1
  - Usage: Pattern view 1 visual marker

[Additional pattern view icons...]

### Diagrams and Architecture (OPTIONAL - Illustrative)

- **reference-architecture**: Official AWS/Azure/GCP reference architecture
  - Asset Type (top-level): diagram
  - Reference Type: illustrative
  - URL: https://docs.aws.amazon.com/wellarchitected/latest/framework/images/architecture.png
  - Description: Multi-region reference architecture
  - Usage: Architecture alpha, Design activities

- **state-progression-diagram**: Alpha state progression visualization
  - Asset Type (top-level): diagram
  - Reference Type: diagram
  - URL: https://methodology-site.com/diagrams/states.svg
  - Description: Visual representation of Platform alpha states
  - Usage: Platform alpha

### Templates and Documents (OPTIONAL)

- **adr-template**: Architecture Decision Record template
  - Asset Type (top-level): template
  - Reference Type: template
  - URL: https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/templates/decision-record-template-by-michael-nygard/index.md
  - Description: Standard ADR template
  - Usage: Architecture Design activity
```

**Guidelines for Asset Identification:**

**REQUIRED - Icon Coverage (Phase 2 Mandatory):**

1. **All Alphas** - Every alpha MUST have at least one icon-type AssetReference
   - Choose semantic Font Awesome or Material Icons icons
   - Use domain-appropriate icons (see Common Font Awesome Icons table below)
   - Icons provide visual identity in UI/tooling

2. **All Activities** - Every activity MUST have at least one icon-type AssetReference
   - Group activities by type and assign consistent icons
   - Common patterns: design (fa-pencil-ruler), implementation (fa-code), operations (fa-gears), governance (fa-shield-halved)

3. **Pattern Views** - RECOMMENDED to have icon-type AssetReferences
   - Sequential icons (fa-1, fa-2, fa-3) or lifecycle stage icons
   - Helps distinguish views in pattern matrices

**OPTIONAL - Illustrative/Diagram/Template Coverage:**

- **Official Resources**: Link directly to authoritative methodology diagrams, templates, reference architectures
- **Source Materials**: Reference diagrams/images from methodology websites using direct URLs
- **Custom Diagrams**: Only create bundled assets when no suitable external resource exists

**Phase 3 (JSON Generation)**: Populate assets array and assetNames properties with AssetReference objects

**CRITICAL: Use assetNames (plural) array, NOT assetName (singular) string.**

**Priority 1 - Font Character Icons (REQUIRED for all alphas/activities):**

```json
{
  "alphas": [
    {
      "name": "Platform",
      "description": "Platform infrastructure capability",
      "assetNames": [
        {
          "assetName": "platform-icon",
          "type": "icon"
        }
      ],
      "states": [...]
    }
  ],
  "activities": [
    {
      "name": "Design Platform Architecture",
      "description": "Create technical architecture",
      "assetNames": [
        {
          "assetName": "design-activity-icon",
          "type": "icon"
        }
      ],
      "activitySpaceName": "Architecture Design",
      "focusName": "Solution",
      "worksOn": [...],
      "requiredCompetencies": [...]
    }
  ],
  "assets": [
    {
      "name": "platform-icon",
      "description": "Platform infrastructure icon",
      "type": "font-character",
      "fontFamily": "Font Awesome 6 Free",
      "fontCharacter": "fa-cubes",
      "fontWeight": "900"
    },
    {
      "name": "design-activity-icon",
      "description": "Design activity type icon",
      "type": "font-character",
      "fontFamily": "Font Awesome 6 Free",
      "fontCharacter": "fa-pencil-ruler",
      "fontWeight": "900"
    }
  ]
}
```

**Common Font Awesome Icons for Practice Elements:**

- Platform/Infrastructure: `fa-cubes`, `fa-server`, `fa-cloud`
- Team/People: `fa-users`, `fa-user-group`, `fa-people-group`
- Security: `fa-shield-halved`, `fa-lock`, `fa-key`
- Architecture: `fa-sitemap`, `fa-diagram-project`, `fa-network-wired`
- Development: `fa-code`, `fa-laptop-code`, `fa-terminal`
- Operations: `fa-gears`, `fa-wrench`, `fa-gauge`
- Strategy: `fa-compass`, `fa-map`, `fa-lightbulb`
- Requirements: `fa-list-check`, `fa-clipboard-list`, `fa-file-lines`
- Value: `fa-dollar-sign`, `fa-chart-line`, `fa-rocket`

**Priority 2 - External URL References (OPTIONAL - illustrative/diagram/template types):**

```json
{
  "alphas": [
    {
      "name": "Platform",
      "description": "Platform infrastructure capability",
      "assetNames": [
        {
          "assetName": "platform-icon",
          "type": "icon"
        },
        {
          "assetName": "platform-states-diagram",
          "type": "diagram"
        }
      ],
      "states": [...]
    }
  ],
  "activities": [
    {
      "name": "Design Reference Architecture",
      "description": "Create multi-region architecture",
      "assetNames": [
        {
          "assetName": "design-activity-icon",
          "type": "icon"
        },
        {
          "assetName": "aws-ref-arch",
          "type": "illustrative"
        },
        {
          "assetName": "adr-template",
          "type": "template"
        }
      ],
      "activitySpaceName": "Architecture Design",
      "focusName": "Solution",
      "worksOn": [...],
      "requiredCompetencies": [...]
    }
  ],
  "assets": [
    {
      "name": "platform-icon",
      "description": "Platform infrastructure icon",
      "type": "font-character",
      "fontFamily": "Font Awesome 6 Free",
      "fontCharacter": "fa-cubes",
      "fontWeight": "900"
    },
    {
      "name": "design-activity-icon",
      "description": "Design activity type icon",
      "type": "font-character",
      "fontFamily": "Font Awesome 6 Free",
      "fontCharacter": "fa-pencil-ruler",
      "fontWeight": "900"
    },
    {
      "name": "platform-states-diagram",
      "description": "Platform alpha state progression diagram",
      "type": "diagram",
      "url": "https://example.com/methodology/platform-states.svg"
    },
    {
      "name": "aws-ref-arch",
      "description": "AWS Well-Architected multi-region reference architecture",
      "type": "diagram",
      "url": "https://docs.aws.amazon.com/wellarchitected/latest/framework/images/multi-region-arch.png"
    },
    {
      "name": "adr-template",
      "description": "Architecture Decision Record template by Michael Nygard",
      "type": "template",
      "url": "https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/templates/decision-record-template-by-michael-nygard/index.md"
    }
  ]
}
```

**Priority 3 - Bundled Files (Only When Necessary):**

```json
{
  "assets": [
    {
      "name": "custom-pattern-diagram",
      "description": "Practice-specific pattern orchestration diagram",
      "type": "diagram",
      "path": "assets/diagrams/pattern-lifecycle.svg",
      "mimeType": "image/svg+xml"
    }
  ]
}
```

**Asset Assignment Guidelines:**

- **Practice**: Main practice icon (font character preferred)
- **Method**: Method-level icon or logo (font character or URL)
- **Alphas**: 
  - Icons for UI representation (font characters)
  - State diagrams for documentation (URLs to methodology sites)
- **Activities**: 
  - Activity type icons (font characters: fa-code, fa-gears, fa-clipboard)
  - Reference diagrams (URLs to official docs)
  - Templates (URLs to GitHub, official sites)
- **Competencies**: Skill area icons (font characters)
- **Patterns**: Workflow diagrams (URLs or bundled if custom)

**Asset Schema Properties:**

```json
{
  "name": "unique-asset-identifier",
  "description": "Human-readable description of asset purpose",
  "type": "icon | diagram | template | image | font-character",
  
  // Font character assets (Priority 1)
  "fontFamily": "Font Awesome 6 Free | Material Icons",
  "fontCharacter": "fa-icon-name | unicode-char | css-class",
  "fontWeight": "400 | 900 | bold",
  
  // External URL assets (Priority 2)
  "url": "https://example.com/diagram.png",
  
  // Bundled file assets (Priority 3)
  "path": "assets/diagrams/custom.svg",
  "mimeType": "image/svg+xml | image/png | application/pdf",
  "checksum": "sha256:abc123..." // Optional, for integrity verification
}
```

**Validation During Phase 3:**

- [ ] **CRITICAL**: Using `assetNames` (plural array), NOT `assetName` (singular string)
- [ ] **CRITICAL**: Each AssetReference has both `assetName` and `type` properties
- [ ] **CRITICAL**: Every alpha has at least one icon-type AssetReference
- [ ] **CRITICAL**: Every activity has at least one icon-type AssetReference
- [ ] All icon assets use font-character type (Font Awesome/Material Icons)
- [ ] Icon AssetReferences have `type: "icon"`
- [ ] Diagram AssetReferences have `type: "diagram"` or `type: "illustrative"`
- [ ] Template AssetReferences have `type: "template"`
- [ ] External diagrams/templates use direct URLs to authoritative sources
- [ ] Bundled assets only used when no external alternative exists
- [ ] Asset descriptions clearly explain purpose and context
- [ ] URLs point to stable, long-lived resources (official docs, GitHub, methodology sites)
- [ ] All referenced assetName values exist in top-level assets array

### Using Delivered Artifacts

Users can:

- Review and edit phase outputs
- Regenerate specific phases if source changes
- Use analysis and mapping as methodology documentation
- Use JSON in tooling that consumes Practice Language
- Share JSON with teams and tools without bundling assets
- Font character icons render automatically with icon font libraries
- External URLs fetch latest versions from authoritative sources
- Bundled assets only needed for custom/proprietary visualizations

---

## Success Metrics

A successful translation achieves:

1. ✓ All three phases complete without errors
2. ✓ Validation passes with 0 schema violations
3. ✓ Validation passes with 0 baseline reference errors
4. ✓ Validation passes with 0 internal integrity errors
5. ✓ All source methodology content mapped (no omissions)
6. ✓ Clear traceability from source → analysis → mapping → JSON
7. ✓ JSON is well-formatted, readable, and usable

Quality indicators:
- Rich narratives with citations (not sparse)
- Complete checklists (5-7 per state, 3-5 per LOD)
- Exact baseline references (case-sensitive matches)
- No floating alphas (all new alphas have contributesTo)
- Orthogonal tags throughout
- Single-sentence descriptions
