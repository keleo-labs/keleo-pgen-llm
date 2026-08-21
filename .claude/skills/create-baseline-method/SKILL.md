# create-baseline-method Skill

## Metadata

**Name:** create-baseline-method
**Description:** Generate foundational baseline practice JSON from source methodology
**Trigger:** When user provides source methodology for baseline practice creation

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — these are prohibited; use reusable utils instead |
| Creating or extending a utility script | §7.4 — follow the Utils Self-Extension Protocol |
| Needing functionality that no existing util covers | §7.4 — create/extend, don't work around it |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |
| Writing prose rules that have a clear pass/fail criterion | §9 — convert to Gherkin scenarios instead |
| Adding or modifying Gherkin scenarios in any SKILL.md | §1–6 — rule structure, categories, and triple-duty |
| Adding a new validation check to assess/validate scripts | §7.2 — follow the Adding New Checks protocol |

**How to read:** `Read .claude/skills/SKILL-STANDARD.md` — then navigate to the relevant `## N.` heading.

---

## Overview

This skill automates the creation of **baseline practice JSON** files - foundational frameworks that define alphas, competencies, activity spaces, and narrative types for a domain. Baseline practices are extended by regular practices (created with `/generate-method`).

**Key Distinction:**
- **Baseline Practices** (this skill): Define foundational ontology (root alphas, alphaInstances, competencies, focuses, narrativeTypes, activitySpaces)
- **Extension Practices** (`/generate-method`): Specialize baselines with redeclarations, new alphas (with `contributesTo` or `mapsTo`), activities, workProducts, patterns

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
2. **Phase 1.5: Distillation** - Identify essential elements and Focus areas (~15-25K words) ****
3. **Phase 2: Baseline Mapping** - Map distilled essentials to baseline structures (~40-60K words)
4. **Phase 3: Baseline JSON** - Generate schema-compliant baseline practice JSON

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

**When this step is needed:** When creating a baseline that extends one or more existing baselines (the new baseline will declare `baselinePracticeNames` in its output JSON). This includes when the user explicitly states the baseline extends another, or when it is inferred from the source materials.

**Process:**

1. **Auto-discover parent baselines by name:**
   If the user indicates this baseline extends other baseline(s) (by providing a name or path):
   - If user provides a **name** (no `/`, doesn't end in `.json`), resolve it:
     ```bash
     python3 utils/discover-dependencies.py --resolve "Parent Baseline Name"
     ```
     - `found` → use the resolved path
     - `not_found` → ask user for the file path
     - `ambiguous` → present candidates to user

2. **Resolve transitive dependencies in a single step:**
   For each resolved parent baseline, check for transitive dependencies:
   ```bash
   python3 utils/discover-dependencies.py --resolve-from <parent-baseline.json> --transitive
   ```
   This scans `baselines/`, `practices/`, and `deps/` directories and recursively resolves all `baselinePracticeNames` in the chain. Ask user only for any `not_found` dependencies.

3. **Confirm all resolved dependencies with user:**
   Present ALL parent baselines and their transitive deps in a single summary:
   ```
   === Dependency Resolution ===

   Parent Baselines:
     1. [baselinePractice] "<parent-name>"
        Path: <resolved-path>
        Transitive:
          1a. [baselinePractice] "<grandparent-name>"
              Path: <resolved-path>

   All dependencies resolved. Please confirm or correct:
   - "ok" to proceed
   - "1=/correct/path.json" to correct a path
   ```
   **Wait for user confirmation before proceeding.**

4. **Create effective context using the unified resolver:**
   ```bash
   python3 utils/resolve-context.py \
     <parent-baseline.json> \
     [<grandparent-1.json> ...] \
     --transitive \
     -o baselines/<name>/_effective-context.json
   ```
   The utility classifies and merges all inputs in hierarchy order (root-first for baselines), stamps `_contributingPracticeName` on every element for provenance tracking, and applies `practiceElementAliases` as `_aliasContext` annotations. If a single baseline with no dependencies, it simply annotates the document.

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
    ├── <baseline-name>.json         # Phase 3 output (intermediate)
    # .keleo package output goes to bundles/<baseline-name>.keleo
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

**Phase 1 Validation:**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --phase 1 --summary
```
Fix any FAIL assertions before proceeding.

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

**Phase 1.5 Validation (run before proceeding to Phase 2):**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --phase 1.5 --summary
```
Fix any FAIL assertions before proceeding to Phase 2.

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
   - Optional `background` on states (use sparingly — practice layer adds detailed Gherkin; see semantics.md Section 5.3.5)

5. **Transform Activity Types → ActivitySpaces**:
   - Each has `contributesTo` (points to alpha states)
   - Each has `requiredCompetencies`
   - Each assigned to a focus
   - Optional `background` on activity spaces (shared prerequisites; use sparingly in baselines)

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

10. **Map Acknowledgements** (optional — recognize contributors, research groups, or supporting organizations that are not published sources)

11. **Define Assets** (icons, diagrams, templates)

**Output:** `baselines/<name>/02-mapping-guide.md` (~40-60K words)

**Phase 2 Validation:**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --phase 2 --summary
```
Fix any FAIL assertions before proceeding to Phase 3.

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

2. **Read schema and baseline metadata** using utility commands (never parse `$comment` manually):
   ```bash
   python3 utils/extract-reference-names.py deps/language.schema.json --metadata
   ```
   If extending a parent baseline, also extract its version:
   ```bash
   python3 utils/extract-reference-names.py <parent-baseline>.json --metadata
   ```

3. **Generate Baseline JSON Skeleton**:
   ```json
   {
     "kind": "practiceBaseline",
     "name": "...",
     "description": "...",
     "schemaVersion": "1.0.0",
     "version": "1.0.0",
     "authors": [...],
     "keywords": [...]
   }
   ```
   Set `schemaVersion` from the schema `$comment`. Set `version` to `"1.0.0"` (three-part semver). If extending a parent baseline (`baselinePracticeNames`), add `dependencyVersions` with caret range for each parent.

4. **Build Top-Level Arrays**:
   - **focuses** - From mapping guide (2-4 focuses)
   - **narrativeTypes** - With narrativeElements (3-5 types)
   - **competencies** - With competencyLevels (5 levels each)
   - **alphas** - With relatesTo (NO contributesTo), 5-7 states each
   - **activitySpaces** - With contributesTo and requiredCompetencies
   - **narratives** - With narrative contexts
   - **citations** - Using Citation Standard
   - **assets** - Icons, diagrams, templates

5. **Validate Cross-References**:
   - All focusName references exist in focuses
   - All relatesTo.alphaName references exist in alphas
   - All contributesTo.alphaName/stateName references exist
   - All requiredCompetencies references exist in competencies
   - All narrativeTypeName references exist in narrativeTypes
   - Element-specific narratives embedded on alphas/activitySpaces/competencies (NOT top-level)
   - All narratives have citationNames arrays referencing relevant citations
   - No narrative name or description references narrative type template names
   - Narrative contexts are self-contained — coherent without element headings (element names are authoring scaffolding, not shown to readers)

6. **Write Final JSON**:
   - Write ONE output file only — do NOT create intermediate fragment files (e.g., `_part1.json`). Write the complete JSON in a single Write call.
   - For asset definitions, copy the format of an existing asset entry (use `type`, `fontCharacter`, `fontFamily`, `fontWeight` — NOT `format` or `character`).
   ```
   Write baselines/<name>/<name>.json
   ```

7. **Auto-fix common issues before validation:**
   ```bash
   python3 utils/fix-common-issues.py baselines/<name>/<name>.json --fix --all
   ```

8. **Validate with Script**:
   ```bash
   # If extending parent baseline(s), pass effective parent for cross-reference validation:
   python3 utils/validate-baseline-json.py \
     baselines/<name>/<name>.json \
     baselines/<name>/_effective-context.json \
     deps/language.schema.json

   # If standalone (no parents):
   python3 utils/validate-baseline-json.py \
     baselines/<name>/<name>.json \
     deps/language.schema.json
   ```

**Output:** `baselines/<name>/<name>.json` (schema-compliant)

**Phase 3 Validation:**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --schema deps/language.schema.json --summary
```
For child baselines extending a parent:
```bash
python3 utils/eval-skill-output.py baselines/<name>/ \
  --parent <parent-baseline.json> --schema deps/language.schema.json --summary
```
Fix all FAIL assertions with `error` severity. Re-run until `error_pass_rate: 1.0`.

**Step 5: Package into .keleo**

After validation passes, package the baseline JSON into a `.keleo` archive. If the baseline has `baselinePracticeName` (extends a parent baseline), resolve transitive dependencies and include all parent baselines:
```bash
# Resolve dependencies (if baselinePracticeName is set):
python3 utils/discover-dependencies.py --resolve-from baselines/<name>/<name>.json --transitive

# Package with all dependencies in topological order (parent baselines first):
python3 utils/package-keleo.py \
  --name "<baseline-name>" \
  --version "1.0.0" \
  --description "<baseline description>" \
  --documents [<parent-baseline>.json] \
              baselines/<name>/<name>.json \
  -o bundles/<name>.keleo \
  --verify
```
Never use `_effective-context.json` as a document — it is a build artifact, not a distributable document.

**Output:** `bundles/<name>.keleo` (packaged baseline with dependencies, verified inline)

**Inspection and fix utilities (never use `python3 -c` or `bash -c`):**
- Discover dependency by name: `python3 utils/discover-dependencies.py --resolve "Practice Name"` (find file path by name)
- Resolve all dependencies: `python3 utils/discover-dependencies.py --resolve-from <file>.json --transitive` (extract and resolve all deps recursively)
- List available files: `python3 utils/discover-dependencies.py --list` (index all JSON files in baselines/, practices/, deps/)
- Top-level structure overview: `python3 utils/extract-reference-names.py <file>.json --structure`
- Structural inspection: `python3 utils/extract-reference-names.py <file>.json --sections focuses alphas activitySpaces competencies narrativeTypes --alpha-details`
- Errors-only assessment: `python3 utils/assess-practice.py <file>.json --errors-only`

## Token Budget Management

**Estimated Token Requirements:**

| Phase | Reading | Writing | Total |
|-------|---------|---------|-------|
| Phase 1 | ~20K | ~40K | ~60K |
| Phase 1.5 | ~50K | ~20K | ~70K |
| Phase 2 | ~80K | ~50K | ~130K |
| Phase 3 | ~50K | ~10K | ~60K |
| **Total** | **~200K** | **~120K** | **~320K** |

**Phase Compaction:** After each phase, compact context by clearing history and retaining only the current output, next prompt, and reference documents. For multi-practice methods, use the Agent tool for parallel execution.

## Feature: Baseline Structural Integrity

Validates that baseline JSON has correct shape, required top-level sections, and no practice-layer elements.

### Scenario: Baseline kind discriminator (@rule:structural-201)
- Given: Phase 3 generates a baseline JSON file
- When: The JSON is validated
- Then: The `kind` property is "practiceBaseline"

### Scenario: All required baseline sections present (@rule:structural-202)
- Given: Phase 3 generates a baseline JSON
- When: The JSON is validated
- Then: focuses, alphas, activitySpaces, competencies, and narrativeTypes arrays are present and non-empty

### Scenario: No practice-layer elements in baseline (@rule:structural-203)
- Given: A baseline practice is being generated
- When: Phase 3 produces the JSON
- Then: The JSON does NOT contain activities, workProducts, or patterns arrays with content
- And: These elements belong in extension practices, not baselines

### Scenario: Focus count within range (@rule:structural-204)
- Given: A baseline defines focus areas
- When: Phase 3 generates the JSON
- Then: The focuses array contains 2-4 focus definitions

### Scenario: Competency level count (@rule:structural-205)
- Given: A baseline defines competencies
- When: Phase 3 generates the JSON
- Then: Each competency has exactly 5 competencyLevels

### Scenario: NarrativeType element count (@rule:structural-206)
- Given: A baseline defines narrative types
- When: Phase 3 generates the JSON
- Then: Each narrativeType has 3-7 narrativeElements with name, description, and howToUse

## Feature: Baseline Alpha Semantics

Validates that baseline alphas are root-level with correct relationship structure.

### Scenario: No contributesTo on baseline alphas (@rule:semantic-201)
- Given: A baseline alpha is defined
- When: Phase 3 generates the JSON
- Then: The alpha does NOT have a `contributesTo` property
- And: Baseline alphas are root-level and relate to each other via `relatesTo`

### Scenario: All baseline alphas have relatesTo (@rule:semantic-202)
- Given: A baseline alpha is defined
- When: Phase 3 generates the JSON
- Then: The alpha has a non-empty `relatesTo` array showing inter-alpha relationships

### Scenario: relatesTo entries have direction (@rule:semantic-203)
- Given: A baseline alpha has relatesTo entries
- When: Phase 3 generates the JSON
- Then: Each relatesTo entry has `relationship`, `alphaName`, and `direction` (outgoing|incoming|mutual)

### Scenario: ActivitySpaces contribute to alpha states (@rule:semantic-204)
- Given: A baseline defines activitySpaces
- When: Phase 3 generates the JSON
- Then: Each activitySpace has a `contributesTo` array referencing alpha states
- And: Every non-initial alpha state is targeted by at least one activitySpace

### Scenario: Alpha state minimum for baselines (@rule:coverage-201)
- Given: A baseline alpha is defined
- When: Phase 3 generates the JSON
- Then: The alpha has 5-7 states representing progressive maturity

## Feature: Baseline Naming and Quality

Validates naming conventions and content quality for baseline elements.

### Scenario: Vendor-neutral terminology (@rule:naming-201)
- Given: Phase 1.5 distills essential concerns
- When: Concerns are named and described
- Then: Names use vendor-neutral, framework-level language
- And: Implementation-specific terms (product names, tool names) are generalized

### Scenario: Competency level names follow standard (@rule:naming-202)
- Given: A baseline defines competencies with levels
- When: Phase 3 generates the JSON
- Then: Level names follow the standard progression: Basic, Applies, Masters, Adapts, Innovating

### Scenario: Gherkin structures minimal in baselines (@rule:coverage-202)
- Given: A baseline practice is being generated
- When: Phase 3 produces the JSON
- Then: background, test, and examples properties are used sparingly
- And: Detailed Gherkin structure is deferred to the practice layer

## Feature: Baseline Process Compliance

Validates that the four-phase baseline pipeline is executed correctly.

### Scenario: Phase 1.5 distillation completed (@rule:process-201)
- Given: The four-phase baseline pipeline is being executed
- When: Phase 2 mapping begins
- Then: 01.5-distilled-essentials.md exists with 8-15 essential concerns and 2-4 focus areas

### Scenario: Distillation uses Phase 1 as input (@rule:process-202)
- Given: Phase 1.5 distillation begins
- When: The agent reads source materials
- Then: 01-analysis-report.md is the primary input, NOT the original source materials directly

### Scenario: Baseline validation run after generation (@rule:process-203)
- Given: Phase 3 has generated a baseline JSON
- When: The phase is marked complete
- Then: validate-baseline-json.py has been run with 0 schema errors
- And: assess-practice.py confirms 0 error-severity issues

## Common Pitfalls

### Phase 1 Pitfalls

❌ **Over-filtering**: Extract comprehensively, don't pre-filter. Phase 1.5 distills.
❌ **Implementation details**: Focus on types of work, not tool-specific steps
❌ **Creating practice hierarchy**: Baselines are single cohesive frameworks
❌ **Role-focused competencies**: Extract skill categories, not job titles
❌ **Citations missing URLs**: Every citation SHOULD have a `url` field — use user-provided URLs, official framework websites, DOI references (`https://doi.org/10.xxxx/xxxxx`) for academic works, or publisher catalog pages. Only omit when no stable public link exists. Never fabricate URLs.

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
❌ **Over-using Gherkin structures**: Baselines should keep background/test/examples minimal — the practice layer is the natural place for detailed Gherkin structure (semantics.md Section 5.3.5)

### Phase 3 Pitfalls

❌ **Missing discriminator**: Forgetting `"kind": "practiceBaseline"`
❌ **Adding contributesTo to alphas**: They're root-level in baselines
❌ **Empty relatesTo**: All alphas need relationships
❌ **Wrong competency level count**: Must be exactly 5 levels
❌ **Invalid cross-references**: All symbolic names must resolve
❌ **Trailing commas**: JSON doesn't allow trailing commas
❌ **Wrong background structure**: `background` must be an object with optional `given`, `alphaStates`, `workProductLevels` arrays — not a string or flat array

## Quality Gates

Run the full eval harness after each phase and at completion:

```bash
# Phase-specific validation (during workflow)
python3 utils/eval-skill-output.py baselines/<name>/ --phase <1|1.5|2|3> --summary

# Full validation (at completion)
python3 utils/eval-skill-output.py baselines/<name>/ --schema deps/language.schema.json --summary
```

**Success criteria:** `error_pass_rate: 1.0` on full validation. All 5 files generated in `baselines/<name>/`. Generated baseline usable by `/generate-method` as parent baseline.

## Skill Invocation

```bash
/create-baseline-method <source-files-or-urls>
```
