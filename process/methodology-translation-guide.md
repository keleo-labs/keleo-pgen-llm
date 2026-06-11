# Methodology Translation Process Guide

## Purpose

This guide helps humans translate enterprise methodology documentation (like AWS Well-Architected, SAFe, TOGAF, Team Topologies) into standardized Practice Language JSON format. The process breaks down large methodologies into manageable chunks using a modular workflow.

---

## Overview: Three Main Phases

**Phase 1:** Write focused analysis modules (one topic at a time)  
**Phase 2:** Assemble modules and validate consistency  
**Phase 3:** Convert to structured JSON format  

**Time Estimate:** 8-16 hours for a typical practice, depending on complexity

---

## Before You Start

### Materials You'll Need

1. **Source Documentation** - The methodology you're translating (PDFs, websites, books)
2. **Reference Framework** - Located in `deps/platform-adoption-kernel.json`
3. **Writing Templates** - Located in `prompts/phase-1-modules/`
4. **Validation Tools** - Python scripts in `utils/` directory

### Key Concepts to Understand

- **Practice** = A single cohesive approach to solving a problem (e.g., "Platform Engineering")
- **Method** = Multiple related practices working together (e.g., "SAFe" includes portfolio, program, and team practices)
- **Alpha** = A key concept that progresses through stages (e.g., "Platform" goes from "Scoped" → "Architected" → "Operational")
- **Work Product** = Evidence that proves progress (e.g., "Architecture Diagram", "Deployment Script")
- **Activity** = Work that moves things forward (e.g., "Design Infrastructure", "Deploy Service")

---

## Phase 1: Planning and Analysis

### Step 1.1: Decide - Practice or Method?

Read your source materials and ask:

**Single Practice if:**
- One clear value stream or journey
- Single stakeholder perspective
- Unified set of activities
- Example: "Kubernetes Platform Engineering"

**Method if:**
- Multiple distinct value streams
- Different stakeholder groups
- Separate practices that connect
- Example: "SAFe" (has Portfolio, Program, Team practices)

### Step 1.2: Create Your Workspace

**For a Practice:**
```bash
mkdir -p practices/your-practice-name/report-elements
cd practices/your-practice-name
```

**For a Method:**
```bash
mkdir -p practices/your-method-name/report-elements
cd practices/your-method-name
```

Use kebab-case names (lowercase with hyphens): `aws-well-architected`, `team-topologies`

### Step 1.3: Create Your Strategic Plan

**File to create:** `report-elements/00-analysis-plan.md` (or `00-method-plan.md` for methods)

**What to write (3-5 pages):**

1. **What is this methodology about?** (2-3 paragraphs)
   - Core purpose and value proposition
   - Who uses it and why
   - Key problems it solves

2. **What are the main concepts?** (bullet list)
   - List 10-15 key concepts the methodology introduces
   - Note which ones might be "Alphas" (things that progress)
   - Note which ones might be "Work Products" (evidence/artifacts)

3. **How will you map to the baseline framework?**
   - Review `deps/platform-adoption-kernel.json`
   - Which baseline Alphas will you enrich? (e.g., "Platform", "Team", "Requirements")
   - What new Alphas might you need? (must connect to baseline via `contributesTo`)

4. **What sources will you cite?** (5-15 authoritative references)
   - Primary sources (original books, official documentation)
   - Key research papers or articles
   - Recognized experts in the field

**Template:** Use `prompts/phase-1-modules/00-analysis-plan.md` as a guide

---

## Phase 2: Write the Content Modules

### Overview: The Seven Core Modules

You'll write 7 focused documents, one topic at a time. Each builds on the previous ones.

| Module | Topic | Size | Time |
|--------|-------|------|------|
| 01 | Practice Details | 2-3 pages | 30 min |
| 02 | Citations | 1-2 pages | 30 min |
| 03 | Alphas (concepts that progress) | 15-20 pages | 3-4 hours |
| 04 | Work Products (evidence) | 10-15 pages | 2-3 hours |
| 05 | Activities & Roles | 15-20 pages | 3-4 hours |
| 06 | Patterns (how activities flow) | 10-15 pages | 2-3 hours |
| 07 | Aliases (terminology mapping) | 0.5-1 page | 15 min |

---

### Module 01: Practice Details

**File:** `report-elements/01-practice-details.md`

**What to write:**

1. **Basic Information**
   - Practice name
   - Short description (1 sentence, max 20 words)
   - Long description (2-3 paragraphs)
   - Version number (e.g., "1.0.0")

2. **Tags** - Categorize your practice:
   - **Domain tags:** What industry/area? (e.g., "Cloud", "Platform Engineering", "AI/ML")
   - **Lifecycle tags:** Where in the journey? (e.g., "Strategy", "Implementation", "Operations")
   - **Organizational tags:** Who's involved? (e.g., "Engineering", "Leadership", "Cross-Functional")

3. **Context Narratives** (2-4 short narratives)
   - Why this practice matters (business context)
   - What problem it solves (technical context)
   - How teams adopt it (organizational context)
   - **REQUIRED:** At least one narrative using a framework template (STAR, Hero's Journey, Three-Act Structure, etc.)

**Writing Tips:**
- Description = single sentence, essence only
- Narratives = 2-4 paragraphs, 2-4 sentences each
- Focus on "why" and "what," not "how" (that comes in Module 05)

**Template:** `prompts/phase-1-modules/01-practice-details.md`

---

### Module 02: Citations

**File:** `report-elements/02-citations.md`

**What to write:**

A list of 5-15 authoritative sources in APA7 format.

**For each citation include:**
- **Name:** Exact title of the source
- **Description:** What this source covers (1 sentence)
- **Authors:** List of author names
- **Date:** Publication date (YYYY-MM-DD or YYYY)
- **Source:** Publisher or journal name
- **URL:** Link to the source (if available)

**Example:**
```
**Name:** "Team Topologies: Organizing Business and Technology Teams for Fast Flow"

**Description:** Foundational text on team structures and interaction patterns for modern software delivery.

**Authors:** Matthew Skelton, Manuel Pais

**Date:** 2019-09-17

**Source:** IT Revolution Press

**URL:** https://teamtopologies.com/book
```

**Writing Tips:**
- Prioritize primary sources (original authors, official docs)
- Include seminal research papers if applicable
- Don't include blog posts unless they're from recognized experts
- Citations are metadata only - no narrative sections

**Template:** `prompts/phase-1-modules/02-citations.md`

---

### Module 03: Alphas (Concepts That Progress)

**File:** `report-elements/03-alphas.md`

**What to write:**

Alphas are the key concepts in your methodology that evolve through stages. For example, a "Platform" might progress from "Scoped" → "Architected" → "Built" → "Operational" → "Optimized."

**For each Alpha:**

1. **Basic Info**
   - Name (e.g., "ML Pipeline")
   - Description (1 sentence, max 20 words)
   - Focus area: Value, Solution, or Endeavor
   - Whether it's a redeclaration (enriching baseline) or specialization (new alpha)

2. **States** (minimum 3, typically 4-7)
   - State name (e.g., "Architected")
   - Description (1 sentence, max 12 words)
   - Checklist: 5-7 verification criteria (1 sentence each)
   - What gets you to this state? What evidence exists when you're here?

3. **Context Narratives** (2-4 focused narratives)
   - Why this alpha matters
   - How it fits into the bigger picture
   - Key insights from your citations

4. **Relationships**
   - If new alpha: What baseline alpha does it contribute to? (`contributesTo`)
   - If redeclaration: Which baseline alpha are you enriching?

**Example Alpha Structure:**
```
## Alpha: ML Model

**Description:** A trained machine learning algorithm ready for inference.

**Focus:** Solution

**Type:** Specialization (contributesTo: "Requirements")

### State 1: Scoped
- **Description:** Model requirements and success criteria defined.
- **Checklist:**
  1. Business problem clearly articulated
  2. Success metrics identified (accuracy, latency, etc.)
  3. Training data sources identified
  4. Model architecture constraints documented
  5. Deployment requirements understood

### State 2: Trained
- **Description:** Model trained and validated on historical data.
- **Checklist:**
  1. Training pipeline executed successfully
  2. Model performance meets success criteria on validation set
  3. Feature importance analyzed and documented
  4. Model artifacts stored in registry
  5. Training metrics logged and available

[... continue for remaining states]

### Narratives

**Narrative: ML Model Lifecycle Context**
- **Type:** STAR (Situation, Task, Action, Result)
- **Situation:** Organizations struggle to operationalize ML models at scale...
- **Task:** Teams need a structured approach to move models from experimentation to production...
- **Action:** This alpha provides clear progression milestones...
- **Result:** Teams can track model maturity and ensure production readiness...
- **Citations:** [Machine Learning Engineering, Model Risk Management Guide]
```

**Writing Tips:**
- Let source content drive state progression, don't force-fit templates
- Use the `references/workproduct-assessment-rubric.csv` as inspiration, not prescription
- States should represent natural waypoints your methodology describes
- Checklist criteria should be verifiable (can someone check this?)
- If you have many alphas (>8), consider splitting by focus: `03a-alphas-value.md`, `03b-alphas-solution.md`, `03c-alphas-endeavor.md`

**Template:** `prompts/phase-1-modules/03-alphas.md`

---

### Module 04: Work Products (Evidence)

**File:** `report-elements/04-workproducts.md`

**What to write:**

Work products are the artifacts that prove progress. They're the tangible evidence that alphas are advancing through states.

**For each Work Product:**

1. **Basic Info**
   - Name (e.g., "Deployment Pipeline Configuration")
   - Description (1 sentence, max 20 words)
   - Focus area: Value, Solution, or Endeavor

2. **Levels of Detail** (minimum 3, typically 3-5)
   - Level name (e.g., "Basic", "Comprehensive", "Automated" - NO "Level 1:" prefix)
   - Description (1 sentence, max 12 words)
   - Checklist: 3-5 characteristics (1 sentence each)
   - What baseline alpha states does this level contribute to?

3. **Context Narratives** (1-3 focused narratives)
   - When and why this work product is created
   - How it evolves over time
   - Best practices from your citations

**Example Work Product Structure:**
```
## Work Product: Infrastructure as Code Repository

**Description:** Version-controlled repository containing infrastructure definitions and deployment automation.

**Focus:** Solution

### Level: Basic
- **Description:** Manual scripts with minimal structure.
- **Checklist:**
  1. Infrastructure defined in script files (bash, PowerShell)
  2. Scripts stored in version control
  3. Basic documentation of parameters
- **Contributes To:**
  - Alpha: Platform, State: Architected

### Level: Modular
- **Description:** Parameterized templates with reusable components.
- **Checklist:**
  1. Infrastructure defined using IaC tool (Terraform, CloudFormation)
  2. Modular design with reusable components
  3. Variables externalized in configuration files
  4. State management configured
  5. README with usage examples
- **Contributes To:**
  - Alpha: Platform, State: Built

### Level: Automated
- **Description:** Fully automated with CI/CD integration.
- **Checklist:**
  1. All features from Modular level
  2. Automated validation (linting, security scanning)
  3. Automated testing (plan validation, policy checks)
  4. CI/CD pipeline integration
  5. Automated deployment with approval gates
- **Contributes To:**
  - Alpha: Platform, State: Operational

[... continue with narratives]
```

**Writing Tips:**
- Levels represent increasing sophistication or automation
- Use the maturity rubric (`references/workproduct-assessment-rubric.csv`) as a lens
- Not all work products need 5 levels - use what fits the source content
- LOD checklists describe characteristics, not steps to create
- Each LOD must contribute to at least one alpha state (usually multiple)

**Template:** `prompts/phase-1-modules/04-workproducts.md`

---

### Module 05: Activities & Roles

**File:** `report-elements/05-activities-roles.md`

**What to write:**

This is typically the largest module. It describes the actual work people do and who does it.

**Part A: Activities** (10-15 pages)

For each activity:

1. **Basic Info**
   - Name: Specific action (e.g., "Design Multi-Tenant Architecture" NOT just "Architecture")
   - Description (1 sentence, max 20 words)
   - Activity Space: Which of the 20 baseline spaces? (e.g., "Prepare to Deliver Value")
   - Focus area: Value, Solution, or Endeavor

2. **Outcomes**
   - Which alpha does this activity advance?
   - Which state does it help achieve?

3. **Work Products**
   - What does this activity create or use?
   - What does it modify or review?

4. **Competencies Required**
   - Which of the 8 baseline competencies? (Analysis, Engineering, Leadership, Management, etc.)
   - What level? (Assists, Applies, Masters, Adapts, Innovates)

5. **How to Perform Narrative** (CRITICAL - don't skip!)
   - 3-6 paragraphs explaining the technique
   - Concrete steps or patterns
   - Examples from source methodology
   - Citations to authoritative sources
   - This is where subject matter expertise lives!

**Example Activity Structure:**
```
## Activity: Design Multi-Tenant Platform Architecture

**Description:** Create architectural blueprints for a platform supporting multiple isolated tenants.

**Activity Space:** Prepare to Deliver Value

**Focus:** Solution

**Contributes To:**
- Alpha: Platform, State: Architected

**Works On:**
- Work Product: Architecture Diagram
- Work Product: Technical Design Document

**Required Competencies:**
- Engineering (Masters level)
- Analysis (Applies level)
- Platform Strategic Alignment (Applies level)

### How to Perform: Multi-Tenant Design Patterns

**Isolation Models:** Multi-tenant platforms require careful consideration of tenant isolation strategies. The three primary models are: (1) Shared everything (namespace-level isolation), (2) Shared infrastructure (node-pool-level isolation), and (3) Full isolation (cluster-per-tenant). Each model presents different trade-offs between resource efficiency and security boundaries.

**Resource Management:** Establish resource quotas and limits at the tenant level to prevent noisy neighbor problems. Kubernetes ResourceQuotas and LimitRanges provide namespace-scoped controls, while node affinity and taints/tolerations enable physical separation when needed.

**Security Boundaries:** Implement network policies to enforce tenant isolation at Layer 3/4, and consider service mesh policies for Layer 7 controls. Use RBAC to ensure tenants cannot access or modify resources outside their namespace scope.

**Data Plane Considerations:** Design ingress routing to support tenant-specific domains while maintaining efficient load balancer usage. Consider tenant-aware observability (logging, metrics, tracing) to enable self-service monitoring without cross-tenant visibility.

**Control Plane Design:** Decide whether tenants share a control plane (namespace model) or have dedicated control planes (cluster model). Shared control planes reduce operational overhead but require robust quota enforcement and admission control.

**Citations:** [Kubernetes Multi-Tenancy Best Practices, NIST Zero Trust Architecture]

[... continue with additional narrative sections if needed]
```

**Part B: Personas** (2-3 pages)

For each role/persona:

1. **Basic Info**
   - Name (e.g., "Platform Engineer", "ML Engineer", "Product Owner")
   - Description (1 sentence, max 20 words)

2. **Competencies**
   - List required competencies with levels
   - Format: Competency Name (Level)

3. **Context Narrative** (optional, 1-2 paragraphs)
   - What this role does
   - How it fits into the team

**Example Persona:**
```
## Persona: Platform Engineer

**Description:** Engineer responsible for building and operating shared platform infrastructure.

**Competencies:**
- Engineering (Masters level)
- Site Reliability (Applies level)
- Platform Security And Compliance Enforcement (Applies level)
- Analysis (Applies level)

### Context
Platform engineers focus on building self-service capabilities that enable product teams to deploy and operate services independently. They balance standardization with flexibility, creating "golden paths" that are easy to adopt while allowing customization when needed.
```

**Part C: Teams/Persona Groups** (1-2 pages)

For each team structure:

1. **Basic Info**
   - Name (e.g., "Platform Team", "ML Platform Team")
   - Description (1 sentence, max 20 words)

2. **Team Members**
   - List personas that comprise this team

**Example Team:**
```
## Persona Group: Platform Team

**Description:** Cross-functional team responsible for platform design, implementation, and operations.

**Team Members:**
- Platform Engineer (3-5 members)
- Site Reliability Engineer (2-3 members)
- Platform Security Engineer (1-2 members)
- Platform Product Manager (1 member)
```

**Writing Tips:**
- Activity names must be specific and different from ActivitySpace names
- Technique narratives are crucial - this is where expertise shows
- Don't skimp on "How to Perform" sections - include real guidance
- If module gets too large (>25K words), split into: `05a-activities.md`, `05b-personas-teams.md`
- Required competencies = must have these to do the work
- Recommended competency levels = helpful to have at this level

**Template:** `prompts/phase-1-modules/05-activities-roles.md`

---

### Module 06: Patterns (Activity Flows)

**File:** `report-elements/06-patterns.md`

**What to write:**

Patterns are recipes that orchestrate activities over time. They show "how things flow" through the practice.

**For each Pattern:**

1. **Basic Info**
   - Name (e.g., "Platform MVP Pattern", "Continuous Platform Improvement")
   - Description (1 sentence, max 20 words)
   - Pattern type: Lifecycle, Situational, or Cross-cutting

2. **Pattern Views** (3-7 views showing progression)
   - View name (e.g., "Phase 1: Foundation", "Sprint 1")
   - Description (1 sentence, max 12 words)
   - Sequence number (1, 2, 3...)
   - Alpha states visible at this view
   - Work products created/used at this view
   - Activities emphasized at this view
   - Alpha instances (specific examples if applicable)

3. **Context Narratives** (2-4 focused narratives)
   - When to use this pattern
   - How it guides the work
   - Success stories or examples

**Example Pattern Structure:**
```
## Pattern: Platform Minimum Viable Product (MVP)

**Description:** Rapid delivery of initial platform capabilities to prove value and gather feedback.

**Type:** Lifecycle

### View 1: Scope Foundation

**Description:** Define core platform requirements and architecture.

**Sequence:** 1

**Alpha States:**
- Platform: Scoped
- Requirements: Conceived
- Stakeholders: Recognized

**Activities:**
- Identify Platform Stakeholder Needs
- Define Platform Value Proposition
- Design Core Platform Architecture

**Work Products:**
- Platform Vision Document (Basic level)
- Architecture Diagram (Basic level)

### View 2: Build Core Services

**Description:** Implement foundational platform capabilities.

**Sequence:** 2

**Alpha States:**
- Platform: Built
- Requirements: Bounded
- Solution: Architected

**Activities:**
- Implement Infrastructure as Code
- Configure Identity and Access Management
- Set Up Deployment Automation

**Work Products:**
- Infrastructure as Code Repository (Modular level)
- CI/CD Pipeline Configuration (Modular level)
- Platform Documentation (Basic level)

[... continue for remaining views]

### Narratives

**Narrative: MVP Pattern Application**
The Platform MVP pattern enables teams to deliver value incrementally while learning from early adopters. Rather than building comprehensive platform capabilities upfront, teams focus on a minimal set of services that solve real problems for a small pilot group. This approach reduces risk and ensures platform evolution is driven by actual user needs rather than assumptions.

**Citations:** [Lean Startup, Continuous Discovery Habits]
```

**Writing Tips:**
- Patterns tell a story - views should have logical progression
- Not all alphas/activities appear in every view
- Views represent time slices or phases, not steps
- Reference actual elements from Modules 03, 04, 05
- If tracking specific instances (e.g., "Security Team" and "Platform Team" instances of "Team" alpha), note them in views

**Template:** `prompts/phase-1-modules/06-patterns.md`

---

### Module 07: Aliases (Terminology Mapping)

**File:** `report-elements/07-aliases.md`

**What to write:**

Only needed if your source methodology uses different terminology than Practice Language.

**For each alias:**
- Practice element type (Alpha, Work Product, Activity, etc.)
- Practice element name (your standardized name)
- Source term (what the methodology calls it)
- Description (why the alias exists)

**Example:**
```
## Aliases

### Alpha Aliases

**Practice Element:** Platform
**Source Term:** "Internal Developer Platform (IDP)"
**Description:** The source methodology uses "IDP" to refer to what we model as the Platform alpha.

**Practice Element:** Requirements
**Source Term:** "User Stories" or "Feature Requests"
**Description:** Agile methodologies use these terms for what we formalize as Requirements.

### Work Product Aliases

**Practice Element:** Architecture Diagram
**Source Term:** "System Design Document"
**Description:** AWS Well-Architected refers to architecture visualizations as system design documents.

[... continue if more aliases exist]
```

**If no aliases:**
```
## No Aliases Required

This practice uses terminology that aligns directly with Practice Language conventions. No terminology mapping is needed.
```

**Writing Tips:**
- Only include if source uses significantly different terms
- Most practices won't need this module
- Helps users who know the source methodology map to standardized language

**Template:** `prompts/phase-1-modules/07-aliases.md`

---

### Module 08: Method Assembly (Methods Only)

**File:** `report-elements/08-method-assembly.md`

**Only for multi-practice methods.** Skip this for single practices.

**What to write:**

1. **Method Overview**
   - How the practices work together
   - Integration points between practices
   - Overall adoption journey

2. **Practice Dependencies**
   - Which practice should be adopted first?
   - What are the prerequisites?
   - How do they build on each other?

3. **Method-Level Patterns** (optional)
   - Patterns that span multiple practices
   - Cross-practice coordination flows

**Example:**
```
## Method Assembly: SAFe

### Overview
SAFe integrates three practices (Portfolio, Program, Team) to align strategy with execution across large organizations. The practices share common alphas (Value Stream, Requirements, Team) but operate at different scales and cadences.

### Practice Integration

**Portfolio Practice → Program Practice:**
- Strategic Themes from Portfolio drive Program-level Epics
- Portfolio Kanban feeds into Program Backlog refinement
- Budget allocation at Portfolio level constrains Program Increment planning

**Program Practice → Team Practice:**
- Program Increment objectives guide Team Sprint planning
- Cross-team dependencies managed through Program-level synchronization
- Teams deliver into shared System Demo for Program stakeholders

### Adoption Path

**Phase 1 - Team Practice:** Start with Agile Team foundations (2-4 months)
**Phase 2 - Program Practice:** Add Program Increment cadence (3-6 months)
**Phase 3 - Portfolio Practice:** Introduce Lean Portfolio Management (6-12 months)

[... continue with method-level patterns and integration details]
```

**Template:** `prompts/phase-1-modules/08-method-assembly.md`

---

## Phase 3: Assembly and Validation

### Step 3.1: Assemble the Complete Report

Concatenate all your modules into one document for human review.

**Create:** `research-report.md`

**Sections in order:**
1. Module 00 (Planning)
2. Module 01 (Practice Details)
3. Module 02 (Citations)
4. Module 03 (Alphas)
5. Module 04 (Work Products)
6. Module 05 (Activities & Roles)
7. Module 06 (Patterns)
8. Module 07 (Aliases)
9. Module 08 (Method Assembly) - if method

**Bash command:**
```bash
cd practices/your-practice-name

# For practices:
cat report-elements/00-*.md \
    report-elements/01-*.md \
    report-elements/02-*.md \
    report-elements/03-*.md \
    report-elements/04-*.md \
    report-elements/05-*.md \
    report-elements/06-*.md \
    report-elements/07-*.md \
    > research-report.md

# For methods, add 08-*.md at the end
```

### Step 3.2: Create Cross-Reference Index

Build an index of all elements to validate internal consistency.

**Create:** `cross-reference-index.json`

**What to include:**
```json
{
  "alphas": ["Platform", "ML Model", "Team", ...],
  "states": {
    "Platform": ["Scoped", "Architected", "Built", "Operational", "Optimized"],
    "ML Model": ["Scoped", "Trained", "Validated", "Deployed", "Monitored"]
  },
  "workProducts": ["Architecture Diagram", "IaC Repository", "Model Registry", ...],
  "activities": ["Design Platform Architecture", "Train ML Model", ...],
  "personas": ["Platform Engineer", "ML Engineer", ...],
  "personaGroups": ["Platform Team", "ML Team", ...],
  "patterns": ["Platform MVP", "Model Deployment Pipeline", ...]
}
```

**Manual process:**
1. Go through Modules 03-06
2. List every unique name
3. Create JSON structure above
4. This becomes your validation reference

### Step 3.3: Validate Consistency

Check that all references are valid:

**Checklist:**
- [ ] All activities reference alphas/states that exist (from Module 03)
- [ ] All activities reference work products that exist (from Module 04)
- [ ] All pattern views reference activities that exist (from Module 05)
- [ ] All pattern views reference alphas/states that exist (from Module 03)
- [ ] All LOD contributesTo references point to valid alpha/state pairs
- [ ] All persona names in teams exist in the persona list
- [ ] All competency names are one of the 8 baseline competencies
- [ ] No floating alphas (all new alphas have contributesTo relationships)

**Manual validation:**
- Read through `research-report.md`
- Check cross-references against `cross-reference-index.json`
- Fix any broken references in the source modules
- Regenerate affected modules if needed

---

## Phase 4: JSON Translation

### Step 4.1: Translate to JSON Structure

Now convert your markdown modules into schema-compliant JSON.

**Reference schemas:**
- `deps/language.schema.json` - Authoritative structure
- `references/semantics.md` - Semantic guidance

**Translation approach:**

Work through modules sequentially, building up JSON:

1. **Practice skeleton** (from Module 01)
2. **Citations** (from Module 02)
3. **Alphas** (from Module 03)
4. **Work products** (from Module 04)
5. **Activities** (from Module 05 Part A)
6. **Personas** (from Module 05 Part B)
7. **Persona groups** (from Module 05 Part C)
8. **Patterns** (from Module 06)
9. **Aliases** (from Module 07)

**File to create:** `your-practice-name.json`

**Key translation rules:**

**For narratives:**
```json
{
  "name": "Platform Evolution Context",
  "description": "How platforms mature from basic infrastructure to strategic enablers.",
  "narrativeTypeName": "STAR",
  "narrativeContexts": [
    {
      "narrativeElement": "Situation",
      "description": "Organizations start with manual infrastructure provisioning...",
      "seq": 1
    },
    {
      "narrativeElement": "Task",
      "description": "Teams need to automate and standardize infrastructure...",
      "seq": 2
    }
  ],
  "citationNames": ["Platform Engineering Guide", "Team Topologies"]
}
```

**For checklists:**
```json
{
  "name": "Architected",
  "description": "Platform architecture is designed and documented.",
  "checklist": [
    {
      "name": "Architecture documented",
      "description": "Platform architecture diagram and design document exist.",
      "seq": 1
    },
    {
      "name": "Components identified",
      "description": "Core platform components and their interactions are defined.",
      "seq": 2
    }
  ]
}
```

**For competency references:**
```json
{
  "recommendedCompetencyLevels": [
    {
      "competencyName": "Engineering",
      "competencyLevelName": "Masters"
    }
  ],
  "requiredCompetencies": ["Engineering", "Analysis"]
}
```

**Common property names:**
- Activity outcomes → `contributesTo` (array of AlphaContribution objects)
- Activity personas → `involves` (array of persona names)
- Activity work products → `worksOn` (array of work product names)
- Pattern views → `patternViews` (not `views`)
- Narrative framework → `narrativeTypeName` (not `narrativeFramework`)

**Text cleaning:**
- Remove ALL markdown syntax (**, ##, -, etc.)
- Remove practice metadata ("the practice defines", "according to", etc.)
- Focus descriptions on domain concepts, not documentation
- Single sentence descriptions only
- No paragraph breaks in description fields

### Step 4.2: Validate JSON Syntax

Make sure your JSON is well-formed.

```bash
# Check JSON syntax
cat your-practice-name.json | python3 -m json.tool > /dev/null && echo "Valid JSON" || echo "Invalid JSON"

# Or use jq
jq empty your-practice-name.json && echo "Valid JSON" || echo "Invalid JSON"
```

### Step 4.3: Run Automated Fixes

**Step 1: Fix property names** (Phase 2.5)

Copy the fix script template and run:

```bash
# From practices/your-practice-name/
cp ../../utils/fix-property-names.py .
python3 fix-property-names.py
```

This corrects common property name issues:
- `outcomes` → `contributesTo`
- `focus` → `focusName`
- `competencies` (on Activity) → `recommendedCompetencyLevels` + `requiredCompetencies`
- `views` → `patternViews`
- Removes `type` from Patterns

**Step 2: Validate baseline references** (Phase 2.6)

```bash
cp ../../utils/validate-baseline-references.py .
python3 validate-baseline-references.py
```

This validates and auto-fixes:
- Competency names (maps descriptions to canonical names)
- State names (corrects invalid state references)
- Alpha/Focus/ActivitySpace references

**For methods:** Rebuild the method JSON after fixing practices:

```bash
python3 rebuild-method-json.py
```

**Step 3: Validate internal integrity** (Phase 2.7)

```bash
cp ../../utils/validate-internal-integrity.py .
python3 validate-internal-integrity.py
```

This generates `INTERNAL-INTEGRITY-REPORT.md` with:
- All activity → alpha/state reference validation
- All activity → work product reference validation
- All pattern view → activity reference validation
- All pattern view → alpha/state reference validation
- Element inventory and statistics

**If issues found:** Review the report and fix manually (internal integrity issues usually need human judgment).

### Step 4.4: Schema Validation (MANDATORY)

Final validation against the authoritative schema:

```bash
node ../../utils/validate-json-schema.js your-practice-name.json
```

**If errors found:** Review error messages and consult `prompts/reference/schema-violations-complete.md` for detailed examples and fixes.

**Common schema violations:**
- Narratives missing `name` or `description` properties
- Checklist items as strings instead of objects
- Tags not nested under `tags` property
- PersonaGroups not in `personaGroups` property
- PatternView missing `seq` or using wrong property names

**Fix and re-validate until you get 0 errors.**

---

## Phase 5: Quality Assurance

### Final Checks

Before considering the translation complete:

**1. No floating alphas:**
```bash
python3 ../../utils/check-floating-alphas.py your-practice-name.json
```

All new alphas must have `contributesTo` relationships to baseline alphas.

**2. Spot-check content:**

```bash
# Check alphas have narratives
jq '.alphas[0] | {name, hasNarrative: (.narratives | length > 0)}' your-practice-name.json

# Check activities have technique narratives
jq '.activities[0] | {name, hasNarrative: (.narratives | length > 0)}' your-practice-name.json

# Check personas have competencies
jq '.personas[0] | {name, hasCompetencies: (.competencies | length > 0)}' your-practice-name.json

# Check practice has intent narrative
jq '.narratives[] | select(.narrativeTypeName != "Citation Standard")' your-practice-name.json
```

**3. Human review:**

- Read through `research-report.md` - does it make sense?
- Are technique narratives (Module 05) substantial and useful?
- Are citations authoritative and relevant?
- Do patterns tell a coherent story?

---

## Deliverables

When complete, you should have:

**In `practices/your-practice-name/`:**

1. **`report-elements/`** - All modular markdown files (editable, version-controllable)
2. **`research-report.md`** - Complete human-readable documentation (~50-80K words)
3. **`cross-reference-index.json`** - Validation index
4. **`your-practice-name.json`** - Schema-compliant Practice Language JSON
5. **Utility scripts:**
   - `fix-property-names.py`
   - `validate-baseline-references.py`
   - `validate-internal-integrity.py`
   - `rebuild-method-json.py` (methods only)

**What you can do with these:**

- **Edit modules individually** - Re-generate specific sections without redoing everything
- **Share research report** - Use as methodology documentation for your organization
- **Integrate JSON** - Feed into tools that consume Practice Language
- **Version control** - Track changes to methodology over time
- **Re-validate** - Re-run scripts after manual edits to ensure consistency

---

## Time Management Tips

**Break the work into sessions:**

- **Session 1 (2-3 hours):** Planning + Modules 00, 01, 02
- **Session 2 (3-4 hours):** Module 03 (Alphas)
- **Session 3 (2-3 hours):** Module 04 (Work Products)
- **Session 4 (3-4 hours):** Module 05 (Activities & Roles)
- **Session 5 (2-3 hours):** Module 06 (Patterns)
- **Session 6 (1-2 hours):** Module 07, Assembly, Validation
- **Session 7 (2-3 hours):** JSON Translation
- **Session 8 (1-2 hours):** Validation, Fixes, QA

**Don't try to do it all in one sitting.** Each module builds on previous ones, so taking breaks helps you internalize the model.

---

## Common Pitfalls

**1. Writing overly verbose descriptions**
- ❌ "This activity is performed by the platform team and involves designing the architecture for the platform including all infrastructure components and ensuring that security requirements are met."
- ✅ "Design platform architecture including infrastructure components and security controls."

**2. Skipping technique narratives**
- Module 05 "How to Perform" sections are where real expertise lives
- Don't just list activities - explain HOW to do them

**3. Force-fitting templates**
- Let the source methodology guide state progression
- Don't impose 5 levels on every work product if the source only describes 3

**4. Floating alphas**
- Every new alpha must connect to baseline via `contributesTo`
- If it doesn't contribute to a baseline alpha, reconsider if it's really an alpha

**5. Inconsistent naming**
- Pick exact names early (use your cross-reference index)
- Case-sensitive exact matches required for all references

**6. Missing citations**
- Don't just reference methodology documentation
- Include authoritative sources, research papers, books

**7. Not validating cross-references**
- Easy to typo an alpha name or state name
- Validation scripts catch these - use them!

---

## Getting Help

**Reference documents:**
- `CLAUDE.md` - Full project documentation
- `prompts/phase-1-modules/` - Detailed prompt templates
- `references/semantics.md` - Practice Language semantic guidance
- `references/domain-framework.md` - Modern enterprise architecture perspectives
- `references/workproduct-assessment-rubric.csv` - Maturity level guidance

**Validation resources:**
- `deps/language.schema.json` - Authoritative schema
- `deps/platform-adoption-kernel.json` - Baseline framework (13 alphas, 8 competencies, 20 activity spaces)
- `utils/README.md` - Utility documentation

**Example practices:**
- Check `practices/` directory for examples of completed translations

---

## Summary Workflow

1. **Plan** - Analyze source, decide Practice vs Method, create strategic plan
2. **Write modules** - 7-9 focused markdown documents, one topic at a time
3. **Assemble** - Concatenate into complete report, build cross-reference index
4. **Validate** - Check internal consistency, fix broken references
5. **Translate** - Convert markdown to JSON following schema
6. **Auto-fix** - Run property name fixes and baseline validation
7. **Validate schema** - Ensure full compliance with authoritative schema
8. **QA** - Final checks for floating alphas, content completeness
9. **Deliver** - Package modules, report, index, and JSON

**Estimated time:** 8-16 hours for typical practice

**Output:** High-quality, schema-compliant Practice Language JSON + comprehensive documentation

---

Good luck with your methodology translation!
