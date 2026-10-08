# Report Foundation

Common workflow, rules, and conventions shared by all reporting skills. **Load lazily** — read only the section you need at the step that needs it.

---

## Report Workspace (Step 0)

Every report owns a directory under `reports/`, mirroring how a practice owns `practices/<name>/`. Everything the report produces lives inside it:

```
reports/<report-slug>/
  00-prompt-history.md        Session provenance (see Session Provenance below)
  <report-slug>.md            The report
  <report-slug>.pdf           Exports, when produced
  .published-docs.json        Google Doc republish state, written by publish-doc.py
  assets/
    <name>.json               Diagram spec
    <name>.svg                Rendered diagram
```

The slug is kebab-case, derived from the report title, and names both the directory and the markdown file inside it. Create the directory at Step 0, before any content is written.

Diagram embeds are relative to the markdown — `![alt](assets/<name>.svg)` — so the whole directory can be moved, copied, or handed over intact.

---

## Session Provenance (Step 0 → close)

Every reporting run records how the report came to exist: the prompt behind it, the practice context that framed it, the narrative decision taken, and what was produced. Use `utils/prompt-history.py` — the same utility the generation skills use — against the report directory.

**Initialise immediately after ExitPlanMode:**

```bash
python3 utils/prompt-history.py reports/<report-slug>/ --init \
  --type report --name "<Report Title>" --prompt "<user's original prompt text>"
```

Then record each source identified during planning:

```bash
python3 utils/prompt-history.py reports/<report-slug>/ --add-source \
  --source-type <file|url|google-doc|google-slides> \
  --source-path "<path or URL>" --source-desc "<brief description>"
```

**`--init` activates the prompt-history hooks.** From this point until `--finalize`, every user turn and every `AskUserQuestion` exchange in the session is appended to the Interaction Log automatically. You DO need to record, manually, any question you put to the user in plain prose, because the hook captures only the answer:

```bash
python3 utils/prompt-history.py reports/<report-slug>/ --add-interaction \
  --interaction-label "<context, e.g. 'Practice selection'>" \
  --interaction-question "<the question you asked>" \
  --interaction-answer "<the user's reply, verbatim>"
```

Resuming a report in a later session re-arms the hooks: `python3 utils/prompt-history.py reports/<report-slug>/ --activate`

**Through Steps 1–3:**

| When | Call |
|---|---|
| Each practice, method, or baseline resolved (Step 1) | `--add-dependency --dep-type <practice\|method\|baseline> --dep-name "<name>" --dep-path "<resolved path>" --dep-version "<version>"` |
| Practice selection and narrative strategy settled (Steps 0, 2) | `--add-decision --decision-label "<Practice Selection\|Narrative Strategy>" --decision-text "<what was chosen and why>"` |
| Entering and leaving each step | `--start-phase --phase "Step N: <name>"` / `--end-phase --phase "Step N: <name>" --phase-output "<file>"` |
| Each artifact produced (markdown, PDF, published Doc URL) | `--add-deliverable --deliverable-path "<path or URL>" --deliverable-desc "<what it is>"` |
| The report is handed over | `--finalize` |

Record the dependency version from the resolved document's `version` field — `extract-reference-names.py <context>.json --metadata` reports it.

---

## Context Resolution (Step 1)

Use `resolve-context.py` to load the effective context. The `--transitive` flag resolves both practice dependencies (`practiceDependencyNames`) and baseline dependencies automatically.

**Baseline-aware resolution:** When multiple practices are involved, check whether they share the same root baseline before resolving:

- **Same root baseline** → pass all practices in a single `resolve-context.py` call. The merged effective context gives you all elements with provenance annotations (`_contributingPracticeName`).
- **Different root baselines** → create separate effective-context.json files, one per distinct root baseline group. Merging practices with different baselines conflates incompatible baseline elements (focuses, narrative types, competencies, activity spaces).

```bash
# Single practice (resolves its dependencies and baseline transitively)
python3 utils/resolve-context.py --by-name "CRM Foundations" --transitive -o /tmp/report-context.json

# Multiple practices sharing the same baseline — single call
python3 utils/resolve-context.py --by-name "CRM Foundations" "MEDDPICC Qualification" --transitive -o /tmp/report-context.json

# Multiple practices with different baselines — separate calls
python3 utils/resolve-context.py --by-name "Practice A" --transitive -o /tmp/primary-context.json
python3 utils/resolve-context.py --by-name "Practice B" --transitive -o /tmp/supplementary-context.json

# To see only specific element types (reduces output size for targeted extraction)
python3 utils/resolve-context.py --by-name "CRM Foundations" --transitive --extract personas alphas patterns -o /tmp/report-context.json

# To understand the output JSON structure
python3 utils/resolve-context.py --describe-output
```

**Checking root baselines:** Use `discover-dependencies.py` to inspect a practice's baseline before resolving:
```bash
python3 utils/discover-dependencies.py --resolve-from <practice>.json
```

**Name resolution:** `--by-name` uses the dependency index to find documents by their `name` field (not directory name). This eliminates trial-and-error path lookups — e.g., the user may type "CRM-Foundations" but the directory is `crm-foundations/` and the document name is "CRM Foundations".

**If a document is not found locally:** Download it from the remote bundle library:
```bash
python3 utils/studio-client.py --pull "<Document Name>"
```
Then re-run the `resolve-context.py` command. If `studio-client.py` reports an auth error, guide the user to run `python3 utils/studio-client.py --configure` to set or refresh their keleo-studio-gas credentials.

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

## Domain Knowledge Extraction (Step 2)

From the effective context, build a mental model of:

1. **Core Concerns** (from alphas): What are the key things this practice cares about? What states do they progress through? These become the conceptual backbone of the report.

2. **Activities & Patterns** (from activities, patterns): What does the practice recommend doing? In what sequence or lifecycle? These inform the report's recommendations and process sections.

3. **Assessment Criteria** (from checklists, states, work products): How does the practice measure progress? These inform evaluation frameworks in the report.

4. **Existing Narratives** (from practice narratives): What stories has the practice already told about its elements? These provide domain-specific framing and context.

5. **Competencies** (from baseline competencies): What skills and capabilities does the domain require?

6. **Figure candidates** (from the relationship graph): Run `python3 utils/derive-diagram.py <context>.json --list`. It reports the focuses, the alphas ranked by relationship count, the patterns and their phase sequence, and the work products — which sections will carry which figure is decided here, not at write-time. See the Diagrams section below.

---

## Citation Pool (Step 2)

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

When the citation has a `url`, wrap the citation text in a markdown hyperlink. When it does not, use plain text.

| Form | With URL | Without URL |
|---|---|---|
| Single personal author | `([Surname, 2024](URL))` | `(Surname, 2024)` |
| Two personal authors | `([Surname & Surname, 2024](URL))` | `(Surname & Surname, 2024)` |
| Three or more | `([Surname et al., 2024](URL))` | `(Surname et al., 2024)` |
| Corporate author | `([Organization Name, 2024](URL))` | `(Organization Name, 2024)` |
| Narrative form | `[Surname (2024)](URL) found that...` | `Surname (2024) found that...` |
| Multiple sources | `([Red Hat, 2025](URL1); [Dell, 2024](URL2))` | `(Red Hat, 2025; Dell, 2024)` |

**Full reference format** (used in the References section):
```
Surname, A. A. (Year). *Title of work*. Source. URL
Organization Name. (Year). *Title of work*. URL
```

---

## Voice and Tone (Step 3)

- Write in clear, professional English appropriate to the audience
- Use active voice and concrete language
- Avoid jargon, acronyms, and technical terms without explanation
- NO references to Keleo, Practice Language, alphas, states, activity spaces, work products, narrative types, baselines, or any schema constructs
- The practice provides the *structure and knowledge* — it should be invisible in the output

### Register

Four rules on how the report sounds. They govern the deliverable, not these instructions, and they
apply equally to decks built from the report — `deck-foundation/slide-grammar.md` §5 carries the
same four with slide-specific examples. Verify with `python3 utils/lint-report.py <report>.md
--checks tone` (@rule:report-619).

**Decisions belong to people.** A variable is an input to a choice, never the maker of one.
Distance does not pick an architecture; an architect weighs distance and picks one. The verb is
only wrong when its subject is a thing — "the platform team decides the update window" is correct.

| Instead of | Write |
|---|---|
| Distance and tolerable loss pick the design | Site separation and recovery point objective are the primary inputs to the design choice |
| Rehearsal decides whether any of it works | Rehearsal establishes whether the mechanism performs as designed |

**Headings state their subject.** No rhetorical or contrarian construction — `X, not Y`,
`Why X fails`, `The two things that matter`. A heading can assert strongly and still be plain:
"Three viable disaster recovery designs", not "Three designs are viable, not one".

**Frame problems pragmatically.** Describe what has to be satisfied, not who was naive. *Well
understood*, *works on paper*, *in the real world*, *breaks the assumption* and *the hard part*
editorialise about the reader's competence and give an architect nothing to act on. Write
"Combining them introduces prerequisites that each approach must satisfy independently", not
"Combining them is where designs that work on paper start to fail".

**Use the domain's terminology.** Prefer the industry term to the shorthand — *site isolation
boundary* over *the gap*, *synchronous metro replication* over *metro sync*, *external dependency
management* over *the air gap problem*. Shorthand is fine once the term has been established.

---

## Content Sourcing (Step 3)

The practice/method provides the **analytical framework** — the structured way of thinking about the subject. The report's actual content should be about the user's specified subject, informed by:

- **Alpha concerns** → translated into the key dimensions or considerations for the subject
- **State progressions** → translated into maturity levels, stages, or phases
- **Activities** → translated into recommended actions, steps, or approaches
- **Checklists** → translated into evaluation criteria or readiness indicators
- **Work products** → translated into deliverables or evidence of progress
- **Patterns** → translated into recommended sequences or lifecycle approaches
- **Existing narratives on elements** → used as domain context and framing inspiration
- **Competencies** → translated into skills or capability requirements
- **Citations** → used as APA 7 in-text references to support factual claims, technical recommendations, and framework references (see Citations in Reports below)

---

## Diagrams (Steps 2–3)

Where a report needs a visual, it is a **rendered SVG** — never ASCII art, never hand-written SVG
geometry. Eight layouts are available (`flow`, `stack`, `timeline`, `hub`, `matrix`, `wardley`,
`swimlane`, `canvas`), plus Mermaid-backed specs for C4, sequence, ERD and state diagrams.

Much of a report's figure set can be **derived from the practice** rather than invented — its alpha
relationships, specialisation tree, pattern phases, state progressions and work-product coverage are
already a graph. Pick the figures at Step 2, while the domain knowledge is in front of you:

```bash
# What this context can yield: focuses, alphas by relationship count, patterns, work products
python3 utils/derive-diagram.py /tmp/report-context.json --list

# Derive a spec, scoped. Then edit it — a derived spec is a starting point, not an output
python3 utils/derive-diagram.py /tmp/report-context.json --view concern-hub \
  --seed "<Alpha>" --out-dir reports/<report-slug>/assets/ --name <diagram-slug>

# Render every spec in one call, then look at the result
python3 utils/render-diagram.py --dir reports/<report-slug>/assets/
python3 utils/preview-diagram.py --report reports/<report-slug>/<report-slug>.md
python3 utils/render-diagram.py --spec-help    # full spec field reference
```

Embed with a relative path, alt text that carries the diagram's claim, and a numbered caption
giving the spec's `title` — the SVG does not draw its own title, so without the caption the figure
reaches the reader unnamed:

```markdown
![Option A: controller-centric scheduled remediation topology](assets/option-a-topology.svg)

*Figure 1 — Option A: controller-centric scheduled remediation*
```

Read `reporting-foundation/diagram-guide.md` for layout and method selection, how many figures a
report should carry, deriving them from the practice graph, drawing a subject's **instances** rather
than the practice's types (a platform with DR has two platforms), and how to write a good spec.
Verify with `python3 utils/lint-report.py <report>.md --checks diagrams`.

---

## Report Structure (Step 3)

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

*Structured using the [<Practice Name>](<studio deep link>) framework.*
```

Rules:
- The report title should be descriptive and subject-focused
- Sections flow from the selected narrative structure
- Each section draws on relevant practice domain knowledge translated into plain language
- Use subsections (###) where depth is needed
- **Frame a section before presenting its parts** — see below
- Include concrete examples, criteria, or recommendations where the practice provides them
- End with actionable content (recommendations, next steps, or conclusions) appropriate to the narrative structure

### Frame a section before its parts

A `##` section whose first content is a `###` subsection, a table or a figure opens with **two to
four sentences of framing** before that element. Without it the reader arrives at `### Option A`
with no idea that B and C exist, why there are three, or what distinguishes them.

The framing says what the section covers, why it is divided the way it is, and what separates the
parts. Where the parts are a **parallel set** — options, phases, workstreams, tiers, perspectives
— it names the set size and gives each member a one-line role:

```markdown
## Architecture options

Three designs are viable, and they differ in what they trade against recovery point.
Option A removes data loss entirely but caps how far apart the sites can sit. Option B
accepts minutes of loss in exchange for unlimited distance. Option C gives up speed for
a fraction of the cost and the only protection against a mistake rather than a failure.

### Option A: metro synchronous, active-active
```

Two failure modes to avoid. The framing must not **restate the heading** ("This section sets out
the architecture options"), and it must not merely **announce** that the section is beginning. The
test: a reader who stops after the framing should be able to say what the section concluded.

A section that opens with prose usually frames itself already — the gap appears specifically where
a structure follows the heading directly, because the structure is what the heading promised.
Verify with `python3 utils/lint-report.py <report>.md --checks sections`.

---

## Framework Attribution (Step 3)

The report closes with a single italic line naming every practice, method, or baseline that shaped it. **Each name is a hyperlink into keleo-studio-gas** so a reader can open the framework itself — a bare name is a dead end for anyone who wants to look it up.

Generate the line rather than writing it by hand. Pass the document names in the order they should read — primary context first, supplementary contexts after:

```bash
python3 utils/studio-client.py --link "Platform Operations" "HPE OpenShift" --attribution
```

This emits the finished line, ready to paste as the last line of the report:

```markdown
*Structured using the [Platform Operations](<deep link>) and [HPE OpenShift](<deep link>) frameworks.*
```

Notes:
- Use the **document `name`** (the `name` field of the practice/method/baseline JSON), not the directory or bundle slug. Deep links resolve on exact document name.
- Names are checked against the remote document index. A name reported as `NOT PUBLISHED` has no page to link to — either push the bundle (`--push`) or drop that name from the attribution.
- If the remote is unreachable or the API token has expired, the links are still generated and marked `unverified`; that is fine for the report, but the warning is worth repeating to the user. A refreshed token goes in with `python3 utils/studio-client.py --configure --token <token>`.
- If keleo-studio-gas is not configured, fall back to plain names and tell the user that `python3 utils/studio-client.py --configure` would make the attribution clickable.
- Verify with `python3 utils/lint-report.py <report>.md --checks attribution`, which fails on any framework name left unlinked.

---

## Length and Depth (Step 3)

Scale the report to the subject complexity:
- **Focused topic**: 1,500–3,000 words (5–8 minute read)
- **Broad assessment**: 3,000–6,000 words (10–20 minute read)
- **Comprehensive analysis**: 6,000–10,000 words (20–30 minute read)

Default to the middle range unless the user specifies otherwise.

---

## Output (Step 3)

Write the report to `reports/<report-slug>/<report-slug>.md` using the Write tool, in the workspace created at Step 0.

Then close the session provenance: record the markdown (and any PDF or published Doc URL) with `--add-deliverable`, and `--finalize`.

Tell the user:
1. The report directory, and what is in it
2. Which practice/method provided the analytical framework
3. Which narrative structure(s) shaped the report
4. Total word count and citation count

---

## Citations in Reports (Step 3)

**In-text citations** support the report's credibility by linking claims and recommendations to their source documents. Use APA 7 parenthetical format, with markdown hyperlinks when the citation has a URL:

- Place the citation at the end of the relevant sentence or paragraph, before the period: `...reducing provisioning time by 80% ([Red Hat, 2025](https://www.redhat.com/...)).`
- Use narrative form when the source is the subject: `According to [Dell Technologies (2024)](https://infohub.delltechnologies.com/...), the recommended architecture uses...`
- When multiple citations support the same point: `([Red Hat, 2025](https://...); [Dell Technologies, 2024](https://...))`
- Citations without a URL remain plain text: `(Surname, 2024)`

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

## Multi-Source Reports

When a report draws on multiple practices, methods, or baselines:

1. **Group by root baseline:** Check each practice's `baselinePracticeName`. Practices sharing the same root baseline go in a single `resolve-context.py` call; practices with different root baselines get separate calls (see Context Resolution above). Each call produces its own effective-context.json.

2. **Persona cross-referencing:** Different practices may define personas for the same real-world role under different names (e.g., "Sales Representative" in CRM, "Account Executive" in MEDDPICC, "Field Seller" in Sales Play). Cross-reference persona names against the user's target roles during planning — document the mapping in the plan.

3. **No forking for extraction:** Each effective context JSON contains all elements at the top level (personas, alphas, activities, patterns, etc.). Read the data directly — do not spawn subagents for data that is already structured in the JSON.

4. **External reference documents:** When the user provides Google Workspace URLs as supplementary context:
   - **Google Docs:** Use `gws drive files export` to fetch as plain text. Write the export to a file within the current working directory (gws sandboxes output paths). Clean up after use.
   - **Google Slides:** Use `python3 utils/extract-gws-slides.py <presentation-id> -o /tmp/slides-content.md` to extract slide content as structured markdown. The presentation ID is the long alphanumeric string in the URL path.

### Primary + Supplementary Contexts

When a report uses a primary practice/method for structure and supplementary practices for depth:

1. **Primary drives structure** — the primary context's narrative types and alphas shape the report's organisation.
2. **Supplementary enriches** — supplementary contexts add technical depth, additional activities, and finer-grained state progressions within specific sections.
3. **Extract per-topic domain knowledge** — use `python3 utils/extract-reference-names.py` or `python3 utils/practice-summary.py` on each resolved context to build topic-specific knowledge that informs the relevant report section.

### Parallel Multi-Report Generation

When the user requests N separate reports from a shared method (e.g., one report per product area):

1. **Plan as a batch in Step 0** — note the full scope (N reports), shared method, per-report subject, and any supplementary methods per report.
2. **Resolve contexts once** — resolve the shared method context once; resolve each supplementary method context once. Reuse across agents.
3. **Extract per-report domain knowledge** — for each report, extract the relevant practice(s) from the shared method:
   ```bash
   # Extract a specific practice document from a .keleo bundle
   python3 utils/inspect-keleo.py bundles/<method>.keleo --extract-doc "Practice Name" -o /tmp/practice.json
   
   # Build a structured summary for an agent prompt
   python3 utils/practice-summary.py /tmp/practice.json
   ```
4. **Create a workspace and history per report** — before launching agents, create `reports/<report-slug>/` for each report and `--init` its prompt history, recording the shared plan decisions (practice selection, narrative strategy) into each one. Agents inherit a workspace rather than deciding on one.
5. **Launch parallel agents** — construct a detailed prompt per report embedding: the report directory, subject, audience, narrative strategy, extracted domain knowledge (alphas, outcomes, patterns, citations), and any supplementary method knowledge. Launch all agents in a single message for concurrent execution.
6. **Each agent writes independently** — each agent generates its report to `reports/<report-slug>/<report-slug>.md` using the standard Steps 1–3 workflow, and records its own dependencies, phases, and deliverables.

**Hook caveat:** the active-history pointer is global, so automatic interaction capture follows whichever history was initialised last. In a batch run, record anything that matters to a specific report with an explicit `--add-interaction` against that report's directory rather than relying on the hooks.

---

## Shared Gherkin Rules

These rules apply to **all** reporting skills. Each skill references them by ID — the canonical definitions live here.

### Feature: Narrative Structure Transparency

#### Scenario: Report hides Keleo internals from reader (@rule:report-600)
- Given: a report is generated from a practice or method
- When: the report content is reviewed
- Then: no Keleo-specific terms appear (alpha, state, activitySpace, workProduct, narrativeType, baseline, contributesTo, mapsTo, relatesTo, checklist item, level of detail, practice language)
- And: the report reads as a standalone document requiring no Keleo knowledge

#### Scenario: Narrative structure drives report organization (@rule:report-601)
- Given: a narrative type is selected from the baseline
- When: the report sections are created
- Then: each top-level section maps to a narrative element from the selected type
- And: section headings are plain English (not raw narrative element names unless naturally appropriate)

#### Scenario: Practice knowledge informs report content (@rule:report-602)
- Given: a practice or method provides domain knowledge
- When: report content is written
- Then: the analytical framework from the practice shapes the report's dimensions, criteria, and recommendations
- And: practice concepts are translated into plain language appropriate to the audience

#### Scenario: Report attribution is minimal and optional (@rule:report-603)
- Given: a report is generated
- When: the report is finalized
- Then: at most one brief line at the end attributes the analytical framework
- And: no structural diagrams, schema references, or methodology deep-dives are included

#### Scenario: Framework attribution links to keleo-studio-gas (@rule:report-610)
- Given: a report closes with a framework attribution line
- And: keleo-studio-gas is configured in `.claude/user-config.json`
- When: the attribution line is written
- Then: every practice, method, or baseline named in it is a markdown hyperlink
- And: each link is a `?doc=<document name>` deep link on the configured deployment
- And: the line is generated with `studio-client.py --link ... --attribution`, not hand-written

### Feature: Report Workspace

#### Scenario: Report is a self-contained directory (@rule:report-613)
- Given: a reporting skill generates a report
- When: the output is written
- Then: the report lives at `reports/<report-slug>/<report-slug>.md`
- And: its diagram specs and rendered SVGs live in `reports/<report-slug>/assets/`
- And: every embedded diagram path is relative to the markdown and resolves

#### Scenario: Session provenance is recorded and closed (@rule:report-614)
- Given: a reporting skill completes a run
- When: the report directory is inspected
- Then: `00-prompt-history.md` is present alongside the report
- And: it records the user's prompt, each practice/method resolved as a dependency, and the narrative strategy decision
- And: it lists the report as a deliverable
- And: the session is finalized

### Feature: Diagrams

#### Scenario: Diagrams are rendered SVG, not ASCII art (@rule:report-611)
- Given: a report needs a diagram
- When: the diagram is produced
- Then: it is generated by `utils/render-diagram.py` from a JSON spec kept beside the output
- And: no fenced code block in the report contains box-drawing or ASCII box-art characters
- And: the spec carries content and structure only, never colours, fonts, or sizes

#### Scenario: Embedded diagrams are reachable and described (@rule:report-612)
- Given: a report embeds a diagram
- When: the markdown image is written
- Then: the target path resolves relative to the report
- And: the alt text states the diagram's claim rather than listing its boxes

#### Scenario: Structural claims carry a figure (@rule:report-616)
- Given: a report section makes a structural claim — components and their connections, a sequence with dependencies, a containment hierarchy, or a progression through stages
- When: the section is written
- Then: the section carries a figure making that claim visible
- And: a section whose content is comparative or quantitative carries a table instead of a diagram
- And: no figure merely restates its own caption

#### Scenario: Deliverable copy uses a professional register (@rule:report-619)
- Given: a generated report or deck
- When: its headings and body copy are reviewed
- Then: no technical or business variable is described as choosing, deciding, picking or driving an outcome
- And: headings state their subject or assertion without rhetorical or contrarian construction
- And: problems are framed as prerequisites, integration and trade-offs rather than as failure or naivety
- And: domain terminology is used in place of colloquial shorthand

#### Scenario: A section frames its parts before presenting them (@rule:report-618)
- Given: a report section whose first content is a subsection, a table or a figure
- When: the section is written
- Then: two to four sentences of framing precede that first element
- And: where the parts are a parallel set, the framing names how many there are and the role of each
- And: the framing neither restates the heading nor merely announces that the section is beginning

#### Scenario: Figures draw the subject's instances, not the practice's types (@rule:report-617)
- Given: the report's subject has more than one instance of a concern the practice names once (for example a production platform and a disaster recovery platform)
- When: a figure covering that concern is drawn
- Then: each instance is a separate node named in the subject's own words
- And: the practice concern appears as a sublabel rather than as the node label
- And: relationships between the instances that the practice does not carry are added to the spec

#### Scenario: Embedded diagrams are captioned (@rule:report-615)
- Given: a report embeds a diagram, which does not draw its own title
- When: the markdown image is written
- Then: an italic caption follows it, numbered sequentially through the report
- And: the caption names the figure, where the alt text states its claim

### Feature: Context Resolution

#### Scenario: Practice context loads successfully (@rule:report-604)
- Given: the user specifies a practice, method, baseline, or .keleo bundle
- When: resolve-context.py runs with --transitive
- Then: the effective context JSON contains the baseline narrative types
- And: the practice/method domain knowledge is accessible

#### Scenario: Missing context fails gracefully (@rule:report-605)
- Given: the user specifies a practice that cannot be resolved
- When: context resolution fails
- Then: the skill reports the error clearly
- And: suggests how the user can provide valid input (path to .json or .keleo file)

#### Scenario: Practices with different baselines resolve separately (@rule:report-609)
- Given: the user specifies practices with different root baselines
- When: context resolution runs
- Then: one effective-context.json is created per distinct root baseline
- And: the primary context drives narrative structure and report organization
- And: supplementary contexts provide domain knowledge for specific sections

### Feature: Citations and References

#### Scenario: Report includes in-text citations in APA 7 format (@rule:report-606)
- Given: the effective context contains citations relevant to the report subject
- When: the report makes factual claims, technical recommendations, or framework references
- Then: those claims are supported by APA 7 parenthetical citations (Author, Year)
- And: citations with a URL are rendered as markdown hyperlinks `([Author, Year](URL))`
- And: citations without a URL remain plain text `(Author, Year)`
- And: 5–15 citations appear in a standard report
- And: citations are placed at the end of the relevant sentence, before the period

#### Scenario: Report ends with a References section (@rule:report-607)
- Given: the report contains in-text citations
- When: the report is finalized
- Then: a "## References" section appears after the final content section
- And: every in-text citation has a corresponding full reference entry
- And: entries are in APA 7 format: `Author. (Year). *Title*. Source. URL`
- And: entries are alphabetized by first author surname

#### Scenario: References are source documents, not practice metadata (@rule:report-608)
- Given: citations are selected from the effective context
- When: the citation pool is built
- Then: citations reference the original source documents (methodology papers, vendor documentation, technical guides)
- And: no citations reference the Keleo practice, method, or baseline itself
