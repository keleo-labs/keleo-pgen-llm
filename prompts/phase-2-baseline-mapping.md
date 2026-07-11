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

4. **references/semantics.md**
   - Comprehensive semantic guidance for Practice Language
   - Section 3: Structural foundations
   - Section 4: Alpha-state trajectory
   - Section 7: Narrative management
   - READ THIS THOROUGHLY before mapping

## Instructions

### Step 1: Load Resources

**Read these in order:**

1. **Read `baselines/<name>/01.5-distilled-essentials.md`** (PRIMARY SOURCE)
   - Review identified focuses (default or custom)
   - Review essential concerns with states and relationships
   - Review activity types with contributesTo mappings
   - Review universal competencies with 5 levels
   - Review narrative frameworks

2. **Read `baselines/<name>/01-analysis-report.md`** (SUPPORTING DETAIL)
   - Reference for citations, narrative examples, additional context
   - Do NOT extract new concerns/activities (use Phase 1.5 distilled versions)

3. **Read optional parent baseline JSON** (if provided)
   - If this baseline extends another baseline
   - Understand parent structure to avoid duplication
   - Note: Most baselines do NOT extend another baseline

4. **Read `references/semantics.md`**
   - Focus on sections:
     - Section 3: PracticeElement, tags, checklists
     - Section 4: Alpha-State Trajectory
     - Section 7: Narrative Management
     - Section 9: Decision frameworks

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
    - **Checklists**:
      - [ ] [Criteria 1 from Phase 1.5]
      - [ ] [Criteria 2 from Phase 1.5]
      - [ ] [Criteria 3-5 from Phase 1.5]
  - **State 2: [Name]**
    - [Same structure, 5-7 states total]
- **Narrative**: [Practice-level narrative using a narrative type from Phase 1.5]
  - Narrative Type: [e.g., "STAR", "Hero's Journey", custom framework]
  - Element Mapping:
    - [Narrative Element 1]: [How this alpha maps to element]
    - [Narrative Element 2]: [How this alpha maps to element]
```

**relatesTo Relationship Guidelines:**

Use **directionality pattern** (provider perspective):

- **"produces" (enables)**: This alpha enables/produces the target alpha
  - Example: Opportunity → produces → Platform Value (opportunity drives value realization)
  
- **"governed by" (constrained)**: This alpha is constrained/governed by the target alpha
  - Example: Platform → governed by → Platform Governance (governance constrains platform)
  
- **"uses" (depends on)**: This alpha uses/depends on the target alpha
  - Example: Platform Consumption Interface → uses → Platform (interface wraps platform)

**Quality Checks:**
- ✓ NO `contributesTo` property (baseline alphas are root-level)
- ✓ ALL alphas have `relatesTo` arrays (show interconnections)
- ✓ 5-7 states per alpha (not more than 7, not fewer than 5)
- ✓ Each state has 3-5 checklist items (from Phase 1.5 criteria)
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

2. **Alpha-Level Narratives** (optional, for key alphas)
   - Alpha progression story
   - Use appropriate narrative type (STAR, Three-Act, etc.)

3. **Alpha State Narratives** (optional, for critical states)
   - State achievement story
   - Use micro-narrative type (ABT)

4. **ActivitySpace Narratives** (optional, for complex activity spaces)
   - Activity space execution story
   - Use tactical narrative type (STAR)

5. **Competency Narratives** (optional)
   - Competency development journey
   - Use progression narrative

**Narrative Structure:**

```markdown
### Narrative: [Target element name]
- **Target**: [baseline | Alpha: [name] | AlphaState: [alpha].[state] | ActivitySpace: [name] | Competency: [name]]
- **Narrative Type**: [Name from Step 7]
- **Element Mapping**:
  - **[Narrative Element 1]**: [2-3 sentences mapping target to this element]
  - **[Narrative Element 2]**: [2-3 sentences mapping target to this element]
  - **[Narrative Element 3]**: [2-3 sentences mapping target to this element]
```

**Quality Checks:**
- ✓ Baseline-level narrative present (REQUIRED)
- ✓ All referenced narrative types exist in Step 7
- ✓ Element mappings provide substantive context (not generic)

**Output Format:**

```markdown
## Narratives

Total: [X narratives]

[Narrative sections as described above]
```

### Step 9: Map Citations

**Extract authoritative citations from Phase 1 analysis.**

Use **Citation Standard** narrative type:

```markdown
### Citation: [Author Last Name] ([Year])
- **Target**: [baseline | specific element]
- **Narrative Type**: Citation Standard
- **Element Mapping**:
  - **Author**: [Full name(s)]
  - **Date**: [Publication date - YYYY-MM-DD or YYYY]
  - **Title**: [Full title]
  - **Source**: [Publisher, journal, URL, or DOI]
```

**Quality Checks:**
- ✓ Prioritize authoritative sources (primary methodology creators)
- ✓ Include publication dates
- ✓ Provide full source references (URLs, DOIs, ISBNs)

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

## Mapping Statistics

- **Focuses**: [X]
- **Alphas**: [X] ([Y] per focus average)
- **ActivitySpaces**: [X]
- **Competencies**: [X]
- **NarrativeTypes**: [X]
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
✅ Output file: `baselines/<name>/02-mapping-guide.md` (~40-60K words)
