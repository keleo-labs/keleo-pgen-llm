# Phase 3: Baseline JSON Generation Prompt

## Context

You are conducting **Phase 3: Baseline JSON Generation** of a baseline practice creation workflow. This phase creates machine-readable baseline practice JSON that precisely conforms to the Practice Language JSON Schema.

**Critical Distinction from Extension Practices:**
- Baseline JSON has `"kind": "practiceBaseline"`
- Defines focuses, competencies, activitySpaces, narrativeTypes (not references)
- Alphas have NO `contributesTo` (root-level), but REQUIRED `relatesTo`
- NO activities, workProducts, patterns, personas (those are in extension practices)

## Objective

Generate schema-compliant baseline JSON that:
- Represents the Phase 2 mapping in valid JSON structure
- Conforms to `deps/language.schema.json` schema specification
- Defines foundational elements (focuses, competencies, activitySpaces, narrativeTypes)
- Passes all validation checks (schema, internal integrity)

## Resources Available

You have access to the following resources via the Read tool:

1. **baselines/<name>/02-mapping-guide.md** (Phase 2 output)
   - Complete mapping specification
   - Read this as PRIMARY source for JSON generation

2. **deps/language.schema.json** (JSON Schema)
   - Authoritative schema definition
   - Defines structure, required fields, types
   - READ THIS to understand exact JSON structure

3. **Semantic Guidance** (sub-documents in `references/semantics/`)
   - `references/semantics/practice-elements.md` — PracticeElement foundations, tags, checklists (§5)
   - `references/semantics/alphas.md` — Alpha-state trajectory (§6)
   - `references/semantics/narrative-and-assets.md` — Narratives and assets (§10-11)
   - Read relevant sections for JSON structure guidance

4. **Example Baseline JSONs** (for reference)
   - `deps/platform-adoption-kernel.json`
   - `deps/partner-ecosystem-baseline.json`
   - Read to understand baseline structure patterns

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

## Instructions

### Step 1: Load Resources

**Read these in order:**

1. **Read `baselines/<name>/02-mapping-guide.md`**
   - This is your PRIMARY source for content
   - Review all mapped elements completely

2. **Read `deps/language.schema.json`**
   - Understand exact schema structure
   - Note required vs optional properties
   - Understand property types (string, array, object)
   - Understand symbolic references vs embedded objects

3. **Read relevant semantics sub-documents:**
   - `references/semantics/practice-elements.md` — checklist format, tagging taxonomy (§5)
   - `references/semantics/alphas.md` — alpha structure, baseline isolation rules (§6)
   - `references/semantics/narrative-and-assets.md` — narrative structure, asset declarations (§10-11)

4. **Read example baselines** (optional, for structure reference)
   - `deps/platform-adoption-kernel.json`
   - `deps/partner-ecosystem-baseline.json`

### Step 2: Generate Baseline JSON Skeleton

**Build JSON incrementally in this order to ensure dependencies are met:**

#### 2.1 Baseline Skeleton

```json
{
  "kind": "practiceBaseline",
  "name": "practice-name-from-mapping-guide",
  "description": "Single sentence from mapping guide",
  "schemaVersion": "<from schema $comment, e.g. 1.0.0>",
  "version": "1.0.0",
  "authors": ["From mapping guide"],
  "createdAt": "YYYY-MM-DDTHH:MM:SSZ",
  "updatedAt": "YYYY-MM-DDTHH:MM:SSZ",
  "keywords": ["From mapping guide"]
}
```

**Versioning rules:**
- `schemaVersion`: Read from the schema's `$comment` field (`schemaVersion:X.Y.Z`). Always set this.
- `version`: `"1.0.0"` for new baselines. Use three-part semver.
- If extending another baseline (`baselinePracticeNames`), add `dependencyVersions` with caret range for each parent baseline.

**CRITICAL Pre-Generation Checks:**
- ✓ `"kind": "practiceBaseline"` discriminator property present
- ✓ NO `"baselinePracticeName"` property (unless extending another baseline)
- ✓ Version is `"1.0.0"` for initial baseline (three-part semver)
- ✓ `schemaVersion` matches schema `$comment`
- ✓ Dates in ISO 8601 format with timezone (Z for UTC)

### Step 3: Build Focuses Array

**Transform mapping guide Focuses to JSON structure.**

From mapping guide Focuses section:

```json
{
  "focuses": [
    {
      "name": "Focus name from mapping guide",
      "description": "Single sentence scope from mapping guide"
    }
  ]
}
```

**Quality Checks:**
- ✓ 2-4 focuses (from mapping guide)
- ✓ Each focus has name + description
- ✓ Names match what alphas/activitySpaces will reference

**Add to JSON skeleton.**

### Step 4: Build NarrativeTypes Array

**Transform mapping guide NarrativeTypes to JSON structure.**

From mapping guide NarrativeTypes section:

```json
{
  "narrativeTypes": [
    {
      "kind": "narrativeType",
      "name": "Narrative type name from mapping guide",
      "description": "When to use description from mapping guide",
      "narrativeElements": [
        {
          "name": "Element name from mapping guide",
          "description": "What it represents from mapping guide",
          "howToUse": "Practitioner guidance from mapping guide"
        }
      ]
    }
  ]
}
```

**Quality Checks:**
- ✓ 3-5 narrative types (from mapping guide)
- ✓ Each narrative type has `"kind": "narrativeType"`
- ✓ Each has 3-7 narrative elements
- ✓ Each element has name, description, howToUse

**Add to JSON skeleton.**

### Step 5: Build Competencies Array

**Transform mapping guide Competencies to JSON structure.**

From mapping guide Competencies section:

```json
{
  "competencies": [
    {
      "name": "Competency name from mapping guide",
      "description": "Expertise area description from mapping guide",
      "narratives": [],
      "assetNames": [
        {
          "assetName": "competency-icon-name",
          "type": "icon"
        }
      ],
      "competencyLevels": [
        {
          "name": "Basic",
          "description": "Level 1 description from mapping guide",
          "level": 1,
          "competencyName": "Competency name (same as parent)"
        },
        {
          "name": "Applies",
          "description": "Level 2 description from mapping guide",
          "level": 2,
          "competencyName": "Competency name (same as parent)"
        },
        {
          "name": "Masters",
          "description": "Level 3 description from mapping guide",
          "level": 3,
          "competencyName": "Competency name (same as parent)"
        },
        {
          "name": "Adapts",
          "description": "Level 4 description from mapping guide",
          "level": 4,
          "competencyName": "Competency name (same as parent)"
        },
        {
          "name": "Innovating",
          "description": "Level 5 description from mapping guide",
          "level": 5,
          "competencyName": "Competency name (same as parent)"
        }
      ]
    }
  ]
}
```

**Competency Narratives:** Include when the mapping guide provides a competency narrative (sourced from Phase 1.5 detail about why this competency matters, how it develops, or its domain significance). Do NOT invent narrative content absent from the mapping guide.

**Competency Asset Icons:** Include a font-character icon for each competency. Add corresponding entries to the top-level `assets` array:
```json
{
  "name": "competency-icon-name",
  "type": "font-character",
  "fontFamily": "Font Awesome 6 Free",
  "fontCharacter": "fa-code",
  "fontWeight": "900"
}
```

**Quality Checks:**
- ✓ 5-10 competencies (from mapping guide)
- ✓ Each competency has exactly 5 competencyLevels
- ✓ Level numbers are 1, 2, 3, 4, 5 (sequential)
- ✓ Level names follow standard pattern (Basic, Applies, Masters, Adapts, Innovating)
- ✓ Each level's competencyName matches parent competency name
- ✓ Each competency has an asset icon with corresponding top-level assets entry

**Add to JSON skeleton.**

### Step 6: Build Alphas Array

**Transform mapping guide Alphas to JSON structure.**

**CRITICAL BASELINE ALPHA RULES:**
- NO `contributesTo` property (baseline alphas are root-level)
- REQUIRED `relatesTo` array (show inter-alpha relationships)
- States have `checklists` arrays (can be empty `[]`)
- Minimum 5 states per alpha (not fewer than 5, not more than 7)

From mapping guide Alphas section:

```json
{
  "alphas": [
    {
      "name": "Alpha name from mapping guide",
      "description": "Description from mapping guide",
      "focusName": "Focus name (must exist in Step 3 focuses array)",
      "relatesTo": [
        {
          "relationship": "produces",
          "alphaName": "Target alpha name",
          "direction": "outgoing",
          "relationshipKind": "production",
          "description": "Why this relationship exists"
        }
      ],
      "states": [
        {
          "name": "State name from mapping guide",
          "description": "State description from mapping guide",
          "background": {  // Optional — use sparingly in baselines; practice layer adds detailed Gherkin
            // NEVER reference the previous state of the SAME alpha — sequential progression is implicit in seq ordering
            "given": ["Precondition for this state"],
            "alphaStates": [
              { "alphaName": "Other Alpha", "stateName": "State" }  // Cross-alpha dependencies ONLY
            ]
          },
          "checklists": [
            "Actionable task 1 from mapping guide (imperative verb phrase)",
            "Actionable task 2 from mapping guide (imperative verb phrase)",
            "Actionable task 3 from mapping guide (imperative verb phrase)"
          ]
        }
      ],
      "narratives": [
        {
          "name": "Subject-matter focused name (NOT 'Alpha Name Narrative')",
          "description": "What this narrative covers (NOT 'The X narrative for the Y alpha')",
          "narrativeTypeName": "Narrative type name from Step 4",
          "narrativeContexts": [
            {
              "seq": 1,
              "narrativeElementName": "Element name from narrative type",
              "context": "2-3 sentences of direct content"
            }
          ],
          "citationNames": ["Citation Name 1", "Citation Name 2"]
        }
      ]
    }
  ]
}
```

**relatesTo Fields (AlphaRelationship):**

| Field | Required | Description |
|-------|----------|-------------|
| `relationship` | Yes | Verb phrase: "produces", "governed by", "uses", "enables", etc. |
| `alphaName` | Yes | Target alpha name (must exist in this baseline's alphas array) |
| `direction` | Yes | `outgoing` (this alpha acts on target), `incoming` (target acts on this), or `mutual` (symmetric) |
| `relationshipKind` | No | Machine-traversable classification: `dependency`, `production`, `guidance`, `information-flow`, `enabling`, `impact`, `consumption`, `mutual` |
| `description` | No | Human-readable explanation of why this relationship exists |

**Direction mapping for common relationship verbs:**
- `outgoing`: "produces", "enables", "constrains", "depends on", "consumes", "hosts", "uses"
- `incoming`: "governed by", "built by", "validated by", "supported by"
- `mutual`: "correlates with", "co-evolves with" (use sparingly)

**Quality Checks:**
- ✓ 8-15 alphas (from mapping guide)
- ✓ NO `contributesTo` property on any alpha
- ✓ ALL alphas have `relatesTo` array (not empty)
- ✓ Every `relatesTo` entry has `direction` field
- ✓ Each alpha has 5-7 states
- ✓ Each state has 3-5 checklist items (imperative verb phrases, positive/additive — actions to perform, not absences); each checklist text adds actionable specificity beyond what the state description already conveys
- ✓ All `focusName` references exist in Step 3 focuses
- ✓ All `relatesTo.alphaName` references exist in alphas array

**Add to JSON skeleton.**

### Step 7: Build ActivitySpaces Array

**Transform mapping guide ActivitySpaces to JSON structure.**

From mapping guide ActivitySpaces section:

```json
{
  "activitySpaces": [
    {
      "name": "ActivitySpace name from mapping guide",
      "description": "Execution boundary description from mapping guide",
      "focusName": "Focus name (must exist in Step 3 focuses array)",
      "background": {  // Optional — shared prerequisites for this activity space; use sparingly in baselines
        "given": ["Precondition before activities in this space begin"],
        "alphaStates": [
          { "alphaName": "Alpha", "stateName": "State" }
        ]
      },
      "contributesTo": [
        {
          "alphaName": "Alpha name (must exist in Step 6 alphas array)",
          "stateName": "State name (must exist in that alpha's states)"
        }
      ],
      "requiredCompetencies": [
        "Competency name 1 (must exist in Step 5 competencies array)",
        "Competency name 2"
      ],
      "ledBy": "Persona Name",  // Optional — single Persona.name accountable for leading this activity space
      "narratives": [...]  // Optional — same structure as alpha narratives
    }
  ]
}
```

**Quality Checks:**
- ✓ 6-12 activity spaces (from mapping guide)
- ✓ All `focusName` references exist in Step 3 focuses
- ✓ All `contributesTo.alphaName` references exist in Step 6 alphas
- ✓ All `contributesTo.stateName` references exist in the alpha's states
- ✓ All `requiredCompetencies` references exist in Step 5 competencies
- ✓ Coverage: Every alpha state from Step 6 has ≥1 activity space contributing to it

**Add to JSON skeleton.**

### Step 7.5: Build Outcomes Array

Build the `outcomes` array from the baseline mapping guide. Baseline outcomes are high-level value propositions — simpler than extension practice outcomes.

```json
"outcomes": [
  {
    "name": "Outcome Name",
    "description": "Framework-level value proposition",
    "measureDescription": "How value delivery is tracked at the framework level"
  }
]
```

Baseline outcomes serve as templates. Extension practices specialize them with specific `metricContributions` and `objectiveContributions`. Do NOT include contribution arrays on baseline outcomes.

**Quality Checks:**
- ✓ 1-3 outcomes (from mapping guide)
- ✓ Each outcome has `name`, `description`, and `measureDescription`
- ✓ No `metricContributions` or `objectiveContributions` (reserved for extension practices)

**Add to JSON skeleton.**

### Step 8: Build Baseline-Level Narratives

**Add ONLY baseline-level narratives to the top-level `narratives[]` array.**

Element-specific narratives (for alphas, activitySpaces, etc.) should already be embedded on those elements' own `narratives[]` property in Steps 6-7. The top-level `narratives[]` array is reserved for narratives that describe the baseline practice itself.

From mapping guide Narratives section (baseline-level entries only):

```json
{
  "narratives": [
    {
      "name": "Subject-matter title for baseline narrative",
      "description": "What the baseline narrative covers",
      "narrativeTypeName": "Narrative type from Step 4",
      "narrativeContexts": [
        {
          "seq": 1,
          "narrativeElementName": "Element from narrative type",
          "context": "2-3 sentences of direct content (NO self-references)"
        }
      ],
      "citationNames": ["Citation Name 1"]
    }
  ]
}
```

**Narrative Placement Rules:**
- **Baseline-level narratives** (describing the practice as a whole) go in the top-level `narratives[]` array (this step)
- **Alpha narratives** go in each alpha's `narratives[]` property (Step 6)
- **ActivitySpace narratives** go in each activitySpace's `narratives[]` property (Step 7)

**Quality Checks:**
- ✓ Baseline-level narrative present (REQUIRED)
- ✓ Narrative names describe subject matter (NOT "X Narrative" or "The Y narrative for Z")
- ✓ Narrative descriptions explain content (NOT "The STAR/Three-Act/ABT narrative for...")
- ✓ All narratives have `citationNames` referencing relevant citations from Step 9
- ✓ All `narrativeTypeName` references exist in Step 4 narrativeTypes
- ✓ All `narrativeElementName` references exist in the narrative type's narrativeElements
- ✓ narrativeContexts provide substantive content (not generic placeholders)

**Add to JSON skeleton.**

### Step 9: Build Citations Array

**Transform mapping guide Citations to JSON structure.**

Citations use the "Citation Standard" narrative type with Author/Date/Title/Source elements:

```json
{
  "citations": [
    {
      "targetElementName": "Element name (baseline | alpha name | etc.)",
      "narrativeTypeName": "Citation Standard",
      "narrativeContexts": [
        {
          "narrativeElementName": "Author",
          "contextText": "Full author name(s)"
        },
        {
          "narrativeElementName": "Date",
          "contextText": "Publication date (YYYY-MM-DD or YYYY)"
        },
        {
          "narrativeElementName": "Title",
          "contextText": "Full title"
        },
        {
          "narrativeElementName": "Source",
          "contextText": "Publisher, journal, URL, or DOI"
        }
      ]
    }
  ]
}
```

**Quality Checks:**
- ✓ All citations use `"narrativeTypeName": "Citation Standard"`
- ✓ Each citation has Author, Date, Title, Source elements
- ✓ The citation `name` field MUST be the **title of the work** (e.g., "Team Topologies", "Accelerate"), NOT an author-date shorthand like "Skelton and Pais (2019)" or "Forsgren et al. (2018)". Authors have their own element.
- ✓ Dates in consistent format (YYYY-MM-DD or YYYY)
- ✓ Sources include URLs, DOIs, or ISBN when available
- ✓ **URL enrichment:** Every citation SHOULD include a retrieval URL — carry forward URLs from the mapping guide and analysis report, including internal, intranet, and Google Docs/Sheets/Slides links. Use user-provided URLs, official websites, DOI references (`https://doi.org/10.xxxx/xxxxx`) for academic works, or publisher pages. Only omit when no stable link exists. Internal/intranet URLs are valid.

**Add to JSON skeleton (or merge with narratives array if preferred).**

### Step 9.5: Build Acknowledgements Array (Optional)

If the source methodology credits specific contributors, research groups, or supporting organizations, add an `acknowledgements` array. Acknowledgements attribute human contributions — distinct from citations which reference published works.

```json
{
  "acknowledgements": [
    {
      "name": "Person or Institution Name",
      "description": "Brief description of their contribution",
      "url": "https://optional-profile-or-contact-url"
    }
  ]
}
```

**Add to JSON skeleton.**

### Step 10: Build Assets Array

**Transform mapping guide Assets to JSON structure.**

From mapping guide Assets section:

**For file-based assets:**

```json
{
  "assets": [
    {
      "name": "asset-name-from-mapping-guide",
      "type": "icon | diagram | template | image",
      "path": "assets/icons/name.svg | assets/diagrams/name.svg | assets/templates/name.pdf",
      "mimeType": "image/svg+xml | image/png | application/pdf"
    }
  ]
}
```

**For font character icons:**

```json
{
  "assets": [
    {
      "name": "asset-name-from-mapping-guide",
      "type": "font-character",
      "fontFamily": "Font Awesome 6 Free",
      "fontCharacter": "fa-cubes",
      "fontWeight": "900"
    }
  ]
}
```

**AssetReference in Elements:**

When an element (alpha, activitySpace, etc.) references an asset:

```json
{
  "alphas": [
    {
      "name": "Platform",
      "assetNames": [
        {
          "assetName": "platform-icon",
          "type": "icon"
        },
        {
          "assetName": "platform-states-diagram",
          "type": "diagram"
        }
      ]
    }
  ]
}
```

**AssetReference Types:**
- `"icon"`: UI markers, visual identity
- `"illustrative"`: Documentation diagrams
- `"template"`: Reusable documents
- `"diagram"`: Technical architecture, state progressions

**Quality Checks:**
- ✓ All asset names in assetNames references exist in assets array
- ✓ AssetReference type matches semantic use (icon, diagram, template)
- ✓ Font character icons for simple icons (scalable, no files)
- ✓ SVG for diagrams (scalable, editable)

**Add to JSON skeleton.**

### Step 10.5: Build PatternGroups Array

**Transform mapping guide PatternGroups to JSON structure.**

Baselines define canonical pattern group categories with empty entries arrays. Extension practices adopt these groups and populate them with their patterns.

From mapping guide PatternGroups section:

```json
{
  "patternGroups": [
    {
      "name": "Core Lifecycles",
      "description": "Primary lifecycle patterns from each practice — the main journey through each value stream",
      "entries": [],
      "seq": 0
    },
    {
      "name": "Maturity Progressions",
      "description": "Patterns tracking growth along a maturity axis within each practice area",
      "entries": [],
      "seq": 1
    }
  ]
}
```

**Quality Checks:**
- ✓ 3-5 groups (from mapping guide)
- ✓ Each group has name, description, and `entries: []`
- ✓ Entries arrays are empty (baselines define categories, extensions populate)
- ✓ Optional `seq` for group ordering
- ✓ Optional narratives on groups (same structure as alpha narratives)

**Add to JSON skeleton.**

### Step 11: Build PracticeElementAliases Array (if applicable)

**If this baseline adapts a parent baseline's terminology for a domain**, add aliases that map canonical element names to domain-appropriate terms. Aliases are presentation-layer substitutions only — all structural references in JSON must use canonical names.

```json
{
  "practiceElementAliases": [
    {
      "practiceElementType": "Alpha",
      "practiceElementName": "Canonical name from baseline",
      "aliasName": "Domain-specific term"
    }
  ]
}
```

**Rules:**
- ✓ Every `practiceElementName` must match an existing element in this baseline or parent baseline
- ✓ `practiceElementType` must match the element's type (Alpha, ActivitySpace, Focus, Competency, NarrativeType)
- ✓ No duplicate aliases (same practiceElementType + practiceElementName)
- ✓ `aliasName` must NEVER appear in any structural reference within the JSON
- ✓ Aliases are optional — only include if the baseline adapts terminology from a parent

**Add to JSON skeleton.**

### Step 12: Final Validation Checks

Before writing the final JSON file, validate:

**Schema Compliance:**
- ✓ `"kind": "practiceBaseline"` discriminator present
- ✓ All required properties present (name, description, version, focuses, narrativeTypes, alphas, activitySpaces, competencies)
- ✓ `outcomes` array present (1-3 outcomes; warn if empty)
- ✓ NO `baselinePracticeName` (unless extending another baseline)
- ✓ Property types correct (strings, arrays, objects per schema)

**Baseline-Specific Rules:**
- ✓ Alphas have NO `contributesTo` property
- ✓ Alphas ALL have `relatesTo` arrays (not empty)
- ✓ Every `relatesTo` entry has required `direction` field
- ✓ Alphas have 5-7 states each
- ✓ ActivitySpaces defined (not referenced)
- ✓ Competencies defined with 5 levels
- ✓ NarrativeTypes defined
- ✓ Focuses defined

**Internal Cross-Reference Integrity:**
- ✓ All `focusName` references exist in focuses array
- ✓ All `relatesTo.alphaName` references exist in alphas array
- ✓ All `contributesTo.alphaName` references exist in alphas array
- ✓ All `contributesTo.stateName` references exist in the alpha's states
- ✓ All `requiredCompetencies` references exist in competencies array
- ✓ All `narrativeTypeName` references exist in narrativeTypes array
- ✓ All `narrativeElementName` references exist in the narrative type's elements
- ✓ All `assetName` references exist in assets array

**Alias Validation (if applicable):**
- ✓ All alias `practiceElementName` values match existing elements
- ✓ All alias `practiceElementType` values match element types
- ✓ No duplicate aliases
- ✓ No `aliasName` used in structural references

**Coverage Validation:**
- ✓ Every alpha state has ≥1 activity space contributing to it
- ✓ Baseline-level narrative present

### Step 13: Write Final JSON

**Write to: `baselines/<name>/<name>.json`**

**Final JSON Structure:**

```json
{
  "kind": "practiceBaseline",
  "name": "...",
  "description": "...",
  "schemaVersion": "...",
  "version": "1.0.0",
  "authors": [...],
  "createdAt": "YYYY-MM-DDTHH:MM:SSZ",
  "updatedAt": "YYYY-MM-DDTHH:MM:SSZ",
  "keywords": [...],
  "focuses": [...],
  "narrativeTypes": [...],
  "alphas": [...],
  "activitySpaces": [...],
  "competencies": [...],
  "outcomes": [...],
  "narratives": [...],
  "citations": [...],
  "patternGroups": [...],
  "assets": [...]
}
```

**JSON Formatting:**
- Use 2-space indentation
- Use UTF-8 encoding
- Ensure valid JSON syntax (commas, brackets, quotes)
- No trailing commas
- Escape special characters in strings

### Step 14: Validate with Script

**After writing JSON, validate:**

```bash
python3 utils/validate-baseline-json.py \
  baselines/<name>/<name>.json \
  deps/language.schema.json
```

**If extending another baseline:**

```bash
python3 utils/validate-baseline-json.py \
  baselines/<name>/<name>.json \
  <parent-baseline.json> \
  deps/language.schema.json
```

**Expected Output:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

**If errors:**
1. Read error messages (category, path, issue, suggestion)
2. Fix issues in JSON
3. Re-validate until `"valid": true`

## Quality Standards

**Exactness**: All names, descriptions, structures must match mapping guide exactly (no paraphrasing).

**Completeness**: All elements from mapping guide must be present in JSON.

**Validity**: JSON must be syntactically valid and schema-compliant.

**Integrity**: All cross-references must resolve to valid elements.

## Common Pitfalls to Avoid

❌ **Missing discriminator**: Forgetting `"kind": "practiceBaseline"`
❌ **Adding contributesTo to alphas**: Baseline alphas are root-level
❌ **Empty relatesTo**: All alphas need inter-alpha relationships
❌ **Missing focuses definition**: Focuses must be defined in baseline, not referenced
❌ **Missing competencies definition**: Competencies must be defined with 5 levels
❌ **Missing narrativeTypes definition**: NarrativeTypes must be defined
❌ **Wrong competency level count**: All competencies need exactly 5 levels
❌ **Invalid cross-references**: focusName, alphaName, stateName, competencyName must all resolve
❌ **Trailing commas**: JSON doesn't allow trailing commas in arrays/objects
❌ **Missing state coverage**: Every alpha state needs ≥1 activity space

## Success Criteria

✅ Valid JSON syntax (no parse errors)
✅ `"kind": "practiceBaseline"` present
✅ Focuses, competencies, activitySpaces, narrativeTypes all defined
✅ Alphas have NO contributesTo, all have relatesTo
✅ All cross-references valid
✅ Validation script reports `"valid": true`
✅ Output file: `baselines/<name>/<name>.json` (schema-compliant)
