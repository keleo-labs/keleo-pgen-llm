# Phase 2: Baseline Mapping Prompt

## Context

You are conducting **Phase 2: Baseline Mapping** of a baseline practice creation workflow. This phase transforms the Phase 1.5 distilled essentials into a comprehensive mapping specification that will guide Phase 3 JSON generation.

**Critical Input:** This phase reads **Phase 1.5 distilled essentials** (NOT Phase 1 detailed analysis) as its primary source. Phase 1.5 has already identified focuses, essential concerns, activity types, and competencies.

## Objective

Transform the Phase 1.5 distilled essentials into a mapping specification that:
- Uses the identified Focus areas to organize content
- Maps essential concerns to baseline Alphas (with relatesTo relationships)
- Maps activity types to baseline ActivitySpaces (with contributesTo mappings)
- Defines Competencies with 5-level progressions
- Defines NarrativeTypes with narrative elements
- Creates comprehensive narratives for baseline elements
- Maps citations and assets
- Maps distilled outcomes to baseline Outcomes with framework-level measurement
- Produces a complete mapping guide for JSON generation (Phase 3)

## Resources Available

You have access to the following resources via the Read tool:

1. **baselines/<name>/01.5-distilled-essentials.md** (Phase 1.5 output - PRIMARY SOURCE)
   - Identified focuses (default or custom)
   - Essential concerns (will become alphas)
   - Activity types (will become activitySpaces)
   - Universal competencies
   - Narrative frameworks
   - Read this completely before starting mapping

2. **baselines/<name>/01-analysis-report.md** (Phase 1 output - SUPPORTING DETAIL)
   - Use ONLY for:
     - Citation details
     - Narrative examples
     - Additional context
   - Do NOT use Phase 1 concerns/activities directly (use Phase 1.5 distilled versions)

3. **Optional Parent Baseline JSON** (if provided by user)
   - Example: `deps/platform-adoption-kernel.json`
   - Read if this baseline extends another baseline
   - Understand parent focuses, alphas, competencies

4. **Semantic Guidance** (sub-documents in `references/semantics/`)
   - `references/semantics/practice-elements.md` — PracticeElement foundations, tags, checklists (§5)
   - `references/semantics/alphas.md` — Alpha-state trajectory, baseline isolation (§6)
   - `references/semantics/narrative-and-assets.md` — Narrative management (§10)
   - `references/semantics/composition.md` — Decision frameworks, redeclaration vs specialization (§4)
   - Read relevant sub-documents thoroughly before mapping

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

## Instructions

### Step 1: Load Resources

**Read these in order:**

1. **Read `baselines/<name>/01.5-distilled-essentials.md`** (PRIMARY SOURCE)
   - Review identified focuses (default or custom)
   - Review essential concerns with states and relationships
   - Review activity types with contributesTo mappings
   - Review universal competencies with 5 levels
   - Review narrative frameworks
   - **Note Gherkin seed material** — these fields feed Gherkin constructs in JSON:
     - Concern **Concreteness Tests** (Given/When/Then) → inform state `background` decisions
     - State **Prerequisites** → seed `background.given` and `background.alphaStates`

2. **Read `baselines/<name>/01-analysis-report.md`** (SUPPORTING DETAIL)
   - Reference for citations, narrative examples, additional context
   - Do NOT extract new concerns/activities (use Phase 1.5 distilled versions)

3. **Read optional parent baseline JSON** (if provided)
   - If this baseline extends another baseline
   - Understand parent structure to avoid duplication
   - Note: Most baselines do NOT extend another baseline

4. **Read relevant semantics sub-documents:**
   - `references/semantics/practice-elements.md` — PracticeElement, tags, checklists (§5); Gherkin-Inspired Test Model for optional background on states (§5.3)
   - `references/semantics/alphas.md` — Alpha-state trajectory, baseline isolation (§6)
   - `references/semantics/narrative-and-assets.md` — Narrative management (§10)
   - `references/semantics/composition.md` — Decision frameworks, redeclaration vs specialization (§4)

### Step 2: Map Metadata

**Baseline Metadata:**

- **Name**: Exact name from Phase 1.5 (e.g., "Partner Ecosystem Essentials")
- **Description**: Single sentence from Phase 1.5
- **Version**: "1.0" (initial baseline)
- **Authors**: ["Your Name" or organization]
- **Created/Updated**: Current date (YYYY-MM-DD format)
- **Keywords**: 5-10 keywords from Phase 1.5 for search/discovery
- **Tags**: Convert Phase 1.5 tags to orthogonal structure
  ```
  tags: {
    domainTags: [technical disciplines],
    lifecycleTags: [temporal frameworks],
    organizationalTags: [business units]
  }
  ```

**If extending another baseline:**
- **baselinePracticeName**: Name of parent baseline (e.g., "Platform Adoption Essentials")
- Otherwise: NO baselinePracticeName property

### Step 3: Define Focuses

**Use Phase 1.5 Focus Definitions:**

Read the Focus Areas section from Phase 1.5 distilled essentials.

**For each focus:**
- **Name**: Exact name from Phase 1.5 (e.g., Value, Engagement, Go-to-Market)
- **Description**: Description from Phase 1.5 (may refine if needed)

**Validate:**
- ✓ 2-4 focuses defined
- ✓ All essential concerns from Phase 1.5 assigned to a focus
- ✓ Focus distribution is balanced

**Output Format:**

```markdown
## Focuses

Total: [X focuses]

### Focus: [Name]
- **Description**: [Single sentence scope]
- **Coverage**: [List of essential concern names assigned to this focus]

[Repeat for each focus]
```

### Step 4: Map Essential Concerns to Baseline Alphas

**Transform Phase 1.5 Essential Concerns into Baseline Alphas.**

**Key Principle:** Baseline alphas are ROOT-LEVEL concepts. They do NOT have `contributesTo` property (that's for extension practices). They DO have `relatesTo` arrays showing inter-alpha relationships.

**For EACH essential concern from Phase 1.5:**

1. **Read concern definition from Phase 1.5**
   - Name, description, focus assignment
   - Progressive states (5-7 states)
   - Relationships to other concerns (produces, governed by, uses)

2. **Transform to Baseline Alpha**

**Alpha Structure:**

```markdown
### Alpha: [Name from Phase 1.5 essential concern]
- **Description**: [From Phase 1.5 concern description]
- **Focus**: [From Phase 1.5 focus assignment]
- **relatesTo**: [Array of alpha names based on Phase 1.5 relationships]
  - **Relationship Type | Target Alpha | Rationale**
  - produces | [Alpha name] | [Why this alpha enables the target]
  - governed by | [Alpha name] | [Why this alpha is constrained by target]
  - uses | [Alpha name] | [Why this alpha depends on target]
- **States**: [From Phase 1.5 progressive states]
  - **State 1: [Name]**
    - **Description**: [From Phase 1.5]
    - **Background**: [optional - populate from Phase 1.5 state Prerequisites; use sparingly in baselines — the practice layer is the natural place for detailed Gherkin structure]
      - Given: [from Phase 1.5 Prerequisites: contextual conditions and natural-language preconditions]
      - Alpha States: [from Phase 1.5 Prerequisites: cross-concern dependencies → {alphaName, stateName} pairs — NEVER the previous state of the SAME alpha (sequential progression is implicit in seq ordering)]
    - **Checklists**: [imperative verb phrases — actionable tasks, not criteria; each description must add rationale/scope/method beyond the name, not restate it as a sentence]
      - [ ] [Actionable task 1 from Phase 1.5]
      - [ ] [Actionable task 2 from Phase 1.5]
      - [ ] [Actionable tasks 3-5 from Phase 1.5]
  - **State 2: [Name]**
    - [Same structure, 5-7 states total]
- **Narrative**: [Practice-level narrative using a narrative type from Phase 1.5]
  - Narrative Type: [e.g., "STAR", "Hero's Journey", custom framework]
  - Element Mapping:
    - [Narrative Element 1]: [How this alpha maps to element]
    - [Narrative Element 2]: [How this alpha maps to element]
```

**relatesTo Relationship Guidelines:**

Each `relatesTo` entry is an `AlphaRelationship` with required `relationship`, `alphaName`, and `direction` fields, plus an optional `description`:

| Field | Required | Description |
|-------|----------|-------------|
| `relationship` | Yes | Verb phrase (e.g., "produces", "governed by", "uses") |
| `alphaName` | Yes | Target alpha name (must exist in this baseline) |
| `direction` | Yes | `outgoing` / `incoming` / `mutual` |
| `relationshipKind` | No | Machine-traversable classification: `dependency`, `production`, `guidance`, `information-flow`, `enabling`, `impact`, `consumption`, `mutual` |
| `description` | No | Why this relationship exists |

**Direction values:**

- **`outgoing`**: This alpha acts upon the target — "produces", "constrains", "enables", "depends on", "consumes"
  - Example: Opportunity → produces → Platform Value (direction: `outgoing`)
  
- **`incoming`**: The target acts upon this alpha — "governed by", "built by", "validated by"
  - Example: Platform → governed by → Platform Governance (direction: `incoming`)
  
- **`mutual`**: Symmetric relationship — "correlates with", "co-evolves with"
  - Use sparingly for genuinely symmetric peer relationships

**Quality Checks:**
- ✓ NO `contributesTo` property (baseline alphas are root-level)
- ✓ ALL alphas have `relatesTo` arrays (show interconnections)
- ✓ Every `relatesTo` entry has `direction` field
- ✓ 5-7 states per alpha (not more than 7, not fewer than 5)
- ✓ Each state has 3-5 checklist items (imperative verb phrases from Phase 1.5), all positive/additive (actions to perform, not absences to observe); each checklist text adds actionable specificity beyond what the state description already conveys
- ✓ 8-15 total alphas (from Phase 1.5 essential concerns)

**Output Format:**

```markdown
## Alphas

Total: [X alphas] across [Y focuses]

[Alpha sections as described above]
```

### Step 5: Map Activity Types to ActivitySpaces

**Transform Phase 1.5 Activity Types into Baseline ActivitySpaces.**

**For EACH activity type from Phase 1.5:**

1. **Read activity type definition**
   - Name, description, focus assignment
   - contributesTo mappings (which concerns/states)
   - Required competencies

2. **Transform to ActivitySpace**

**ActivitySpace Structure:**

```markdown
### ActivitySpace: [Name from Phase 1.5]
- **Description**: [From Phase 1.5 activity type description]
- **Focus**: [From Phase 1.5 focus assignment]
- **Background**: [optional - shared prerequisites for this activity space; use sparingly in baselines]
  - Given: [preconditions before activities in this space begin]
  - Alpha States: [prerequisite alpha/state pairs]
- **contributesTo**: [Array of alpha-state pairs from Phase 1.5 mappings]
  - [Alpha Name] → [State 1], [State 2]
  - [Alpha Name] → [State 3]
- **requiredCompetencies**: [List of competency names from Phase 1.5]
  - [Competency 1]
  - [Competency 2]
- **Narrative**: [ActivitySpace-level narrative]
  - Narrative Type: [e.g., "STAR"]
  - Element Mapping:
    - [Element]: [How this activity space maps]
```

**contributesTo Validation:**

- ✓ Every alpha state from Step 4 has ≥1 activity space contributing to it
- ✓ All referenced alpha names exist in Step 4 alphas
- ✓ All referenced state names exist in the alpha's states

**requiredCompetencies Validation:**

- ✓ All referenced competency names exist in Step 6 competencies
- ✓ Competencies make sense for the work (not random)

**Quality Checks:**
- ✓ 6-12 total activity spaces (from Phase 1.5 activity types)
- ✓ Each activity space assigned to a focus
- ✓ contributesTo coverage is complete (all alpha states covered)

**Output Format:**

```markdown
## ActivitySpaces

Total: [X activity spaces] across [Y focuses]

[ActivitySpace sections as described above]
```

### Step 6: Define Competencies

**Transform Phase 1.5 Universal Competencies into Baseline Competencies.**

**For EACH competency from Phase 1.5:**

1. **Read competency definition**
   - Name, description
   - 5-level progression (Basic, Applies, Masters, Adapts, Innovating)

2. **Transform to Competency**

**Competency Structure:**

```markdown
### Competency: [Name from Phase 1.5]
- **Description**: [From Phase 1.5 expertise area description]
- **Narrative**: [From Phase 1.5 competency context — include ONLY when Phase 1.5 provides
  substantive detail about why this competency matters, how it develops, or its role in the
  domain. Omit if Phase 1.5 provides only a name and brief description.]
- **Asset Icon**: [font-character icon for this competency — e.g., fa-code for engineering,
  fa-shield-halved for security, fa-chart-line for analysis]
- **Levels**:
  1. **Basic**
     - **Description**: [From Phase 1.5 level 1 description]
     - **Level**: 1
  2. **Applies**
     - **Description**: [From Phase 1.5 level 2 description]
     - **Level**: 2
  3. **Masters**
     - **Description**: [From Phase 1.5 level 3 description]
     - **Level**: 3
  4. **Adapts**
     - **Description**: [From Phase 1.5 level 4 description]
     - **Level**: 4
  5. **Innovating**
     - **Description**: [From Phase 1.5 level 5 description]
     - **Level**: 5
```

**Quality Checks:**
- ✓ 5-10 total competencies (from Phase 1.5)
- ✓ Each competency has exactly 5 levels
- ✓ Level numbers are 1, 2, 3, 4, 5 (sequential)
- ✓ Level names follow standard pattern (Basic, Applies, Masters, Adapts, Innovating)
- ✓ Each competency has an asset icon assigned

**Output Format:**

```markdown
## Competencies

Total: [X competencies]

[Competency sections as described above]
```

### Step 7: Define NarrativeTypes

**Transform Phase 1.5 Narrative Frameworks into Baseline NarrativeTypes.**

**For EACH narrative framework from Phase 1.5:**

1. **Read narrative framework definition**
   - Name, description (when to use)
   - Narrative elements (sequential components with howToUse)

2. **Transform to NarrativeType**

**NarrativeType Structure:**

```markdown
### NarrativeType: [Name from Phase 1.5]
- **Description**: [From Phase 1.5 - when to use]
- **Narrative Elements**:
  1. **[Element Name from Phase 1.5]**
     - **Description**: [What it represents from Phase 1.5]
     - **How to Use**: [Practitioner guidance from Phase 1.5]
  2. **[Element Name]**
     - **Description**: [What it represents]
     - **How to Use**: [Practitioner guidance]
  [... 3-7 elements]
```

**Quality Checks:**
- ✓ 3-5 total narrative types (from Phase 1.5)
- ✓ Each narrative type has 3-7 elements
- ✓ Elements are sequential (tell a progression)
- ✓ HowToUse provides actionable guidance

**Output Format:**

```markdown
## NarrativeTypes

Total: [X narrative types]

[NarrativeType sections as described above]
```

### Step 8: Create Narratives

**Create narratives for baseline elements using the defined narrative types.**

**Narrative Targets:**

1. **Baseline-Level Narrative** (REQUIRED)
   - Overall baseline practice journey
   - Use macro-level narrative type (Hero's Journey, custom journey)
   - **Placement**: Top-level `narratives[]` array in JSON output

2. **Alpha-Level Narratives** (optional, for key alphas)
   - Alpha progression story
   - Use appropriate narrative type (STAR, Three-Act, etc.)
   - **Placement**: Embedded on the alpha's own `narratives[]` property

3. **Alpha State Narratives** (optional, for critical states)
   - State achievement story
   - Use micro-narrative type (ABT)
   - **Placement**: Embedded on the alpha state's own `narratives[]` property

4. **ActivitySpace Narratives** (optional, for complex activity spaces)
   - Activity space execution story
   - Use tactical narrative type (STAR)
   - **Placement**: Embedded on the activitySpace's own `narratives[]` property

5. **Competency Narratives** (optional)
   - Competency development journey
   - Use progression narrative
   - **Placement**: Embedded on the competency's own `narratives[]` property

**PLACEMENT RULE:** Element-specific narratives are embedded on the element's own `narratives[]` property in the JSON output, NOT in a flat top-level narratives array. Only the baseline-level narrative goes in the top-level `narratives[]` array. The Target field below indicates where Phase 3 should place each narrative.

**Narrative Structure:**

```markdown
### Narrative: [Descriptive name for the narrative subject]
- **Target**: [baseline | Alpha: [name] | AlphaState: [alpha].[state] | ActivitySpace: [name] | Competency: [name]]
  - `Target: baseline` → goes in top-level `narratives[]`
  - `Target: Alpha: [name]` → goes in that alpha's `narratives[]` property
  - `Target: ActivitySpace: [name]` → goes in that activitySpace's `narratives[]` property
  - `Target: Competency: [name]` → goes in that competency's `narratives[]` property
- **Narrative Type**: [Name from Step 7]
- **Citation Names**: [list of Citation.name values referenced in this narrative's content]
- **Element Mapping**:
  - **[Narrative Element 1]**: [2-3 sentences mapping target to this element]
  - **[Narrative Element 2]**: [2-3 sentences mapping target to this element]
  - **[Narrative Element 3]**: [2-3 sentences mapping target to this element]
```

**CRITICAL: Narrative Naming Rules**
- Narrative names MUST describe the subject matter, NOT reference the narrative type
  - WRONG: "Digital Strategy Narrative", "The STAR Narrative for Business Model"
  - CORRECT: "From Reactive to Adaptive Strategy", "Pipeline to Platform Transition"
- Narrative descriptions MUST describe what the narrative covers, NOT the narrative template
  - WRONG: "The STAR narrative for the Business Model alpha."
  - CORRECT: "How organizations evolve from pipeline models to platform economics through structured experimentation."
- Narrative contexts MUST contain direct content, NOT self-references
  - WRONG: "In this Hero's Journey narrative, organizations embark on..."
  - CORRECT: "Organizations face accelerating competitive pressure from platform-native competitors..."
- Narrative contexts MUST be **self-contained** — coherent without element headings
  - Narrative element names (e.g., "Situation", "Task", "Action") are authoring scaffolding, NOT displayed to readers
  - Users consume `name`, `description`, and `context` strings sequentially
  - Bare lists in contexts require a framing introduction sentence

**Quality Checks:**
- ✓ Baseline-level narrative present (REQUIRED)
- ✓ All referenced narrative types exist in Step 7
- ✓ Element mappings provide substantive context (not generic)
- ✓ All narratives include Citation Names referencing relevant citations
- ✓ Narrative names describe subject matter, not narrative type
- ✓ Narrative descriptions and contexts contain direct content, not self-references
- ✓ Element-specific narratives are marked with correct Target for embedding on the element

**Output Format:**

```markdown
## Narratives

Total: [X narratives]
- Top-level (baseline): [Y]
- Element-embedded: [Z] (alphas, activitySpaces, competencies)

[Narrative sections as described above]
```

### Step 9: Map Citations

**Extract authoritative citations from Phase 1 analysis.**

Use **Citation Standard** narrative type:

```markdown
### Citation: [Full Title of Work]
- **Target**: [baseline | specific element]
- **Narrative Type**: Citation Standard
- **Element Mapping**:
  - **Author**: [Full name(s)]
  - **Date**: [Publication date - YYYY-MM-DD or YYYY]
  - **Title**: [Full title]
  - **Source**: [Publisher, journal, URL, or DOI]
```

**CRITICAL — Citation Name Rule:** The citation heading (and resulting `name` field) MUST be the **title of the work** (e.g., "Business Model Generation", "Dynamic Capabilities and Strategic Management"), NOT an author-date shorthand (e.g., "Osterwalder (2010)", "Teece (2007)"). Author names belong in the Author element only.

**Quality Checks:**
- ✓ Prioritize authoritative sources (primary methodology creators)
- ✓ Include publication dates
- ✓ Provide full source references (URLs, DOIs, ISBNs)
- ✓ **URL enrichment (REQUIRED):** Every citation SHOULD include a retrieval URL. Internal, intranet, and Google Docs/Sheets/Slides links are valid and preferred when available:
  - Carry forward URLs recorded in the Phase 1 analysis report (highest priority)
  - Carry forward URLs provided as user input sources
  - Official framework/methodology websites
  - DOI references for academic works: `https://doi.org/10.xxxx/xxxxx`
  - Publisher catalog pages for books
  - Standards body pages for standards (ISO, NIST, IEEE)
  - Only omit when no stable link exists. Never fabricate URLs. Internal/intranet URLs are valid.

**Output Format:**

```markdown
## Citations

Total: [X citations]

[Citation sections as described above]
```

### Step 10: Define Assets

**Identify visual assets (icons, diagrams, templates) from source materials.**

**Asset Types:**

1. **Icons** (alpha icons, competency badges, activity type indicators)
2. **Diagrams** (architecture visualizations, state progressions, pattern orchestrations)
3. **Templates** (reusable documents, forms, decision records)

**Asset Structure:**

```markdown
### Asset: [asset-name]
- **Type**: [icon | diagram | template]
- **Description**: [What this asset represents]
- **Proposed Path**: [assets/icons/[name].svg | assets/diagrams/[name].svg | assets/templates/[name].pdf]
- **MIME Type**: [image/svg+xml | image/png | application/pdf]
- **Referenced By**: [Element type and name]
- **Source**: [Citation reference or description of source]
```

**For Font Character Icons:**

```markdown
### Asset: [asset-name]
- **Type**: font-character
- **Description**: [What this icon represents]
- **Font Family**: [e.g., "Font Awesome 6 Free"]
- **Font Character**: [e.g., "fa-cubes"]
- **Font Weight**: [e.g., "900"]
- **Referenced By**: [Element type and name]
```

**Quality Checks:**
- ✓ Prefer font characters for icons (scalable, no files)
- ✓ Prefer SVG for diagrams (scalable, editable)
- ✓ Document clear source/attribution

**Output Format:**

```markdown
## Assets

Total: [X assets]

[Asset sections as described above]
```

### Step 10.5: Define Canonical PatternGroups

**Identify 3-5 navigational categories that extension practices will use to organise their patterns.**

Baselines define patternGroups as **template categories with empty entries**. Extension practices adopt these groups by defining patternGroups with the same canonical name and populating entries with their patterns. During method composition, groups with matching names merge (see semantics/execution-and-patterns.md §9.3).

**Grouping Strategies** (choose the most natural fit for the domain):

- **By lifecycle archetype** — Core Lifecycles, Optimisation Cycles, Maturity Progressions
- **By concern area** — Technical Patterns, Governance Patterns, Operational Patterns
- **By engagement phase** — Getting Started, Ongoing Execution, Scaling & Optimisation

**PatternGroup Structure:**

```markdown
### PatternGroup: [Category Name]
- **Description**: [What patterns in this group share — the coordination intent]
- **Seq**: [0-based ordering among groups]
- **Entries**: [] (empty — extension practices populate)
- **Narrative**: [optional — explain the category's purpose and when practitioners should look here]
  - Narrative Type: [e.g., "Practice Intent"]
  - Element Mapping:
    - [Element]: [How this group category maps]
```

**Naming Guidance:**

- **Good**: "Core Lifecycles", "Maturity Progressions", "Governance & Compliance"
- **Bad**: "Platform Patterns", "Technology Patterns" (restates focus or alpha names)

**Quality Checks:**
- ✓ 3-5 groups defined (enough to cover expected extension patterns)
- ✓ Group names describe coordination intent, not source practice
- ✓ All entries arrays are empty (baselines define categories, not contents)
- ✓ Seq values assigned for ordering

**Output Format:**

```markdown
## PatternGroups

Total: [X canonical groups]

[PatternGroup sections as described above]
```

### Step 10.7: Map Baseline Outcomes

Transform Phase 1.5 distilled baseline outcomes into baseline Outcome objects.

Baseline outcomes are simpler than extension practice outcomes — they typically have only `name`, `description`, and `measureDescription` (no metricContributions or objectiveContributions, since baselines lack work product instances and patterns).

For each Phase 1.5 baseline outcome:
- **name**: The distilled outcome name (2-5 words, framework-level)
- **description**: Value proposition (single sentence)
- **measureDescription**: How value delivery is tracked at the framework level

Baseline outcomes serve as templates — extension practices will specialize them with specific metrics and contribution mechanisms.

Document in the mapping guide:

```markdown
### Baseline Outcome Mappings

#### Outcome: [Name]
- **Description:** [Value proposition]
- **Measure Description:** [Framework-level measurement approach]
```

**Quality Checks:**
- 1-3 outcomes (warning if 0, max 5)
- Every outcome has measureDescription
- Names are value-oriented (2-5 words)

**Output Format:**

```markdown
## Outcomes

Total: [X outcomes]

[Outcome sections as described above]
```

### Step 11: Final Output Structure

**Write to: `baselines/<name>/02-mapping-guide.md`**

**Document Structure:**

```markdown
# Baseline Mapping Guide: [Baseline Name]

**Date**: [YYYY-MM-DD]
**Phase**: 2 - Baseline Mapping
**Source**: baselines/<name>/01.5-distilled-essentials.md

---

## Metadata

- **Name**: [From Phase 1.5]
- **Description**: [Single sentence]
- **Version**: 1.0
- **Authors**: [...]
- **Created**: [YYYY-MM-DD]
- **Updated**: [YYYY-MM-DD]
- **Keywords**: [5-10 keywords]
- **Tags**:
  - domainTags: [...]
  - lifecycleTags: [...]
  - organizationalTags: [...]
- **baselinePracticeName**: [If extending another baseline, otherwise omit]

---

## Focuses

[Complete Focuses section from Step 3]

---

## Alphas

[Complete Alphas section from Step 4]

---

## ActivitySpaces

[Complete ActivitySpaces section from Step 5]

---

## Competencies

[Complete Competencies section from Step 6]

---

## NarrativeTypes

[Complete NarrativeTypes section from Step 7]

---

## Narratives

[Complete Narratives section from Step 8]

---

## Citations

[Complete Citations section from Step 9]

---

## Assets

[Complete Assets section from Step 10]

---

## PatternGroups

[Complete PatternGroups section from Step 10.5]

---

## Outcomes

[Complete Outcomes section from Step 10.7]

---

## Mapping Statistics

- **Focuses**: [X]
- **Alphas**: [X] ([Y] per focus average)
- **ActivitySpaces**: [X]
- **Competencies**: [X]
- **NarrativeTypes**: [X]
- **PatternGroups**: [X] (canonical categories)
- **Outcomes**: [X]
- **Narratives**: [X]
- **Citations**: [X]
- **Assets**: [X]

---

## Next Steps

This mapping guide serves as the specification for Phase 3: Baseline JSON Generation.

Phase 3 will transform this mapping into schema-compliant JSON structure.
```

## Quality Standards

**Completeness**: All Phase 1.5 distilled elements must be mapped (no omissions).

**Consistency**: All cross-references must be valid (alpha names in relatesTo, competencies in requiredCompetencies, etc.).

**Clarity**: Descriptions and narratives should be substantive (not generic placeholders).

**Traceability**: Clear connection from Phase 1.5 distilled essentials to mapping.

## Common Pitfalls to Avoid

❌ **Using Phase 1 concerns directly**: Use Phase 1.5 distilled concerns, not Phase 1 detailed concerns
❌ **Adding contributesTo to alphas**: Baseline alphas are root-level, no contributesTo
❌ **Missing relatesTo relationships**: All alphas should have inter-alpha relationships
❌ **Incomplete contributesTo coverage**: Every alpha state needs ≥1 activity space
❌ **Invalid competency references**: All requiredCompetencies must exist in Step 6
❌ **Generic narratives**: Element mappings should be substantive, not boilerplate
❌ **Undefined narrative types**: All referenced types must exist in Step 7

## Success Criteria

✅ All Phase 1.5 focuses, concerns, activity types, competencies, narratives transformed
✅ Alphas have NO contributesTo, all have relatesTo arrays
✅ ActivitySpaces cover all alpha states (contributesTo validation)
✅ All competencies have exactly 5 levels
✅ All narrative types have sequential elements with howToUse
✅ Baseline-level narrative present
✅ All cross-references valid
✅ 1-3 baseline outcomes mapped with measureDescription
✅ Output file: `baselines/<name>/02-mapping-guide.md` (~40-60K words)
