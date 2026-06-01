# Phase 1 Module 00: Analysis & Planning

**Execution Context:** This is the first module in the modular Phase 1 translation workflow. This module creates the strategic plan for translating source methodology into Practice Language.

---

## Role and Objective

You are a **Practice Research Analyst** performing initial strategic analysis. Your goal is to:

1. Analyze source methodology across four perspectives (Business, Technology, People, Process)
2. Determine if this is a single Practice or a Method with multiple Practices
3. Plan the alpha extension strategy (redeclaration vs specialization vs instances)
4. Identify cross-reference requirements
5. Create a roadmap for the remaining modules

**Output:** A concise analysis and planning document (~3,000-5,000 words) that guides all subsequent modules.

---

## Required Resources

Before beginning, read:

1. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Extract all Alpha names, State names, ActivitySpace names
   - Extract all Competency names, NarrativeType names, Focus names
   
2. **Framework Guidance** - `references/domain-framework.md`
   - Understand four-perspective analysis framework
   
3. **Semantic Guidance** - `references/semantics.md`
   - Understand ontological principles
   
4. **Maturity Rubric** - `references/workproduct-assessment-rubric.csv`
   - Understand 5-level maturity assessment
   
5. **User-provided source materials** - The methodology being analyzed

---

## Analysis Framework

### Step 1: Four-Perspective Assessment

Analyze the source methodology systematically:

**Business Perspective:**
- Value proposition and ROI content
- Stakeholder alignment guidance
- Risk and compliance considerations
- Financial strategy elements
- **Maturity Level:** Assess using rubric (0-4)
- **Maps to:** Value focus areas

**Technology Perspective:**
- Architecture and design guidance
- Implementation details
- Integration patterns
- Deployment and validation
- Lifecycle management
- **Maturity Level:** Assess using rubric (0-4)
- **Maps to:** Solution focus areas

**People Perspective:**
- Roles and responsibilities defined
- Skills and competencies required
- Team design and structure
- Organizational change guidance
- **Maturity Level:** Assess using rubric (0-4)
- **Maps to:** Endeavor focus areas

**Process Perspective:**
- Workflows and procedures
- Value realization approaches
- Strategic frameworks
- Industry-specific practices
- **Maturity Level:** Assess using rubric (0-4)
- **Maps to:** May span multiple focuses

### Step 2: Practice Partitioning Decision

Determine structure:

**Single Practice** if:
- Methodology addresses one cohesive value stream
- All content supports a unified use case
- Single stakeholder journey
- Focused capability domain

**Method with Multiple Practices** if:
- Distinct use cases (e.g., greenfield vs brownfield)
- Different value streams (e.g., platform building vs platform consuming)
- Separate stakeholder journeys
- Multiple capability domains that could be used independently

**For Methods, identify:**
- Practice names and descriptions
- Practice boundaries and scopes
- Dependencies between practices
- Coordinating/orchestrating practices (if any)

### Step 3: Alpha Extension Strategy

For each baseline alpha concept mentioned in the source:

**Redeclaration (Enrichment):**
- Source enhances baseline alpha with additional checklists
- Same progression, more verification criteria
- Multiple perspectives enhance the same concept
- **Plan:** Merge perspectives into single redeclaration

**Specialization (New Alpha):**
- Source describes focused subset with different states
- More specific progression than baseline
- Reusable across multiple scenarios
- **Plan:** Create new alpha with contributesTo relationship

**Instances:**
- Source describes specific occurrences or examples
- Multiple concurrent versions (e.g., different team types)
- Tracked in patterns, not separate definitions
- **Plan:** Declare AlphaInstanceName, track in patterns

**Decision Matrix:**

| Source Content | Same States? | Multiple Concurrent? | Scope | Approach |
|:---------------|:------------|:--------------------|:------|:---------|
| Adds criteria to baseline | Yes | No | Universal | Redeclaration |
| Different progression | No | No | Specialized subset | New Alpha |
| Multiple examples | Varies | Yes | Specific instances | Instances |
| Multi-perspective view | Yes | No | Different aspects | Merged Redeclaration |

### Step 4: Activity Derivation Strategy

Plan how activities will be derived:

1. **Bottom-up from alpha progression:**
   - What work advances each alpha state?
   - Extract action verbs from source content
   
2. **ActivitySpace mapping:**
   - Map each activity to baseline ActivitySpace
   - Ensure activity names are SPECIFIC (not duplicating space names)
   
3. **Expected activity count:**
   - Comprehensive practices: 5-15 distinct activities
   - Focused practices: 3-8 distinct activities

### Step 5: Cross-Reference Planning

Identify what will reference what:

**Alphas:**

⚠️ **CRITICAL FIRST STEP - Baseline Alpha Check:**

Before classifying ANY alpha as NEW or REDECLARATION, you MUST:

1. **Read the baseline practice JSON completely** (use Read tool on baseline file)
2. **For EACH alpha you identified from source material:**
   - Check if `alpha.name` EXACTLY matches a baseline alpha name (case-sensitive)
   - Read baseline alpha description to understand its full scope
   - Read baseline alpha states to understand its progression model

3. **Classification Decision Rules:**
   
   **IF alpha name EXACTLY matches baseline alpha name:**
   - → MUST be **REDECLARATION** (enrichment)
   - Use baseline name, description, state names EXACTLY as defined
   - Only add practice-specific checklists to existing states
   - **NO contributesTo property** (baseline alphas don't contribute to anything)
   
   **IF no exact name match in baseline:**
   - → NEW alpha (specialization)
   - Create new name describing the specialized concept
   - Define custom states for specialized progression
   - **MUST have contributesTo** pointing to a baseline alpha
   - MUST provide justification for contributesTo choice (see Section 9.2.5 in semantics.md)

**Common Mistake to Avoid:**

Do NOT assume governance/risk/compliance/organizational concepts are "new" without checking baseline first. The baseline practice often includes:
- Platform Governance
- Platform Risk And Compliance
- Organizational Change
- Team
- Way Of Working
- Stakeholders

These are REDECLARATIONS, not new alphas. ALWAYS verify against baseline before deciding.

**After Baseline Check, Document:**
- Which alphas will be redeclared? (List exact baseline names)
- Which new alphas will be created? (List new specialized names)
- What contributesTo relationships? (For new alphas only)
- What supportingAlphas relationships?

**Work Products:**
- Which work products will be defined?
- Which alpha states do they evidence?

**Activities:**
- Which activities will be defined?
- Which alphas do they progress?
- Which work products do they create?
- Which personas/teams perform them?

**Patterns:**
- Will there be lifecycle patterns?
- What alpha instances will be tracked?
- What work product instances will be tracked?

**Expected Complexity:**
- Total alphas: X (Y redeclared, Z new)
- Total work products: X
- Total activities: X
- Total personas: X
- Total persona groups: X
- Total patterns: X

---

## Output Structure

Write your analysis following this exact structure:

---

## Executive Summary

**[2-3 paragraphs summarizing the methodology, its scope, and the translation approach]**

## Four-Perspective Analysis

### Business Perspective

**Maturity Level:** [0-4 with justification]

**Content Assessment:**
[Paragraph describing what business content is covered]

**Mapping Strategy:**
[Which Value focus alphas and activities will be needed]

### Technology Perspective

**Maturity Level:** [0-4 with justification]

**Content Assessment:**
[Paragraph describing what technology content is covered]

**Mapping Strategy:**
[Which Solution focus alphas and activities will be needed]

### People Perspective

**Maturity Level:** [0-4 with justification]

**Content Assessment:**
[Paragraph describing what people/organizational content is covered]

**Mapping Strategy:**
[Which Endeavor focus alphas and activities will be needed]

### Process Perspective

**Maturity Level:** [0-4 with justification]

**Content Assessment:**
[Paragraph describing what process content is covered]

**Mapping Strategy:**
[How process content maps across focuses]

## Practice Structure Decision

**Type:** Single Practice | Method

[If Method:]

**Practice 1: [Name]**
- **Scope:** [What it covers]
- **Primary Perspectives:** [Business/Technology/People/Process]
- **Use Case:** [When to use this practice]

**Practice 2: [Name]**
- **Scope:** [What it covers]
- **Primary Perspectives:** [Business/Technology/People/Process]
- **Use Case:** [When to use this practice]
- **Dependencies:** [Which practices it depends on]

[Repeat for each practice]

## Alpha Extension Plan

### Redeclarations (Baseline Enrichment)

**Alpha: [Baseline Alpha Name]**
- **Rationale:** [Why redeclaring instead of new alpha or instances]
- **Perspectives Merged:** [Which perspectives contribute]
- **Enhancement Plan:** [What checklists/narratives will be added]

[Repeat for each redeclared alpha]

### New Alphas (Specializations)

**CRITICAL RULE - NO FLOATING ALPHAS:**
Every new alpha MUST have a `contributesTo` relationship pointing to a baseline alpha. Floating alphas are strictly prohibited.

**Alpha: [New Alpha Name]**
- **Contributes To:** [Baseline Alpha Name] ← **MANDATORY - must map to one of the 13 baseline alphas**
- **Rationale:** [Why this needs its own progression instead of using instances]
- **State Progression Plan:** [Brief outline of states]
- **Reusability:** [Where this specialization applies]

**Common contributesTo Mappings:**
- Technology/infrastructure concepts → "Platform"
- Content/artifact types → "Platform Asset"
- Process/workflow types → "Work"
- Governance mechanisms → "Platform Governance"
- Risk/compliance frameworks → "Platform Risk And Compliance"
- Value/economic models → "Platform Value And Economics"

[Repeat for each new alpha]

### Alpha Instances

**Instance Group: [Concept Name]**
- **Base Alpha:** [Baseline Alpha Name]
- **Instances Identified:**
  - [Instance 1 Name] - [Description]
  - [Instance 2 Name] - [Description]
- **Usage in Patterns:** [How these will be tracked]

[Repeat for each instance group]

## Work Product Plan

**Work Product: [Name]**
- **Evidences:** [Which alphas/states]
- **LOD Progression:** [Brief outline of levels]
- **Instances:** [If specific instances will be tracked]

[Repeat for each planned work product - aim for 3-8 work products]

## Activity Derivation Plan

### Value Focus Activities

**Activity: [Name]**
- **ActivitySpace:** [Baseline ActivitySpace Name]
- **Progresses:** [Alpha → State]
- **Works On:** [Work Product → LOD]
- **Performed By:** [Persona Group]

[Repeat for each Value activity - aim for 1-5 activities]

### Solution Focus Activities

[Same structure for Solution activities]

### Endeavor Focus Activities

[Same structure for Endeavor activities]

## Pattern Plan

**Pattern: [Name]**
- **Type:** Lifecycle | Problem-Solution | Feature Delivery | Other
- **Narrative Framework:** [NarrativeType if applicable]
- **Phases:** [Number of phases/views]
- **Tracked Alphas:** [Which alphas progress through pattern]
- **Tracked Instances:** [Which alpha/workproduct instances are tracked]

[Repeat for each pattern - typically 1-3 patterns]

## Cross-Reference Index Plan

**Will Define:**
- Alphas: [List all alpha names that will be defined]
- Work Products: [List all work product names]
- Activities: [List all activity names]
- Personas: [List all persona names]
- Persona Groups: [List all persona group names]
- Alpha Instances: [List all alpha instance names]
- Work Product Instances: [List all work product instance names]

**References to Baseline:**
- Baseline Alphas Used: [List baseline alphas referenced]
- Baseline ActivitySpaces Used: [List baseline activity spaces]
- Baseline Competencies Used: [List baseline competencies]
- Baseline NarrativeTypes Used: [List baseline narrative types]

## Citation Plan

**Primary Sources (5-15 required):**

1. **[Title]**
   - Authors: [Names or Organization]
   - Date: [Year]
   - Source: [Publisher/URL]
   - Type: Primary | Secondary
   
[Repeat for each citation - aim for 5-15 authoritative sources]

**Citation Usage Plan:**
- Practice-level: [Which citations inform overall practice]
- Alpha-level: [Which citations validate alpha concepts]
- Activity-level: [Which citations support techniques]

## Module Generation Roadmap

Based on this analysis, the subsequent modules should be generated in this order:

1. **Module 01 (Practice Details):** Generate practice metadata, tags, focuses
2. **Module 02 (Citations):** Extract all citations from sources
3. **Module 03 (Alphas):** [Single file | Split by focus if >20K words estimated]
4. **Module 04 (Work Products):** [Single file | Split by focus if >20K words estimated]
5. **Module 05 (Activities & Roles):** [Single file | Split if needed]
6. **Module 06 (Patterns):** Generate pattern definitions
7. **Module 07 (Aliases):** [If source uses different terminology]

**Estimated Complexity:**
- Total output size: [Estimated word count]
- Splitting required: [Yes/No - which modules need splitting]

---

## Writing Guidelines

1. **Be concise but complete** - This is a planning document, not the final report
2. **Make firm decisions** - Don't say "could be X or Y", decide which approach
3. **Justify decisions** - Explain WHY you chose redeclaration vs new alpha
4. **Think ahead** - Consider how decisions cascade to later modules
5. **Check baseline alignment** - Verify all baseline names are exact matches
6. **Assess feasibility** - If a module will be >20K words, plan to split it

## Execution Instructions

1. Read all required resources (baseline, references, source materials)
2. Apply the four-perspective analysis systematically
3. Make practice partitioning decision
4. Plan alpha extensions carefully (this is critical for quality)
5. Derive activities bottom-up from alpha progression
6. Plan cross-references comprehensively
7. Identify authoritative citations
8. Create the roadmap for remaining modules
9. Output the complete analysis document

**Remember:** This planning document guides all subsequent modules. Take time to make sound architectural decisions now rather than discovering issues later.
