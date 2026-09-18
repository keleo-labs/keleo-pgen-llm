# Improve Tooling

Improve skills and utility scripts based on user feedback, session observations, or mid-execution needs. Creates, extends, refactors, or consolidates utils; proposes and applies skill instruction improvements.

**Trigger**: `/improve-tooling`, or invoked by another skill via the Skill tool when it needs a mechanical helper function.

## Supporting Standards

| Standard | Location | Scope |
|----------|----------|-------|
| Skill Specification Standard | `.claude/skills/SKILL-STANDARD.md` | §7.3 No Inline Scripts, §7.4 Utils Self-Extension Protocol, §11 Post-Completion Review |
| Utils Registry | `utils/README.md` | Canonical registry of all utility scripts |
| Shared Module | `utils/_shared.py` | Common functions: `load_json`, `merge_by_name`, `detect_kind`, `increment_version`, etc. |
| Global Coding Standards | `~/.claude/CLAUDE.md` | Reusable utility scripts over ad hoc inline scripts |

---

## Invocation Modes

This skill operates in two modes, auto-detected from context:

### Direct Invocation

The user explicitly invokes `/improve-tooling` with a request. Examples:
- "Add a `--count` flag to `extract-reference-names.py`"
- "The Phase 3 fix-validate loop is slow — consolidate it into a single pipeline script"
- "After running `/generate-method`, I noticed the LLM was doing checklist name validation manually — script it"

**For util changes**: Assess, implement, verify, and apply directly (mechanical, low risk).

**For skill improvements**: Enter plan mode, propose changes with rationale, apply after user approval.

### Mid-Execution Invocation

Another skill discovers it needs a mechanical helper that doesn't exist. It invokes `/improve-tooling` via the Skill tool with a structured request:

```
Need: <what the helper should do>
Context: <which skill/phase encountered the need>
Mechanical test: <a concrete input→output example proving this is scriptable>
```

In mid-execution mode:
- Do NOT enter plan mode or prompt the user
- Auto-proceed through all phases (per SKILL-STANDARD.md §7.4 Step 4)
- Return a brief report of what was created/extended so the calling skill can use it immediately

---

## Workflow

### Phase 1: Assessment

1. **Read the registry.** Read `utils/README.md` to understand current capabilities.

2. **Locate existing coverage.** If a specific util is named, read it. If the request is a capability need, search for existing scripts that might cover it:
   - Run `python3 utils/<candidate>.py --help` for promising matches
   - Grep for relevant function names or keywords in `utils/`

3. **Classify the request:**

   | Classification | Criteria | Action |
   |---------------|----------|--------|
   | **Use existing** | An existing script already covers the need | Report the script and usage to caller |
   | **Extend existing** | An existing script is close but missing a feature | Modify that script |
   | **Create new** | No existing script covers the need | Write a new script in `utils/` |
   | **Refactor/merge** | Overlapping scripts need consolidation | Merge into one, delete originals |
   | **Improve skill** | Skill instructions need updating (direct mode only) | Enter plan mode, propose changes |
   | **Reject** | The request requires semantic LLM judgment | Explain why and suggest the caller handle it in the LLM layer |

4. **Apply the mechanical-vs-semantic gate** (see below).

### Phase 2: Implementation

**For utils (both modes):**

Follow the conventions established by peer scripts:
- Use `argparse` with `--help` documentation
- Import from `utils/_shared.py` where applicable (`load_json`, `detect_kind`, `increment_version`, etc.)
- Include `--fix` for write operations (default: dry-run/report)
- Include `--dry-run` for preview where appropriate
- Use consistent positional file arguments
- Write to stdout for reports, stderr for warnings
- Exit 0 on success, 1 on validation failure, 2 on usage error

When extending an existing script:
- Follow the script's existing patterns (argument style, output format, error handling)
- Do not change existing CLI interfaces — add new flags/modes alongside

When creating a new script:
- Name it with kebab-case matching its primary verb: `verb-noun.py`
- Add the shebang line: `#!/usr/bin/env python3`
- Include a docstring with purpose and usage examples

**For skill improvements (direct mode only, requires plan mode approval):**

1. Enter plan mode with proposed changes
2. Read the skill's SKILL.md and contract.feature
3. Identify the specific instruction gap or improvement
4. Present the change rationale and proposed edits
5. Apply after user approval via ExitPlanMode
6. If Gherkin scenarios changed, re-run `python3 utils/extract-specs.py <SKILL.md>` to regenerate specs

### Phase 3: Verification

1. **CLI check**: Run `python3 utils/<script>.py --help` to confirm argparse works
2. **Smoke test**: Run the util against a real file from `practices/`, `baselines/`, or `deps/` to confirm it produces valid output
3. **Regression check**: If extending an existing script, confirm that existing usage patterns still work (run with the same arguments that skills already use)
4. **Spec regeneration**: If skill Gherkin scenarios changed, run `python3 utils/extract-specs.py <SKILL.md> -o <specs-index.json>`

### Phase 4: Registry & Report

1. **Update `utils/README.md`**: Add new scripts to the appropriate section; update entries for extended scripts; remove entries for deleted scripts
2. **Report**: Tell the caller (user or calling skill) what was created/extended/modified, with usage examples

---

## Mechanical vs. Semantic Decision Gate

### Feature: Mechanical-Semantic Boundary (@rule:process-800)

#### Scenario: Request is mechanical (@rule:process-801)
- Given: A request to create or extend a utility script
- When: The operation's input/output is fully determined by rules and data
- And: The operation is idempotent (running twice produces the same result)
- And: No domain knowledge beyond the input data is required
- Then: Proceed with implementation

**Mechanical examples**: rename elements, validate structure, merge JSON files, extract fields, calculate diffs, fix cross-reference consistency, apply version bumps, test URL reachability.

#### Scenario: Request is semantic (@rule:process-802)
- Given: A request to create or extend a utility script
- When: The operation requires understanding meaning, quality, or fitness
- Or: The output depends on context not present in the input data
- Or: Human judgment is needed to evaluate correctness
- Then: Reject the request
- And: Explain why the task requires LLM judgment
- And: Suggest the caller handle it in the skill's LLM layer (prompt instructions or subagent)

**Semantic examples**: improve checklist wording, decide which patterns to keep, rewrite descriptions for clarity, choose element groupings, assess narrative quality, determine whether an alpha should use `contributesTo` or `mapsTo`.

### Feature: Scope Guard (@rule:process-803)

#### Scenario: Request is practice-specific (@rule:process-804)
- Given: A request to create a utility script
- When: The script would only work for one specific practice, method, or baseline
- Or: The script hardcodes practice names, file paths, or domain-specific data
- Then: Reject the request
- And: Suggest either generalizing the approach or handling it as a one-off in the skill's workflow

#### Scenario: Hardcoded data should be externalized (@rule:process-805)
- Given: A utility script contains practice-specific constants, mappings, or IDs
- When: The data could be provided via a config file or command-line argument
- Then: Externalize the data into a `--config` or `--assignments` JSON file
- And: The script's logic remains general-purpose

---

## Quality Rules

### Feature: Utils Convention Compliance (@rule:structural-806)

#### Scenario: New utility follows conventions (@rule:structural-807)
- Given: A new utility script is created
- Then: It uses `argparse` with `--help`
- And: It imports from `utils/_shared.py` where applicable
- And: It uses `--fix` for write operations
- And: It follows kebab-case naming: `verb-noun.py`
- And: It includes a docstring with purpose and usage examples

#### Scenario: Extended utility preserves interfaces (@rule:structural-808)
- Given: An existing utility is extended
- Then: All existing CLI arguments and flags still work identically
- And: New functionality is added as new flags or modes

### Feature: Registry Currency (@rule:process-809)

#### Scenario: Registry updated after changes (@rule:process-810)
- Given: A utility was created, extended, or removed
- Then: `utils/README.md` reflects the change
- And: New scripts appear in the appropriate section
- And: Removed scripts are no longer listed
