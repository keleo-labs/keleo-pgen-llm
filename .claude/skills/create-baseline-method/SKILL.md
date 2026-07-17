# create-baseline-method Skill

## Metadata

**Name:** create-baseline-method
**Description:** Generate foundational baseline practice JSON from source methodology
**Trigger:** When user provides source methodology for baseline practice creation

## Overview

This skill automates the creation of **baseline practice JSON** files - foundational frameworks that define alphas, competencies, activity spaces, and narrative types for a domain. Baseline practices are extended by regular practices (created with `/generate-method`).

**Key Distinction:**
- **Baseline Practices** (this skill): Define foundational ontology (root alphas, alphaInstances, competencies, focuses, narrativeTypes, activitySpaces)
- **Extension Practices** (`/generate-method`): Specialize baselines with redeclarations, new alphas (with contributesTo), activities, workProducts, patterns

### Alpha Instances in Baselines

Baseline alphas are intentionally broad to support reuse across multiple extension practices. **Alpha Instances** illustrate how a broad alpha applies within the baseline's specific domain without narrowing the alpha itself.

**When to use Alpha Instances vs Aliases vs New Alphas:**

| Technique | Use When | Example |
|---|---|---|
| **Alpha Instance** | The parent alpha is correct but has multiple domain-specific manifestations worth naming | Stakeholders → instances: "Application Developer", "Platform Engineer", "Budget Owner" |
| **Alias** | The parent alpha maps 1:1 to a domain term that is universally used in the domain | Platform → "Internal Developer Platform" |
| **New Alpha** | A genuinely new root-level concern exists that is present in every implementation of this domain | A concern not covered by any parent alpha, even with domain-specific interpretation |
| **Redeclaration** | The parent alpha is correct but needs domain-specific states, checklists, or narratives | Platform alpha redeclared with IDP-specific maturity states |

**Alpha Instance structure** (in the baseline JSON):
```json
{
  "alphaInstances": [
    {
      "name": "Application Developer",
      "description": "Engineers who build and deploy applications on the platform",
      "alphaName": "Stakeholders"
    },
    {
      "name": "Platform Engineer",
      "description": "Engineers who build and maintain the platform itself",
      "alphaName": "Stakeholders"
    }
  ]
}
```

**Guidelines:**
- Instances are examples, not subdivisions — they show how the alpha manifests in practice
- Each instance references its parent alpha via `alphaName`
- Instances can be used for any alpha where the domain has well-known specific manifestations
- Document instances during Phase 1.5 distillation when mapping concerns to parent alphas

## Four-Phase Workflow

This skill orchestrates a 4-phase pipeline:

1. **Phase 1: Analysis** - Extract comprehensive methodology structure (~30-50K words)
2. **Phase 1.5: Distillation** - Identify essential elements and Focus areas (~15-25K words) **[NEW]**
3. **Phase 2: Baseline Mapping** - Map distilled essentials to baseline structures (~40-60K words)
4. **Phase 3: Baseline JSON** - Generate schema-compliant baseline practice JSON

**Output Location:** All files for a baseline are in `baselines/<baseline-name>/`:
- `01-analysis-report.md` - Phase 1 output
- `01.5-distilled-essentials.md` - Phase 1.5 output **(critical new phase)**
- `02-mapping-guide.md` - Phase 2 output
- `<baseline-name>.json` - Phase 3 output

## Critical Process Requirements

### Mandatory Planning Phase

**BEFORE executing any phase, you MUST:**

1. **Enter Plan Mode** using the EnterPlanMode tool
2. **Analyze source materials** to understand:
   - Domain scope and objectives
   - Natural concern clustering (for Focus identification)
   - Complexity and coverage
3. **Create execution roadmap**:
   - Confirm baseline creation approach (vs extension practice)
   - Estimate token requirements per phase
   - Identify potential custom Focuses (vs default Value/Solution/Endeavor)
4. **Exit Plan Mode** and present plan to user for approval

**Planning ensures:**
- Appropriate baseline vs extension practice decision
- Token budget management
- User alignment on scope and approach

### Baseline Dependency Resolution (Parent Baselines)

**When this step is needed:** When creating a baseline that extends one or more existing baselines (the new baseline will declare `baselinePracticeNames` in its output JSON).

**Process:**

1. **If user indicates this baseline extends other baseline(s):**
   - Ask for file path(s) of parent baseline(s)
   - The new baseline's JSON will declare these in `baselinePracticeNames`

2. **Check each parent for transitive dependencies:**
   ```bash
   python3 utils/resolve-baseline.py <parent-baseline.json> --check-only -o /dev/null
   ```
   If any parent has `baselinePracticeNames`, ask the user for those transitive dependency files. Continue until all roots are reached.

3. **Create effective parent baseline using the resolver utility:**
   ```bash
   python3 utils/resolve-baseline.py \
     <parent-baseline.json> \
     [<grandparent-1.json> ...] \
     -o baselines/<name>/_effective-parent-baseline.json
   ```
   The utility programmatically merges baselines in dependency order and applies `practiceElementAliases` as `_aliasContext` annotations with `_domainAlias` on each aliased element. If only one parent with no transitive dependencies, the utility copies it directly (alias annotations are still applied).

5. **Use effective parent baseline in all phases:**
   - **Phase 1.5:** Read effective parent to understand inherited elements and their domain terminology
   - **Phase 2:** Read effective parent to avoid duplicating elements and to use correct cross-references
   - **Phase 3:** Reference parent elements for cross-reference validation

**Merging semantics (overlay, name-keyed union):**
- Start with root baseline (no parents)
- Layer each child on top: child elements with same name override parent, new elements are added
- Metadata (name, description) comes from the leaf parent
- Result is the complete set of inherited elements this new baseline can reference

**CRITICAL:** The NEW baseline being created does NOT need to redeclare all parent elements. It can:
- Redeclare parent elements with domain-specific descriptions (override)
- Add entirely new elements not in any parent
- Reference parent elements in `relatesTo` without redeclaring them
- Define its own `practiceElementAliases` to rename inherited elements for its domain

The effective parent baseline provides the complete context for understanding what is inherited.

### Directory Structure

```
baselines/
└── <baseline-name>/
    ├── 01-analysis-report.md        # Phase 1 output (~30-50K words)
    ├── 01.5-distilled-essentials.md # Phase 1.5 output (~15-25K words)
    ├── 02-mapping-guide.md          # Phase 2 output (~40-60K words)
    └── <baseline-name>.json         # Phase 3 output (schema-compliant)
```

### Reference Documents Required

These documents must be readable for all phases:

1. **`references/domain-framework.md`** - Four-perspective analysis (Business, Technology, People, Process)
2. **`references/semantics.md`** - Practice Language semantic guidance
3. **`deps/language.schema.json`** - JSON Schema definition
4. **Optional parent baseline(s)** - If this baseline extends other baselines via `baselinePracticeNames` (see Baseline Dependency Resolution below)

## Phase 1: Analysis

**Objective:** Extract comprehensive methodology structure from source materials

**Prompt:** `prompts/phase-1-baseline-analysis.md`

**Process:**

1. **Load Reference Framework**
   ```
   Read references/domain-framework.md
   ```

2. **Read All Source Materials**
   - PDF documents
   - Web pages (via URLs)
   - Markdown files
   - Technical documentation

3. **Extract Elements** (using four-perspective framework):
   - **Outcomes** (3-8 primary objectives)
   - **Concerns** (5-15+ areas of attention) - extract comprehensively
   - **Progressive States** (5-7 maturity levels per concern)
   - **Work Products** (artifacts with 3-5 levels of detail)
   - **Activities** (5-15+ types of work) - extract comprehensively
   - **Competencies** (required expertise with levels)
   - **Personas** (roles combining competencies)
   - **Workflows** (common patterns and lifecycles)

4. **Emphasis on Universality**:
   - Prefer vendor-neutral terminology
   - Extract framework-level concepts
   - Document broadly applicable patterns

**Output:** `baselines/<name>/01-analysis-report.md` (~30-50K words)

**Validation:**
- ✓ All 4 perspectives represented
- ✓ 12 required sections present (skip Practice Hierarchy for baselines)
- ✓ Rich citations and source references
- ✓ Universal terminology preferred

## Phase 1.5: Distillation (CRITICAL NEW PHASE)

**Objective:** Distill Phase 1's comprehensive analysis into essential foundational elements

**Prompt:** `prompts/phase-1.5-baseline-distillation.md`

**Process:**

1. **Load Resources**
   ```
   Read baselines/<name>/01-analysis-report.md (Phase 1 output)
   Read references/domain-framework.md
   Read effective parent baseline (from Baseline Dependency Resolution, if this baseline extends others)
   ```
   If the effective parent has `_aliasContext`, review domain aliases to understand inherited elements by their domain-specific names.

2. **Identify Focus Areas** (2-4 high-level groupings):
   - Analyze Phase 1 concern patterns for natural clustering
   - Decide: **DEFAULT** (Value, Solution, Endeavor) OR **CUSTOM** focuses
   - Example custom: Partner Ecosystem → Value, Engagement, Go-to-Market
   - Document rationale for decision

3. **Distill Essential Concerns** (8-15 foundational concepts):
   - Review all Phase 1 concerns
   - Remove practice-specific concerns
   - Merge similar concerns to higher abstractions
   - Define universal progressive states (5-7 per concern)
   - Document relationships (produces, governed by, uses)
   - **When extending a parent baseline:** Map concerns against parent alphas to determine what is a redeclaration (with domain-specific content) vs. a genuinely new alpha
   - **Identify Alpha Instances:** Where a parent alpha is broad by design and has multiple well-known domain-specific manifestations, document these as Alpha Instances rather than creating new alphas or narrowing aliases

4. **Distill Activity Types** (6-12 execution boundaries):
   - Generalize Phase 1 activities to high-level work types
   - Map to essential concerns (contributesTo)
   - Identify required competencies

5. **Identify Universal Competencies** (5-10 skill categories):
   - Extract skill categories (not role titles)
   - Define 5-level progressions: Basic → Applies → Masters → Adapts → Innovating

6. **Identify Narrative Frameworks** (3-5 storytelling structures):
   - Universal frameworks (STAR, Hero's Journey, Three-Act, ABT)
   - Domain-specific frameworks (if source suggests)
   - Define narrative elements with howToUse guidance

**Output:** `baselines/<name>/01.5-distilled-essentials.md` (~15-25K words)

**This becomes the PRIMARY input for Phase 2.**

**Validation:**
- ✓ Focuses clearly defined (2-4 focus areas)
- ✓ Essential concerns distilled (8-15, not more than 15)
- ✓ Activity types generalized (6-12, not more than 12)
- ✓ Universal competencies identified (5-10 with 5 levels each)
- ✓ Narrative frameworks defined (3-5)
- ✓ All terminology is neutral, framework-level
- ✓ All elements are generally applicable

## Phase 2: Baseline Mapping

**Objective:** Map distilled essentials to baseline practice structures

**Prompt:** `prompts/phase-2-baseline-mapping.md`

**Process:**

1. **Load Resources**
   ```
   Read baselines/<name>/01.5-distilled-essentials.md (PRIMARY SOURCE)
   Read baselines/<name>/01-analysis-report.md (supporting detail)
   Read effective parent baseline (from Baseline Dependency Resolution, if this baseline extends others)
   Read references/semantics.md
   ```
   If the effective parent has `_aliasContext`, use domain aliases for semantic understanding of inherited elements. The new baseline's elements should use canonical names in structural references (`relatesTo`, etc.).

2. **Map Metadata**:
   - Name, description, version, authors, keywords
   - NO baselinePracticeName at root (use `baselinePracticeNames` array if extending other baselines)

3. **Use Identified Focuses** from Phase 1.5:
   - Validate focus coverage
   - Refine descriptions if needed

4. **Transform Essential Concerns → Alphas**:
   - NO `contributesTo` property (baseline alphas are root-level)
   - REQUIRED `relatesTo` arrays (from Phase 1.5 relationships)
   - 5-7 states per alpha with checklists
   - Assign to appropriate focus

5. **Transform Activity Types → ActivitySpaces**:
   - Each has `contributesTo` (points to alpha states)
   - Each has `requiredCompetencies`
   - Each assigned to a focus

6. **Transform Universal Competencies → Competencies**:
   - Each has exactly 5 competencyLevels
   - Level numbers: 1, 2, 3, 4, 5

7. **Transform Narrative Frameworks → NarrativeTypes**:
   - Each has 3-7 narrativeElements
   - Each element has name, description, howToUse

8. **Create Narratives** (using defined narrative types):
   - Baseline-level narrative (REQUIRED)
   - Alpha-level narratives (optional)
   - ActivitySpace narratives (optional)

9. **Map Citations** (using Citation Standard narrative type)

10. **Define Assets** (icons, diagrams, templates)

**Output:** `baselines/<name>/02-mapping-guide.md` (~40-60K words)

**Validation:**
- ✓ All Phase 1.5 elements transformed
- ✓ Alphas have NO contributesTo, ALL have relatesTo
- ✓ ActivitySpaces cover all alpha states
- ✓ All competencies have exactly 5 levels
- ✓ All narrative types have sequential elements
- ✓ Baseline-level narrative present
- ✓ All cross-references valid

## Phase 3: Baseline JSON Generation

**Objective:** Generate schema-compliant baseline practice JSON

**Prompt:** `prompts/phase-3-baseline-json.md`

**Process:**

1. **Load Resources**
   ```
   Read baselines/<name>/02-mapping-guide.md (PRIMARY SOURCE)
   Read deps/language.schema.json
   Read references/semantics.md
   ```

2. **Generate Baseline JSON Skeleton**:
   ```json
   {
     "kind": "practiceBaseline",
     "name": "...",
     "description": "...",
     "version": "1.0",
     "authors": [...],
     "keywords": [...]
   }
   ```

3. **Build Top-Level Arrays**:
   - **focuses** - From mapping guide (2-4 focuses)
   - **narrativeTypes** - With narrativeElements (3-5 types)
   - **competencies** - With competencyLevels (5 levels each)
   - **alphas** - With relatesTo (NO contributesTo), 5-7 states each
   - **activitySpaces** - With contributesTo and requiredCompetencies
   - **narratives** - With narrative contexts
   - **citations** - Using Citation Standard
   - **assets** - Icons, diagrams, templates

4. **Validate Cross-References**:
   - All focusName references exist in focuses
   - All relatesTo.alphaName references exist in alphas
   - All contributesTo.alphaName/stateName references exist
   - All requiredCompetencies references exist in competencies
   - All narrativeTypeName references exist in narrativeTypes

5. **Write Final JSON**:
   ```
   Write baselines/<name>/<name>.json
   ```

6. **Validate with Script**:
   ```bash
   # If extending parent baseline(s), pass effective parent for cross-reference validation:
   python3 utils/validate-baseline-json.py \
     baselines/<name>/<name>.json \
     baselines/<name>/_effective-parent-baseline.json \
     deps/language.schema.json

   # If standalone (no parents):
   python3 utils/validate-baseline-json.py \
     baselines/<name>/<name>.json \
     deps/language.schema.json
   ```

**Output:** `baselines/<name>/<name>.json` (schema-compliant)

**Validation:**
- ✓ `"kind": "practiceBaseline"` discriminator present
- ✓ Focuses, competencies, activitySpaces, narrativeTypes all defined
- ✓ Alphas have NO contributesTo, all have relatesTo
- ✓ All cross-references valid
- ✓ Validation script reports `"valid": true`
- ✓ 0 schema errors, 0 baseline errors, 0 integrity errors

## Token Budget Management

**Estimated Token Requirements:**

| Phase | Reading | Writing | Total |
|-------|---------|---------|-------|
| Phase 1 | ~20K | ~40K | ~60K |
| Phase 1.5 | ~50K | ~20K | ~70K |
| Phase 2 | ~80K | ~50K | ~130K |
| Phase 3 | ~50K | ~10K | ~60K |
| **Total** | **~200K** | **~120K** | **~320K** |

**Phase Compaction Pattern:**

After each phase completes:
1. **Clear conversation history** (compact context)
2. **Retain only essential artifacts**:
   - Current phase output file
   - Next phase prompt
   - Reference documents
3. **Restart next phase** with fresh context

**Instructions for Phase Transitions:**

After Phase 1:
```
Phase 1 complete. Output: baselines/<name>/01-analysis-report.md

Starting Phase 1.5 Distillation. Reading:
- Phase 1 analysis
- Domain framework
- Distillation prompt
```

After Phase 1.5:
```
Phase 1.5 complete. Output: baselines/<name>/01.5-distilled-essentials.md

Starting Phase 2 Mapping. Reading:
- Phase 1.5 distilled essentials (PRIMARY)
- Phase 1 analysis (supporting)
- Semantics
- Mapping prompt
```

After Phase 2:
```
Phase 2 complete. Output: baselines/<name>/02-mapping-guide.md

Starting Phase 3 JSON Generation. Reading:
- Phase 2 mapping guide
- Schema
- JSON prompt
```

## Baseline vs Extension Practice Decision

**Use this skill (create-baseline-method) when:**
- ✓ Creating a **foundational framework** for a domain
- ✓ Defining **root-level alphas** (no parent baseline to extend)
- ✓ Establishing **focuses, competencies, narrative types** for a domain
- ✓ Source methodology defines **universal ontology**

**Use /generate-method when:**
- ✓ Creating a **practice that extends** an existing baseline
- ✓ Defining **specialized alphas** with contributesTo
- ✓ Adding **activities, work products, patterns** (not in baselines)
- ✓ Source methodology is an **implementation** of a framework

**Examples:**

| Source | Use |
|--------|-----|
| Platform Adoption Essentials | create-baseline-method (foundational framework) |
| AWS Well-Architected (specific practices) | /generate-method (extends Platform Adoption baseline) |
| Partner Ecosystem Essentials | create-baseline-method (foundational framework) |
| Specific Partner Demand Gen practice | /generate-method (extends Partner Ecosystem baseline) |
| Team Topologies | create-baseline-method (foundational framework) |
| Specific SDLC practice | /generate-method (extends appropriate baseline) |

## Common Pitfalls

### Phase 1 Pitfalls

❌ **Over-filtering**: Extract comprehensively, don't pre-filter. Phase 1.5 distills.
❌ **Implementation details**: Focus on types of work, not tool-specific steps
❌ **Creating practice hierarchy**: Baselines are single cohesive frameworks
❌ **Role-focused competencies**: Extract skill categories, not job titles

### Phase 1.5 Pitfalls (NEW)

❌ **Too many essential concerns**: If >15, merge more aggressively
❌ **Practice-specific language**: "AWS Lambda" → "Serverless Compute"
❌ **Undefined relationships**: Document concern relationships explicitly
❌ **Unbalanced focuses**: One focus with 2 concerns, another with 10
❌ **Too many activity types**: If >12, generalize more
❌ **Missing state coverage**: Every concern state needs ≥1 activity type

### Phase 2 Pitfalls

❌ **Using Phase 1 directly**: Use Phase 1.5 distilled essentials (primary source)
❌ **Adding contributesTo to alphas**: Baseline alphas are root-level
❌ **Missing relatesTo**: All alphas should have inter-alpha relationships
❌ **Incomplete contributesTo coverage**: Every alpha state needs ≥1 activity space
❌ **Generic narratives**: Element mappings should be substantive

### Phase 3 Pitfalls

❌ **Missing discriminator**: Forgetting `"kind": "practiceBaseline"`
❌ **Adding contributesTo to alphas**: They're root-level in baselines
❌ **Empty relatesTo**: All alphas need relationships
❌ **Wrong competency level count**: Must be exactly 5 levels
❌ **Invalid cross-references**: All symbolic names must resolve
❌ **Trailing commas**: JSON doesn't allow trailing commas

## Quality Gates

### After Phase 1:
- [ ] 12 required sections present (skip Practice Hierarchy)
- [ ] All 4 perspectives represented
- [ ] Universal terminology preferred
- [ ] Rich citations and source references

### After Phase 1.5:
- [ ] 2-4 focuses defined with rationale
- [ ] 8-15 essential concerns distilled
- [ ] 6-12 activity types generalized
- [ ] 5-10 competencies with 5 levels
- [ ] 3-5 narrative frameworks
- [ ] Neutral, framework-level terminology

### After Phase 2:
- [ ] All Phase 1.5 elements mapped
- [ ] Alphas have NO contributesTo, all have relatesTo
- [ ] ActivitySpaces cover all alpha states
- [ ] All competencies have 5 levels
- [ ] Baseline-level narrative present
- [ ] All cross-references valid

### After Phase 3:
- [ ] Valid JSON syntax
- [ ] `"kind": "practiceBaseline"` present
- [ ] Focuses, competencies, activitySpaces, narrativeTypes defined
- [ ] Alphas have NO contributesTo, all have relatesTo
- [ ] Validation script: `"valid": true`
- [ ] 0 errors (schema, baseline, integrity)

## Success Criteria

✅ 4 files generated in `baselines/<name>/` directory
✅ All phase prompts followed exactly
✅ Phase 1.5 successfully identifies essential elements and Focuses
✅ Baseline JSON passes schema validation
✅ Baseline JSON passes internal integrity validation
✅ All cross-references resolve correctly
✅ Generated baseline can be used by /generate-method as parent baseline

## Deliverables

**Final Output Structure:**

```
baselines/<baseline-name>/
├── 01-analysis-report.md        # ~30-50K words
├── 01.5-distilled-essentials.md # ~15-25K words
├── 02-mapping-guide.md          # ~40-60K words
└── <baseline-name>.json         # Schema-compliant baseline JSON
```

**Validation:**

```bash
# Validate baseline JSON (standalone, no parents)
python3 utils/validate-baseline-json.py \
  baselines/<baseline-name>/<baseline-name>.json \
  deps/language.schema.json

# Validate baseline JSON (extending parent baselines)
python3 utils/validate-baseline-json.py \
  baselines/<baseline-name>/<baseline-name>.json \
  baselines/<baseline-name>/_effective-parent-baseline.json \
  deps/language.schema.json

# Expected output: {"valid": true, "errors": [], "warnings": []}
```

**Usage:**

Generated baseline can be referenced by extension practices:

```bash
# Create practice extending this baseline
/generate-method --baseline baselines/<baseline-name>/<baseline-name>.json <source-files>
```

## Skill Invocation

**Usage:**

```bash
/create-baseline-method <source-files-or-urls>
```

**Examples:**

```bash
# From local files
/create-baseline-method docs/partner-ecosystem-framework.pdf

# From URLs
/create-baseline-method https://teamtopologies.com/key-concepts

# From directory
/create-baseline-method methodologies/platform-adoption/

# With optional parent baseline
/create-baseline-method --parent deps/platform-adoption-kernel.json docs/specialized-framework.md
```

## Notes

- **Phase 1.5 is the critical new innovation** - it bridges the gap between comprehensive extraction (Phase 1) and focused baseline creation (Phase 2/3)
- **Focus identification in Phase 1.5** allows baselines to define custom groupings beyond default Value/Solution/Endeavor
- **Distillation in Phase 1.5** ensures baselines contain only universal, foundational elements suitable for broad reuse
- Generated baselines become the **foundation for extension practices** created with `/generate-method`
