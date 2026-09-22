---
name: method-based-report
description: Generate plain English reports structured by practice/method narrative frameworks — audience sees domain insight, not Keleo internals
triggerPatterns:
  - "method.*report"
  - "practice.*report"
  - "report.*using"
  - "write.*report"
  - "generate.*report"
---

# Method-Based Report Skill

Generate a well-structured markdown report on a user-specified subject, using the narrative frameworks and domain knowledge from a Keleo practice, method, or baseline. The report reads as a standalone document for a general audience — no Keleo terminology, no schema references, no Practice Language jargon.

## Workflow Overview

**Step 1: Plan** → Identify practice context, subject, and report strategy
**Step 2: Load Context** → Resolve practice/method into effective context
**Step 3: Analyze & Select** → Extract domain knowledge and select narrative structures
**Step 4: Generate Report** → Write plain English report structured by narrative frameworks

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — these are prohibited; use reusable utils instead |
| Creating or extending a utility script | §7.4 — follow the Utils Self-Extension Protocol |
| Needing functionality that no existing util covers | §7.4 — create/extend, don't work around it |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |

---

## Critical Process: ALWAYS Use EnterPlanMode

**MANDATORY FIRST STEP:** Before generating any report, you MUST use EnterPlanMode to:

1. Identify the practice/method/baseline to use as the structural foundation
2. Clarify the subject/topic the report should cover
3. Determine the report's purpose and intended audience
4. Select narrative structure strategy
5. Create execution roadmap

**Do NOT proceed without planning.**

---

## Directory Structure

### Output Location

All generated reports go in `reports/`:

```text
reports/
└── <report-name>.md          (Generated report — plain English markdown)
```

Report filenames use kebab-case derived from the subject (e.g., `cloud-migration-readiness.md`, `team-topology-assessment.md`).

The `reports/` directory is git-ignored (contents only) — reports are ephemeral deliverables, not versioned artifacts.

---

## Execution Workflow

### Step 0: EnterPlanMode (REQUIRED)

**YOU MUST DO THIS FIRST.**

In plan mode:

1. **Identify the practice context**
   - The user must specify a practice, method, baseline, or `.keleo` bundle
   - Accept any of: `.keleo` path, `.json` path, practice name (resolved from `practices/`, `baselines/`, `deps/`, `bundles/`)
   - If ambiguous, ask the user to clarify

2. **Clarify the subject and purpose**
   - What is the report about? (the domain subject, not the practice itself)
   - Who is the audience? (default: general business/technical audience)
   - What is the report's purpose? (inform, assess, recommend, persuade)
   - What scope or angle should the report take?

3. **Preview the narrative strategy**
   - Note which narrative types are available from the baseline
   - Propose a primary narrative structure for the overall report
   - Propose any secondary structures for subsections
   - Confirm the approach with the user before proceeding

**ExitPlanMode** once the user approves the plan.

---

### Step 1: Load Practice Context

Use `resolve-context.py` to load the effective context. **Always pass all inputs in a single call** — the utility merges them with correct tier precedence.

```bash
# By file path (one or many)
python3 utils/resolve-context.py practices/crm-foundations/crm-foundations.json practices/meddpicc-qualification/meddpicc-qualification.json --transitive -o /tmp/report-context.json

# By document name (preferred — avoids path guessing and directory name mismatches)
python3 utils/resolve-context.py --by-name "CRM Foundations" "MEDDPICC Qualification" "User Stories" --transitive -o /tmp/report-context.json

# To see only specific element types (reduces output size for targeted extraction)
python3 utils/resolve-context.py --by-name "CRM Foundations" --transitive --extract personas alphas patterns -o /tmp/report-context.json

# To understand the output JSON structure
python3 utils/resolve-context.py --describe-output
```

**Name resolution:** `--by-name` uses the dependency index to find documents by their `name` field (not directory name). This eliminates trial-and-error path lookups — e.g., the user may type "CRM-Foundations" but the directory is `crm-foundations/` and the document name is "CRM Foundations".

**If a document is not found locally:** Download it from the remote bundle library:
```bash
python3 utils/studio-client.py --pull "<Document Name>"
```
Then re-run the `resolve-context.py` command. If `studio-client.py` reports an auth error, guide the user to run `python3 utils/studio-client.py --configure` to set or refresh their keleo-studio-gas credentials.

**Multi-practice reports:** When the report draws on multiple practices, pass all of them in one call. The merged effective context gives you all personas, alphas, activities, and patterns from all sources with provenance annotations (`_contributingPracticeName`) so you know which practice each element came from.

Read the output effective context JSON to extract:
- **Baseline**: The foundational framework (narrative types, focuses, alphas, competencies)
- **Practice/Method**: The specialized domain knowledge (alphas, states, activities, patterns, narratives, work products)

**Do not fork subagents to extract data from the effective context.** The JSON is already structured — use inspection utilities to extract specific element types:

```bash
# Document shape and metadata
python3 utils/extract-reference-names.py /tmp/report-context.json --metadata --structure

# Specific sections (alphas, activities, patterns, personas, citations, etc.)
python3 utils/extract-reference-names.py /tmp/report-context.json --sections alphas patterns personas

# Alpha details (states, checklists)
python3 utils/extract-reference-names.py /tmp/report-context.json --sections alphas --alpha-details

# Narrative types and placement
python3 utils/extract-reference-names.py /tmp/report-context.json --sections narrativeTypes --narrative-details

# Citation details (full metadata with URLs)
python3 utils/extract-reference-names.py /tmp/report-context.json --sections citations --citation-details

# Human-readable practice summary
python3 utils/practice-summary.py /tmp/report-context.json
```

**NEVER use inline `python3 -c` scripts** — the utilities above cover all inspection needs and produce structured, readable output.

---

### Step 2: Analyze Domain Knowledge & Select Narrative Structures

#### 2.1 Extract Domain Knowledge

From the effective context, build a mental model of:

1. **Core Concerns** (from alphas): What are the key things this practice cares about? What states do they progress through? These become the conceptual backbone of the report.

2. **Activities & Patterns** (from activities, patterns): What does the practice recommend doing? In what sequence or lifecycle? These inform the report's recommendations and process sections.

3. **Assessment Criteria** (from checklists, states, work products): How does the practice measure progress? These inform evaluation frameworks in the report.

4. **Existing Narratives** (from practice narratives): What stories has the practice already told about its elements? These provide domain-specific framing and context.

5. **Competencies** (from baseline competencies): What skills and capabilities does the domain require?

#### 2.2 Select Narrative Structures

Choose narrative structures from the baseline's `narrativeTypes` to organize the report. The selection should match the report's purpose:

| Report Purpose | Recommended Primary Structure | Good Secondary Structures |
|---|---|---|
| Formal assessment or analysis | Report Narrative | STAR (for examples), Crawl-Walk-Run (for maturity) |
| Thought leadership or position paper | Essay Narrative | Three-Act/StoryBrand (for framing) |
| Implementation guide or roadmap | Design-Build-Run-Optimize or SDLC | Crawl-Walk-Run (for phasing) |
| Case study or success story | STAR or Three-Act/StoryBrand | Hero's Journey (for transformation arc) |
| Maturity assessment | Crawl-Walk-Run | Report Narrative (for formal structure) |
| Innovation or experimentation | Build-Measure-Learn | PDCA (for iteration cycles) |
| Continuous improvement review | PDCA | Report Narrative (for findings) |

**Composing structures:** A report typically uses one primary structure for its top-level organization, with secondary structures shaping individual sections. For example, a Report Narrative overall structure might use STAR for case study sections and Crawl-Walk-Run to frame maturity recommendations.

#### 2.3 Map Narrative Elements to Report Sections

For each narrative type selected, map its `narrativeElements` to natural section headings. The section headings should be plain English — do NOT use the narrative element names as headings unless they happen to be natural (e.g., "Recommendations" is fine; "Act II: The Guide and the Plan" is not).

**Mapping examples:**

Report Narrative elements → plain headings:
- Executive Summary → "Executive Summary" (natural as-is)
- Introduction → "Introduction" or a subject-specific heading
- Methods → "Approach" or "How We Assessed This"
- Results and Findings → "Key Findings" or "What We Found"
- Discussion → "Analysis" or "What This Means"
- Recommendations → "Recommendations" or "Next Steps"

Essay Narrative elements → plain headings:
- Introduction → Subject-specific opening heading
- Defining Key Concepts → "Core Concepts" or domain-specific heading
- Presenting Evidence → "Evidence and Analysis" or domain-specific
- Conclusion → "Conclusion" or "The Way Forward"

STAR elements → plain headings (for a section, not the whole report):
- Situation → "Background" or "The Challenge"
- Task → "Objectives" or "What Was Needed"
- Action → "What Was Done" or domain-specific
- Result → "Outcomes" or "Impact"

#### 2.4 Build Citation Pool

Extract citations from the effective context to support claims and recommendations in the report. These are the original source documents cited by the practice — methodology papers, technical guides, vendor documentation, research — not references to the practice itself.

**Step 1 — Collect candidates:** Read the `citations` array from the effective context. Each citation has `name`, `authors` (array), `date`, `source`, and optional `url`.

**Step 2 — Filter for relevance:** Not every citation in the practice belongs in the report. Include a citation when:
- It is referenced by `citationNames` on a narrative attached to an alpha, activity, or element that the report covers
- Its `name` or `description` is directly relevant to the report's subject matter
- It supports a specific claim, recommendation, or framework reference in the report

Aim for **5–15 citations** in a standard report. Fewer is fine for focused topics; more is acceptable for comprehensive analyses. Do not pad the list with tangentially relevant citations.

**Step 3 — Format for APA 7:** Build a lookup from citation name to formatted reference. Use these rules to convert the citation fields:

| Citation field | APA 7 usage |
|---|---|
| `authors` | Author names. Corporate/organizational names stay as-is (e.g., "Red Hat", "Dell Technologies"). Personal names use surname-first format: `Surname, A. A.` |
| `date` | Extract the 4-digit year from strings like `"2024"`, `"December 2023"`, `"April 2026"` |
| `name` | Work title — italicized in the reference entry |
| `source` | Publisher or site name |
| `url` | Appended to the reference entry when present |

**In-text shorthand** (used when writing the report):
- Single personal author: `(Surname, 2024)`
- Two personal authors: `(Surname & Surname, 2024)`
- Three or more personal authors: `(Surname et al., 2024)`
- Corporate author: `(Organization Name, 2024)`
- Narrative form: `Surname (2024) found that...` or `According to Organization Name (2024),...`

**Full reference format** (used in the References section):
```
Surname, A. A. (Year). *Title of work*. Source. URL
Organization Name. (Year). *Title of work*. URL
```

---

### Step 3: Generate the Report

Write the report as a single markdown file. Follow these principles:

#### 3.1 Voice and Tone

- Write in clear, professional English appropriate to the audience
- Use active voice and concrete language
- Avoid jargon, acronyms, and technical terms without explanation
- NO references to Keleo, Practice Language, alphas, states, activity spaces, work products, narrative types, baselines, or any schema constructs
- The practice provides the *structure and knowledge* — it should be invisible in the output

#### 3.2 Content Sourcing

The practice/method provides the **analytical framework** — the structured way of thinking about the subject. The report's actual content should be about the user's specified subject, informed by:

- **Alpha concerns** → translated into the key dimensions or considerations for the subject
- **State progressions** → translated into maturity levels, stages, or phases
- **Activities** → translated into recommended actions, steps, or approaches
- **Checklists** → translated into evaluation criteria or readiness indicators
- **Work products** → translated into deliverables or evidence of progress
- **Patterns** → translated into recommended sequences or lifecycle approaches
- **Existing narratives on elements** → used as domain context and framing inspiration
- **Competencies** → translated into skills or capability requirements
- **Citations** → used as APA 7 in-text references to support factual claims, technical recommendations, and framework references (see §3.6)

#### 3.3 Structure

```markdown
# <Report Title>

<Optional subtitle or date line>

<Primary narrative structure drives top-level sections>

## <Section derived from narrative element 1>

<Content informed by relevant practice knowledge>

## <Section derived from narrative element 2>

...

## <Final section>

## References

<APA 7 formatted entries, alphabetical by first author surname>

---

*<Optional: brief note on the analytical framework used, e.g., "This report was structured using the [Practice Name] framework.")*
```

Rules:
- The report title should be descriptive and subject-focused
- Sections flow from the selected narrative structure
- Each section draws on relevant practice domain knowledge translated into plain language
- Use subsections (###) where depth is needed
- Include concrete examples, criteria, or recommendations where the practice provides them
- End with actionable content (recommendations, next steps, or conclusions) appropriate to the narrative structure

#### 3.4 Length and Depth

Scale the report to the subject complexity:
- **Focused topic**: 1,500–3,000 words (5–8 minute read)
- **Broad assessment**: 3,000–6,000 words (10–20 minute read)
- **Comprehensive analysis**: 6,000–10,000 words (20–30 minute read)

Default to the middle range unless the user specifies otherwise.

#### 3.5 Output

Write the report to `reports/<report-name>.md` using the Write tool.

Tell the user:
1. Where the report was saved
2. Which practice/method provided the analytical framework
3. Which narrative structure(s) shaped the report
4. Total word count and citation count

#### 3.6 Citations and References

**In-text citations** support the report's credibility by linking claims and recommendations to their source documents. Use APA 7 parenthetical format:

- Place the citation at the end of the relevant sentence or paragraph, before the period: `...reducing provisioning time by 80% (Red Hat, 2025).`
- Use narrative form when the source is the subject: `According to Dell Technologies (2024), the recommended architecture uses...`
- When multiple citations support the same point: `(Red Hat, 2025; Dell Technologies, 2024)`

**What to cite:**
- Specific factual claims, statistics, or benchmarks
- Technical recommendations or best practices attributed to a source
- Framework descriptions or methodology references
- Architecture patterns or design decisions from vendor documentation

**What not to cite:**
- General knowledge or widely accepted facts
- Your own analysis, synthesis, or recommendations (these are the report's original contribution)
- Every sentence — aim for natural density, not exhaustive attribution

**Density:** 5–15 in-text citations for a standard report. A focused report on a single practice may use 5–8; a comprehensive multi-practice analysis may use 10–15.

**References section:** After the final content section and before the optional framework attribution, include a `## References` section listing every cited source in full APA 7 format, alphabetized by first author surname:

```markdown
## References

Dell Technologies. (2024). *Red Hat OpenShift Virtualization with Dell PowerFlex*. Dell Technologies. https://infohub.delltechnologies.com/...

Red Hat. (2025). *OpenShift Security Best Practices for Kubernetes Cluster Design*. Red Hat Blog. https://www.redhat.com/en/blog/...

Surname, A. A., & Surname, B. B. (2023). *Title of the work*. Publisher Name. https://example.com/...
```

**Only include references that were actually cited in the text.** The References section is not a bibliography — every entry must have a corresponding in-text citation.

---

## Feature: Narrative Structure Transparency

### Scenario: Report hides Keleo internals from reader (@rule:report-600)
- Given: a report is generated from a practice or method
- When: the report content is reviewed
- Then: no Keleo-specific terms appear (alpha, state, activitySpace, workProduct, narrativeType, baseline, contributesTo, mapsTo, relatesTo, checklist item, level of detail, practice language)
- And: the report reads as a standalone document requiring no Keleo knowledge

### Scenario: Narrative structure drives report organization (@rule:report-601)
- Given: a narrative type is selected from the baseline
- When: the report sections are created
- Then: each top-level section maps to a narrative element from the selected type
- And: section headings are plain English (not raw narrative element names unless naturally appropriate)

### Scenario: Practice knowledge informs report content (@rule:report-602)
- Given: a practice or method provides domain knowledge
- When: report content is written
- Then: the analytical framework from the practice shapes the report's dimensions, criteria, and recommendations
- And: practice concepts are translated into plain language appropriate to the audience

### Scenario: Report attribution is minimal and optional (@rule:report-603)
- Given: a report is generated
- When: the report is finalized
- Then: at most one brief line at the end attributes the analytical framework
- And: no structural diagrams, schema references, or methodology deep-dives are included

---

## Feature: Context Resolution

### Scenario: Practice context loads successfully (@rule:report-604)
- Given: the user specifies a practice, method, baseline, or .keleo bundle
- When: resolve-context.py runs with --transitive
- Then: the effective context JSON contains the baseline narrative types
- And: the practice/method domain knowledge is accessible

### Scenario: Missing context fails gracefully (@rule:report-605)
- Given: the user specifies a practice that cannot be resolved
- When: context resolution fails
- Then: the skill reports the error clearly
- And: suggests how the user can provide valid input (path to .json or .keleo file)

---

## Feature: Citations and References

### Scenario: Report includes in-text citations in APA 7 format (@rule:report-606)
- Given: the effective context contains citations relevant to the report subject
- When: the report makes factual claims, technical recommendations, or framework references
- Then: those claims are supported by APA 7 parenthetical citations (Author, Year)
- And: 5–15 citations appear in a standard report
- And: citations are placed at the end of the relevant sentence, before the period

### Scenario: Report ends with a References section (@rule:report-607)
- Given: the report contains in-text citations
- When: the report is finalized
- Then: a "## References" section appears after the final content section
- And: every in-text citation has a corresponding full reference entry
- And: entries are in APA 7 format: `Author. (Year). *Title*. Source. URL`
- And: entries are alphabetized by first author surname

### Scenario: References are source documents, not practice metadata (@rule:report-608)
- Given: citations are selected from the effective context
- When: the citation pool is built
- Then: citations reference the original source documents (methodology papers, vendor documentation, technical guides)
- And: no citations reference the Keleo practice, method, or baseline itself

---

## Multi-Source Reports

When a report draws on multiple practices, methods, or baselines:

1. **Single context call:** Pass all sources to `resolve-context.py` in one invocation (with `--by-name` or file paths). The merged context preserves provenance via `_contributingPracticeName` on each element.

2. **Persona cross-referencing:** Different practices may define personas for the same real-world role under different names (e.g., "Sales Representative" in CRM, "Account Executive" in MEDDPICC, "Field Seller" in Sales Play). Cross-reference persona names against the user's target roles during planning — document the mapping in the plan.

3. **No forking for extraction:** The merged effective context JSON contains all elements at the top level (personas, alphas, activities, patterns, etc.). Read the data directly — do not spawn subagents for data that is already structured in the JSON.

4. **External reference documents:** When the user provides Google Docs URLs as supplementary context, use `gws drive files export` to fetch them as plain text (see memory `gws-cli`). Write the export to a file within the current working directory (gws sandboxes output paths). Clean up the file after use.

---

## Post-Completion

After generating the report, perform the Post-Completion Review per SKILL-STANDARD.md §11.
