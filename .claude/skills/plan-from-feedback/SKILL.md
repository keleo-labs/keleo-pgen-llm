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

Read an issue register (Google Sheet), triage each item, and plan/execute fixes at up to three levels: direct practice/method fixes, skill/utility improvements (keleo-pgen-llm), and schema/semantics improvements (keleo-language). Write resolution status and change details back to the register.

## Workflow Overview

**Step 0: Configuration** → Load or prompt for issue register URL
**Step 1: Read Issues** → Fetch register, identify actionable items
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

---

## Step 1: Read Issues

### Fetch the Register

Read the issue register using the gws CLI:

```bash
gws sheets +read --spreadsheet "<SPREADSHEET_ID>" --range "Sheet1"
```

### Register Column Layout

The register has two zones — **input columns** (A–P) populated by the feedback form, and **resolution columns** (Q–T) populated by this skill.

**Input columns (A–P):**

| Col | Field |
|---|---|
| A | Timestamp |
| B | Email |
| C | Type (Issue, Enhancement, Question) |
| D | Summary |
| E | Description |
| F | Page |
| G | Document Name |
| H | Document Version |
| I | Document Kind |
| J | Bundle |
| K | Navigator Mode |
| L | Selected Element |
| M | Element Type |
| N | Secondary Element |
| O | Secondary Type |
| P | Status |

**Resolution columns (Q–T) — written by this skill:**

| Col | Field |
|---|---|
| Q | Resolution Summary |
| R | Practice/Method Changes |
| S | keleo-pgen-llm Changes |
| T | keleo-language Changes |

If the header row (row 1) does not yet contain Q–T headers, write them first:

```bash
gws sheets spreadsheets values update \
  --params '{"spreadsheetId": "<ID>", "range": "Sheet1!Q1:T1", "valueInputOption": "USER_ENTERED"}' \
  --json '{"values": [["Resolution Summary", "Practice/Method Changes", "keleo-pgen-llm Changes", "keleo-language Changes"]]}'
```

### Identify Actionable Items

Filter for rows where Status (column P) is **"New"**. These are the items to triage. Skip rows with any other status — they have already been processed or are in progress.

Present the actionable items to the user as a summary table before planning.

---

## Step 2: Plan (MANDATORY — Use EnterPlanMode)

**MANDATORY:** Before making any changes, enter plan mode to triage each issue.

### Triage Each Issue

For each New issue, determine:

1. **Is this actionable?** Does the issue describe a real problem or improvement? If not (duplicate, cannot reproduce, unclear), mark as Declined.

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

### Locating Practice/Method Files

Use the Document Name and Document Kind from the register to locate source files:

- **Practices**: `practices/<practice-name>/` or within `.keleo` bundles in `bundles/`
- **Methods**: `practices/<method-name>/` (methods live alongside practices)
- **Baselines**: `baselines/<baseline-name>/`

If the document cannot be found locally, inform the user and set the issue to **Planned** (awaiting the document).

### Resolution Dependencies

If multiple issues affect the same document, group them and plan a single update pass. Note dependencies between issues in the plan.

---

## Step 3: Execute

Work through the plan, one issue at a time (or grouped by document when multiple issues share one).

### L1: Practice/Method Changes

- Load the practice/method JSON
- Make the specific fix described in the plan
- Validate with `python3 utils/validate-practice-json.py <file>` or `python3 utils/validate-baseline-json.py <file>`
- Run `python3 utils/assess-practice.py <file> --summary` to check for regressions
- Rebundle with `python3 utils/package-keleo.py` if the file is part of a `.keleo` package
- Record what changed (file paths, nature of change)

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

---

## Step 4: Update Register

After executing changes for each issue, write back to the spreadsheet.

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

For each processed row, update columns P–T:

```bash
gws sheets spreadsheets values update \
  --params '{"spreadsheetId": "<ID>", "range": "Sheet1!P<ROW>:T<ROW>", "valueInputOption": "USER_ENTERED"}' \
  --json '{"values": [["<Status>", "<Resolution Summary>", "<Practice/Method Changes>", "<keleo-pgen-llm Changes>", "<keleo-language Changes>"]]}'
```

**Column content guidelines:**

- **P (Status)**: One of the six status values above
- **Q (Resolution Summary)**: 1-3 sentences explaining the assessment and resolution approach. Include rationale for declined items.
- **R (Practice/Method Changes)**: Brief description of L1 changes. File paths and nature of change. "N/A" if no L1 changes.
- **S (keleo-pgen-llm Changes)**: Brief description of L2 changes. File paths and nature of change. "N/A" if no L2 changes.
- **T (keleo-language Changes)**: Brief description of L3 changes. File paths and nature of change. "N/A" if no L3 changes.

### Batch Updates

When processing multiple issues, update the register after each issue is resolved (not all at once). This provides incremental progress visibility in the spreadsheet.

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

When the practice files are only available inside a `.keleo` bundle:

```bash
# Extract the bundle to inspect
unzip -l bundles/<name>.keleo  # List contents
unzip -o bundles/<name>.keleo -d /tmp/keleo-inspect/  # Extract to temp
```

---

## Error Handling

- **Document not found locally**: Set Status to "Planned" with Resolution Summary explaining the document needs to be available locally. Do not guess at changes.
- **Validation fails after change**: Revert the change, investigate the validation error, and fix properly. Do not suppress validation errors.
- **Google Sheet write fails**: Report the intended status update to the user in the conversation so they can update manually.
- **Ambiguous issue**: Ask the user for clarification using AskUserQuestion. Set Status to "New" until clarified.

---

## Post-Completion

After processing all actionable items:

1. Present a summary of all issues processed, their resolutions, and the status updates written
2. Note any issues that were set to Planned (awaiting action) or where clarification was needed
3. If L2 or L3 changes were made, remind the user these may need separate commits in their respective repos
