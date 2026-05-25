# Phase 1 Module 06: Patterns and Pattern Views

**Execution Context:** This module generates patterns that orchestrate practice elements into cohesive lifecycle progressions or scenario-based workflows.

**Size Estimate:** ~10,000-15,000 words depending on pattern complexity.

---

## Role and Objective

You are a **Practice Research Analyst** defining patterns that show how alphas, work products, and activities coordinate across time or scenarios.

**Input:**
- Module 00 analysis-plan.md (pattern plan)
- Module 03 alphas.md (alphas and instances to track)
- Module 04 workproducts.md (work products and instances to track)
- Module 05 activities-roles.md (activities to reference)
- Source methodology materials
- Baseline framework

**Output:** Patterns document (~10,000-15,000 words) containing pattern definitions with pattern views showing progression or scenarios.

---

## Required Resources

1. **Read Module 00** - `report-elements/00-analysis-plan.md`
   - Review pattern plan
   
2. **Read Module 03** - `report-elements/03-alphas.md`
   - Extract alpha names, state names, and alpha instance names
   
3. **Read Module 04** - `report-elements/04-workproducts.md`
   - Extract work product names, LOD names, and work product instance names
   
4. **Read Module 05** - `report-elements/05-activities-roles.md`
   - Extract activity names and activity space names
   
5. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Extract NarrativeType names if pattern uses narrative framework
   
6. **Source Materials** - User-provided methodology documentation

---

## Pattern Types

### Lifecycle Patterns

**Purpose:** Show temporal progression through phases

**Structure:** Sequential pattern views representing phases/stages

**Tracks:** How alphas advance states, how work products evolve, which activities are active

**Example:** Platform Adoption Lifecycle (Strategy → Planning → Implementation → Operations → Optimization)

### Problem-Solution Patterns

**Purpose:** Address specific recurring challenges

**Structure:** Pattern views showing problem context, solution approach, validation

**Tracks:** Specific alpha instances, targeted work products, recommended activities

**Example:** Platform Migration Pattern (Assessment → Planning → Pilot → Rollout → Stabilization)

### Feature Delivery Patterns

**Purpose:** Guide delivery of specific capabilities

**Structure:** Pattern views showing capability phases

**Tracks:** Capability-specific alpha instances and work products

**Example:** Golden Path Definition Pattern (Discovery → Design → Implementation → Adoption)

---

## Output Structure

---

## Patterns

### Pattern: [Pattern Name]

**Type:** Lifecycle | Problem-Solution | Feature Delivery | [Other specific type]

**Narrative Framework:** [NarrativeType Name from baseline if applicable, otherwise "None"]

**Description:**

Write a single SHORT sentence (8-15 words, max 20 words) that captures what this pattern orchestrates.

**Guidelines:**
- **What it orchestrates:** The lifecycle or workflow being coordinated
- **Brevity:** Aim for 8-15 words, absolute maximum 20 words
- **No elaboration:** Save structure, views, timing, anti-patterns for narratives below
- **Direct language:** Describe the orchestration itself

**Examples:**
- ❌ BAD (52 words): "The Platform Development Lifecycle pattern orchestrates the complete journey from initial platform conception through design, implementation, deployment, and ongoing operations by coordinating activities across multiple teams and ensuring proper progression through alpha states while maintaining alignment with organizational governance and delivering measurable business value."
- ✅ GOOD (11 words): "Orchestrates platform journey from conception through design, deployment, and operations."

- ❌ BAD (45 words): "The Automation Content Development pattern coordinates the iterative process of creating, testing, validating, and publishing automation artifacts by bringing together content developers, reviewers, and consumers while ensuring quality standards are met and operational knowledge is properly encoded in reusable playbooks and roles."
- ✅ GOOD (12 words): "Coordinates iterative development, testing, and publication of reusable automation artifacts."

**For detailed context:** Use Pattern-Level Narratives and Phase Context sections below with citations.

---

#### Pattern-Level Narratives

[If the pattern uses a narrative framework, create pattern-level narratives providing overall context]

**[Narrative Title]**

**Narrative Type:** [NarrativeType Name - e.g., "The Three-Act Structure & StoryBrand"]

[Structure prose according to the narrative framework specified in the pattern's narrativeTypeName]

**For StoryBrand (Hero's Journey):**

**Hero:**
[Describe the protagonist - typically the team or organization adopting this pattern]

**Problem:**
[Describe the challenge or need this pattern addresses]

**Guide:**
[Describe how this pattern/practice guides the hero]

**Plan:**
[Outline the pattern's approach]

**Action:**
[Describe what the hero does following the pattern]

**Success:**
[Describe the transformation and outcomes]

**Citations Referenced:** [List citation names from Module 02 that support this pattern, or omit if based on general practice]

**For Lifecycle Narrative:**

[Describe the overall journey through the pattern phases at a high level - 3-5 paragraphs]

**Citations Referenced:** [List citation names from Module 02]

---

#### Pattern Views (Phases)

[Create pattern views showing progression - minimum 1, typically 3-7]

##### Phase 0: Prerequisites

[For lifecycle patterns, always start with a prerequisites phase at seq: 0]

**Phase Description:**

Single SHORT sentence (8-12 words) describing this view's perspective and emphasis.

**Guidelines:**
- **The perspective:** What this phase focuses on
- **Brevity:** Aim for 8-12 words, absolute maximum 12 words
- **Direct language:** Describe the phase itself

**Examples:**
- ❌ BAD (24 words): "This view emphasizes the technical implementation perspective by focusing on solution architecture, infrastructure design, and deployment activities while tracking platform and automation content alphas through their technical maturity states."
- ✅ GOOD (8 words): "Technical implementation perspective focusing on architecture and deployment."

- ❌ BAD (21 words): "The business value perspective tracks the progression from initial value identification through capability delivery and benefit realization while ensuring stakeholder alignment and measuring outcomes."
- ✅ GOOD (9 words): "Business perspective tracking value identification through benefit realization."

**For detailed context:** Use Phase Context section below to elaborate on what needs to be in place, foundational states, and prerequisite work.

**Areas of Concern at this Phase:**

By the end of this phase, the following concepts should reach these states:

- **[Alpha Name]** should reach the **[State Name]** state
- **[Alpha Name]** should reach the **[State Name]** state

[List baseline alphas and target states]

**Specific Instances Tracked:**

- **[Alpha Instance Name]** (instance of **[Alpha Name]**) should reach **[State Name]**
- **[Alpha Instance Name]** (instance of **[Alpha Name]**) should reach **[State Name]**

[List specific alpha instances if this pattern tracks them]

**Key Deliverables:**

At this phase, the following artifacts should reach these levels of detail:

- **[Work Product Instance Name]** (**[Work Product Name]**) should reach **[Level Name]** level
- **[Work Product Instance Name]** (**[Work Product Name]**) should reach **[Level Name]** level

[List work product instances and target LODs]

**Active Work:**

The primary activity spaces active during this phase include:
- [ActivitySpace Name]
- [ActivitySpace Name]

Specific activities being performed:
- [Activity Name]
- [Activity Name]

[List active activity spaces and specific activities]

**Phase Context:**

**Narrative Context Guidelines:**

Each context element should be **1-2 sentences maximum**, conveying specific insights about this phase. Avoid multi-paragraph exposition.

[Provide focused context points:]
- What's happening during this phase (1-2 sentences)
- Why these particular states/deliverables matter (1-2 sentences)
- Key challenges or success factors (1-2 sentences)
- Dependencies or sequencing considerations if critical (1-2 sentences)

**Citations Referenced:** [List citation names from Module 02 supporting this phase guidance, or omit if based on general practice]

**Phase Narratives:**

[If using a narrative framework at pattern level, add phase-specific narrative contexts]

**[Narrative Element Name from Pattern's NarrativeType]:**

[Prose content mapping this phase to the narrative element - 1-2 sentences conveying the specific point]

**Citations Referenced:** [List citation names if this narrative element references specific sources]

---

##### Phase 1: [Phase Name]

**Phase Description:**

[Same structure as Prerequisites]

**Areas of Concern at this Phase:**

[Same structure - note that alphas should show progression from previous phase]

**Specific Instances Tracked:**

[Same structure]

**Key Deliverables:**

[Same structure - work products should show advancement from previous phase]

**Active Work:**

[Same structure]

**Phase Context:**

[Same structure]

**Phase Narratives:**

[If applicable]

---

[Continue for all phases - typically 3-7 phases total for lifecycle patterns]

---

##### Phase N: [Final Phase Name]

[Same structure as previous phases]

---

#### Pattern Summary

[Create a summary table showing the progression]

Below is a summary view of how areas of concern and deliverables progress through this pattern:

| Element | Prerequisites | [Phase 1 Name] | [Phase 2 Name] | [Phase 3 Name] | [Phase N Name] |
|:--------|:--------------|:---------------|:---------------|:---------------|:---------------|
| **Core Concepts** ||||||
| [Alpha Name] | [State] | [State] | [State] | [State] | [State] |
| [Alpha Name] | [State] | [State] | [State] | [State] | [State] |
| **Specific Instances** ||||||
| [Instance Name] ([Alpha]) | [State] | [State] | [State] | [State] | [State] |
| [Instance Name] ([Alpha]) | [State] | [State] | [State] | [State] | [State] |
| **Key Deliverables** ||||||
| [Instance Name] ([WP]) | [LOD] | [LOD] | [LOD] | [LOD] | [LOD] |
| [Instance Name] ([WP]) | [LOD] | [LOD] | [LOD] | [LOD] | [LOD] |

**Reading the table:**
- Each row shows one alpha or work product
- Each column shows a phase
- Cell values show the target state or level of detail for that phase
- Progression should be left-to-right (increasing maturity)

---

[Repeat Pattern structure for each pattern - typically 1-3 patterns per practice]

---

## Writing Standards

This module follows the centralized writing standards defined in the skill documentation:

**Key Standards for This Module:**
- **Descriptions:** Single-sentence essence only (max 20 words for patterns, max 12 words for pattern views/phases)
- **Phase context:** 1-2 sentences per context point (focused insights, not paragraphs)
- **Narrative contexts:** 1-2 sentences per element (concise, actionable)
- **Element references:** Exact name matching with Modules 03-05
- **Citations:** Reference via citationNames

**For complete guidelines**, see the skill's "Centralized Writing Standards" section, including:
- Descriptive Discipline (essence vs. elaboration)
- Narrative Context Guidelines (concise phase context)
- Pattern-specific conventions (instance tracking, progression)

**Use Pattern-Level Narratives and Phase Context sections for elaboration.**

---

## Writing Guidelines

1. **Prerequisites phase required:** Lifecycle patterns must have a seq: 0 prerequisites phase
2. **Show progression:** Alpha states and work product LODs should advance left-to-right through phases
3. **Instance tracking:** Use specific instance names (from Modules 03/04) when tracking concrete examples
4. **Pruning:** If an alpha doesn't change state across the entire pattern, consider removing it from the pattern
5. **Active pruning between phases:** If an alpha state is the same in two consecutive phases, omit it from the later phase to highlight only active transitions
6. **Rich phase context:** Provide detailed narrative guidance for each phase (not just lists)
7. **Complete references:** All alpha names, state names, work product names, LOD names, activity names must match exactly with previous modules
8. **Narrative frameworks:** If pattern specifies a narrativeTypeName, create pattern-level and phase-level narrative contexts

## Pattern View Sequencing

**seq: 0** - Prerequisites (what must be true before starting)
**seq: 1** - First main phase
**seq: 2** - Second main phase
**seq: N** - Final phase

Sequence numbers must be consecutive integers starting from 0.

## Alpha and Work Product State Progression

**Important Baseline State Clarifications:**

**Platform Alpha States:**
1. Architecture Selected
2. Baselined
3. Provisioned
4. Ready
5. Hosting Assets
6. Evolving (adaptive evolution with continuous feedback)
7. Retiring (systematic decommissioning)

**Platform Asset Alpha States:**
1. Identified
2. Specified
3. Provisioned
4. Integrated
5. Operational
6. Value Yielding (delivering measurable value - NOT decommissioning)
7. Retiring (systematic decommissioning in progress)

When showing alpha progression through phases:
- Early phases: Architecture Selected, Baselined, Provisioned
- Middle phases: Ready, Hosting Assets, Operational
- Later phases: Evolving, Value Yielding
- Final phases (if decommissioning): Retiring

## Instance Tracking Guidelines

**When to track instances in patterns:**
- Source describes multiple concurrent examples (multiple teams, multiple platforms, multiple requirements sets)
- Pattern shows how specific occurrences progress (not just the abstract concept)
- Instances have names (declared in Module 03 or 04)

**Format for instance references:**
- **[Instance Name]** (instance of **[Parent Alpha Name]**)

**Examples:**
- **Platform Team** (instance of **Team**) should reach **Collaborating**
- **API Gateway Capability** (instance of **Platform Asset**) should reach **Operational**
- **Security Requirements** (instance of **Requirements**) should reach **Coherent**

## Pattern Summary Table Guidelines

**Rows to include:**
- Core baseline alphas that progress through the pattern
- Specific instances being tracked
- Key work product instances being developed

**Columns:**
- One column per phase (including Prerequisites)

**Cell values:**
- Alpha cells: State name
- Work product cells: Level of detail name

**Omit cells where state/LOD doesn't change from previous phase** (helps highlight what's actively progressing)

## Execution Instructions

1. Read Modules 00, 03, 04, 05 to understand patterns, alphas, work products, activities
2. Load baseline to extract NarrativeType names if patterns use narrative frameworks
3. For each pattern in Module 00 plan:
   - Define pattern type and narrative framework
   - Create pattern-level overview and narratives (if using narrative framework)
   - Create pattern views (phases):
     - Prerequisites phase (seq: 0) for lifecycle patterns
     - Main phases showing progression
     - For each phase:
       - Define alpha state targets
       - Define alpha instance state targets (if tracking instances)
       - Define work product instance LOD targets
       - List active activity spaces and activities
       - Provide rich phase context narratives
       - Map to narrative framework elements (if applicable)
   - Create pattern summary table showing progression
4. Verify all references:
   - [ ] All alpha names match Module 03
   - [ ] All state names match Module 03
   - [ ] All alpha instance names match Module 03
   - [ ] All work product names match Module 04
   - [ ] All LOD names match Module 04
   - [ ] All work product instance names match Module 04
   - [ ] All activity names match Module 05
   - [ ] All activity space names match baseline
   - [ ] All narrative type names match baseline (if used)

**Output:** Save complete patterns document to be consumed by Phase 2.
