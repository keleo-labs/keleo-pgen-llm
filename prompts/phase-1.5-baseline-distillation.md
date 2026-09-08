# Phase 1.5: Baseline Distillation Prompt

## Context

You are conducting **Phase 1.5: Baseline Distillation** of a baseline practice creation workflow. This phase distills the detailed Phase 1 analysis into **essential foundational elements** suitable for a baseline practice framework.

**Critical Distinction:**
- **Phase 1** extracted ALL concerns, activities, and details from source materials
- **Phase 1.5** distills to ESSENTIAL, UNIVERSAL elements that form a reusable foundation
- **Baseline practices** define foundational ontology (alphas, competencies, narrative frameworks, activity spaces) that extension practices will later specialize

## Objective

Transform the comprehensive Phase 1 analysis into a focused distillation that identifies:
- **Focus Areas** (2-4 high-level groupings of concerns)
- **Essential Concerns** (8-15 universal concerns that will become baseline alphas)
- **Generalizable Activity Types** (6-12 high-level execution boundaries that will become ActivitySpaces)
- **Universal Competencies** (5-10 skill categories with 5-level progressions)
- **Narrative Frameworks** (3-5 reusable storytelling structures)

## Resources Available

You have access to the following resources via the Read tool:

1. **baselines/<name>/01-analysis-report.md** (Phase 1 output)
   - Comprehensive analysis with all concerns, activities, competencies
   - Read this completely before distillation

2. **references/domain-framework.md**
   - Four-perspective enterprise analysis framework
   - Use to understand Business, Technology, People, Process perspectives

3. **Optional Parent Baseline** (if provided)
   - Another baseline practice this one may extend
   - Read if user provides a parent baseline file path

4. **Example Baselines** (for reference)
   - `deps/platform-adoption-kernel.json` (default Value/Solution/Endeavor focuses)
   - `deps/partner-ecosystem-baseline.json` (custom Value/Engagement/Go-to-Market focuses)

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

## Instructions

### Step 1: Load Resources

**Read these in order:**

1. **Read `baselines/<name>/01-analysis-report.md`**
   - Review all extracted outcomes, concerns, states, activities, competencies, personas
   - Understand the breadth of the source methodology

2. **Read `references/domain-framework.md`**
   - Refresh understanding of four perspectives (Business, Technology, People, Process)
   - These inform focus area identification

3. **Optional: Read parent baseline** (if this baseline extends another)
   - Understand what focuses/alphas/competencies already exist
   - Identify gaps this baseline needs to fill

### Step 2: Identify Focus Areas (CRITICAL)

**Focus Areas group related concerns into 2-4 high-level categories.**

**Default Focuses (from Platform Adoption Kernel):**
- **Value**: Business value, economics, stakeholder alignment, strategy
- **Solution**: Technical architecture, implementation, integration, platforms
- **Endeavor**: Organizational structure, teams, ways of working, governance

**When to Use Custom Focuses:**
- Source methodology suggests a different natural grouping
- Domain has distinct value streams that don't map to default focuses
- Example: Partner Ecosystem → Value, Engagement, Go-to-Market

**Analysis Process:**

1. **Review Phase 1 Concerns by Perspective**
   - Group concerns by Business/Technology/People/Process tags
   - Look for natural clustering patterns
   - Count concerns per cluster

2. **Evaluate Default vs Custom Focuses**
   
   **Use DEFAULT (Value, Solution, Endeavor) if:**
   - Source concerns naturally map to business value, technical solution, organizational aspects
   - No compelling alternative grouping emerges
   - Standard practice domains (platform engineering, software delivery, architecture)
   
   **Use CUSTOM FOCUSES if:**
   - Source methodology explicitly organizes around different themes
   - Domain has distinct lifecycle phases or value streams
   - Clear natural clustering that doesn't align with defaults
   - Example domains: Partner ecosystems, customer success, sales methodology

3. **Define Focus Areas**
   
   For each focus (2-4 total):
   - **Name**: 1-2 words (Value, Solution, Engagement, Go-to-Market, etc.)
   - **Description**: Single sentence explaining scope (what concerns belong here)
   - **Rationale**: Why this focus grouping makes sense for this domain
   
   **Quality Checks:**
   - ✓ Each Phase 1 concern can be assigned to exactly one focus
   - ✓ Focuses are roughly balanced (no focus with <20% or >50% of concerns)
   - ✓ Focus names are neutral, domain-level terminology
   - ✓ Focuses are mutually exclusive and collectively exhaustive

**Output Section:**

```markdown
## Focus Areas

**Decision: [DEFAULT | CUSTOM]**

**Rationale**: [2-3 sentences explaining why default or custom focuses were chosen]

### Focus 1: [Name]
- **Description**: [Single sentence scope]
- **Typical Concerns**: [Examples of concern types that belong here]
- **Coverage**: [Approximate % of Phase 1 concerns]

[Repeat for each focus]
```

### Step 3: Distill Essential Concerns

**Essential Concerns are universal, foundational concepts that will become baseline alphas.**

**Distillation Process:**

1. **Review All Phase 1 Concerns**
   - Note concerns that appear across multiple source documents
   - Identify concerns that are fundamental vs. practice-specific
   - Look for concerns at different abstraction levels

2. **Remove Practice-Specific Concerns**
   
   **Remove if:**
   - Overly specific to a single vendor, tool, or platform
   - Tactical execution details rather than strategic concerns
   - Niche edge cases not broadly applicable
   - Example: "AWS IAM Role Configuration" → too specific
   
   **Keep if:**
   - Fundamental to the domain regardless of implementation
   - Represents a universal progression challenge
   - Applies across multiple contexts/organizations
   - Example: "Access Control" → universal

3. **Merge Similar Concerns to Higher Abstractions**
   
   If Phase 1 has:
   - "API Gateway", "Service Mesh", "Load Balancer" → Merge to "Platform Consumption Interface"
   - "Incident Response", "Change Management", "Capacity Planning" → Merge to "Platform Operations"
   
   Target: 8-15 essential concerns

4. **Define Each Essential Concern**
   
   For each concern:
   - **Name**: 2-5 words, neutral framework-level terminology
   - **Description**: Single sentence, general applicability (avoid vendor/tool names)
   - **Focus Assignment**: Which focus area (from Step 2)
   - **Concreteness Test**: Carry forward (and generalize) the Given/When/Then triplet from Phase 1. If Phase 1 concern was merged or renamed during distillation, write a new triplet for the distilled concern.
   - **Progressive States**: 5-7 universal maturity levels
     - Use Phase 1 state progressions as input
     - Generalize to remove practice-specific details
     - Each state: Name, Description, Prerequisites (1-3 cross-concern preconditions carried from Phase 1, generalized — do NOT list the previous state of the same concern, sequential progression is implicit), 3-5 verification criteria
   - **Relationships to Other Concerns**: Document dependencies/relationships (will become relatesTo)
     - "produces" relationships (this concern enables another)
     - "governed by" relationships (this concern is constrained by another)
     - "uses" relationships (this concern depends on another)

**Quality Checks:**
- ✓ Terminology is neutral (not vendor/tool specific)
- ✓ Descriptions are generally applicable (not context-specific)
- ✓ States represent universal progressions (not implementation details)
- ✓ 8-15 total concerns (not more than 15, not fewer than 8)
- ✓ Each concern assigned to a focus
- ✓ Relationships documented for inter-concern coordination

**Output Section:**

```markdown
## Essential Concerns (Future Baseline Alphas)

Total: [X concerns] across [Y focuses]

### Concern 1: [Name]
- **Description**: [Single sentence, universal scope]
- **Focus**: [Value | Solution | Engagement | etc.]
- **Concreteness Test**:
  - **Given** [precondition making this concern relevant]
  - **When** [trigger or action that advances the concern]
  - **Then** [observable outcome demonstrating progress]
- **Progressive States**: 
  1. **[State Name]**: [Description] — Prerequisites: [1-3 preconditions] — Criteria: [3-5 bullets]
  2. **[State Name]**: [Description] — Prerequisites: [1-3 preconditions] — Criteria: [3-5 bullets]
  [... 5-7 states total]
- **Relationships**:
  - Produces: [Concern names]
  - Governed by: [Concern names]
  - Uses: [Concern names]
- **Source Phase 1 Concerns**: [List of Phase 1 concerns merged/abstracted]

[Repeat for 8-15 essential concerns]
```

### Step 3.5: Distill Baseline Outcomes

Review the Phase 1 Outcomes section and consolidate to **1-3 baseline-level outcomes** that represent the universal value propositions of this framework domain.

For each baseline outcome:
- **Name** (2-5 words, value-oriented, framework-level terminology)
- **Description** (single sentence: what value this framework delivers)
- **Measurement Approach** (how value delivery is tracked at the framework level — general enough for any extension practice to specialize)
- **Related Essential Concerns** (which Step 3 essential concerns contribute to this outcome)
- **Source Phase 1 Outcomes** (which Phase 1 outcomes were consolidated)

**Quality checks:**
- 1-3 outcomes (not one per concern — outcomes are value propositions, not activities)
- Framework-level terminology (not vendor-specific)
- Measurable at a general level (extension practices will add specific metrics)
- Each outcome maps to at least one essential concern

**Output Section:**

```markdown
## Baseline Outcomes (Future Outcome Templates)

### [Outcome Name]
**Description:** ...
**Measurement Approach:** ...
**Related Essential Concerns:** ...
**Source Phase 1 Outcomes:** ...
```

### Step 4: Distill Generalizable Activity Types

**Activity Types are high-level execution boundaries that will become baseline ActivitySpaces.**

**Distillation Process:**

1. **Review All Phase 1 Activities**
   - Note common activity categories across concerns
   - Identify execution boundaries (explore vs build vs operate vs govern)
   - Look for high-level work types rather than specific tasks

2. **Generalize to Activity Types**
   
   If Phase 1 has:
   - "Design API Gateway", "Configure Load Balancer", "Set up Service Mesh" 
     → "Architect and Build the Foundation"
   - "Create Business Case", "Estimate TCO", "Define Success Metrics"
     → "Establish Value Proposition"
   - "Negotiate Partnership Terms", "Define SLAs", "Create Governance Framework"
     → "Govern Relationships"
   
   Target: 6-12 activity types

3. **Define Each Activity Type**
   
   For each activity type:
   - **Name**: 3-6 words, active voice, general boundary (e.g., "Explore Possibilities", "Build Trust", "Manage Economics")
   - **Description**: Single sentence describing the execution boundary
   - **Focus Assignment**: Which focus area this work primarily supports
   - **Contributes To**: Which essential concerns (and states) this activity type advances
     - Example: "Explore Possibilities" → Opportunity (Identified, Scoped), Requirements (Elicited)
   - **Required Competencies**: Which universal competencies (from Step 5) are needed
   - **Source Phase 1 Activities**: List of specific activities abstracted into this type

**Quality Checks:**
- ✓ Names are generalizable (not tool/vendor specific)
- ✓ Descriptions define clear execution boundaries
- ✓ 6-12 total activity types (not more than 12, not fewer than 6)
- ✓ Each activity type assigned to a focus
- ✓ contributesTo maps to essential concern states
- ✓ Coverage: Every essential concern state has ≥1 supporting activity type

**Output Section:**

```markdown
## Generalizable Activity Types (Future ActivitySpaces)

Total: [X activity types] across [Y focuses]

### Activity Type 1: [Name]
- **Description**: [Single sentence execution boundary]
- **Focus**: [Value | Solution | Engagement | etc.]
- **Contributes To**: 
  - [Concern Name] → [State 1], [State 2]
  - [Concern Name] → [State 3]
- **Required Competencies**: [Competency names from Step 5]
- **Source Phase 1 Activities**: [List of specific activities abstracted]

[Repeat for 6-12 activity types]
```

### Step 5: Identify Universal Competencies

**Universal Competencies are broad skill categories with 5-level progressions.**

**Distillation Process:**

1. **Review All Phase 1 Competencies and Personas**
   - Extract skill categories (not specific roles)
   - Identify expertise areas rather than job titles
   - Example: "Cloud Architecture" (skill) not "Cloud Architect" (role)

2. **Generalize to Universal Skill Categories**
   
   If Phase 1 has:
   - "Platform Engineer", "Infrastructure Engineer", "SRE" → "Platform Engineering"
   - "Security Architect", "Security Engineer", "Compliance Specialist" → "Security and Compliance"
   
   Target: 5-10 competencies

3. **Define 5-Level Progression for Each Competency**
   
   **Standard 5-Level Pattern:**
   1. **Basic**: Understands fundamental concepts, requires guidance
   2. **Applies**: Can execute standard tasks with minimal supervision
   3. **Masters**: Independent proficiency, handles complexity
   4. **Adapts**: Adapts approaches to novel situations, mentors others
   5. **Innovating**: Creates new practices, recognized expert
   
   For each competency:
   - **Name**: 2-4 words (skill category, not role)
   - **Description**: Single sentence describing expertise area
   - **Levels**: 5 levels following the progression pattern
     - Each level: Name, Description (specific skill and experience expectations)

**Quality Checks:**
- ✓ Names are skill categories (not role titles)
- ✓ 5 levels per competency (standard progression)
- ✓ 5-10 total competencies
- ✓ Level descriptions are actionable (what someone can DO at this level)
- ✓ Coverage: All activity types from Step 4 reference valid competencies

**Output Section:**

```markdown
## Universal Competencies

Total: [X competencies]

### Competency 1: [Name]
- **Description**: [Single sentence expertise area]
- **Levels**:
  1. **Basic**: [Description - understands concepts, requires guidance]
  2. **Applies**: [Description - executes tasks with minimal supervision]
  3. **Masters**: [Description - independent proficiency]
  4. **Adapts**: [Description - handles complexity, mentors]
  5. **Innovating**: [Description - creates new practices, expert]
- **Source Phase 1 Competencies/Personas**: [List abstracted from]

[Repeat for 5-10 competencies]
```

### Step 6: Identify Narrative Frameworks

**Narrative Frameworks are reusable storytelling structures with sequential elements.**

**Distillation Process:**

1. **Review Phase 1 Workflows and Patterns**
   - Look for storytelling patterns in source methodology
   - Identify lifecycle narratives (journey structures)
   - Note explicit frameworks mentioned (STAR, Agile ceremonies, etc.)

2. **Identify 3-5 Narrative Types**
   
   **Universal Frameworks (always consider):**
   - **STAR**: Situation, Task, Action, Result (tactical)
   - **Hero's Journey**: Ordinary World, Call to Adventure, Ordeal, Return (transformation)
   - **Three-Act / StoryBrand**: Hero+Problem, Guide+Plan, Call to Action+Success (solution positioning)
   - **Micro-Narratives (ABT)**: And (context), But (conflict), Therefore (resolution) (daily updates)
   
   **Domain-Specific Frameworks (if source suggests):**
   - Example: Partner Ecosystem Journey (Discovery, Alignment, Collaboration, Maturity)
   - Example: Platform Adoption Journey (Assess, Design, Build, Operate, Optimize)
   
   Target: 3-5 narrative types

3. **Define Each Narrative Type**
   
   For each narrative type:
   - **Name**: Framework name (recognizable or domain-specific)
   - **Description**: When to use (macro-level lifecycle, tactical execution, daily updates)
   - **Narrative Elements**: Sequential components (3-7 elements)
     - Each element: Name, Description (what it represents), HowToUse (guidance for practitioners)

**Quality Checks:**
- ✓ 3-5 narrative types (not more than 5)
- ✓ Mix of universal frameworks + domain-specific if applicable
- ✓ Elements are sequential (tell a story progression)
- ✓ HowToUse provides actionable guidance (not just definitions)

**Output Section:**

```markdown
## Narrative Frameworks (Future NarrativeTypes)

Total: [X narrative types]

### Narrative 1: [Name]
- **Description**: [When to use - macro/tactical/daily]
- **Narrative Elements**:
  1. **[Element Name]**: [What it represents] — **How to Use**: [Practitioner guidance]
  2. **[Element Name]**: [What it represents] — **How to Use**: [Practitioner guidance]
  [... 3-7 elements]

[Repeat for 3-5 narrative types]
```

### Step 7: Quality Validation

Before finalizing, validate the distillation:

**Focus Area Validation:**
- [ ] 2-4 focuses defined with clear scope
- [ ] All essential concerns assigned to exactly one focus
- [ ] Focus distribution is balanced (no single focus >50% of concerns)
- [ ] Rationale documented for default vs custom focuses

**Outcome Validation:**
- [ ] 1-3 baseline-level outcomes distilled from Phase 1
- [ ] Each outcome has a measurement approach
- [ ] Terminology is framework-level (not vendor-specific)
- [ ] Each outcome maps to at least one essential concern

**Essential Concerns Validation:**
- [ ] 8-15 essential concerns (not more, not fewer)
- [ ] Terminology is neutral, framework-level (no vendor names)
- [ ] Each concern has 5-7 progressive states
- [ ] Relationships documented (relatesTo will use these)
- [ ] Coverage across all focuses

**Activity Types Validation:**
- [ ] 6-12 activity types (not more, not fewer)
- [ ] Names are generalizable execution boundaries
- [ ] Every essential concern state has ≥1 supporting activity type
- [ ] contributesTo mappings are complete
- [ ] requiredCompetencies reference valid competencies

**Competencies Validation:**
- [ ] 5-10 competencies
- [ ] Names are skill categories (not roles)
- [ ] All competencies have exactly 5 levels
- [ ] Level descriptions are actionable

**Narrative Frameworks Validation:**
- [ ] 3-5 narrative types
- [ ] Mix of universal + domain-specific frameworks
- [ ] Elements are sequential with howToUse guidance

**Cross-Section Validation:**
- [ ] Activity types reference competencies from Step 5
- [ ] Activity types contribute to concerns from Step 3
- [ ] All focuses used across concerns and activity types
- [ ] No orphaned elements (everything referenced)

### Step 8: Final Output Structure

**Write to: `baselines/<name>/01.5-distilled-essentials.md`**

**Document Structure:**

```markdown
# Baseline Distillation: [Baseline Name]

**Date**: [YYYY-MM-DD]
**Phase**: 1.5 - Distillation
**Source**: baselines/<name>/01-analysis-report.md

---

## Executive Summary

[2-3 paragraphs summarizing the distillation:
- What source methodology was analyzed
- Key decision (default vs custom focuses) and rationale
- Number of essential concerns, activity types, competencies, narratives identified
- Overall scope of the baseline]

---

## Focus Areas

[Complete Focus Areas section from Step 2]

---

## Essential Concerns (Future Baseline Alphas)

[Complete Essential Concerns section from Step 3]

---

## Baseline Outcomes (Future Outcome Templates)

### [Outcome Name]
**Description:** ...
**Measurement Approach:** ...
**Related Essential Concerns:** ...
**Source Phase 1 Outcomes:** ...

---

## Generalizable Activity Types (Future ActivitySpaces)

[Complete Activity Types section from Step 4]

---

## Universal Competencies

[Complete Competencies section from Step 5]

---

## Narrative Frameworks (Future NarrativeTypes)

[Complete Narrative Frameworks section from Step 6]

---

## Distillation Statistics

- **Phase 1 Outcomes Analyzed**: [X]
- **Baseline Outcomes Identified**: [Y]
- **Phase 1 Concerns Analyzed**: [X]
- **Essential Concerns Identified**: [Y] (distillation ratio: [Y/X])
- **Phase 1 Activities Analyzed**: [X]
- **Activity Types Identified**: [Y] (distillation ratio: [Y/X])
- **Phase 1 Competencies Analyzed**: [X]
- **Universal Competencies Identified**: [Y] (distillation ratio: [Y/X])
- **Focus Areas**: [X] ([DEFAULT | CUSTOM])
- **Narrative Frameworks**: [X]

---

## Next Steps

This distilled essentials report serves as the PRIMARY input for Phase 2: Baseline Mapping.

Phase 2 will transform these distilled elements into:
- **Focuses** array (JSON structure)
- **Outcomes** array (from baseline outcomes with measurement approaches)
- **Alphas** array (with relatesTo relationships from concern relationships)
- **ActivitySpaces** array (from activity types with contributesTo mappings)
- **Competencies** array (with 5-level competencyLevels structure)
- **NarrativeTypes** array (with narrativeElements structure)
```

## Quality Standards

**Conciseness**: This is a distillation, not expansion. Aim for 15-25K words (vs Phase 1's 30-50K).

**Universality**: Every element should be generally applicable, not practice-specific. Use the "Would this apply to any organization in this domain?" test.

**Neutrality**: Avoid vendor names, tool names, platform names. Use framework-level terminology.

**Traceability**: Document which Phase 1 elements were merged/abstracted into each distilled element.

**Coherence**: Focuses should group related concerns logically. Activity types should clearly support concern progressions. Competencies should clearly map to activity requirements.

## Common Pitfalls to Avoid

❌ **Including too many concerns**: If you have >15 essential concerns, merge more aggressively.
❌ **Practice-specific language**: "AWS Lambda" → "Serverless Compute", "Jira" → "Work Tracking"
❌ **Undefined relationships**: Document concern relationships explicitly (produces, governed by, uses)
❌ **Unbalanced focuses**: One focus with 2 concerns and another with 10 suggests poor grouping
❌ **Role-based competencies**: "Product Manager" → "Product Management", "DevOps Engineer" → "DevOps Practices"
❌ **Too many activity types**: If you have >12, you're not generalizing enough
❌ **Missing state coverage**: Every essential concern state needs ≥1 activity type supporting it
❌ **Inconsistent level progressions**: All competencies should use the 5-level pattern

## Success Criteria

✅ Focus areas clearly defined with rationale for default vs custom
✅ 8-15 essential concerns with universal scope
✅ 6-12 generalizable activity types mapped to concerns
✅ 5-10 universal competencies with 5-level progressions
✅ 3-5 narrative frameworks with sequential elements
✅ All cross-references valid (activity types → concerns → focuses)
✅ Neutral, framework-level terminology throughout
✅ Documented traceability to Phase 1 elements
✅ Output file: `baselines/<name>/01.5-distilled-essentials.md` (~15-25K words)
