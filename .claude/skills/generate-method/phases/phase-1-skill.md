# Phase 1: Analysis -- Subagent Skill

## Context

You are a Phase 1 subagent in the practice generation pipeline. Your job is to analyze source methodology documentation and produce a structured analysis report. This report feeds Phase 2 (Mapping), where elements are mapped to a baseline practice framework.

**You do NOT:**
- Determine practice vs method boundaries (that happens in Step 1.5, Delineation Gate, by the main agent)
- Identify primary alphas (requires baseline context, unavailable until Phase 2)
- Decide how many practices to create (requires baseline alpha coverage analysis)
- Load baseline practice JSON (Phase 2 concern)

**You DO:**
- Extract ALL methodology content into structured form
- Classify content using four enterprise architecture perspectives
- Identify concern relationships for downstream mapping
- Produce a complete, placeholder-free analysis report (~30-50K words)

## Inputs

The orchestrator provides these in the subagent prompt:

| Variable | Description |
|----------|-------------|
| `<practice-name>` | Kebab-case name for the output directory |
| `<source-materials>` | File paths, URLs, or directory paths to methodology documentation |

**Output file:** `practices/<practice-name>/01-analysis-report.md`

## Reading Plan

Execute reads in this order -- each step builds on the previous.

| Seq | What to Read | Why |
|-----|-------------|-----|
| 1 | `references/domain-framework.md` | Load the four-perspective analysis framework (Business, Technology, People, Process) and "The Cycle" lifecycle model. This is your analytical lens for all subsequent reading. |
| 2 | ALL source materials (files, URLs, PDFs, markdown) | Comprehensive extraction. Take perspective-organized notes as you read. |
| 3 | `references/workproduct-assessment-rubric.csv` | Use as a recognition lens for work product maturity levels. Do NOT force-fit its structure -- let source content drive progression. |

## Tool Call Guidelines

Use **simple single-command** Bash calls matching auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`). Make separate tool calls instead.

## Process

Work through these steps sequentially. Each step's output references the previous steps.

### Step 1: Load Analytical Framework

Read `references/domain-framework.md`. Internalize:

- **Business Perspective**: Value streams, capabilities, strategic themes, ROI, stakeholder alignment, risk/compliance
- **Technology Perspective**: MVA design, architectural runway, integration, continuous deployment, lifecycle management
- **People Perspective**: Team design, targeted viewpoints, human-centered design, roles, competencies, change management
- **Process Perspective**: Intentional architecture, systems thinking, workflows, value realization, industry alignment

You will classify all extracted content through these four lenses.

### Step 2: Read Source Materials

Read ALL provided source materials completely. No skimming, no sampling. For each source:

- Extract concepts organized by the four perspectives
- Note exact terminology used (preserve source language; aliasing happens in Phase 2)
- Record page numbers, section references, and URLs for citations
- Flag content that credits contributors (for acknowledgements)

### Step 3: Identify Outcomes

**Question: What value does the methodology deliver, and how is that value measured?**

Identify 3-8 outcome candidates across the entire source methodology. Each describes a measurable value proposition.

Per outcome, document:

- **Name** (2-5 words, value-oriented)
- **Description** (single sentence: what value this delivers)
- **How Value is Measured** (1-2 sentences: metric, KPI, or observable)
- **Related Concerns** (which Step 4 concerns contribute)
- **Perspective** (Business / Technology / People / Process)

Phase 2 will distill these to 1-3 structured Outcomes per practice with `measureDescription` and optional metric/objective contribution chains.

### Step 4: Identify Concerns (Areas of Attention)

**Question: What must be addressed to achieve the outcomes?**

For each outcome, ask:
- What needs to be built, configured, or established? (Technology)
- What needs to be organized, aligned, or decided? (Business)
- What skills, teams, or changes are needed? (People)
- What processes, workflows, or practices must be followed? (Process)

Document 5-15 distinct concerns, each with:

| Field | Requirement |
|-------|------------|
| Name | 2-5 words, descriptive |
| Description | Single sentence, 15-20 words max |
| Tags | Domain, lifecycle, organizational |
| Narrative | 2-4 bulleted points |
| Concreteness Test | One Given/When/Then triplet (see below) |
| Further Reading | Citations to source material sections |

**Concreteness Test (Gherkin Validation Heuristic):**

Each concern MUST pass a Given/When/Then test confirming it is real and trackable, not abstract. One triplet per concern is sufficient.

- **Given**: What precondition makes this concern relevant?
- **When**: What trigger or action advances this concern?
- **Then**: What observable outcome demonstrates progress?

If you cannot write a coherent triplet, the concern is too abstract (split it) or too narrow (merge it). The triplet seeds downstream Gherkin structure: preconditions feed `background`, triggers feed `test.when`, outcomes feed `test.then`.

### Step 5: Identify Progressive States

**Question: How does each concern mature from initial state to completion?**

For EACH concern, identify natural progression waypoints from the source:

- Look for explicit maturity levels, phases, or stages in the source
- Identify implicit progression (setup -> production -> optimized)
- Use `references/workproduct-assessment-rubric.csv` as a LENS to recognize patterns, NOT as a template to force-fit
- **Minimum 3, maximum 7 states per concern**

Per state:

| Field | Requirement |
|-------|------------|
| Name | 2-4 words describing the waypoint |
| Description | Single sentence |
| Prerequisites | 1-3 preconditions (cross-concern dependencies or contextual conditions). Do NOT list the previous state of the same concern -- sequential progression is implicit in state ordering. |
| Criteria | 3-7 distinct observable verification criteria (error if >10 unless justified). Same-state near-duplicate names are a fail. Extract unique criteria globally, then assign -- do not invent per-state. For each criterion, note whether the source treats it as essential, important-but-deferrable, or supplementary -- this feeds checklist `priority` assignment in Phase 2. |

### Step 6: Identify Work Products

**Question: What artifacts demonstrate that concerns have achieved levels of progress?**

Categories to look for: documentation (architecture diagrams, plans, policies), code artifacts (IaC, scripts, configurations), operational artifacts (dashboards, runbooks), evidence artifacts (test results, audit reports).

Per work product:

| Field | Requirement |
|-------|------------|
| Name | 2-4 words |
| Description | Single sentence |
| Levels of Detail | 3-5 levels showing increasing maturity/completeness. Use rubric as lens: Non-Existent -> Descriptive -> Logical -> Behavioral -> Comprehensive/Automated. Each level: Name, Description, 3-5 one-sentence characteristics. |
| Instances | If source describes distinct variants (e.g., "Platform Architecture" vs "Security Architecture"), note them. |

**Consolidation signal:** When multiple work products follow the same LOD progression, note this pattern. Phase 2 may consolidate them as `mapsTo` variants of a single parent work product.

### Step 7: Identify Activities

**Question: What types of work are performed?**

For each concern and work product, identify activities that:
- Contribute to state progression
- Create or develop work products
- Coordinate work across teams

Per activity:

| Field | Requirement |
|-------|------------|
| Name | Verb + specific object (e.g., "Design Security Architecture" not "Design") |
| Description | Single sentence |
| Triggers | What decision point, event, or lifecycle moment initiates this? 1-2 sentences. Seeds `test.when` in Phase 3. |
| Technique Narrative | 2-5 paragraphs (2-4 sentences each): how performed, techniques used, common patterns/anti-patterns, citations |
| Outcomes | Which concerns/states does this contribute to? |
| Observable Results | What is different after this activity completes, beyond state changes? Seeds `test.then` in Phase 3. |
| Work Products Used | Which artifacts does this create/update? |
| Required Competencies | List with recommended levels |

### Step 8: Identify Competencies

**Question: What expertise is required?**

Across all activities, identify expertise types: technical (engineering, architecture, operations), leadership (strategic alignment, stakeholder management), management (project, risk), specialized (security, compliance, reliability).

Per competency:

- **Name** (2-4 words)
- **Description** (single sentence)
- **Levels** (3-5 levels from novice to expert, each with name and skill/experience description)

Map each activity to required competencies with recommended levels.

### Step 9: Identify Personas

**Question: What roles combine competencies?**

From the source, identify explicit roles and implied roles based on competency combinations.

Per persona:

- **Name** (role title)
- **Description** (single sentence)
- **Competencies** (competency + level pairs)
- **Tags** (domain, lifecycle, organizational)

### Step 10: Identify Persona Groups (Teams)

**Question: How do personas work together?**

Describe team structures: platform teams, product teams, enabling teams, cross-functional groups, communities of practice.

Per group:

- **Name** (team name)
- **Description** (single sentence)
- **Team Members** (list of persona names)
- **Tags** (organizational)

Map activities to involved persona groups.

### Step 11: Identify Concern Relationships

**Question: How do concerns interact with each other?**

This step is CRITICAL for Phase 2 mapping. Analyze and document the following relationship types between concerns:

| Relationship Type | Question | Example |
|-------------------|----------|---------|
| Production flows | Which concerns produce/generate/create other concerns? | "Platform Architecture" produces "Deployment Pipeline" |
| Enablement patterns | Which concerns enable/support/facilitate others? | "Security Posture" enables "Compliance Achievement" |
| Governance structures | Which concerns guide/constrain/govern others? | "Architecture Standards" governs "Service Design" |
| Information flows | Which concerns provide data to/inform/validate others? | "Monitoring" informs "Capacity Planning" |
| Dependencies | Which concerns require/depend on others? | "Auto-scaling" depends on "Resource Management" |

Document these as a relationship table or adjacency list. The validation script checks for at least 5 lines documenting inter-concern relationships.

### Step 12: Identify Workflows and Patterns

**Question: What are the common patterns of work?**

**Patterns are REQUIRED for practices with multiple concerns.** Read `references/domain-framework.md` for "The Cycle" lifecycle model.

**Pattern identification -- look for:**
- Migration patterns (brownfield -> cloud-native)
- Onboarding patterns (new team -> productive)
- Deployment patterns (code -> production)
- Bootstrap patterns (infrastructure setup -> optimization)
- Maturity patterns (governance establishment -> automated compliance)

Per pattern:

| Field | Requirement |
|-------|------------|
| Name | Journey or lifecycle oriented |
| Description | Single sentence describing coordination |
| Narrative Type | STAR, Hero's Journey, SDLC, PDCA, Build-Measure-Learn, Design-Build-Run-Optimize, Crawl-Walk-Run |
| Pattern Views | 3-5 phases/steps (see below) |

Pattern view structure:
- **View 0 (Prerequisites):** Initial states of all concerns
- **Views 1-N (Progression):** Coordinated advancement of concerns
- Each view: Name, Description, Concerns addressed (with target states), Work products developed, Activities emphasized

**Quality checks:**
- Multi-concern practices have at least one pattern
- Each pattern has 3-5 views
- Prerequisites view establishes all initial states
- Pattern views coordinate multiple concerns (not single-concern storytelling)

**Overarching Lifecycle:** Map methodology phases/stages to "The Cycle" from `references/domain-framework.md`:
1. Sense & Strategize
2. Translate & Map
3. Co-Create the Runway
4. Deliver & Emerge
5. Feedback & Refactor

### Step 13: Identify Preliminary Practice Structure

**Question: How might outcomes be grouped?**

**NOTE:** This is a PRELIMINARY structural observation. The FINAL practice vs method decision happens in Step 1.5 (Delineation Gate) by the main agent when baseline alpha context is available. Do not treat this assessment as binding.

Observe whether the source describes:
- **Likely Single Practice** (one cohesive value stream)
- **Likely Multiple Practices** (distinct use cases or value streams)

Note structural separation signals:
- Different use-cases (greenfield vs brownfield)
- Different value-streams (platform building vs consuming)
- Different stakeholder journeys (builders vs consumers)
- Different capability domains (security, observability, deployment)
- Distinct concern clusters (strong internal ties, weak cross-group ties)

Per preliminary practice: Name, Description, Objectives/Outcomes, and which Concerns/Work Products/Activities/Workflows belong to it.

### Step 14: Identify Reference Content Candidates

**Question: What reusable content could practitioners directly use or adapt?**

References are actionable starting points (templates, sample artifacts, worked examples, reference architectures) -- NOT documentation explaining how to do work.

**What to look for:**
- Templates and starter documents (ADRs, runbook templates, governance policies)
- Reference architectures (reusable design patterns with concrete structure)
- Sample artifacts and worked examples (completed work products practitioners can replicate)
- Tools and repositories (GitHub repos, starter kits, automation frameworks)
- Reusable components within standards (checklists, control matrices, assessment templates)

**Page-level identification required:** When a larger document contains actionable content at a specific location, record specific pages/sections/slide numbers. Use `Pages/Sections` field in APA 7th format: "pp. 23-31", "Section 3", "Slides 12-15".

**Actionability test:** "If a practitioner followed this link, would they find something they can directly use, adapt, or fill in -- or text explaining a concept?" Only the former qualifies.

Per candidate:

| Field | Requirement |
|-------|------------|
| Name | Descriptive, identifying the source (e.g., "TOGAF Architecture Document Template") |
| Description | 1-2 sentences: what the practitioner gets and how to use it |
| Related Concern | Which concern area it relates to (preliminary) |
| Content Type | template / sample artifact / worked example / reference architecture / tool / reusable component |
| URLs/Links | REQUIRED (without a link, no actionable value) |
| Pages/Sections | REQUIRED when content is at a specific location in a larger document |
| Estimated Maturity | basic starter / intermediate / comprehensive production-ready |

Quality over quantity. 3-10 per practice. Zero references is better than documentation links pretending to be references.

### Step 15: Generate Citations

Document all source materials as structured citations. This is the authoritative citation record -- Phase 2 and Phase 3 carry these forward.

Per source:

| Field | Requirement |
|-------|------------|
| Name | Exact source title (becomes the citation's symbolic key) |
| Description | 1 sentence summary |
| Authors | Array of full names |
| Date | Publication year or full date |
| Source | Publisher, journal, or organization |
| URL | REQUIRED where possible (see enrichment rules below) |

**URL enrichment priority:**
1. User-provided URLs (including Google Docs, SharePoint, intranet) -- carry directly
2. Official websites (framework homepages)
3. DOI references (`https://doi.org/10.xxxx/xxxxx`)
4. Publisher pages (catalog or stable reference)
5. Standards body pages (ISO, NIST, IEEE, TOGAF)

Only omit `url` when no stable link exists. Never fabricate URLs. Internal/intranet URLs are acceptable.

## Output Format

Create: `practices/<practice-name>/01-analysis-report.md`

Run `mkdir -p practices/<practice-name>` before writing.

### Required Structure

```markdown
# Phase 1 Analysis Report: <Methodology Name>

## Metadata
- **Analysis Date**: YYYY-MM-DD
- **Source Materials**: [list]
- **Preliminary Structure**: Likely Single Practice | Likely Multiple Practices | Unclear (Phase 2 will determine)
- **Analyst**: [your name]

## 1. Outcomes
### 1.1 [Outcome Name]
**Description:** ...
**How Value is Measured:** ...
**Related Concerns:** ...
**Perspective:** ...

## 2. Concerns (Areas of Attention)
### 2.1 [Concern Name]
**Description:** ...
**Tags:** Domain: [...] | Lifecycle: [...] | Organizational: [...]
**Narrative:** [2-4 bullets]
**Concreteness Test:**
- **Given** [precondition]
- **When** [trigger]
- **Then** [observable outcome]
**Further Reading:** [citations]

#### Progressive States
**State 1: [Name]**
- Description: ...
- Prerequisites: [1-3 cross-concern or contextual preconditions]
- Criteria:
  1. ...
  2. ...

## 3. Work Products
### 3.1 [Work Product Name]
**Description:** ...
**Levels of Detail:**
**Level 1: [Name]** - Description: ... - Characteristics: 1. ... 2. ...
**Instances:** (if applicable)

## 4. Activities
### 4.1 [Activity Name]
**Description:** ...
**Triggers:** ...
**How to Perform:** [2-5 paragraphs]
**Outcomes:** ...
**Observable Results:** ...
**Work Products Used:** ...
**Required Competencies:** ...

## 5. Competencies
### 5.1 [Competency Name]
**Description:** ...
**Levels:** Level 1: [Name] - Description: ...

## 6. Personas
### 6.1 [Persona Name]
**Description:** ...
**Competencies:** [competency + level pairs]
**Tags:** ...

## 7. Persona Groups (Teams)
### 7.1 [Team Name]
**Description:** ...
**Team Members:** ...
**Tags:** ...

## 8. Workflows and Patterns
### 8.1 [Pattern Name]
**Description:** ...
**Pattern Views:**
**View 1: [Name]** - Description: ... - Concerns Addressed: ... - Work Products: ... - Activities: ...

### 8.N Overarching Lifecycle
(Map to "The Cycle" from domain-framework.md)

## 9. Practices
### Practice Hierarchy (if multiple)
### 9.1 [Practice Name]
**Description:** ...
**Objectives and Outcomes:** ...
**Concerns:** [references to Section 2]
**Work Products:** [references to Section 3]
**Activities:** [references to Section 4]
**Workflows:** [references to Section 8]

## 10. Reference Content Candidates
### 10.1 [Reference Name]
**Description:** ...
**Related Concern:** ...
**Content Type:** ...
**URL:** ...
**Pages/Sections:** ...
**Estimated Maturity:** ...

## 11. Citations
### [1] [Exact Source Title]
- **Description**: ...
- **Authors**: ...
- **Date**: ...
- **Source**: ...
- **URL**: ...
```

### Quality Standards

| Dimension | Rule |
|-----------|------|
| Descriptions | Single sentence, max 20 words |
| State/LOD descriptions | Max 12 words |
| Narrative contexts | 1-3 sentences per bullet (not paragraphs) |
| Criteria | Distinct, observable, one sentence each; 3-7 per state (error if >10); no same-state near-duplicates |
| Completeness | NO placeholders ("etc.", "..."). Extract ALL relevant content. |
| Source fidelity | Let source drive progression, not templates. Preserve source maturity models. |
| Terminology | Use exact terms from source (aliasing happens in Phase 2) |

## Validation

After writing the report, run:

```bash
python3 utils/eval-skill-output.py practices/<practice-name>/ --phase 1 --summary
```

The validator checks:
- At least 8 top-level sections (## headings)
- All 8 required sections present: Outcomes, Concerns, Work Products, Activities, Competencies, Personas, Persona Groups, Workflows
- At least 5 numbered subsections (### N.)
- Sufficient citations/source references (>= 3)
- Four-perspective coverage (Business, Technology, People, Process perspectives mentioned)
- Inter-concern relationship documentation (>= 5 lines mentioning relationships)

Fix any FAIL assertions before reporting completion.

## Common Mistakes

1. **Premature practice boundaries** -- Do NOT finalize practice vs method decisions. Note structural signals only. Step 1.5 (Delineation Gate) handles this with baseline alpha context.
2. **Force-fitting the rubric** -- The workproduct-assessment-rubric.csv is a recognition lens, not a template. Let the source's natural maturity waypoints drive state definitions.
3. **Placeholder text** -- Never write "etc.", "[...]", "and so on", or leave sections incomplete. The full report must be generated in this phase.
4. **Fabricated URLs** -- If uncertain about a URL, omit it. Never guess or construct URLs that might not exist. Internal/intranet URLs are perfectly valid.
5. **Duplicate criteria** -- Extract unique criteria globally, then assign to states. Do not independently invent criteria per state, which produces near-duplicates.
6. **Missing concern relationships** -- Step 11 is critical for Phase 2. The validator checks for at least 5 lines documenting inter-concern relationships (production flows, enablement, governance, information flows, dependencies).
7. **Activity names without verbs** -- Activity names must be verb + specific object (e.g., "Design Security Architecture" not "Security Architecture Design").
8. **Previous-state prerequisites** -- Do NOT list the previous state of the same concern as a prerequisite. Sequential progression is implicit in state ordering.
9. **Missing acknowledgements** -- When source materials credit contributors (authors, working groups, institutions), note them. These become `acknowledgements` in the practice JSON, distinct from citations.
10. **Reference candidates that are documentation** -- References must be templates, examples, or artifacts a practitioner can directly use. A link to explanatory documentation is a citation, not a reference.
