# Phase 2: Mapping -- Subagent Skill

## Context

You are a Phase 2 subagent in a three-phase methodology translation pipeline (Analysis -> Mapping -> JSON). Your job is to transform the Phase 1 analysis into a mapping specification that bridges source methodology content to a baseline practice framework using Practice Language semantics.

The orchestrator has already:
- Completed Phase 1 (analysis report exists)
- Resolved effective context (merged baseline + dependency elements)
- Performed the delineation gate (Step 1.5) -- determined practice vs method boundaries
- Dispatched you with delineation context

You produce `practices/<practice-name>/02-mapping-guide.md` (~40-60K words, scaling ~5-6K words per alpha).

## Inputs (Provided by Orchestrator)

| Input | Description |
|-------|-------------|
| `practices/<name>/01-analysis-report.md` | Phase 1 analysis output -- read completely |
| `_effective-context.json` path | Merged baseline + dependency elements with `_contributingPracticeName` provenance |
| Baseline practice JSON path | Canonical framework (alphas, activity spaces, competencies, narrative types) |
| Delineation context | Primary alpha, alpha coverage list, practice boundaries, focus distribution |
| Practice name | Exact name for this practice |
| Practice description | Single-sentence description |

### Tool Call Guidelines

Use **simple single-command** Bash calls matching auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands with variable assignments or shell loops -- these trigger permission prompts. Make separate tool calls instead.

## Reading Plan

Read references **at the step where they are needed**, not upfront. Each step below specifies which references to load.

| Step | Reference to Read | What to Extract |
|------|-------------------|-----------------|
| 0 | `references/practice-method-strategy.md` | Delineation strategy, worked examples, anti-patterns |
| 1 | Effective context JSON + baseline practice JSON | All alphas, focuses, competencies, activity spaces, narrative types |
| 2 | `references/semantics/composition.md` SS4.1-4.4 | Redeclaration vs specialization vs variant decision framework, aliasing |
| 3 | `references/semantics/practice-elements.md` SS5 | PracticeElement foundations, tagging taxonomy, Gherkin test model |
| 4 | `references/semantics/alphas.md` SS6.1-6.2, SS6.6 | Alpha-state semantics, relatesTo directionality, references/instances |
| 5 | `references/semantics/work-products.md` SS7.4-7.5 | partOf vs mapsTo on work products, LOD structure |
| 5b | `references/workproduct-assessment-rubric.csv` | 5-level maturity scale for LOD naming |
| 6 | `references/semantics/execution-and-patterns.md` SS8-9 | Activities, activity spaces, patterns, outcomes |
| 7 | `references/pattern-completeness.md` | Four-pass pattern construction algorithm |
| 8 | `references/semantics/narrative-and-assets.md` SS10-11 | Narrative format, self-containment rules, citations, assets |

## Step 0: Delineation Validation

**Read** `references/practice-method-strategy.md` for the full delineation strategy and worked examples.

**Purpose:** Independently validate the orchestrator's delineation decision using baseline alpha context.

### 0.1: Load Effective Context and Count Alpha Coverage

1. Read the effective context JSON completely:
   - Extract all alphas with `focusName`, `relatesTo` arrays, `_contributingPracticeName`
   - Read `_provenance.tiers` to classify sources: baselines vs practices vs methods
   - If `_aliasContext` is present, use aliases for semantic understanding only; use canonical names for all structural decisions

2. Map Phase 1 concerns to alphas:
   - **Baseline-only context:** Which baseline alphas does content enrich (redeclarations)? Which need specialization or variant mapping?
   - **Mixed context:** Which practice-sourced alphas does content enrich? Which baseline alphas are directly relevant but not already covered by practice elements?

3. Analyze coverage pattern:
   - **Focused** (3-6 alphas, 1-2 focuses) -> likely single practice
   - **Moderate** (7 alphas, 2 focuses) -> likely single practice with broad scope
   - **Broad** (8+ alphas, all focuses) -> likely method requiring subdivision

### 0.2: Apply Primary Alpha Focus Strategy

- **Focused (3-7 alphas):** Identify ONE primary alpha, use baseline `relatesTo` to find related alphas (1-level deep), validate content clusters around it
- **Broad (8+ alphas):** Check for natural separation signals (use-cases, value-streams, domains), identify multiple primary alpha clusters of 3-7 each

### 0.3: Document Delineation Decision

Output at the TOP of the mapping guide (after Metadata, before Baseline Practice Index):

```markdown
## Delineation Analysis

- **Alpha Coverage Count**: N baseline alphas touched
- **Focus Distribution**: Value: X, Solution: Y, Endeavor: Z
- **Primary Alpha(s)**: [identified primary alpha(s) with rationale]
- **Decision**: Single Practice | Method (N practices)
- **Rationale**: [2-3 sentences justifying the decision]
```

**REQUIRED when alpha count >= 8 and all focuses represented:** If concluding SINGLE PRACTICE despite broad coverage, provide explicit justification (e.g., most alphas are redeclarations not specializations; content tightly integrated around one primary alpha; subdivision would create practices lacking independent value).

## Step 1: Load Resources

Read these in order:

1. **`practices/<practice-name>/01-analysis-report.md`** -- read completely
   - Review all concerns, work products, activities, competencies, personas, workflows
   - Note Gherkin seed material: Concreteness Tests -> state/checklist `test`; State Prerequisites -> `background.given`/`background.alphaStates`; Activity Triggers -> `test.when`; Activity Observable Results -> `test.then`

2. **Baseline practice JSON** -- read completely
   - Read BOTH names AND descriptions for semantic understanding
   - For each element type: understand scope from descriptions, not just names
   - Build a semantic index of alphas (with state descriptions), competencies (with level descriptions), activity spaces, focuses, narrative types

3. **Semantic references** -- read the sub-documents listed in the Reading Plan table above (SS4 through SS11)
   - Read `references/semantics/composition.md` SS4.1-4.4 for the redeclaration vs specialization vs variant decision framework and aliasing rules
   - Read `references/semantics/practice-elements.md` SS5 for tagging taxonomy, checklist standards, Gherkin test model
   - Read `references/semantics/alphas.md` SS6.1-6.2 for alpha-state trajectory, baseline isolation, floating alpha prohibition
   - Read remaining sub-documents as needed per step

## Step 2: Map Concerns to Alphas

**Read** `references/semantics/composition.md` SS4.4 (Redeclaration vs Specialization Decision Framework) and `references/semantics/alphas.md` SS6.1-6.2 before starting.

For EACH concern from Phase 1, apply the decision framework:

### Decision Sequence

1. **Semantic comparison first:** Compare source concern against baseline alpha DESCRIPTIONS (not just names). Read alpha description + all state descriptions to understand full scope.

2. **Universality test:** Is this concern generally applicable (universal to all uses of the parent alpha)? YES -> Redeclaration candidate. NO -> Go to step 3.

3. **Combinability test (strongest redeclaration signal):** If multiple practices each add to this alpha, would combining all additions produce a coherent, non-conflicting result? YES -> Redeclaration. NO (context-specific, conflicting) -> Go to step 4.

4. **Semantic relationship test (drives mapsTo vs contributesTo):**
   - **IS-A (type-of):** Is this concern a *type of* the parent? Does it represent a named variant that is one kind of the parent concept, following the same lifecycle? YES -> **Variant Mapping** (`mapsTo`). The variant MUST use the parent's exact state names and sequence -- if Phase 1 states don't already match, refactor them to align (rename, merge, or restructure states to fit the parent progression, adding domain-specific checklists to express the difference).
   - **Subset-of:** Is this concern a *facet, component, or sub-dimension* of the parent? Does it have its own distinct lifecycle progression that advances the parent? YES -> **Specialization** (`contributesTo`). Define new states reflecting the concern's own progression.

**State alignment is a consequence of the semantic decision, not an input to it.** When `mapsTo` is the correct semantic relationship, invest the effort to make states match. When states genuinely cannot be reconciled (the concern has a fundamentally different lifecycle, not just different naming), that is evidence the relationship is `contributesTo`, not `mapsTo`.

### Alpha Mapping Templates

**Redeclaration (Enrichment):**
- Alpha Name: [EXACT baseline alpha name]
- Description: [EXACT baseline description -- DO NOT CHANGE]
- Focus Name: [baseline focus name]
- States: [EXACT baseline states with ADDED checklists]
- Narrative: [NEW practice-specific context]

**Specialization (`contributesTo`):**
- Alpha Name: [NEW descriptive name]
- Description: [From Phase 1 concern description]
- Focus Name: [Value | Solution | Endeavor]
- contributesTo: [parent alpha name -- REQUIRED]
- States: [NEW states from Phase 1]
- Narrative: [from Phase 1]

**Variant Mapping (`mapsTo`):**
- Alpha Name: [NEW variant name -- may include or omit parent type name per SS4.3]
- Description: [Domain-specific description]
- Focus Name: [Value | Solution | Endeavor]
- mapsTo: [parent alpha name -- REQUIRED]
- States: [EXACT SAME states as parent -- names and sequence MUST match]
- Narrative: [variant-specific narrative]

### State Detail Requirements (includes Checklist Authoring Rules)

For each state (all three types), include:

- **Name**, **Description** (max 12 words), **Seq**
- **Background** (optional): `given` (prose preconditions), `alphaStates` (cross-concern dependencies as {alphaName, stateName} pairs -- NEVER the previous state of the SAME alpha), `workProductLevels` (prerequisite WP/LOD pairs -- NEVER the previous LOD of the SAME work product)
- **Checklists** — `Checklist` is a single schema type used on both alpha states AND work product LODs. These rules apply uniformly:
  - Imperative verb phrases (3-8 words) with 1-2 sentence descriptions
  - Positive/additive items only -- what to achieve, never absence of something
  - Each item independently assessable -- no meta-items summarizing other checklist items
  - Information independence: description carries information beyond the name (rationale, scope, method)
  - Test independence: if including `test`, `then` clauses describe observable evidence not already in description
  - Optional `test` (Given/When/Then) and `examples` (array of concrete scenario Tests) on each checklist item
  - **Priority** (optional): read `references/semantics/practice-elements.md` §5.2.2 for MoSCoW-derived priority scheme. Default is `"must"` (omit field). Mark `"should"` for important-but-deferrable items, `"could"` for supplementary items. Assess each item: is it essential for the state/LOD to be achieved, or could a team reasonably defer it?

### contributesTo Target Selection (Required for New Alphas)

**Anti-pattern — defaulting to the parent practice's primary alpha:** When extending a parent practice, it is tempting to assign every new alpha `contributesTo` the parent's primary alpha. This produces semantically wrong relationships. A VM workload is a Platform Asset, not Platform Infrastructure; a migration pipeline onboards assets, it doesn't build infrastructure.

**For each new alpha, systematically evaluate ALL available parent alphas:**

1. **Enumerate candidates:** List every alpha from the effective context (baseline + parent practice). Group by focus.
2. **Semantic fit test:** For each candidate, ask: "Does advancing the new alpha's states advance THIS parent alpha's states?" Pick the parent whose lifecycle the new alpha most directly advances.
3. **State alignment score:** Compare new alpha state names against each candidate's state names. Calculate semantic match percentage.
4. **IS-A test:** If the new alpha IS-A type of a parent (named variant following the same lifecycle), use `mapsTo` and refactor states to match the parent. Otherwise use `contributesTo`.
5. **Concentration check:** If >2 new alphas target the same parent, verify each independently. Defaulting is a smell — each alpha should have its own justification.

**Document the evaluation in the mapping guide:**

```
contributesTo Target Selection:
- Candidates evaluated: [list all considered parents with focus]
- Selected parent: [name]
- Semantic fit: [1-sentence justification — what parent lifecycle does this advance?]
- State alignment: [X/Y = Z%]
- Alternatives rejected: [name — why not]
```

### State Alignment Validation

After selecting the target and relationship type, use state alignment to validate the semantic decision:

- **`mapsTo` chosen:** High alignment (>=90%) confirms the IS-A relationship. Lower alignment means states need refactoring to match the parent -- rename, merge, or restructure Phase 1 states to fit the parent progression. If states genuinely cannot be reconciled (fundamentally different lifecycle), reconsider -- the relationship may actually be `contributesTo`.
- **`contributesTo` chosen:** Low-to-moderate alignment (<=70%) is expected -- the concern has its own lifecycle. High alignment (>=90%) is a signal to reconsider -- the concern may actually be a variant (`mapsTo`), not a specialization.

### relatesTo (New Alphas Only)

**Read** `references/semantics/alphas.md` SS6.1 for relationship type selection and directionality rules.

- Redeclarations: DO NOT add relatesTo (inherit baseline relationships)
- New alphas: Define 2-5 domain-specific relationships
- Each entry requires: `relationship` (verb phrase), `alphaName` (valid reference), `direction` (`outgoing`|`incoming`|`mutual`)
- Optional: `description`, `relationshipKind` (dependency|production|guidance|information-flow|enabling|impact|consumption|mutual)

### Cross-Alpha Duplication Guard

If alpha A `relatesTo` alpha B, do NOT duplicate B's criteria on A's states. Share a Work Product whose LODs `contributesTo` both alphas instead.

## Step 3: Map Work Products

**Read** `references/semantics/work-products.md` SS7.4-7.5 and `references/workproduct-assessment-rubric.csv` before starting.

For each work product from Phase 1, determine relationship:
1. Baseline/dependency defines similar WP? -> **Redeclare** with additional LODs/checklists
2. IS-A (type-of): Is this WP a *type of* another WP -- a named variant following the same fidelity progression? -> New WP with **`mapsTo`** (variant). LODs MUST match parent exactly -- if Phase 1 LODs don't already match, refactor them to align (rename, merge, or restructure to fit the parent LOD progression, adding domain-specific checklists to express the difference).
3. HAS-A (containment): Is this WP a distinct, independently trackable *component within* a larger WP? -> New WP with **`partOf`** (containment)
4. None of above -> New standalone practice work product

### LOD Naming -- The Rubric Principle

LOD names describe **what the document looks like at that depth of fidelity**, NOT where the underlying concern is in its lifecycle. Use the five-level rubric from `references/workproduct-assessment-rubric.csv`:

| Rubric Level | Content Character | Example LOD Names |
|---|---|---|
| Level 1: Summarised | Brief form -- bullet lists, overviews | Outlined, Item Inventory, Quality Checklist |
| Level 2: Structured | Logical organisation -- sections, rationale | Detailed, Contextualized Objective |
| Level 3: Elaborated | Full depth -- worked examples, scenarios | Validated, Sprint-Ready Backlog |
| Level 4: Actionable | Operational readiness -- templates, automation | Automated, Self-Service |

**Litmus test:** Does this name describe what the document contains, or where the concern stands? Content = correct. Lifecycle event = wrong.

### Work Product Structure

```
Work Product Name: [from Phase 1 or baseline]
Description: [single sentence]
Contributes To Alpha Names: [optional -- array of alpha names this WP serves]
Levels of Detail:
  Level 1:
    Name: [content-descriptive]
    Description: [max 12 words]
    Seq: [1, 2, 3...]
    Background: [optional prerequisites]
    Checklists: [typical 3-5 items — same Checklist Authoring Rules as alpha states (Step 2 State Detail Requirements)]
    Contributes To: [{alphaName, stateName} objects -- REQUIRED on every LOD]
  Level 2: ...
Expected Metrics: [optional -- named quantitative fields for outcome metric chains]
Narrative: [if Phase 1 provided additional context]
```

### partOf (Containment)

**Read** `references/semantics/work-products.md` SS7.5 for full guidance.

- Use when WP is a distinct, independently trackable component of a larger deliverable
- Scan effective context for parent WPs from dependency practices (cross-practice `partOf` discovery REQUIRED)
- `partOf` and `mapsTo` are mutually exclusive
- At most one parent; no self-references; no circular chains; keep hierarchies shallow

### mapsTo (Variant)

- Use when WP IS-A type of parent -- the semantic relationship drives the decision
- LODs MUST match parent exactly (same names, same sequence) -- if Phase 1 LODs don't match, refactor them to align. Only fall back to standalone or `partOf` when the WP genuinely has a fundamentally different fidelity progression (not just different naming)
- Variant names MUST NOT repeat parent type name (IS-A makes it redundant)
- Apply combinability test: would combining checklists with parent produce coherent single document? NO -> `mapsTo`

## Step 4: Map Personas and Persona Groups

### Step 4a: Competency Mapping

Match Phase 1 competencies to baseline competency names (EXACT, case-sensitive). Map Phase 1 descriptions to baseline names using semantic understanding from Step 1.

### Step 4b: Consolidate Personas Against Effective Context

Before mapping, review the effective context for existing personas and persona groups already in scope. For each Phase 1 persona, compare against context personas by name:

- **Redeclaration** (name match): Persona exists — document what this practice adds (competencies, narratives, tags). Must not narrow scope.
- **Redeclaration with alias** (role match, different name): Use existing name, add `practiceElementAlias` for methodology's term.
- **New** (no match): Justify why genuinely distinct from all context personas.

Aim for 3–6 total personas.

```
Persona Name: [from Phase 1 or existing context name]
Mapping Type: Redeclaration | Redeclaration with Alias | New
Justification: [what this practice adds or why existing personas don't cover this role]
Description: [single sentence]
Competencies: [{competencyName, competencyLevelName} -- EXACT baseline names]
Tags: {domainTags, lifecycleTags, organizationalTags}
Narrative: [ONLY when Phase 1 provides substantive role detail -- omit if brief mention only]
Asset Icon: [font-character icon, e.g., fa-user-gear]
```

### Step 4c: Consolidate Persona Groups

Compare Phase 1 groups against context groups. Prefer composing via `personaGroupNames` (hierarchical inclusion) over flat groups that duplicate membership.

- **Redeclare** existing groups to add members or sub-groups
- **Create new** focused sub-groups (3–5 members) for genuinely novel team structures
- **Compose** cross-functional groups by referencing sub-groups via `personaGroupNames`

Aim for 1–3 total groups.

```
Persona Group Name: [team name or existing context name]
Mapping Type: Redeclaration | New | Composition
Description: [single sentence]
Persona Names: [array of direct member persona names]
Persona Group Names: [array of existing group names to include as sub-groups]
Tags: {organizationalTags}
Narrative: [ONLY when Phase 1 provides substantive team detail -- omit if name/member list only]
Asset Icon: [font-character icon, e.g., fa-people-group]
```

## Step 5: Map Activities

For each activity from Phase 1:

```
Activity Name: [verb + specific object -- NEVER same as activity space name]
Description: [single sentence]
Activity Space Name: [baseline activity space]
Focus Name: [Value | Solution | Endeavor]
Background: [optional prerequisites]
Test: [optional -- seeded from Phase 1 Triggers and Observable Results]
  When: [triggers, decision points, events]
  Then: [practitioner-meaningful outcomes beyond structural contributesTo]
Contributes To: [{alphaName, stateName} objects]
Works On: [{workProductName, levelOfDetailName} objects]
Required Competencies: [baseline competency names]
Recommended Competency Levels: [{competencyName, competencyLevelName}]
Involves: [PersonaGroup names]
Led By: [optional -- single Persona name accountable. Only when Phase 1 identifies clear single-person accountability]
Narrative: [Technique narrative with Overview, Technique, Common Pitfalls]
```

### Alpha-State-Activity Gap Analysis (REQUIRED)

**CRITICAL: Every alpha state beyond null-point initial states MUST have at least one supporting activity.**

After initial activity mapping, systematically check:

1. **Evaluate initial state (State 1):**
   - **Null Point** (no activity needed): State represents absence/non-existence (e.g., "Not Identified", "Not Started") -> Skip
   - **Prepared** (bootstrap activity needed): State represents actual achievement (e.g., "Identified", "Initiated", "Architecture Selected") -> Add bootstrap activity

2. **For each subsequent state (State 2+):** Verify at least one activity has `contributesTo` pointing to {alphaName, stateName}. If none -> Activity gap -> infer missing activity.

3. **Infer missing activities** from: methodology content (Phase 1), parent alpha patterns (for specializations), baseline ActivitySpace patterns.

4. **Document gap analysis matrix:**

```markdown
## Alpha-State-Activity Coverage Matrix

| Alpha Name | State Name | Seq | State Type | Activities Contributing | Status | Action |
|:-----------|:-----------|:----|:-----------|:----------------------|:-------|:-------|
| Platform | Architecture Selected | 1 | Prepared | Select Platform Architecture | Covered | None |
| Platform | Baselined | 2 | Progression | - | Gap | ADD: "Baseline Platform Configuration" |
```

**Quality gate:** 100% coverage with state types documented. All inferred activities must have complete properties (contributesTo, worksOn, competencies, narrative).

## Step 6: Build Patterns

**Read** `references/pattern-completeness.md` for the four-pass pattern construction algorithm, constraints, and worked examples.

**CRITICAL: Every practice MUST have at least one pattern.**

### Pattern Candidacy

- 2+ alphas -> pattern REQUIRED (coordinates multiple concerns)
- 1 alpha -> evaluate if external lifecycle applies

### Four-Pass Construction (Summary)

1. **Pass 1 (Source-Driven):** Extract pattern structure from source, map explicit alpha states to PatternViews
2. **Pass 2 (Backfill -- REQUIRED):** For each alpha, review ALL states, backfill missing cells. Final PatternView must include ALL alphas
3. **Pass 3 (Related Alphas -- OPTIONAL):** Consider adding alphas from practice/dependencies with meaningful progressions
4. **Pass 4 (Validation -- REQUIRED):** Max 1 state per alpha per view (split views if 2+), backfill late-appearing alphas with progressive states

### State Compression Rule (Critical for JSON Output)

- **Non-final views:** Include ONLY alpha states that CHANGE from the previous view. Unchanged carry-forward states are omitted (implicit).
- **Final view:** MUST include ALL alphas (even if unchanged) as complete end-state snapshot.
- **Empty view elimination:** After compression, any non-final view with zero alpha states should be removed. Merge its activities into the next view and renumber `seq` values.

### Pattern Structure

```
Pattern Name: [from Phase 1]
Description: [single sentence]
Narrative Type Name: [baseline narrative type]
Narrative: [optional -- only when Phase 1 provides substantive lifecycle rationale]
Pattern Views:
  View 1:
    Seq: [0 for prerequisites, 1+ for main phases]
    Name: [phase name]
    Description: [max 12 words]
    Alpha States: [{alphaName, stateName} objects]
    Alpha Instances: [if tracking specific instances]
    Work Product Levels: [optional -- {workProductName, levelOfDetailName} objectives]
    Activities: [array of activity names active in this phase]
    Narrative Contexts: [{seq, narrativeElementName, context (1-2 sentences)}]
  View 2: ...
```

### Pattern Groups (If Applicable)

**Read** `references/semantics/execution-and-patterns.md` SS9.3 for guidance.

When to create: 3+ patterns in practice, or 10+ patterns across method. Single-pattern practices generally do NOT need groups.

1. **Check baseline for existing patternGroups** -- baselines define canonical groups as templates
2. **Assign patterns to baseline groups** (preferred)
3. **Novel groups only when justified** -- document why no baseline group fits

## Step 7: Define Outcomes

Transform Phase 1 outcome candidates into **1-3 structured Outcomes** per practice.

Each Outcome requires:
- **name** (2-5 words, value-oriented)
- **description** (single sentence)
- **measureDescription** (ALWAYS REQUIRED -- how success is measured)

Each Outcome optionally includes:
- **metricContributions** -- when alpha -> work product -> metric chain exists:
  - `alphaName` must match a defined alpha
  - `metricName` must match a `WorkProduct.expectedMetrics` entry
  - `workProductName` (optional filter) must match a WorkProduct.name
  - `recognizedAtStateName` must match a valid state on the named alpha
  - `forecastWeights` array of {stateName, weight} for 0-1 probability
- **objectiveContributions** -- when patterns have well-defined lifecycle views:
  - `patternName` REQUIRED -- must match a defined pattern
  - `recognizedAtPatternViewName` must match a view within that pattern
  - `forecastWeights` array of {patternViewName, weight} for cumulative progress

**Lifecycle pattern outcome (STRONGLY RECOMMENDED):** If the practice defines lifecycle patterns, at least one outcome SHOULD use `objectiveContributions` tied to the **main lifecycle pattern** (broadest alpha coverage). Set `recognizedAtPatternViewName` to the final view with monotonically increasing forecast weights.

## Step 8: Map Narratives, Citations, Assets, and References

**Read** `references/semantics/narrative-and-assets.md` SS10-11 for narrative format rules, self-containment requirements, and asset specifications.

### Narrative Format Templates

**Practice/Method Narrative** (REQUIRED -- structured format):
```
- Narrative Type Name: [STAR | Hero's Journey | Three-Act Structure | Essay]
- Narrative Contexts:
  - Seq: 1, Narrative Element Name: [from type], Context: [1-3 sentences]
  - Seq: 2, Narrative Element Name: [from type], Context: [1-3 sentences]
  - ...
- Citation Names: [citation references]
```

**Alpha Narrative** (REQUIRED for new alphas, RECOMMENDED for redeclarations):
```
- Narrative Type Name: Essay
- Narrative Contexts:
  - Seq: 1, Narrative Element Name: Introduction, Context: [why this alpha matters]
  - Seq: 2, Narrative Element Name: Body, Context: [key considerations]
  - Seq: 3, Narrative Element Name: Conclusion, Context: [success factors]
- Citation Names: [references]
```

**Activity Narrative** (REQUIRED for all activities):
```
- Narrative Type Name: Technique
- Narrative Contexts:
  - Seq: 1, Narrative Element Name: Overview, Context: [what this accomplishes]
  - Seq: 2, Narrative Element Name: Technique, Context: [step-by-step guidance]
  - Seq: 3, Narrative Element Name: Common Pitfalls, Context: [what to avoid]
- Citation Names: [references]
```

### Narrative Quality Checklist

- [ ] Practice narrative uses structured format (NOT prose)
- [ ] All new alphas have narrative objects with narrativeTypeName
- [ ] All activities have Technique narrative objects
- [ ] All narrative contexts are 1-3 sentences (NOT paragraphs)
- [ ] **Narrative contexts contain direct content -- NO self-references** ("In this STAR narrative...", "This Essay explores...", "The following narrative describes...")
- [ ] **Narrative contexts are self-contained** -- coherent without element headings (element names are authoring scaffolding, not displayed to readers)
- [ ] Citations referenced in citationNames arrays
- [ ] Narrative names describe subject matter, not template type ("Accelerating Platform Adoption" not "Practice Intent")
- [ ] Element-specific narratives placed on their elements, not in top-level array
- [ ] Citations have NO narratives property (metadata only)

### Citation Format

```
Name: [Exact source title -- NOT author-date shorthand]
Description: [1 sentence summary]
Authors: [array of author names]
Date: [publication year]
Source: [publisher/journal]
URL: [retrieval URL -- REQUIRED where possible; carry forward Phase 1 URLs including internal/intranet links]
```

### Visual Assets

**Read** `references/semantics/narrative-and-assets.md` SS11 for asset specifications.

Priority: font-character icons > external URLs > bundled files. Identify assets for alphas, activities, personas, competencies.

### Reference Content

**Read** `references/semantics/alphas.md` SS6.6 for naming conventions, instance naming, merge rules, and two-level link architecture.

For each Phase 1 reference candidate:
1. Apply actionability test -- practitioners must get something directly usable (template, example, artifact), not documentation
2. Map to alpha + state, optionally evidence with work product + LOD
3. Every reference MUST have at least one `links` entry with URI
4. Links to large documents MUST include `pages` pointing to specific template/example location
5. Drop candidates without links

## Step 9: Map Terminology Aliases

**Read** `references/semantics/composition.md` SS4.3 for the complete aliasing decision tree, priority rules, and worked examples.

### Decision Tree for Each Domain Term

1. Canonical alternative to baseline element? -> **Alias** (1 per element max)
2. Different deployment of same type? -> **Instance**
3. Facet/component with different states? -> **Specialization** (`contributesTo`)
4. Named variant with same states (IS-A)? -> **Variant Mapping** (`mapsTo`)
5. Acronym/abbreviation/synonym? -> **Keywords**

### Quality Target

- **3-8 aliases** per practice (ONE alias per PracticeElement)
- **10-20 keywords** per practice
- ALL structural references use CANONICAL names, NEVER alias names
- No alias collisions with parent/dependency practice aliases
- Do NOT re-declare aliases inherited through `practiceDependencyNames`

### Alias Structure

```
Practice Element Aliases:
  - Element Type: [Alpha | WorkProduct | Activity | Persona | PersonaGroup]
    Element Name: [CANONICAL name]
    Alias Name: [domain-specific alternative term]
```

## Step 10: Assemble Output

Write the complete mapping guide to `practices/<practice-name>/02-mapping-guide.md`.

### Output Format

#### Element Heading Conventions (Required for Eval Parser)

Use these EXACT formats for element headings so automated validation can count elements:

```
#### Alpha: Name (Type -- Enrichment Level)
#### Work Product: Name
#### Activity: Name
#### Pattern: Name
```

Both `**Alpha: Name**` (bold) and `#### Alpha: Name` (heading level 3-5) are accepted.

#### Section Structure

```markdown
# Phase 2 Mapping Guide: <Methodology Name>

## Metadata
- **Mapping Date**: YYYY-MM-DD
- **Source Analysis**: practices/<practice-name>/01-analysis-report.md
- **Baseline Practice**: <path to baseline JSON>
- **Practice Type**: Single Practice | Method (Multiple Practices)

## Delineation Analysis
[From Step 0]

## Baseline Practice Index
### Focuses (N)
### Alphas (N baseline + N practice-defined)
### Competencies (N)
### Activity Spaces (N)
### Narrative Types (N)

---

## Method Mapping (if applicable)
[Method name, description, keywords, narrative, citations, practice list]

---

## Practice: <Practice Name>

### Practice Metadata
[Name, description, baseline practice name, tags, keywords, narrative]

### Terminology Aliases
[From Step 9]

### Citations
[From Step 8]

### Alpha Mappings
#### Redeclared Baseline Alphas
#### New Practice-Defined Alphas
#### Alpha Instances

### Work Product Mappings
[From Step 3]

### Persona and Persona Group Mappings
#### Competency Mapping Table
#### Personas
#### Persona Groups

### Activity Mappings
[From Step 5]

### Alpha-State-Activity Gap Analysis
[Coverage matrix from Step 5]

### Pattern Mappings
[From Step 6]

### Pattern Groups (if applicable)
[From Step 6]

### Outcome Mappings
[From Step 7]

### Reference Content Mappings
[From Step 8]

### Assets
[From Step 8]

### Acknowledgements
[If source identifies individuals/groups to credit]

---

## Validation Checklist
[Final validation pass]
```

### Global Name Uniqueness

All PracticeElement names must be unique across ALL element types within the practice. An Alpha and a WorkProduct cannot share a name. An Activity and an Alpha cannot share a name. Check for collisions before finalizing.

## Validation

### Pre-Output Validation Checklist

- [ ] All new alphas have `contributesTo` or `mapsTo` (may coexist on different targets; no floating alphas)
- [ ] All `mapsTo` alphas have exact state name matches with target alpha
- [ ] All baseline references use exact canonical names (case-sensitive)
- [ ] Competency names are exact baseline names
- [ ] Tags use orthogonal structure {domainTags, lifecycleTags, organizationalTags}
- [ ] Descriptions: max 20 words for elements, max 12 for states/LODs
- [ ] Activity names differ from Activity Space names
- [ ] LOD names are content-descriptive (no "Level X:" prefix, no lifecycle stages)
- [ ] All LODs have contributesTo array (required)
- [ ] Work product `partOf` and `mapsTo` are mutually exclusive
- [ ] Narrative contexts are 1-3 sentences, self-contained, no self-references
- [ ] Citations have NO narratives property (metadata only)
- [ ] Checklists: imperative verb phrases, positive/additive only, independently assessable, information-independent descriptions
- [ ] Checklist priority: deferrable/supplementary items marked `should`/`could`; essential items have no priority (defaults to `must`)
- [ ] 1-3 outcomes per practice, each with measureDescription
- [ ] Outcome metricContribution.alphaName matches valid alpha; workProductName matches valid WP with expectedMetrics
- [ ] Outcome objectiveContribution.patternName matches valid pattern; recognizedAtPatternViewName matches valid view
- [ ] At least one outcome with objectiveContributions tied to main lifecycle pattern (if practice has lifecycle patterns)
- [ ] Pattern views: max 1 state per alpha per view; final view includes ALL alphas
- [ ] Gherkin structures used selectively where verification logic adds value
- [ ] Every reference has at least one `links` entry with URI
- [ ] Global name uniqueness across all PracticeElement types
- [ ] Delineation Analysis section present; broad coverage justified if >= 8 alphas

### Programmatic Validation

```bash
python3 utils/eval-skill-output.py practices/<name>/ --phase 2 --summary
```

Fix any FAIL assertions before reporting completion. If sections are missing, read Phase 1 analysis for unmapped content and generate missing sections.

## Common Mistakes

1. **Name collisions across element types** -- Alpha and WorkProduct sharing a name breaks global uniqueness
2. **Missing relatesTo `direction` field** on new alphas -- every relatesTo entry requires `outgoing`, `incoming`, or `mutual`
3. **Missing outcome contributions** -- extension practice outcomes must have `metricContributions` or `objectiveContributions`, never neither
4. **Narrative self-references** -- "In this STAR narrative..." or "This Essay explores..." instead of direct content
5. **Pattern views with >1 state per alpha** -- must split into separate views
6. **Skipping alpha-state-activity gap analysis** -- every non-null-point state needs at least one supporting activity
7. **Alias collisions with parent/dependency practice aliases** -- do not re-declare inherited aliases or reuse alias names for different targets
8. **Missing `ledBy` on activities** where source identifies clear single-person accountability -- distinct from `involves` (groups)
9. **Pattern final view missing alphas** that appear in earlier views -- final view must be a complete snapshot of ALL alphas
10. **Outcomes inflated beyond 1-3 per practice** -- distill to the most important value propositions

## User Feedback Messages

Report progress at these milestones:
- "Reading analysis report and loading baseline practice..."
- "Mapping N concerns to alphas using redeclaration/specialization framework..."
- "Conducting alpha-state-activity gap analysis..."
- "Gap analysis complete: 100% alpha state coverage achieved"
- "Constructing patterns using four-pass approach..."
- "Pattern validation complete: NxM matrix with 1-2 states per alpha per view"
- "Phase 2 complete: Mapping guide generated at practices/<name>/02-mapping-guide.md"
