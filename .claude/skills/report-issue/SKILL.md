---
name: report-issue
description: Capture one or more issues, enhancements, or questions from the user and record them in the feedback/issue register for later triage
triggerPatterns:
  - "report.*issue"
  - "raise.*issue"
  - "file.*issue"
  - "log.*issue"
  - "report.*bug"
  - "report.*problem"
  - "record.*feedback"
  - "add.*to.*register"
  - "request.*enhancement"
---

# Report Issue Skill

Capture issues, enhancements, and questions from the user and append them to the feedback register as rows with Status **New**. This is the reciprocal of `/plan-from-feedback`: this skill fills the register's input columns (A–P), that skill triages those rows and fills the resolution columns (Q–T).

**Scope boundary:** this skill records issues. It does not fix them. If the user wants a fix now, file the issue, then suggest `/plan-from-feedback` (triage and resolve) or `/update-method` (direct fix).

## Workflow Overview

**Step 0: Configuration** → Resolve register ID and reporter email
**Step 1: Capture** → Elicit type, summary, and description for each issue
**Step 2: Enrich** → Resolve the document and element the issue is about
**Step 3: Check** → Validate drafts and detect duplicates
**Step 4: Confirm & Append** → Show the user what will be written, then write it

---

## Invocation Modes

Auto-detect the mode from how the skill was reached.

### Direct invocation

The user invokes `/report-issue`, with or without a description of the problem. Run
Steps 0–4 as written below, including the Step 4 confirmation round.

### Mid-execution invocation

Another skill found a defect in practice content it was consuming and is filing it under
`SKILL-STANDARD.md` §13. The request names a drafts file:

```
Mode: mid-execution
Drafts: /tmp/keleo-defects-<slug>-<timestamp>.json
Context: <which skill and phase found them>
```

In this mode:

| Step | Behaviour |
|---|---|
| 0 — Configuration | Unchanged. If the register or `issueReporterEmail` is unconfigured, ask once via AskUserQuestion exactly as a first direct run would. |
| 1 — Capture | **Skip.** The drafts are already written. Do not re-elicit, and do not reword what the calling skill observed. |
| 2 — Enrich | Run **only** for drafts missing `documentVersion`, `documentKind`, or `elementType`. Resolve them mechanically; leave blank what cannot be resolved. Never ask the user to disambiguate — pick nothing rather than guessing, and say so in the report. |
| 3 — Check | Unchanged. Validate and duplicate-check in full. |
| 4 — Append | **Append without a confirmation round.** The calling run is the authorisation. |

The guard-rails below replace the confirmation prompt — do not skip them:

- A draft that fails validation is **not** filed. Report it back unfiled rather than
  repairing it with invented detail.
- A draft matching an open row (New, Planned, In Progress) above threshold is **skipped**,
  not filed twice. Name the row that covers it.
- A draft matching a Resolved or Closed row is filed, with the earlier row number
  referenced in the description — a recurrence is worth knowing about.

Return a compact report for the calling skill to surface at its handover:

```
Filed: row 72 — [Issue] Pipeline Health declares only two states (CRM Foundations / Pipeline Health)
Filed: row 73 — [Enhancement] Win Themes persona has no narrative (CRM Foundations / Win Themes)
Skipped: "Pattern views repeat the same state" — row 68 [In Progress] already covers it
```

Do not emit any other commentary in this mode. The calling skill owns the conversation.

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

## External Dependencies

| Dependency | Required? | Role |
|---|---|---|
| `gws` CLI | Yes | Reads and writes the Google Sheets register (wrapped by `utils/issue-register.py`) |
| `.claude/user-config.json` | Yes | Stores the register spreadsheet ID and the reporter's email (git-ignored, per-user) |
| Remote bundle repository | Optional | Resolves document version/kind when the reported document isn't available locally |

For Google Workspace specifics (invocation patterns, auth, schema discovery), use the **`gws` skill** rather than reconstructing commands here. Everything this skill needs from Sheets is already wrapped by `utils/issue-register.py`.

---

## Step 0: Configuration

### Register

The register spreadsheet is shared with `/plan-from-feedback` and read from `.claude/user-config.json` (`issueRegisterSpreadsheetId`, falling back to `issueRegisterUrl`).

Confirm the register is reachable and inspect its shape:

```bash
python3 utils/issue-register.py --schema
```

If no register is configured, the utility says so. Ask the user for the register URL with AskUserQuestion and save it to `.claude/user-config.json` as `issueRegisterUrl` + `issueRegisterSpreadsheetId` — the same keys `/plan-from-feedback` uses. Do not create a second config entry.

### Reporter Email

Every register row carries the reporter's email so triage can follow up.

1. Read `issueReporterEmail` from `.claude/user-config.json`
2. If absent, propose the local git identity (`git config user.email`) via AskUserQuestion
3. Save the confirmed address as `issueReporterEmail` in `.claude/user-config.json`

Ask once, then reuse it silently on later runs.

---

## Step 1: Capture *(direct invocation only)*

The user may report one issue or several in a single message. Treat each distinct problem as its own register row — do not merge unrelated observations into one entry, and do not split one problem into several rows just because it has multiple symptoms.

### Required per issue

| Field | Guidance |
|---|---|
| **Type** | `Issue` (something is wrong), `Enhancement` (something should be added or improved), `Question` (why does it work this way?) |
| **Summary** | A specific title under 120 characters. "Pattern views repeat the same alpha state" — not "pattern problem". |
| **Description** | What was observed, where, and what was expected instead. Enough that a triager can act without going back to the reporter. |

### Classification

Classify from what the user describes, not from the words they use — "this is annoying" about missing content is an Enhancement; "can you add validation for X" about something already broken is an Issue.

| Signal | Type |
|---|---|
| Content is wrong, inconsistent, broken, or contradicts the source methodology | Issue |
| Content is absent, thin, or could be presented better | Enhancement |
| The user wants to understand a design decision before deciding whether it's wrong | Question |

### Elicitation

Ask only for what's materially missing. Use AskUserQuestion when the type is genuinely ambiguous or the target document is unclear; infer everything else from conversation context, including documents and elements already discussed in this session.

If the user is reporting something they just observed in your own output (a report, a generated practice), capture what the register needs: which document, which element, what's wrong.

**Do not editorialise.** Record the user's observation and expectation. Triage decides the resolution; do not pre-judge it in the description.

---

## Step 2: Enrich Document and Element Context

Register rows are only actionable if triage can find what the issue is about. Resolve these mechanically — never guess a version or element type.

### Document

```bash
python3 utils/discover-dependencies.py --resolve "<Document Name>"
```

- **Resolved** — use the returned path, and read `version` and `kind` from the document:
  ```bash
  python3 utils/extract-reference-names.py <path> --metadata
  ```
- **Ambiguous** — multiple candidates; ask the user which document they meant via AskUserQuestion
- **Not found** — try `python3 utils/studio-client.py --pull "<Document Name>"` and re-resolve. If it still can't be found, record the document name as the user gave it and leave version and kind blank rather than inventing them.

Use the document's canonical `name` from the JSON, not a slug or filename — `/plan-from-feedback` resolves rows by that name.

### Element

When the issue is about a specific element, confirm it exists and capture its exact name and type:

```bash
python3 utils/extract-reference-names.py <path> --locate "<Element Name>" --json
```

- **Match** — use the returned `name` (exact spelling and case) as Selected Element and `elementType` as Element Type
- **No match, suggestions returned** — the user likely paraphrased. Confirm the intended element with AskUserQuestion using the suggestions.
- **No match, no suggestions** — if the issue is that the element is *missing*, that's valid: leave Selected Element blank and name the expected element in the description instead.

When an issue concerns a relationship between two elements (an alpha's `relatesTo`, a work product evidencing a state), record the second element as Secondary Element / Secondary Type using the same lookup.

### Studio UI issues

An issue about Keleo Studio rendering, navigation, or interaction is still worth recording — `/plan-from-feedback` omits them from pgen-llm triage and leaves them for studio-side review. Record them with document and element context where it applies, and describe the UI behaviour plainly.

---

## Step 3: Validate and Check for Duplicates

In mid-execution mode the drafts file already exists — skip to the validation commands below.

In direct mode, build the drafts file outside the repo (`/tmp/keleo-issues-<timestamp>.json`), one issue at a time:

```bash
python3 utils/issue-register.py --add-draft /tmp/keleo-issues-<timestamp>.json \
  --type Issue --summary "Pattern views repeat the same alpha state" \
  --description "Every pattern view in the annual rhythm shows Ecosystem Discover at Published..." \
  --document "EcoTech Sales Foundations" --document-version 1.0.2 --document-kind method \
  --element "Partner Ecosystem Annual Operating Rhythm" --element-type pattern \
  --secondary "Ecosystem Discover" --secondary-type alpha
```

Each call validates the draft before writing, so a missing field surfaces immediately. The resulting file is an array of issue objects:

```json
[
  {
    "type": "Issue",
    "summary": "Pattern views repeat the same alpha state",
    "description": "Every pattern view in the annual rhythm shows Ecosystem Discover at Published, so the lifecycle shows no progression. Each view should show the state that view actually advances the alpha to.",
    "documentName": "EcoTech Sales Foundations",
    "documentVersion": "1.0.2",
    "documentKind": "method",
    "selectedElement": "Partner Ecosystem Annual Operating Rhythm",
    "elementType": "pattern",
    "secondaryElement": "Ecosystem Discover",
    "secondaryType": "alpha"
  }
]
```

Timestamp, Email, Page, and Status are set by the utility — do not populate them.

Validate and check for duplicates:

```bash
python3 utils/issue-register.py --validate /tmp/keleo-issues-<timestamp>.json
python3 utils/issue-register.py --check-duplicates /tmp/keleo-issues-<timestamp>.json
```

Fix every validation **error** before proceeding. Act on **warnings** — an over-long summary or an unknown element type means the capture needs tightening, not overriding.

### Handling duplicates

In mid-execution mode, apply the guard-rails from Invocation Modes instead of the table below: skip open duplicates, file recurrences, report both.

| Existing row status | Action |
|---|---|
| New, Planned, or In Progress | Tell the user which row already covers it and ask via AskUserQuestion: skip, or file anyway because it's materially different |
| Resolved or Closed | Mention the earlier row — this may be a regression. Default to filing, and reference the earlier row number in the description. |
| Declined | Mention the earlier decision and ask whether the new report adds grounds to reconsider |

Never silently drop an issue the user asked you to file, and never silently file a duplicate.

---

## Step 4: Confirm and Append

In mid-execution mode, skip the confirmation and go straight to the append command, then return the compact report described in Invocation Modes.

In direct mode: the register is shared with other people. **Always show the user what will be written and get confirmation before appending** — this is an outward-facing write, and an inaccurate row costs a triager's time.

Present the drafts as a compact table (Type, Summary, Document, Element) plus the full description text for each, then confirm.

Preview the exact rows if the user wants to see them as the register will:

```bash
python3 utils/issue-register.py --append /tmp/keleo-issues-<timestamp>.json --dry-run
```

On confirmation:

```bash
python3 utils/issue-register.py --append /tmp/keleo-issues-<timestamp>.json
```

Report back the row numbers written and the register URL. Mention that `/plan-from-feedback` picks up rows with Status New on its next run.

---

## Error Handling

- **No register configured**: Ask for the URL via AskUserQuestion, save it to user-config, and continue.
- **Google auth expired**: `issue-register.py` detects auth failures and reports them. Ask the user to run `gws auth status`, then `! gws auth login` interactively — you cannot complete this for them.
- **Append fails**: Report the drafts to the user in the conversation so nothing is lost, and keep the scratch JSON file so the append can be retried without recapturing.
- **Document can't be resolved**: File the issue with the document name as given and blank version/kind. A locatable issue with partial metadata beats no issue.
- **User reports something already fixed locally**: Say so and ask whether they still want it recorded — an already-fixed problem may still warrant a register entry if the fix isn't released.

---

## Post-Completion

1. Confirm the rows written, with row numbers.
2. If any issue was skipped as a duplicate, say which existing row covers it.
3. Delete nothing from the register — this skill only appends.
4. Run the Post-Completion Review (SKILL-STANDARD §11): if any part of the capture needed ad-hoc inline logic, remediate it into `utils/` immediately.
