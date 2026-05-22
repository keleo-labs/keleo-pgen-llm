# Phase 1 Modular Prompts

Prompts for generating focused research analysis modules (3K-20K words each) from source methodology documentation.

## Overview

Phase 1 uses a **modular approach** to break down methodology analysis into manageable pieces. Each module prompt generates a self-contained markdown file that analyzes one aspect of the source methodology.

**Benefits:**
- Manageable size (no 80K word monoliths)
- Incremental progress (generate and validate one section at a time)
- Iteration-friendly (re-generate individual modules without redoing everything)
- Parallel potential (Wave 2 modules can run concurrently)

## Module Sequence

### For Single Practice

Generate modules in this order:

1. **00-analysis-plan.md** - Strategic foundation
2. **01-practice-details.md** - Practice metadata
3. **02-citations.md** - Bibliographic references
4. **03-alphas.md** - Alpha definitions
5. **04-workproducts.md** - Work product definitions
6. **05-activities-roles.md** - Activities, personas, teams
7. **06-patterns.md** - Pattern orchestrations
8. **07-aliases.md** - Terminology mappings (if needed)

### For Multi-Practice Method

Generate modules in this order:

1. **00-method-plan.md** - Method composition strategy
2. For each practice 1..N:
   - Create subdirectory `practice-N/`
   - Generate modules 00-07 in practice subdirectory (same as single practice)
3. **08-method-assembly.md** - Method integration layer

## Module Descriptions

### 00-analysis-plan.md (Single Practice)

**Purpose:** Strategic analysis and planning foundation

**Key Outputs:**
- Four-perspective framework application preview
- Alpha extension strategy (which baseline alphas to redeclare, which new alphas to create)
- Activity derivation plan
- Pattern identification approach
- Module splitting decisions (if needed)

**Dependencies:** Source materials only

**Output Size:** ~3-5K words

---

### 00-method-plan.md (Multi-Practice Method)

**Purpose:** Method composition and integration planning

**Key Outputs:**
- Method overview and objectives
- Practice composition (how many practices, their scopes)
- Practice boundaries and relationships
- Integration strategy
- Method-level patterns
- Adoption guidance framework

**Dependencies:** Source materials only

**Output Size:** ~4-6K words

---

### 01-practice-details.md

**Purpose:** Practice metadata, tags, and context

**Key Outputs:**
- Practice name, description, authors, version
- Domain tags (technology/business domains)
- Lifecycle tags (planning, execution, optimization, etc.)
- Organizational tags (team types, organizational scopes)
- Context narratives (background, purpose, value proposition)
- Keywords for discoverability

**Dependencies:** Module 00 (analysis plan or method plan)

**Output Size:** ~2-3K words

**Quality Rules:**
- Description MUST be single sentence
- Tags should be specific and searchable
- Context narratives: 2-4 focused paragraphs

---

### 02-citations.md

**Purpose:** Bibliographic references in APA7 format

**Key Outputs:**
- 5-15 authoritative citations
- Primary sources (methodology creators, official documentation)
- All user-provided sources included
- Citation Standard narrative type

**Dependencies:** Minimal (can read Module 01 for context)

**Output Size:** ~1-2K words

**Quality Rules:**
- APA7 format strictly
- Prioritize primary/authoritative sources
- Include URLs where available
- Each citation: name, description, authors, date, source, url

---

### 03-alphas.md

**Purpose:** Alpha definitions with states, checklists, narratives

**Key Outputs:**
- Baseline alpha redeclarations (enriched with practice-specific content)
- New practice-specific alphas (ALL must have contributesTo)
- States (minimum 3, typically 4-7 per alpha)
- State checklists (5-7 criteria per state)
- Context and Rationale narratives
- Alpha instances (if tracking specific occurrences)

**Dependencies:**
- Module 00 for alpha extension strategy
- Module 01 for practice context

**Output Size:** ~15-20K words (may split by focus: 03a-value, 03b-solution, 03c-endeavor)

**Quality Rules:**
- **NO FLOATING ALPHAS:** All new alphas MUST have contributesTo to baseline alpha
- State descriptions: single sentence
- Checklist criteria: one sentence each (5-7 per state)
- Narratives: 2-4 focused paragraphs
- State progression should reflect source methodology's natural maturity model

---

### 04-workproducts.md

**Purpose:** Work product definitions with Levels of Detail

**Key Outputs:**
- All work product definitions
- Levels of Detail (minimum 3, typically 3-5 per work product)
- LOD checklists (3-5 characteristics per level)
- contributesTo alpha states for each LOD
- Usage narratives
- Work product instances (if tracking variants)

**Dependencies:**
- Module 00 for work product strategy
- Module 01 for practice context
- Module 03 for alpha states

**Output Size:** ~10-15K words

**Quality Rules:**
- Work product descriptions: single sentence
- LOD characteristics: one sentence each (3-5 per level)
- LOD.contributesTo is REQUIRED (which alpha states this LOD proves)
- Levels should reflect natural progression from descriptive → comprehensive → automated
- Usage narratives: 2-4 focused paragraphs

---

### 05-activities-roles.md

**Purpose:** Activities with technique narratives, personas, and teams

**Key Outputs:**
- All activity definitions
- contributesTo alpha states
- worksOn work products
- Competency requirements (recommendedCompetencyLevels with exact baseline names)
- Rich "How to Perform" technique narratives (STAR, How-To, StoryBrand, etc.)
- All personas with competency requirements
- Persona Groups (teams) with member lists

**Dependencies:**
- Module 00 for activity derivation plan
- Module 01 for practice context
- Module 03 for alpha states
- Module 04 for work products

**Output Size:** ~15-20K words (largest module due to technique narratives)

**Quality Rules:**
- Activity names MUST NOT duplicate ActivitySpace names
- Activity descriptions: single sentence
- Technique narratives: 2-5 focused paragraphs using structured frameworks
- Persona descriptions: single sentence
- Competency names MUST match baseline exactly (Analysis, Engineering, Leadership, Management, etc.)
- Team descriptions: single sentence
- Extract ALL "How to Perform" content from source

---

### 06-patterns.md

**Purpose:** Pattern orchestrations and views

**Key Outputs:**
- Pattern definitions (lifecycle orchestrations)
- Pattern narratives (context and usage)
- Pattern views (specific use cases or variants)
- Activities per view
- Alpha state progressions per view
- Work products per view
- View sequencing (seq property)
- Alpha instances and work product instances tracked in views

**Dependencies:**
- Module 00 for pattern identification
- Module 01 for practice context
- Module 03 for alpha states
- Module 04 for work products
- Module 05 for activities

**Output Size:** ~10-15K words

**Quality Rules:**
- Pattern descriptions: single sentence
- Pattern narratives: 2-4 focused paragraphs
- Each pattern view MUST have seq number
- Activities, alphas, work products clearly identified per view
- Extract instance tracking for assembly

---

### 07-aliases.md

**Purpose:** Terminology mappings when source uses different terms

**Key Outputs:**
- Practice element aliases (source terminology → baseline terminology)
- OR "No aliases needed" if source uses same terminology

**Dependencies:** All previous modules (to know element names)

**Output Size:** ~0.5-1K words (often very short or empty)

**Quality Rules:**
- Only create aliases if source ACTUALLY uses different terms
- Map source terms to exact baseline element names
- Document WHY alias is needed (disambiguation, vendor-specific naming, etc.)

---

### 08-method-assembly.md (Multi-Practice Methods Only)

**Purpose:** Method integration layer

**Key Outputs:**
- Cross-practice integration patterns
- Method-level pattern orchestrations
- Adoption pathways (how to adopt practices incrementally)
- Cross-practice dependencies
- Method-level narratives

**Dependencies:** All practice modules (practice-1/ through practice-N/)

**Output Size:** ~3-5K words

**Quality Rules:**
- Focus on integration, not duplication
- Show how practices work together
- Provide adoption guidance
- Identify cross-practice patterns

## Module Generation Guidelines

### Conciseness Rules

**Descriptions:**
- ALL descriptions MUST be single grammatically correct sentences
- Capture ESSENCE only, not exhaustive detail
- Additional context goes in narratives, not descriptions

**Checklists:**
- State checklists: 5-7 criteria per state (not 10+)
- LOD checklists: 3-5 characteristics per level
- Each criterion: ONE sentence explaining what must be verifiable

**Narratives:**
- Focus on salient points, not exhaustive documentation
- 2-5 paragraphs, each 2-4 sentences
- Structured frameworks for technique narratives (STAR, How-To, etc.)
- Trust citations for deeper detail (don't reproduce source verbatim)

### Natural Progression Discovery

**Use source content, not templates:**
- Read how SOURCE describes progression/maturity
- Identify natural waypoints from methodology
- Use rubric (workproduct-assessment-rubric.csv) as recognition LENS, not template to impose
- Create states/LODs matching source, not force-fitting rubric

**Examples:**
- ✅ Good: Source describes "manual → scripted → CI/CD" → Create 3-4 LODs matching these
- ❌ Bad: Forcing 5 rubric levels when source only describes 3 stages

### Text Cleaning

**Avoid in research modules:**
- Do NOT include markdown syntax in descriptions/narratives (it will be cleaned in Phase 2)
- Do NOT reference the practice's documentation structure ("This practice defines...")
- Focus on SUBJECT MATTER, not the documentation itself

**Write naturally:**
- "Ensures infrastructure is secure and compliant" (subject matter)
- NOT "This activity ensures infrastructure..." (documentation structure)

## Parallel Execution Opportunities

### Wave 2: Concurrent Generation

Modules 02, 03, 04 have minimal cross-dependencies and can be generated in parallel:

- **Agent A:** Module 02 (citations) - mostly independent
- **Agent B:** Module 03 (alphas) - references Module 00 for strategy
- **Agent C:** Module 04 (workproducts) - references Module 03 lightly for alpha states

**Critical path:** Module 03 (alphas) typically takes longest (15-20 min)

See `.claude/skills/translate-methodology/PARALLEL-EXECUTION-GUIDE.md` for detailed parallel execution instructions.

## Output Location

**Single Practice:**
```
practices/<practice-name>/report-elements/
├── 00-analysis-plan.md
├── 01-practice-details.md
├── 02-citations.md
├── 03-alphas.md
├── 04-workproducts.md
├── 05-activities-roles.md
├── 06-patterns.md
└── 07-aliases.md
```

**Multi-Practice Method:**
```
practices/<method-name>/report-elements/
├── 00-method-plan.md
├── practice-1/
│   ├── 00-analysis-plan.md
│   ├── 01-practice-details.md
│   └── ... (modules 02-07)
├── practice-2/
│   └── ... (modules 00-07)
└── 08-method-assembly.md
```

## Next Steps After Phase 1

After all modules are generated:

1. **Phase 1.5:** Run `phase-1-assembly.md` prompt to:
   - Assemble modules into `research-report.md`
   - Generate `cross-reference-index.json`
   - Validate completeness

2. **Phase 2:** Run `phase-2-modular.md` prompt to:
   - Translate modules to JSON
   - Build schema-compliant Practice/Method JSON

## Related Documentation

- **Main Prompts README:** [../README.md](../README.md)
- **Phase 1 Assembly:** [../phase-1-assembly.md](../phase-1-assembly.md)
- **Phase 2 Translation:** [../phase-2-modular.md](../phase-2-modular.md)
- **Skill Workflow:** `../../.claude/skills/translate-methodology/SKILL.md`
- **Semantic Guidance:** `../../references/semantics.md`
