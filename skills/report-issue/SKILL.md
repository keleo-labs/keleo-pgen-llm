---
name: report-issue
description: Capture one or more issues, enhancements, or questions from the user and record them in the feedback/issue register for later triage
metadata:
  version: "1.0.1"
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
| 0 — Configuration | Unchanged. If the register or `issueReporterEmail` is unconfigured, ask once via the agent's question tool exactly as a first direct run would. |
| 1 — Capture | **Skip.** The drafts are already written, to the same structure, by a caller that held context you no longer have (`SKILL-STANDARD.md` §13.4). Do not re-elicit, and do not reword what the calling skill observed — you would be rewriting an orientation you cannot verify. |
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

**How a row is written is governed by `skills/feedback-foundation/drafting.md`** — the same file that governs the issues published from these rows. Read it before Step 1, along with `examples.md` beside it on your first run. This skill does not restate the structure; it declares only what is specific to capture.

`skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

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
| `config/user-config.json` | Yes | Stores the register spreadsheet ID and the reporter's email (git-ignored, per-user) |
| Remote bundle repository | Optional | Resolves document version/kind when the reported document isn't available locally |

For Google Workspace specifics (invocation patterns, auth, schema discovery), use the **`gws` skill** rather than reconstructing commands here. Everything this skill needs from Sheets is already wrapped by `utils/issue-register.py`.

---

## Step 0: Configuration

### Register

The register spreadsheet is shared with `/plan-from-feedback` and read from `config/user-config.json` (`issueRegisterSpreadsheetId`, falling back to `issueRegisterUrl`).

Confirm the register is reachable and inspect its shape:

```bash
python3 utils/issue-register.py --schema
```

If no register is configured, the utility says so. Ask the user for the register URL with the agent's question tool and save it to `config/user-config.json` as `issueRegisterUrl` + `issueRegisterSpreadsheetId` — the same keys `/plan-from-feedback` uses. Do not create a second config entry.

### Reporter Email

Every register row carries the reporter's email so triage can follow up.

1. Read `issueReporterEmail` from `config/user-config.json`
2. If absent, propose the local git identity (`git config user.email`) via the agent's question tool
3. Save the confirmed address as `issueReporterEmail` in `config/user-config.json`

Ask once, then reuse it silently on later runs.

---

## Step 1: Capture *(direct invocation only)*

The user may report one issue or several in a single message. Treat each distinct problem as its own register row — do not merge unrelated observations into one entry, and do not split one problem into several rows just because it has multiple symptoms.

### Required per issue

| Field | Guidance |
|---|---|
| **Type** | `Issue` (something is wrong), `Enhancement` (something should be added or improved), `Question` (why does it work this way?) |
| **Summary** | A specific title under 120 characters, stating the defect or the gap rather than the area it lives in. "Pattern views repeat the same alpha state" — not "pattern problem". |
| **Description** | The five moves from `drafting.md`. See below. |

### Writing the description

Follow the five moves in `skills/feedback-foundation/drafting.md` — where this
sits, what happens or what you cannot do today, why it matters, what would close it, and
the detail. A row written that way publishes cleanly later; a row that opens on an
element name has to be rescued by whoever publishes it.

Two things are specific to the register.

**Keep everything.** A row is internal, so it carries what publication cannot: the
practice and element names, the products, the engagement that prompted the report, what
the reporter was doing. Put that in move 5, not move 1 — the orientation paragraph gets
rewritten at publication and the identifying detail gets dropped, so mixing them means
both have to be untangled.

**Orient for a triager, not for a stranger.** They know the Practice Language and the
toolchain; they do not know this practice, this element, or why anyone depends on it.
One sentence saying what the element is for and who reads it is usually enough, and is
the sentence most reports leave out.

A missing-content report needs this most. "The Win Themes persona has no narrative"
states a fact that only means something to someone who already knows what Win Themes is
for and what a narrative does on a persona.

### Issues and enhancements read differently

An enhancement has no "what is wrong", and asking for one produces a row that invents a
defect to justify a request. Move 2 becomes what you cannot do today, stated as a gap
rather than as a proposal; move 3 becomes what the change is worth, which is the whole
case; move 4 becomes the shape of an acceptable answer plus the questions triage should
settle.

**Do not pre-judge the resolution.** Record the observation, the consequence, and what
an acceptable answer looks like. Triage chooses the mechanism. A row that arrives as a
finished design narrows the options before anyone has weighed them.

### Classification

Classify from what the user describes, not from the words they use — "this is annoying" about missing content is an Enhancement; "can you add validation for X" about something already broken is an Issue.

| Signal | Type |
|---|---|
| Content is wrong, inconsistent, broken, or contradicts the source methodology | Issue |
| Content is absent, thin, or could be presented better | Enhancement |
| The user wants to understand a design decision before deciding whether it's wrong | Question |

### Elicitation

Ask only for what's materially missing. Use the agent's question tool when the type is genuinely ambiguous or the target document is unclear; infer everything else from conversation context, including documents and elements already discussed in this session.

If the user is reporting something they just observed in your own output (a report, a generated practice), capture what the register needs: which document, which element, what's wrong.

**Write the orientation yourself where you can.** Users report the symptom, because they are looking at it — the context is what they already hold in their head and therefore the part they leave out. If this session has the document open, you can read what the element is for and why it matters and write move 1 from the document rather than asking. Only ask when the purpose is genuinely unclear from the source, and ask for the consequence rather than for context in the abstract: "what were you trying to do when this got in the way?" produces a usable move 3; "can you give me some context?" does not.

**Do not pad.** The structure is there to make a row readable, not long. If the user reports a typo in a description, the row is one sentence and still passes — the moves collapse. Inventing a paragraph of significance for a trivial defect wastes the triager's time more reliably than terseness does.

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
  The path may be a `bundles/<name>.keleo::documents/<doc>.json` reference when the document
  lives inside a package. Pass it through unchanged — the utilities read package members
  directly.
- **Ambiguous** — check whether the candidates are the *same* document at several versions
  or genuinely different documents. Each candidate carries a `version`, and the highest is
  flagged `"newest": true`.
  - **Same document name throughout** — take the candidate marked `newest` without asking,
    and say which version and which bundle you chose. Filing against a superseded version
    wastes triage time and invites a wrong "already fixed" closure. Re-check that the issue
    still exists in that version before drafting.
  - **Genuinely different documents** — ask the user which they meant via the agent's question tool.
- **Not found** — try `python3 utils/studio-client.py --pull "<Document Name>"` and re-resolve. If it still can't be found, record the document name as the user gave it and leave version and kind blank rather than inventing them.

Use the document's canonical `name` from the JSON, not a slug or filename — `/plan-from-feedback` resolves rows by that name.

### Element

When the issue is about a specific element, confirm it exists and capture its exact name and type:

```bash
python3 utils/extract-reference-names.py <path> --locate "<Element Name>" --json
```

- **Match** — use the returned `name` (exact spelling and case) as Selected Element and `elementType` as Element Type
- **No match, suggestions returned** — the user likely paraphrased. Confirm the intended element with the agent's question tool using the suggestions.
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
  --description "Every pattern view in the annual rhythm shows Progress at Published..." \
  --document "Example Partner Method" --document-version 1.0.2 --document-kind method \
  --element "Annual Planning Cycle" --element-type pattern \
  --secondary "Progress" --secondary-type alpha
```

Each call validates the draft before writing, so a missing field surfaces immediately. The resulting file is an array of issue objects:

```json
[
  {
    "type": "Issue",
    "summary": "Pattern views repeat the same alpha state",
    "description": "The annual operating rhythm is the pattern a partner team works through over a year. Each view is one stage of it, and the alpha states a view carries are how a reader tells what that stage moves forward.\n\nEvery view in the pattern shows Progress at Published. The alpha is therefore in the same state at the end of the year as at the start, and the pattern shows no progression at all.\n\nSomeone planning against the rhythm cannot tell which stage advances what, which is the one thing the pattern exists to tell them. It reads as deliberate rather than as an error, so it does not prompt a second look.\n\nExpected: each view carries the state that view actually advances the alpha to.\n\nDetail: all six views are affected in Example Partner Method 1.0.2. The same shape appears in two other methods generated from the same mapping guide, so the cause is likely to be upstream of this document. Observed while reviewing a sample planning document.",
    "documentName": "Example Partner Method",
    "documentVersion": "1.0.2",
    "documentKind": "method",
    "selectedElement": "Annual Planning Cycle",
    "elementType": "pattern",
    "secondaryElement": "Progress",
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
| New, Planned, or In Progress | Tell the user which row already covers it and ask via the agent's question tool: skip, or file anyway because it's materially different |
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

- **No register configured**: Ask for the URL via the agent's question tool, save it to user-config, and continue.
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
