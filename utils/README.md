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

## Structural Inspection

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-reference-names.py` | Extract symbolic names from JSON (alphas, states, activities, etc.) | `python3 utils/extract-reference-names.py <file>.json [--sections alphas,activities,...] [--alpha-details] [--structure]` |
| `extract-practice-content.py` | Extract practice content from methods or resolve dependencies | `python3 utils/extract-practice-content.py <file>.json` |
| `diff-practice-json.py` | Diff two practice JSON files by element type | `python3 utils/diff-practice-json.py <old>.json <new>.json [--json] [--changes-only]` |

## Resolution & Merging

| Script | Purpose | Usage |
|--------|---------|-------|
| `discover-dependencies.py` | Auto-discover and resolve dependencies by scanning project directories | `python3 utils/discover-dependencies.py --resolve "Name" \| --resolve-from <file>.json [--transitive] \| --list` |
| `resolve-baseline.py` | Merge a practice with its baseline to produce an effective baseline | `python3 utils/resolve-baseline.py <practice>.json <baseline>.json [-o <output>.json]` |
| `resolve-parent-practice.py` | Merge a practice with its parent practice | `python3 utils/resolve-parent-practice.py <child>.json <parent>.json [-o <output>.json]` |
| `resolve-practice-dependencies.py` | Resolve and merge practice dependency chain | `python3 utils/resolve-practice-dependencies.py <practice>.json [--deps-dir <dir>]` |
| `assemble-method-json.py` | Assemble a method JSON from individual practice files | `python3 utils/assemble-method-json.py --name "Name" --baseline-name "Baseline" --practices p1.json p2.json -o method.json [--merge-assets] [--narrative-file narr.json]` |

## Auto-Fix Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `fix-common-issues.py` | Fix structural issues: kind, narratives, citations, contributesTo, schema violations | `python3 utils/fix-common-issues.py <file>.json [--fix] [--all]` |
| `fix-competency-levels.py` | Fix invalid competency level names against baseline | `python3 utils/fix-competency-levels.py <file>.json <baseline>.json [--fix] [--map "Old=New"]` |
| `fix-alpha-refs.py` | Add/remap/remove alpha references in practice JSON | `python3 utils/fix-alpha-refs.py <file>.json <baseline>.json [--add-redeclaration NAME] [--remap OLD NEW --state-map JSON] [--remove-alpha NAME] [--fix]` |
| `fix-redeclaration.py` | Fix alpha redeclaration compliance (restore baseline descriptions, merge checklists) | `python3 utils/fix-redeclaration.py <file>.json <baseline>.json [--fix]` |
| `fix-citation-names.py` | Fix citation name fields to use work titles | `python3 utils/fix-citation-names.py <file>.json [--fix]` |
| `fix-narrative-metadata.py` | Fix narrative metadata (names, descriptions, types) | `python3 utils/fix-narrative-metadata.py <file>.json [--fix]` |
| `fix-narrative-placement.py` | Move narratives to correct element locations | `python3 utils/fix-narrative-placement.py <file>.json [--fix]` |
| `apply-citation-corrections.py` | Apply batch citation corrections from a corrections file | `python3 utils/apply-citation-corrections.py <file>.json <corrections>.json [--fix]` |

## Refactoring & Backup

| Script | Purpose | Usage |
|--------|---------|-------|
| `backup-practice.py` | Create timestamped backup of a practice directory | `python3 utils/backup-practice.py <directory>/` |

## Internal Module

| Module | Purpose |
|--------|---------|
| `_shared.py` | Shared utilities: `load_json`, `load_json_pair`, `merge_by_name`, `detect_kind`, `collect_element_names`, `collect_alpha_state_names`, `MERGEABLE_ARRAYS`. Not a CLI tool. |

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

# 8. Re-assess to confirm (errors only)
python3 utils/assess-practice.py practices/<name>/<name>.json --baseline deps/platform-adoption-kernel.json --errors-only
```
