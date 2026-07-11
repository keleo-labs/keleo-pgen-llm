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

3. **references/semantics.md** (Semantic Guidance)
   - Section 3: Structural Foundations (PracticeElement, tags, checklists)
   - Section 4: Alpha-State Trajectory
   - Section 7: Narratives
   - READ relevant sections for JSON structure guidance

4. **Example Baseline JSONs** (for reference)
   - `deps/platform-adoption-kernel.json`
   - `deps/partner-ecosystem-baseline.json`
   - Read to understand baseline structure patterns

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

3. **Read `references/semantics.md` (relevant sections)**
   - Focus on JSON structure examples
   - Note schema-specific rules (e.g., checklist format, competency structure)

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
  "version": "1.0",
  "authors": ["From mapping guide"],
  "createdAt": "YYYY-MM-DDTHH:MM:SSZ",
  "updatedAt": "YYYY-MM-DDTHH:MM:SSZ",
  "keywords": ["From mapping guide"]
}
```

**CRITICAL Pre-Generation Checks:**
- ✓ `"kind": "practiceBaseline"` discriminator property present
- ✓ NO `"baselinePracticeName"` property (unless extending another baseline)
- ✓ Version is "1.0" for initial baseline
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

**Quality Checks:**
- ✓ 5-10 competencies (from mapping guide)
- ✓ Each competency has exactly 5 competencyLevels
- ✓ Level numbers are 1, 2, 3, 4, 5 (sequential)
- ✓ Level names follow standard pattern (Basic, Applies, Masters, Adapts, Innovating)
- ✓ Each level's competencyName matches parent competency name

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
          "alphaName": "Target alpha name",
          "relationship": "produces | governed by | uses",
          "rationale": "Why this relationship exists"
        }
      ],
      "states": [
        {
          "name": "State name from mapping guide",
          "description": "State description from mapping guide",
          "checklists": [
            "Checklist item 1 from mapping guide criteria",
            "Checklist item 2 from mapping guide criteria",
            "Checklist item 3 from mapping guide criteria"
          ]
        }
      ]
    }
  ]
}
```

**relatesTo Relationship Types:**
- `"produces"`: This alpha enables/produces the target alpha
- `"governed by"`: This alpha is constrained/governed by the target alpha
- `"uses"`: This alpha uses/depends on the target alpha

**Quality Checks:**
- ✓ 8-15 alphas (from mapping guide)
- ✓ NO `contributesTo` property on any alpha
- ✓ ALL alphas have `relatesTo` array (not empty)
- ✓ Each alpha has 5-7 states
- ✓ Each state has 3-5 checklist items
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
      "contributesTo": [
        {
          "alphaName": "Alpha name (must exist in Step 6 alphas array)",
          "stateName": "State name (must exist in that alpha's states)"
        }
      ],
      "requiredCompetencies": [
        "Competency name 1 (must exist in Step 5 competencies array)",
        "Competency name 2"
      ]
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

### Step 8: Build Narratives Array

**Transform mapping guide Narratives to JSON structure.**

From mapping guide Narratives section:

```json
{
  "narratives": [
    {
      "targetElementName": "Element name (baseline | alpha name | activitySpace name | competency name)",
      "narrativeTypeName": "Narrative type name (must exist in Step 4 narrativeTypes)",
      "narrativeContexts": [
        {
          "narrativeElementName": "Element name from narrative type",
          "contextText": "2-3 sentences mapping target to this element"
        }
      ]
    }
  ]
}
```

**targetElementName Values:**
- Baseline itself: Use baseline practice name (e.g., "Partner Ecosystem Essentials")
- Alpha: Use alpha name (e.g., "Partner Value")
- AlphaState: Use `"AlphaName.StateName"` format (e.g., "Partner Value.Optimized")
- ActivitySpace: Use activity space name (e.g., "Establish Value Proposition")
- Competency: Use competency name (e.g., "Partnership Management")

**Quality Checks:**
- ✓ Baseline-level narrative present (REQUIRED)
- ✓ All `narrativeTypeName` references exist in Step 4 narrativeTypes
- ✓ All `narrativeElementName` references exist in the narrative type's narrativeElements
- ✓ All `targetElementName` values reference valid elements (baseline, alphas, activitySpaces, competencies)
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
- ✓ Dates in consistent format (YYYY-MM-DD or YYYY)
- ✓ Sources include URLs, DOIs, or ISBN when available

**Add to JSON skeleton (or merge with narratives array if preferred).**

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

### Step 11: Final Validation Checks

Before writing the final JSON file, validate:

**Schema Compliance:**
- ✓ `"kind": "practiceBaseline"` discriminator present
- ✓ All required properties present (name, description, version, focuses, narrativeTypes, alphas, activitySpaces, competencies)
- ✓ NO `baselinePracticeName` (unless extending another baseline)
- ✓ Property types correct (strings, arrays, objects per schema)

**Baseline-Specific Rules:**
- ✓ Alphas have NO `contributesTo` property
- ✓ Alphas ALL have `relatesTo` arrays (not empty)
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

**Coverage Validation:**
- ✓ Every alpha state has ≥1 activity space contributing to it
- ✓ Baseline-level narrative present

### Step 12: Write Final JSON

**Write to: `baselines/<name>/<name>.json`**

**Final JSON Structure:**

```json
{
  "kind": "practiceBaseline",
  "name": "...",
  "description": "...",
  "version": "1.0",
  "authors": [...],
  "createdAt": "YYYY-MM-DDTHH:MM:SSZ",
  "updatedAt": "YYYY-MM-DDTHH:MM:SSZ",
  "keywords": [...],
  "focuses": [...],
  "narrativeTypes": [...],
  "alphas": [...],
  "activitySpaces": [...],
  "competencies": [...],
  "narratives": [...],
  "citations": [...],
  "assets": [...]
}
```

**JSON Formatting:**
- Use 2-space indentation
- Use UTF-8 encoding
- Ensure valid JSON syntax (commas, brackets, quotes)
- No trailing commas
- Escape special characters in strings

### Step 13: Validate with Script

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
