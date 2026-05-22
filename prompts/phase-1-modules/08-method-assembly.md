# Phase 1 Module 08: Method Assembly and Integration

**Execution Context:** This module is generated AFTER all individual practice modules (practice-1/, practice-2/, etc.) have been completed. It describes how practices integrate and provides method-level orchestration guidance.

---

## Role and Objective

You are a **Practice Research Analyst** creating the integration layer for a multi-practice method.

**Input:**
- Module 00-method-plan.md (method planning document)
- All completed practice modules from practice-1/, practice-2/, etc.
- Source methodology materials

**Output:** Method assembly document (~3,000-5,000 words) explaining how practices integrate, method-level patterns, and adoption guidance.

---

## Required Resources

1. **Read Method Plan** - `report-elements/00-method-plan.md`
   - Review practice composition, dependencies, integration points
   
2. **Read All Practice Modules** - `report-elements/practice-*/*.md`
   - Understand what each practice provides
   - Identify actual integration points
   
3. **Source Materials** - User-provided methodology documentation
   - Extract method-level guidance

---

## Purpose of This Module

This module answers:

1. **How do the practices work together?**
   - What are the integration points?
   - How do shared alphas coordinate across practices?
   - How do work products flow between practices?

2. **How should organizations adopt the method?**
   - What's the recommended sequence?
   - What are the dependencies?
   - What's the minimum viable adoption?

3. **What method-level patterns orchestrate practices?**
   - Are there lifecycle patterns spanning multiple practices?
   - Are there coordinating workflows?

4. **What method-level narratives provide context?**
   - Overall transformation story
   - Multi-practice journey

---

## Output Structure

---

## Method Integration and Orchestration

### Method Overview

**Method Name:** [From Module 00]

**Description:** [2-3 sentences describing the complete method]

**Constituent Practices:**

1. **[Practice 1 Name]** - [One sentence purpose]
2. **[Practice 2 Name]** - [One sentence purpose]
3. [Continue for all practices]

**Method Value Proposition:**

[2-3 paragraphs explaining the value of the complete method]

**First Paragraph:** What the integrated method enables that individual practices don't. The synergies and compounding effects.

**Second Paragraph:** Target organizations and use cases. When to adopt the full method vs individual practices.

**Third Paragraph:** Key outcomes and transformation enabled by full method adoption.

---

### Practice Integration Map

[Describe how practices relate to each other]

#### Practice Relationships

**[Practice 1 Name]:**
- **Provides:** [What this practice establishes that others depend on]
- **Requires:** [What this practice needs from other practices]
- **Complements:** [Which practices work synergistically with this one]
- **Integration Points:** [Specific alphas, work products, patterns that connect to other practices]

**[Practice 2 Name]:**

[Repeat for each practice]

#### Dependency Graph

[Create a visual representation of dependencies]

```
Foundational Practices (no dependencies):
└─ [Practice Name]

Layer 1 (depends on foundational):
├─ [Practice Name] → requires [Foundational Practice]
└─ [Practice Name] → requires [Foundational Practice]

Layer 2 (depends on Layer 1):
└─ [Practice Name] → requires [Practice from Layer 1]

Advanced/Optional:
└─ [Practice Name] → requires [Multiple practices]
```

---

### Shared Elements Coordination

[Describe how shared elements are managed across practices]

#### Shared Alphas

**[Shared Alpha Name]:**
- **Owned by:** [Practice that defines/redeclares it]
- **Referenced by:** [Practices that use it]
- **Coordination Strategy:** [How practices coordinate on this alpha]

**Example:**
**Platform:**
- **Owned by:** Platform Foundation Practice
- **Referenced by:** Platform Operations Practice, Platform Security Practice
- **Coordination Strategy:** Platform Foundation establishes the Platform alpha through states Architecture Selected → Ready. Platform Operations continues progression through Hosting Assets → Evolving. Platform Security adds security-specific checklists to states but doesn't change the progression.

[Repeat for each shared alpha]

#### Shared Work Products

**[Shared Work Product Name]:**
- **Created by:** [Practice that defines and primarily creates it]
- **Used by:** [Practices that consume or refine it]
- **Flow:** [How the work product flows between practices]

**Example:**
**Platform Blueprint:**
- **Created by:** Platform Foundation Practice (establishes through Detailed level)
- **Used by:** Platform Operations Practice (references for deployment), Platform Security Practice (validates against security requirements)
- **Flow:** Foundation creates initial blueprint → Security reviews and annotates → Operations uses for deployment planning

[Repeat for each shared work product]

#### Shared Personas and Teams

**[Shared Persona/Team Name]:**
- **Defined by:** [Practice that defines the role]
- **Active in:** [Practices where this role performs activities]
- **Role Evolution:** [How the role's focus changes across practices]

**Example:**
**Platform Team:**
- **Defined by:** Platform Foundation Practice
- **Active in:** All practices (Foundation, Operations, Security, Consumption)
- **Role Evolution:** In Foundation, focuses on architecture and build. In Operations, focuses on reliability and evolution. In Security, focuses on compliance and controls. In Consumption, focuses on enablement and support.

[Repeat for key shared roles]

---

### Method-Level Patterns

[Describe patterns that orchestrate multiple practices]

#### Pattern: [Method-Level Pattern Name]

**Type:** Multi-Practice Lifecycle | Cross-Practice Workflow

**Practices Involved:**
- [Practice Name] - [Role in pattern]
- [Practice Name] - [Role in pattern]

**Purpose:** [What this pattern orchestrates across practices]

[2-3 paragraphs describing the pattern]

**Pattern Views:**

**Phase 0: Prerequisites**

**Practices Active:** [Which practices are involved]

**Key Milestones:**
- [Practice Name]: [Alpha instances/work products at what states/LODs]
- [Practice Name]: [Alpha instances/work products at what states/LODs]

**Phase Context:** [What's happening across practices in this phase]

---

**Phase 1: [Phase Name]**

[Repeat structure for each phase]

---

[Repeat for each method-level pattern - typically 1-3 patterns]

---

### Method-Level Narratives

[Create narratives that tell the overall method adoption story]

#### Narrative: [Narrative Title]

**Narrative Type:** The Three-Act Structure & StoryBrand | Epic | Essay Narrative

[Structure according to narrative framework, telling the multi-practice journey]

**For StoryBrand:**

**Hero:**

[Describe the organization or team adopting the complete method]

**Problem:**

[Describe the complex challenges that require the full method, not just individual practices]

**Guide:**

[Describe how the method guides the hero through transformation]

**Plan:**

[Outline the multi-practice adoption journey]

**Action:**

[Describe what the hero does, practice by practice]

**Success:**

[Describe the transformation achieved through full method adoption]

**For Epic:**

[Tell the long-form story of organizational transformation through method adoption, spanning strategic vision through operational excellence]

---

### Adoption Guidance

#### Adoption Strategies

**Strategy 1: Sequential Foundation-First**

[Describe sequential adoption approach]

**Sequence:**
1. Adopt [Practice Name] first - [Rationale]
2. Then adopt [Practice Name] - [Rationale]
3. Then adopt [Practice Names] in parallel - [Rationale]
4. Finally adopt [Practice Name] - [Rationale]

**Pros:**
- [Benefit 1]
- [Benefit 2]

**Cons:**
- [Drawback 1]
- [Drawback 2]

**Best For:** [Organization types or contexts]

---

**Strategy 2: Parallel Quick-Win**

[Describe parallel adoption approach]

**Sequence:**
1. Adopt [Practice Names] in parallel - [Rationale]
2. Later add [Practice Names] - [Rationale]

**Pros:**
- [Benefit 1]

**Cons:**
- [Drawback 1]

**Best For:** [Organization types or contexts]

---

**Strategy 3: Use-Case Driven**

[Describe use-case specific adoption]

**For [Specific Use Case]:**
- Required practices: [Practice Names]
- Optional practices: [Practice Names]
- Adoption sequence: [Recommendation]

[Repeat for different use cases]

---

#### Minimum Viable Adoption

**To achieve [Specific Outcome]:**

**Must Adopt:**
- [Practice Name] - [Why essential]
- [Practice Name] - [Why essential]

**Should Consider:**
- [Practice Name] - [Added value]

**Can Defer:**
- [Practice Name] - [When it becomes relevant]

---

#### Full Method Adoption

**Complete Adoption Provides:**

- [Capability 1]
- [Capability 2]
- [Capability 3]

**Organizational Readiness Required:**

- [Readiness factor 1]
- [Readiness factor 2]

**Expected Timeline:** [Rough estimate for full adoption]

**Success Indicators:**
- [Indicator 1]
- [Indicator 2]

---

### Cross-Practice Coordination Mechanisms

[Describe how organizations should coordinate across practices]

**Governance:**
[How organizations govern multi-practice adoption]

**Knowledge Sharing:**
[How teams share learning across practices]

**Tooling Integration:**
[How tools and platforms integrate across practices]

**Measurement:**
[How success is measured across the method]

---

### Method Extensions and Customization

[Guidance on adapting the method]

**Common Customizations:**

- [Customization 1]: [When and how to adapt]
- [Customization 2]: [When and how to adapt]

**Industry-Specific Adaptations:**

- **[Industry]:** [How to adapt for this industry]
- **[Industry]:** [How to adapt for this industry]

**Scale Considerations:**

- **Startup/Small:** [How to scale down]
- **Enterprise/Large:** [How to scale up]

---

## Writing Guidelines

1. **Focus on integration:** Don't repeat practice details, focus on how they work together
2. **Clear dependencies:** Make practice dependencies explicit and justified
3. **Practical adoption guidance:** Provide concrete sequencing recommendations
4. **Real coordination mechanisms:** Describe actual integration points, not theoretical ones
5. **Multiple paths:** Recognize that different organizations will adopt differently
6. **Honest about complexity:** Don't oversimplify multi-practice adoption

## Execution Instructions

1. Read Module 00-method-plan.md to understand the planned structure
2. Read all completed practice modules (practice-1/, practice-2/, etc.)
3. Identify actual shared elements across practices:
   - Which alphas appear in multiple practices?
   - Which work products are referenced across practices?
   - Which personas/teams span practices?
4. Create integration descriptions for each shared element
5. Identify or create method-level patterns that orchestrate practices
6. Create method-level narratives telling the overall story
7. Develop practical adoption guidance with multiple strategies
8. Describe coordination mechanisms
9. Output complete method assembly document

**Cross-Reference Check:**

Verify:
- [ ] All practices from Module 00 are addressed
- [ ] All shared elements identified in Module 00 are described
- [ ] All practice dependencies are explained
- [ ] At least one adoption strategy is provided
- [ ] Method-level patterns (if any) are complete
- [ ] Integration points are specific and actionable

**Output:** Save to `practices/<method-name>/report-elements/08-method-assembly.md`
