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

2. **Identify context sources (baselines, practices, methods, .keleo bundles):**
   - Ask user which baseline, parent practice/method, or `.keleo` bundle(s) to use
   - User can provide **file paths** (`.json` or `.keleo`), **names**, or a mix
   - **Auto-discover by name:** If user provides a name (no `/`, doesn't end in `.json`/`.keleo`), resolve it:
     ```bash
     python3 utils/discover-dependencies.py --resolve "Name Provided By User"
     ```
     - `found` → use the resolved path
     - `ambiguous` → present candidates to user, let them choose (filesystem entries preferred over bundle copies)
     - `not_found` → ask user for the file path
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
     - Multiple distinct use-cases mentioned? (e.g., greenfield vs brownfield)
     - Different stakeholder journeys? (e.g., builders vs consumers)
     - Clearly separate capability domains? (e.g., security chapter + deployment chapter)
   - **If obvious separation:** Plan for method with multiple practices
   - **If unified framework:** Plan for single practice (subject to Phase 2 validation)
   - **Key principle:** Don't determine primary alphas or practice boundaries yet - you need baseline context first

4. **Reference strategy (present to user):**
   - Estimate reference yield from source materials — how many templates, case studies, reference architectures, or sample artifacts are likely to emerge?
   - Recommend whether secondary reference research (Step 2.5) is warranted:
     - **Few candidates** (0-2 from source) → recommend secondary research
     - **Moderate candidates** (3-5 from source) → optional, user decides
     - **Many candidates** (6+) → recommend skipping secondary research
   - Types of references expected (templates, case studies, architectures, tools)
   - Note: References are only generated for practices (not baselines)

5. **Plan execution:**
   - Tentative practice/method name (kebab-case)
   - Phase execution sequence
   - Expected complexity and size
   - Potential challenges
   - Whether secondary reference research (Step 2.5) will be performed
   - **Note:** Practice boundaries will be finalized in Step 1.5 (Delineation Gate) before Phase 2 delegation

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
   The `_provenance.tiers.baselines` array in the output shows which baselines were merged. For **validation** (running `validate-practice-json.py`), always use the **leaf baseline file** (the most specific baseline in the chain) — canonical names in the generated JSON must match the actual baseline, not the effective context annotations.
   
   Record:
   - `effectiveContextPath` = `<output-dir>/_effective-context.json`
   - `validationBaselinePath` = path to the leaf baseline JSON (for validation only)

4. **How the mapping agent uses `_contributingPracticeName`:**
   - **Baseline elements** (`_contributingPracticeName` points to a name in `_provenance.tiers.baselines`): These are ontology-level concepts. The new practice can redeclare them (add practice-specific checklists/narratives) or specialize them (`contributesTo` / `mapsTo`).
   - **Practice elements** (`_contributingPracticeName` points to a name in `_provenance.tiers.practices`): These came from parent practices. `contributesTo`/`mapsTo` targets that point to these elements create `practiceDependencyNames` entries.
   - **Method elements** (`_contributingPracticeName` points to a name in `_provenance.tiers.methods`): Coordination-level concepts from the parent method.

**User Feedback:**
- "Context resolution complete: N baselines, M practices, K methods merged"
- "Merge order: [list of names in merge order]"
- "Effective context: N alphas, M activitySpaces, K competencies"
- "Using _effective-context.json for analysis/mapping. Leaf baseline '<name>' for validation."

**CRITICAL:** All structural references in the generated JSON (`contributesTo`, `alphaName`, `stateName`, etc.) MUST use canonical names. If the effective context has `_aliasContext`, aliases inform semantic understanding only — they do NOT appear in generated JSON output.

**CRITICAL:** If the context resolution fails (unresolved dependencies, missing files), STOP and discuss alternatives. Do NOT proceed with an incomplete context.

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

**For ALL translations (single-practice AND multi-practice):**
- **ALWAYS use Agent tool** for Phase 1, Phase 2, and Phase 3
- Each agent is self-contained with complete prompt and file paths
- Benefits: isolated token budget per phase, no context window pressure, consistent quality
- The main agent handles Step 0 (planning), Step 0.5 (context resolution), and Step 1.5 (delineation gate)
- Phases 1, 2, and 3 are delegated to agents

**For Multi-Practice methods (2+ practices):**
- **Phase 2 and Phase 3:** Launch parallel agents (one per practice)
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

**Phase 1 Validation:**

```bash
python3 utils/eval-skill-output.py practices/<name>/ --phase 1 --summary
```

Fix any FAIL assertions before proceeding to Step 1.5. If sections are missing, re-read source materials and generate missing content.

**User Feedback:** Brief progress updates

- "Analyzing source materials using four-perspective framework..."
- "Extracted N concerns across M perspectives..."
- "Phase 1 complete: Analysis report generated at practices/<name>/01-analysis-report.md"

### Step 1.5: Practice Delineation Gate (Main Agent Only)

**Objective:** Determine practice structure BEFORE delegating Phase 2 mapping.

**CRITICAL:** This step MUST be performed by the main agent, not delegated to subagents. The delegation strategy (single agent vs parallel agents) depends on this step's outcome. Phase 2 subagents will independently validate this decision via Step 0 of `phase-2-mapping.md`.

**Process:**

1. **Load baseline practice JSON** (use effective baseline from Step 0.5 if dependencies were resolved, otherwise use the user-provided baseline directly):
   ```bash
   python3 utils/extract-reference-names.py <effective-context-or-baseline.json> --sections focuses alphas activitySpaces competencies narrativeTypes --alpha-details
   ```
   This shows all structural elements: focuses, alphas (with states, contributesTo, relatesTo), activitySpaces, competencies (with levels), and narrativeTypes (with elements).
   
   If the effective baseline has `_aliasContext`, review domain aliases to understand the baseline's domain-specific terminology. Use canonical names for structural decisions, but let domain aliases inform your semantic understanding of each alpha's role.

   **Parent Practice Mode:** The effective context already contains merged baselines AND parent practices. Use `_contributingPracticeName` on each element to distinguish baseline-level alphas (ontology context) from practice-level alphas (primary mapping targets). Cross-reference with `_provenance.tiers` to classify each source.
   
   **IMPORTANT:** Never use inline `python3 -c` scripts to inspect JSON structure. Use `extract-reference-names.py` with appropriate `--sections` and detail flags (`--alpha-details`, `--citation-details`, `--activity-details`, `--narrative-details`).

2. **Map Phase 1 concerns to alphas:**
   
   **Standard baseline mode:**
   - Which baseline alphas does the content enrich (redeclarations)?
   - Which baseline alphas need specialization (new alphas with `contributesTo`) or variant mapping (new alphas with `mapsTo`)?
   - Count total baseline alpha coverage (both redeclarations + contributesTo/mapsTo targets)
   
   **Parent practice mode:**
   - Which **parent practice** alphas does the content enrich (redeclarations of parent practice alphas)?
   - Which **parent practice** alphas need further specialization or variant mapping (new alphas with `contributesTo` or `mapsTo` pointing to parent practice alphas)?
   - Which **baseline** alphas are directly relevant but NOT already covered by the parent practice? (these can still be redeclared, specialized, or variant-mapped directly)
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

1. Read `prompts/phase-2-mapping.md`, analysis report, effective context JSON (`_effective-context.json` from Step 0.5), semantics.md
   - The effective context contains ALL merged elements (baselines + parent practices + methods) with `_contributingPracticeName` on each element. Use `_provenance.tiers` to distinguish baseline elements (ontology context) from practice elements (primary `contributesTo`/`mapsTo` targets). If the context has `_aliasContext`, use aliases for semantic understanding but always use canonical names in structural references.
2. **Document primary alpha decision** at top of mapping guide (Delineation Analysis section)
   - **Parent practice mode:** Document which parent practice alphas are being extended and which (if any) baseline alphas are being addressed directly.
3. Map concerns to alphas (redeclaration vs specialization vs variant mapping)
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
   - Include required `direction` field on every relatesTo entry (`outgoing`, `incoming`, or `mutual`)
   - Document relationships in mapping guide
5. **Generate patterns using FOUR-PASS construction:**
   - Pass 1: Extract pattern structure from source (phases, explicitly mentioned states)
   - Pass 2: Backfill missing alpha states for complete matrix (REQUIRED)
   - Pass 3: Consider related alphas from practice/dependencies (OPTIONAL)
   - Pass 4: State distribution validation (REQUIRED - max 2 states per alpha per view, backfill late-appearing alphas)
6. Generate complete `02-mapping-guide.md` with terminology aliases, all alphas (including relatesTo), work products, activities, complete patterns

**CRITICAL: Mapping Guide Element Heading Format**

The eval validator (`validate-phase-output.py`) parses the mapping guide to count elements. Use these heading formats for elements so validation passes:

```markdown
#### Alpha: Name (Type -- Enrichment Level)
#### Work Product: Name
#### Activity: Name
#### Pattern: Name
```

Acceptable heading levels: `###`, `####`, or `#####`. The key format is `<heading> <ElementType>: <Name>`. Bold format also works: `**Alpha: Name**`. Do NOT use other formats like `#### Name` without the element type prefix.

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
   - File paths to read: `practices/<method-name>/01-analysis-report.md` (practice-specific section), `<effective-context-path>` (from Step 0.5), `references/semantics.md`, `prompts/phase-2-mapping.md`
   - Add to agent prompt: "The effective context contains ALL merged elements (baselines + parent practices) with `_contributingPracticeName` on each element. Use `_provenance.tiers` to distinguish baseline elements from practice elements. Practice-level alphas are your primary `contributesTo`/`mapsTo` targets. Baseline-level alphas provide ontology context. Use canonical names for all structural references. Use `contributesTo` for specializations (different states) and `mapsTo` for variant mappings (exact same states, IS-A semantics). IMPORTANT: `practiceDependencyNames` must only include parent practices whose unique alphas (those NOT contributed by baselines per `_contributingPracticeName`) are actually referenced via `contributesTo` or `mapsTo`."
   - If the effective context has `_aliasContext`, include in the agent prompt: "The context includes domain-specific aliases (e.g., 'Platform' is known as 'Automation Platform' in this domain). Use domain terms for semantic understanding but always use canonical names in structural references."
   - What to generate: Complete practice mapping with metadata, terminology aliases, alphas (with relatesTo), work products, activities, patterns
   - Output location: Write to `practices/<method-name>/02-mapping-guide-practice-N.md` OR append to shared file with clear section markers
   - Explicit instruction: "Generate COMPLETE mapping including: (0) Delineation Analysis section validating your practice boundaries; (1) Keywords section with 10-20 domain terms/acronyms; (2) Terminology Aliases section identifying 3-8 domain canonical terms (ONE alias per element - use keywords for synonyms/acronyms, use instances for multiple variants); (3) Alphas (if any) WITH relatesTo relationships (include relationshipKind where applicable); (4) Work products (include contributesToAlphaNames where applicable); (5) Activities (include ledBy where source identifies clear single-person accountability); (6) PATTERNS with complete matrix coverage; (7) PATTERN GROUPS if practice has 3+ patterns — load baseline patternGroups first and assign patterns to existing baseline groups before creating new ones (novel groups require justification); include narratives when source material supports rationale for the grouping. CRITICAL: Map concern interactions from Phase 1 to alpha relatesTo arrays using directionality pattern. Every practice MUST have at least ONE pattern coordinating multiple alphas/concerns (see semantics.md Section 8.1.1)."

3. **After all agents complete:**
   - **Assemble mapping guides** (REQUIRED — never use heredocs, cat, or shell loops):
     ```bash
     python3 utils/assemble-mapping-guide.py \
       --name "<method-name>" \
       --baseline-name "<baseline-name>" \
       --parent-name "<parent-name>" \
       --guides practices/<method-name>/02-mapping-guide-practice-1.md \
                practices/<method-name>/02-mapping-guide-practice-2.md \
                ... \
       -o practices/<method-name>/02-mapping-guide.md \
       --stats
     ```
   - **Validate pattern views** in each practice guide:
     ```bash
     python3 utils/validate-phase-output.py --phase 2 --validate-patterns \
       practices/<method-name>/02-mapping-guide-practice-N.md
     ```
   - Validate completeness: every practice has alphas + work products + activities

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
  - New alpha with `contributesTo` pointing to parent (different states/lifecycle)
  - OR new alpha with `mapsTo` pointing to parent (same states, IS-A variant)
  - Example (contributesTo): Automation Controller, Execution Environment are specialized facets of Platform with unique lifecycles
  - Example (mapsTo): "AI-Ready Enterprise" IS a "Sales Play" — same states, domain-specific checklists
  - **mapsTo naming convention:** Do NOT repeat the parent type name in the variant alpha name. Since `mapsTo` reads as "is a type of", including the type is redundant (e.g., "AI-Ready Enterprise" not "AI-Ready Enterprise Play"; "Container Management" not "Container Management TDP"). This convention applies to both the alpha `name` and any `aliasName`. It does NOT apply to `contributesTo` alphas, where including the type helps distinguish the specialized concept.
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

**CRITICAL RULE: No Alias Collisions with Dependencies**
- **Do NOT re-declare aliases from parent/dependency practices** — they are inherited through `practiceDependencyNames` and will be merged automatically
- **Do NOT reuse an alias name from a dependency for a different target** — this creates ambiguity on merge (validator flags as error)
- When creating aliases for **mapsTo variant alphas**, differentiate the alias name from any parent alias for the mapped-to alpha. Prefix with the practice's domain qualifier (e.g., "RHEL Deal Registration" instead of "Deal Registration" when the parent already aliases "Deal Registration" → "Partner Deal Opportunity")
- **Only create aliases for elements this practice defines or redefines** — not for inherited elements

**CRITICAL RULE: Strict Alias Isolation**
- Aliases are PRESENTATION-LAYER ONLY
- **NEVER use aliasName in structural references** (alphaName, activitySpaceName, contributesTo, etc.)
- ALL structural references MUST use canonical baseline names
- Aliases enable user-facing terminology without breaking validation

**Decision Tree for Each Domain Term:**
1. Canonical alternative to baseline element? → **Alias** (1 per element max)
2. Different deployment of same type? → **Instance** (same states, different tracking)
3. Facet/component with different states? → **Specialization** (`contributesTo`)
4. Named variant with same states (IS-A)? → **Variant Mapping** (`mapsTo`, name omits parent type)
5. Acronym/abbreviation/synonym? → **Keywords** (10-20 per practice)

See `references/semantics.md` Section 4.3 for comprehensive aliasing rules with worked examples across domains.

**Quality Target:** 3-8 aliases + 10-20 keywords per practice.

## Validation Rules

Validation rules are defined in `references/practice-rules.feature` (8 Features, 33 Scenarios covering alpha relationships, work products, narratives, naming, coverage, aliasing, structural integrity, and process compliance) and enforced programmatically by `utils/eval-skill-output.py` and `utils/assess-practice.py`.

**Key rules to keep in mind during orchestration:**
- No floating alphas: every new alpha needs `contributesTo` or `mapsTo` (@rule:semantic-001)
- `contributesTo` and `mapsTo` are mutually exclusive (@rule:semantic-002)
- `mapsTo` variants must match parent states exactly and omit parent type name (@rule:semantic-003, -010)
- Competency level names must exactly match baseline (@rule:semantic-006)
- `relatesTo` only on new alphas, with required `direction` field (@rule:semantic-007, -008)
- Narratives must have `citationNames`, be placed on correct elements, and describe subject matter not template type (@rule:narrative-001 through -006)
- Element descriptions max 20 words; state/LOD descriptions max 12 words (@rule:naming-001)
- Global name uniqueness across all PracticeElement types (@rule:naming-003)
- Alphas need 3+ states, work products need 2+ LODs (@rule:coverage-001, -002)
- Every alpha state beyond initial needs supporting activity and LOD (@rule:coverage-003, -005)

**Relationship guidance:** `contributesTo` = specialization (different states), `mapsTo` = named variant (same states, IS-A). Valid targets: baseline, practice-local, or dependency alphas. `partOf` = HAS-A containment on work products (mutually exclusive with `mapsTo`).

**relatesTo directionality:** Source alpha declares relationships. Use `outgoing` for acts-upon, `incoming` for acted-upon, `mutual` for symmetric. Prefer active voice from provider perspective.

**Gherkin structured guidance:** Optional `background`, `test`, `examples` properties on states, LODs, checklists, activities (see semantics.md Section 5.3).

**Narrative Citation Rules**

- Citations provide provenance for the claims and frameworks referenced in the narrative

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
- [ ] Narrative names describe subject matter (NOT "X Narrative" or template type references)
- [ ] Narrative descriptions explain content (NOT "The STAR/ABT/Three-Act narrative for...")
- [ ] Element-specific narratives placed on their elements, not in top-level array

**CRITICAL: Pattern Completeness Requirements**

Patterns MUST show complete alpha state progressions across all PatternViews. Read `references/pattern-completeness.md` for the full four-pass construction algorithm, worked examples, and validation checklists. Phase 2 subagents should read this file when mapping patterns (Step 8).

**Summary of Four-Pass Construction:**
1. **Pass 1 (Source-Driven):** Extract pattern structure from source, map explicit alpha states
2. **Pass 2 (Backfill — REQUIRED):** For each alpha, review ALL states, backfill missing cells. Final PatternView must include ALL alphas.
3. **Pass 3 (Related Alphas — OPTIONAL):** Consider adding alphas from practice/dependencies with meaningful progressions
4. **Pass 4 (Validation — REQUIRED):** Max 1 state per alpha per view (split views if 2+), backfill late-appearing alphas with progressive states

**State Compression (JSON Output):** Non-final PatternViews include ONLY alpha states that CHANGE from the previous view. Unchanged carry-forward states are omitted — they are implicit. The FINAL PatternView MUST include ALL alphas (even if unchanged) as a complete end-state snapshot. This prevents redundant entries that obscure which alphas actually progress in each phase.

**Phase 2 Validation:**

```bash
python3 utils/eval-skill-output.py practices/<name>/ --phase 2 --summary
```

Fix any FAIL assertions before proceeding to Phase 3. If sections are missing, read Phase 1 analysis for unmapped content and generate missing sections.

**User Feedback:**
- "Reading analysis report and loading baseline practice..."
- "Mapping N concerns to alphas using redeclaration/specialization framework..."
- "Conducting alpha-state-activity gap analysis..."
- "Gap analysis complete: 100% alpha state coverage achieved"
- "Constructing patterns using four-pass approach..."
- "Pattern validation complete: N×M matrix with 1-2 states per alpha per view"
- "Phase 2 complete: Mapping guide generated at practices/<name>/02-mapping-guide.md"

If `narratives` is missing, review Phase 1 analysis for overarching lifecycle and add method narrative.

### Step 2.5: Secondary Reference Research (Opt-In)

**Skip this step if the planning phase (Step 0) determined secondary research is not needed.**

**Objective:** Actively discover additional reference content to supplement what Phase 1 tagged from source materials. This step runs after Phase 2 mapping is complete, using the established alpha/state/work-product mappings as a search framework.

**When to run:**
- Planning step recommended it (few reference candidates from source materials)
- User explicitly requested reference research

**Process:**

1. **Review Phase 2 reference mappings:** Read the "Reference Content Mappings" section of `02-mapping-guide.md`. Identify which alphas/states have reference coverage and which have gaps.

2. **Search for additional references** targeting uncovered alphas/states:
   - Official methodology templates and starter documents
   - Community tools, GitHub repos, starter kits
   - Reference implementations and architectural examples
   - Industry standards and frameworks (ISO, NIST, TOGAF)
   - Case studies and exemplary implementations

3. **Map discovered references** following reference semantic conventions:
   - `alphaName` + `stateName` (from established mappings)
   - **Name**: Concept-oriented, not content-centric. Pattern: `"Standard [Qualifier] <AlphaName>"`. "Standard" prefix indicates exemplar.
   - **Description**: Semantic role of the reference instance in terms of alpha state progression, not a description of the content asset.
   - **`evidenceBy`**: Document artifacts (decks, guides, templates, cheatsheets) become **full WorkProductInstance objects** — each requires `name`, `description`, `workProductName`, `levelOfDetailName`, and `links` (with at least one valid URI). Bare `{workProductName, levelOfDetailName}` objects are invalid. Navigation resources (hub/landing pages) stay as alpha-level `links` only.
   - **Instance naming**: Instance names scope to the **example**, NOT the state/LOD. The same real-world example at different maturity levels shares ONE name. Before creating a new reference, apply the "same example or different?" test — if content belongs to an existing instance at a different state, use the same name.
   - **Link names**: Use actual content title (not generic platform labels like "Sales Hub"). Applies at both alpha-level and evidenceBy-level links.
   - **Link descriptions**: Optional but recommended when derivable from content inspection.
   - **Links arrays aggregate many documents** — a single instance can have multiple links, producing richer references.
   - `links` with valid URIs (REQUIRED — drop candidates without links)
   - Tags for categorisation
   - **Merge pass**: After generating all references, merge same-name instances: key on instance `name` (NOT alphaName/workProductName), keep highest state/LOD, aggregate all links. Apply same merge to evidenceBy entries within each reference.
   - See update-method SKILL.md Step 3C for the full content-to-work-product heuristics table and structural examples

4. **Present findings to user for approval** before appending to the mapping guide.

5. **Append approved references** to the "Reference Content Mappings" section of `02-mapping-guide.md`.

**User Feedback:**
- "Searching for reference content across N uncovered alpha states..."
- "Found M additional references (templates, tools, case studies)..."
- "Appended N approved references to mapping guide"

### Step 3: Phase 3 - JSON Generation

**Objective:** Generate schema-compliant Practice or Method JSON

**APPROACH DECISION:**

- **Single Practice**: Generate JSON directly, then package into .keleo
- **Multi-Practice Method (2+ practices)**: Use parallel Agent tool approach + package assembly

**Process for Single Practice:**

1. Read `prompts/phase-3-json.md`, mapping guide, schema, effective baseline JSON (from Step 0.5, or user-provided baseline if no dependencies). If the effective baseline has `_aliasContext`, note that all structural references MUST use canonical names.
2. **Read schema version and baseline version** using utilities (NEVER use `python3 -c` for JSON inspection):
   ```bash
   python3 utils/extract-reference-names.py deps/language.schema.json --metadata
   python3 utils/extract-reference-names.py <baseline>.json --metadata
   ```
3. Generate complete practice JSON with **REQUIRED discriminator property**:
   ```json
   {
     "kind": "practice",  // CRITICAL: Required at root level
     "name": "Practice Name",
     "description": "...",
     "schemaVersion": "1.0.0",  // From schema $comment
     "version": "1.0.0",  // Three-part semver
     "baselinePracticeName": "...",  // Inherited from parent practice in parent practice mode
     "practiceDependencyNames": ["..."],  // Only parent practices with actually-referenced unique alphas
     "dependencyVersions": [  // One entry per declared dependency
       {"documentName": "...", "versionRange": "^1.0.0"}
     ],
     ...
   }
   ```
   - **Versioning:** Set `schemaVersion` from schema `$comment`. Set `version` to `"1.0.0"` for new documents. Populate `dependencyVersions` with a caret range (`^X.Y.Z`) pinned to each dependency's current `version` — one entry for `baselinePracticeName` and one per `practiceDependencyNames` entry.
   - **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice's `baselinePracticeName` (NOT the parent practice name). Set `practiceDependencyNames` using the filtering rule (see "Determining practiceDependencyNames" below).
4. Include aliases array from mapping guide
5. **IMPORTANT:** Never re-run `resolve-context.py` during repair/fix iterations — the `_effective-context.json` was generated once in Step 0.5 from the correct baseline + parent sources. Re-running it after the practice JSON exists may include the practice itself, corrupting the context.
6. **Auto-fix common issues first** (resolves missing assets, pattern compression, narrative structure, etc.):
   ```bash
   python3 utils/fix-common-issues.py <practice>.json <leaf-baseline>.json --fix --all
   ```
   Then validate until 0 errors. Always pass the **leaf baseline** as the baseline argument. The validator auto-discovers `_effective-context.json` in the practice directory as a dependency (for cross-practice competency/alpha/alias resolution):
   ```bash
   python3 utils/validate-practice-json.py <practice>.json <leaf-baseline>.json deps/language.schema.json
   ```
6. **Generate ChangeRequest and report downstream impact (if updating existing):** If a prior version of the practice JSON exists in the output directory (i.e., this is a regeneration, not first-time generation), generate a ChangeRequest and present a downstream impact report:
   ```bash
   python3 utils/generate-change-request.py \
     <old-version>.json <new-version>.json \
     --author "<git user>" \
     --status accepted \
     -o practices/<name>/<name>.changerequest.json
   ```
   Then discover downstream dependents and present an impact report to the user:
   ```bash
   python3 utils/discover-dependencies.py --dependents "<Practice Name>"
   ```
   **Present a Downstream Impact Report** listing each affected practice, its path, and which nameChanges impact it. Classify each as "auto-propagatable" (renames that `apply-change-request.py` handles) or "manual remap needed" (structural changes requiring `/update-method`). See `update-method` SKILL.md "ChangeRequest Generation" section for the full report format and propagation workflow.
   
   Skip this step for first-time generation (no prior version exists).
7. **Resolve transitive dependencies** — `.keleo` bundles must include ALL dependency documents (baselines + practices), not the merged effective context:
   ```bash
   python3 utils/discover-dependencies.py --resolve-from practices/<name>/<name>.json --transitive
   ```
   Resolve any ambiguous dependencies (prefer `deps/` or `baselines/` or `practices/` paths over `.keleo`-embedded copies). Collect the full list of resolved file paths.
8. **Package into .keleo** (NEVER use `python3 -c`, heredocs, or shell loops). The packager auto-reads `schemaVersion` from the schema and auto-builds package dependencies from document `dependencyVersions`:
   ```bash
   python3 utils/package-keleo.py \
     --name "<practice-name>" \
     --version "1.0.0" \
     --description "<practice description>" \
     --documents <baseline>.json \
                 [<transitive-dep-1>.json] \
                 [<transitive-dep-2>.json] \
                 practices/<name>/<name>.json \
     -o bundles/<name>.keleo \
     --verify
   ```
   List dependencies in topological order (baselines first, then practices in dependency order, entry-point practice last). Never use `_effective-context.json` as a document — it is a build artifact for semantic context during generation, not a distributable document.

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
   - File paths: `practices/<method-name>/02-mapping-guide.md` (practice section), `deps/language.schema.json`, `<effective-context-path>` (from Step 0.5, or user-provided baseline if no dependencies)
   - **Parent practice mode:** Include in the agent prompt: "Set `baselinePracticeName` to '<inherited baseline name>' (inherited from parent practice). `contributesTo`/`mapsTo` targets reference parent practice alphas using canonical names. Use `contributesTo` for specializations (different states) and `mapsTo` for variant mappings (exact same states, IS-A). Set `practiceDependencyNames` to ONLY those parent practices whose unique alphas (not in baseline) are actually referenced via `contributesTo` or `mapsTo` — see 'Determining practiceDependencyNames' section."
   - If the effective baseline has `_aliasContext`, include in the agent prompt: "The baseline uses domain aliases for semantic context. All structural references in the JSON (contributesTo, mapsTo, alphaName, stateName, etc.) MUST use canonical names, not alias names."
   - What to generate: **Practice JSON** (NOT method JSON) - single practice object
   - Output location: `practices/<method-name>/<practice-name>.json`
   - Schema compliance: all required properties (aliases, alphas, activities, work products, **patterns**, etc.)
   - Explicit instruction: "Generate STANDALONE practice JSON, not embedded in method. CRITICAL REQUIREMENTS: (1) MUST include 'kind': 'practice' property at root level (required discriminator). (2) MUST include aliases array from mapping guide terminology section. (3) MUST include patterns array from mapping guide - minimum 1 pattern per practice with 2+ PatternViews showing alpha progression. (4) Set 'schemaVersion' from schema $comment, 'version' to '1.0.0', and populate 'dependencyVersions' with caret ranges for all declared dependencies. (5) Write output to the SAME directory containing 02-mapping-guide.md — verify the directory exists before writing. (6) For redeclared alphas, include ALL states from the baseline/parent but add checklists ONLY to states enriched in the mapping guide — use empty checklist for unenriched states. Copy baseline state name and description fields VERBATIM — do not rephrase. (7) Every activity MUST have focusName, contributesTo, worksOn, requiredCompetencies, AND recommendedCompetencyLevels — all are schema-required. Include ledBy (Persona.name) when the mapping guide identifies a lead. (8) After writing each pattern, verify the FINAL PatternView includes ALL alphas that appear anywhere in the pattern — missing alphas in the final view is the most common auto-fix. (9) Write ONE output file only — do NOT create intermediate fragment files (e.g., _part1.json). Write the complete JSON in a single Write call. (10) For asset definitions, copy the format of an existing asset entry (use `type`, `fontCharacter`, `fontFamily`, `fontWeight` — NOT `format` or `character`). (11) If the mapping guide defines patternGroups, include them with entries referencing exact Pattern.name values. Preserve baseline patternGroup names exactly when adopting them — the name is the merge key. Only emit groups that have patterns assigned (not empty baseline groups). Include narratives on groups when the mapping guide provides group-level rationale. (12) Include relationshipKind on relatesTo entries and contributesToAlphaNames on work products when present in the mapping guide."

3. **Agents run concurrently**, each producing one practice JSON file

**Step 3B: Package Assembly**

4. **After all practice JSONs complete:**
   - **Review Phase 1 analysis** for method-level overarching narrative (e.g., "The Cycle", SDLC mapping, value stream)
   - **Create method narrative file** using the Write tool (auto-approved):
     Write the narrative JSON to `practices/<method-name>/_method-narrative.json`:
     ```json
     [
       {
         "name": "Method Lifecycle Narrative",
         "description": "Overarching journey across all practices",
         "narrativeTypeName": "The Cycle | STAR | Hero's Journey",
         "narrativeContexts": [
           {"seq": 1, "narrativeElementName": "...", "context": "..."}
         ],
         "citationNames": [...]
       }
     ]
     ```
   - **Resolve transitive dependencies** for all practices in the method:
     ```bash
     python3 utils/discover-dependencies.py --resolve-from practices/<method-name>/practice-1.json --transitive
     ```
     Collect all unique dependency file paths across all practices (deduplicate shared baselines/dependencies).
   - **Package into .keleo** using utility (NEVER use `python3 -c`, heredocs, or shell loops):
     ```bash
     python3 utils/package-keleo.py \
       --name "<method-name>" \
       --version "1.0.0" \
       --description "<method description>" \
       --documents <baseline>.json \
                   [<transitive-dep-1>.json] \
                   [<transitive-dep-2>.json] \
                   practices/<method-name>/practice-1.json \
                   practices/<method-name>/practice-2.json \
                   ... \
       --method-name "<Method Name>" \
       --method-description "<method description>" \
       --method-narrative-file practices/<method-name>/_method-narrative.json \
       -o bundles/<method-name>.keleo \
       --verify
     ```
   List dependencies in topological order (baselines first, then practices in dependency order, method practices last). Never use `_effective-context.json` as a document — it is a build artifact for semantic context during generation, not a distributable document. The packager automatically: generates an externalized method JSON with `practiceNames` (string references) and `baselinePracticeName`, merges/deduplicates citations from all practices, bundles all documents and assets into a `.keleo` ZIP archive with `manifest.json`. The `--verify` flag lists package contents inline.

**Step 3C: Validation and Fixes**

5. **Auto-fix then validate each practice JSON** — always use the **leaf baseline** as the baseline argument:
   ```bash
   python3 utils/fix-common-issues.py <practice>.json <leaf-baseline>.json --fix --all
   python3 utils/validate-practice-json.py <practice>.json <leaf-baseline>.json deps/language.schema.json
   ```

6. **Audit cross-practice references** (methods only — run on individual practice JSONs before packaging):
   ```bash
   python3 utils/audit-method-references.py \
     bundles/<method-name>.keleo \
     --baseline <effective-context.json>
   ```
   If the audit tool does not support `.keleo` input, run it against the individual practice JSONs instead.

7. **Fix errors** — iterate until 0 errors. Common alpha-level fixes:
   ```bash
   # Add missing baseline alpha redeclaration
   python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --add-redeclaration "Alpha Name" --fix
   # Remap references from one alpha to another
   python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remap "Old" "New" --state-map '{"OldState":"NewState"}' --fix
   # Quick error check after fixes (add --parent for each practiceDependencyNames entry)
   python3 utils/assess-practice.py <practice>.json --baseline <baseline>.json --errors-only [--parent <dep>.json ...]
   ```

**Critical JSON Rules:**

From `deps/language.schema.json`:

- **Discriminator property:** `"kind": "practice"` REQUIRED at root level of every practice JSON (enables type discrimination)
- **Redeclared alphas:** Alphas that exist in the baseline or parent practice are REDECLARATIONS — they MUST NOT have `contributesTo` or `mapsTo` properties. These relationships are inherited from the baseline/parent definition.
  - **Include ALL states** from the baseline/parent definition — never subset to only enriched states (the validator checks for exact state-set match)
  - **Copy baseline state `name` and `description` fields verbatim** — do NOT rephrase, shorten, or enrich state descriptions (the validator flags description mismatches as redeclaration-compliance warnings)
  - **Add checklists ONLY to states** that the Phase 2 mapping guide explicitly enriches
  - **For unenriched states**, include them with an empty `"checklist": []` — do NOT fabricate checklists for states the mapping guide does not cover
- **Checklist format:** Objects {name, description, seq}, NOT strings
- **Checklist polarity:** Every item must be positive and additive — describes an achievement to reach, never the absence or lack of something (e.g., "Key Metrics Defined" not "Metrics absent"). Use description/narratives for level qualities including limitations
- **Competency references:** {competencyName, competencyLevelName}, NOT {competencyName, level}
- **Persona property:** `competencies`, NOT `requiredCompetencies`
- **Activity competencies:** BOTH `requiredCompetencies` (strings) AND `recommendedCompetencyLevels` (objects)
- **PatternView properties:** `alphaStates` NOT `alphas`, `patternViews` NOT `views`, NO `workProducts`
- **LOD contributesTo:** REQUIRED on every LevelOfDetail
- **Tags structure:** Nested object {domainTags, lifecycleTags, organizationalTags}, NOT flat array
- **ledBy on activities:** Optional `Persona.name` string identifying the single lead (distinct from `involves` which maps participating groups)
- **patternGroups:** Optional array of PatternGroup objects organizing patterns into navigational categories. Include when practice has 3+ patterns. Adopt baseline-defined groups first; novel groups require justification. Use exact baseline group names (merge key). Groups have narratives when source material supports rationale. Entries reference exact Pattern.name values.
- **contributesToAlphaNames on work products:** Optional array of alpha names serving as purpose-hub summary
- **relationshipKind on relatesTo:** Optional enum (dependency, production, guidance, information-flow, enabling, impact, consumption, mutual)

**Phase 3 Validation:**

```bash
# --baseline and --schema are auto-discovered from the practice JSON;
# explicit flags override auto-discovery when needed.
python3 utils/eval-skill-output.py practices/<name>/ --summary
```

Quick status check:
```bash
python3 utils/eval-skill-output.py practices/<name>/ --one-line
```

To see only failed assertions with details:
```bash
python3 utils/eval-skill-output.py practices/<name>/ --show-failed
```

Fix all FAIL assertions with `error` severity. Warning assertions are advisory — address where practical. Re-run until `error_pass_rate: 1.0`.

**Combined validate-fix loop** (preferred — runs all fixes and re-validates in one command):
```bash
python3 utils/lint-practice.py <practice>.json [<baseline>.json] [<schema>.json] --fix
```

**Individual fix tools** (when targeted intervention is needed):
- `python3 utils/fix-competency-levels.py <file>.json <baseline>.json --fix` — fix competency level name mismatches
- `python3 utils/assess-practice.py <file.json> --baseline <baseline.json>` — detailed issue report for targeted fixes

**User Feedback:**
- "Generating JSON from mapping guide..."
- "Running validation (schema, baseline, integrity)..."
- "Found N errors in category X, applying fixes..."
- "Packaging into .keleo archive..."
- "Validation passed! Generated schema-compliant package at bundles/<name>.keleo"

---

## Validation Script

**Location:** `utils/validate-practice-json.py`

**Purpose:** Comprehensive validation combining:
1. JSON Schema compliance
2. Baseline practice reference checking
3. Internal cross-reference integrity (including patternView ambiguity and alias collisions)

**Usage:**
```bash
python3 utils/validate-practice-json.py \
  <practice-or-method.json> \
  <leaf-baseline.json> \
  <language-schema.json>
```

The validator auto-discovers `_effective-context.json` or `_effective-parent.json` in the practice directory and loads them as dependencies for cross-practice element resolution. Always pass the **leaf baseline** — not the effective context — as the baseline argument.

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
   - Add `contributesTo` or `mapsTo` to floating alphas
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

### No Inline Scripts + Utils Self-Extension

**All programmatic actions use reusable scripts in `utils/`, never `python3 -c` or `bash -c`.**
Use the Write tool (auto-approved) to create intermediate files, then call utility scripts. This rule applies to subagents too.

**No compound bash scripts.** Avoid `TARGET=... && grep ... && wc ...` or `for f in ...; do ... done` in Bash calls — these trigger permission prompts. Instead, use separate tool calls for each simple command (`grep`, `wc`, `head`, etc.) which are auto-approved. For batch inspection of multiple files, use a utility script.

**When you need functionality that doesn't exist yet**, read `.claude/skills/SKILL-STANDARD.md` §7.4 for the full Utils Self-Extension Protocol, then:
1. Read `utils/README.md` to check for existing capabilities
2. Extend an existing script or create a new one (do NOT halt or defer to the user)
3. Update `utils/README.md` with the change
4. Continue processing

### Key Utilities

**Canonical registry:** `utils/README.md` — read this for the full, current list of all utilities.

Run `python3 utils/<script>.py --help` for detailed usage of any script.

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

- User provides a baseline name or file path
- Auto-discovery scans `baselines/`, `practices/`, and `deps/` directories to resolve names to paths
- All resolved dependencies are confirmed with user before proceeding
- Validation script validates against provided baseline
- Works with any baseline following Practice Language schema

### Determining practiceDependencyNames (Parent Practice Mode)

**Rule:** A practice must declare a dependency on a parent practice when it references alphas that originate from that parent practice. There are two cases:

1. **`contributesTo`/`mapsTo` targets:** If a new alpha targets a practice-only alpha (not in baseline), that creates a dependency.
2. **Redeclarations of practice-only alphas:** If the practice redeclares an alpha that was **introduced** by a parent practice (has `contributesTo`/`mapsTo` in the parent, not a baseline root alpha), that alpha's defining practice is a dependency — the validator checks redeclared states against the defining practice.

**Algorithm (apply per practice after Phase 3 JSON generation):**

1. **Collect all alpha references:**
   - `contributesTo`/`mapsTo` targets from new alphas
   - Names of all redeclared alphas (alphas without `contributesTo`/`mapsTo`)
2. **Filter out practice-local targets** (alphas defined within the same practice)
3. **For each remaining reference**, classify it using `_effective-context.json`:
   - Check the alpha's `_contributingPracticeName` against `_provenance.tiers`
   - **Baseline alpha** (source in `tiers.baselines`): no dependency created
   - **Practice-only alpha** (source in `tiers.practices`): creates dependency on that contributing practice
4. **Set `practiceDependencyNames`** to the deduplicated list of contributing practices. If all referenced alphas trace to baselines, set to `[]`.

**Using `_contributingPracticeName` for dependency determination:**
The effective context annotates every element with its source. Check each referenced alpha's `_contributingPracticeName` and cross-reference with `_provenance.tiers`:
- If the source is in `tiers.baselines` → baseline alpha → no dependency
- If the source is in `tiers.practices` → practice alpha → add that practice to `practiceDependencyNames`

**Verification command (legacy, still works):**
```bash
python3 utils/resolve-practice-dependencies.py \
  --parent _effective-context.json \
  --baseline <validation-baseline.json> \
  --practice <practice.json> \
  --per-alpha
```

**Why this matters:** Blindly including all parent practice names inflates the dependency graph and creates false coupling. A practice that only contributes to baseline alphas (e.g., "Platform", "Way Of Working") has no structural dependency on the parent practices that redeclare those alphas.

**Example:**
- Practice alpha "AI Model" has `contributesTo: "Platform Asset"` → "Platform Asset" is a baseline alpha → no dependency
- Practice alpha "Inference Monitoring" has `contributesTo: "Observability Stack"` → "Observability Stack" is NOT in baseline, defined in parent's "Observability" practice → dependency on "Observability"
- Result: `practiceDependencyNames: ["Observability"]`

---

## Common Pitfalls

Validation rules are defined in `references/practice-rules.feature` and enforced by `utils/assess-practice.py`. This section lists pitfalls with unique fix commands not covered by those rules.

### Workflow
- Compact context between phases (token budget exhaustion is the #1 failure mode)
- Generate ALL content — never "example" or partial output

### Phase 1
- Citations SHOULD have `url` fields (official sites, DOI, publisher pages). Never fabricate URLs.
- Include `acknowledgements` when source credits contributors (distinct from citations)
- Identify concern relationships (production flows, enablement, governance) for Phase 2 mapping

### Phase 2 — Aliases
- Target 3-8 aliases. ONE per baseline element. Distinguish:
  - **Synonyms/acronyms** → `keywords` array
  - **Facets/components** → specialization alphas (`contributesTo`)
  - **Named variants** → variant alphas (`mapsTo`)
  - **Deployments** → instances (same behavior, different tracking)

### Phase 2 — Alpha Relationships
- `contributesTo`/`mapsTo` can target baseline, practice-local, OR external practice alphas
- `mapsTo` = exact same states + IS-A semantics. `contributesTo` = different state progression
- Competency levels: extract valid names with `python3 utils/extract-reference-names.py <baseline>.json --sections competencies`

### Phase 2 — Coverage
- Alpha-state-activity gap analysis (Phase 2 Step 7.5): every state beyond initial needs ≥1 supporting activity
- Multi-practice methods: each practice MUST have alphas, work products, activities, AND patterns — don't let later practices degenerate to activities-only
- Patterns: use four-pass construction from `references/pattern-completeness.md`

### Phase 3 — Schema Shape
Auto-fixable with `python3 utils/fix-common-issues.py <file>.json --fix --all`. Key gotchas:

| Property | Correct | Wrong |
|---|---|---|
| `kind` | `"practice"` or `"method"` at root | Missing (most common error) |
| `involves` | `string[]` of persona group names | Array of objects |
| `assetNames` | `[{"assetName": "x", "type": "icon"}]` | `"assetName": "x"` (singular string) |
| `background` | `{"given": [...], "alphaStates": [...]}` | String or array |
| `test` | Object with `name`, `description`, optional `given`/`when`/`then` | Missing PracticeElement fields |
| `competencies` on personas | `competencies` | `requiredCompetencies` |

### Phase 3 — Name Collisions
Names must be globally unique across element types. Fix with disambiguating suffixes:
- WorkProduct: add "File", "Document", "Template"
- Activity: add verb prefix ("Configure Platform")
- Detect: `python3 utils/assess-practice.py <file>.json`

### Phase 3 — Competency Levels
Fix invalid levels: `python3 utils/fix-competency-levels.py <file>.json <baseline>.json --fix`
Common PAE mappings: "Advanced"→"Masters", "Expert"→"Innovating", "Intermediate"→"Applies", "Beginner"→"Basic"

---

## Cross-Practice Dependencies

Alpha hierarchies and cross-practice dependencies are covered in `references/semantics.md` Section 4.4-4.5 and `references/practice-method-strategy.md`.

**Key rules:**
- **Practice-local chains**: `Platform Service → Platform Capability → Platform (baseline)` — referenced alpha must be defined earlier in the mapping guide
- **Cross-practice references**: Set `practiceDependencyNames` array + `dependencies` array with `{practiceName, reason}`
- **Orchestration practices**: Use `practiceDependencyNames` to load alphas, create patterns that coordinate across them, do NOT redefine alphas from dependencies
- **Validation**: `python3 utils/assess-practice.py <file>.json --baseline <baseline>.json --parent <dep>.json` — use `--parent` per dependency to avoid false positives

---

## Practice vs Method Handling

Full delineation strategy with worked examples is in `references/practice-method-strategy.md`. Phase 2 subagents should read this during Step 0 (delineation validation).

**Quick reference:**

| Signal | Decision | Alpha Range |
|---|---|---|
| 3-7 baseline alphas, one primary | Single Practice | 1 primary + 2-6 related |
| 8+ alphas, multiple primaries | Method (multi-practice) | 3-7 per practice |
| Cross-practice coordination needed | Orchestration Practice | Minimal (coordination only) |

**Core principle:** Each practice focuses on ONE primary alpha + its directly related alphas (via `relatesTo`, 1-level deep). No "everything else" catch-all practices.

**Cross-baseline methods:** Use `bindings.alphaBindings` when composing practices from different baseline families (see `references/semantics.md` Section 4.8).

---

## User Interaction

- **Start**: Enter plan mode, analyze sources, create execution roadmap
- **Before Phase 2**: Request baseline practice file path
- **During phases**: Brief progress updates
- **After validation**: Report findings, apply fixes, confirm 0 errors
- **Final output**: List generated files with validation summary
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

3. **`bundles/<name>.keleo`**
   - `.keleo` package (ZIP archive with `manifest.json`)
   - Bundles all documents: baseline JSON, practice JSON(s), method JSON (for methods)
   - Method uses externalized `practiceNames` and `baselinePracticeName` string references
   - Each practice/baseline validated against schema before packaging
   - Includes bundled assets if visual artifacts use file-based paths

4. **`practices/<name>/<practice-name>.json`** (intermediate files)
   - Individual practice JSONs produced by Phase 3 agents
   - Used for validation before packaging
   - Included as documents in the `.keleo` package

### Assets

**Coverage requirements:**
- **REQUIRED**: Every alpha and activity MUST have an icon-type AssetReference (Font Awesome 6 Free preferred)
- **RECOMMENDED**: Pattern views with icon references
- **OPTIONAL**: Diagrams (URLs to methodology sites), templates (URLs to GitHub/official docs)

**Priority**: Font characters > external URLs > bundled files. Use `assetNames` (plural array of `{assetName, type}` objects), NOT `assetName` (singular string).

**Phase 2**: Document icons in Assets section of mapping guide. **Phase 3**: Populate `assets` array and element `assetNames`. See `deps/language.schema.json` `$defs/Asset` and `$defs/AssetReference` for schema. See CLAUDE.md Assets section for JSON examples.

**Common FA icons**: Platform (`fa-cubes`), Team (`fa-users`), Security (`fa-shield-halved`), Architecture (`fa-sitemap`), Dev (`fa-code`), Ops (`fa-gears`), Strategy (`fa-compass`), Requirements (`fa-list-check`), Value (`fa-chart-line`)

**Validation**: `assess-practice.py` checks icon coverage and assetName resolution.

---

## Success Criteria

1. All three phases complete, validation passes with 0 errors (schema + baseline + internal integrity)
2. All source methodology content mapped — no omissions
3. Rich narratives with citations, distinct observable criteria (typical 3-7/state; error if >10), orthogonal tags

---

## Post-Completion Review (MANDATORY)

**After completing the skill workflow OR after completing planning**, read `.claude/skills/SKILL-STANDARD.md` §11 for the full Post-Completion Review protocol, then follow these steps:

1. **Utils remediation (apply immediately)**: Audit the session for inline scripts, ad-hoc logic, or workarounds that should be generalizable utilities. For each finding, follow the Utils Self-Extension Protocol — extend or create the utility, update `utils/README.md`, and confirm it works. Do NOT defer to the user for utils changes.

2. **Permission gaps (propose to user)**: Identify Bash commands that triggered permission prompts but could be auto-allowed. Suggest additions to `.claude/settings.json`.

3. **Skill improvements (propose to user)**: Identify instruction gaps that led to wrong output or repeated manual corrections. Propose specific SKILL.md edits.

4. **Report**: Tell the user what was remediated (utils created/extended) and what is proposed (permissions, skill changes). A clean session is a good signal — say so if nothing was found.
