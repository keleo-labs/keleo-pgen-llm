---
name: plan-from-feedback
description: Publish register issues to project trackers, then resolve keleo-pgen-llm issues — skills, prompts and utilities from the public tracker, practice content from the register
triggerPatterns:
  - "plan.*feedback"
  - "feedback.*plan"
  - "issue.*register"
  - "triage.*issues"
  - "process.*feedback"
  - "publish.*issues"
---

# Plan from Feedback — keleo-pgen-llm

Read `.claude/skills/feedback-foundation/FEEDBACK-FOUNDATION.md` for the workflow,
routing, sanitisation, commit linking and closing rules. This file declares only what
is specific to keleo-pgen-llm.

**Routing:** `keleo-labs/keleo-pgen-llm` — **public**, so everything published is
sanitised.

**This project also publishes for everyone.** It alone reads the register, so Step 1 of
the foundation workflow runs here and routes rows to whichever project owns them. The
other four projects only read their own trackers.

## Two queues, and the line between them

This project has an unusual split, and getting it wrong leaks.

**The tracker holds issues about the project** — its skills, prompts and utilities.
That is public code, and an issue about it is safe to publish.

**The register holds issues about generated content** — practices, methods, baselines.
Those are **not public**. They get no issue, not even a sanitised one, because the
subject of a practice is itself what is being withheld. They are worked from the
register and marked Issue State `Not Published`.

The question is never "which document was this seen in?" but **"what has to change?"**

| The fix lands in | Queue | Published |
|---|---|---|
| A prompt, a skill, a utility | tracker | yes |
| A practice, method or baseline JSON | register | **no** |
| Both | tracker for the generator half only | partly |

A row reporting a defect in a practice that was *caused* by a prompt produces one
published issue about the prompt and one unpublished register fix for the document.
Say nothing in the public issue about which practice revealed it.

The reciprocal skill is `/report-issue`, which files rows into the register with full
unredacted detail. Reporters should not self-censor — that detail is what makes triage
possible, and publication strips it later.

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards. **Do not read it
upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — prohibited; use reusable utils |
| Creating or extending a utility script | §7.4 — Utils Self-Extension Protocol |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |
| Noticing a defect no issue covers | §13 — fix it in run, or file it on the owning project |

---

## External Dependencies

| Dependency | Required? | Role |
|---|---|---|
| `gh` | Yes | GitHub issues for the three public projects |
| `glab` | For cross-project | Internal GitLab issues for keleo-studio-gas and keleo-userskillz |
| `gws` CLI | Yes | Reads and writes the register; only this project needs it |
| `.claude/user-config.json` | Yes | Register spreadsheet id and optional bundle repository credentials |

---

## Change levels

| Level | Scope | When |
|---|---|---|
| **L1** | Practice, method and baseline JSON | The issue is about content in a specific document — wrong states, missing work products, bad checklists, drift from the mapping guide. **Register-only; never published.** |
| **L2** | Skills, prompts, `utils/` | The issue reveals a generation problem that would recur in the next practice. **This is what the public tracker is for.** |
| **L3** | Escalate to keleo-language | The issue reveals a gap in the Practice Language itself. **File it there; do not edit the schema from here.** |

Most issues are L1 only. Some are L1 + L2 — fix the document and the generator that
produced it. Few are all three. Choose the minimum set.

**L1 changes are delegated, never hand-edited.** Invoke `/update-method` with the file
path, the specific fixes, and the baseline. It runs assessment, backs up, applies the
fix with the right utility, validates, rebundles, and generates a ChangeRequest for
downstream propagation. Editing practice JSON directly skips all of that.

| Fix nature | Skill |
|---|---|
| Wrong states, bad checklists, missing elements, structural drift | `/update-method` |
| Curated reference content, templates, exemplars | `/update-method` (Mode 3) |
| A practice should exist but does not | `/generate-method` |
| A new foundational framework is needed | `/create-baseline-method` |

Group issues by document: several issues against one practice become a single
invocation with a combined brief.

---

## Locating the change

```bash
python3 utils/discover-dependencies.py --resolve "<Document Name>"
```

Searches `practices/`, `baselines/`, `deps/` and `bundles/*.keleo`. An ambiguous result
carries a version on every candidate with the highest flagged `newest` — where the
candidates are one document at several versions, take the newest and say which.

A resolved path may be a `bundles/<name>.keleo::documents/<doc>.json` reference; pass it
through unchanged, since the utilities read package members directly.

Not found locally: `python3 utils/studio-client.py --pull "<Document Name>"`, then
re-resolve. Still missing: comment on the issue saying the document could not be
located, and leave it open.

---

## Validating the change

```bash
python3 utils/assess-practice.py <file>.json --baseline <baseline>.json \
  --schema deps/language.schema.json [--parent <dep>.json ...]
python3 utils/eval-skill-output.py practices/<name>/ --baseline <baseline>.json \
  --schema deps/language.schema.json --summary
```

`error_pass_rate` must be 1.0. Warnings are advisory.

Where a defect class might recur elsewhere, check before closing:

```bash
python3 utils/scan-corpus.py --category <category>
```

**Always rebundle after changing any document** — `utils/audit-bundle-freshness.py
--rebuild --fix`. A bundle carrying a stale copy reintroduces the defect downstream.

---

## Project notes

- Practice, baseline and bundle output is git-ignored. A content fix shows up in the
  repository only as a rebundled `.keleo`, so the issue comment is the durable record of
  what changed.
- `deps/` and `references/` are symlinks into keleo-language. A change that appears to
  be in `utils/validate-*.py` is an L3 change in another repository — file it there.
- The register's Document Name is a canonical document name, not a filename or slug.
