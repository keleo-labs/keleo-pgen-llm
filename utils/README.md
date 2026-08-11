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
| `eval-skill-output.py` | Evaluate skill output quality against assertions | `python3 utils/eval-skill-output.py <practice-dir> [--specs <specs-index.json>]` |

## Structural Inspection

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-reference-names.py` | Extract symbolic names from JSON (alphas, states, activities, etc.) | `python3 utils/extract-reference-names.py <file>.json [--sections alphas,activities,...] [--alpha-details] [--structure]` |
| `extract-practice-content.py` | Extract practice content from methods or resolve dependencies | `python3 utils/extract-practice-content.py <file>.json` |
| `extract-specs.py` | Parse Gherkin scenarios from SKILL.md into specs-index.json | `python3 utils/extract-specs.py <SKILL.md> [-o <specs-index.json>]` |
| `diff-practice-json.py` | Diff two practice JSON files by element type | `python3 utils/diff-practice-json.py <old>.json <new>.json [--json] [--changes-only]` |

## Resolution & Merging

| Script | Purpose | Usage |
|--------|---------|-------|
| `discover-dependencies.py` | Auto-discover and resolve dependencies by scanning project directories | `python3 utils/discover-dependencies.py --resolve "Name" \| --resolve-from <file>.json [--transitive] \| --dependents "Name" \| --list` |
| `resolve-context.py` | Unified context resolver: baselines + practices + .keleo → effective context | `python3 utils/resolve-context.py <baseline>.json [<practice>.json] [<bundle>.keleo] --transitive -o <output>.json` |

## Auto-Fix Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `fix-common-issues.py` | Fix structural issues: kind, narratives, citations, contributesTo, schema violations, narrative placement | `python3 utils/fix-common-issues.py <file>.json [--fix] [--all]` |
| `fix-competency-levels.py` | Fix invalid competency level names against baseline | `python3 utils/fix-competency-levels.py <file>.json <baseline>.json [--fix] [--map "Old=New"]` |
| `fix-alpha-refs.py` | Add/remap/remove alpha references in practice JSON | `python3 utils/fix-alpha-refs.py <file>.json <baseline>.json [--add-redeclaration NAME] [--remap OLD NEW --state-map JSON] [--remove-alpha NAME] [--fix]` |
| `fix-method-redeclarations.py` | Fix redeclaration issues across all practices in a method | `python3 utils/fix-method-redeclarations.py <method>.json <baseline>.json [--fix]` |
| `fix-citation-names.py` | Fix citation name fields to use work titles | `python3 utils/fix-citation-names.py <file>.json [--fix]` |
| `patch-practice-json.py` | Apply targeted JSON patches to practice files | `python3 utils/patch-practice-json.py <file>.json <patch>.json [--fix]` |
| `transform-alphas.py` | Batch alpha transformations (rename, reparent, convert type) | `python3 utils/transform-alphas.py <file>.json [--fix]` |
| `apply-change-request.py` | Apply ChangeRequest nameChanges/removals to downstream JSON | `python3 utils/apply-change-request.py <change-request>.json <target>.json [--fix]` |

## Packaging

| Script | Purpose | Usage |
|--------|---------|-------|
| `package-keleo.py` | Create .keleo archive from constituent JSON files | `python3 utils/package-keleo.py --name "Name" --version 1.0.0 --documents <file>.json [<file2>.json] -o <output>.keleo` |
| `bundle-practices.py` | Batch-package practice directories into .keleo archives | `python3 utils/bundle-practices.py <dir1> [<dir2>...] [--baseline <baseline>.json]` |

## Refactoring & Backup

| Script | Purpose | Usage |
|--------|---------|-------|
| `backup-practice.py` | Create timestamped backup of a practice directory | `python3 utils/backup-practice.py <directory>/` |
| `assemble-mapping-guide.py` | Assemble Phase 2 mapping guide from cluster fragments | `python3 utils/assemble-mapping-guide.py <cluster1>.md [<cluster2>.md...] -o <output>.md` |

## Ingestion

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-gws-slides.py` | Extract Google Workspace Slides content via gws CLI | `python3 utils/extract-gws-slides.py <presentation-id> [-o <output>.md]` |

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
