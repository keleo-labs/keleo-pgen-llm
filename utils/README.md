# Practice Language Utilities

Scripts for validating, inspecting, fixing, and assembling Practice Language JSON files.

## Prerequisites

**Required:** Python 3.9+ (standard library only — no pip packages), `keleo-language` repo at `../../keleo-language/` (provides schema, validators, and semantic references via symlinks)

**Optional tools by feature:**

| Tool | Scripts that use it | Role |
|------|-------------------|------|
| `gws` CLI | `extract-gws-slides.py`, `studio-client.py` | Content sourcing from Google Workspace (Slides, Drive) |
| Node.js 18+ | `validate-json-schema.js` | Alternative schema validation via ajv-cli |
| Remote bundle repository | `studio-client.py`, `discover-dependencies.py --remote` | Centralised `.keleo` package storage and version management |

## Assessment & Validation

| Script | Purpose | Usage |
|--------|---------|-------|
| `assess-practice.py` | Unified quality assessment: structure, uniqueness, competency levels, cross-references, baseline references; `--online` checks asset URLs, citation URLs, reference URIs, and citations missing URLs; `--category` filters to specific issue categories | `python3 utils/assess-practice.py <file>.json [--baseline <baseline>.json] [--schema <schema>.json] [--errors-only] [--category CAT [CAT ...]] [--online]` |
| `audit-method-references.py` | Cross-practice reference auditing within a method (alpha refs, duplicates, persona consistency) | `python3 utils/audit-method-references.py <method>.json --baseline <baseline>.json [--json]` |
| `validate-practice-json.py` | Schema validation for practices/methods | `python3 utils/validate-practice-json.py <file>.json` |
| `validate-baseline-json.py` | Schema validation for baselines | `python3 utils/validate-baseline-json.py <file>.json` |
| `validate-phase-output.py` | Validate Phase 1/1.5/2 markdown output structure | `python3 utils/validate-phase-output.py <file>.md --phase <1|1.5|2>` |
| `verify-mapping-against-specs.py` | Verify Phase 2 mapping output against Gherkin specs | `python3 utils/verify-mapping-against-specs.py <mapping>.md --baseline <baseline>.json [--parent <parent>.json] [--kind baseline]` |
| `eval-skill-output.py` | Evaluate skill output quality against assertions | `python3 utils/eval-skill-output.py <practice-dir> [--specs <specs-index.json>] [--one-line]` |
| `lint-practice.py` | Combined validate-fix-revalidate loop (auto-discovers baseline/schema) | `python3 utils/lint-practice.py <practice>.json [--fix] [--one-line] [--max-iterations N]` |

## Structural Inspection

| Script | Purpose | Usage |
|--------|---------|-------|
| `practice-summary.py` | Structured practice summary for subagent prompt construction (metadata, alphas, patterns, outcomes, feature coverage) | `python3 utils/practice-summary.py <file>.json [--baseline <baseline>.json] [--json] \| --dir <dir>/` |
| `detect-schema-gaps.py` | Schema evolution gap detection (outcomes, patternGroups, priorities, references vs current schema) | `python3 utils/detect-schema-gaps.py <file>.json [--schema <schema>.json] [--json] \| --dir <dir>/` |
| `extract-reference-names.py` | Extract symbolic names from JSON (alphas, states, activities, outcomes, pattern-views, etc.) | `python3 utils/extract-reference-names.py <file>.json [--sections alphas activities outcomes pattern-views ...] [--alpha-details] [--structure] [--metadata]` |
| `extract-practice-content.py` | Extract practice content from methods or resolve dependencies; `--summary` prints a human-readable text overview | `python3 utils/extract-practice-content.py <file>.json [--output <report>.md] [--summary] [--extract-narratives <out>.json]` |
| `extract-specs.py` | Parse Gherkin scenarios from SKILL.md into specs-index.json | `python3 utils/extract-specs.py <SKILL.md> [-o <specs-index.json>]` |
| `diff-practice-json.py` | Diff two practice JSON files by element type; `--gate` mode checks for element arrays that dropped to 0 (post-Phase-3 completeness gate, exit 1 on critical) | `python3 utils/diff-practice-json.py <old>.json <new>.json [--json] [--changes-only] [--gate]` |
| `inspect-keleo.py` | Inspect `.keleo` package contents: manifest, documents, versions, dependencies | `python3 utils/inspect-keleo.py <bundle>.keleo [--json] [--list]` |
| `query-schema.py` | Query Practice Language schema `$defs` type definitions; auto-discovers `deps/language.schema.json` | `python3 utils/query-schema.py <TypeName> [--properties] [--json] [--list]` |

## Remote Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `studio-client.py` | Remote bundle repository client: fetch remote index, compare versions, download/upload `.keleo` bundles, configure credentials | `python3 utils/studio-client.py --status \| --index [--max-age N] \| --check [name] \| --pull "Name" \| --push <file>.keleo \| --configure [--json]` |

## Resolution & Merging

| Script | Purpose | Usage |
|--------|---------|-------|
| `discover-dependencies.py` | Auto-discover and resolve dependencies by scanning project directories; `--remote` checks cached remote index, `--auto-pull` downloads missing bundles | `python3 utils/discover-dependencies.py --resolve "Name" [--remote] [--auto-pull] \| --resolve-from <file>.json [--transitive] [--remote] \| --dependents "Name" \| --tiers <method>.json \| --consumers "Name" \| --list` |
| `sync-practices.py` | Sync shared practices across method directories (match by name, preserve filenames) | `python3 utils/sync-practices.py <source-dir>/ [--fix] [--rebuild-bundles] [--json]` |
| `resolve-context.py` | Unified context resolver: baselines + practices + .keleo → effective context | `python3 utils/resolve-context.py <baseline>.json [<practice>.json] [<bundle>.keleo] --transitive -o <output>.json` |
| `resolve-practice-dependencies.py` | Determine practiceDependencyNames by comparing parent and baseline alphas | `python3 utils/resolve-practice-dependencies.py --parent <parent>.json --baseline <baseline>.json --practice <practice>.json [--per-alpha]` |

## Auto-Fix Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `fix-common-issues.py` | Fix structural issues: kind, narratives, citations, contributesTo, schema violations, narrative placement, pattern compression, missing assets, nested narrative wrappers, missing versions | `python3 utils/fix-common-issues.py <file>.json [--fix] [--all] [--compress-patterns] [--fix-missing-assets] [--fix-nested-narratives] [--fix-versions]` |
| `fix-competency-levels.py` | Fix invalid competency level names against baseline | `python3 utils/fix-competency-levels.py <file>.json <baseline>.json [--fix] [--map "Old=New"]` |
| `fix-alpha-refs.py` | Add/remap/remove alpha references in practice JSON | `python3 utils/fix-alpha-refs.py <file>.json <baseline>.json [--add-redeclaration NAME] [--remap OLD NEW --state-map JSON] [--remove-alpha NAME] [--fix]` |
| `fix-citation-names.py` | Fix citation name fields to use work titles | `python3 utils/fix-citation-names.py <file>.json [--fix]` |
| `fix-citation-urls.py` | Test citation URLs and reference URIs; fix/remove broken ones (4xx/5xx); `--check-missing` detects citations missing URLs; `--no-references` skips reference URI checks; `--remove-citations` removes entire citation + references | `python3 utils/fix-citation-urls.py <file>.json [--fix] [--remove-citations] [--replace "old=new"] [--check-missing] [--no-references] [--json]` |
| `patch-practice-json.py` | Apply targeted JSON patches to practice files; `--batch-file` applies multiple element patches from a spec | `python3 utils/patch-practice-json.py <file>.json [--element-path PATH --patch-file <patch>.json] [--batch-file <spec>.json] [--rename-in COLL OLD NEW] [--dry-run]` |
| `transform-alphas.py` | Batch alpha transformations (rename, reparent, convert type, set/remove relationships, set relatesTo, strip contributesToState, remove). State renames cascade to checklists, activities, patterns, LOD backgrounds, references, outcomes, and contributesToAlphaNames. | `python3 utils/transform-alphas.py <file>.json --spec-file <spec>.json [--fix]` |
| `transform-workproducts.py` | Batch work product transformations: rename, convert relationship types (mapsTo/partOf), align LODs | `python3 utils/transform-workproducts.py <file>.json --spec <spec>.json [--fix]` |
| `apply-versioning.py` | Add schemaVersion, normalize version, populate dependencyVersions, bump/set version, ahead-of-copies | `python3 utils/apply-versioning.py [--all] [--bump patch\|minor\|major] [--set-version X.Y.Z] [--show] [--ahead-of-copies] [--fix]` |
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
| `package-keleo.py` | Create .keleo archive from constituent JSON files | `python3 utils/package-keleo.py --name "Name" --version 1.0.0 --documents <file>.json [<file2>.json] -o <output>.keleo [--verify]` |
| `rebuild-keleo.py` | Rebuild existing .keleo packages from their manifests using current source files | `python3 utils/rebuild-keleo.py [<files>.keleo] [--all] [--dry-run] [--if-changed] [--json]` |

## Refactoring & Backup

| Script | Purpose | Usage |
|--------|---------|-------|
| `backup-practice.py` | Create timestamped backup of a practice directory; `--prune N` keeps only the N most recent | `python3 utils/backup-practice.py <directory>/ [--prune N] [--prune-only]` |
| `assemble-mapping-guide.py` | Assemble Phase 2 mapping guide from cluster fragments | `python3 utils/assemble-mapping-guide.py <cluster1>.md [<cluster2>.md...] -o <output>.md` |

## Ingestion

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-gws-slides.py` | Extract Google Workspace Slides content via gws CLI | `python3 utils/extract-gws-slides.py <presentation-id> [-o <output>.md]` |
| `extract-gws-text.py` | Extract text from Google Workspace API JSON (auto-detects Slides/Docs format) | `python3 utils/extract-gws-text.py <input>.json [-o <output-dir>] [--format slides\|docs]` |

## Internal Module

| Module | Purpose |
|--------|---------|
| `_shared.py` | Shared utilities: `load_json`, `load_json_pair`, `merge_by_name` (with optional `_contributingPracticeName` provenance), `detect_kind`, `load_json_from_keleo`, `load_all_from_keleo`, `get_project_root`, `load_user_config`, `save_user_config`, `get_schema_version`, `increment_version`, `build_dependency_versions`, `MERGEABLE_ARRAYS`. Not a CLI tool. |

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
