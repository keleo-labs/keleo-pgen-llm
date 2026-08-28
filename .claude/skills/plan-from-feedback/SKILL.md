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

On each run, verify the table includes the resolution columns. If the table's `endColumnIndex` is 16 (only input columns), extend it:

**Step 1a: Extend the table range and add resolution column definitions:**

```bash
gws sheets spreadsheets batchUpdate \
  --params '{"spreadsheetId": "<ID>"}' \
  --json '{
    "requests": [
      {
        "updateTable": {
          "table": {
            "tableId": "<TABLE_ID>",
            "range": {
              "sheetId": 0,
              "startRowIndex": 0,
              "startColumnIndex": 0,
              "endRowIndex": <CURRENT_END_ROW>,
              "endColumnIndex": 20
            },
            "columnProperties": [
              {"columnIndex": 16, "columnName": "Resolution Summary"},
              {"columnIndex": 17, "columnName": "Practice/Method Changes"},
              {"columnIndex": 18, "columnName": "keleo-pgen-llm Changes"},
              {"columnIndex": 19, "columnName": "keleo-language Changes"}
            ]
          },
          "fields": "range,columnProperties"
        }
      }
    ]
  }'
```

**Step 1b: Update Status column dropdown to include all status values:**

The Status column (index 15) is a DROPDOWN type. Update its data validation to include all six status values:

```bash
gws sheets spreadsheets batchUpdate \
  --params '{"spreadsheetId": "<ID>"}' \
  --json '{
    "requests": [
      {
        "updateTable": {
          "table": {
            "tableId": "<TABLE_ID>",
            "columnProperties": [
              {
                "columnIndex": 15,
                "columnName": "Status",
                "columnType": "DROPDOWN",
                "dataValidationRule": {
                  "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                      {"userEnteredValue": "New"},
                      {"userEnteredValue": "Planned"},
                      {"userEnteredValue": "In Progress"},
                      {"userEnteredValue": "Resolved"},
                      {"userEnteredValue": "Closed"},
                      {"userEnteredValue": "Declined"}
                    ]
                  }
                }
              }
            ]
          },
          "fields": "columnProperties"
        }
      }
    ]
  }'
```

Steps 1a and 1b can be combined into a single batchUpdate with both requests if both are needed.

**Idempotency:** If the table already has 20 columns and the Status dropdown already has all values, skip the schema update. Check by inspecting the table metadata from Step 0.

### Identify Actionable Items

Filter for rows where Status (column P, index 15) is **"New"**. These are the items to triage. Skip rows with any other status — they have already been processed or are in progress.

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
- **Table schema update fails**: Fall back to plain cell-range writes for data, and inform the user that the table structure may need manual adjustment.
- **Ambiguous issue**: Ask the user for clarification using AskUserQuestion. Set Status to "New" until clarified.

---

## Post-Completion

After processing all actionable items:

1. Present a summary of all issues processed, their resolutions, and the status updates written
2. Note any issues that were set to Planned (awaiting action) or where clarification was needed
3. If L2 or L3 changes were made, remind the user these may need separate commits in their respective repos
