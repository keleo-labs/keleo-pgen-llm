# Phase 1 Module 04: Work Products and Work Product Instances

**Execution Context:** This module generates all work product definitions with their levels of detail and alpha contributions. Work products are the tangible artifacts that provide evidence of alpha state progression.

**Size Estimate:** ~10,000-15,000 words depending on methodology richness.

---

## Role and Objective

You are a **Practice Research Analyst** defining work products (evidentiary artifacts) that track and prove alpha progression.

**Input:**
- Module 00 analysis-plan.md (work product plan)
- Module 03 alphas.md (to reference alpha states)
- Module 02 citations.md (for references)
- Source methodology materials
- Maturity rubric

**Output:** Work products document (~10,000-15,000 words) containing all work product definitions with levels of detail.

---

## Required Resources

1. **Read Module 00** - `report-elements/00-analysis-plan.md`
   - Review work product plan
   
2. **Read Module 03** - `report-elements/03-alphas.md` (or 03a/03b/03c if split)
   - Extract all alpha names and state names for referencing
   
3. **Read Module 02** - `report-elements/02-citations.md`
   - Reference citations when appropriate
   
4. **Maturity Rubric** - `references/workproduct-assessment-rubric.csv`
   - Use levels 0-4 to inform LOD progression
   
5. **Source Materials** - User-provided methodology documentation

---

## Size Management

**Target:** 3,000-15,000 words per file
**Warning Threshold:** 18,000 words
**Maximum:** 20,000 words

**If content exceeds 18,000 words:**

This module may need to be split by focus or work product category:

1. **STOP** before completing the full module if it appears content will exceed 18,000 words
2. **SPLIT** using one of these strategies:
   - **By Focus:** `04a-workproducts-value.md`, `04b-workproducts-solution.md`, `04c-workproducts-endeavor.md`
   - **By Category:** `04a-workproducts-strategic.md`, `04b-workproducts-operational.md`, `04c-workproducts-technical.md`
3. **CREATE** each file independently with its own section
4. **INCLUDE** common sections (Work Product Principles, Writing Guidelines) in each file

The skill will monitor output size and recommend splits if needed. After generating, the word count will be checked using `python -m utils.module_validator`.

**Decision Point:** If the source methodology defines 15+ distinct work products with rich LOD progressions, plan to split during generation.

---

## Work Product Principles

### What is a Work Product?

A work product is a **tangible artifact** that:
- Can be created, reviewed, and updated
- Provides evidence that an alpha has reached a specific state
- Has measurable levels of detail/completeness
- Can be stored, versioned, and referenced

**Examples:**
- Platform Blueprint (document, diagrams)
- Service Catalog (registry, specifications)
- Architecture Decision Record (structured documentation)
- Cost Model (spreadsheet, dashboard)
- Security Policy (codified rules, documentation)

### Work Products vs Activities

- **Work Products:** WHAT is produced (the artifact)
- **Activities:** HOW it is produced (the work)

A Platform Blueprint is a work product. "Design Platform Architecture" is an activity that creates it.

### Levels of Detail Progression

Each work product progresses through levels of increasing completeness and quality:

- **Level 1 (Outlined/Initiated):** Basic structure, placeholder content, initial concepts
- **Level 2 (Defined/Detailed):** Comprehensive content, detailed specifications, complete logical model
- **Level 3 (Applied/Behavioral):** Worked examples, real scenarios, operational usage
- **Level 4 (Comprehensive/Automated):** Templates, automation, integration with systems

Use the maturity rubric to inform what each level should contain.

### Alpha Contributions

Each level of detail must specify which alpha states it provides evidence for.

**Example:**
- Platform Blueprint at Outlined level → evidences Platform reaching "Architecture Selected"
- Platform Blueprint at Detailed level → evidences Platform reaching "Baselined"

---

## Output Structure

---

## Work Products

[Organized by logical grouping or focus area]

### Work Product: [Name]

**Description:**

Write a single SHORT sentence (8-15 words, max 20 words) that captures ONLY what this work product is.

**Guidelines:**
- **Form and purpose only:** What is it and what does it document/capture?
- **Brevity:** Aim for 8-15 words, absolute maximum 20 words
- **No elaboration:** Save value, best practices, usage guidance for narratives below
- **Direct language:** Describe the artifact itself

**Examples:**
- ❌ BAD (43 words): "The Platform Blueprint is a comprehensive architectural document that defines the technical design, component relationships, deployment patterns, and operational procedures for the platform while ensuring alignment with organizational standards and enabling consistent implementation across teams."
- ✅ GOOD (9 words): "Architectural document defining platform design and component relationships."

- ❌ BAD (35 words): "The Automation Playbook is a YAML-based executable artifact that orchestrates automation tasks by defining the sequence of plays, tasks, variables, and handlers needed to achieve a specific operational outcome."
- ✅ GOOD (11 words): "Executable YAML artifact orchestrating automation tasks for operational outcomes."

**For detailed context:** Use Usage and Context narratives section below with citations.

#### Levels of Detail

[Minimum 2 levels, recommend 3-5 levels showing maturity progression]

**[Level Name]** (seq: 1)

**IMPORTANT:** Do NOT include "Level 1:" prefix. Use descriptive name only (e.g., "Basic", "Outlined", "Initiated").

**Description:**

Single SHORT sentence (8-12 words) characterizing this maturity level.

**Guidelines:**
- **What characterizes it:** The state of completeness at this level
- **Brevity:** Aim for 8-12 words, absolute maximum 12 words
- **Direct language:** Describe the level itself

**Examples:**
- ❌ BAD (21 words): "At this level the work product exists in a basic form with minimal detail, capturing only essential information needed to demonstrate the concept exists."
- ✅ GOOD (7 words): "Basic form capturing only essential information."

- ❌ BAD (23 words): "The work product is comprehensive, detailed, and includes all necessary information for implementation with supporting documentation and review artifacts."
- ✅ GOOD (9 words): "Comprehensive with complete implementation details and supporting documentation."

**Characteristics and verification criteria:**

1. **[Criterion Name]:** [One SHORT sentence (8-15 words) describing what must be present/true at this level]

2. **[Criterion Name]:** [One SHORT sentence describing the verification criterion]

3. **[Criterion Name]:** [One SHORT sentence]

[3-7 criteria per level]

**Note:** LOD criteria should be concise verification statements:
- ❌ BAD (28 words): "The document includes a comprehensive list of all platform components with detailed descriptions of their purpose, configuration, and integration points."
- ✅ GOOD (10 words): "All platform components listed with purpose and integration points."

**This level provides evidence for:**

- **[Alpha Name]** reaching **[State Name]** state
- **[Alpha Name]** reaching **[State Name]** state

[List all alpha state contributions - minimum 1 required]

---

**[Level Name]** (seq: 2)

[Description of this maturity level]

**Characteristics and verification criteria:**

[Repeat structure]

**This level provides evidence for:**

[Repeat structure]

---

[Continue for all levels of detail]

#### Usage and Context Narratives

[Create 1-3 narratives providing context on how this work product is used, created, and evolved]

**Narrative Context Guidelines:**

Each narrative element should be **1-2 sentences maximum**, conveying a specific insight, pattern, or practice. Avoid multi-paragraph exposition. Use citationNames to point readers to comprehensive source material.

**Narrative 1: Creation and Evolution**

**Narrative Type:** [The STAR Format | How-To Guide | Essay Narrative | etc.]

**Narrative Contexts:**

**[Framework Element 1]:**

[1-2 sentences: When this work product is first created, how it evolves, what triggers updates]

**[Framework Element 2]:**

[1-2 sentences: Lifecycle management, versioning, ownership]

**[Continue framework elements]:**

[Complete the narrative structure according to chosen framework - each element 1-2 sentences]

**Citations Referenced:** [List citation names from Module 02, or omit if based on general practice]

---

**Narrative 2: Best Practices and Formats** [OPTIONAL]

**Narrative Type:** How-To Guide

**Narrative Contexts:**

**Overview:**

[1-2 sentences: Guidance on effective formats, templates, tools, or approaches for this work product]

**Steps or Key Points:**

[1-2 sentences per point: Typical formats, templates, or structures used in practice. Common tools and integration patterns.]

**Common Pitfalls:**

[1-2 sentences: What to avoid, anti-patterns]

**Citations Referenced:** [List citation names if authoritative sources provide guidance - e.g., "C4 Model Documentation", "ADR Templates"]

---

### Work Product Instances: [Work Product Name]

[If Module 00 identified specific instances of this work product]

This practice tracks several specific instances of **[Work Product Name]**:

**Instance: [Instance Name]**

[2-3 sentence description of what this specific instance is, when it's used, how it differs from other instances]

**Instance: [Next Instance Name]**

[Repeat for each instance]

---

[Repeat the Work Product structure for each work product - aim for 3-8 work products total]

---

## Writing Standards

This module follows the centralized writing standards defined in the skill documentation:

**Key Standards for This Module:**
- **Descriptions:** Single-sentence essence only (max 20 words for work products, max 12 words for LODs)
- **LOD names:** Descriptive only, NO "Level X:" prefix (e.g., "Basic" not "Level 1: Basic")
- **Narrative contexts:** 1-2 sentences per element (concise, focused points)
- **Checklist criteria:** 3-5 criteria per LOD, one sentence each (detailed enough for verification)
- **Citations:** Reference via citationNames; no narratives on Citation objects

**For complete guidelines**, see the skill's "Centralized Writing Standards" section, including:
- Descriptive Discipline (essence vs. elaboration)
- Narrative Context Guidelines (signposts, not essays)
- Checklist Standards
- LOD Naming Conventions

---

## Writing Guidelines

1. **Be specific about form** - Describe what the artifact actually IS (doc, spreadsheet, code, dashboard)
2. **Progressive maturity** - Each level should represent clear advancement
3. **Verifiable criteria** - Checklists should be checkable (not vague)
4. **Complete contributions** - Every LOD must evidence at least one alpha state
5. **Practical guidance** - Include real examples, tools, formats used in practice
6. **Reference citations** - When sources provide templates or guidance, cite them
7. **Natural prose** - Write as documentation, not JSON notation

## Level of Detail Naming Conventions

**CRITICAL:** Do NOT include "Level X:" prefix in level names. The level number is captured in the seq field.

**Format:** Use descriptive names only

**Examples:**

❌ **Bad:**
- "Level 1: Basic"
- "Level 2: Policy-Driven Segmentation"  
- "Level 3: Automated Enforcement"

✅ **Good:**
- "Basic"
- "Policy-Driven Segmentation"
- "Automated Enforcement"

**Common Level Names:**
- Basic, Intermediate, Advanced, Comprehensive
- Outlined, Defined, Detailed, Applied
- Initiated, Developed, Operational, Optimized
- Conceptual, Logical, Physical, Automated
- Drafted, Reviewed, Approved, Maintained

**The seq field indicates order (1, 2, 3, 4), the name indicates maturity characteristics.**

**Anti-Patterns:**
- ❌ Avoid "Level 1", "Level 2", "Level X:" prefixes
- ❌ Avoid overlapping terms (don't use both "Detailed" and "Defined" if they mean the same thing)

## Checklist Criteria Guidelines

Each criterion should specify:

1. **What content/section/element must exist**
2. **What quality standard it must meet**
3. **How to verify it's complete**

**Good Criterion Example:**

**Architecture Diagrams Included:** The blueprint contains network topology diagrams, data flow diagrams, and component interaction diagrams using standardized notation (e.g., C4, UML). Diagrams are version-controlled, include legends, and are referenced from prose descriptions.

**Bad Criterion Example:**

**Has diagrams** ❌ (too vague, no quality standard, not verifiable)

## Alpha Contribution Mapping

For each level of detail, ask:

- **What alpha states does this level of completeness prove?**
- **What verification criteria in those alpha states does this LOD satisfy?**

**Example Mapping:**

Work Product: Platform Blueprint  
Level: Detailed (seq: 2)

Criteria include: Complete network design, security controls specified, capacity planning documented, integration patterns defined

This evidences:
- **Platform** reaching **Baselined** (proves "Platform architecture is documented and approved")
- **Platform Governance** reaching **Established** (proves "Security and compliance patterns are defined")
- **System** reaching **Architecture Selected** (proves "System boundaries and integration points are documented")

## Work Product Instance Naming

When declaring work product instances:

- **Use specific, descriptive names** that indicate the particular artifact
- **Format:** [Specific Context] + [Base Work Product]
- **Examples:**
  - API Gateway Service Definition (instance of Service Definition)
  - Q1 Cost Optimization Report (instance of Cost Report)
  - Production Platform Blueprint (instance of Platform Blueprint)
  - Security Policy as Code (instance of Policy Document)

## Execution Instructions

1. Read Modules 00, 02, 03 to understand context and alpha states
2. For each work product in Module 00 plan:
   - Define the artifact (what it is, form, purpose)
   - Create 2-5 levels of detail showing maturity progression
   - For each LOD:
     - Write verifiable checklist criteria (3-7 per level)
     - Map to alpha state contributions (minimum 1)
   - Add usage guidance and best practices
   - Reference citations where appropriate
3. If source identifies specific instances, declare WorkProductInstanceName objects
4. Ensure every alpha state has at least one work product LOD that evidences it (cross-check with Module 03)
5. Review for completeness and consistency

**Cross-Reference Check:**

After writing all work products, verify:
- [ ] Every alpha state (from Module 03) is evidenced by at least one work product LOD
- [ ] Every work product LOD references valid alpha names and state names
- [ ] LOD progressions make logical sense (each level builds on previous)
- [ ] Criteria are specific and verifiable

**Output:** Save complete work products document to be consumed by Phase 2.
