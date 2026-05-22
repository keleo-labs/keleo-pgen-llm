# Phase 1 Module 00: Method Planning (Multi-Practice)

**Execution Context:** This is the first module when translating a methodology that requires MULTIPLE practices (a Method). Use this instead of `00-analysis-plan.md` when the source methodology needs to be partitioned into multiple distinct practices.

---

## Role and Objective

You are a **Practice Research Analyst** performing strategic analysis of a complex methodology that requires multiple practices to represent fully.

**Goal:** Create a high-level method plan that:
1. Identifies all constituent practices and their boundaries
2. Determines dependencies between practices
3. Plans the generation strategy for each practice
4. Establishes cross-practice integration points

**Output:** Method planning document (~4,000-6,000 words) that serves as the blueprint for generating all constituent practices.

---

## Required Resources

1. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Understand baseline structure
   
2. **Framework Guidance** - `references/domain-framework.md`
   - Four-perspective analysis framework
   
3. **Semantic Guidance** - `references/semantics.md`
   - Practice partitioning principles
   
4. **Maturity Rubric** - `references/workproduct-assessment-rubric.csv`
   - Assessment framework
   
5. **User-provided source materials** - The methodology being analyzed

---

## Analysis Framework

### Step 1: High-Level Methodology Assessment

**Overall Scope Analysis:**

Analyze the complete source methodology:
- What is the total scope covered?
- What are the major domains or capability areas?
- What are the distinct stakeholder journeys?
- What are the different use cases or contexts?

**Maturity Assessment:**

Apply the four-perspective framework at a high level:
- Business perspective: Level [0-4]
- Technology perspective: Level [0-4]
- People perspective: Level [0-4]
- Process perspective: Level [0-4]

### Step 2: Practice Partitioning Strategy

**Determine Practice Boundaries:**

A methodology should be partitioned into multiple practices when it has:

1. **Distinct Value Streams:**
   - Platform building vs platform consuming
   - Developer-focused vs operator-focused
   - Strategic planning vs tactical execution

2. **Different Use Cases:**
   - Greenfield vs brownfield
   - Cloud-native vs hybrid/on-prem
   - Single-tenant vs multi-tenant

3. **Separate Stakeholder Journeys:**
   - Executive decision-making
   - Team-level implementation
   - Individual contributor practices

4. **Independent Capability Domains:**
   - Security practices
   - Cost optimization practices
   - Developer experience practices
   - That can be adopted independently

**Avoid Over-Partitioning:**

Do NOT create separate practices for:
- Functional decomposition (e.g., "Testing Practice", "Coding Practice")
- Arbitrary phase splitting (e.g., "Planning Practice", "Execution Practice")
- Single activities or small clusters of work

**Each practice should be:**
- Cohesive (internally unified)
- Value-additive (delivers concrete outcomes)
- Independently usable (can be adopted without all others, though may have dependencies)
- Perspective-balanced (addresses business, technology, people, or process holistically for its domain)

### Step 3: Practice Definition

For EACH practice identified:

**Practice Identity:**
- Name: [Practice Name in kebab-case]
- Primary Purpose: [1-2 sentences]
- Primary Value Stream: [What outcome it enables]
- Primary Perspectives: [Business/Technology/People/Process - which dominate]

**Scope Boundaries:**
- What's In Scope: [What this practice covers]
- What's Out of Scope: [What it doesn't cover - handled by other practices]
- Key Distinguishing Features: [What makes it distinct from other practices]

**Expected Complexity:**
- Alpha Count: [Estimated number]
- Activity Count: [Estimated number]
- Pattern Count: [Estimated number]
- Word Count Estimate: [Rough estimate for this practice]

### Step 4: Dependency Mapping

**Practice Dependencies:**

For each practice, identify:
- **Prerequisites:** Which practices MUST be understood/adopted first
- **Complements:** Which practices work well together
- **Alternatives:** Which practices address similar problems differently (choose one)

**Dependency Justification:**

Explain WHY dependencies exist:
- Foundational concepts defined in prerequisite
- Shared alphas or work products
- Organizational readiness requirements
- Logical progression of adoption

### Step 5: Integration Points

**Cross-Practice Elements:**

Identify elements that span practices:
- Shared alphas (same alpha referenced in multiple practices)
- Shared work products
- Coordinating patterns (patterns that span practices)

**Integration Strategy:**

- Which practice "owns" shared elements?
- How are shared elements referenced across practices?
- Are there method-level orchestration patterns?

---

## Output Structure

---

## Executive Summary

[2-3 paragraphs]

**First Paragraph:** Describe the overall methodology scope and why it requires multiple practices to represent fully.

**Second Paragraph:** Explain the partitioning strategy - how many practices, what distinguishes them, how they work together.

**Third Paragraph:** Highlight the key value of this method composition - why the sum is greater than the parts.

---

## Method Overview

**Method Name:** [Name of overall method]

**Description:** [2-3 sentence description of what the complete method provides]

**Baseline Practice:** Platform Adoption Essentials

**Number of Practices:** [Count]

**Primary Use Case:** [When organizations should adopt this method]

**Key Characteristics:**
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

---

## Practice Composition

[For EACH practice, create a section]

### Practice 1: [Practice Name]

**Directory:** `practice-1/` (or use practice-specific kebab-case name)

**Primary Purpose:** [What this practice enables - 1-2 sentences]

**Value Stream:** [What outcome this practice delivers]

**Primary Perspectives:** [Business | Technology | People | Process - which dominate this practice]

**Scope:**

**In Scope:**
- [What this practice covers - bulleted list]
- [Key alphas, activities, patterns expected]

**Out of Scope:**
- [What this practice doesn't cover - handled by other practices]

**Key Distinguishing Features:**
- [What makes this practice unique]
- [Target audience or use case]

**Dependencies:**

**Prerequisites:** [List practice names that must be understood first, or "None"]
- [Practice Name]: [Reason for dependency]

**Complements:** [List practices that work well with this one]
- [Practice Name]: [How they complement each other]

**Four-Perspective Assessment:**

- **Business:** [Maturity level 0-4] - [Brief assessment]
- **Technology:** [Maturity level 0-4] - [Brief assessment]
- **People:** [Maturity level 0-4] - [Brief assessment]
- **Process:** [Maturity level 0-4] - [Brief assessment]

**Expected Complexity:**

- **Alphas:** ~[Estimated count] ([X] redeclarations, [Y] new, [Z] instances)
- **Work Products:** ~[Estimated count]
- **Activities:** ~[Estimated count]
- **Personas:** ~[Estimated count]
- **Patterns:** ~[Estimated count]
- **Estimated Output:** ~[Estimated total word count]
- **Splitting Required:** [Yes/No - if modules will need splitting by focus]

**Narrative Framework for Intent:**

**MANDATORY:** This practice will include at least one narrative summarizing its intent and objective using one of these baseline narrative templates:
- [RECOMMENDED FRAMEWORK: The STAR Format | The Hero's Journey | The Three-Act Structure & StoryBrand | Micro-Narratives (ABT) | Essay Narrative | Epic | Report Narrative]
- [WHY THIS FRAMEWORK: Brief justification for why this narrative framework suits this practice's story]

**Alpha Planning Preview:**

[Brief list of expected alphas with type]
- [Alpha Name] - Redeclaration
- [Alpha Name] - New (Specialization)
- [Alpha Name] - Instances expected

**Activity Planning Preview:**

[Brief list of expected key activities]
- [Activity Name] → [ActivitySpace]
- [Activity Name] → [ActivitySpace]

**Pattern Planning Preview:**

[Brief description of expected patterns]
- [Pattern Name] - [Type]

---

### Practice 2: [Practice Name]

[Repeat structure for each practice]

---

## Integration and Orchestration

### Cross-Practice Elements

**Shared Alphas:**

[List alphas that appear in multiple practices]

- **[Alpha Name]:**
  - Owned by: [Practice Name]
  - Referenced by: [Practice Names]
  - Integration approach: [How practices coordinate on this alpha]

**Shared Work Products:**

[List work products referenced across practices]

- **[Work Product Name]:**
  - Created by: [Practice Name]
  - Used by: [Practice Names]
  - Integration approach: [How practices share this artifact]

**Coordinating Patterns:**

[List patterns that span multiple practices]

- **[Pattern Name]:**
  - Type: [Lifecycle | Multi-Practice Workflow]
  - Practices involved: [List]
  - Purpose: [How this coordinates practices]

### Method-Level Narratives

[Optional: Create method-level narratives explaining the overall journey]

**[Narrative Title]**

**Narrative Type:** [The Three-Act Structure & StoryBrand | Epic | etc.]

[Multi-paragraph narrative explaining the overall method adoption journey across all practices]

---

## Adoption Sequence Recommendation

**Recommended Adoption Path:**

[Provide guidance on which practices to adopt in what order]

1. **[Practice Name]** - [Rationale for starting here]
2. **[Practice Name]** - [Rationale for this being next]
3. **[Practice Names]** - [These can be adopted in parallel after prerequisites]
4. **[Practice Name]** - [Advanced/optional practice]

**Minimum Viable Adoption:**

[Which practices represent the minimum useful subset]

To achieve [specific outcome], organizations must adopt:
- [Practice Name] - [Why essential]
- [Practice Name] - [Why essential]

**Full Adoption:**

[What capabilities unlock with complete adoption]

Complete method adoption provides:
- [Capability 1]
- [Capability 2]
- [Capability 3]

---

## Citation Strategy

**Primary Sources:** [5-15 total for method]

[List authoritative sources that inform the overall method]

1. **[Title]** - Authors: [Names/Org], Date: [Year], Type: Primary
2. [Continue list]

**Citation Distribution:**

[How citations will be distributed across practices]

- Practice 1: [Expected citation count] - [Types of sources]
- Practice 2: [Expected citation count] - [Types of sources]
- Method-level: [Citations that apply to overall method]

---

## Module Generation Roadmap

Based on this analysis, the generation sequence should be:

### Phase 1: Method Planning (This Document)

**Output:** `report-elements/00-method-plan.md`

### Phase 2: Practice 1 Generation

**Directory:** `report-elements/practice-1/`

**Modules to Generate:**
1. 00-analysis-plan.md - Practice-specific planning
2. 01-practice-details.md
3. 02-citations.md
4. 03-alphas.md [Split by focus if estimated >20K words]
5. 04-workproducts.md
6. 05-activities-roles.md
7. 06-patterns.md
8. 07-aliases.md (if needed)

**Estimated Timeline:** [Rough estimate of generation effort]

### Phase 3: Practice 2 Generation

[Repeat for each practice]

### Phase 4: Method Assembly

**Module:** `report-elements/08-method-assembly.md`

**Purpose:** Describe how practices integrate and orchestrate

### Phase 5: Final Assembly

**Outputs:**
- `research-report.md` - Complete method documentation
- `cross-reference-index.json` - Validation index for all practices
- Phase 2 ready for JSON generation

---

## Quality Checks

Before proceeding to practice generation:

- [ ] Practice partitioning is justified (not arbitrary decomposition)
- [ ] Each practice is cohesive and value-additive
- [ ] Dependencies are clearly identified and justified
- [ ] Integration points are documented
- [ ] Expected complexity is reasonable (each practice is substantial but manageable)
- [ ] Adoption sequence provides clear guidance
- [ ] No practice is just a functional decomposition (avoid "Testing Practice", etc.)
- [ ] Citation strategy covers all practices

---

## Execution Instructions

1. Read all required resources (baseline, references, source materials)
2. Assess overall methodology scope and complexity
3. Apply practice partitioning strategy to identify distinct practices
4. For each practice:
   - Define identity, scope, boundaries
   - Assess across four perspectives
   - Estimate complexity
   - Plan alphas, activities, patterns at high level
5. Map dependencies between practices
6. Identify integration points and shared elements
7. Plan citation distribution
8. Create module generation roadmap
9. Output complete method planning document

**Success Criteria:**
- Clear rationale for multiple practices
- Each practice is cohesive and valuable independently
- Dependencies are logical and documented
- Integration strategy is clear
- Roadmap provides clear path for generation

**Output:** Save to `practices/<method-name>/report-elements/00-method-plan.md`
