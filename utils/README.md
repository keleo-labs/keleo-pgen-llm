# Practice Language Utilities

Scripts for validating, inspecting, fixing, and assembling Practice Language JSON files.

## Assessment & Validation

| Script | Purpose | Usage |
|--------|---------|-------|
| `assess-practice.py` | Unified quality assessment: structure, uniqueness, competency levels, cross-references, baseline references | `python3 utils/assess-practice.py <file>.json [--baseline <baseline>.json] [--schema <schema>.json] [--errors-only]` |
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
| `extract-practice-content.py` | Extract practice content from methods or resolve dependencies | `python3 utils/extract-practice-content.py <file>.json [--output <report>.md] [--extract-narratives <out>.json]` |
| `extract-specs.py` | Parse Gherkin scenarios from SKILL.md into specs-index.json | `python3 utils/extract-specs.py <SKILL.md> [-o <specs-index.json>]` |
| `diff-practice-json.py` | Diff two practice JSON files by element type | `python3 utils/diff-practice-json.py <old>.json <new>.json [--json] [--changes-only]` |

## Resolution & Merging

| Script | Purpose | Usage |
|--------|---------|-------|
| `discover-dependencies.py` | Auto-discover and resolve dependencies by scanning project directories | `python3 utils/discover-dependencies.py --resolve "Name" \| --resolve-from <file>.json [--transitive] \| --dependents "Name" \| --tiers <method>.json \| --consumers "Name" \| --list` |
| `sync-practices.py` | Sync shared practices across method directories (match by name, preserve filenames) | `python3 utils/sync-practices.py <source-dir>/ [--fix] [--rebuild-bundles] [--json]` |
| `resolve-context.py` | Unified context resolver: baselines + practices + .keleo → effective context | `python3 utils/resolve-context.py <baseline>.json [<practice>.json] [<bundle>.keleo] --transitive -o <output>.json` |
| `resolve-practice-dependencies.py` | Determine practiceDependencyNames by comparing parent and baseline alphas | `python3 utils/resolve-practice-dependencies.py --parent <parent>.json --baseline <baseline>.json --practice <practice>.json [--per-alpha]` |

## Auto-Fix Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `fix-common-issues.py` | Fix structural issues: kind, narratives, citations, contributesTo, schema violations, narrative placement, pattern compression, missing assets | `python3 utils/fix-common-issues.py <file>.json [--fix] [--all] [--compress-patterns] [--fix-missing-assets]` |
| `fix-competency-levels.py` | Fix invalid competency level names against baseline | `python3 utils/fix-competency-levels.py <file>.json <baseline>.json [--fix] [--map "Old=New"]` |
| `fix-alpha-refs.py` | Add/remap/remove alpha references in practice JSON | `python3 utils/fix-alpha-refs.py <file>.json <baseline>.json [--add-redeclaration NAME] [--remap OLD NEW --state-map JSON] [--remove-alpha NAME] [--fix]` |
| `fix-citation-names.py` | Fix citation name fields to use work titles | `python3 utils/fix-citation-names.py <file>.json [--fix]` |
| `patch-practice-json.py` | Apply targeted JSON patches to practice files | `python3 utils/patch-practice-json.py <file>.json <patch>.json [--fix]` |
| `transform-alphas.py` | Batch alpha transformations (rename, reparent, convert type, set/remove relationships, set relatesTo, strip contributesToState, remove). State renames cascade to checklists, activities, patterns, LOD backgrounds, references, outcomes, and contributesToAlphaNames. | `python3 utils/transform-alphas.py <file>.json --spec-file <spec>.json [--fix]` |
| `transform-workproducts.py` | Batch work product transformations: rename, convert relationship types (mapsTo/partOf), align LODs | `python3 utils/transform-workproducts.py <file>.json --spec <spec>.json [--fix]` |
| `apply-versioning.py` | Add schemaVersion, normalize version, populate dependencyVersions, bump/set version, ahead-of-copies | `python3 utils/apply-versioning.py [--all] [--bump patch\|minor\|major] [--set-version X.Y.Z] [--show] [--ahead-of-copies] [--fix]` |
| `align-baseline-states.py` | Align child baseline redeclared alpha states with parent canonical names | `python3 utils/align-baseline-states.py <child>.json <parent>.json [--check] [--mapping JSON]` |
| `fix-pattern-progression.py` | Remove non-progressing alphas from pattern views and remove degenerate single-alpha patterns | `python3 utils/fix-pattern-progression.py <file>.json [--fix] [--bump minor] [--json]` |

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

## Packaging

| Script | Purpose | Usage |
|--------|---------|-------|
| `package-keleo.py` | Create .keleo archive from constituent JSON files | `python3 utils/package-keleo.py --name "Name" --version 1.0.0 --documents <file>.json [<file2>.json] -o <output>.keleo [--verify]` |
| `rebuild-keleo.py` | Rebuild existing .keleo packages from their manifests using current source files | `python3 utils/rebuild-keleo.py [<files>.keleo] [--all] [--dry-run] [--if-changed] [--json]` |

## Refactoring & Backup

| Script | Purpose | Usage |
|--------|---------|-------|
| `backup-practice.py` | Create timestamped backup of a practice directory | `python3 utils/backup-practice.py <directory>/` |
| `assemble-mapping-guide.py` | Assemble Phase 2 mapping guide from cluster fragments | `python3 utils/assemble-mapping-guide.py <cluster1>.md [<cluster2>.md...] -o <output>.md` |

## Ingestion

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-gws-slides.py` | Extract Google Workspace Slides content via gws CLI | `python3 utils/extract-gws-slides.py <presentation-id> [-o <output>.md]` |
| `extract-gws-text.py` | Extract text from Google Workspace API JSON (auto-detects Slides/Docs format) | `python3 utils/extract-gws-text.py <input>.json [-o <output-dir>] [--format slides\|docs]` |

## Internal Module

| Module | Purpose |
|--------|---------|
| `_shared.py` | Shared utilities: `load_json`, `load_json_pair`, `merge_by_name` (with optional `_contributingPracticeName` provenance), `detect_kind`, `load_json_from_keleo`, `load_all_from_keleo`, `get_schema_version`, `increment_version`, `build_dependency_versions`, `MERGEABLE_ARRAYS`. Not a CLI tool. |

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
