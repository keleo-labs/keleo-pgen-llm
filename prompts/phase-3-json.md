# Phase 3: JSON Generation Prompt

## Context

You are conducting **Phase 3: JSON Generation** of a methodology translation workflow. This phase creates machine-readable Practice or Method JSON that precisely conforms to the Practice Language JSON Schema.

## Objective

Generate schema-compliant JSON files that:
- Represent the Phase 2 mapping in valid JSON structure
- Conform to `deps/language.schema.json` schema specification
- Maintain referential integrity with baseline practice
- Pass all validation checks (schema, baseline, internal integrity)

## Resources Available

You have access to the following resources via the Read tool:

1. **practices/<practice-name>/02-mapping-guide.md** (Phase 2 output)
   - Complete mapping specification
   - Read this as primary source for JSON generation

2. **deps/language.schema.json** (JSON Schema)
   - Authoritative schema definition
   - Defines structure, required fields, types
   - READ THIS to understand exact JSON structure

3. **references/semantics.md** (Semantic Guidance)
   - Section 3: Structural Foundations (PracticeElement, tags, checklists)
   - Section 4: Alpha-State Trajectory
   - Section 5: Work Product Elements
   - Section 6: Activities and Personas
   - Section 7: Narratives
   - Section 8: Patterns and PatternViews
   - READ relevant sections for JSON structure guidance

4. **Baseline Practice JSON** (same as Phase 2)
   - For validation of references
   - For extracting baseline structure

## Instructions

### Step 1: Load Resources

**Read these in order:**

1. **Read `practices/<practice-name>/02-mapping-guide.md`**
   - This is your PRIMARY source for content
   - Review all mapped elements completely

2. **Read `deps/language.schema.json`**
   - Understand exact schema structure
   - Note required vs optional properties
   - Understand property types (string, array, object)
   - Understand symbolic references vs embedded objects

3. **Read `references/semantics.md` (relevant sections)**
   - Focus on JSON structure examples
   - Note schema-specific rules (e.g., checklist format, competency references)

### Step 2: Determine Output Type

**From mapping guide, determine:**
- **Single Practice** → Generate Practice JSON
- **Method (Multiple Practices)** → Generate Method JSON with embedded practices

### Step 3: Generate JSON Incrementally

**Build JSON in this order to ensure dependencies are met:**

#### 3.1 Practice/Method Skeleton

**For Practice:**
```json
{
  "name": "practice-name",
  "description": "Single sentence from mapping guide",
  "baselinePracticeName": "Platform Adoption Essentials",
  "tags": {
    "domainTags": [...],
    "lifecycleTags": [...],
    "organizationalTags": [...]
  },
  "keywords": [...],
  "authors": [...],
  "createdAt": "YYYY-MM-DD",
  "updatedAt": "YYYY-MM-DD",
  "version": "1.0.0"
}
```

**Parent Practice Mode:** When extending a parent practice (instead of mapping directly to a baseline):
- `baselinePracticeName`: Set to the value **inherited** from the parent practice's `baselinePracticeName` (NOT the parent practice name itself)
- `practiceDependencyNames`: Auto-populated with the parent practice name(s) provided in Step 0.25
- All `contributesTo` references should primarily target parent practice alphas using canonical names
```json
{
  "baselinePracticeName": "Platform Adoption Essentials",  // inherited from parent
  "practiceDependencyNames": ["Red Hat OpenShift Foundations"],  // parent practice names
  ...
}
```

**For Method:**
```json
{
  "name": "method-name",
  "description": "Single sentence from mapping guide",
  "baselinePracticeName": "Platform Adoption Essentials",
  "practices": []  // Will be populated with Practice objects
}
```

**NOTE:** The schema uses structural discrimination (presence of `practices` array) to identify Methods vs Practices, not an explicit "kind" property.

#### 3.2 Citations

Add citations array (for both Practice and Method):
```json
"citations": [
  {
    "name": "Exact source title",
    "description": "1 sentence summary",
    "authors": ["Author 1", "Author 2"],
    "date": "YYYY",
    "source": "Publisher or journal",
    "url": "https://..."
  }
]
```

**CRITICAL:** Citations have NO narratives property

#### 3.3 Assets (Optional)

If the mapping guide identifies visual assets, add assets array. **PRIORITIZE externally-referenceable assets:**

**Priority 1 - Font Character Icons (for all icons):**

```json
"assets": [
  {
    "name": "platform-icon",
    "description": "Platform infrastructure icon",
    "type": "font-character",
    "fontFamily": "Font Awesome 6 Free",
    "fontCharacter": "fa-cubes",
    "fontWeight": "900"
  },
  {
    "name": "team-icon",
    "description": "Team collaboration icon",
    "type": "font-character",
    "fontFamily": "Font Awesome 6 Free",
    "fontCharacter": "fa-users",
    "fontWeight": "900"
  }
]
```

**Priority 2 - External URLs (for diagrams, templates, reference architectures):**

```json
"assets": [
  {
    "name": "aws-reference-architecture",
    "description": "AWS Well-Architected multi-region reference architecture",
    "type": "diagram",
    "url": "https://docs.aws.amazon.com/wellarchitected/latest/framework/images/multi-region.png"
  },
  {
    "name": "adr-template",
    "description": "Architecture Decision Record template by Michael Nygard",
    "type": "template",
    "url": "https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/templates/decision-record-template-by-michael-nygard/index.md"
  }
]
```

**Priority 3 - Bundled Files (only when no external alternative exists):**

```json
"assets": [
  {
    "name": "custom-pattern-diagram",
    "description": "Practice-specific pattern orchestration workflow",
    "type": "diagram",
    "path": "assets/diagrams/pattern-lifecycle.svg",
    "mimeType": "image/svg+xml"
  }
]
```

**Asset Properties by Type:**

**All assets require:**
- **name**: Unique identifier (kebab-case)
- **description**: Human-readable explanation (1-2 sentences)
- **type**: `icon | diagram | template | image | font-character`

**Font character assets (Priority 1):**
- **fontFamily**: `"Font Awesome 6 Free"` | `"Material Icons"`
- **fontCharacter**: Icon identifier (e.g., `"fa-cubes"`, `"fa-users"`, `"settings"`)
- **fontWeight**: `"400"` | `"900"` | `"bold"` (optional, defaults to regular)

**External URL assets (Priority 2):**
- **url**: Direct link to external resource (methodology sites, GitHub, official docs)

**Bundled file assets (Priority 3):**
- **path**: Relative path (e.g., `"assets/diagrams/custom.svg"`)
- **mimeType**: `"image/svg+xml"` | `"image/png"` | `"application/pdf"`
- **checksum**: `"sha256:..."` (optional, for integrity verification)

**Linking Assets to Elements:**

Individual elements reference assets via optional `assetName` property (singular, not array):

```json
{
  "name": "Platform",
  "description": "Platform infrastructure capability",
  "assetName": "platform-icon",
  "focusName": "Solution",
  "states": [...]
}
```

```json
{
  "name": "Design Reference Architecture",
  "description": "Create multi-region platform architecture",
  "assetName": "aws-reference-architecture",
  "activitySpaceName": "Architecture Design",
  "focusName": "Solution",
  "worksOn": [...],
  "requiredCompetencies": [...]
}
```

**Asset Assignment Guidelines:**

- **Practice/Method**: Main icon (font character)
- **Alphas**: Icon for UI representation (font character)
- **Activities**: Icon for activity type (font character) OR reference diagram (URL)
- **Competencies**: Skill area icon (font character)
- **Work Products**: Template reference (URL) if applicable
- **Patterns**: Workflow diagram (URL or bundled if custom)

**Common Font Awesome Icons:**

- Platform/Infrastructure: `fa-cubes`, `fa-server`, `fa-cloud`
- Team/People: `fa-users`, `fa-user-group`
- Security: `fa-shield-halved`, `fa-lock`
- Architecture: `fa-sitemap`, `fa-diagram-project`
- Development: `fa-code`, `fa-laptop-code`
- Operations: `fa-gears`, `fa-wrench`
- Strategy: `fa-compass`, `fa-lightbulb`

#### 3.4 Narratives (Practice/Method Level)

Add practice-level or method-level narratives:
```json
"narratives": [
  {
    "name": "Practice Intent",
    "description": "Narrative describing practice objectives",
    "narrativeTypeName": "STAR",
    "narrativeContexts": [
      {
        "seq": 1,
        "narrativeElementName": "Situation",
        "context": "1-2 sentences"
      },
      {
        "seq": 2,
        "narrativeElementName": "Task",
        "context": "1-2 sentences"
      }
    ],
    "citationNames": ["Citation 1", "Citation 2"]
  }
]
```

#### 3.4 Alphas

Add alphas array:
```json
"alphas": [
  {
    "name": "Alpha Name",
    "description": "Single sentence",
    "focusName": "Value | Solution | Endeavor",
    "contributesTo": "baseline-alpha-name",  // REQUIRED for new alphas
    "relatesTo": [  // ONLY for new alphas (NOT redeclarations)
      {
        "relationship": "produces",
        "alphaName": "Platform Asset"
      },
      {
        "relationship": "depends on",
        "alphaName": "Requirements"
      }
    ],
    "tags": {
      "domainTags": [...],
      "lifecycleTags": [...],
      "organizationalTags": [...]
    },
    "states": [
      {
        "name": "State Name",
        "description": "Single sentence (max 12 words)",
        "seq": 1,
        "checklist": [
          {
            "name": "Checklist item name",
            "description": "One sentence verification criterion",
            "seq": 1,
            "evidencedBy": [
              {
                "workProductName": "Work Product",
                "levelOfDetailName": "Level Name"
              }
            ]
          }
        ],
        "tags": { ... },
        "narratives": [ ... ]  // Optional
      }
    ],
    "narratives": [
      {
        "name": "Context and Rationale",
        "description": "Why this alpha matters",
        "narrativeTypeName": "Essay",
        "narrativeContexts": [...],
        "citationNames": [...]
      }
    ]
  }
]
```

**CRITICAL:**

- New alphas MUST have `contributesTo` (NO FLOATING ALPHAS)
- **relatesTo ONLY on new alphas**: Do NOT add relatesTo to baseline alpha redeclarations
  - Redeclarations inherit baseline relationships automatically
  - Only new alphas (with contributesTo) should define relatesTo
  - Copy relatesTo array exactly from mapping guide for new alphas
  - Validate every alphaName in relatesTo references a valid alpha (baseline or practice-defined)
- Checklist items are objects {name, description, seq}, NOT strings
- evidencedBy is optional array of WorkProductContribution

**Asset Linking:**

- If mapping guide identifies diagrams for this alpha (e.g., state transition diagrams, architecture diagrams), add `assetNames` property:

  ```json
  {
    "name": "Platform",
    "assetNames": ["platform-architecture-diagram", "platform-states-diagram"]
  }
  ```

- Asset names must match entries in the practice-level `assets` array

#### 3.5 Alpha Instances

If mapping guide defines alpha instances:
```json
"alphaInstances": [
  {
    "name": "Core Platform",
    "description": "Primary production platform",
    "alphaName": "Platform",
    "tags": { ... },
    "narratives": [ ... ]  // Optional
  }
]
```

#### 3.6 Work Products

Add workProducts array:
```json
"workProducts": [
  {
    "name": "Work Product Name",
    "description": "Single sentence",
    "levelsOfDetail": [
      {
        "name": "Level Name",  // NO "Level X:" prefix
        "description": "Single sentence (max 12 words)",
        "seq": 1,
        "checklist": [
          {
            "name": "Characteristic name",
            "description": "One sentence quality criterion",
            "seq": 1
          }
        ],
        "contributesTo": [  // REQUIRED array
          {
            "alphaName": "Alpha",
            "stateName": "State"
          }
        ],
        "tags": { ... },
        "narratives": [ ... ]  // Optional
      }
    ],
    "tags": { ... },
    "narratives": [ ... ]  // Optional
  }
]
```

**CRITICAL:**

- LOD names have NO "Level X:" prefix
- checklist items are objects, NOT strings
- contributesTo is REQUIRED on every LOD

**Asset Linking:**

- If mapping guide identifies templates or examples for this work product, add `assetNames`:

  ```json
  {
    "name": "Architecture",
    "assetNames": ["architecture-template", "architecture-example"]
  }
  ```

- Can also link at LOD level if different assets for different maturity levels

#### 3.7 Work Product Instances

If mapping guide defines work product instances:
```json
"workProductInstances": [
  {
    "name": "Platform Architecture",
    "description": "Core platform technical architecture",
    "workProductName": "Architecture",
    "tags": { ... },
    "narratives": [ ... ]  // Optional
  }
]
```

#### 3.8 Personas

Add personas array:
```json
"personas": [
  {
    "name": "Persona Name",
    "description": "Single sentence",
    "competencies": [  // NOT "requiredCompetencies"
      {
        "competencyName": "EXACT baseline competency name",
        "competencyLevelName": "Level name from baseline"
      }
    ],
    "tags": { ... },
    "narratives": [ ... ]  // Optional
  }
]
```

**CRITICAL:**
- Property name is `competencies` NOT `requiredCompetencies`
- Use exact baseline competency names (case-sensitive)
- Use {competencyName, competencyLevelName} format

#### 3.9 Persona Groups

Add personaGroups array:
```json
"personaGroups": [
  {
    "name": "Team Name",
    "description": "Single sentence",
    "personaNames": ["Persona 1", "Persona 2"],
    "tags": { ... },
    "narratives": [ ... ]  // Optional
  }
]
```

#### 3.10 Activities

Add activities array:
```json
"activities": [
  {
    "name": "Specific Activity Name",  // DIFFERENT from activity space name
    "description": "Single sentence",
    "activitySpaceName": "Baseline Activity Space",
    "focusName": "Value | Solution | Endeavor",
    "contributesTo": [
      {
        "alphaName": "Alpha",
        "stateName": "State"
      }
    ],
    "worksOn": [
      {
        "workProductName": "Work Product",
        "levelOfDetailName": "Level"
      }
    ],
    "requiredCompetencies": [  // Array of strings
      "EXACT baseline competency name 1",
      "EXACT baseline competency name 2"
    ],
    "recommendedCompetencyLevels": [  // Array of objects
      {
        "competencyName": "EXACT baseline competency name",
        "competencyLevelName": "Level name"
      }
    ],
    "involves": [  // Array of PersonaGroup names
      "Team Name 1",
      "Team Name 2"
    ],
    "tags": { ... },
    "narratives": [
      {
        "name": "How to Perform",
        "description": "Technique guidance",
        "narrativeTypeName": "Technique",
        "narrativeContexts": [...],
        "citationNames": [...]
      }
    ]
  }
]
```

**CRITICAL:**

- Activity name MUST differ from activitySpaceName
- BOTH requiredCompetencies (strings) AND recommendedCompetencyLevels (objects) are required
- Use exact baseline competency names
- involves references PersonaGroup names

**Asset Linking:**

- If mapping guide identifies flowcharts or diagrams for this activity, add `assetNames`:

  ```json
  {
    "name": "Design Platform Architecture",
    "assetNames": ["architecture-design-flowchart", "reference-architecture-diagram"]
  }
  ```

#### 3.11 Patterns

Add patterns array:
```json
"patterns": [
  {
    "name": "Pattern Name",
    "description": "Single sentence",
    "narrativeTypeName": "Hero's Journey",  // NOT "narrativeFramework"
    "patternViews": [  // NOT "views"
      {
        "name": "Phase Name",
        "description": "Essence of phase (max 12 words)",
        "seq": 0,  // 0 for prerequisites, 1+ for main phases
        "alphaStates": [  // NOT "alphas"
          {
            "alphaName": "Alpha",
            "stateName": "State"
          }
        ],
        "alphaInstances": [
          {
            "name": "Instance Name",
            "description": "Instance description",
            "alphaName": "Alpha",
            "stateName": "State",
            "evidenceBy": [
              {
                "name": "Work Product Instance",
                "description": "Instance description",
                "workProductName": "Work Product",
                "levelOfDetailName": "Level"
              }
            ]
          }
        ],
        "activities": [  // Array of activity names (strings)
          "Activity Name 1",
          "Activity Name 2"
        ],
        "narrativeContexts": [
          {
            "seq": 1,
            "narrativeElementName": "Element from NarrativeType",
            "context": "1-2 sentences"
          }
        ],
        "tags": { ... }
      }
    ],
    "tags": { ... },
    "narratives": [ ... ]  // Optional
  }
]
```

**CRITICAL:**

- Use `patternViews` NOT `views`
- Use `alphaStates` NOT `alphas`
- PatternView.seq is REQUIRED
- NO `workProducts` property on PatternView (not in schema)
- activities are string names, not objects

**Asset Linking:**

- If mapping guide identifies workflow diagrams or lifecycle visualizations for this pattern, add `assetNames`:

  ```json
  {
    "name": "Platform Adoption Lifecycle",
    "assetNames": ["platform-adoption-workflow-diagram", "maturity-progression-chart"]
  }
  ```

#### 3.12 Practice Element Aliases

If mapping guide defines aliases:
```json
"practiceElementAliases": [
  {
    "practiceElementType": "Alpha",
    "practiceElementName": "Platform",  // CANONICAL name
    "aliasName": "Cloud Infrastructure"  // Source term
  }
]
```

#### 3.13 Method Assembly (For Methods)

If generating Method JSON:

1. Generate complete Practice JSON for EACH practice (following steps 3.1-3.12)
2. Embed each practice in method's `practices` array:
```json
{
  "name": "method-name",
  "description": "Method description",
  "baselinePracticeName": "Platform Adoption Essentials",
  "practices": [
    {
      "name": "practice-1",
      "description": "...",
      "baselinePracticeName": "Platform Adoption Essentials",
      "alphas": [...],
      "workProducts": [...],
      ...
    },
    {
      "name": "practice-2",
      ...
    }
  ],
  "citations": [...],  // Merged from all practices
  "narratives": [...]  // Method-level narratives
}
```

**Parent Practice Mode:** When extending a parent practice:
- Method-level `baselinePracticeName`: Inherited from parent practice
- Method-level `practiceDependencyNames`: Parent practice name(s) from Step 0.25
- Each embedded practice inherits the same `baselinePracticeName` and `practiceDependencyNames`

#### 3.14 Verify Complete Structure

Before proceeding to validation, verify ALL sections from 3.1-3.13 are complete:

**Required Arrays Checklist (For Practice JSON):**

- [ ] 3.1: Practice skeleton (metadata, tags, keywords)
- [ ] 3.2: citations array populated
- [ ] 3.3: narratives array (practice-level)
- [ ] 3.4: alphas array populated
- [ ] 3.5: alphaInstances array (if applicable)
- [ ] 3.6: workProducts array populated
- [ ] 3.7: workProductInstances array (if applicable)
- [ ] 3.8: personas array populated
- [ ] 3.9: **personaGroups array populated** ← Often missed!
- [ ] 3.10: activities array populated
- [ ] 3.11: patterns array populated (REQUIRED: minimum 1 pattern per practice)
- [ ] 3.12: practiceElementAliases array (if applicable)

**For Method JSON, verify EACH practice has:**

- [ ] All arrays from 3.4-3.12 above
- [ ] Method-level: citations, narratives (3.2-3.3)
- [ ] Method-level: practices array with complete Practice objects

**CRITICAL:** Do NOT skip sections even if they seem minor. Empty arrays `[]` are valid if Phase 2 has no content, EXCEPT:

- **patterns array MUST have minimum 1 pattern** for multi-alpha practices
- Verify each practice has at least one pattern with 2+ pattern views

If any section is incomplete, return to that step and complete it before validation.

### Step 4: Validate JSON Syntax

Before proceeding to validation:
```bash
jq empty <practice-name>.json
```

Ensure valid JSON syntax (no trailing commas, proper quotes, balanced braces).

### Step 5: Run Validation Script

Run the comprehensive validator:
```bash
python3 ../../utils/validate-practice-json.py \
  <practice-name>.json \
  ../../deps/platform-adoption-kernel.json \
  ../../deps/language.schema.json
```

**Output:** JSON report with categorized errors

### Step 6: Interpret Validation Results

Read validation output JSON and categorize errors:

**Schema Violations:**
- Property name mismatches → Correct property names
- Type errors → Fix data types
- Missing required fields → Add required properties
- Unevaluated properties → Remove or correct property names

**Baseline Reference Errors:**
- Invalid competency names → Use exact baseline competency names
- Invalid state names → Use valid state from target alpha
- Invalid alpha references → Use exact baseline alpha names
- Floating alphas → Add contributesTo

**Internal Integrity Errors:**
- Broken work product references → Define work product or fix reference
- Broken activity references → Define activity or fix reference
- Broken alpha/state references → Fix references or define elements

### Step 7: Apply Fixes

Based on error category, apply fixes:

**For Schema Violations:**
- Edit JSON directly to correct property names, types, structure
- Add missing required fields
- Remove invalid properties

**For Baseline Reference Errors:**
- Map competency descriptions to exact baseline names
- Correct state names to match alpha definitions
- Add contributesTo to new alphas
- Use exact case-sensitive baseline references

**For Internal Integrity Errors:**
- Create missing work products, activities, or alphas
- Correct symbolic references to match defined elements
- Fix cross-practice references (for methods)

### Step 8: Re-validate Until Clean

After applying fixes:
1. Run validation script again
2. Review new errors (if any)
3. Apply additional fixes
4. Repeat until validation passes with 0 errors

### Step 9: Final Quality Check

Once validation passes, verify:

- [ ] All Phase 2 mappings translated to JSON
- [ ] Verify ALL arrays present: citations, narratives, alphas, alphaInstances, workProducts, workProductInstances, personas, **personaGroups**, activities, patterns, practiceElementAliases
- [ ] No content omissions from Phase 2 mapping guide
- [ ] All narratives present (alpha, activity, practice/method level)
- [ ] All checklists present (alpha states, work product LODs)
- [ ] All citations referenced in citationNames exist
- [ ] All symbolic references are exact matches
- [ ] JSON is well-formatted and readable

## Common Schema Violations to Avoid

### 1. Checklist Format
❌ Wrong: `"checklist": ["Item 1", "Item 2"]`
✅ Right:
```json
"checklist": [
  {
    "name": "Item name",
    "description": "One sentence description",
    "seq": 1
  }
]
```

### 2. Competency Level Reference
❌ Wrong: `{"competencyName": "Engineering", "level": 3}`
✅ Right: `{"competencyName": "Engineering", "competencyLevelName": "Advanced"}`

### 3. Persona Property
❌ Wrong: `"requiredCompetencies": [...]`
✅ Right: `"competencies": [...]`

### 4. Activity Competencies
❌ Wrong: Only `requiredCompetencies` OR only `recommendedCompetencyLevels`
✅ Right: BOTH properties present:
```json
{
  "requiredCompetencies": ["Engineering", "Analysis"],
  "recommendedCompetencyLevels": [
    {"competencyName": "Engineering", "competencyLevelName": "Advanced"}
  ]
}
```

### 5. PatternView Properties
❌ Wrong: `"alphas": [...]` or `"views": [...]` or `"workProducts": [...]`
✅ Right: `"alphaStates": [...]` and `"patternViews": [...]`

### 6. LevelOfDetail.contributesTo
❌ Wrong: Missing contributesTo
✅ Right:
```json
{
  "name": "Level Name",
  "description": "...",
  "seq": 1,
  "contributesTo": [
    {"alphaName": "Alpha", "stateName": "State"}
  ]
}
```

### 7. Floating Alphas
❌ Wrong: New alpha without contributesTo
✅ Right:
```json
{
  "name": "New Alpha",
  "description": "...",
  "focusName": "Solution",
  "contributesTo": "Platform",  // REQUIRED!
  "states": [...]
}
```

### 8. Tags Structure
❌ Wrong: `"tags": ["tag1", "tag2"]` OR `"domainTags": [...], "lifecycleTags": [...]` (flat)
✅ Right:
```json
"tags": {
  "domainTags": [...],
  "lifecycleTags": [...],
  "organizationalTags": [...]
}
```

### 9. Citation Narratives
❌ Wrong: Citations with narratives property
✅ Right: Citations with ONLY metadata (no narratives)

### 10. Work Product LOD Names
❌ Wrong: `"name": "Level 1: Basic"`
✅ Right: `"name": "Basic"`

## Text Cleaning

**CRITICAL:** Remove all markdown syntax and practice metadata from JSON content:

❌ Wrong:
```json
{
  "description": "**Platform** is the _core infrastructure_ (see Section 2.3)"
}
```

✅ Right:
```json
{
  "description": "Platform is the core infrastructure supporting services"
}
```

**Clean:**
- Remove markdown bold `**text**` → `text`
- Remove markdown italic `_text_` → `text`
- Remove section references `(see Section X)`
- Remove practice metadata `(from Phase 1 Section 4.2)`
- Keep ONLY subject matter content

## Quality Standards

### Exact Matching
- All baseline references MUST be exact, case-sensitive string matches
- Competency names: Use exact baseline names (not descriptions)
- Alpha/State names: Exact matches (case-sensitive)
- Activity Space names: Exact matches

### Required Fields
- contributesTo: REQUIRED on all new alphas, all LODs
- Both requiredCompetencies AND recommendedCompetencyLevels on activities
- patternViews.seq: REQUIRED on all pattern views

### Prohibited Patterns
- NO floating alphas (all new alphas have contributesTo)
- NO markdown in JSON strings
- NO practice metadata in descriptions
- NO "Level X:" prefixes on LOD names
- NO narratives on citations
- NO workProducts property on PatternView

## Execution Notes

1. **Read schema.json FIRST** - Understand exact structure before generating
2. **Build incrementally** - Skeleton → Citations → Alphas → Work Products → Personas → Activities → Patterns
3. **Validate continuously** - Check each section as you build
4. **Use validation script** - Programmatic validation catches issues humans miss
5. **Iterate on fixes** - Don't expect perfect first try, iterate until clean
6. **Cross-reference mapping guide** - Ensure all mapped content is in JSON

## Output Location

Write to: `practices/<practice-name>/<practice-name>.json`

For methods: `practices/<method-name>/<method-name>.json`

## Success Criteria

- ✓ Valid JSON syntax (passes jq empty)
- ✓ Schema validation: 0 errors
- ✓ Baseline validation: 0 errors
- ✓ Internal integrity validation: 0 errors
- ✓ All Phase 2 mappings present in JSON
- ✓ No floating alphas
- ✓ All required fields present
- ✓ All competency references use exact baseline names
- ✓ All symbolic references are exact matches
- ✓ No markdown or metadata in JSON strings
- ✓ Narratives and checklists complete

Validated JSON is ready for use in Practice Language consuming systems.
