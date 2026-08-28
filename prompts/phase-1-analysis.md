# Phase 1: Analysis Prompt

## Context

You are conducting **Phase 1: Analysis** of a methodology translation workflow. This phase organizes source methodology content into a structured methodological framework that will later be mapped to a baseline practice in Phase 2.

## Objective

Extract and organize the key elements from the source methodology into a structured report that identifies:
- **Outcomes** - Primary objectives and intended outcomes
- **Concerns** - Areas requiring attention to achieve objectives
- **Progressive States** - Maturity waypoints for each concern
- **Work Products** - Artifacts demonstrating progress
- **Activities** - Types of work performed
- **Competencies** - Required expertise and skill levels
- **Personas** - Roles combining competencies
- **Workflows** - Common patterns and lifecycles
- **Practices** - Cohesive groupings by value stream or use case

## Resources Available

You have access to the following reference documents via the Read tool:

1. **references/domain-framework.md**
   - Four-perspective enterprise analysis framework
   - Business, Technology, People, Process perspectives
   - Use to identify perspectives and classify content

2. **Source Methodology Materials**
   - User will provide files, URLs, or directory paths
   - Read all source materials thoroughly
   - Extract concepts using the domain framework

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

## Instructions

### Step 1: Load Reference Framework

Read `references/domain-framework.md` to understand the four-perspective analysis approach:

- **Business Perspective**: Value streams, capabilities, strategic themes, ROI, stakeholder alignment, risk/compliance
- **Technology Perspective**: MVA design, architectural runway, integration, continuous deployment, lifecycle management
- **People Perspective**: Team design, targeted viewpoints, human-centered design, roles, competencies, change management
- **Process Perspective**: Intentional architecture, systems thinking, workflows, value realization, industry alignment

### Step 2: Read Source Materials

Read ALL provided source materials completely:
- PDF documents
- Web pages (via URLs)
- Markdown files
- Technical documentation

Take comprehensive notes organized by the four perspectives.

### Step 3: Identify Outcomes

**What are the primary objectives?**

For the entire source methodology:
- What outcomes does it promise?
- What problems does it solve?
- Who benefits and how?
- What value does successful adoption deliver?

Document 3-8 primary outcomes, organized by perspective (Business, Technology, People, Process).

### Step 4: Identify Concerns (Areas of Attention)

**What must be addressed to achieve the outcomes?**

For each outcome, identify the major concerns or areas requiring attention:
- What needs to be built, configured, or established? (Technology)
- What needs to be organized, aligned, or decided? (Business)
- What skills, teams, or changes are needed? (People)
- What processes, workflows, or practices must be followed? (Process)

Document 5-15 distinct concerns, each with:
- **Name** (2-5 words, descriptive)
- **Description** (single sentence, 15-20 words max)
- **Tags** (domain, lifecycle, organizational)
- **Narrative** (2-4 bulleted points summarizing the concern)
- **Concreteness Test** (one Given/When/Then triplet proving the concern is actionable — see guidance below)
- **Further Reading** (citations to source material sections)

#### Concreteness Test (Gherkin Validation Heuristic)

Each concern must pass a quick Given/When/Then test to confirm it represents a real, trackable area of attention rather than an abstract category. This is a validation gate, not full scenario specification — one triplet per concern is sufficient.

- **Given**: What precondition or context makes this concern relevant?
- **When**: What trigger, action, or event advances this concern?
- **Then**: What observable outcome demonstrates progress?

If you cannot write a coherent triplet, the concern is likely too abstract (split it) or too narrow (merge it with a related concern). The triplet also seeds downstream Gherkin structure in Phase 3 — preconditions feed `background`, triggers feed `test.when`, outcomes feed `test.then`.

**Example:**
> **Concern:** Platform Observability
> - **Given** the platform hosts production workloads
> - **When** the operations team deploys a monitoring stack with SLO dashboards
> - **Then** service health is measurable and alert fatigue is within acceptable bounds

### Step 5: Identify Progressive States for Each Concern

**How does each concern mature from initial state to completion?**

For EACH concern, identify natural progression waypoints described in the source:
- Look for explicit maturity levels, phases, or stages
- Identify implicit progression (setup → production → optimized)
- Use `references/workproduct-assessment-rubric.csv` as a LENS to recognize patterns, NOT as a template to force-fit
- Minimum 3 states, maximum 7 states per concern

For each state:
- **Name** (2-4 words, describing the waypoint)
- **Description** (single sentence)
- **Prerequisites** (what must already hold before this state is relevant? List 1-3 preconditions — cross-concern dependencies or contextual conditions. These seed `background.given` and `background.alphaStates` in Phase 3. Do NOT list the previous state of the same concern — sequential progression is implicit in state ordering and restating it is redundant.)
- **Criteria** (distinct observable verification criteria — what must be demonstrably true? Typical 3-7 per state; error if >10 unless justified. Same-state near-duplicate names are a fail. Extract unique criteria globally, then assign to states — do not invent per-state.)

### Step 6: Identify Work Products

**What artifacts demonstrate that concerns have achieved levels of progress?**

For each concern and its states, identify work products mentioned or implied:
- Documentation (architecture diagrams, plans, policies)
- Code artifacts (IaC, scripts, configurations)
- Operational artifacts (dashboards, runbooks)
- Evidence artifacts (test results, audit reports)

For each work product:
- **Name** (2-4 words)
- **Description** (single sentence)
- **Levels of Detail** (3-5 levels showing increasing maturity/completeness)
  - Use rubric as lens: Non-Existent → Descriptive → Logical → Behavioral → Comprehensive/Automated
  - Each level: Name, Description, 3-5 one-sentence characteristics
- **Instances** (if source describes distinct variants, e.g., "Platform Architecture" vs "Security Architecture")

When multiple work products follow the same LOD progression (e.g., several architecture documents all with Outlined → Detailed → Validated), note this pattern — Phase 2 may consolidate them as `mapsTo` variants of a single parent work product rather than separate work products.

### Step 7: Identify Activities

**What types of work are performed?**

For each concern and work product, identify activities:
- Activities contributing to state progression
- Activities creating or developing work products
- Activities coordinating work across teams

For each activity:
- **Name** (verb + specific object, e.g., "Design Security Architecture" not "Design")
- **Description** (single sentence)
- **Triggers** (what decision point, event, or lifecycle moment initiates this activity? 1-2 sentences. Seeds `test.when` in Phase 3)
- **Technique Narrative** (2-5 paragraphs, 2-4 sentences each)
  - How is this activity performed?
  - What techniques or approaches are used?
  - What are common patterns or anti-patterns?
  - Citations to source material for details
- **Outcomes** (which concerns/states does this activity contribute to?)
- **Observable Results** (what is different after this activity completes, beyond concern state changes? E.g., "risk factors are documented", "team capacity plan is reviewed". Seeds `test.then` in Phase 3)
- **Work Products Used** (which artifacts does this activity create/update?)

### Step 8: Identify Competencies

**What expertise is required?**

Across all activities, identify types of expertise needed:
- Technical skills (engineering, architecture, operations)
- Leadership skills (strategic alignment, stakeholder management)
- Management skills (project management, risk management)
- Specialized skills (security, compliance, reliability)

For each competency:
- **Name** (2-4 words, e.g., "Cloud Architecture")
- **Description** (single sentence)
- **Levels** (3-5 levels from novice to expert)
  - Each level: Name, Description (skill and experience expectations)

Map each activity to:
- **Required Competencies** (list of competency names needed)
- **Recommended Competency Levels** (specific level recommendations)

### Step 9: Identify Personas

**What roles combine competencies?**

From the source, identify:
- Explicit roles mentioned (Platform Engineer, Security Architect)
- Implied roles (based on competency combinations)

For each persona:
- **Name** (role title)
- **Description** (single sentence)
- **Competencies** (competency + level pairs)
- **Tags** (domain, lifecycle, organizational)

### Step 10: Identify Persona Groups (Teams)

**How do personas work together?**

Describe team structures:
- Platform teams, product teams, enabling teams
- Cross-functional groups
- Communities of practice

For each group:
- **Name** (team name)
- **Description** (single sentence)
- **Team Members** (list of persona names)
- **Tags** (organizational)

Map activities to **Involved Persona Groups**.

### Step 11: Identify Workflows and Patterns

**What are the common patterns of work?**

**CRITICAL: Patterns are REQUIRED for practices with multiple concerns.** Patterns coordinate how multiple alphas/concerns mature together through a lifecycle.

#### Pattern Requirements (Read references/semantics.md Section 8.1.1)

**Multi-Alpha Coordination (REQUIRED):**

- If practice will have 2+ alphas → pattern REQUIRED
- Pattern shows how alphas reach states in coordinated sequence
- Example: Platform + Execution Environment + Mesh → "Platform Bootstrap Journey"

**Multi-Faceted Concerns (REQUIRED):**

- If practice addresses multiple independent concerns → pattern REQUIRED
- Pattern orchestrates how distinct capabilities co-evolve
- Example: RBAC + Analytics + Catalog → "Governance Maturity Journey"

**External Lifecycle Mapping (RECOMMENDED):**

- Consider if practice naturally follows an established architectural lifecycle
- Available lifecycle narrative types: SDLC, PDCA, Build-Measure-Learn, Design-Build-Run-Optimize, Crawl-Walk-Run
- Example: Infrastructure deployment → "Design-Build-Run-Optimize"

#### Patterns (Specific Workflows)

For EACH identified practice, create at least ONE pattern:

**Pattern Identification:**

- Migration patterns (brownfield → cloud-native)
- Onboarding patterns (new team → productive)
- Deployment patterns (code → production)
- Bootstrap patterns (infrastructure setup → optimization)
- Maturity patterns (governance establishment → automated compliance)

**For each pattern:**

- **Name** (journey or lifecycle oriented)
- **Description** (single sentence describing coordination)
- **Narrative Type** (STAR, Hero's Journey, SDLC, PDCA, Build-Measure-Learn, Design-Build-Run-Optimize, Crawl-Walk-Run)
- **Pattern Views** (3-5 phases or steps):
  - View 0 (Prerequisites): Initial states of all concerns
  - Views 1-N (Progression): Coordinated advancement of concerns
  - Each view: Name, Description, Concerns addressed (with target states), Work products developed, Activities emphasized

**Quality Check:**
- [ ] Multi-alpha practices have at least one pattern
- [ ] Each pattern has 3-5 views (not too few, not too many)
- [ ] Prerequisites view (seq: 0) establishes all initial states
- [ ] Pattern views coordinate multiple concerns (not single-concern storytelling)

#### Lifecycle (Overarching Pattern)

Identify the overarching lifecycle using "The Cycle" from domain-framework:
1. Sense & Strategize
2. Translate & Map
3. Co-Create the Runway
4. Deliver & Emerge
5. Feedback & Refactor

Map methodology phases/stages to this cycle framework.

### Step 12: Identify Preliminary Practice Structure

**How might outcomes be grouped?**

**NOTE:** This is a PRELIMINARY structural observation based on source content alone. The FINAL practice vs method decision happens in Phase 2 (Step 0: Practice Delineation) when baseline alpha context is available. Do not treat this assessment as binding.

Observe whether source describes:
- **Likely Single Practice** (one cohesive value stream, unified framework)
- **Likely Multiple Practices** (distinct use cases, value streams, or capability domains)

Note these structural separation signals (same qualitative signals used in Phase 2, but without baseline alpha coverage analysis):
- Different use-cases (greenfield vs brownfield)
- Different value-streams (platform building vs consuming)
- Different stakeholder journeys (builders vs consumers)
- Different capability domains (security, observability, deployment)
- Distinct concern clusters (groups of concerns with strong internal relationships but weak cross-group ties)

For each Practice:
- **Name**
- **Description**
- **Objectives and Outcomes**
- **Concerns** (subset from Step 4 relevant to this practice)
- **Work Products** (subset from Step 6)
- **Activities** (subset from Step 7)
- **Workflows** (subset from Step 11)

Document practice hierarchy and relationships.

### Step 13: Identify Reference Content Candidates

**What external content could help practitioners bootstrap their work?**

During source material analysis, tag content that could serve as curated references — real-world exemplars that illustrate what alpha states look like in practice, with links to downloadable or viewable content.

**What to look for:**

- **Templates and starter documents** — Architecture decision records, runbook templates, governance policy templates, onboarding checklists
- **Reference architectures** — Canonical design patterns with concrete examples (e.g., AWS reference architectures, TOGAF building blocks)
- **Case studies and exemplary implementations** — Real-world examples showing how an organization achieved a particular maturity state
- **Tools and repositories** — GitHub repos, community tools, starter kits, automation frameworks
- **External standards and frameworks** — ISO standards, NIST frameworks, industry benchmarks that map to specific concerns
- **Sample artifacts** — Example work products at various levels of maturity (e.g., a sample architecture document, a completed risk register)

**For each candidate, document:**

- **Name** (descriptive, identifying the source — e.g., "TOGAF Architecture Document Template", NOT "Architecture Template 1")
- **Description** (1-2 sentences: what it illustrates and why it is useful)
- **Related Concern** (which concern/alpha area it relates to — preliminary, pre-mapping)
- **Content Type** (template | case study | reference architecture | tool | standard | sample artifact)
- **URLs/Links** (REQUIRED where available — without a link, a reference provides no actionable value)
- **Estimated Maturity** (what level of maturity/completeness does this content represent? e.g., basic starter vs comprehensive production-ready)

**Quality over quantity** — focus on high-value references that would genuinely accelerate practitioner work. A practice may have 3-10 references; not every alpha state needs one.

### Step 14: Generate Citations

Document all source materials as structured citations with full metadata. This is the authoritative citation record — Phase 2 and Phase 3 will carry these details forward, so completeness here prevents information loss downstream.

For each source:
- **Name** (exact source title — this becomes the citation's symbolic key)
- **Description** (1 sentence summary of content/relevance)
- **Authors** (array of author names, full names preferred)
- **Date** (publication year or full date if known)
- **Source** (publisher, journal, or organization name)
- **URL** (REQUIRED where possible — see URL enrichment rules below)

Prioritize authoritative sources (primary methodology creators).

**Citation URL Enrichment (REQUIRED):**

Every citation SHOULD have a `url` field. Internal, intranet, and Google Docs/Sheets/Slides URLs are valid and preferred when the source material was accessed via those links. Populate URLs using these sources in priority order:

1. **User-provided URLs** — If the user supplied URLs as input sources (including Google Docs, SharePoint, intranet links, or any internal domain), carry those URLs directly into the corresponding citations. These are the most authoritative source locators.
2. **Official websites** — For frameworks, methodologies, and standards with known homepages (e.g., `https://framework.scaledagile.com/` for SAFe, `https://teamtopologies.com/` for Team Topologies)
3. **DOI references** — For academic papers, journal articles, and conference proceedings, use the DOI URL format: `https://doi.org/10.xxxx/xxxxx`
4. **Publisher pages** — For books, use the publisher's catalog page or a stable reference (e.g., IT Revolution Press, O'Reilly, Wiley)
5. **Standards body pages** — For standards (ISO, NIST, IEEE, TOGAF), link to the official standards page

Only omit `url` when no stable link exists. Never fabricate URLs — if uncertain, omit rather than guess. Internal/intranet URLs are perfectly acceptable; do not omit a URL merely because it is not publicly accessible.

## Output Format

Create a markdown file: `practices/<practice-name>/01-analysis-report.md`

### File Structure

```markdown
# Phase 1 Analysis Report: <Methodology Name>

## Metadata
- **Analysis Date**: YYYY-MM-DD
- **Source Materials**: [list]
- **Preliminary Structure**: Likely Single Practice | Likely Multiple Practices | Unclear (Phase 2 will determine)
- **Analyst**: [your name]

## 1. Outcomes
[Business Perspective]
- Outcome 1...
- Outcome 2...

[Technology Perspective]
- Outcome 3...

[People Perspective]
- Outcome 4...

[Process Perspective]
- Outcome 5...

## 2. Concerns (Areas of Attention)

### 2.1 Concern Name
**Description:** Single sentence

**Tags:**
- Domain: [...]
- Lifecycle: [...]
- Organizational: [...]

**Narrative:**
- Key point 1
- Key point 2
- Key point 3

**Concreteness Test:**
- **Given** [precondition making this concern relevant]
- **When** [trigger or action that advances the concern]
- **Then** [observable outcome demonstrating progress]

**Further Reading:**
- [Citation reference]

#### Progressive States

**State 1: Name**
- Description: ...
- Prerequisites:
  - [Prior state or cross-concern dependency]
- Criteria:
  1. Criterion 1
  2. Criterion 2
  ...

**State 2: Name**
...

### 2.2 [Next Concern]
...

## 3. Work Products

### 3.1 Work Product Name
**Description:** Single sentence

**Levels of Detail:**

**Level 1: Name**
- Description: ...
- Characteristics:
  1. Characteristic 1
  2. Characteristic 2
  ...

**Level 2: Name**
...

**Instances:** (if applicable)
- Instance 1 Name: Description
- Instance 2 Name: Description

### 3.2 [Next Work Product]
...

## 4. Activities

### 4.1 Activity Name
**Description:** Single sentence

**Triggers:**
[What decision point, event, or lifecycle moment initiates this activity?]

**How to Perform:**
[2-5 paragraphs describing techniques, approaches, patterns]

**Outcomes:**
- Contributes to Concern X → State Y
- Contributes to Concern Z → State W

**Observable Results:**
- [What is different after this activity completes, beyond state changes?]

**Work Products Used:**
- Creates/Updates: Work Product A at Level N
- Creates/Updates: Work Product B at Level M

**Required Competencies:**
- Competency 1
- Competency 2

**Recommended Competency Levels:**
- Competency 1: Level X
- Competency 2: Level Y

### 4.2 [Next Activity]
...

## 5. Competencies

### 5.1 Competency Name
**Description:** Single sentence

**Levels:**

**Level 1: Name**
- Description: Skill and experience expectations

**Level 2: Name**
...

### 5.2 [Next Competency]
...

## 6. Personas

### 6.1 Persona Name
**Description:** Single sentence

**Competencies:**
- Competency 1: Level X
- Competency 2: Level Y

**Tags:**
- Domain: [...]
- Lifecycle: [...]
- Organizational: [...]

### 6.2 [Next Persona]
...

## 7. Persona Groups (Teams)

### 7.1 Team Name
**Description:** Single sentence

**Team Members:**
- Persona 1
- Persona 2
- Persona 3

**Tags:**
- Organizational: [...]

### 7.2 [Next Team]
...

## 8. Workflows and Patterns

### 8.1 Pattern Name
**Description:** Single sentence

**Pattern Views:**

**View 1: Phase Name**
- Description: ...
- Concerns Addressed: [list]
- Work Products Developed: [list]
- Activities Emphasized: [list]

**View 2: [Next Phase]**
...

### 8.2 [Next Pattern]
...

### 8.9 Overarching Lifecycle
**Description:** Map to "The Cycle" framework

**Phase 1: Sense & Strategize**
- Methodology mapping: [...]

**Phase 2: Translate & Map**
- Methodology mapping: [...]

...

## 9. Practices

### Practice Hierarchy
[If multiple practices]
- Practice 1: Name - Objective
  - Practice 1.1: Sub-practice...
- Practice 2: Name - Objective

### 9.1 Practice Name
**Description:** Single sentence

**Objectives and Outcomes:**
- Objective 1
- Objective 2

**Concerns:**
- Concern 1 (from Section 2.1)
- Concern 2 (from Section 2.3)
...

**Work Products:**
- Work Product 1 (from Section 3.1)
...

**Activities:**
- Activity 1 (from Section 4.1)
...

**Workflows:**
- Pattern 1 (from Section 8.1)
...

### 9.2 [Next Practice if applicable]
...

## 10. Reference Content Candidates

### 10.1 [Reference Name]
**Description:** 1-2 sentences explaining what this illustrates and why it is useful
**Related Concern:** [concern name from Section 2]
**Content Type:** template | case study | reference architecture | tool | standard | sample artifact
**URL:** https://... (REQUIRED where available)
**Estimated Maturity:** [basic starter | intermediate | comprehensive/production-ready]

### 10.2 [Next Reference]
...

## 11. Citations

### [1] [Exact Source Title]
- **Description**: 1 sentence summary
- **Authors**: Author 1, Author 2
- **Date**: YYYY
- **Source**: Publisher or journal
- **URL**: https://... (or internal/Google Docs link)

### [2] ...
...
```

## Quality Standards

### Conciseness
- **Descriptions**: Single grammatically correct sentence, max 20 words
- **State/LOD Descriptions**: Max 12 words
- **Narrative Contexts**: 1-3 sentences per bullet point (not paragraphs)
- **Criteria**: Each a distinct observable criterion, one sentence; typical 3-7 per state (error if >10 unless justified), typical 3-5 per LOD. Same-state near-duplicates are a fail.

### Completeness
- NO placeholders ("etc.", "...")
- Extract ALL relevant content from source
- Use exact terminology from source (aliases can be added in Phase 2)

### Source Fidelity
- Let source content drive progression, not templates
- Use rubric as lens to recognize patterns, not force-fit
- Preserve source's maturity models and lifecycle phases
- Create states/LODs matching source's natural waypoints

### Narrative Quality
- Focused, specific insights (not comprehensive essays)
- Citations for further reading (don't replicate source verbatim)
- Clear connection between perspectives and practice elements

## Execution Notes

1. **Read domain-framework.md FIRST** - Load the four perspectives before analyzing source
2. **Read ALL source materials** - Comprehensive review, take perspective-organized notes
3. **Work sequentially** - Outcomes → Concerns → States → Work Products → Activities → Competencies → Personas → Workflows → Practices
4. **Cross-reference continuously** - Activities reference concerns/work products, patterns reference activities/concerns
5. **Preserve source terminology** - Use exact terms from source (aliasing happens in Phase 2)
6. **Document decisions** - When making judgment calls, note reasoning in narratives
7. **Create directory structure**: `mkdir -p practices/<practice-name>` before writing output

## Output Location

Write to: `practices/<practice-name>/01-analysis-report.md`

Where `<practice-name>` is kebab-case derived from the methodology name (e.g., "aws-well-architected", "team-topologies").

## Success Criteria

- ✓ All four perspectives represented in analysis
- ✓ Clear traceability: Outcomes → Concerns → States → Work Products → Activities
- ✓ Progressive states reflect source's natural maturity model (not forced template)
- ✓ Work product LODs match source's described progression
- ✓ Activities have rich "How to Perform" narratives with citations
- ✓ Competencies, personas, and teams clearly defined
- ✓ Patterns and lifecycle mapped to workflow frameworks
- ✓ Preliminary practice structure observed with structural signals noted (final boundaries determined in Phase 2)
- ✓ Comprehensive citations to source materials
- ✓ Reference content candidates tagged with URLs, related concerns, and content types

This analysis will be used as input for Phase 2 (Mapping to Baseline Practice).
