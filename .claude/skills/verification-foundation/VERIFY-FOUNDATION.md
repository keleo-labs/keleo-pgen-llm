# Verification Foundation

**Version:** 1.0.0

Shared verification protocol for the generation skills — `generate-method`,
`create-baseline-method`, `update-method`. **This is not a skill.** It is reference
material those skills read at the gate they have reached.

**Load lazily.** Read this file once per session, then read only
`verifiers/phase-<N>.md` at the gate you have reached. A Phase 1 gate must not pay for
the Phase 3 briefs.

---

## 1. Why this exists

Mechanical validation — `eval-skill-output.py`, `validate-phase-output.py`,
`verify-mapping-against-specs.py`, `assess-practice.py` — checks structure, counts and
cross-references. It cannot tell you whether a claim is true, whether a citation
supports what it is attached to, or whether an agent invented a state progression that
appears nowhere in the source.

Verification agents close that gap. They answer one question per phase: **does this
output trace back to the material it was derived from?**

---

## 2. Gate placement

A verification gate sits between the mechanical check and the user review gate:

```
producing agent(s)
  → mechanical validation      (eval-skill-output.py --phase N)
  → VERIFICATION GATE          (this document)
  → user review gate           (existing, now also shows the verdict)
  → next phase
```

Run the gate **after** mechanical validation, not instead of it. The mechanical
findings are an input to reconciliation, and a mechanically broken output wastes
verifier tokens.

| Skill | Gates |
|---|---|
| `generate-method` | Phase 1, Phase 2, Phase 3 |
| `create-baseline-method` | Phase 1, Phase 1.5, Phase 2, Phase 3 |
| `update-method` | Scoped to changed elements only — see §9 |

---

## 3. Fan-out rule

> **One verifier set per producing agent, plus the cross-cutting set once.**

Phase 1 and Phase 1.5 have one producing agent, so one verifier set. Phase 2 and
Phase 3 of a method run P producing agents (one per practice), so P verifier sets run —
each scoped to its own practice — plus one cross-practice verifier over all outputs
together.

**Concurrency cap: four verifier agents at a time.** Above that, batch. A six-practice
method at Phase 2 runs 24 practice-scoped verifiers in six batches, then the
cross-practice verifier, then one reconciler.

Launch each batch in a single message with multiple Agent tool calls so they run
concurrently.

---

## 4. The findings contract

Every verifier writes exactly one JSON file and returns a one-line summary. It does
**not** return findings in its response text — the file is the interface.

**Path:** `<output-dir>/_verification/phase-<N>-<verifier>.json`

Ask for the exact path rather than constructing it:

```bash
python3 utils/verification-gate.py practices/<name>/ --phase 2 --path-for source-fidelity
```

**Shape:**

```json
{
  "verifier": "source-fidelity",
  "summary": "Traced 34 structural claims; 1 untraceable, 2 paraphrased beyond source.",
  "findings": [
    {
      "rule": "fidelity-001",
      "severity": "error",
      "message": "Alpha 'Platform Telemetry' state 'Self-Tuning' has no basis in any source",
      "evidence": "Absent from source-a.md and source-b.md; nearest match is §4.1 'Monitoring', which stops at alerting"
    }
  ]
}
```

| Field | Rule |
|---|---|
| `rule` | A `@rule:` ID from the skill's specs index where one applies, else omit |
| `severity` | `error`, `warning` or `info` — see §5 |
| `message` | One sentence, naming the specific element. Not "some alphas are vague" |
| `evidence` | Where you looked and what you found. A finding without evidence is an opinion |

For a method practice, scope the verifier to one practice and name it in the verifier
slug: `phase-2-source-fidelity-<practice-slug>`.

---

## 5. Severity

| Severity | Meaning | Effect |
|---|---|---|
| `error` | Content is unsupported by, or contradicts, its source; or a required trace is absent | **Blocks the phase** |
| `warning` | Defensible but questionable — a judgement call the user should see | Surfaced at the review gate |
| `info` | Observation worth recording, no action implied | Surfaced at the review gate |

**Calibrate conservatively.** A verifier that flags everything is worse than no
verifier, because the gate gets ignored. Reserve `error` for content you actively
could not trace after looking, not content you did not happen to find on first pass.
Absence of a match in a skim is a `warning`; absence after a directed search of the
source is an `error`.

---

## 6. Reconciliation

After the verifiers, run **one** reconciliation agent per phase. It receives the
mechanical findings and the verifier findings and rules on each.

**Path:** `<output-dir>/_verification/phase-<N>-reconcile.json`

```json
{
  "overallVerdict": "pass-with-warnings",
  "summary": "One flagged state is in fact in source-b.md under a different heading.",
  "confirmed": [
    {
      "originalMessage": "<the finding's message, copied verbatim>",
      "verdict": "confirmed",
      "reasoning": "Why"
    }
  ],
  "newFindings": []
}
```

| Verdict | Effect on the gate |
|---|---|
| `confirmed` | Kept at its original severity |
| `false-positive` | Dismissed — reported but not blocking |
| `needs-context` | Errors downgrade to warning, stay visible |

**Copy `originalMessage` verbatim.** Matching is on the message text; a paraphrase will
not match and the finding stays as the verifier filed it. That is the safe direction,
but it produces an `unmatchedVerdicts` entry in the verdict file, which means a
reconciler ruling went nowhere.

Reconciler instruction, use as written:

> Be conservative: when in doubt, confirm a finding rather than dismissing it. Dismiss
> only when you can state the specific evidence that clears it — a section of a source
> the verifier missed, a parent-practice reference that resolves, a convention the
> verifier did not know about.

---

## 7. Running the gate

```bash
python3 utils/verification-gate.py practices/<name>/ --phase 2 --gate --summary \
  --expect source-fidelity,alpha-semantics,coverage,naming-consistency
```

`--expect` is not optional in practice. Without it, a verifier that crashed before
writing its file is indistinguishable from a verifier that found nothing — the gate
would pass on silence. List every verifier you launched.

The script writes `_verification/phase-<N>-verdict.json` and
`_verification/phase-<N>-summary.md`, prints the markdown summary, and exits 1 when a
blocking error survives.

---

## 8. Remediation loop

On `--gate` exit 1:

1. Read `_verification/phase-<N>-summary.md`.
2. For each blocking error, decide: **fix the output**, or **challenge the finding**.
3. To fix: resume the producing agent with the specific findings, or edit the output
   directly where the fix is small and unambiguous.
4. To challenge: you need evidence, not an assertion. Point at the source span the
   verifier missed. Record it as a decision (§10) — a dismissal with no evidence
   recorded is how a verification layer becomes theatre.
5. Re-run the affected verifier and the gate.

Do **not** advance to the user review gate while the gate fails. Do **not** weaken a
verifier's brief to make a finding go away — if a brief is miscalibrated, fix it in
`verifiers/phase-<N>.md` and say so in the post-completion review.

---

## 9. `update-method` scoping

Re-verifying an unchanged 60K-word mapping guide is waste. For updates:

| Mode | Verification scope |
|---|---|
| Mode 1 (full reanalysis) | Full gates, as `generate-method` |
| Mode 1B (light reanalysis) | Phase 1 and 2 gates scoped to sections the reanalysis touched |
| Mode 2 (remap) | Phase 2 and 3 gates scoped to remapped elements |
| Mode 3 (references) | `reference-citation-fidelity` only |

Scope by passing the changed-element list into the verifier brief. `diff-practice-json.py`
gives you that list for an update that already has a prior version.

---

## 10. Recording the outcome

After each gate, record the verdict alongside the existing phase record:

```bash
python3 utils/prompt-history.py practices/<name>/ --add-decision \
  --decision-label "Phase <N> Verification Gate" \
  --decision-text "<verdict>: <N> errors, <M> warnings. <What was fixed, or which findings were dismissed and on what evidence>"
```

Include the verification summary in what you present at the user review gate. The user
is reviewing the output *and* what the verifiers said about it.

---

## 11. Cost

A single practice adds roughly 12 verifier agents plus 3 reconcilers; a four-practice
method roughly 30. Sources are read a second time at Phase 1 and Phase 2. The controls
that keep this proportionate:

| Control | Rule |
|---|---|
| **Sampling** | Trace **all** structural claims (alphas, states, outcomes, work products, personas). Sample prose at 1 claim in 5, weighted toward claims carrying a citation |
| **Concurrency** | Four verifier agents at a time |
| **Effort** | `source-coverage`, `citation-integrity` and `reference-citation-fidelity` seed from util JSON and need little reasoning — run them at low effort |
| **Paths not payloads** | Give verifiers file paths. Never paste a 50K-word analysis report into a prompt |
| **Scope** | `update-method` verifies changed elements only (§9) |

---

## 12. Briefs

| File | Phase | Verifiers |
|---|---|---|
| `verifiers/phase-1.md` | Analysis | `source-fidelity`, `source-coverage`, `citation-integrity` |
| `verifiers/phase-1.5.md` | Distillation (baseline only) | `distillation-fidelity`, `focus-coherence` |
| `verifiers/phase-2.md` | Mapping | `source-fidelity`, `alpha-semantics`, `coverage`, `naming-consistency`, `cross-practice-consistency` |
| `verifiers/phase-3.md` | JSON generation | `generation-drift`, `reference-citation-fidelity` |

Each brief is literal prompt text. Pass it through to the Agent tool with the paths
filled in — do not paraphrase it, or the calibration described in §5 is lost.
