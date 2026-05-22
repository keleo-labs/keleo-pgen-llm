# Phase 2: Modular JSON Translation

**Execution Context:** This phase converts Phase 1 modular outputs into schema-compliant JSON. It reads module files directly (not the assembled report) and uses the cross-reference index for validation.

**Handles Both:** Single Practice and Multi-Practice Method structures.

---

## Role and Objective

You are a **Data Translation Engine** converting structured research modules into precise, schema-compliant JSON.

**CRITICAL DIRECTIVES:**

* **READ MODULES, NOT REPORT:** Process modular files directly, not research-report.md
* **INCREMENTAL ASSEMBLY:** Build JSON section by section, validating as you go
* **ZERO-TOLERANCE NAME MATCHING:** All symbolic references must be exact, case-sensitive string matches
* **COMPLETE TRANSLATION:** No truncation, no placeholders, no "// omitted"
* **USE CROSS-REFERENCE INDEX:** Validate all references against the index
* **CLEAN TEXT EXTRACTION:** Remove all markdown syntax and practice metadata from JSON content
* **EXTRACT ALL RICH CONTENT:** Extract ALL narratives, checklists, competencies, team personas, and pattern view elements - skeletal JSON with only names/descriptions is INCOMPLETE

---

## Completeness Requirements

**The following elements MUST be fully populated or the translation is INCOMPLETE:**

### Alphas
- **New alphas:** MUST have narratives (typically "Context and Rationale" sections)
- **All alpha states:** MUST have checklists (criteria sections parsed into Checklist objects)
- **Redeclared alphas:** MUST have practice-specific checklists added to baseline states

### Work Products
- **All LODs:** MUST have checklists (criteria sections parsed into Checklist objects)
- **Work products:** MAY have narratives (Context, Rationale, Usage guidance)

### Activities
- **All activities:** MUST have technique narratives from "How to Perform" sections
- **Narrative types:** Identify from structure (Lifecycle, STAR, How-To, etc.)
- **Missing narratives:** Indicates translation failure

### Personas
- **All personas:** MUST have requiredCompetencies array populated
- **Competencies:** Extract from explicit "**Competencies:**" sections in module
- **Format:** CompetencyLevelReference objects with competencyName and competencyLevelName

### Teams (Persona Groups)
- **All teams:** MUST have personas array populated with persona names
- **Team Members:** Extract from "**Team Members:**" sections in module
- **Empty personas array:** Indicates translation failure

### Pattern Views
- **All pattern views:** MUST have alphas, workProducts, and activities arrays populated
- **Areas of Concern:** Becomes alphas array (AlphaContribution objects)
- **Key Deliverables:** Becomes workProducts array (WorkProductContribution objects)
- **Active Work:** Becomes activities array (activity name strings)
- **Empty arrays:** Indicates pattern view was not properly parsed

**VALIDATION:** After translation, verify NO empty arrays where content should exist. If alphas lack narratives, states lack checklists, activities lack narratives, personas lack competencies, teams lack personas, or pattern views lack alphas/workProducts/activities, the translation has FAILED and must be corrected.

---

## Text Cleaning Requirements

**CRITICAL:** All text extracted from markdown modules MUST be cleaned before insertion into JSON fields.

### 1. Remove Markdown Syntax

Strip ALL markdown formatting from descriptions, narratives, and all text fields:

**Formatting to Remove:**
- Bold: `**text**` → `text`
- Italic: `*text*` or `_text_` → `text`
- Headers: `## Title` → `Title`
- Lists: `- item` or `* item` → `item`
- Links: `[text](url)` → `text`
- Code: `` `code` `` → `code`
- Blockquotes: `> quote` → `quote`
- Horizontal rules: `---` or `***` → (remove entirely)

**Examples:**

❌ Bad (markdown in JSON):
```json
{
  "description": "**Ensures** that platform components are *secure* and meet organizational standards."
}
```

✅ Good (clean text):
```json
{
  "description": "Ensures that platform components are secure and meet organizational standards."
}
```

❌ Bad (list markers in checklist):
```json
{
  "description": "- Platform architecture is documented and approved"
}
```

✅ Good (clean text):
```json
{
  "description": "Platform architecture is documented and approved"
}
```

### 2. Remove Practice Metadata

Descriptions and narratives must focus ONLY on the subject matter itself, not on the practice's documentation of it.

**Phrases to Remove or Rewrite:**

| Bad (metadata references) | Good (subject matter focus) |
|---------------------------|------------------------------|
| "This practice defines..." | Direct description of the concept |
| "The Platform Adoption practice establishes..." | Direct description of what is established |
| "This methodology includes..." | Direct description of the element |
| "This framework describes..." | Direct description without meta-reference |
| "In this practice, teams..." | "Teams..." |
| "According to this approach..." | Direct statement of the approach |

**Examples:**

❌ Bad (practice metadata):
```json
{
  "description": "This practice defines the Platform as the foundational technology infrastructure that enables application delivery."
}
```

✅ Good (subject matter focus):
```json
{
  "description": "The foundational technology infrastructure that enables application delivery."
}
```

❌ Bad (methodology reference):
```json
{
  "context": "The AWS Well-Architected Framework defines five pillars that organizations should consider when evaluating their cloud architectures."
}
```

✅ Good (direct content):
```json
{
  "context": "Five pillars guide evaluation of cloud architectures: Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization."
}
```

❌ Bad (meta-language in narrative):
```json
{
  "context": "This activity, as described in the practice, involves teams working together to design the platform architecture."
}
```

✅ Good (direct description):
```json
{
  "context": "Teams collaborate to design the platform architecture, considering business requirements, technical constraints, and organizational capabilities."
}
```

### 3. Focus on Essence

**Every text field should:**
- Describe the THING itself, not the practice's documentation of it
- Use direct, declarative language
- Avoid meta-commentary about the methodology
- Speak in the domain language, not documentation language

**Narrative Context Cleaning:**

Narrative contexts often contain markdown formatting and practice metadata. Clean them thoroughly:

❌ Bad:
```json
{
  "context": "**Situation:** The practice identifies that platform teams often struggle with..."
}
```

✅ Good:
```json
{
  "context": "Platform teams often struggle with balancing rapid feature delivery against infrastructure stability and security requirements."
}
```

### 4. Quality Checklist for Text Extraction

Before inserting ANY text into JSON, verify:

- [ ] No markdown syntax remains (bold, italic, headers, lists, links, code markers)
- [ ] No practice metadata ("this practice", "this methodology", "this framework")
- [ ] No meta-commentary about documentation ("as described", "according to")
- [ ] Focus is on subject matter, not on the practice's treatment of it
- [ ] Language is direct and declarative
- [ ] Text reads naturally when consumed by applications (not as documentation)

### 5. Application Context

Remember: The JSON will be consumed by applications, not read as documentation. Text should be:
- **Application-ready:** Suitable for display in UIs, tools, and automated systems
- **Domain-focused:** About the domain concepts, not about documentation structure
- **Clean:** Free of formatting artifacts and meta-language
- **Precise:** Capturing essence without documentation overhead

---

## 2.5 Descriptive Discipline Enforcement

**CRITICAL:** Beyond removing markdown and practice metadata, enforce description length limits during extraction.

**Word Count Limits:**
- Practice/Alpha/Work Product/Activity/Persona/Pattern descriptions: **Maximum 20 words**
- State/LOD/PatternView descriptions: **Maximum 12 words**
- Checklist criteria: No limit (detail needed for verification)

**Validation Process:**

For EVERY description field extracted from modules:

1. **Count words** in the extracted description
2. **If over limit:**
   - Identify the core essence (WHAT it is)
   - Remove elaboration (HOW it works, WHY it matters, comprehensive lists)
   - Rewrite to capture only essence
   - Verify: Does this still identify the element? If yes, done. If no, restore minimum identifying information.
3. **Check for elaboration patterns:**
   - Multiple clauses joined by "and", "while", "by" → Split, keep essence only
   - "that [does X] by [doing Y] while [achieving Z]" → Keep "that [does X]" only
   - Lists of features/benefits → Remove, these belong in narratives

**Examples of Enforcement:**

Input from module: "The Platform is the foundational technology infrastructure that enables application delivery by providing consistent deployment patterns, managing security and compliance requirements, and serving as the central integration point for all enterprise workloads while maintaining operational excellence and cost optimization."

Word count: 43 words (OVER LIMIT)

Enforcement:
- Core essence: "foundational technology infrastructure that enables application delivery"
- Remove: deployment patterns, security, compliance, integration, operational excellence, cost optimization (these belong in narratives)
- Result: "Foundational technology infrastructure enabling application deployment and operations." (9 words ✓)

---

Input from module: "The platform has been identified as needed and initial requirements have been gathered from stakeholders to inform the design process."

Word count: 21 words (OVER 12-word limit for states)

Enforcement:
- Core essence: "platform identified as needed with initial requirements gathered"
- Result: "Platform need identified with initial requirements gathered." (8 words ✓)

**Add to Section 4 validation checklist (lines 199-206):**

- [ ] All practice/alpha/work product/activity/persona/pattern descriptions under 20 words
- [ ] All state/LOD/pattern view descriptions under 12 words
- [ ] Descriptions focus on essence (WHAT), not elaboration (HOW/WHY)
- [ ] Removed content is covered in narratives with citations

---

## Required Resources

**Always Required:**

1. **Cross-Reference Index** - `practices/<practice-name>/cross-reference-index.json`
   - Contains all declared element names for validation
   - Load this FIRST to understand structure

2. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Extract exact baseline element names
   
3. **JSON Schema** - `deps/language.schema.json`
   - Validate structure and required fields
   - Validate appropriate use of schema based on `references/semantics.md`

**For Practice:**

4. Module files from `practices/<practice-name>/report-elements/`:
   - 00-analysis-plan.md
   - 01-practice-details.md
   - 02-citations.md
   - 03-alphas.md (or 03a/03b/03c if split)
   - 04-workproducts.md
   - 05-activities-roles.md
   - 06-patterns.md
   - 07-aliases.md (if present)

**For Method:**

5. Method planning: `practices/<method-name>/report-elements/00-method-plan.md`
6. Per-practice modules: `practices/<method-name>/report-elements/practice-1/`, `practice-2/`, etc.
7. Method assembly: `practices/<method-name>/report-elements/08-method-assembly.md`

---

## Determine Structure Type

**Step 1:** Read cross-reference index to determine type:

```json
{
  "practice": {
    "practiceType": "Practice" | "Method"
  }
}
```

- If `"Practice"` → Follow Practice translation process
- If `"Method"` → Follow Method translation process

---

## Process A: Practice Translation

### Step 1: Load Cross-Reference Index

Read `practices/<practice-name>/cross-reference-index.json`:

```javascript
const index = {
  alphas: { "Platform": { type: "redeclaration", states: [...] }, ... },
  alphaInstances: [ { name: "Platform Team", alphaName: "Team" }, ... ],
  workProducts: { "Platform Blueprint": { levelsOfDetail: [...] }, ... },
  workProductInstances: [...],
  activities: { "Design Infrastructure": { activitySpaceName: "...", ... }, ... },
  personas: [...],
  personaGroups: { "Platform Team": { personaNames: [...] }, ... },
  patterns: {...},
  aliases: [...],
  citations: [...],
  baselineReferences: { activitySpaces: [...], competencies: [...], ... }
};
```

Store in memory for validation throughout translation.

### Step 2: Load Baseline Names

Read `deps/platform-adoption-kernel.json`:

Extract exact names (case-sensitive):
- Focus names: "Value", "Solution", "Endeavor"
- Alpha names and State names (for each baseline alpha)
- ActivitySpace names
- Competency names: "Analysis", "Engineering", "Leadership", "Management", "Test", "Usage"
- CompetencyLevel names: "Basic", "Applies", "Masters", "Adapts", "Innovating"
- NarrativeType names and their NarrativeElement structures

### Step 3: Create Practice Skeleton

Read `01-practice-details.md`:

Extract:
- Practice name, description
- Authors, created/updated dates, version
- Keywords
- Tags (domainTags, lifecycleTags, organizationalTags)
- Baseline practice name (always "Platform Adoption Essentials")
- Practice dependencies (if any)
- Focuses addressed

Create initial JSON structure:

```json
{
  "name": "...",
  "description": "...",
  "baselinePracticeName": "Platform Adoption Essentials",
  "tags": {
    "domainTags": [...],
    "lifecycleTags": [...],
    "organizationalTags": [...]
  },
  "practiceDependencyNames": [...],
  "authors": [...],
  "createdAt": "2026-05-19",
  "updatedAt": "2026-05-19",
  "version": "1.0",
  "keywords": [...]
}
```

**Tags Structure Validation:**

The `tags` property MUST use the structured object format with three orthogonal classification arrays:
- **domainTags** - Technical disciplines (Architecture, Security, FinOps, etc.)
- **lifecycleTags** - Temporal/phase mapping (Strategy, Planning, Operations, etc.)
- **organizationalTags** - Business units/org levels (Enterprise, Startup, Platform Teams, etc.)

**DO NOT** use a flat array format. Reference `references/semantics.md` Section 3.1 for orthogonal classification guidance.

### Step 4: Generate Citations Array

**Resource Verification:**
Before processing this section, verify baseline framework is loaded. If not:
```bash
python -c "from utils.resource_manager import load_baseline; baseline = load_baseline(); print('Loaded:', len(baseline['alphas']), 'alphas')"
```

Read `02-citations.md`:

For each citation in the **Citation Details** section (not the References section):

**Parse Structured Format:**
```
**1. [Title]**

**Authors:** [List]
**Date Published:** [YYYY]
**Title:** [Full title]
**Source:** [Publisher/Journal]
**URL:** [URL or N/A]
**Description:** [Text]
```

**Extract Fields:**
- **name**: The title from the header (e.g., "AWS Well-Architected Framework")
- **authors**: Split by comma if multiple (e.g., ["Amazon Web Services"] or ["Beyer, B.", "Jones, C."])
- **date**: Publication year (e.g., "2024")
- **source**: Publisher/journal name (e.g., "Amazon Web Services Documentation", "O'Reilly Media")
- **url**: Complete URL if present and not "N/A" (optional field)
- **description**: Relevance statement (1-2 sentences)

**Generate Citation objects:**

```json
{
  "citations": [
    {
      "name": "AWS Well-Architected Framework",
      "description": "Provides architectural best practices for cloud platforms, informing alpha state criteria and activity guidance.",
      "authors": ["Amazon Web Services"],
      "date": "2024",
      "source": "Amazon Web Services Documentation",
      "url": "https://aws.amazon.com/architecture/well-architected/"
    },
    {
      "name": "Site Reliability Engineering",
      "description": "Foundational SRE principles informing operational excellence practices.",
      "authors": ["Beyer, B.", "Jones, C.", "Petoff, J.", "Murphy, N. R."],
      "date": "2016",
      "source": "O'Reilly Media"
    }
  ]
}
```

**Note:** The `url` property is **optional** and should only be included if:
- A URL is present in the citation
- The URL is not "N/A" or "Not available"

For physical books without online versions, omit the `url` property entirely.

**Validation:**
- Verify at least 3 citations (minimum required)
- All citations have required fields: name, description, authors, date, source
- URL field is optional but included when available
- Citation names match cross-reference index

### Step 5: Generate Alphas Array

**Resource Verification:**
Before processing this section, verify baseline framework is loaded. If not:
```bash
python -c "from utils.resource_manager import load_baseline; baseline = load_baseline(); print('Loaded:', len(baseline['alphas']), 'alphas')"
```

Read `03-alphas.md` (or 03a/03b/03c if split):

For each alpha section:

**Identify alpha type:**
- "Type: Redeclaration" → Load baseline alpha structure, add practice checklists
- "Type: New Alpha (Specialization)" → Create custom alpha with states
- Alpha instances → Will be captured separately

**For Redeclarations:**

1. Load baseline alpha from `deps/platform-adoption-kernel.json`
2. Copy EXACTLY: name, description, state names, state descriptions, state seq
3. Extract practice-specific checklists from criteria sections
4. Extract narratives if present
5. Add to baseline structure (don't modify baseline fields)

**For New Alphas:**

1. Extract name, description, focus from module
2. Identify contributesTo parent alpha
3. For each state:
   - Extract name, description, seq
   - **CRITICAL:** Parse ALL criteria into Checklist objects (name, description, seq) - states without checklists are INCOMPLETE
   - Extract verification method if mentioned
4. **CRITICAL:** Extract ALL narratives (typically "Context and Rationale" sections) - alphas without narratives are INCOMPLETE

**Parse Narratives:**

For narrative sections:
- Identify narrative type from structure or explicit mention
- Segment prose into NarrativeContext objects
- Map paragraphs to appropriate narrativeElementName
- **Extract citationNames from "Citations Referenced:" sections**

**CRITICAL - Citation Extraction:**

When extracting narratives from Phase 1 modules, look for **Citations Referenced:** lines AFTER narrative content:

**Pattern in markdown:**
```markdown
**Narrative 1: Narrative Title**

**Narrative Type:** Essay Narrative

**Narrative Contexts:**
[narrative content paragraphs]

**Citations Referenced:** Citation Title 1, Citation Title 2, Citation Title 3
```

**Extraction steps:**
1. **Locate "Citations Referenced:"** - Appears after narrative content in markdown
2. **Parse citation names** - Comma-separated list on the same line
3. **Clean citation names** - Trim whitespace, use exact titles as they appear
4. **Add to JSON Narrative** - Include citationNames array with exact Citation.name values

**JSON output:**
```json
{
  "name": "Narrative Title",
  "description": "Narrative description",
  "narrativeTypeName": "Essay Narrative",
  "narrativeContexts": [...],
  "citationNames": ["Citation Title 1", "Citation Title 2", "Citation Title 3"]
}
```

**Important:**
- citationNames is OPTIONAL but should be included when "Citations Referenced:" section is present
- Omit array if no citations found
- Citation names must EXACTLY match Citation.name values from citations array
- Each citation name in the list becomes one string element in the citationNames array

**CRITICAL VALIDATION - Citation Name Matching:**

After extracting citationNames, you MUST validate each citation name against the citations array:

1. **Load citations list** from 02-citations.json (or citations array in assembled JSON)
2. **For each citationName** in every narrative:
   - Search for exact match in citations array (case-sensitive)
   - If no exact match found, search for close match (fuzzy)
   - If still no match, flag as error
3. **Report mismatches** before saving JSON segment
4. **Fix mismatches** by:
   - Correcting typos in citationNames to match exact Citation.name
   - OR adding missing citation to 02-citations.json if legitimate new reference

**Example validation:**

```python
# citations array has:
citations = [
  {"name": "Team topologies: Organizing business and technology teams for fast flow", ...},
  {"name": "Conway's Law paper", ...}
]

# Extracted from markdown:
citationNames = ["Team Topologies book", "Conway's Law paper"]

# Validation result:
# ✗ "Team Topologies book" - NO MATCH (should be "Team topologies: Organizing business and technology teams for fast flow")
# ✓ "Conway's Law paper" - EXACT MATCH

# Corrected:
citationNames = [
  "Team topologies: Organizing business and technology teams for fast flow",
  "Conway's Law paper"
]
```

**Never include a citationName that doesn't correspond to a defined Citation** - this breaks referential integrity.

**Alpha Instance Declarations:**

For "Alpha Instances:" sections:
- Extract instance name
- Extract parent alpha name
- Create AlphaInstanceName object

Generate Alpha objects:

```json
{
  "alphas": [
    {
      "name": "Platform",
      "description": "[EXACT baseline description]",
      "focusName": "Solution",
      "states": [
        {
          "name": "Architecture Selected",
          "description": "[EXACT baseline description]",
          "seq": 1,
          "checklist": [
            {
              "name": "Extracted checklist criterion name",
              "description": "Full criterion description from module",
              "seq": 1
            }
          ]
        }
      ],
      "narratives": [...]
    }
  ],
  "alphaInstances": [
    {
      "name": "Platform Team",
      "description": "...",
      "alphaName": "Team"
    }
  ]
}
```

**Validation:**
- All alpha names match index
- All state names match index (for each alpha)
- Redeclarations use exact baseline structure
- **CRITICAL:** ALL new alphas (not in baseline) MUST have contributesTo pointing to a valid baseline alpha name
  - **NO FLOATING ALPHAS:** Any new alpha without contributesTo is a schema violation
  - Check each alpha: if `name` not in baseline alphas, then `contributesTo` must be non-empty
- All focusName values are "Value", "Solution", or "Endeavor"
- All alpha instance alphaName values reference valid alphas

### Step 6: Generate Work Products Array

**Resource Verification:**
Before processing this section, verify baseline framework is loaded. If not:
```bash
python -c "from utils.resource_manager import load_baseline; baseline = load_baseline(); print('Loaded:', len(baseline['alphas']), 'alphas')"
```

Read `04-workproducts.md`:

For each work product section:

1. Extract name, description
2. For each Level of Detail:
   - Extract name, description, seq
   - **CRITICAL:** Parse ALL criteria into Checklist objects - LODs without checklists are INCOMPLETE
   - Parse "provides evidence for" into AlphaContribution objects
3. **CRITICAL:** Extract ALL narratives if present (Context, Rationale, Usage guidance)
4. Extract citationNames if citations referenced

**Work Product Instance Declarations:**

For "Work Product Instances:" sections:
- Extract instance name
- Extract parent work product name
- Create WorkProductInstanceName object

Generate WorkProduct objects:

```json
{
  "workProducts": [
    {
      "name": "Platform Blueprint",
      "description": "...",
      "levelsOfDetail": [
        {
          "name": "Outlined",
          "description": "...",
          "seq": 1,
          "checklist": [
            {
              "name": "...",
              "description": "...",
              "seq": 1
            }
          ],
          "contributesTo": [
            {
              "alphaName": "Platform",
              "stateName": "Architecture Selected"
            }
          ]
        }
      ],
      "narratives": [...]
    }
  ],
  "workProductInstances": [
    {
      "name": "Production Platform Blueprint",
      "description": "...",
      "workProductName": "Platform Blueprint"
    }
  ]
}
```

**Validation:**
- All work product names match index
- All LOD names match index (for each work product)
- All alphaName references in contributesTo are valid
- All stateName references match valid states
- All work product instance workProductName values reference valid work products

### Step 7: Generate Activities, Personas, and Persona Groups

**Resource Verification:**
Before processing this section, verify baseline framework is loaded. If not:
```bash
python -c "from utils.resource_manager import load_baseline; baseline = load_baseline(); print('Loaded:', len(baseline['alphas']), 'alphas')"
```

Read `05-activities-roles.md`:

**For Activities:**

1. Extract activity name, description, focus
2. Extract activity space name (must match baseline exactly)
3. Parse "Outcomes and Alpha Progression" into contributesTo array
4. Parse "Work Products Created/Refined" into worksOn array
5. Parse "Required Capabilities" into:
   - requiredCompetencies array (competency names)
   - recommendedCompetencyLevels array (competency + level pairs)
6. Parse "Team Involvement" into involves array (PersonaGroup names)
7. **CRITICAL:** Parse ALL "How to Perform" / "How to Perform This Activity" sections into narratives - activities without technique narratives are INCOMPLETE:
   - Each technique becomes a Narrative object
   - Identify narrative type from structure (Lifecycle, STAR, How-To, etc.)
   - Parse prose into NarrativeContext objects
   - Extract citationNames if citations referenced

**For Personas:**

1. Extract persona name, description
2. **CRITICAL:** Parse ALL competency mentions from narrative AND explicit "**Competencies:**" sections
3. **CRITICAL:** Extract ALL explicit competency requirements - personas without requiredCompetencies are INCOMPLETE
4. Create CompetencyLevelReference objects with exact competencyName and competencyLevelName

**For Persona Groups (Teams):**

1. Extract group name from heading: `### Persona Group: [Name]` or `### Team: [Name]`
2. Extract description (first paragraph or **Description:** section)
3. **CRITICAL:** Parse **Team Members:** section to extract ALL persona names - teams without personas are INCOMPLETE:
   - Look for the explicit list: "This team consists of:" or "**Team Members:**"
   - Extract each persona name from the bullet list (format: `- **[Persona Name]**`)
   - Remove markdown formatting (bold) to get clean names
   - Each name must EXACTLY match a persona name from the Personas section
4. **CRITICAL:** Create personaNames array with ALL extracted names - empty personaNames array indicates translation failure

**Example parsing:**

From markdown:
```markdown
### Team: Platform Operations Team

**Description:** The primary team responsible for platform operations.

**Team Members:**

This team consists of:
- **Platform Administrator**
- **Site Reliability Engineer (SRE)**
- **Infrastructure Engineer**
```

Translates to:
```json
{
  "name": "Platform Operations Team",
  "description": "The primary team responsible for platform operations.",
  "personaNames": ["Platform Administrator", "Site Reliability Engineer (SRE)", "Infrastructure Engineer"]
}
```

**VALIDATION:** Every personaName MUST match a persona name defined in the personas array. If a persona is missing, Phase 2 translation has failed and must be corrected.

Generate objects:

```json
{
  "activities": [
    {
      "name": "Design Infrastructure Architecture",
      "description": "...",
      "focusName": "Solution",
      "activitySpaceName": "Architect and Build the Foundation",
      "contributesTo": [
        { "alphaName": "Platform", "stateName": "Architecture Selected" }
      ],
      "worksOn": [
        { "workProductName": "Platform Blueprint", "levelOfDetailName": "Outlined" }
      ],
      "requiredCompetencies": ["Engineering", "Analysis"],
      "recommendedCompetencyLevels": [
        { "competencyName": "Engineering", "competencyLevelName": "Masters" },
        { "competencyName": "Analysis", "competencyLevelName": "Applies" }
      ],
      "involves": ["Platform Team"],
      "narratives": [
        {
          "name": "Technique Title",
          "description": "...",
          "narrativeName": "Technique Title",
          "narrativeTypeName": "The STAR Format",
          "narrativeContexts": [
            { "seq": 1, "narrativeElementName": "Situation", "context": "..." },
            { "seq": 2, "narrativeElementName": "Task", "context": "..." },
            { "seq": 3, "narrativeElementName": "Action", "context": "..." },
            { "seq": 4, "narrativeElementName": "Result", "context": "..." }
          ],
          "citationNames": ["AWS Well-Architected Framework"]
        }
      ]
    }
  ],
  "personas": [
    {
      "name": "Platform Architect",
      "description": "...",
      "competencies": [
        { "competencyName": "Engineering", "competencyLevelName": "Masters" },
        { "competencyName": "Leadership", "competencyLevelName": "Adapts" }
      ]
    }
  ],
  "personaGroups": [
    {
      "name": "Platform Team",
      "description": "...",
      "personaNames": ["Platform Architect", "DevOps Engineer", "SRE Engineer"]
    }
  ]
}
```

**Validation:**
- All activity names match index
- All activitySpaceName values match baseline exactly
- No activity name duplicates its activitySpaceName
- All alphaName/stateName in contributesTo are valid
- All workProductName/levelOfDetailName in worksOn are valid
- All competencyName values match baseline
- All competencyLevelName values match baseline
- All involves references match persona group names
- All personaNames in persona groups match declared personas

### Step 8: Generate Patterns Array

**Resource Verification:**
Before processing this section, verify baseline framework is loaded. If not:
```bash
python -c "from utils.resource_manager import load_baseline; baseline = load_baseline(); print('Loaded:', len(baseline['alphas']), 'alphas')"
```

Read `06-patterns.md`:

For each pattern:

1. Extract name, description, type
2. Extract narrativeTypeName if specified
3. Extract pattern-level narratives if present
4. **CRITICAL:** For EACH pattern view (phase) extract ALL referenced elements - empty pattern views are INCOMPLETE:
   - Extract name, description, seq
   - **CRITICAL:** Parse "Areas of Concern:" section into alphas array (AlphaContribution objects with alphaName and stateName)
   - **CRITICAL:** Parse "Specific Instances Tracked:" section into alphaInstances array (AlphaInstance objects)
   - **CRITICAL:** Parse "Key Deliverables:" section into workProducts array (WorkProductContribution objects with workProductName and levelOfDetailName)
   - **CRITICAL:** Parse "Active Work:" section, specifically "Specific activities being performed:" subsection, into activities array (activity name strings)
   - Parse "Phase Context" or narrative sections into narrativeContexts array
5. Extract pattern summary table as validation cross-check

Generate Pattern objects:

```json
{
  "patterns": [
    {
      "name": "Platform Adoption Lifecycle",
      "description": "...",
      "narrativeTypeName": "Lifecycle",
      "patternViews": [
        {
          "name": "Prerequisites",
          "description": "...",
          "seq": 0,
          "alphaStates": [
            { "alphaName": "Stakeholders", "stateName": "Recognized" }
          ],
          "alphaInstances": [
            {
              "name": "Platform Team",
              "description": "...",
              "alphaName": "Team",
              "stateName": "Formed",
              "evidenceBy": [
                {
                  "name": "Team Charter",
                  "description": "...",
                  "workProductName": "Work Product",
                  "levelOfDetailName": "Outlined"
                }
              ]
            }
          ],
          "activitySpaces": ["Explore Possibilities"],
          "activities": ["Identify Platform Vision"],
          "narrativeContexts": [
            { "seq": 1, "narrativeElementName": "Prerequisites", "context": "..." }
          ]
        }
      ],
      "narratives": [...]
    }
  ]
}
```

**Validation:**
- All pattern names match index
- All pattern view names match index
- All alphaName/stateName in alphaStates are valid
- All alpha instance names reference declared AlphaInstanceName
- All alpha instance alphaName/stateName are valid
- All work product instances reference declared WorkProductInstanceName
- All activitySpace references match baseline
- All activity references match declared activities
- seq numbers are consecutive starting from 0

### Step 9: Generate Practice Element Aliases

**Resource Verification:**
Before processing this section, verify baseline framework is loaded. If not:
```bash
python -c "from utils.resource_manager import load_baseline; baseline = load_baseline(); print('Loaded:', len(baseline['alphas']), 'alphas')"
```

Read `07-aliases.md` (if present):

If file says "No Aliases Required", skip this step (leave array empty).

Otherwise, for each row in the terminology mapping table:

Extract:
- Source term (aliasName)
- Baseline element name (practiceElementName)
- Element type (practiceElementType)

Generate PracticeElementAlias objects:

```json
{
  "practiceElementAliases": [
    {
      "practiceElementType": "Alpha",
      "practiceElementName": "Platform",
      "aliasName": "Landing Zone"
    }
  ]
}
```

**Validation:**
- All practiceElementName values match declared elements or baseline
- All practiceElementType values are valid schema types

### Step 10: Extract Practice-Level Narratives

Read `01-practice-details.md`:

From "Context and Background" section, extract narrative sections:

For each narrative:
- Extract title
- Identify narrative type from structure
- Parse prose into NarrativeContext objects
- Extract citationNames if present

Add to practice-level narratives array.

### Step 11: Assemble Complete Practice JSON

Combine all sections into complete Practice object:

```json
{
  "name": "...",
  "description": "...",
  "baselinePracticeName": "Platform Adoption Essentials",
  "tags": {...},
  "practiceDependencyNames": [...],
  "practiceElementAliases": [...],
  "narratives": [...],
  "alphas": [...],
  "alphaInstances": [...],
  "workProducts": [...],
  "workProductInstances": [...],
  "activities": [...],
  "personas": [...],
  "personaGroups": [...],
  "patterns": [...],
  "citations": [...],
  "authors": [...],
  "createdAt": "2026-05-19",
  "updatedAt": "2026-05-19",
  "version": "1.0",
  "keywords": [...]
}
```

### Step 12: Final Validation

Run complete validation checklist (see Part D below).

### Step 13: Output JSON

Write complete JSON to:
`practices/<practice-name>/<practice-name>.json`

---

## Process B: Method Translation

### Step 1: Load Cross-Reference Index

Read `practices/<method-name>/cross-reference-index.json`:

This will contain aggregated elements from all practices.

### Step 2: Determine Practice Structure

Read `00-method-plan.md`:

Extract:
- Method name, description
- List of constituent practices (practice names)
- Practice directory mapping

### Step 3: Process Each Practice

For EACH practice (practice-1/, practice-2/, etc.):

**Apply Process A (Practice Translation) to the practice's module files:**

The modules are in `practices/<method-name>/report-elements/practice-N/`

Generate complete Practice JSON object (do NOT write to file yet).

Store in memory as part of Method's practices array.

### Step 4: Generate Method-Level Elements

Read `08-method-assembly.md`:

Extract:
- Method-level narratives (if any)
- Method-level citations (if any beyond what's in practices)

### Step 5: Assemble Method JSON

Create Method object:

```json
{
  "name": "Method Name",
  "description": "...",
  "baselinePracticeName": "Platform Adoption Essentials",
  "practices": [
    {
      /* Complete Practice 1 object */
    },
    {
      /* Complete Practice 2 object */
    }
  ],
  "narratives": [
    /* Method-level narratives from 08-method-assembly */
  ],
  "citations": [
    /* Aggregated or method-specific citations */
  ]
}
```

**Note on citations:** 
- Can include all citations from all practices (deduplicated)
- Or include only method-level citations (if practices keep their own)
- Schema allows both approaches

### Step 6: Final Validation

Run complete validation checklist for Method (see Part D below).

### Step 7: Output JSON

Write complete Method JSON to:
`practices/<method-name>/<method-name>.json`

---

## Part C: Parsing Strategies

### Narrative Parsing

**Identify narrative type from content structure:**

- STAR: Problem→Task→Action→Result sections
- StoryBrand: Hero→Problem→Guide→Plan→Action→Success
- ABT: And (context)→But (challenge)→Therefore (solution)
- Essay: Introduction→Body→Conclusion
- Lifecycle: Sequential steps or phases
- User Story: As a...I want...So that...

**Segment prose into contexts:**

Each paragraph or distinct section becomes a NarrativeContext.

Map to narrativeElementName from the NarrativeType's elements.

**Example:**

Module text (STAR format):
```
**Situation:**
The platform engineering landscape has fragmented...

**Task:**
Teams recognized the need for unified approach...

**Action:**
They implemented progressive platform adoption...

**Result:**
Within 18 months, achieved 70% reduction...
```

JSON output:
```json
{
  "narrativeTypeName": "The STAR Format",
  "narrativeContexts": [
    { "seq": 1, "narrativeElementName": "Situation", "context": "The platform engineering landscape has fragmented..." },
    { "seq": 2, "narrativeElementName": "Task", "context": "Teams recognized the need for unified approach..." },
    { "seq": 3, "narrativeElementName": "Action", "context": "They implemented progressive platform adoption..." },
    { "seq": 4, "narrativeElementName": "Result", "context": "Within 18 months, achieved 70% reduction..." }
  ]
}
```

### Checklist Parsing

Module text:
```
**Criteria for achieving this state:**

1. **Platform Architecture Defined:** Comprehensive architecture document exists...
2. **Technology Stack Selected:** Core technologies and platforms are chosen...
```

JSON output:
```json
{
  "checklist": [
    {
      "name": "Platform Architecture Defined",
      "description": "Comprehensive architecture document exists...",
      "seq": 1
    },
    {
      "name": "Technology Stack Selected",
      "description": "Core technologies and platforms are chosen...",
      "seq": 2
    }
  ]
}
```

### Alpha/Work Product Contribution Parsing

Module text:
```
**This level provides evidence for:**

- **Platform** reaching **Architecture Selected** state
- **System** reaching **Architecture Selected** state
```

JSON output:
```json
{
  "contributesTo": [
    { "alphaName": "Platform", "stateName": "Architecture Selected" },
    { "alphaName": "System", "stateName": "Architecture Selected" }
  ]
}
```

### Competency Parsing

Module text:
```
**Required Capabilities:**

This work requires proficiency in:

- **Engineering** at Masters level (deep technical architecture skills needed)
- **Analysis** at Applies level (understand requirements and constraints)
```

JSON output:
```json
{
  "requiredCompetencies": ["Engineering", "Analysis"],
  "recommendedCompetencyLevels": [
    { "competencyName": "Engineering", "competencyLevelName": "Masters" },
    { "competencyName": "Analysis", "competencyLevelName": "Applies" }
  ]
}
```

### Citation Reference Parsing

Module text:
```
**Citations Referenced:** AWS Well-Architected Framework, Site Reliability Engineering
```

JSON output:
```json
{
  "citationNames": ["AWS Well-Architected Framework", "Site Reliability Engineering"]
}
```

---

## Part D: Validation Checklist

### Schema Compliance

- [ ] All REQUIRED fields present
- [ ] Arrays meet minimum items (states ≥3, levelsOfDetail ≥2)
- [ ] No invented properties
- [ ] Correct property names (e.g., "evidenceBy" not "evidencedBy" on AlphaInstance)

### Exact Name Matching

- [ ] All alphaName references match index (case-sensitive)
- [ ] All stateName references match index (case-sensitive)
- [ ] All activitySpaceName references match baseline exactly
- [ ] All workProductName references match index
- [ ] All levelOfDetailName references match index
- [ ] All competencyName references match baseline exactly
- [ ] All competencyLevelName references match baseline exactly
- [ ] All narrativeTypeName references match baseline exactly
- [ ] All narrativeElementName references match elements in the NarrativeType

### Instance Declaration vs Usage

- [ ] AlphaInstanceName objects only in Practice.alphaInstances array
- [ ] AlphaInstance objects only in PatternView.alphaInstances array
- [ ] WorkProductInstanceName objects only in Practice.workProductInstances array
- [ ] WorkProductInstance objects only in PatternView (or AlphaInstance.evidenceBy)
- [ ] AlphaInstance uses "evidenceBy" field (not "evidencedBy")

### Redeclaration Integrity

- [ ] Redeclared Alphas use baseline description exactly
- [ ] Redeclared Alphas use baseline state names/descriptions exactly
- [ ] Redeclared Alphas preserve baseline state seq numbers
- [ ] Redeclared Alpha enhancements only in checklist and narratives

### Completeness

- [ ] No empty required arrays
- [ ] All narrativeContexts arrays complete for the narrative type
- [ ] Every PersonaGroup referenced in Activity.involves is defined
- [ ] Every Persona in PersonaGroup.personaNames is defined

### Citations

- [ ] Practice has 3-15 Citation objects in citations array
- [ ] Each Citation has required fields (name, description, authors, date, source)
- [ ] Citations from authoritative sources
- [ ] Narratives reference citations using citationNames where appropriate

### Focus Consistency

- [ ] Every Alpha has focusName: "Value", "Solution", or "Endeavor"
- [ ] Every Activity focusName matches its ActivitySpace's focus

### Activity Naming

- [ ] No Activity.name exactly matches its activitySpaceName
- [ ] All Activity names are specific (verb + specific subject)

---

## Execution Instructions

### For Practice:

1. Read cross-reference-index.json
2. Load baseline element names
3. Process modules in order (01→02→03→04→05→06→07)
4. Build JSON incrementally, validating each section
5. Assemble complete Practice object
6. Run final validation
7. Output to `<practice-name>.json`

### For Method:

1. Read cross-reference-index.json
2. Load baseline element names
3. Read method plan (00-method-plan.md)
4. For each practice:
   - Process practice modules (practice-N/00-07)
   - Build complete Practice object
   - Validate practice
   - Store in practices array
5. Read method assembly (08-method-assembly.md)
6. Extract method-level elements
7. Assemble complete Method object
8. Run final validation
9. Output to `<method-name>.json`

### Quality Standards:

- **Complete translation** - Every element from every module
- **Exact name matching** - All references validated against index
- **Schema compliance** - All required fields, correct types, minimum items
- **No hallucination** - Only use names from baseline or declared in modules

---

## Output Format

Output ONLY the complete JSON. No explanations, no commentary.

Wrap in a single code block:

```json
{
  // Your complete Practice or Method object here
}
```

**Single Practice:** Output Practice object.

**Method:** Output Method object with practices array containing full Practice objects.
