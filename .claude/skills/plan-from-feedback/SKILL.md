---
name: plan-from-feedback
description: Read a feedback/issue register, triage issues, plan and execute fixes across practice/method, skill/utility, and schema/semantics layers
triggerPatterns:
  - "plan.*feedback"
  - "feedback.*plan"
  - "issue.*register"
  - "triage.*issues"
  - "process.*feedback"
---

# Plan from Feedback Skill

Read an issue register (Google Sheet with structured table), triage each item, and plan/execute fixes at up to three levels: direct practice/method fixes, skill/utility improvements (keleo-pgen-llm), and schema/semantics improvements (keleo-language). Write resolution status and change details back to the register.

## Workflow Overview

**Step 0: Configuration** → Load or prompt for issue register URL; detect table structure
**Step 1: Read Issues** → Fetch register, ensure table schema is current, identify actionable items
**Step 2: Plan** → Triage each issue, determine resolution approach
**Step 3: Execute** → Make changes at appropriate level(s)
**Step 4: Update Register** → Write back status, rationale, and change details

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

## Step 0: Configuration

### Issue Register URL

The issue register URL is stored per-user in `.claude/user-config.json` (git-ignored). This file is **never committed** — each user maintains their own.

**On first use:**

1. Check if `.claude/user-config.json` exists and contains `issueRegisterUrl`
2. If not, ask the user for the issue register URL using AskUserQuestion
3. Extract the spreadsheet ID from the URL (the segment between `/d/` and `/edit` or end)
4. Save to `.claude/user-config.json`:

```json
{
  "issueRegisterUrl": "<full URL>",
  "issueRegisterSpreadsheetId": "<extracted ID>"
}
```

**On subsequent uses:**

1. Read `.claude/user-config.json`
2. Use the stored `issueRegisterSpreadsheetId`
3. If the user provides a different URL, update the config

### Keleo Studio GAS Configuration (Lazy)

The keleo-studio-gas connection is configured **only when needed** — when a bundle referenced in an issue cannot be found locally (see Bundle Resolution below). Do not prompt for these on first use.

When remote bundle access is needed and the config is missing, ask the user for:

1. **Deployment URL** — the base URL of their keleo-studio-gas instance (a Google Apps Script web app URL, e.g., `https://script.google.com/a/macros/.../exec`)
2. **API token** — a Google OAuth bearer token obtained from the GAS app's help page (Settings → API Token). Tokens expire after ~1 hour.

Save to `.claude/user-config.json`:

```json
{
  "issueRegisterUrl": "...",
  "issueRegisterSpreadsheetId": "...",
  "keleoStudioGasUrl": "<deployment URL>",
  "keleoStudioGasToken": "<OAuth bearer token>"
}
```

**Token expiry:** If an API call returns a 401 or auth error, inform the user that their token has expired and ask them to provide a fresh one from the GAS app. Update the stored token.

### Detect Table Structure

After obtaining the spreadsheet ID, fetch the spreadsheet metadata to detect the table:

```bash
gws sheets spreadsheets get --params '{"spreadsheetId": "<ID>", "includeGridData": false}' \
  | jq '.sheets[0].tables'
```

Store the table metadata (name, ID, column count, row count) in memory for use in subsequent steps. The register uses a Google Sheets structured table — all reads and writes must respect table boundaries and column definitions.

---

## Step 1: Read Issues

### Fetch the Register

Read the full table range using the gws CLI:

```bash
gws sheets +read --spreadsheet "<SPREADSHEET_ID>" --range "Sheet1"
```

### Register Table Schema

The register is a structured Google Sheets table with two column zones — **input columns** populated by the feedback form, and **resolution columns** populated by this skill.

**Input columns (form-populated):**

| Index | Column | Field |
|---|---|---|
| 0 | A | Timestamp |
| 1 | B | Email |
| 2 | C | Type (Issue, Enhancement, Question) |
| 3 | D | Summary |
| 4 | E | Description |
| 5 | F | Page |
| 6 | G | Document Name |
| 7 | H | Document Version |
| 8 | I | Document Kind |
| 9 | J | Bundle |
| 10 | K | Navigator Mode |
| 11 | L | Selected Element |
| 12 | M | Element Type |
| 13 | N | Secondary Element |
| 14 | O | Secondary Type |
| 15 | P | Status |

**Resolution columns (skill-populated):**

| Index | Column | Field |
|---|---|---|
| 16 | Q | Resolution Summary |
| 17 | R | Practice/Method Changes |
| 18 | S | keleo-pgen-llm Changes |
| 19 | T | keleo-language Changes |

### Ensure Table Schema Is Current

On each run, verify the table includes the resolution columns. If the table's `endColumnIndex` is 16 (only input columns), extend it using `gws sheets spreadsheets batchUpdate`:

1. **Extend table range** to `endColumnIndex: 20` and add resolution column definitions (indices 16-19: Resolution Summary, Practice/Method Changes, keleo-pgen-llm Changes, keleo-language Changes)
2. **Update Status dropdown** (column index 15) to include all six values: New, Planned, In Progress, Resolved, Closed, Declined

Both can be combined into a single `batchUpdate` with two `updateTable` requests.

**Idempotency:** If the table already has 20 columns and the Status dropdown already has all values, skip the schema update. Check by inspecting the table metadata from Step 0.

### Identify Actionable Items

Filter for rows where Status (column P, index 15) is **"New"**. These are the items to triage. Skip rows with any other status — they have already been processed or are in progress.

Present the actionable items to the user as a summary table before planning.

---

## Step 2: Plan (MANDATORY — Use EnterPlanMode)

**MANDATORY:** Before making any changes, enter plan mode to triage each issue.

### Triage Each Issue

For each New issue, determine:

1. **Is this actionable and in scope?** Does the issue describe a real problem or improvement to practice/method content or generation? If it's a keleo-studio UI enhancement, **omit it** (see "Omitting Out-of-Scope Issues"). If it's a duplicate, cannot reproduce, or unclear, mark as Declined.

2. **What level(s) of change are needed?**

   | Level | Scope | When to use |
   |---|---|---|
   | **L1: Practice/Method** | Fix the specific practice or method JSON that was reported | The issue is about content in a specific document (wrong states, missing work products, bad checklists, etc.) |
   | **L2: Skill/Utility** | Improve keleo-pgen-llm skills, prompts, or utilities | The issue reveals a systemic generation problem that would recur in future practices |
   | **L3: Schema/Semantics** | Improve keleo-language schema, semantics, or specifications | The issue reveals a gap in the Practice Language itself |

   Most issues need only L1. Some need L1 + L2. Few need all three. Choose the minimum set.

3. **What is the resolution approach?**

   - **Fix**: Directly resolve the reported problem
   - **Improve**: Enhance beyond what was asked (e.g., issue reports a symptom, you fix the root cause)
   - **Decline**: The reported behaviour is intentional, or the change would be harmful

### Plan Structure

For each issue, document in the plan:

```
Issue #<row>: <Summary>
  Type: <Issue|Enhancement|Question>
  Document: <Document Name> (<Document Kind> v<Version>)
  Element: <Selected Element> (<Element Type>)
  
  Assessment: <1-2 sentence analysis>
  Resolution: <Fix|Improve|Decline>
  Levels: <L1|L2|L3 or combination>
  
  L1 Actions: <what to change in the practice/method>
  L2 Actions: <what to change in skills/utilities> (if applicable)
  L3 Actions: <what to change in schema/semantics> (if applicable)
```

### Bundle Resolution

Use the Document Name and Document Kind from the register to locate source files. Resolution follows a three-tier strategy — local first, local bundles second, remote download third.

**Tiers 1-2 — Local resolution:**

```bash
python3 utils/discover-dependencies.py --resolve "<Document Name>"
```

This searches `practices/`, `baselines/`, `deps/`, and `bundles/*.keleo` automatically. If found, use the returned path. For bundle hits, extract with `unzip -o bundles/<slug>.keleo -d /tmp/keleo-extract/`.

**Tier 3 — Remote download from keleo-studio-gas:**

If `discover-dependencies.py` returns `"status": "not_found"`, attempt remote download. This triggers the lazy configuration prompt if `keleoStudioGasUrl` and `keleoStudioGasToken` are not yet in `.claude/user-config.json`.

1. Search: `curl -s -H "Authorization: Bearer <TOKEN>" '<GAS_URL>?api=packages'` → match on document name
2. Get download URL: `curl -s -H "Authorization: Bearer <TOKEN>" '<GAS_URL>?api=download&name=<DOCUMENT_NAME>'` → returns `{ downloadUrl }`
3. Download: extract Drive file ID from URL, use `gws drive files get --params '{"fileId": "<FILE_ID>", "alt": "media"}' --output bundles/<slug>.keleo`
4. Extract: `unzip -o bundles/<slug>.keleo -d /tmp/keleo-extract/` and read `manifest.json` for document layout

**If remote download also fails:** Inform the user and set the issue status to **Planned** with a note explaining the document could not be located.

### Resolution Dependencies

If multiple issues affect the same document, group them and plan a single update pass. Note dependencies between issues in the plan.

---

## Step 3: Execute

Work through the plan, one issue at a time (or grouped by document when multiple issues share one).

**Delegation principle:** This skill orchestrates triage and planning. For actual fix execution, delegate to the appropriate specialized skill rather than editing practice/method JSON directly. Each skill handles its own assessment, backup, validation, rebundling, change requests, and downstream impact reporting.

### L1: Practice/Method Changes — Delegate to Skills

**Do not manually edit practice/method/baseline JSON.** Instead, invoke the appropriate skill based on the nature of the fix:

| Fix Nature | Skill to Invoke | When |
|---|---|---|
| Fix existing content (wrong states, bad checklists, missing elements, structural issues) | `/update-method` | Most L1 issues — fix, remap, or reanalyze existing documents |
| Add/update curated reference content | `/update-method` (Mode 3) | Issues requesting exemplar content, templates, or reference links |
| Generate a new practice from source materials | `/generate-method` | Rare — when the issue reveals a practice should exist but doesn't |
| Generate a new baseline framework | `/create-baseline-method` | Rare — when a new foundational framework is needed |

**Invocation approach:**

1. **Group issues by document.** Multiple issues affecting the same document become a single skill invocation. Combine the fix requirements into one clear brief.

2. **Invoke the skill via the Skill tool** with a prompt that includes:
   - The document file path (resolved during Bundle Resolution in Step 2)
   - The specific fixes needed (from the plan)
   - The baseline path (for extension practices)
   - Any constraints or scope boundaries from the plan

3. **Let the skill handle the full lifecycle.** `/update-method` will:
   - Run assessment to determine update mode (auto-fix, remap, full-reanalysis)
   - Backup before overwriting
   - Apply fixes with proper utilities
   - Validate and re-assess
   - Rebundle into `.keleo`
   - Generate ChangeRequests for downstream propagation
   - Present Downstream Impact Report

4. **Record the skill's output** — capture what changed (file paths, nature of change, version bumps, any downstream impact) for the register update in Step 4.

**Example — fixing checklist quality issues in a practice:**

```
Invoke /update-method:
  File: practices/aws-well-architected/aws-well-architected.json
  Baseline: deps/platform-adoption-kernel.json
  Fixes needed:
    - Issue #5: Rewrite checklist names on Reliability alpha (truncated, echo descriptions)
    - Issue #8: Add missing activity for Operational Excellence alpha
    - Issue #12: Fix pattern view completeness for Security lifecycle
```

The update-method skill will assess, determine auto-fix vs remap, and execute the full workflow.

### L2: Skill/Utility Changes (keleo-pgen-llm)

- Identify the specific skill, prompt, or utility file to improve
- Make the change
- Verify it doesn't break existing functionality
- Record what changed

### L3: Schema/Semantics Changes (keleo-language)

- Identify the specific schema, semantics, or specification file to improve
- Make the change in `/Users/eseymour/code/keleo/keleo-language/`
- If schema changes: validate existing practices still pass
- Record what changed

### Declining an Issue

If an issue is declined:
- Set Status to "Declined"
- Write a clear rationale in the Resolution Summary explaining why
- No changes needed in R/S/T columns (leave empty or write "N/A")

### Omitting Out-of-Scope Issues

Issues that are **keleo-studio UI enhancements** (rendering, navigation, layout, or interaction changes that don't affect practice/method content or generation) are outside pgen-llm scope. **Omit them entirely** — do not set Status, do not write resolution columns, leave the register row unchanged for studio-side triage. Do not decline studio enhancements from pgen-llm.

---

## Step 4: Update Register

After executing changes for each issue, write back to the spreadsheet within the table structure.

### Status Values

| Status | Meaning |
|---|---|
| **New** | Incoming — awaiting triage (initial state from form) |
| **Planned** | Approved and queued for action (e.g., document not available locally) |
| **In Progress** | Active work underway (set during Step 3 execution) |
| **Resolved** | Fix completed and ready |
| **Closed** | Verified and deployed |
| **Declined** | Will not be actioned (with rationale) |

### Writing Resolution Data

For each processed row, update columns P–T using the Sheets values API. The table structure ensures banding and formatting are maintained automatically.

```bash
gws sheets spreadsheets values update \
  --params '{"spreadsheetId": "<ID>", "range": "Sheet1!P<ROW>:T<ROW>", "valueInputOption": "USER_ENTERED"}' \
  --json '{"values": [["<Status>", "<Resolution Summary>", "<Practice/Method Changes>", "<keleo-pgen-llm Changes>", "<keleo-language Changes>"]]}'
```

**Column content guidelines:**

- **P (Status)**: One of the six status values above. Must match a dropdown value.
- **Q (Resolution Summary)**: 1-3 sentences explaining the assessment and resolution approach. Include rationale for declined items.
- **R (Practice/Method Changes)**: Brief description of L1 changes. File paths and nature of change. "N/A" if no L1 changes.
- **S (keleo-pgen-llm Changes)**: Brief description of L2 changes. File paths and nature of change. "N/A" if no L2 changes.
- **T (keleo-language Changes)**: Brief description of L3 changes. File paths and nature of change. "N/A" if no L3 changes.

### Batch Updates

When processing multiple issues, update the register after each issue is resolved (not all at once). This provides incremental progress visibility in the spreadsheet.

### Table Integrity

- **Never write outside the table range.** All writes target cells within the table's column and row boundaries.
- **New rows** added by the form automatically extend the table. No action needed from this skill.
- **Status values** must match the dropdown validation. Writing an invalid status will produce a validation error in the sheet.

---

## Issue Type Handling

### Issue

A reported problem with existing content. Most common type. Typical resolutions:

- Fix incorrect states, checklists, or work products (L1)
- Fix pattern views that have repeated or meaningless states (L1)
- Remove single-alpha patterns that add no value (L1)
- Restructure work products to better serve their purpose (L1)

### Enhancement

A request for improvement or new capability. May span multiple levels:

- Add a missing element to a practice/method (L1)
- Add diagram generation capabilities (L2 — skill/utility improvement)
- Add new schema constructs (L3 — rare)

### Question

A query about why something works a certain way. Resolution is usually:

- Answer in the Resolution Summary (no code changes)
- Set Status to Resolved or Declined depending on whether a change resulted
- If the question reveals a real issue, treat as Issue

---

## Context Loading

When working on L1 changes, load the practice context:

```bash
python3 utils/resolve-context.py --transitive <practice-or-method>.json
```

This resolves baseline dependencies and produces `_effective-context.json` for the full picture.

When the practice files were downloaded from keleo-studio-gas or are only available inside a `.keleo` bundle:

```bash
# Extract the bundle
unzip -o bundles/<name>.keleo -d /tmp/keleo-extract/

# Read the manifest to understand document layout
cat /tmp/keleo-extract/manifest.json | jq '.documents'

# Copy the document you need to edit into the working directory
cp /tmp/keleo-extract/documents/<doc>.json practices/<name>/<doc>.json
```

After making L1 changes to a document that came from a remote bundle, rebundle and optionally re-upload. The skill does NOT auto-upload — inform the user that the updated bundle needs to be uploaded to keleo-studio-gas manually if desired.

### Querying Document Details Remotely

If you need to inspect a specific document without downloading the full bundle, use the document API:

```bash
curl -s -H "Authorization: Bearer <TOKEN>" \
  '<GAS_URL>?api=document&bundle=<SLUG>&path=documents/<filename>.json'
```

This returns the full document JSON directly, useful for read-only inspection during triage.

---

## Error Handling

- **Document not found locally**: Attempt remote download from keleo-studio-gas (triggers lazy config if needed). If remote also fails, set Status to "Planned" with Resolution Summary explaining the document could not be located.
- **keleo-studio-gas token expired (401/auth error)**: Inform the user their token has expired. Ask for a fresh token from the GAS app (Settings → API Token). Update `.claude/user-config.json` with the new token and retry.
- **keleo-studio-gas unreachable**: Fall back to setting Status to "Planned". Note the connection issue in the Resolution Summary.
- **Validation fails after change**: Revert the change, investigate the validation error, and fix properly. Do not suppress validation errors.
- **Google Sheet write fails**: Report the intended status update to the user in the conversation so they can update manually.
- **Table schema update fails**: Fall back to plain cell-range writes for data, and inform the user that the table structure may need manual adjustment.
- **Ambiguous issue**: Ask the user for clarification using AskUserQuestion. Set Status to "New" until clarified.

---

## Post-Completion

After processing all actionable items:

1. Present a summary of all issues processed, their resolutions, and the status updates written
2. Note any issues that were set to Planned (awaiting action) or where clarification was needed
3. If L2 or L3 changes were made, remind the user these may need separate commits in their respective repos
