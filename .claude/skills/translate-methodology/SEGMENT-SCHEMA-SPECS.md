# Phase 2 Segment Generation - Schema-Compliant Specifications

**CRITICAL:** All segments MUST comply with `/deps/language.schema.json`

Reference documents:
- Schema: `/deps/language.schema.json`
- Semantic guidance: `/references/semantics.md`
- Violations found: `/prompts/reference/schema-violations-found.md`
- Generation rules: `/prompts/segment-generation-rules.md`

---

## Segment 01: Practice Skeleton

**Source:** `01-practice-details.md`
**Output:** `json-segments/practice-N/01-practice-skeleton.json`
**Size:** ~2KB
**Format:** JSON object (NOT array)

**Schema-compliant structure:**
```json
{
  "name": "Practice Name",
  "description": "Single sentence description",
  "baselinePracticeName": "Platform Adoption Essentials",
  "domainTags": ["tag1", "tag2"],
  "lifecycleTags": ["tag1", "tag2"],
  "organizationalTags": ["tag1", "tag2"],
  "authors": ["Author Name"],
  "createdAt": "2026-05-21",
  "updatedAt": "2026-05-21",
  "version": "1.0",
  "keywords": ["keyword1", "keyword2"]
}
```

---

## Segment 02: Citations

**Source:** `02-citations.md`
**Output:** `json-segments/practice-N/02-citations.json`
**Size:** ~3KB
**Format:** JSON array of Citation objects

**Schema-compliant structure:**
```json
[
  {
    "name": "Citation Identifier",
    "description": "Brief description of source",
    "authors": ["Author Name"],
    "date": "2025",
    "source": "Publisher or URL",
    "url": "https://..."
  }
]
```

---

## Segment 03: Alphas

**Source:** `03-alphas.md`
**Output:** `json-segments/practice-N/03-alphas.json`
**Size:** ~20-40KB (largest segment)
**Format:** JSON array of Alpha objects

**CRITICAL SCHEMA REQUIREMENTS:**

1. **Checklist items MUST be objects:**
   ```json
   "checklist": [
     {
       "name": "Checklist Item Name",
       "description": "Specific verifiable criterion",
       "seq": 1
     }
   ]
   ```
   **NOT strings!**

2. **New alphas MUST have contributesTo:**
   ```json
   {
     "name": "AI Model Catalog",
     "contributesTo": ["Platform"]
   }
   ```

3. **Narrative citations MUST be extracted:**
   - Look for `**Citations Referenced:**` sections after narrative content
   - Parse comma-separated citation names
   - Add `citationNames` array to Narrative objects
   - Citation names must EXACTLY match Citation.name values from 02-citations.json

**Full schema-compliant structure:**
```json
[
  {
    "name": "Alpha Name",
    "description": "Clean description without markdown",
    "focusName": "Value" | "Solution" | "Endeavor",
    "contributesTo": ["Parent Alpha"],  // ONLY for new alphas
    "states": [
      {
        "name": "State Name",
        "description": "State description",
        "seq": 1,
        "checklist": [
          {
            "name": "Criterion Name",
            "description": "Specific verifiable criterion",
            "seq": 1
          }
        ]
      }
    ],
    "narratives": [
      {
        "narrativeTypeName": "Context and Rationale",
        "narrativeContexts": [
          {
            "narrativeElementName": "Context",
            "context": "Narrative text",
            "seq": 1
          }
        ],
        "citationNames": ["Citation Title 1", "Citation Title 2"]  // OPTIONAL but include when present
      }
    ]
  }
]
```

**Narrative Citation Extraction Pattern:**

From 03-alphas.md:
```markdown
**Narrative 1: Team Structure and Organizational Design**

**Narrative Type:** Essay Narrative

**Narrative Contexts:**
[narrative content paragraphs]

**Citations Referenced:** Team topologies: Organizing business and technology teams for fast flow, Conway's Law paper
```

Extracts to:
```json
{
  "name": "Team Structure and Organizational Design",
  "narrativeTypeName": "Essay Narrative",
  "narrativeContexts": [...],
  "citationNames": [
    "Team topologies: Organizing business and technology teams for fast flow",
    "Conway's Law paper"
  ]
}
```

---

## Segment 04: Work Products

**Source:** `04-workproducts.md`
**Output:** `json-segments/practice-N/04-workproducts.json`
**Size:** ~15-25KB
**Format:** JSON array of WorkProduct objects

**CRITICAL SCHEMA REQUIREMENTS:**

1. **Checklist items MUST be objects** (same as alphas)

2. **LevelOfDetail.contributesTo is REQUIRED:**
   ```json
   "contributesTo": [
     {
       "alphaName": "Platform",
       "stateName": "Architecture Selected"
     }
   ]
   ```

3. **Narrative citations MUST be extracted:**
   - Work products MAY have narratives (Context, Rationale, Usage guidance)
   - Extract `citationNames` from `**Citations Referenced:**` sections
   - Same extraction pattern as alphas

**Full schema-compliant structure:**
```json
[
  {
    "name": "Work Product Name",
    "description": "Description without markdown",
    "levelsOfDetail": [
      {
        "name": "Level Name",
        "description": "Level description",
        "seq": 1,
        "checklist": [
          {
            "name": "Characteristic Name",
            "description": "Specific characteristic",
            "seq": 1
          }
        ],
        "contributesTo": [
          {
            "alphaName": "Platform",
            "stateName": "Ready"
          }
        ]
      }
    ]
  }
]
```

---

## Segment 05a: Activities

**Source:** `05-activities-roles.md` (Activities section)
**Output:** `json-segments/practice-N/05-activities.json`
**Size:** ~15-20KB
**Format:** JSON array of Activity objects

**CRITICAL SCHEMA REQUIREMENTS:**

1. **CompetencyLevelReference uses competencyLevelName:**
   ```json
   {
     "competencyName": "Engineering",
     "competencyLevelName": "Expert"  // NOT "level": 5
   }
   ```

   Competency level names:
   - Level 1: "Awareness"
   - Level 2: "Novice"
   - Level 3: "Proficient"
   - Level 4: "Advanced"
   - Level 5: "Expert"

2. **Activities need BOTH required and recommended:**
   ```json
   "requiredCompetencies": ["Engineering", "Site Reliability"],
   "recommendedCompetencyLevels": [
     {"competencyName": "Engineering", "competencyLevelName": "Expert"}
   ]
   ```

3. **Technique narrative citations MUST be extracted:**
   - All activities MUST have technique narratives from "How to Perform" sections
   - Extract `citationNames` from `**Citations Referenced:**` sections after narrative content
   - Same extraction pattern as alphas
   - **CRITICAL:** Activities without narratives indicate translation FAILURE

**Full schema-compliant structure:**
```json
[
  {
    "name": "Activity Name",
    "description": "Description without markdown",
    "focusName": "Value" | "Solution" | "Endeavor",
    "activitySpaceName": "Activity Space Name",
    "contributesTo": [
      {"alphaName": "Platform", "stateName": "Ready"}
    ],
    "worksOn": [
      {"workProductName": "Architecture Doc", "levelOfDetailName": "Detailed"}
    ],
    "requiredCompetencies": ["Engineering", "Site Reliability"],
    "recommendedCompetencyLevels": [
      {"competencyName": "Engineering", "competencyLevelName": "Expert"},
      {"competencyName": "Site Reliability", "competencyLevelName": "Proficient"}
    ],
    "involves": ["Platform Engineering"],
    "techniqueNarratives": [
      {
        "narrativeTypeName": "How-To Guide",
        "narrativeContexts": [
          {
            "narrativeElementName": "Step 1",
            "context": "Detailed step description",
            "seq": 1
          }
        ],
        "citationNames": ["Citation Title"]  // OPTIONAL but include when present
      }
    ]
  }
]
```

---

## Segment 05b: Personas

**Source:** `05-activities-roles.md` (Personas section)
**Output:** `json-segments/practice-N/05-personas.json`
**Size:** ~3-5KB
**Format:** JSON array of Persona objects

**CRITICAL SCHEMA REQUIREMENTS:**

1. **Property name is `competencies` (NOT `requiredCompetencies`):**
   ```json
   {
     "name": "Platform Engineer",
     "competencies": [...]  // NOT requiredCompetencies
   }
   ```

2. **Use CompetencyLevelReference format:**
   ```json
   "competencies": [
     {"competencyName": "Engineering", "competencyLevelName": "Expert"}
   ]
   ```

**Full schema-compliant structure:**
```json
[
  {
    "name": "Persona Name",
    "description": "Role description",
    "competencies": [
      {"competencyName": "Engineering", "competencyLevelName": "Expert"},
      {"competencyName": "Site Reliability", "competencyLevelName": "Proficient"}
    ]
  }
]
```

---

## Segment 05c: Teams

**Source:** `05-activities-roles.md` (Persona Groups section)
**Output:** `json-segments/practice-N/05-teams.json`
**Size:** ~2KB
**Format:** JSON array of PersonaGroup objects

**Schema-compliant structure:**
```json
[
  {
    "name": "Team Name",
    "description": "Team description",
    "personas": ["Persona Name 1", "Persona Name 2"]
  }
]
```

---

## Segment 06: Patterns

**Source:** `06-patterns.md`
**Output:** `json-segments/practice-N/06-patterns.json`
**Size:** ~10-20KB
**Format:** JSON array of Pattern objects

**CRITICAL SCHEMA REQUIREMENTS:**

1. **PatternView uses `alphaStates` (NOT `alphas`):**
   ```json
   "alphaStates": [
     {"alphaName": "Platform", "stateName": "Ready"}
   ]
   ```

2. **PatternView.seq is REQUIRED**

3. **NO `workProducts` property in PatternView** (not in schema)

4. **Activities are string names** (not objects)

5. **Pattern-level narrative citations MUST be extracted:**
   - Patterns typically have one pattern-level narrative
   - Extract `citationNames` from `**Citations Referenced:**` sections
   - Same extraction pattern as alphas

**Full schema-compliant structure:**
```json
[
  {
    "name": "Pattern Name",
    "description": "Pattern description",
    "narrativeTypeName": "The STAR Format",
    "narratives": [
      {
        "name": "Pattern-Level Narrative Title",
        "narrativeTypeName": "The STAR Format",
        "narrativeContexts": [
          {
            "narrativeElementName": "Situation",
            "context": "Pattern-level narrative text",
            "seq": 1
          }
        ],
        "citationNames": ["Citation Title"]  // OPTIONAL but include when present
      }
    ],
    "patternViews": [
      {
        "name": "View Name",
        "description": "View description",
        "seq": 1,
        "alphaStates": [
          {"alphaName": "Platform", "stateName": "Ready"}
        ],
        "activities": ["Activity Name 1", "Activity Name 2"],
        "narrativeContexts": [
          {
            "narrativeElementName": "Situation",
            "context": "Narrative text",
            "seq": 1
          }
        ]
      }
    ]
  }
]
```

---

## Segment 07: Aliases

**Source:** `07-aliases.md`
**Output:** `json-segments/practice-N/07-aliases.json`
**Size:** ~2KB
**Format:** JSON array of PracticeElementAlias objects (or empty array if no aliases)

**Schema-compliant structure:**
```json
[
  {
    "practiceElementType": "Alpha" | "WorkProduct" | "Activity" | "Pattern",
    "practiceElementName": "Canonical Name",
    "aliasName": "Alternative Name"
  }
]
```

---

## Validation Checklist (ALL Segments)

Before saving ANY segment, verify:

- [ ] JSON syntax valid: `jq empty <file>`
- [ ] All checklist items are objects with {name, description, seq}
- [ ] All CompetencyLevelReference use {competencyName, competencyLevelName}
- [ ] Persona property is `competencies` not `requiredCompetencies`
- [ ] Activities have BOTH `requiredCompetencies` AND `recommendedCompetencyLevels`
- [ ] PatternView uses `alphaStates` not `alphas`
- [ ] PatternView has `seq` field
- [ ] PatternView does NOT have `workProducts` property
- [ ] All LOD have `contributesTo` array
- [ ] All text cleaned (no markdown, no metadata phrases)
- [ ] New alphas have `contributesTo` array
- [ ] **Narrative citations extracted** - all narratives have `citationNames` when Phase 1 module has "Citations Referenced:" sections
- [ ] **Citation names validated** - EVERY citationName EXACTLY matches a Citation.name from 02-citations.json (NO broken references)
- [ ] **Citation reference integrity** - Run validation script to verify all citationNames correspond to defined citations
- [ ] File size within expected range for segment type

---

## Citation Extraction - Universal Pattern

**Applies to:** Segments 03 (Alphas), 04 (Work Products), 05a (Activities), 06 (Patterns)

**Markdown Pattern in Phase 1 Modules:**

```markdown
**Narrative N: Narrative Title**

**Narrative Type:** Essay Narrative | The STAR Format | How-To Guide | etc.

**Narrative Contexts:**
[narrative content paragraphs]

**Citations Referenced:** Citation Title 1, Citation Title 2, Citation Title 3
```

**Extraction Algorithm:**

1. **Locate narrative section** - Identified by `**Narrative N: Title**` or similar heading
2. **Find "Citations Referenced:"** - Look for this marker AFTER narrative content
3. **Parse citation list** - Comma-separated list on same line as marker
4. **Clean names** - Trim whitespace from each citation name
5. **Validate names** - Each must EXACTLY match a Citation.name from 02-citations.json
6. **Add to JSON** - Include `citationNames` array in Narrative object

**JSON Output:**

```json
{
  "name": "Narrative Title",
  "narrativeTypeName": "Essay Narrative",
  "narrativeContexts": [...],
  "citationNames": ["Citation Title 1", "Citation Title 2", "Citation Title 3"]
}
```

**Critical Rules:**

- `citationNames` is OPTIONAL (not in required schema fields)
- Include when "Citations Referenced:" section is present
- Omit entirely if no citations found (don't include empty array unless you're certain)
- Citation names are case-sensitive and must match exactly
- Order doesn't matter but preserve order from source for consistency

**MANDATORY VALIDATION - Citation Name Verification:**

Before saving ANY segment with narratives containing citationNames:

1. **Load citations reference** - Read 02-citations.json to get valid Citation.name values
2. **Check each citationName** - Every string in every citationNames array must EXACTLY match a Citation.name
3. **Report mismatches** - Flag any citationName that doesn't correspond to a defined Citation
4. **Fix before proceeding** - Correct typos or add missing citations to 02-citations.json

**Validation script pattern:**

```python
# Load valid citation names
with open('json-segments/practice-N/02-citations.json') as f:
    valid_citations = {c['name'] for c in json.load(f)}

# Check all narratives in segment
for element in segment_data:
    for narrative in element.get('narratives', []):
        for citation_name in narrative.get('citationNames', []):
            if citation_name not in valid_citations:
                print(f"ERROR: Citation '{citation_name}' not found in citations array")
                print(f"  Referenced in: {element['name']} -> {narrative.get('name', 'unnamed narrative')}")
                # Find closest match for suggestion
                close_matches = difflib.get_close_matches(citation_name, valid_citations, n=1)
                if close_matches:
                    print(f"  Did you mean: '{close_matches[0]}'?")
```

**Common mismatch causes:**
- Different capitalization (e.g., "team topologies" vs "Team Topologies")
- Abbreviated vs full titles (e.g., "Team Topologies book" vs "Team topologies: Organizing business and technology teams for fast flow")
- Punctuation differences (e.g., "Conway's Law" vs "Conway's Law paper")
- Year/edition differences in title

**Never save a segment with unvalidated citationNames** - broken references indicate incomplete translation.
