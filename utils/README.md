# Practice Language Utilities

Scripts for validating, inspecting, fixing, and assembling Practice Language JSON files.

## Prerequisites

**Required:** Python 3.9+ (standard library only — no pip packages), `keleo-language` repo at `../../keleo-language/` (provides schema, validators, and semantic references via symlinks)

**Optional tools by feature:**

| Tool | Scripts that use it | Role |
|------|-------------------|------|
| `gws` CLI | `extract-gws-slides.py`, `edit-gws-slides.py`, `check-gws-slides-fit.py`, `render-gws-slides.py`, `studio-client.py`, `issue-register.py` | Content sourcing from Google Workspace (Slides, Drive), published deck editing, and feedback register access (Sheets) |
| Node.js 18+ | `validate-json-schema.js` | Alternative schema validation via ajv-cli |
| Remote bundle repository | `studio-client.py`, `discover-dependencies.py --remote` | Centralised `.keleo` package storage and version management |

## Assessment & Validation

| Script | Purpose | Usage |
|--------|---------|-------|
| `assess-practice.py` | Unified quality assessment: structure, uniqueness, competency levels, cross-references, baseline references, pattern quality (sparse alphas, few views, misaligned states); auto-discovers baseline and parent practices from declared dependencies; `--online` checks asset URLs, citation URLs, reference URIs, and citations missing URLs; `--category` filters to specific issue categories (supports prefix matching, e.g. `pattern` matches `pattern-*`) | `python3 utils/assess-practice.py <file>.json [--baseline <baseline>.json] [--schema <schema>.json] [--parent <parent>.json] [--errors-only] [--category CAT [CAT ...]] [--online]` |
| `audit-method-references.py` | Cross-practice reference auditing within a method (alpha refs, duplicates, persona consistency). Accepts a method JSON, a directory of practice JSONs, or a `.keleo` bundle | `python3 utils/audit-method-references.py <method>.json \| <dir>/ \| <bundle>.keleo --baseline <baseline>.json [--json]` |
| `audit-bundle-freshness.py` | Detect `.keleo` bundles carrying stale embedded copies of documents that have since been fixed on disk. Compares each bundled document's version against the highest on-disk version of the same name and reports drift, so corrected content (renamed elements, removed aliases) cannot be reintroduced by an un-rebuilt bundle. Exits 1 when any stale copy is found. `--rebuild` repackages drifted bundles from current on-disk sources and bumps the manifest version (prerelease suffixes preserved); documents that exist only inside the bundle — typically externalized method documents generated at packaging time — are carried over verbatim. Naming bundles with `--bundle` forces their rebuild whether stale or not | `python3 utils/audit-bundle-freshness.py [--bundle <b>.keleo ...] [--document "Name" ...] [--stale-only] [--json]` <br> `python3 utils/audit-bundle-freshness.py --rebuild [--bump patch\|minor\|major\|none] [--fix]` |
| `validate-practice-json.py` | Schema validation for practices/methods | `python3 utils/validate-practice-json.py <file>.json` |
| `validate-baseline-json.py` | Schema validation for baselines | `python3 utils/validate-baseline-json.py <file>.json` |
| `validate-phase-output.py` | Validate Phase 1/1.5/2 markdown output structure; `--one-line` prints a single-line verdict instead of the full JSON check list; `--source-manifest` checks every source document in an `extract-html-text.py` manifest (or newline-delimited source list) is actually drawn on, searching all given files — catches guides that fall between parallel cluster analysts | `python3 utils/validate-phase-output.py <file>.md --phase <1\|1.5\|2> [--validate-patterns] [--gate] [--one-line] [--stats] [--source-manifest <manifest>.json]` |
| `verify-mapping-against-specs.py` | Verify Phase 2 mapping output against Gherkin specs. Accepts alpha sections at h3–h6 and activities as either a bold run-in label or an h3–h6 heading — all forms are in active use across the library. Check `extracted.alphaCount` is non-zero before trusting a pass: a guide the extractor cannot parse reports no findings, which looks identical to a clean run | `python3 utils/verify-mapping-against-specs.py <mapping>.md --baseline <baseline>.json [--parent <parent>.json] [--kind baseline]` |
| `eval-skill-output.py` | Evaluate skill output quality against assertions; auto-discovers baseline, parent practices, and schema; `--errors-only` filters to error-severity (excludes warnings). `--selftest` proves each assertion catches a planted defect, using `tests/fixtures/practice-good.json` and the mutation catalogue in `tests/mutations.py` — offline, no API. It reports `UNCOVERED` assertions (nothing proves they can fail) and gates `--evals`, which refuses to score a batch on an unproven grader unless `--no-selftest` is passed | `python3 utils/eval-skill-output.py <practice-dir> [--specs <specs-index.json>] [--one-line] [--errors-only]` <br> `python3 utils/eval-skill-output.py --selftest [--verbose]` |
| `run-skill-eval.py` | Run a skill's eval cases with and without the skill, in isolated workspaces, and report the delta. Cells run in a temp directory outside any git repo with `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` and `--setting-sources project,local`, because a no-skill arm that still reads the project CLAUDE.md measures nothing. `--selftest` proves the isolation and that each contaminant is actually detected; it gates every run. Workspaces are kept so `--rescore` re-grades offline after an assertion changes. **A cell is a full skill run and costs real money** — start with `--dry-run`, then one `--case` and `--runs 1` | `python3 utils/run-skill-eval.py --selftest` <br> `python3 utils/run-skill-eval.py --evals <evals.json> --case <id> --dry-run` <br> `python3 utils/run-skill-eval.py --evals <evals.json> --case <id> --arms with-skill,without-skill --runs 1` <br> `python3 utils/run-skill-eval.py --rescore runs/<stamp>` |
| `lint-practice.py` | Combined validate-fix-revalidate loop (auto-discovers baseline/schema) | `python3 utils/lint-practice.py <practice>.json [--fix] [--one-line] [--max-iterations N]` |
| `lint-report.py` | Verify generated markdown reports before handover: Keleo vocabulary leaks (@rule:report-600), bidirectional in-text ↔ `## References` citation correspondence with surname matching (@rule:report-607/608), framework names in the closing attribution line rendered as keleo-studio-gas deep links (@rule:report-610), diagrams rendered as SVG rather than ASCII art with alt text and a resolvable target (@rule:report-611/612), professional register — variables given agency over decisions, rhetorical or contrarian headings, and editorialising phrases such as "works on paper" (@rule:report-619, warnings only, since each is context-dependent) — framing prose before a section's first subsection, table or figure so a reader does not meet `### Option A` without knowing B and C exist (@rule:report-618, tunable with `--min-section-words`, skips `00-prompt-history.md`), body word count against the target band, and a heading outline for checking the narrative mapping. Citation matching recognises all four in-text forms the reporting foundation prescribes: parenthetical `(Author, 2024)`, hyperlinked parenthetical `([Author, 2024](url))`, narrative `Author (2024)`, and hyperlinked narrative `[Author (2024)](url)`. Accepts several reports at once; with `--consistent-terms` it also checks that fixed names (play, TDP, tactic, product) are used identically across the whole set. Exits 1 on any error | `python3 utils/lint-report.py <report>.md [<report>.md ...] [--checks terminology citations diagrams attribution length structure sections tone] [--consistent-terms "Name A" "Name B"] [--min-words N --max-words N] [--min-citations N --max-citations N] [--studio-url URL] [--strict] [--json]` |
| `post-validate-method.py` | Batch fix-validate pipeline across all practice JSONs in a directory; wraps lint-practice.py per file, optional cross-practice audit | `python3 utils/post-validate-method.py <directory>/ [--fix] [--one-line] [--audit] [--baseline <baseline>.json]` |
| `verification-gate.py` | Consolidate the findings of a stage's verification agents and gate on them. `--phase` takes a generation phase (`1`, `1.5`, `2`, `3`) or `report` for the reporting skills' single gate, which writes `report-<verifier>.json` rather than `phase-<N>-<verifier>.json`. Reads `<dir>/_verification/phase-<N>-<verifier>.json`, dedupes across verifiers keeping the highest severity, applies the reconciler's per-finding verdicts from `phase-<N>-reconcile.json`, and writes `phase-<N>-verdict.json` plus a markdown summary for the user review gate. `--gate` exits 1 when a blocking error survives. **Always pass `--expect`** — without it a verifier that crashed before writing its file is indistinguishable from one that found nothing, and the gate passes on silence. `--path-for` prints the path a named verifier should write to. Purely mechanical: deciding whether a finding is real stays with the reconciliation agent. See `.claude/skills/verification-foundation/` | `python3 utils/verification-gate.py <dir>/ --phase <1\|1.5\|2\|3\|report> --gate --summary --expect <v1>,<v2>` <br> `python3 utils/verification-gate.py <dir>/ --phase 2 --path-for source-fidelity` <br> `python3 utils/verification-gate.py --selftest` |

## Structural Inspection

| Script | Purpose | Usage |
|--------|---------|-------|
| `practice-summary.py` | Structured practice summary for subagent prompt construction (metadata, alphas, patterns with their per-view alpha→state contributions, outcomes, feature coverage); `--names-only` lists name/kind/version compactly; `--show` prints full element detail — persona competencies and narratives, alpha state checklists with Gherkin `given`, work product LODs, citations with URLs — optionally filtered by `--name <substring>`, and works on a resolved `_effective-context.json` as well as a practice file | `python3 utils/practice-summary.py <file>.json [--baseline <baseline>.json] [--json] [--names-only] [--show personas\|alphas\|workProducts\|activities\|outcomes\|narratives\|citations\|personaGroups\|all [--name <substring>]] \| --dir <dir>/` |
| `detect-schema-gaps.py` | Schema evolution gap detection (outcomes, patternGroups, priorities, references vs current schema) | `python3 utils/detect-schema-gaps.py <file>.json [--schema <schema>.json] [--json] \| --dir <dir>/` |
| `extract-reference-names.py` | Extract symbolic names from JSON (alphas, states, activities, outcomes, pattern-views, etc.); `--hierarchy` shows alpha contributesTo tree with provenance; `--alpha-details` includes contributesTo, mapsTo, and contributingPractice; `--locate` finds where a named element is *defined* and reports its element type (with close-match suggestions), complementing `--find-refs` which finds where it is *used*; `--metadata` reports kind, name, version, schemaVersion, baseline and dependency names, and a method's `practiceNames` | `python3 utils/extract-reference-names.py <file>.json [--sections alphas activities outcomes pattern-views ...] [--alpha-details] [--structure] [--metadata] [--hierarchy] [--locate "Name" [--exact]] [--find-refs "Name"]` |
| `library-index.py` | Build a compact index of all discoverable practices and methods with matchable metadata (description, outcomes, keywords, tags, baseline and resolved root baseline); `--compact` produces LLM-readable text, `--name` filters to named documents, `--group-by-root` groups them by root baseline to show whether they share one effective context | `python3 utils/library-index.py [--kind practice method] [--name "A" "B"] [--compact\|--group-by-root] [-o <output>.json]` |
| `extract-practice-content.py` | Extract practice content from methods or resolve dependencies; `--summary` prints a human-readable text overview | `python3 utils/extract-practice-content.py <file>.json [--output <report>.md] [--summary] [--extract-narratives <out>.json]` |
| `extract-specs.py` | Parse Gherkin scenarios from SKILL.md into specs-index.json. `--list-manual` reads an index back and lists the scenarios no script can check — the contract a verification agent carries; `--category` narrows that to one rule category. `--to-markdown` is the inverse of extraction, rendering an index back into its `## Feature:` block: needed when a SKILL.md is refactored and loses its scenarios while the generated index survives, since regenerating from the stripped file would silently delete every rule | `python3 utils/extract-specs.py <SKILL.md> [-o <specs-index.json>] [--stats]` <br> `python3 utils/extract-specs.py --list-manual <specs-index.json> [--category fidelity] [--json]` <br> `python3 utils/extract-specs.py --to-markdown <specs-index.json>` |
| `diff-practice-json.py` | Diff two practice JSON files by element type; `--gate` mode checks for element arrays that dropped to 0 (post-Phase-3 completeness gate, exit 1 on critical) | `python3 utils/diff-practice-json.py <old>.json <new>.json [--json] [--changes-only] [--gate]` |
| `inspect-keleo.py` | Inspect `.keleo` package contents: manifest, documents, versions, dependencies; extract individual documents by name. `-o` takes a file path, or a directory to receive the document under its archive filename — so repeated `--extract-doc` calls can share one destination | `python3 utils/inspect-keleo.py <bundle>.keleo [--json] [--list] [--extract-doc NAME [-o PATH\|DIR/]]` |
| `query-schema.py` | Query Practice Language schema `$defs` type definitions; auto-discovers `deps/language.schema.json` | `python3 utils/query-schema.py <TypeName> [--properties] [--json] [--list]` |

## Remote Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `studio-client.py` | Remote bundle repository client: fetch remote package and document indexes, compare versions (`--check --deep` also compares document content, catching a bundle republished without a version bump), download/upload `.keleo` bundles, build `?doc=` deep links (and the closing report attribution line) for published practices/methods, configure credentials | `python3 utils/studio-client.py --status \| --index [--max-age N] \| --docs [--kind K] \| --check [name] [--deep] \| --link "Name" ["Name" ...] [--element E] [--markdown \| --attribution] [--strict] \| --pull "Name" \| --push <file>.keleo \| --configure [--url URL] [--token TOKEN] [--json]` |

## Feedback Register

| Script | Purpose | Usage |
|--------|---------|-------|
| `issue-register.py` | Google Sheets feedback register client: inspect table schema, list issues by status, accumulate draft issues one at a time into a drafts file (`--add-draft`, offline, suppresses in-file repeats), validate and duplicate-check drafts, append new rows (Status always written as `New`), and write resolution columns P–T back onto existing rows. Used by `/report-issue` to file issues, `/plan-from-feedback` to read and resolve them, and by any skill filing content defects under SKILL-STANDARD §13 | `python3 utils/issue-register.py --schema \| --list [--status New] [--limit N] \| --validate <drafts>.json \| --add-draft <drafts>.json --type Issue --summary "..." --description "..." [--document NAME] [--document-version V] [--document-kind KIND] [--element NAME] [--element-type TYPE] [--secondary NAME] [--secondary-type TYPE] [--page PAGE] \| --check-duplicates <drafts>.json [--threshold 0.72] \| --append <drafts>.json [--dry-run] [--no-duplicate-check] [--email ADDR] \| --resolve <resolutions>.json [--dry-run] [--spreadsheet URL_OR_ID] [--json]` |

## Resolution & Merging

| Script | Purpose | Usage |
|--------|---------|-------|
| `discover-dependencies.py` | Auto-discover and resolve dependencies by scanning project directories; `--related` finds practices sharing dependencies with a method or practice; `--remote` checks cached remote index, `--auto-pull` downloads missing bundles | `python3 utils/discover-dependencies.py --resolve "Name" [--remote] [--auto-pull] \| --resolve-from <file>.json [--transitive] [--remote] \| --dependents "Name" \| --tiers <method>.json \| --consumers "Name" \| --related <file>.json \| --list` |
| `sync-practices.py` | Sync shared practices across method directories (match by name, preserve filenames) | `python3 utils/sync-practices.py <source-dir>/ [--fix] [--rebuild-bundles] [--json]` |
| `resolve-context.py` | Unified context resolver: baselines + practices + .keleo → effective context; `--transitive` resolves practice dependencies (practiceDependencyNames), a method's externalized member practices (practiceNames) and baseline dependencies. Any member practice that cannot be resolved — missing, or an ambiguous name with several copies on disk — is listed in `unresolvedMethodPractices` with its candidate paths and summarised in `warnings`; an effective context that ends up with no alphas or focuses also warns. Stamps `_contributingPracticeName` (last writer) and `_contributingPracticeNames` (all contributors) on every element; `_provenance.multiSourceElements` lists elements declared by more than one source | `python3 utils/resolve-context.py <baseline>.json [<practice>.json] [<bundle>.keleo] --transitive -o <output>.json` |
| `resolve-practice-dependencies.py` | Determine practiceDependencyNames by comparing parent and baseline alphas. Resolves alpha ownership from `_contributingPracticeName` provenance when `--parent` is a resolved effective context, so `--parent-method` is optional. Reports only *forced* dependencies (single-owner alphas); alphas declared by several practices appear under `sharedAlphaOwners` and, when unsatisfied, `requiresDependencyChoice` for a semantic decision. **Covers alpha references only** — redeclaring a persona, persona group or other element defined by a dependency practice also creates a dependency, and must be checked separately | `python3 utils/resolve-practice-dependencies.py --parent <parent>.json --baseline <baseline>.json --practice <practice>.json [--per-alpha]` |

## Auto-Fix Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `manage-aliases.py` | List, audit, and remove `practiceElementAliases`. `--audit` flags scope-narrowing aliases — those placed on an element that several documents in `--scope` define, where the alias asserts one practice's local framing onto a shared element instead of naming what the element IS. Pass the baselines in `--scope` to catch aliases on root baseline alphas, and `--ignore-baseline-aliases` to exclude a baseline's own domain vocabulary. Exits 1 when narrowing aliases are found | `python3 utils/manage-aliases.py [--list] <file>.json ... \| --audit --scope <dir-or-file> ... [--ignore-baseline-aliases] [--json] \| <file>.json --remove "Type:Name" ... [--fix]` |
| `fix-common-issues.py` | Fix structural issues: kind, narratives, citations, contributesTo, schema violations, narrative placement, pattern compression, missing assets, nested narrative wrappers, missing checklist seq, missing versions. `--fix-unknown-activity-spaces` resolves against the merged vocabulary from the whole baseline chain, not just the leaf baseline passed on the command line, and leaves anything it cannot confidently match for the validator to report rather than guessing | `python3 utils/fix-common-issues.py <file>.json [--fix] [--all] [--compress-patterns] [--fix-missing-assets] [--fix-nested-narratives] [--fix-missing-seq] [--fix-versions]` |
| `fix-competency-levels.py` | Fix invalid competency level names against baseline | `python3 utils/fix-competency-levels.py <file>.json <baseline>.json [--fix] [--map "Old=New"]` |
| `fix-alpha-refs.py` | Add/remap/remove alpha references in practice JSON | `python3 utils/fix-alpha-refs.py <file>.json <baseline>.json [--add-redeclaration NAME] [--remap OLD NEW --state-map JSON] [--remove-alpha NAME] [--fix]` |
| `fix-citation-names.py` | Fix citation name fields to use work titles | `python3 utils/fix-citation-names.py <file>.json [--fix]` |
| `fix-citation-urls.py` | Test citation URLs and reference URIs; fix/remove broken ones (4xx/5xx); `--check-missing` detects citations missing URLs; `--no-references` skips reference URI checks; `--remove-citations` removes entire citation + references | `python3 utils/fix-citation-urls.py <file>.json [--fix] [--remove-citations] [--replace "old=new"] [--check-missing] [--no-references] [--json]` |
| `patch-practice-json.py` | Apply targeted JSON patches to practice files; `--batch-file` applies multiple element patches from a spec | `python3 utils/patch-practice-json.py <file>.json [--element-path PATH --patch-file <patch>.json] [--batch-file <spec>.json] [--rename-in COLL OLD NEW] [--dry-run]` |
| `transform-alphas.py` | Batch alpha transformations (rename, reparent, convert type, set/remove relationships, set relatesTo, set alias, strip contributesToState, remove). State renames cascade to checklists, activities, patterns, LOD backgrounds, references, outcomes, and contributesToAlphaNames. `setAlias` works on inherited/redeclared baseline alphas without requiring them in the practice's own alphas array. | `python3 utils/transform-alphas.py <file>.json --spec-file <spec>.json [--fix]` |
| `transform-workproducts.py` | Batch work product transformations: rename, set/remove mapsTo and partOf (concurrent supported), align LODs, add new work products with auto-seq | `python3 utils/transform-workproducts.py <file>.json --spec <spec>.json [--fix]` |
| `transform-wp-to-alpha.py` | Config-driven transformation: convert a work product into an alpha + revised work product; handles alpha creation from LOD checklists, WP revision, pattern view updates, activity worksOn/contributesTo updates, alias updates, relatesTo reciprocals, global WP name rename | `python3 utils/transform-wp-to-alpha.py <practice>.json --config <config>.json [--fix]` |
| `apply-versioning.py` | Add schemaVersion, normalize version, populate dependencyVersions (supports practice, method, and baseline kinds), bump/set version, ahead-of-copies | `python3 utils/apply-versioning.py [--all] [--bump patch\|minor\|major] [--set-version X.Y.Z] [--show] [--ahead-of-copies] [--fix]` |
| `update-method-json.py` | Manage method JSON: add/remove/import practices to practiceNames, sync dependencyVersions from resolved files, merge tags/keywords from constituent practices | `python3 utils/update-method-json.py <method>.json [--add-practice NAME] [--remove-practice NAME] [--import-practice FILE] [--sync-deps] [--sync-tags] [--fix]` |
| `align-baseline-states.py` | Align child baseline redeclared alpha states with parent canonical names | `python3 utils/align-baseline-states.py <child>.json <parent>.json [--check] [--mapping JSON]` |
| `fix-pattern-progression.py` | Fix pattern progression: remove non-progressing alphas, remove degenerate single-alpha patterns, and reorder reversed alpha state sequences | `python3 utils/fix-pattern-progression.py <file>.json [--fix] [--bump minor] [--json]` |
| `manage-pattern-groups.py` | Manage patternGroups: init canonical groups in baselines (`--groups`), or adopt baseline groups in extensions (`--assignments`). Auto-detects mode from target's `kind` | `python3 utils/manage-pattern-groups.py <target>.json [<baseline>.json] [--groups <groups>.json] [--assignments <map>.json] [--fix] [--dry-run]` |
| `modernize-checklists.py` | Transform checklist item names from past-participle to imperative verb phrases; supports batch mode | `python3 utils/modernize-checklists.py <file>.json [--fix] [--dir <dir>]` |
| `harmonize-personas.py` | Ensure redeclared personas preserve competencies from dependencies; detect personaGroup composition opportunities | `python3 utils/harmonize-personas.py <practice>.json --deps <dep1>.json [<dep2>.json ...] [--fix] [--json]` |
| `checklist-priorities.py` | Extract checklist items for priority review or apply priority assignments | `python3 utils/checklist-priorities.py <file>.json [--extract] [--apply <assignments>.json] [--fix]` |

## Change Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `generate-change-request.py` | Generate a ChangeRequest JSON from the diff between old and new practice/baseline/method JSON files | `python3 utils/generate-change-request.py <old>.json <new>.json [--author NAME] [--status draft\|accepted] [--note "..."] [-o <output>.json]` |
| `apply-change-request.py` | Apply ChangeRequest nameChanges/removals to downstream JSON | `python3 utils/apply-change-request.py <change-request>.json <target>.json [--fix]` |
| `check-downstream-impact.py` | Orchestrate downstream impact analysis: generate ChangeRequest from old/new diff, find all dependents (filesystem, .keleo bundles, and remote repository), check for broken references, optionally fix and rebuild bundles | `python3 utils/check-downstream-impact.py <old>.json <new>.json [--fix] [--rebuild-bundles] [--remote] [--auto-pull] [--element-types TYPE ...] [--json]` |

## Enrichment

| Script | Purpose | Usage |
|--------|---------|-------|
| `add-citations.py` | Add citations to a practice/baseline JSON and link them to element narratives | `python3 utils/add-citations.py <target>.json --citations-file <citations>.json [--link-to alphas activities workProducts all] [--dry-run]` |
| `add-element-icons.py` | Add Font Awesome icon assets to elements in bulk from an icon mapping file | `python3 utils/add-element-icons.py <file>.json --map <icons>.json [--fix] [--skip-existing]` |
| `apply-narratives.py` | Apply narrative JSON to matching elements by name in a practice/baseline JSON | `python3 utils/apply-narratives.py <target>.json --map <narratives>.json [--fix]` |
| `build-references.py` | Build schema-compliant AlphaInstance references from a compact spec, validating anchors against the practice | `python3 utils/build-references.py <practice>.json --spec <spec>.json [--fix] [-o <output>.json]` |
| `enrich-references.py` | Generate build-references specs from a content inventory; requires `--config` with URL templates and category mappings | `python3 utils/enrich-references.py <inventory>.json --config <config>.json [--apply] [-o <dir>]` |

## Packaging

| Script | Purpose | Usage |
|--------|---------|-------|
| `package-keleo.py` | Create .keleo archive from constituent JSON files. For methods, `--method-name` generates an externalized method document; `--method-version` sets its `version` (defaults to `--version`) and `schemaVersion` is read from the schema | `python3 utils/package-keleo.py --name "Name" --version 1.0.0 --documents <file>.json [<file2>.json] -o <output>.keleo [--verify]` |
| `rebuild-keleo.py` | Rebuild existing .keleo packages from their manifests using current source files | `python3 utils/rebuild-keleo.py [<files>.keleo] [--all] [--dry-run] [--if-changed] [--json]` |

## Refactoring & Backup

| Script | Purpose | Usage |
|--------|---------|-------|
| `backup-practice.py` | Create timestamped backup of a practice directory; `--prune N` keeps only the N most recent | `python3 utils/backup-practice.py <directory>/ [--prune N] [--prune-only]` |
| `assemble-mapping-guide.py` | Assemble Phase 2 mapping guide from cluster fragments | `python3 utils/assemble-mapping-guide.py <cluster1>.md [<cluster2>.md...] -o <output>.md` |
| `assemble-analysis-report.py` | Merge partial Phase 1 analyses into one `01-analysis-report.md`. Used when a source corpus is too large for a single Phase 1 agent and is split into clusters. Matches each partial's `## ` headings to the canonical Phase 1 sections, renumbers `### ` subsections sequentially, deduplicates citations by title, and preserves unmatched sections in an appendix. `--digest` also emits a compact cross-cluster file (concern names, descriptions and `#### Concern Relationships` blocks) so parallel Phase 2 agents get cross-practice awareness without carrying the full report | `python3 utils/assemble-analysis-report.py --name "<Methodology>" --partials <p1>.md [<p2>.md...] -o <output>.md [--sources "<text>"] [--structure "<text>"] [--digest <digest>.md] [--stats]` |
| `reconcile-cross-references.py` | Rename predicted sibling-practice alpha/state names in phase outputs once parallel Phase 2 agents have landed. Single-pass regex so a rename whose target contains its source cannot double-apply; `--verify` gates that no predicted name survives | `python3 utils/reconcile-cross-references.py <file>.md [<file>.md ...] --map <renames>.json (--fix \| --dry-run \| --verify) [--json]` |
| `migrate-report-layout.py` | Migrate flat `reports/<slug>.md` output into per-report workspace directories: moves the markdown and its companion exports into `reports/<slug>/`, relocates `reports/assets/<slug>/` to `reports/<slug>/assets/`, shortens embedded image paths to `assets/<name>.svg`, and splits the root `.published-docs.json` into a per-directory state file so an already-published report keeps updating the same Google Doc. Idempotent — reports already in workspace form are reported and skipped, so a partial migration can be finished by re-running. Dry run by default | `python3 utils/migrate-report-layout.py [--reports-dir <dir>] [--fix] [--json]` |

## Session Provenance

| Script | Purpose | Usage |
|--------|---------|-------|
| `prompt-history.py` | Manage prompt history files for practice, baseline, and report sessions: init, record sources/dependencies/decisions/interactions/phases/deliverables, finalise. `--type report` is used by the reporting skills against `reports/<report-slug>/` | `python3 utils/prompt-history.py <directory>/ --init --type practice\|baseline\|method\|report --name "Name" --prompt "..." \| --add-source --source-type file --source-path "..." --source-desc "..." \| --add-dependency --dep-type baseline --dep-name "..." --dep-path "..." [--dep-version "..."] \| --add-decision --decision-label "..." --decision-text "..." \| --add-interaction [--interaction-label "..."] [--interaction-question "..."] --interaction-answer "..." \| --start-phase --phase "Phase 1: Analysis" \| --end-phase --phase "Phase 1: Analysis" [--phase-output "..."] [--phase-validation "..."] \| --add-deliverable --deliverable-path "..." --deliverable-desc "..." \| --activate \| --finalize \| --batch <ops>.json` |

### Automatic interaction capture

`prompt-history.py --init` writes `.tmp/active-prompt-history.json`, which points two hooks in
`.claude/settings.json` at the live history:

| Hook | Records |
|------|---------|
| `UserPromptSubmit` → `--hook user-prompt` | Every user turn, verbatim, under `## Interaction Log` |
| `PostToolUse` matching `AskUserQuestion` → `--hook tool` | The question(s) put to the user and the option(s) they chose |

The pointer binds to the first session that fires, so a concurrent session in this project
cannot leak its prompts into the history. `--finalize` clears the pointer; `--activate`
re-arms it when resuming an existing practice in a new session. Hook mode never writes to
stdout and always exits 0 — a recording failure must not break the session.

The hooks capture what the user *said*. A question asked in plain prose, outside
`AskUserQuestion`, still needs `--add-interaction` so the question is recorded alongside the
answer.

**`.claude/settings.json` is git-ignored**, so a fresh clone has no hooks. Re-add the two
entries above to enable automatic capture.

## Session Analysis

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze-transcripts.py` | Analyze Claude Code session transcripts for user corrections and ad hoc inline scripts | `python3 utils/analyze-transcripts.py <transcript.jsonl> [--corrections-only] [--scripts-only] [--json]` |

## Ingestion

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-docx-text.py` | Extract text from Office Open XML `.docx` documents as markdown — headings from paragraph styles, numbered/bulleted paragraphs as lists, `w:tbl` as pipe tables. Standard library only (a `.docx` is a ZIP holding `word/document.xml`). Use for Word-format source material: solution builds, statements of work, partner proposals. `--headings-only` surveys structure before reading the whole thing; `--output-dir` batches many files | `python3 utils/extract-docx-text.py <file>.docx [-o <output>.md] [--headings-only]`<br>`python3 utils/extract-docx-text.py <dir>/*.docx --output-dir <dir>/` |
| `extract-gws-slides.py` | Extract Google Workspace Slides content via gws CLI | `python3 utils/extract-gws-slides.py <presentation-id> [-o <output>.md]` |
| `extract-gws-text.py` | Extract text from Google Workspace API JSON (auto-detects Slides/Docs format) | `python3 utils/extract-gws-text.py <input>.json [-o <output-dir>] [--format slides\|docs]` |
| `extract-html-text.py` | Extract text from HTML **or markdown** sources (URL or file), preserving heading structure in markdown; input format is sniffed from content, not extension, so `--headings-only` works against this tool's own output; `--anchors` outputs heading→anchor ID JSON map (HTML only). `--links` outputs the page's links as JSON (`{text, href}`, resolved against the source URL, fragments and `mailto:`/`javascript:` dropped, duplicates collapsed), with `--same-host` to drop off-site links — use it to enumerate the guides in a documentation set, then feed the result to `--sources-file`. Batch mode takes many sources (or `--sources-file`) and writes one `<stem>.txt` per source into `--output-dir`, continuing past failures, with an optional JSON `--manifest`. Colliding stems are disambiguated with the nearest differing path segment (`1.3-architecture`, `1.1-architecture`), not an ordinal — two versions of the same documentation page would otherwise produce `architecture.txt` and `architecture-2.txt`, leaving no way to tell which version you are reading | `python3 utils/extract-html-text.py <url-or-file> [-o <output>.md] [--anchors] [--anchors-file <map>.json] [--headings-only]`<br>`python3 utils/extract-html-text.py <doc-set-url> --links --same-host`<br>`python3 utils/extract-html-text.py --sources-file <urls>.txt --output-dir <dir>/ [--anchors] [--manifest <manifest>.json]` |

## Published Deck Editing

For decks that live only in Google Slides — no local Slidev source, or a source that has diverged — these edit and verify the published deck in place, preserving its layout and theme. Edits are reversible through Google Slides version history.

| Script | Purpose | Usage |
|--------|---------|-------|
| `edit-gws-slides.py` | Apply find/replace edits to a published deck. Three edit forms: `find`/`replace` across body copy (case-sensitive, notes deliberately out of scope), `notesForSlide`/`replace` to rewrite a slide's whole speaker-note body (fragment matching is unreliable — pptx import leaves vertical-tab soft breaks mid-sentence), and `objectId` with `fontSize` and/or `widthInches` to reshape an element whose box was exported around the old wording. Pre-flight counts every match and fails on a no-op edit; post-flight re-fetches and reports anything that did not take | `python3 utils/edit-gws-slides.py <presentation-id> --edits <edits>.json [--dry-run] [--allow-missing] [--rename TITLE]` |
| `check-gws-slides-fit.py` | Flag text that probably collides with the element below it or runs off the slide, by estimating rendered height from font size and box width. Triage for which slides to render — it does not catch text that wraps into whitespace, and deliberately does not test box fit (pptx export sizes boxes tighter than one line of their own text) | `python3 utils/check-gws-slides-fit.py <presentation-id> [--all] [--advance 0.52] [--line-height 1.2] [--tolerance 0.1]` |
| `render-gws-slides.py` | Download slides as PNG for visual review. Google Slides sets text wider than a local Chromium render, so overflow defects only show up on the published deck | `python3 utils/render-gws-slides.py <presentation-id> (--slides 1,4-6,30- \| --all) [-o <dir>] [--prefix NAME] [--size small\|medium\|large]` |

## Report Diagrams

| Script | Purpose | Usage |
|--------|---------|-------|
| `derive-diagram.py` | Derive diagram specs from the semantic graph a practice already carries, so a report's figures come out of the effective context rather than being hand-transcribed from it. Emits specs only — `render-diagram.py` renders them, and the spec is the artifact worth keeping. `--list` first: it reports the focuses, the alphas ranked by relationship count (the best seeds), the patterns with their phase sequence, and the work products. One view per structural relation in the language: `concern-map` (`flow` — alphas and their `relatesTo` verbs, clustered by focus), `concern-hub` (`hub` — one alpha and everything touching it; usually reads better than a seeded concern-map, which strings out into a chain), `capability-tree` (`flow` — the `contributesTo`/`mapsTo` rollup, where `--seed` names a root and `--depth` counts generations), `journey` (`timeline` — a pattern's views by `seq`), `maturity` (`stack` — one alpha's states, most mature on top), `evidence-map` (`flow` — work products and the concerns they serve, via `contributesToAlphaNames`, with `partOf` as cluster groups), `pattern-matrix` (`matrix` — alphas by pattern view, cell is the target state, empty cell is the finding), `outcome-chain` (`flow` — `Outcome.metricContributions`/`objectiveContributions` as a chain from the work product carrying the metric, through the concern and the state at which it counts, to the outcome), `role-map` (`flow` — `PersonaGroup` membership and nesting), `competency-matrix` (`matrix` — competencies by level, cell is that level's rubric text). `State.contributesToState`, `LevelOfDetail.contributesTo` and `Activity.ledBy` carry structure too but are not derived — no context here populates them. Every edge runs declaring alpha → target with the verb verbatim, because a relationship verb is phrased from the alpha that declares it and reads as nonsense inverted; `direction` chooses between the two reciprocal phrasings rather than orienting the line, preferring the active one. Scope with `--seed`/`--depth`, `--focus`, `--practice`. Three guards: `--max-nodes` (default 9, counting `--instance` expansion) refuses a hairball and names the best seeds; past ~1.8 edges per node a layered flow collapses into a column and stops drawing edges where they belong, so it refuses and points at `concern-hub` unless `--allow-dense` is passed; and three or more labelled edges meeting at one node trigger a crowding note naming that node (`--no-edge-labels` is usually the answer). `--instance "Alpha=Name,Name"` splits one node into named instances each inheriting its edges — for a subject with a production and a DR platform — with inter-instance edges added to the emitted spec by hand. Exits 1 on an unresolvable name or a budget overflow | `python3 utils/derive-diagram.py <context>.json --list` <br> `python3 utils/derive-diagram.py <context>.json --view concern-hub --seed "<Alpha>" --out-dir reports/<slug>/assets/ --name <stem>` <br> `python3 utils/derive-diagram.py <context>.json --view journey --pattern "<Pattern>" --stdout` |
| `render-diagram.py` | Thin wrapper over the shared engine in `.claude/skills/diagram-foundation/` (a vendored copy of `~/.claude/skills/diagram-foundation/` — fix upstream, re-copy down). Renders a declarative spec into styled SVG for embedding in a markdown report. Eight native layouts: `flow` (layered boxes and directed edges, `LR`/`TB`, nestable cluster groups — topologies, pipelines, process flows), `stack` (vertical tiers — layer models, maturity stacks), `timeline` (sequential phase bands with arrows — roadmaps, adoption journeys), `hub` (centre node with satellites on an ellipse — relationship maps, fan-out), `matrix` (grid with row and column headers — capability heat maps, Zachman, coverage audits), `wardley` (value-chain / evolution grid — build versus buy), `swimlane` (lanes of steps with handoffs — who does what, in order), `canvas` (Event Storming wall). A `.mmd` spec — YAML frontmatter plus Mermaid source — adds C4, ERD, sequence, class and state diagrams; `render: scene` lets Mermaid lay a flowchart out and redraws it in house shapes, anything else keeps Mermaid's picture themed to the palette. Needs `npx` on PATH for the Mermaid routes. Nodes accept `shape`, `emphasis` and a semantic `role`; edges accept `dash` and `arrow`. Visual language is lifted from the keleo-studio-gas navigator diagrams, so reports, the studio UI and the deck theme read as one system; restyle via the `THEME` dict rather than per-diagram. `title` and `description` are metadata only — they become `<title>` and `<desc>`/`aria-label`, never drawn, because the heading above the diagram in the report already names it. Labels are native `<text>` with wrapping done in-module (a `foreignObject` does not render when an SVG loads through a markdown `<img>`) and every diagram paints an opaque background so dark-theme pages do not swallow the text. `--dir` renders every spec in a directory beside itself — one call per report. Exits 1 on an unknown layout, duplicate node id, dangling edge endpoint, or unknown group/emphasis | `python3 utils/render-diagram.py <spec>.json [-o <out>.svg] [--stdout]` <br> `python3 utils/render-diagram.py --dir reports/<report-slug>/assets/` <br> `python3 utils/render-diagram.py --spec-help` |
| `preview-diagram.py` | Rasterise rendered diagrams to PNG so they can be eyeballed for defects a validator cannot see — labels clipped to an ellipsis, edge labels colliding, cluster rects overlapping. `--report` reads the markdown and rasterises every SVG it embeds, which is the form a reporting skill wants at the end of Step 3; `--dir` and a bare path cover the other cases. Sizes each raster from the SVG's own viewBox and stretches it to the viewport in a wrapper page, so the whole diagram is in frame at a legible scale whatever its aspect. **Do not substitute macOS `qlmanage -t`** — it fits to width on a square canvas, so a tall diagram is silently cropped and a broken diagram reads as a clean one. Finds a browser from Playwright's bundled Chromium, `chromium`/`chrome` on PATH, or Google Chrome on macOS, and prints per-platform install guidance when none is present | `python3 utils/preview-diagram.py --report reports/<report-slug>/<report-slug>.md` <br> `python3 utils/preview-diagram.py --dir reports/<report-slug>/assets/` <br> `python3 utils/preview-diagram.py <diagram>.svg [-o <dir>] [--width 1100]` |

## URL & Reference Resolution

| Script | Purpose | Usage |
|--------|---------|-------|
| `resolve-doc-anchors.py` | Resolve section references in practice JSON to anchored URLs; matches reference/citation descriptions against heading anchors and appends `#fragment` to URLs. `--dump-anchors` prints a document's heading→anchor map with no practice JSON at all, which is what you want when authoring citations by hand so a URL carries a verified fragment rather than pointing at the document root; `--grep` filters that map. Sends a browser user-agent, because several documentation CDNs — docs.redhat.com among them — answer unrecognised agents with HTTP 403 | `python3 utils/resolve-doc-anchors.py <file>.json --anchors <map>.json [--fix] [--json]` <br> `python3 utils/resolve-doc-anchors.py <file>.json --url <page-url> [--fix] [--json]` <br> `python3 utils/resolve-doc-anchors.py --url <page-url> --dump-anchors [--grep TERM]` |

## Skill Vendoring

| Script | Purpose | Usage |
|--------|---------|-------|
| `vendor-skills.py` | Re-copy the user-level skills at `~/.claude/skills/` into `.claude/skills/` so a clone has diagram and deck capability without a user-level install. Six are vendored: `diagram-foundation`, `diagram`, `deck-foundation`, `slide-deck`, `pitch-deck`, `exec-readout`. Text files are rewritten on the way down so `~/.claude/skills/…` becomes `.claude/skills/…`, which CLAUDE.md names as the only intended difference, and each vendored `SKILL.md` or foundation gains a provenance banner pointing at upstream. `deck-foundation/scripts/inspect-template.py` is deliberately preserved from the project copy — upstream re-execs into a virtualenv that is not vendored. The convention is fix upstream, then re-copy; doing it by hand is how the trees drift. `git-guardrails` and `writing-style` are not vendored by design — the first governs this repository's git rather than its output, the second is a user preference. Exits 1 under `--check` when drift is found | `python3 utils/vendor-skills.py` <br> `python3 utils/vendor-skills.py --check` <br> `python3 utils/vendor-skills.py --only deck-foundation` |

## Internal Module

| Module | Purpose |
|--------|---------|
| `_shared.py` | Shared utilities: `load_json`, `load_json_pair`, `merge_by_name` (with optional `_contributingPracticeName` provenance), `detect_kind`, `load_json_from_keleo`, `load_all_from_keleo`, `get_project_root`, `load_user_config`, `save_user_config`, `get_schema_version`, `increment_version`, `build_dependency_versions`, `MERGEABLE_ARRAYS`, `GWS` (gws CLI path, resolved from `PATH`). Not a CLI tool. |

## Typical Workflow

```bash
# 1. Generate JSON via /generate-method or /create-baseline-method skill

# 2. Assess quality
python3 utils/assess-practice.py practices/<name>/<name>.json --baseline deps/platform-adoption-kernel.json

# 3. Auto-fix common issues
python3 utils/fix-common-issues.py practices/<name>/<name>.json --fix --all

# 4. Fix competency levels if needed
python3 utils/fix-competency-levels.py practices/<name>/<name>.json deps/platform-adoption-kernel.json --fix

# 5. For methods: audit cross-practice references
python3 utils/audit-method-references.py practices/<name>/<name>.json --baseline <effective-baseline>.json

# 6. Fix alpha references if needed
python3 utils/fix-alpha-refs.py practices/<name>/<practice>.json <baseline>.json --add-redeclaration "Alpha Name" --fix

# 7. Validate against schema
python3 utils/validate-practice-json.py practices/<name>/<name>.json

# 8. Package into .keleo
python3 utils/package-keleo.py --name "<name>" --version 1.0.0 --documents <baseline>.json <practice>.json -o bundles/<name>.keleo

# 9. Re-assess to confirm (errors only)
python3 utils/assess-practice.py practices/<name>/<name>.json --baseline deps/platform-adoption-kernel.json --errors-only
```
