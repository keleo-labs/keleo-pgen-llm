# Phase 3: JSON Generation Prompt

## Context

You are conducting **Phase 3: JSON Generation** of a methodology translation workflow. This phase creates machine-readable Practice or Method JSON that precisely conforms to the Practice Language JSON Schema.

## Output Location

**CRITICAL — verify before writing any files:**

- **Single practice:** `practices/<practice-name>/<practice-name>.json`
- **Method:** `practices/<method-name>/<method-name>.json` (plus per-practice JSONs)

Always use the practice directory that already contains `01-analysis-report.md` and `02-mapping-guide.md`. Verify the directory exists before writing. Never write to the repository root.

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

3. **Semantic Guidance** (sub-documents in `references/semantics/`)
   - `references/semantics/practice-elements.md` — PracticeElement foundations, tags, checklists (§5)
   - `references/semantics/alphas.md` — Alpha-state trajectory (§6)
   - `references/semantics/work-products.md` — Work product elements, partOf, mapsTo (§7)
   - `references/semantics/execution-and-patterns.md` — Activities, personas, patterns, outcomes (§8-9)
   - `references/semantics/narrative-and-assets.md` — Narratives and assets (§10-11)
   - Read relevant sections for JSON structure guidance

4. **Baseline Practice JSON** (same as Phase 2)
   - For validation of references
   - For extracting baseline structure

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

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

3. **Read relevant semantics sub-documents:**
   - `references/semantics/practice-elements.md` — checklist format, tagging taxonomy (§5)
   - `references/semantics/alphas.md` — alpha structure, state semantics (§6)
   - `references/semantics/work-products.md` — work product LODs, partOf, mapsTo (§7)
   - `references/semantics/execution-and-patterns.md` — activity structure, pattern views, outcomes (§8-9)
   - `references/semantics/narrative-and-assets.md` — narrative structure, citation format (§10-11)

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
  "schemaVersion": "<from schema $comment, e.g. 1.0.0>",
  "version": "1.0.0",
  "baselinePracticeName": "Platform Adoption Essentials",
  "dependencyVersions": [
    {"documentName": "Platform Adoption Essentials", "versionRange": "^1.0.0"}
  ],
  "tags": {
    "domainTags": [...],
    "lifecycleTags": [...],
    "organizationalTags": [...]
  },
  "keywords": [...],
  "authors": [...],
  "createdAt": "YYYY-MM-DD",
  "updatedAt": "YYYY-MM-DD"
}
```

**Versioning rules:**
- `schemaVersion`: Read from the schema's `$comment` field (`schemaVersion:X.Y.Z`). Always set this.
- `version`: `"1.0.0"` for new documents. Use three-part semver.
- `dependencyVersions`: One entry per dependency name (`baselinePracticeName`, each `practiceDependencyNames` entry). Use caret range (`^`) pinned to the dependency's current `version`.

**Parent Practice Mode:** When extending a parent practice (instead of mapping directly to a baseline):
- `baselinePracticeName`: Set to the value **inherited** from the parent practice's `baselinePracticeName` (NOT the parent practice name itself)
- `practiceDependencyNames`: Include any parent practice whose **non-baseline alphas** you redeclare, specialize, or reference. Check `_effective-context.json` provenance: if an alpha's `_contributingPracticeName` points to a practice (not a baseline), and you redeclare/reference that alpha, you MUST list that practice as a dependency.
- `dependencyVersions`: Include entries for BOTH the inherited baseline AND each practice dependency
- All `contributesTo`/`mapsTo` references should primarily target parent practice alphas using canonical names
```json
{
  "baselinePracticeName": "Platform Adoption Essentials",  // inherited from parent
  "practiceDependencyNames": ["Red Hat OpenShift Foundations"],  // parent practice names
  "dependencyVersions": [
    {"documentName": "Platform Adoption Essentials", "versionRange": "^1.0.0"},
    {"documentName": "Red Hat OpenShift Foundations", "versionRange": "^1.0.0"}
  ],
  ...
}
```

**For Method:**
```json
{
  "name": "method-name",
  "description": "Single sentence from mapping guide",
  "schemaVersion": "<from schema $comment>",
  "version": "1.0.0",
  "baselinePracticeName": "Platform Adoption Essentials",
  "dependencyVersions": [
    {"documentName": "Platform Adoption Essentials", "versionRange": "^1.0.0"}
  ],
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

**CRITICAL:**
- Citations have NO narratives property
- The `name` field MUST be the **title of the work** (e.g., "Business Model Generation", "The Art of Action"), NOT an author-date shorthand like "Osterwalder (2010)" or "Bungay (2011)". Authors have their own `authors` field.
- The `url` field SHOULD be populated for every citation — carry forward URLs from the mapping guide (which inherits them from the analysis report). Internal, intranet, and Google Docs/Sheets/Slides URLs are valid and preferred when available. Use user-provided URLs, official websites, DOI references (`https://doi.org/10.xxxx/xxxxx`), or publisher pages. Only omit when no stable link exists.

#### 3.3 Acknowledgements (Optional)

Add acknowledgements to recognize individuals, groups, or institutions that contributed to the methodology. Distinct from citations — acknowledgements attribute human contributions rather than published works.

```json
"acknowledgements": [
  {
    "name": "Person or Institution Name",
    "description": "Brief description of their contribution",
    "url": "https://optional-profile-or-contact-url"
  }
]
```

Include acknowledgements when the source methodology credits specific contributors, research groups, or supporting organizations.

#### 3.4 Assets (Optional)

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
- **Personas**: Role icon (font character) — e.g., `fa-user-gear` for engineer, `fa-user-shield` for security lead
- **Persona Groups**: Team icon (font character) — e.g., `fa-people-group` for cross-functional team
- **Competencies**: Skill area icon (font character)
- **Work Products**: Template reference (URL) if applicable
- **Patterns**: Workflow diagram (URL or bundled if custom)

**Common Font Awesome Icons:**

- Platform/Infrastructure: `fa-cubes`, `fa-server`, `fa-cloud`
- Team/People: `fa-users`, `fa-user-group`, `fa-people-group`
- Roles: `fa-user-gear`, `fa-user-tie`, `fa-user-shield`, `fa-user-doctor`, `fa-user-astronaut`
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
    "contributesTo": "baseline-alpha-name",  // REQUIRED for specializations (may coexist with mapsTo on different target)
    // AND/OR: "mapsTo": "parent-alpha-name",    // REQUIRED for variant mappings (may coexist with contributesTo on different target)
    "relatesTo": [  // ONLY for new alphas (NOT redeclarations)
      {
        "relationship": "produces",
        "alphaName": "Platform Asset",
        "direction": "outgoing",
        "relationshipKind": "production",  // Optional — machine-traversable classification
        "description": "Each capability produces consumable platform assets"
      },
      {
        "relationship": "depends on",
        "alphaName": "Requirements",
        "direction": "outgoing",
        "relationshipKind": "dependency"
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
        "contributesToState": "Parent State Name",  // Optional - for alphas with contributesTo or mapsTo
        "background": {  // Optional - shared prerequisites for this state
          // NEVER reference the previous state of the SAME alpha — sequential progression is implicit in seq ordering
          // NEVER reference the previous LOD of the SAME work product in workProductLevels
          "given": ["Precondition that should hold when evaluating this state"],
          "alphaStates": [
            { "alphaName": "Other Alpha", "stateName": "State" }  // Cross-alpha dependencies ONLY
          ],
          "workProductLevels": [
            { "workProductName": "Work Product", "levelOfDetailName": "Level" }
          ]
        },
        "checklist": [
          {
            "name": "Imperative verb phrase (action to take)",
            "description": "WHY and HOW — rationale, scope, method (must add information beyond the name)",
            "seq": 1,
            "priority": "should",  // Optional — omit for essential items (defaults to "must"). Use "should" for important-but-deferrable, "could" for supplementary. See semantics §5.2.2.
            "test": {  // Optional - completion criteria / definition of done
              "name": "What is being verified (not mechanical '{fragment} verification')",
              "description": "Specific verification purpose (not 'Definition of done.')",
              "given": ["Meaningful precondition (omit test entirely if empty)"],
              "when": ["Meaningful trigger or evaluation point (omit test entirely if empty)"],
              "then": ["Independently observable evidence (not description in past tense)"]
            },
            "examples": [  // Optional - concrete scenario Tests
              {
                "name": "Example scenario",
                "description": "Concrete illustration",
                "given": ["Specific setup"],
                "when": ["Specific trigger"],
                "then": ["Specific outcome"]
              }
            ],
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

- New alphas MUST have `contributesTo` OR `mapsTo` (NO FLOATING ALPHAS). Both may coexist on the same alpha but must reference different targets.
- **`mapsTo` alphas**: States MUST exactly match the target alpha (same names, same sequence). Use for IS-A variants.
- **relatesTo ONLY on new alphas**: Do NOT add relatesTo to baseline alpha redeclarations
  - Redeclarations inherit baseline relationships automatically
  - Only new alphas (with `contributesTo` or `mapsTo`) should define relatesTo
  - Copy relatesTo array exactly from mapping guide for new alphas
  - Every relatesTo entry MUST include `direction` (`outgoing`, `incoming`, or `mutual`) — required by schema
  - Optional `description` field explains why the relationship exists
  - Validate every alphaName in relatesTo references a valid alpha (baseline or practice-defined)
- Checklist items are objects {name, description, seq}, NOT strings. Every item name must be an imperative verb phrase describing an action to take (e.g., "Define key metrics" not "Metrics defined"; "Establish security controls" not "Security controls established"). Every item must be positive and additive — describes an action to perform, never the absence or lack of something (e.g., "Define key metrics" not "Metrics absent"). When `test` is present, it defines the completion criteria (definition of done); the `then` clauses specify what "done" looks like. Every item must be independently assessable — no meta-items that summarise or reference other checklist items (e.g., "All requirements met", "Minimum standards achieved", "N criteria satisfied"). The checklist IS the requirements; items that restate that fact are circular and must be removed. The `description` must carry information not present in the `name` — rationale, scope, method, or context that a practitioner needs before starting. A description that restates the name as a longer sentence is redundant and must be rewritten. When `test` is present, `test.then` must describe independently observable evidence — not the description in past tense. `test.given` and `test.when` must be populated with meaningful preconditions and triggers; if they cannot be, omit the `test` entirely. `test.description` must describe the specific verification purpose — not the literal string "Definition of done." Optional `priority` field: omit for essential items (defaults to `"must"`); set `"should"` for important-but-deferrable items, `"could"` for supplementary items. See `references/semantics/practice-elements.md` §5.2.2 for authoring guidance. Transfer priority signals from the Phase 2 mapping guide.
- evidencedBy is optional array of WorkProductContribution
- **Redeclared alpha state handling (CRITICAL):**
  - Include ALL states from the baseline/parent practice definition — never subset to only enriched states
  - Add practice-specific checklists ONLY to states that the Phase 2 mapping guide explicitly enriches
  - For unenriched states, include them with an empty `"checklist": []` — do NOT fabricate checklists
  - The validator checks for exact state-set match with the parent; missing or extra states are errors

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
    "contributesToAlphaNames": ["Alpha 1", "Alpha 2"],  // Optional — purpose-hub summary of which alphas this WP serves (union of all LOD contributesTo alphaNames)
    "expectedMetrics": [  // Optional — declare metric names that instances may carry. Include when outcomes reference this work product via metricContributions
      { "name": "metric-name", "description": "What this metric measures", "unit": "USD" }
    ],
    "partOf": "Parent Work Product Name",  // Optional — containment relationship (mutually exclusive with mapsTo; see semantics/work-products.md §7.5)
    "mapsTo": "Parent Work Product Name",  // Optional — variant mapping (mutually exclusive with partOf). LODs MUST match target exactly. See semantics/work-products.md §7.6
    "levelsOfDetail": [
      {
        "name": "Level Name",  // NO "Level X:" prefix
        "description": "Single sentence (max 12 words)",
        "seq": 1,
        "background": {  // Optional - shared prerequisites for this LOD
          // NEVER reference the previous LOD of the SAME work product — sequential progression is implicit in seq ordering
          // NEVER reference the previous state of the SAME alpha in alphaStates
          "given": ["Precondition for reaching this level"],
          "alphaStates": [
            { "alphaName": "Alpha", "stateName": "State" }
          ],
          "workProductLevels": [
            { "workProductName": "Other Work Product", "levelOfDetailName": "Level" }  // Cross-work-product dependencies ONLY
          ]
        },
        "checklist": [
          {
            "name": "Imperative verb phrase (action to take)",
            "description": "What to accomplish and why (one sentence)",
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
- LOD names describe **document fidelity/depth** (what the artifact looks like), NOT concern lifecycle (where the concern stands). Use `references/workproduct-assessment-rubric.csv` as the naming lens. Every LOD covers the same scope at increasing depth — the difference is detail, not temporal progression.
- checklist items are objects, NOT strings
- contributesTo is REQUIRED on every LOD
- `partOf` is optional — include when the mapping guide identifies a containment relationship. The value must exactly match a WorkProduct.name (same practice, dependency, or baseline)
- `mapsTo` is optional — include when the mapping guide identifies a variant relationship (IS-A). The value must exactly match a WorkProduct.name. `mapsTo` and `partOf` are **mutually exclusive** — never set both on the same work product
- **`mapsTo` work products**: LODs MUST exactly match the target work product (same LOD names, same sequence). The variant has domain-specific checklists but shares the parent's LOD structure. On merge, variants are added to the parent's `variants` array.
- **`mapsTo` naming convention**: Variant work product names MUST NOT repeat the parent type name — `mapsTo` reads as "is a type of", so including the type is redundant (e.g., "Cloud Architecture" not "Cloud Architecture Document" when mapping to "Architecture")
- **`expectedMetrics` consistency**: When an outcome's `metricContributions` references a `metricName`, the work product whose instances will carry that metric SHOULD declare it in `expectedMetrics`. This validates the metric chain: Outcome → MetricContribution → alpha → evidenceBy → WorkProductInstance → metrics. The `metricName` values must match exactly.

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
    "narratives": [ ... ],
    "assetNames": [
      {
        "assetName": "persona-icon-name",
        "type": "icon"
      }
    ]
  }
]
```

**Narratives:** Include when the mapping guide provides a persona narrative (sourced from Phase 1 role detail). Use the same narrative structure as other elements — narrativeTypeName + narrativeContexts. Do NOT invent narrative content absent from the mapping guide.

**Asset Icons:** Include a font-character icon for each persona. Add corresponding entries to the top-level `assets` array:
```json
{
  "name": "persona-icon-name",
  "type": "font-character",
  "fontFamily": "Font Awesome 6 Free",
  "fontCharacter": "fa-user-gear",
  "fontWeight": "900"
}
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
    "narratives": [ ... ],
    "assetNames": [
      {
        "assetName": "team-icon-name",
        "type": "icon"
      }
    ]
  }
]
```

**Narratives:** Include when the mapping guide provides a persona group narrative (sourced from Phase 1 team detail — charter, formation model, interaction patterns). Do NOT invent team narratives absent from the mapping guide.

**Asset Icons:** Include a font-character icon for each persona group, with corresponding top-level `assets` entry.

#### 3.10 Activities

Add activities array:
```json
"activities": [
  {
    "name": "Specific Activity Name",  // DIFFERENT from activity space name
    "description": "Single sentence",
    "activitySpaceName": "Baseline Activity Space",
    "focusName": "Value | Solution | Endeavor",
    "background": {  // Optional - shared prerequisites for this activity
      "given": ["Precondition before activity begins"],
      "alphaStates": [
        { "alphaName": "Alpha", "stateName": "State" }
      ],
      "workProductLevels": [
        { "workProductName": "Work Product", "levelOfDetailName": "Level" }
      ]
    },
    "test": {  // Optional - structured execution scenario (see semantics/execution-and-patterns.md §8.1.1)
      "name": "Execution scenario name",
      "description": "What triggers and outcomes this test captures",
      "given": ["Preconditions for the activity"],
      "when": ["Triggers, decision points, or events that initiate the activity"],
      "then": ["Expected outcomes — MUST NOT restate contributesTo/worksOn targets"]
    },
    "examples": [  // Optional - concrete scenario Tests
      {
        "name": "Concrete scenario",
        "description": "Specific illustration",
        "given": ["Specific setup"],
        "when": ["Specific trigger"],
        "then": ["Specific outcome"]
      }
    ],
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
    "ledBy": "Persona Name",  // Optional — single Persona.name accountable for leading this activity (distinct from involves which maps participating groups)
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
        "workProductLevels": [  // Optional — work product LOD objectives for this phase
          {
            "workProductName": "Work Product",
            "levelOfDetailName": "Level Name"
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
    "narratives": [ ... ]
  }
]
```

**Pattern-Level Narratives:** Include when the mapping guide provides a pattern narrative (sourced from Phase 1 lifecycle rationale — why these phases exist, the transformation story). This is the pattern's own narrative, distinct from the per-view `narrativeContexts`. Do NOT invent lifecycle rationale absent from the mapping guide.

**CRITICAL:**

- Use `patternViews` NOT `views`
- Use `alphaStates` NOT `alphas`
- PatternView.seq is REQUIRED
- NO `workProducts` property on PatternView — use `workProductLevels` (array of `{workProductName, levelOfDetailName}`) to declare work product LOD objectives per phase
- activities are string names, not objects
- **Each alpha MUST target at most 1 state per patternView** — if a phase advances an alpha through multiple states, split into sub-views using `Phase: Sub-step` naming (e.g., "Enable: Train", "Enable: Certify"). Each sub-view gets its own seq, activities, and narrative context.
- **State compression:** In non-final views, only include alpha states that CHANGE from the previous view. Omit unchanged carry-forward states — they are implicit. The FINAL view MUST include ALL alphas (even if unchanged) as a complete end-state snapshot.

**Asset Linking:**

- If mapping guide identifies workflow diagrams or lifecycle visualizations for this pattern, add `assetNames`:

  ```json
  {
    "name": "Platform Adoption Lifecycle",
    "assetNames": ["platform-adoption-workflow-diagram", "maturity-progression-chart"]
  }
  ```

#### 3.11.5 Pattern Groups

If the mapping guide defines pattern groups (Step 8.5), add a `patternGroups` array. PatternGroups organize patterns into navigational categories — most useful when a practice has 3+ patterns or a method will compose 10+.

```json
"patternGroups": [
  {
    "name": "Core Lifecycles",
    "description": "Primary adoption and maturity journeys for each practice area",
    "seq": 0,
    "entries": [
      { "patternName": "Platform Adoption Lifecycle", "seq": 0 },
      { "patternName": "Team Formation Journey", "seq": 1 },
      { "patternName": "Value Realization Cycle", "seq": 2 }
    ],
    "narratives": [
      {
        "name": "Navigating Core Lifecycles",
        "description": "How the primary lifecycles relate and when to use each",
        "narrativeTypeName": "Essay",
        "narrativeContexts": [
          {
            "seq": 1,
            "narrativeElementName": "Introduction",
            "context": "Each practice area follows a distinct lifecycle reflecting its primary concern."
          },
          {
            "seq": 2,
            "narrativeElementName": "Body",
            "context": "Platform adoption drives technical maturity, team formation builds organizational capability, and value realization tracks business outcomes."
          },
          {
            "seq": 3,
            "narrativeElementName": "Conclusion",
            "context": "Start with platform adoption as the foundation, then layer team and value lifecycles as the organization matures."
          }
        ],
        "citationNames": ["..."]
      }
    ],
    "tags": {
      "lifecycleTags": ["Adoption"]
    }
  }
]
```

**CRITICAL:**

- When adopting baseline-defined groups, use the **exact baseline group name** — this is the merge key for cross-practice composition
- Only include groups that have patterns assigned — do NOT emit empty baseline groups in extension practices (the baseline already defines them)
- `patternName` must exactly match a defined `Pattern.name`
- `seq` on entries provides sort order within the group (0-based)
- `seq` on the group provides sort order among groups (0-based); alphabetical when absent
- A pattern should appear in at most one group
- Ungrouped patterns remain valid — they render in a default section
- **Narratives:** Include when the mapping guide provides group-level rationale — why these patterns belong together, how they relate, how to navigate between them. Narratives help users understand the group's purpose. Omit if the grouping is self-explanatory.
- Cross-practice groups merge by canonical name during method composition (entries merge by `patternName`, overlay seq wins)

#### 3.11.7 Outcomes

Build the `outcomes` array from the mapping guide's Outcome Mappings section. Each practice should have 1-3 outcomes describing how it creates value and how that value is measured.

```json
"outcomes": [
  {
    "name": "Outcome Name",
    "description": "Single sentence describing the value this practice delivers",
    "measureDescription": "How success is measured — clear enough for teams to set meaningful targets",
    "metricContributions": [
      {
        "alphaName": "Alpha Name",
        "metricName": "metric-name",
        "workProductName": "Work Product Name",
        "recognizedAtStateName": "State Name",
        "forecastWeights": [
          { "stateName": "Earlier State", "weight": 0.3 },
          { "stateName": "Later State", "weight": 1.0 }
        ]
      }
    ],
    "objectiveContributions": [
      {
        "patternName": "Pattern Name",
        "recognizedAtPatternViewName": "View Name",
        "forecastWeights": [
          { "patternViewName": "Foundation", "weight": 0.25 },
          { "patternViewName": "Optimized", "weight": 1.0 }
        ]
      }
    ]
  }
]
```

**CRITICAL:**
- Every outcome MUST have at least one of `metricContributions` or `objectiveContributions` — an outcome with neither is a validation error
- `measureDescription` is always required — describes the measurement framework
- Omit empty arrays entirely rather than including `"metricContributions": []`
- All `alphaName` values must match an alpha defined in this practice, baseline, or dependency
- All `stateName` values must match a state on the referenced alpha
- Optional `workProductName` on a metricContribution filters which evidencing work product type supplies the metric; when set it must match a WorkProduct.name
- `patternName` is REQUIRED on every objectiveContribution — it scopes all patternViewName references to views within that pattern (analogous to alphaName on MetricContribution)
- All `patternViewName` values must match a PatternView.name within the named pattern
- The `recognizedAtStateName` entry MUST have weight 1.0 in `forecastWeights`

**Deriving forecastWeights:**
- Use `metricContributions` when the outcome tracks a numerical aggregate (revenue, count, capacity) through the alpha evidence chain
- Use `objectiveContributions` when the outcome tracks lifecycle phase completion (readiness, maturity, compliance) through pattern views
- Weights represent the probability or proportion of the outcome value recognized at each state/view — earlier states get lower weights, the recognition state gets 1.0
- For sales-type pipelines: map weights to conversion probability (e.g., Identified=0.05, Qualified=0.25, Validated=0.5, Committed=0.8, Won=1.0)
- For maturity-type outcomes: map weights to cumulative progress (e.g., initial=0.1, developing=0.3, established=0.6, optimized=0.85, transformational=1.0)
- Include a weight entry for every state/view where partial recognition is meaningful — states not listed have implicit weight 0

**Lifecycle pattern outcome bias:** If the practice has at least one lifecycle pattern, at least one outcome SHOULD use `objectiveContributions` tied to the main lifecycle pattern (broadest alpha coverage). Set `patternName` to the pattern name, `recognizedAtPatternViewName` to the final view, and assign monotonically increasing `forecastWeights` across all views. This is the most natural way to track practice adoption maturity.

#### 3.12 References (Curated External Content)

If the mapping guide includes a "Reference Content Mappings" section, add a `references` array. Each reference is an `AlphaInstance` object anchored to an alpha at a specific state, with links to actionable external content (templates, sample artifacts, worked examples) and optional work product evidence. References must be things practitioners can directly use or adapt — not documentation explaining concepts.

```json
"references": [
  {
    "name": "TOGAF-Based Platform Architecture",
    "description": "Example of a platform achieving Architecture Selected state following TOGAF architectural patterns.",
    "alphaName": "Platform",
    "stateName": "Architecture Selected",
    "links": [
      {
        "name": "TOGAF Architecture Framework",
        "description": "The Open Group Architecture Framework reference",
        "uri": "https://www.opengroup.org/togaf"
      }
    ],
    "evidenceBy": [
      {
        "name": "TOGAF Architecture Document Template",
        "description": "Template for creating architecture documentation following TOGAF standards with ADR structure.",
        "workProductName": "Architecture",
        "levelOfDetailName": "Defined",
        "links": [
          {
            "name": "Architecture Document Template",
            "description": "Downloadable TOGAF-aligned architecture document template",
            "uri": "https://example.com/templates/togaf-architecture.docx"
          }
        ]
      }
    ],
    "tags": {
      "domainTags": ["Architecture"],
      "lifecycleTags": ["Adoption"],
      "organizationalTags": ["Platform Team"]
    }
  }
]
```

**CRITICAL:**

- Every reference MUST have at least one `links` entry with a valid `uri`. References without links provide no actionable value — drop them.
- **Use `pages` on `ExternalLink` when the actionable content (template, example, artifact) is at a specific location within a larger document.** A link to a large document without `pages` is rarely a valid reference — without it, the link points to documentation, not a starting point. Format: APA 7th edition ("pp. 23-31", "Section 3", "Slides 12-15", "Appendix B").
- `alphaName` must match a defined alpha (baseline or practice)
- `stateName` must match a state on the referenced alpha
- `evidenceBy` entries are **full WorkProductInstance objects** — each MUST have `name`, `description`, `workProductName`, `levelOfDetailName`, and `links` (with at least one valid URI). Bare `{workProductName, levelOfDetailName}` objects are invalid.
- Reference names should be unique and descriptive (identify the source, not generic labels)
- Tags are optional but recommended for filtering

**Instance Naming Rules:**

- **Instance names scope to the example, NOT the state or LOD.** A real-world instance that appears at different maturity levels shares ONE name — the name identifies the specific example, not where it sits in the progression.
- **"Same example or different?" test:** Before creating a new reference for the same alpha, check whether the content belongs to an existing instance at a different state. If it's the same real-world example at a different level of progression, use the same instance name. Only create a separate instance for a genuinely different example.
- **Apply the same logic to `evidenceBy`:** If multiple work product artifacts are instances of the same real-world document at different LODs, use the same WorkProductInstance name.

**Merge Pass (Post-Generation):**

After generating all references, perform a merge pass:
1. **Key on instance `name`** (NOT `alphaName` or `workProductName`)
2. Same-name AlphaInstance references → keep highest `stateName`, aggregate all `links` and `evidenceBy`
3. Same-name WorkProductInstance entries within `evidenceBy` → keep highest `levelOfDetailName`, aggregate all `links`
4. **Links arrays can contain many documents** — aggregation produces richer, more useful references

#### 3.13 Practice Element Aliases

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

**Alias rules:**
- **Do NOT re-declare aliases from parent/dependency practices** — they are inherited through `practiceDependencyNames`
- **Do NOT reuse a dependency alias name for a different target** — causes collision errors on merge
- For **mapsTo variant** alphas, differentiate alias names from parent aliases (e.g., prefix with practice domain: "RHEL Deal Registration" not "Deal Registration")
- Only create aliases for elements **this practice defines or redefines**

#### 3.14 Method Packaging (For Methods)

If generating a Method:

1. Generate complete Practice JSON for EACH practice as **standalone files** (following steps 3.1-3.12)
2. Each practice JSON is a self-contained document with `kind: "practice"`, `baselinePracticeName`, and all its own elements
3. The method uses **externalized references** — `practiceNames` (string array) and `baselinePracticeName` (string) instead of embedded objects:

```json
{
  "kind": "method",
  "name": "Method Name",
  "description": "Method description",
  "baselinePracticeName": "Platform Adoption Essentials",
  "practiceNames": ["Practice 1", "Practice 2"],
  "citations": [...],    // Merged from all practices (deduplicated)
  "narratives": [...],   // Method-level narratives
  "alphaBindings": [...]  // Optional - cross-baseline alpha contributions (see below)
}
```

4. All documents (baseline JSON, practice JSONs, method JSON) are bundled into a `.keleo` package (ZIP archive with `manifest.json`). The packaging is handled by `utils/package-keleo.py`.

**Schema rules for externalized methods:**
- `baselinePracticeName` and `baselinePractice` (embedded object) are **mutually exclusive** — use only the string form for packaged methods
- `practiceNames` must be present (even if empty) for the document to be classified as a Method by the schema discriminator
- `practiceNames` and `practices` (embedded array) can coexist, but for `.keleo` packages use only `practiceNames`

**Parent Practice Mode:** When extending a parent practice:
- Method-level `baselinePracticeName`: Inherited from parent practice
- Method-level `practiceDependencyNames`: Parent practice name(s) from Step 0.25
- Each standalone practice inherits the same `baselinePracticeName` and `practiceDependencyNames`

**Cross-Baseline Alpha Bindings (`alphaBindings`):**

When a method composes practices from different baseline families, add `alphaBindings` at the method level to declare cross-baseline contribution relationships:

```json
"alphaBindings": [
  {
    "baselineAlpha": {
      "baselineName": "Target Baseline Name",
      "alphaName": "Target Alpha Name"
    },
    "contributingAlphas": [
      {
        "baselineName": "Contributing Baseline Name",
        "alphaName": "Contributing Alpha Name",
        "stateContributions": [
          { "fromState": "Contributing State", "toState": "Target State" }
        ]
      }
    ]
  }
]
```

Only include `alphaBindings` when the method spans multiple baselines. `stateContributions` is optional — alpha-level binding without state mapping is valid. All baseline/alpha/state names must resolve to valid references.

#### 3.15 Verify Complete Structure

Before proceeding to validation, verify ALL sections from 3.1-3.14 are complete:

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
- [ ] 3.11.7: `outcomes` array (1-3 per practice; warn if empty)
- [ ] 3.12: references array (if mapping guide has Reference Content Mappings)
- [ ] 3.13: practiceElementAliases array (if applicable)

**For Method JSON, verify EACH practice has:**

- [ ] All arrays from 3.4-3.13 above
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

Run the comprehensive validator with the **leaf baseline** (not the effective context):
```bash
python3 ../../utils/validate-practice-json.py \
  <practice-name>.json \
  <leaf-baseline>.json \
  ../../deps/language.schema.json
```

The validator auto-discovers `_effective-context.json` in the practice directory for cross-practice element resolution. Checks include schema compliance, baseline references, internal integrity, patternView ambiguity, and alias collision detection.

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
- Floating alphas → Add `contributesTo` or `mapsTo`

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
- Add `contributesTo` or `mapsTo` to new alphas
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
- [ ] Verify ALL arrays present: citations, narratives, alphas, alphaInstances, workProducts, workProductInstances, personas, **personaGroups**, activities, patterns, references (if mapped), practiceElementAliases
- [ ] No content omissions from Phase 2 mapping guide
- [ ] All narratives present (alpha, activity, practice/method level)
- [ ] Persona/PersonaGroup/Pattern narratives present where mapping guide provided source-grounded content
- [ ] Asset icons present for personas, persona groups, and competencies (with corresponding top-level assets entries)
- [ ] All checklists present (alpha states, work product LODs)
- [ ] All citations referenced in citationNames exist
- [ ] All symbolic references are exact matches
- [ ] Work product `mapsTo` references (if any) point to valid targets with matching LOD names/sequences; `partOf` and `mapsTo` not both set on same work product
- [ ] JSON is well-formatted and readable

## Common Schema Violations to Avoid

### 1. Checklist Format
❌ Wrong: `"checklist": ["Item 1", "Item 2"]`
❌ Wrong: `"name": "Architecture documented"` (criteria-style, past participle)
✅ Right:
```json
"checklist": [
  {
    "name": "Document the architecture",
    "description": "Create a reference architecture with technology stack decisions and rationale.",
    "seq": 1
  }
]
```
Names must be imperative verb phrases (actions to take), not past-participle conditions.

### 2. Meta-Checklist Items
❌ Wrong: `"name": "Meet minimum requirements", "description": "Complete all thirteen minimum documentation requirements"`
❌ Wrong: `"name": "Achieve standards", "description": "Satisfy all mandatory criteria"`
✅ Right: Each checklist item independently describes a specific, actionable task. The checklist IS the list of tasks — items that reference or count other items are circular and add no value.

### 2b. Checklist Information Echo

**Bad:** Description restates name; test restates description in past tense:

```json
{
  "name": "Identify Target AI Personas",
  "description": "Identify target AI personas across the organization.",
  "test": {
    "name": "Target AI Personas verification",
    "description": "Definition of done.",
    "given": [], "when": [],
    "then": ["target AI personas identified across the organization"]
  }
}
```

**Good:** Each field carries distinct information:

```json
{
  "name": "Identify Target AI Personas",
  "description": "Map organizational roles that will interact with AI capabilities to inform platform configuration and adoption sequencing.",
  "test": {
    "name": "AI persona coverage verification",
    "description": "Verify persona mapping spans all relevant organizational functions.",
    "given": ["Customer has active or planned AI initiatives"],
    "when": ["Account team prepares AI platform engagement plan"],
    "then": [
      "Each business unit with AI initiatives has at least one mapped persona",
      "Persona-capability mapping informs platform configuration priorities"
    ]
  }
}
```

### 3. Competency Level Reference
❌ Wrong: `{"competencyName": "Engineering", "level": 3}`
✅ Right: `{"competencyName": "Engineering", "competencyLevelName": "Advanced"}`

### 4. Persona Property
❌ Wrong: `"requiredCompetencies": [...]`
✅ Right: `"competencies": [...]`

### 5. Activity Competencies
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

### 6. PatternView Properties
❌ Wrong: `"alphas": [...]` or `"views": [...]` or `"workProducts": [...]`
✅ Right: `"alphaStates": [...]` and `"patternViews": [...]`

### 7. LevelOfDetail.contributesTo
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

### 8. Floating Alphas
❌ Wrong: New alpha without `contributesTo` or `mapsTo`
✅ Right (Specialization):
```json
{
  "name": "Platform Capability",
  "description": "...",
  "focusName": "Solution",
  "contributesTo": "Platform",  // Specialization — different states from parent
  "states": [...]  // Own state progression
}
```
✅ Right (Variant Mapping):
```json
{
  "name": "AI-Ready Enterprise",
  "description": "...",
  "focusName": "Value",
  "mapsTo": "Sales Play",  // Variant mapping — EXACT same states as parent
  "states": [...]  // Must match Sales Play states exactly
}
```
❌ Wrong: Both set to same target
```json
{
  "contributesTo": "Platform",
  "mapsTo": "Platform"  // INVALID — must reference different alphas!
}
```

### 9. Tags Structure
❌ Wrong: `"tags": ["tag1", "tag2"]` OR `"domainTags": [...], "lifecycleTags": [...]` (flat)
✅ Right:
```json
"tags": {
  "domainTags": [...],
  "lifecycleTags": [...],
  "organizationalTags": [...]
}
```

### 10. Citation Narratives
❌ Wrong: Citations with narratives property
✅ Right: Citations with ONLY metadata (no narratives)

### 11. Work Product LOD Names
❌ Wrong: `"name": "Level 1: Basic"` (generic numbered prefix)
❌ Wrong: `"name": "Work Completed"`, `"name": "Definition of Done Met"`, `"name": "Goal Stated"` (lifecycle/temporal stages — describe where the concern is, not what the document looks like)
❌ Wrong: `"name": "Continuously Updated"`, `"name": "Evolved and Optimized"` (process states, not content depth)
✅ Right: `"name": "Completion Record"`, `"name": "Quality-Verified Release"`, `"name": "Brief Objective"` (describe document content at that fidelity level)

### 12. Gherkin Structures (background, test, examples)
❌ Wrong: `background` as a string or array
✅ Right: `background` is an object with optional `given`, `alphaStates`, `workProductLevels` arrays:
```json
"background": {
  "given": ["Stakeholder needs have been documented"],
  "alphaStates": [{ "alphaName": "Requirements", "stateName": "Bounded" }]
}
```
❌ Wrong: `alphaStates` referencing the previous state of the SAME alpha (redundant — seq ordering is implicit):
```json
// On alpha "Platform", state "Operational" (seq: 3):
"background": { "alphaStates": [{ "alphaName": "Platform", "stateName": "Provisioned" }] }  // BAD — same alpha
```
❌ Wrong: `workProductLevels` referencing the previous LOD of the SAME work product (redundant):
```json
// On work product "Architecture Document", LOD "Logical" (seq: 2):
"background": { "workProductLevels": [{ "workProductName": "Architecture Document", "levelOfDetailName": "Descriptive" }] }  // BAD — same work product
```
✅ Right: Only cross-element dependencies in `alphaStates` and `workProductLevels`
❌ Wrong: `test` as a string or using `test` on elements that don't support it
✅ Right: `test` is a Test object (extends PracticeElement) — only on Checklist and Activity. On checklists, test defines the completion criteria (definition of done); on activities, test captures triggers and observable results:
```json
"test": {
  "name": "Completion criteria scenario",
  "description": "Definition of done for this task",
  "given": ["Precondition"],
  "when": ["Trigger or condition"],
  "then": ["What 'done' looks like — observable outcome"]
}
```
❌ Wrong: `examples` as a flat string array
✅ Right: `examples` is an array of Test objects:
```json
"examples": [
  { "name": "Scenario 1", "description": "...", "given": ["..."], "when": ["..."], "then": ["..."] }
]
```

### 13. Activity Properties
❌ Wrong: Activities with `seq`, `citationNames`, or `involves` as object array
✅ Right:
- Activities do NOT have `seq` (unlike checklists)
- Activities do NOT have `citationNames` (use citation refs in narratives instead)
- `involves` is a `string[]` of persona group names, NOT an array of objects
- Activities MUST have `focusName` (derived from activity space focus)
```json
{
  "name": "Configure Platform",
  "focusName": "Solution",
  "activitySpaceName": "Architecture Design",
  "involves": ["Platform Team", "Security Team"],
  "requiredCompetencies": ["Engineering"],
  "recommendedCompetencyLevels": [...]
}
```

### 14. Work Product Properties
❌ Wrong: Work products with `alphaName` or `focusName`
✅ Right: Work products link to alpha states via `contributesTo` on their LODs, not top-level properties

### 14b. Work Product `partOf` and `mapsTo`
❌ Wrong: `"partOf": "Same Work Product Name"` (self-reference)
❌ Wrong: Circular chain (A partOf B, B partOf A)
❌ Wrong: Work product with both `partOf` and `mapsTo` (mutually exclusive)
❌ Wrong: `mapsTo` variant with different LOD names than parent (LODs must match exactly)
❌ Wrong: `"mapsTo": "Same Work Product Name"` (self-reference)
✅ Right: `"partOf": "Parent Work Product Name"` — optional string referencing another WorkProduct.name in the same practice, a dependency, or the baseline. Use for containment (component within a larger deliverable), not for "contributes evidence to" relationships.
✅ Right: `"mapsTo": "Architecture"` with matching LOD progression (e.g., Outlined → Detailed → Validated) — use for IS-A variant mapping. Variant has domain-specific checklists but same LOD structure as parent. On merge, added to parent's `variants` array.

### 15. Work Product Instances
❌ Wrong: `"instanceName": "Production Platform"`
✅ Right: `"name": "Production Platform"` — instances use `name`, not `instanceName`

### 16. Pattern View Alpha State Deduplication
❌ Wrong: Same alpha appearing multiple times in a single PatternView's `alphaStates`
✅ Right: Each alpha targets at most 1 state per PatternView — deduplicate

### 17. Outcomes
**Missing:** `outcomes` array absent — practices should have 1-3 outcomes describing value delivery
**Wrong:** Outcome with only `measureDescription` and no contribution mechanism; `metricContributions` referencing non-existent alphas or states; `objectiveContributions` missing `patternName`; empty contribution arrays instead of omitting; `recognizedAt` state without weight 1.0 in forecastWeights
**Right:** 1-3 outcomes with `measureDescription` plus at least one of `metricContributions` or `objectiveContributions`; every objectiveContribution has `patternName` scoping its view references; valid symbolic references; `recognizedAt` entry has weight 1.0; empty arrays omitted

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
- `contributesTo` OR `mapsTo`: REQUIRED on all new alphas (may coexist on different targets). `contributesTo`: REQUIRED on all LODs.
- Both requiredCompetencies AND recommendedCompetencyLevels on activities
- patternViews.seq: REQUIRED on all pattern views

### Prohibited Patterns
- NO floating alphas (all new alphas have `contributesTo` or `mapsTo`)
- NO `contributesTo` AND `mapsTo` referencing the same target alpha (must be different targets)
- NO `partOf` AND `mapsTo` on same work product (mutually exclusive)
- NO `mapsTo` work product with LOD names/sequences that differ from the target
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
- ✓ No floating alphas (all new alphas have `contributesTo` or `mapsTo`)
- ✓ All required fields present
- ✓ All competency references use exact baseline names
- ✓ All symbolic references are exact matches
- ✓ No markdown or metadata in JSON strings
- ✓ Narratives and checklists complete
- ✓ References array populated from mapping guide (if Reference Content Mappings section present)
- ✓ Every reference has at least one link with valid URI

Validated JSON is ready for use in Practice Language consuming systems.
