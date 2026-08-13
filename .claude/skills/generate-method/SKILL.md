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

4. **Plan execution:**
   - Tentative practice/method name (kebab-case)
   - Phase execution sequence
   - Expected complexity and size
   - Potential challenges
   - **Note:** Practice boundaries will be finalized in Step 1.5 (Delineation Gate) before Phase 2 delegation

5. **Exit plan mode** with clear execution roadmap

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
   - Explicit instruction: "Generate COMPLETE mapping including: (0) Delineation Analysis section validating your practice boundaries; (1) Keywords section with 10-20 domain terms/acronyms; (2) Terminology Aliases section identifying 3-8 domain canonical terms (ONE alias per element - use keywords for synonyms/acronyms, use instances for multiple variants); (3) Alphas (if any) WITH relatesTo relationships; (4) Work products; (5) Activities; (6) PATTERNS with complete matrix coverage. CRITICAL: Map concern interactions from Phase 1 to alpha relatesTo arrays using directionality pattern. Every practice MUST have at least ONE pattern coordinating multiple alphas/concerns (see semantics.md Section 8.1.1)."

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

3. **Does this term represent a facet/component with specialized behavior, or a named variant?**
   - YES, with different states → Use **specialization** (`contributesTo`) (e.g., "Automation Controller", "Execution Environment" are facets of Platform with unique lifecycles)
   - YES, with same states (IS-A variant) → Use **variant mapping** (`mapsTo`) (e.g., "AI-Ready Enterprise" IS a "Sales Play" with same lifecycle)
   - Optional: alias the specialized/variant alpha if domain uses shortened form
   - NO → Go to step 4

4. **Is this an acronym/abbreviation/synonym?**
   - YES → Add to **keywords** array (e.g., "AAP", "automation platform", "EE")
   - NO → Skip

**Four-Way Distinction:**
- **Alias (1 per element):** "Playbook" replaces "Deployment Documentation" in presentation
- **Keywords (10-20 per practice):** ["AAP", "ansible", "automation", "controller", "EE"] for search
- **Specialization (`contributesTo`):** "Automation Controller" is new alpha (facet of Platform with unique states/lifecycle)
- **Variant Mapping (`mapsTo`):** "AI-Ready Enterprise" is new alpha (named variant of Sales Play with same states, domain-specific checklists). Name omits parent type — reads as "[Name] is a [Parent Type]", so repeating the type is redundant.
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

## Feature: Alpha Relationship Integrity

Rules governing alpha hierarchy, parent relationships, and semantic connections. From `references/semantics.md` Sections 4.1, 6.1, 6.2.

### Scenario: No floating alphas (@rule:semantic-001)
- Given: A new alpha is defined that does not exist in the baseline
- When: Phase 3 generates the alpha JSON
- Then: The alpha has exactly one of `contributesTo` or `mapsTo`
- And: The target resolves to a baseline, practice-local, or dependency alpha

### Scenario: contributesTo and mapsTo are mutually exclusive (@rule:semantic-002)
- Given: A new alpha declares a parent relationship
- When: The alpha JSON is generated
- Then: The alpha has `contributesTo` or `mapsTo` but never both

### Scenario: mapsTo variants match parent states exactly (@rule:semantic-003)
- Given: A new alpha has `mapsTo` pointing to a parent alpha
- When: The alpha's states are generated
- Then: The state names and sequence exactly match the parent alpha's states

### Scenario: mapsTo variant names omit parent type (@rule:semantic-010)
- Given: A new alpha has `mapsTo` pointing to a parent alpha
- When: The alpha name is chosen
- Then: The alpha name does not contain the parent alpha's name
- And: The alias name (if present) does not contain the parent alpha's name

### Scenario: Redeclared alphas have no contributesTo or mapsTo (@rule:semantic-005)
- Given: An alpha name matches a baseline or parent practice alpha
- When: The alpha is included in the practice JSON
- Then: The alpha has neither `contributesTo` nor `mapsTo`
- And: Only practice-specific checklists, narratives, and Gherkin guidance are added

### Scenario: Competency level names match baseline exactly (@rule:semantic-006)
- Given: An activity or persona references a competency level
- When: The `competencyLevelName` value is set
- Then: The value exactly matches a CompetencyLevel.name from the baseline for that competency
- And: Level names are extracted with `python3 utils/extract-reference-names.py <baseline>.json --sections competencies`

### Scenario: relatesTo only on new alphas (@rule:semantic-007)
- Given: An alpha is a redeclaration of a baseline alpha
- When: The alpha JSON is generated
- Then: No `relatesTo` array is added (baseline relationships are inherited)

### Scenario: relatesTo entries have required fields (@rule:semantic-008)
- Given: A new alpha defines `relatesTo` relationships
- When: The relatesTo array is generated
- Then: Every entry has `relationship`, `alphaName`, and `direction` fields
- And: `direction` is one of `outgoing`, `incoming`, or `mutual`

### Scenario: contributesToState references valid parent state (@rule:semantic-009)
- Given: A state on a new alpha declares `contributesToState`
- When: The state JSON is generated
- Then: The `contributesToState` value is a valid state name on the parent alpha referenced by `contributesTo` or `mapsTo`

### Scenario: Baseline references are case-sensitive (@rule:semantic-011)
- Given: The practice references baseline elements (alphas, focuses, activitySpaces, competencies)
- When: Symbolic reference values are set
- Then: Every reference exactly matches the baseline element's `name` (case-sensitive)

**Relationship Guidance (not testable — instructional context):**

`contributesTo` creates a specialization with distinct state progression. `mapsTo` creates a named variant with identical states (IS-A semantics — appears in parent's `variants` array on merge). Valid targets for both: baseline alphas, practice-local alphas (multi-level chains), or external practice alphas (creates dependency via `practiceDependencyNames`).

**relatesTo Directionality Pattern:** The declaring alpha is the SOURCE. Read as `[Source] [relationship verb] [target]`. Use `outgoing` for acts-upon ("produces", "enables", "constrains", "hosts"), `incoming` for acted-upon ("governed by", "built by"), `mutual` for symmetric (sparingly). Prefer active voice from provider perspective: "Y enables X" over "X depends on Y".

**Identifying Relationships:** Look for Phase 1 concern interactions:
- Production: A.relatesTo = `[{relationship: "produces", alphaName: "B", direction: "outgoing"}]`
- Enablement: "enables", Guidance: "guides"/"constrains", Validation: "validates"
- Hosting: "hosts", Impact: "influences", Information: "provides"
- Passive: "governed by" with `direction: "incoming"`

**`contributesToState`**: Optional on State objects — maps child state → parent state. Not every state needs a mapping. For `contributesTo`: contribution evidence; for `mapsTo`: state equivalence.

**Orthogonal tags:** Use `{domainTags, lifecycleTags, organizationalTags}` (Section 3.1.2).

**Redeclaration vs Specialization:** Follow decision framework (Section 9.2.5).

**Gherkin-Inspired Structured Guidance:** Optional `background`, `test`, and `examples` properties add structured verification context (semantics.md Section 5.3, 8.1.1):
- **Background** (on State, LevelOfDetail, ActivitySpace/Activity): `given`, `alphaStates`, `workProductLevels`
- **Test** (on Checklist, Activity): Given/When/Then verification with `name` and `description`
- **Examples** (on Checklist, Activity): Concrete scenario array
- Use for complex prerequisites, verification logic, non-obvious triggers. Skip for self-evident items.

## Feature: Narrative Quality

Rules governing narrative structure, naming, self-containment, and citation linkage.

### Scenario: Narratives are structured objects (@rule:narrative-001)
- Given: A narrative is defined on any element or at practice level
- When: The narrative JSON is generated
- Then: The narrative has `narrativeTypeName` and `narrativeContexts` array
- And: Each context has `seq`, `narrativeElementName`, and `context` fields

### Scenario: Narrative names describe subject matter (@rule:narrative-003)
- Given: A narrative has a `name` and `description`
- When: The narrative JSON is generated
- Then: The name describes the subject matter, not the template type
- And: The description explains what the narrative covers, not the framework structure
- And: Contexts contain direct story content without mentioning the narrative type

### Scenario: Narrative contexts are self-contained (@rule:narrative-005)
- Given: A narrative has contexts with `narrativeElementName` labels
- When: The context strings are generated
- Then: Each context is coherent without its element heading visible
- And: Bare lists include a framing introduction sentence

### Scenario: Narratives placed on correct elements (@rule:narrative-002)
- Given: A narrative describes a specific alpha, activity, or work product
- When: The narrative is attached in the JSON
- Then: Element-specific narratives are on the element's `narratives[]` property
- And: Only practice/method-level narratives go in the top-level `narratives[]` array

### Scenario: All narratives have citation references (@rule:narrative-006)
- Given: A narrative is defined
- When: The narrative JSON is generated
- Then: The narrative includes a `citationNames` array with at least one citation reference

## Feature: Element Naming

Rules governing element names, descriptions, and name uniqueness.

### Scenario: Descriptions are single sentences under word limit (@rule:naming-001)
- Given: An element has a `description` field
- When: The description is generated
- Then: Element descriptions are at most 20 words
- And: State and LOD descriptions are at most 12 words

### Scenario: Checklist names are noun-phrase labels (@rule:naming-002)
- Given: A checklist item on an alpha state has `name` and `description`
- When: The checklist JSON is generated
- Then: The name is a short noun phrase (not truncated from the description)
- And: The name is not identical to the description

### Scenario: Global name uniqueness across element types (@rule:naming-003)
- Given: Multiple PracticeElement types are defined (alphas, workProducts, activities, personas, patterns)
- When: All element names are collected
- Then: No name appears in more than one element type

### Scenario: LOD names describe content maturity (@rule:naming-004)
- Given: A work product has levels of detail
- When: LOD names are chosen
- Then: Names describe what the **document looks like** at that fidelity level, following the rubric in `references/workproduct-assessment-rubric.csv` (Summarised → Structured → Elaborated → Actionable)
- And: Every LOD covers the **same full scope** — the difference between levels is depth, not breadth or temporal progression
- And: Names do not use generic labels ("Level 1", "Basic") or concern progression terms ("Established", "Optimized", "Evolved")
- And: Names do not describe lifecycle events or temporal stages (e.g., "Work Completed", "Definition of Done Met", "Goal Stated", "Continuously Updated")
- And: The litmus test passes: the name answers "what does this document contain?" not "where does the concern stand?"

### Scenario: Activity names differ from ActivitySpace names (@rule:naming-005)
- Given: An activity is assigned to an ActivitySpace
- When: The activity name is chosen
- Then: The activity name is distinct from the ActivitySpace name

## Feature: Coverage Completeness

Rules governing minimum counts and activity-to-state coverage.

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
- And: Each alpha appears in every view (backfilled if needed)

### Scenario: Alpha states have supporting activities (@rule:coverage-005)
- Given: An alpha state beyond the initial state exists on a new alpha
- When: Activity contributesTo references are checked
- Then: At least one activity has `contributesTo` targeting the alpha state

## Feature: Terminology Aliasing

Rules governing practice element aliases and keywords.

### Scenario: One alias per element maximum (@rule:aliasing-001)
- Given: The practice defines terminology aliases
- When: Aliases are assigned to baseline elements
- Then: Each baseline element has at most one alias

### Scenario: Alias names excluded from structural references (@rule:aliasing-002)
- Given: An alias maps a baseline name to a domain-specific name
- When: The practice JSON uses symbolic references (alphaName, contributesTo, activitySpaceName, etc.)
- Then: Only canonical baseline names appear in structural reference fields
- And: Alias names never appear in structural reference fields

### Scenario: Keyword count within range (@rule:aliasing-003)
- Given: The practice defines a keywords array
- When: Keywords are generated
- Then: The array contains between 10 and 20 keywords

## Feature: Structural Integrity

Validates that generated JSON has correct shape, required sections, and resolved cross-references.

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
- And: Every stateName resolves to a valid state on that alpha

### Scenario: Activity-alpha cross-references resolve (@rule:structural-004)
- Given: An activity has contributesTo entries referencing alphas and states
- When: Phase 3 generates the JSON
- Then: Every alphaName and stateName in activity contributesTo resolves to a defined alpha and state

### Scenario: Activity-work product cross-references resolve (@rule:structural-005)
- Given: An activity has worksOn entries referencing work products and LODs
- When: Phase 3 generates the JSON
- Then: Every workProductName and levelOfDetailName in worksOn resolves to defined elements

### Scenario: Work product partOf references resolve (@rule:structural-006)
- Given: A work product has a `partOf` property
- When: Phase 3 generates the JSON
- Then: The `partOf` value resolves to a WorkProduct.name in the same practice, a dependency practice, or the baseline
- And: The work product does not reference itself
- And: No circular partOf chains exist (A partOf B, B partOf A)

## Feature: Process Compliance

Validates that the three-phase pipeline is executed in order with proper gates.

### Scenario: Phase 1 completed before Phase 2 (@rule:process-001)
- Given: The three-phase pipeline is being executed
- When: Phase 2 mapping begins
- Then: 01-analysis-report.md exists with all 8 required sections
- And: Analysis has sufficient depth (5+ numbered subsections and 3+ source references)

### Scenario: Phase 2 completed before Phase 3 (@rule:process-002)
- Given: The three-phase pipeline is being executed
- When: Phase 3 JSON generation begins
- Then: 02-mapping-guide.md exists with all 7 required sections
- And: At least 3 alphas, 5 activities, and 1 pattern are mapped

### Scenario: Validation run after JSON generation (@rule:process-003)
- Given: Phase 3 has generated a JSON file
- When: The phase is marked complete
- Then: validate-practice-json.py has been run with 0 schema errors
- And: assess-practice.py has been run with 0 error-severity issues

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

**Constraint 1: One Alpha State Per PatternView**
- **Rule:** Each alpha MUST target at most 1 state per PatternView
- **Anti-pattern:** 2+ states for the same alpha in a single view → **Ambiguous** (which state is the view's target?)
- **Validator enforcement:** `validate-practice-json.py` flags multi-state alpha targets as errors

**When 2+ states appear for an alpha in a PatternView, split into sub-views:**
- **Naming convention:** `Phase: Sub-step` (e.g., "Enable: Train", "Enable: Certify")
- Each sub-view gets its own `seq` number, activities, and narrative context
- Activities are assigned to the sub-view whose alpha state they most directly advance
- Sub-views within a phase can share the same narrative element (e.g., both map to "Do")

**Example:**
  - **Before:** View 2 "Implement" has Platform states: Architecture Designed, Built, Deployed, Monitored (4 states!)
  - **After:** Split into:
    - View 2 "Implement: Design": Architecture Designed
    - View 3 "Implement: Build": Built
    - View 4 "Implement: Deploy": Deployed
    - View 5 "Implement: Operate": Monitored

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

### Step 3: Phase 3 - JSON Generation

**Objective:** Generate schema-compliant Practice or Method JSON

**APPROACH DECISION:**

- **Single Practice**: Generate JSON directly, then package into .keleo
- **Multi-Practice Method (2+ practices)**: Use parallel Agent tool approach + package assembly

**Process for Single Practice:**

1. Read `prompts/phase-3-json.md`, mapping guide, schema, effective baseline JSON (from Step 0.5, or user-provided baseline if no dependencies). If the effective baseline has `_aliasContext`, note that all structural references MUST use canonical names.
2. **Read schema version** from `deps/language.schema.json` `$comment` field (format: `schemaVersion:X.Y.Z`).
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
5. Validate and fix until 0 errors. Always pass the **leaf baseline** as the baseline argument. The validator auto-discovers `_effective-context.json` in the practice directory as a dependency (for cross-practice competency/alpha/alias resolution):
   ```bash
   python3 utils/validate-practice-json.py <practice>.json <leaf-baseline>.json deps/language.schema.json
   ```
6. **Resolve transitive dependencies** — `.keleo` bundles must include ALL dependency documents (baselines + practices), not the merged effective context:
   ```bash
   python3 utils/discover-dependencies.py --resolve-from practices/<name>/<name>.json --transitive
   ```
   Resolve any ambiguous dependencies (prefer `deps/` or `baselines/` or `practices/` paths over `.keleo`-embedded copies). Collect the full list of resolved file paths.
7. **Package into .keleo** (NEVER use `python3 -c`, heredocs, or shell loops). The packager auto-reads `schemaVersion` from the schema and auto-builds package dependencies from document `dependencyVersions`:
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
   - Explicit instruction: "Generate STANDALONE practice JSON, not embedded in method. CRITICAL REQUIREMENTS: (1) MUST include 'kind': 'practice' property at root level (required discriminator). (2) MUST include aliases array from mapping guide terminology section. (3) MUST include patterns array from mapping guide - minimum 1 pattern per practice with 2+ PatternViews showing alpha progression. (4) Set 'schemaVersion' from schema $comment, 'version' to '1.0.0', and populate 'dependencyVersions' with caret ranges for all declared dependencies."

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

5. **Validate each practice JSON** — always use the **leaf baseline** as the baseline argument. The validator auto-discovers `_effective-context.json` in the practice directory as a dependency (resolves cross-practice competency/alpha/alias references):
   ```bash
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
- **Redeclared alphas:** Alphas that exist in the baseline or parent practice are REDECLARATIONS — they MUST NOT have `contributesTo` or `mapsTo` properties. These relationships are inherited from the baseline/parent definition. Only add practice-specific checklists, narratives, and Gherkin guidance to redeclared alphas.
- **Checklist format:** Objects {name, description, seq}, NOT strings
- **Competency references:** {competencyName, competencyLevelName}, NOT {competencyName, level}
- **Persona property:** `competencies`, NOT `requiredCompetencies`
- **Activity competencies:** BOTH `requiredCompetencies` (strings) AND `recommendedCompetencyLevels` (objects)
- **PatternView properties:** `alphaStates` NOT `alphas`, `patternViews` NOT `views`, NO `workProducts`
- **LOD contributesTo:** REQUIRED on every LevelOfDetail
- **Tags structure:** Nested object {domainTags, lifecycleTags, organizationalTags}, NOT flat array

**Phase 3 Validation:**

```bash
# --baseline and --schema are auto-discovered from the practice JSON;
# explicit flags override auto-discovery when needed.
python3 utils/eval-skill-output.py practices/<name>/ --summary
```

To see only failed assertions with details:
```bash
python3 utils/eval-skill-output.py practices/<name>/ --show-failed
```

Fix all FAIL assertions with `error` severity. Warning assertions are advisory — address where practical. Re-run until `error_pass_rate: 1.0`.

**Common fix tools:**
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

### No Inline Scripts

**All programmatic actions use reusable scripts in `utils/`, never `python3 -c` or `bash -c`.**

**NEVER use any of these shell patterns — they all trigger permission prompts:**
- `python3 -c "..."` — inline Python scripts
- `bash -c "..."` — inline Bash scripts
- `cat << 'EOF' ... EOF` — heredoc file creation (use Write tool instead)
- `cat file1 <(echo ...) file2` — process substitution (use `assemble-mapping-guide.py` instead)
- `for i in ...; do ... done` with variable expansion (use utility `--stats` flags or multi-file arguments instead)

**Instead:** Use the Write tool (auto-approved) to create any intermediate files (e.g., narrative JSON, patch files), then call utility scripts with `--patch-file` or `--narrative-file`.

Source material extraction (Google Workspace):
- **Extract text from Slides or Docs API JSON:** `python3 utils/extract-gws-text.py <api-output.json>` (auto-detects Slides vs Docs format)
- **Force format:** `python3 utils/extract-gws-text.py <file.json> --format slides|docs`
- **Batch with output directory:** `python3 utils/extract-gws-text.py file1.json file2.json -o output-dir/`
- **Typical workflow:** Fetch via `gws slides presentations get --params '{"presentationId": "..."}' 2>/dev/null > /tmp/slides.json`, then `python3 utils/extract-gws-text.py /tmp/slides.json`

Common utilities for JSON inspection:
- **Structural inspection:** `python3 utils/extract-reference-names.py <file.json> --sections focuses alphas activitySpaces competencies narrativeTypes --alpha-details`
- **Citation inspection:** `python3 utils/extract-reference-names.py <file.json> --sections citations --citation-details`
- **Activity inspection:** `python3 utils/extract-reference-names.py <file.json> --sections activities --activity-details`
- **Work product inspection:** `python3 utils/extract-reference-names.py <file.json> --sections workProducts`
- **Narrative inspection (top-level):** `python3 utils/extract-reference-names.py <file.json> --sections narratives`
- **Narrative placement (all elements):** `python3 utils/extract-reference-names.py <file.json> --narrative-placement`
- **Narrative content preview:** `python3 utils/extract-reference-names.py <file.json> --narrative-content` (descriptions + first context snippet)
- **Aliases/types/citations:** `python3 utils/extract-reference-names.py <file.json> --sections aliases narrativeTypes citations`
- **Element template (raw JSON):** `python3 utils/extract-reference-names.py <file.json> --sample activities` (also: alphas, workProducts, patterns, etc.)
- **Discover dependency by name:** `python3 utils/discover-dependencies.py --resolve "Practice Name"` (find file path by practice/baseline name)
- **Resolve all dependencies:** `python3 utils/discover-dependencies.py --resolve-from <file>.json --transitive` (extract and resolve all deps recursively)
- **List available files:** `python3 utils/discover-dependencies.py --list` (index all JSON files in baselines/, practices/, deps/)
- **Dependency analysis:** `python3 utils/resolve-practice-dependencies.py --parent <parent.json> --baseline <baseline.json> --practice <practice.json> --per-alpha`
- **Baseline/parent narrative types:** `python3 utils/extract-reference-names.py <baseline-or-parent>.json --sections narrativeTypes` (type names with narrative elements)
- **Specific narrative type definitions (full JSON):** `python3 utils/extract-reference-names.py <file>.json --sections narrativeTypes --narrative-type-names "STAR" "Technique" "PDCA"` (dumps complete JSON objects for named types)
- **Find all references to an element:** `python3 utils/extract-reference-names.py <file>.json --find-refs "Platform"` (searches alphas, activities, workProducts, patterns, aliases for all references to a named element)
- **Narrative contexts by element:** `python3 utils/extract-reference-names.py <file>.json --context-element "Common Pitfalls"` (shows all contexts for a specific narrative element across all narratives)
- **Long narrative contexts:** `python3 utils/extract-reference-names.py <file>.json --long-contexts` (lists contexts exceeding 3 sentences, sorted by length, truncated)
- **Long contexts with full text:** `python3 utils/extract-reference-names.py <file>.json --long-contexts --full-text` (full context text, no truncation)
- **Context element with full text:** `python3 utils/extract-reference-names.py <file>.json --context-element "Common Pitfalls" --full-text` (full text, no truncation)
- **Pattern details with narratives:** `python3 utils/extract-reference-names.py <file>.json --sections patterns --narrative-content`
- **Parent activity narratives:** `python3 utils/extract-reference-names.py <parent>.json --sections activities --activity-details` (narrative types and elements per activity)
- **Baseline/parent summary:** `python3 utils/extract-reference-names.py <baseline-or-parent>.json` (summary, focuses, alphas, activitySpaces, competencies, narrativeTypes)
- **Cross-reference validation:** `python3 utils/assess-practice.py <file.json>` (internal crossrefs: activity→alpha/state, worksOn→workProduct/LOD, involves→personaGroup, citationNames, pattern evidenceBy→workProduct/LOD, narrative types)
- **Baseline reference validation:** `python3 utils/assess-practice.py <file.json> --baseline <baseline.json>` (focuses, activitySpaces, competencies, competency levels, narrative types, contributesTo targets, alias targets)
- **Full assessment:** `python3 utils/assess-practice.py <file.json> --baseline <baseline.json> --schema deps/language.schema.json`
- **Compare two versions:** `python3 utils/diff-practice-json.py old.json new.json` (structural diff: count deltas, added/removed elements, keyword/tag changes)
- **Compare (changes only):** `python3 utils/diff-practice-json.py old.json new.json --changes-only`
- **Assessment with parent:** `python3 utils/assess-practice.py <file.json> --baseline <baseline.json> --parent <parent.json>` (merges parent alphas/narrativeTypes/competencies/activitySpaces into baseline for validation)
- **Assessment summary:** `python3 utils/assess-practice.py <file.json> --summary` (counts by severity/category, suggested mode — no full issue list)
- **Errors-only assessment:** `python3 utils/assess-practice.py <file.json> --errors-only` (filter to only severity=error issues — useful in fix loops)
- **Top-level structure overview:** `python3 utils/extract-reference-names.py <file>.json --structure` (shows type and count/length for each top-level key)
- **Cross-practice method audit:** `python3 utils/audit-method-references.py <method>.json --baseline <baseline>.json` (checks alpha/state refs, duplicates, persona consistency across practices)
- **Cross-practice audit (JSON):** `python3 utils/audit-method-references.py <method>.json --baseline <baseline>.json --json`
- **Add missing alpha redeclaration:** `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --add-redeclaration "Alpha Name" [--fix]`
- **Remap alpha references:** `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remap "Old Alpha" "New Alpha" --state-map '{"OldState":"NewState"}' [--fix]`
- **Remove alpha and references:** `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remove-alpha "Alpha Name" [--fix]`
- **Resolve transitive deps:** `python3 utils/discover-dependencies.py --resolve-from <file>.json --transitive` (find all baselines + practices in dependency tree)
- **Package into .keleo:** `python3 utils/package-keleo.py --name "name" --version "1.0.0" --description "..." --documents baseline.json dep1.json dep2.json p1.json p2.json --method-name "Method Name" --method-narrative-file narratives.json -o bundles/name.keleo --verify` (list ALL transitive deps in topological order, never use `_effective-context.json`)
- **Package single practice:** `python3 utils/package-keleo.py --name "name" --version "1.0.0" --description "..." --documents baseline.json [transitive-deps.json ...] practice.json -o bundles/name.keleo --verify`
- **Convert embedded method to .keleo:** `python3 utils/package-keleo.py --from-embedded method.json --baseline baseline.json -o bundles/method.keleo --verify`
- **Verify existing package:** `python3 utils/package-keleo.py --verify-only bundles/name.keleo`
- **Extract method narratives:** `python3 utils/extract-practice-content.py <method>.json --extract-narratives <output>.json` (for package-keleo.py --method-narrative-file)

Mapping guide assembly and validation:
- **Assemble method mapping guide:** `python3 utils/assemble-mapping-guide.py --name "Name" --baseline-name "Baseline" --guides g1.md g2.md -o output.md --stats` (auto-generates method header with practice summary table)
- **Assemble with parent:** `python3 utils/assemble-mapping-guide.py --name "Name" --baseline-name "Baseline" --parent-name "Parent" --guides g1.md g2.md g3.md -o output.md`
- **File statistics:** `python3 utils/validate-phase-output.py --stats g1.md g2.md g3.md` (word/line/size counts for each file)
- **Validate pattern views:** `python3 utils/validate-phase-output.py --phase 2 --validate-patterns guide.md` (checks alpha presence in every view, state validity, max 2 states per alpha per view)

JSON patching (write operations):
- **Set a top-level key:** `python3 utils/patch-practice-json.py <target>.json --set-key assets --patch-file assets.json`
- **Merge keys at root:** `python3 utils/patch-practice-json.py <target>.json --patch-file patch.json` (merges all keys from patch into target)
- **Append to array:** `python3 utils/patch-practice-json.py <target>.json --append-key assets --patch-file more-assets.json`
- **Patch a named element:** `python3 utils/patch-practice-json.py <target>.json --element-path "alphas[Platform]" --patch-file patch.json`
- **Patch by field match:** `python3 utils/patch-practice-json.py <target>.json --element-path "activities[My Activity].narratives[0].narrativeContexts[narrativeElementName=Common Pitfalls]" --patch-file patch.json` (use `field=value` in brackets to match on any field)
- **Create new file from patch:** `python3 utils/patch-practice-json.py <new>.json --patch-file skeleton.json --create`
- **Delete a top-level key:** `python3 utils/patch-practice-json.py <target>.json --delete-key kind`
- **Deep find-and-replace:** `python3 utils/patch-practice-json.py <target>.json --replace "old text" "new text"` (recursive through all string values)
- **Bulk replacements:** `python3 utils/patch-practice-json.py <target>.json --replace-file replacements.json` (JSON array of `["old", "new"]` pairs)
- **Rename element (with reference update):** `python3 utils/patch-practice-json.py <target>.json --rename-in activities "Old Name" "New Name"` (renames element AND all string references throughout JSON)
- **Set key with inline value:** `python3 utils/patch-practice-json.py <target>.json --set-key narratives --value '[{"name":"..."}]'` (avoids temp files for simple values)
- **Preview without writing:** Add `--dry-run` to any command above

These commands work on ANY JSON file — practice, method, baseline, `_effective-context.json`, or `_effective-context.json`. This rule applies to subagents too. If a subagent needs to inspect or modify JSON structure, it must use these utilities.

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

**Rule:** A practice should only declare a dependency on a parent practice if it actually references an alpha that is **uniquely defined** in that parent practice — i.e., an alpha that exists in the parent but NOT in the effective baseline. Baseline alphas that are merely **redeclared** by a parent practice do NOT create a dependency.

**Algorithm (apply per practice after Phase 3 JSON generation):**

1. **Collect `contributesTo` and `mapsTo` targets** from all alphas in the practice
2. **Filter out practice-local targets** (alphas defined within the same practice)
3. **For each remaining target**, classify it:
   - **Baseline alpha** (`_contributingPracticeName` points to a baseline in `_provenance.tiers.baselines`): no dependency created
   - **Practice-only alpha** (`_contributingPracticeName` points to a practice in `_provenance.tiers.practices`): creates dependency on that contributing practice
4. **Set `practiceDependencyNames`** to the deduplicated list of contributing practices that own at least one referenced practice-only alpha. If no practice-only alphas are referenced, set to `[]`.

**Using `_contributingPracticeName` for dependency determination:**
The effective context annotates every element with its source. When your new practice references an alpha via `contributesTo`/`mapsTo`, check that alpha's `_contributingPracticeName` and cross-reference with `_provenance.tiers`:
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
- ❌ **Citations missing URLs** — every citation SHOULD have a `url` field. Use user-provided URLs, official framework websites, DOI references (`https://doi.org/10.xxxx/xxxxx`) for academic works, or publisher catalog pages. Only omit when no stable public link exists. Never fabricate URLs.
- ❌ Missing acknowledgements — if source methodology credits specific contributors or supporting organizations, include an `acknowledgements` array (distinct from citations — attributes human contributions rather than published works)
- ❌ **Incomplete activity coverage** (must include ALL activities identified, not just 1-2 examples)
- ❌ **Not identifying concern relationships** - Missing production flows, enablement patterns, governance structures, information flows between concerns
  - **Fix:** Explicitly analyze how concerns interact: what produces what, what enables what, what governs what
  - Document these relationships in concern analysis for Phase 2 mapping

### Phase 2 Pitfalls

- ❌ Not reading semantics.md before mapping
- ❌ Creating floating alphas (missing `contributesTo` or `mapsTo`)
- ❌ **Missing or insufficient terminology aliases** - Saying "no aliases needed" when source uses domain-specific vocabulary
  - **Fix:** Review source for domain canonical terms differing from baseline
  - Examples: "Playbook" (vs Deployment Documentation), "Execution Environment" (specialized alpha)
  - Target: 3-8 aliases per practice
  - **ONE alias per element** - if multiple terms exist, use instances/specializations instead
- ❌ **Multiple aliases for same element** - Creating Platform → "AAP", Platform → "Automation Controller", Platform → "Automation Platform"
  - **Fix:** Distinguish synonyms vs facets vs deployments
  - **Synonyms/acronyms** → keywords: "AAP", "automation platform", "ansible automation platform"
  - **Facets/components** → specializations: "Automation Controller", "Automation Hub", "Execution Environment" (new alphas with `contributesTo`)
  - **Named variants** → variant mappings: "AI-Ready Enterprise", "IT Operations Efficiency" (new alphas with `mapsTo` — same states as parent)
  - **Different deployments** → instances: "Production AAP", "Staging AAP", "Development AAP" (same behavior, different tracking)
  - Do NOT create multiple aliases for one baseline element
- ❌ **CRITICAL: `contributesTo`/`mapsTo` only references baseline** - Forgetting that these can reference practice-local alphas (internal hierarchy) or external practice alphas (cross-practice dependency)
  - **Fix:** Consider all three target options: baseline, practice-local, external practice
  - Use State Alignment Heuristic to find best parent across all three sources
  - Choose `contributesTo` (different states) vs `mapsTo` (exact same states, IS-A variant)
  - Document practice dependencies when using external practice references
- ❌ **Using `contributesTo` when `mapsTo` is appropriate** - Alpha has identical state progression as parent and IS-A semantics apply
  - **Fix:** If states match exactly and the concept IS a named variant of the parent → use `mapsTo`
  - Example: "AI-Ready Enterprise" IS a "Sales Play" with same states → `mapsTo`, not `contributesTo`
  - Example: Specific TDPs that follow the same "Technical Decision Point" lifecycle → `mapsTo`
- ❌ **Setting both `mapsTo` and `contributesTo` on same alpha** - These are mutually exclusive
  - **Fix:** Choose one based on state progression match and IS-A semantics
- ❌ **Repeating parent type name in `mapsTo` alpha names** - "AI-Ready Enterprise Play" (redundant "Play"), "Container Management TDP" (redundant "TDP")
  - **Fix:** Since `mapsTo` reads as "is a type of", drop the parent type from the name: "AI-Ready Enterprise" (is a Sales Play), "Container Management" (is a Technical Decision Point)
  - This applies to both alpha `name` and any `aliasName`
  - Does NOT apply to `contributesTo` alphas — including the type in specialization names is fine
- ❌ **Not using baseline relatesTo for alpha analysis** - Ignoring existing semantic relationships when analyzing baseline alphas
  - **Fix:** Read baseline alpha's `relatesTo` array to understand dependencies, production, governance patterns
  - Use relationships to inform how the alpha fits in the practice's value stream
  - Example: "Platform" is "governed by" Platform Governance → include governance activities in practice
- ❌ **Adding relatesTo to redeclarations** - Enriching baseline alphas should NOT add new relationships
  - **Fix:** Only define `relatesTo` on NEW alphas (specializations), not redeclarations
  - Redeclarations inherit baseline relationships automatically
- ❌ **Missing relatesTo on new alphas** - New specialized alphas lack semantic relationships to peer alphas
  - **Fix:** Review Phase 1 concern interactions and map to relatesTo arrays
  - Define domain-specific relationships using appropriate verbs from semantics.md Section 6.1
  - Every relatesTo entry MUST include `direction` (`outgoing`, `incoming`, or `mutual`) — required by schema
  - Optionally include `description` to explain why the relationship exists
  - Example: `{ "relationship": "produces", "alphaName": "Platform Asset", "direction": "outgoing", "description": "Capabilities produce consumable platform assets" }`
- ❌ **Using vague relationship verbs** - Generic "relates to" instead of specific relationship types
  - **Fix:** Use domain-appropriate verbs: "produces", "enables", "guides", "validates", "constrains", "provides", "hosts"
  - Prefer active voice from provider perspective
- ❌ **Missing `direction` field on relatesTo entries** - Schema requires `direction` on every AlphaRelationship
  - **Fix:** Add `direction` field: `outgoing` (this alpha acts on target), `incoming` (target acts on this), `mutual` (symmetric)
  - Common mappings: "produces"/"enables"/"constrains"/"depends on" → `outgoing`; "governed by"/"built by"/"validated by" → `incoming`
- ❌ **Wrong relationship directionality** - Alpha declares dependencies instead of provisions
  - **Fix:** Flip perspective - alpha should declare what it provides TO others, not what it needs FROM others
  - "Platform enables Software System" not "Software System depends on Platform"
  - Use `direction: "outgoing"` for active relationships, `direction: "incoming"` for passive
- ❌ **Using invalid competency level names** - Using descriptive names instead of exact baseline CompetencyLevel.name values
  - **Fix:** Extract valid level names from baseline: `python3 utils/extract-reference-names.py <baseline>.json --sections competencies`
  - Use EXACT level names from baseline (case-sensitive)
  - Common errors: "Advanced" (check baseline), "Expert" (check baseline), "Intermediate" (check baseline)
  - For Platform Adoption Essentials: use "Basic", "Applies", "Masters", "Adapts", "Innovating"
  - **Validate BEFORE Phase 3:** Check all competencyLevelName values in mapping guide against baseline
- ❌ Using competency descriptions instead of exact baseline names
- ❌ Using alias names in structural references (use canonical names)
- ❌ Wrong alpha approach (should use redeclaration vs specialization vs variant mapping framework)
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

- ❌ **`focusName` missing on activities** — Every activity MUST have a `focusName` property derived from its activity space's focus mapping
- ❌ **`involves` as object array instead of string array** — `involves` on activities is a `string[]` of persona group names, NOT an array of objects
- ❌ **`alphaName`/`focusName` on work products** — Work products do NOT have `alphaName` or `focusName` properties; they use `contributesTo` on LODs to link to alpha states
- ❌ **`seq` on activities** — Activities do NOT have a `seq` property (unlike checklists and LODs)
- ❌ **`citationNames` on activities** — Activities do NOT have `citationNames`; use citation references in activity narratives instead
- ❌ **`instanceName` on work product instances** — Use `name` not `instanceName` for `workProductInstances` entries
- ❌ **Duplicate alpha states in pattern views** — Each alpha MUST target at most 1 state per PatternView; deduplicate before generating
- ❌ Not reading language.schema.json before generating
- ❌ **PracticeElement name collisions** - CRITICAL ERROR - Using same name for different element types
  - **Problem:** Alpha "Platform Configuration" + WorkProduct "Platform Configuration" = INVALID (names must be globally unique)
  - **Detection:** Run `python3 utils/assess-practice.py <file>.json` (uniqueness check included)
  - **Fix:** Rename more specific element with disambiguating suffix:
    - WorkProduct collision: Add "File", "Document", "Template" (e.g., "Platform Configuration" → "Platform Configuration File")
    - Activity collision: Add verb prefix (e.g., "Platform" → "Configure Platform")
    - Pattern collision: Add "Pattern", "Journey" (e.g., "Delivery" → "Delivery Journey")
  - **Update references:** Search and replace all references to renamed element (workProductName, activityName, etc.)
  - **Common culprit:** Alphas and WorkProducts sharing names (alpha is usually concept, work product is the artifact)
- ❌ **Missing `kind` property at root level** - MOST COMMON ERROR
  - **Fix Practice JSON:** Add `"kind": "practice"` at root level (conventionally first property for readability)
  - **Fix Method JSON:** Add `"kind": "method"` at root level
  - **Check EVERY practice in method:** `python3 utils/assess-practice.py <file>.json` - validates kind on root and all embedded practices
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
  - **Validate:** `python3 utils/assess-practice.py <file>.json --baseline <baseline>.json`
- ❌ Wrong competency reference format ({competencyName, level} instead of {competencyName, competencyLevelName})
- ❌ Using `requiredCompetencies` on personas (should be `competencies`)
- ❌ Missing BOTH `requiredCompetencies` AND `recommendedCompetencyLevels` on activities
- ❌ **Missing `activitySpaceName` property on activities** (required for flat Practice.activities)
- ❌ Wrong PatternView property names (`alphas` instead of `alphaStates`, `views` instead of `patternViews`)
- ❌ Missing contributesTo on LODs
- ❌ **Invalid alphaName in relatesTo** - Relationship references non-existent alpha
  - **Fix:** Validate every relatesTo.alphaName against defined alphas in baseline and practice
- ❌ **Missing relatesTo on new alphas from mapping guide** - Mapping specifies relationships but JSON omits them
  - **Fix:** Copy relatesTo array from mapping guide to JSON for all new alphas
- ❌ **Using `rationale` instead of `description` in relatesTo** - `rationale` is not a valid schema field
  - **Fix:** Rename `rationale` to `description` (optional field for explaining the relationship)
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
- ❌ **Wrong Gherkin property placement** - Adding `test`/`examples` to elements that don't support them
  - **Fix:** `test` and `examples` are ONLY valid on Checklist items and Activities. `background` is valid on State, LevelOfDetail, ActivitySpace, and Activity.
- ❌ **Gherkin `test` missing PracticeElement fields** - Test extends PracticeElement, so requires `name` and `description`
  - **Fix:** Every `test` object must include `name` (string) and `description` (string) alongside optional `given`/`when`/`then` arrays
- ❌ **Duplicating structural relationships in Gherkin** - Activity `test.then` repeating what `contributesTo`/`worksOn` already declares
  - **Fix:** `test.then` should capture human-readable outcomes that complement (not duplicate) structural references
- ❌ **Background as string or array** - `background` must be an object with optional `given`, `alphaStates`, `workProductLevels` arrays
  - **Fix:** Use `{"given": [...], "alphaStates": [...]}` structure
- ❌ **Invalid `partOf` on work products** - Self-reference, circular chain, or unresolvable target
  - **Fix:** `partOf` must reference a valid WorkProduct.name in the same practice, a dependency, or the baseline. No self-references. No cycles (A partOf B, B partOf A). Keep one level deep.

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

**Step 5: Cross-Baseline Alpha Bindings (`alphaBindings`)**

When a method composes practices from **different baseline families** (e.g., Platform Adoption Essentials + Partner Ecosystem Essentials), use `alphaBindings` at the method level to declare cross-baseline contribution relationships.

`alphaBindings` is an array on the Method object. Each entry declares that alphas from one baseline contribute to an alpha in another baseline:

```json
"alphaBindings": [
  {
    "baselineAlpha": {
      "baselineName": "Partner Ecosystem Essentials",
      "alphaName": "Partner Engagement"
    },
    "contributingAlphas": [
      {
        "baselineName": "Platform Adoption Essentials",
        "alphaName": "Stakeholders",
        "stateContributions": [
          { "fromState": "Recognized", "toState": "Identified" },
          { "fromState": "Involved", "toState": "Active" }
        ]
      }
    ]
  }
]
```

**When to use:**
- Method composes practices from 2+ different baselines
- Alphas from different baselines have natural contribution relationships
- These bindings are post-merge metadata — consumed AFTER merge produces the unified document

**When NOT to use:**
- Single-baseline methods (use `contributesTo` on alphas instead)
- Within-baseline relationships (use `contributesTo` or `relatesTo`)

**Rules:**
- Each `baselineName` must reference an accessible baseline
- Each `alphaName` must exist in that baseline
- State names in `stateContributions` must be valid for the respective alphas
- `stateContributions` is optional — alpha-level binding without state mapping is valid
- Bindings are additive — they don't replace existing `contributesTo` relationships

**Examples:**

**Example 1: Multi-Practice Method (CORRECT)**
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

**Example 2: "Everything Else" Anti-Pattern (INCORRECT)**
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

**Example 3: Orchestration Practice (CORRECT)**
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
 ✓ bundles/<name>.keleo (schema-compliant package)

Package contents:
 ✓ manifest.json
 ✓ documents/<baseline>.json (practiceBaseline)
 ✓ documents/<practice>.json (practice) [× N for methods]
 ✓ documents/<method>.json (method, entry point) [methods only]

Validation summary:
 ✓ Schema compliance: PASS
 ✓ Baseline references: PASS
 ✓ Internal integrity: PASS

Package is ready for use in Practice Language consuming systems."

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

**Asset Validation:** Covered by `eval-skill-output.py` assertion `qual:asset-coverage` (checks icon asset presence on elements and assetName resolution).

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
- No floating alphas (all new alphas have `contributesTo` or `mapsTo`)
- Orthogonal tags throughout
- Single-sentence descriptions

---

## Post-Completion Review (MANDATORY)

**After completing the skill workflow OR after completing planning**, review the session for optimisation opportunities:

1. **Audit ad-hoc commands**: Did the user have to confirm execution of any commands or scripts that weren't auto-approved? Look for:
   - Permission prompts for Bash commands not in the project's `.claude/settings.json` allow list
   - Inline `python3 -c` or `bash -c` scripts that should have been reusable utils
   - Shell patterns (heredocs, loops, process substitution) that triggered prompts
   - External tool calls (e.g., `unzip`, `zip`, `curl`) that could be absorbed into existing utils

2. **Identify missing utils**: Did you have to write any ad-hoc logic that could be generalised into a reusable utility script in `utils/`?

3. **Propose fixes** (present to user, don't apply unilaterally):
   - **Permission gaps**: Suggest adding auto-allow entries to `.claude/settings.json`
   - **Missing utils**: Propose new utility scripts or extensions to existing ones
   - **Skill improvements**: Suggest skill instruction updates to prevent the ad-hoc pattern in future runs

4. **Report**: Briefly tell the user what you found and what you'd recommend changing. If nothing was found, say so — a clean session is a good signal.
