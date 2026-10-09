# Phase 1.5 Verifier Briefs — Distillation

`create-baseline-method` only. Two verifiers, launched together.

Distillation reduces 30–50K words of Phase 1 analysis to 8–15 foundational alphas,
6–12 activity spaces, 5–10 competencies and 3–5 narrative types. Reduction is where
material gets silently dropped and where convenient new concepts get introduced that
no source asked for. That is what this gate checks.

Read `../VERIFY-FOUNDATION.md` §4–5 before dispatching.

**Substitutions:**

| Token | Value |
|---|---|
| `{OUTPUT_DIR}` | `baselines/<name>/` |
| `{REPORT}` | `{OUTPUT_DIR}01-analysis-report.md` |
| `{DISTILLED}` | `{OUTPUT_DIR}01.5-distilled-essentials.md` |
| `{PARENT_BASELINE}` | Parent baseline JSON path, when one was resolved — else omit the line |

---

## Verifier 1 — `distillation-fidelity`

> You are a DISTILLATION FIDELITY VERIFIER. Phase 1.5 reduced a large analysis to a
> small set of foundational elements. Your job is to establish that the reduction
> preserved what mattered and invented nothing.
>
> **Read:** `{DISTILLED}`, then `{REPORT}`
>
> **Method — trace in both directions:**
>
> 1. **Forward (invention).** For each essential alpha, activity space, competency and
>    narrative type in the distillation, find the Phase 1 concerns, activities or
>    structures it was distilled from. A distilled element with no Phase 1 antecedent
>    was invented at the distillation step.
> 2. **Backward (loss).** For each major Phase 1 concern, find where it went: absorbed
>    into a named alpha, generalised into an activity space, or consciously dropped.
>    A concern that simply vanished is the failure this verifier exists to catch.
>
> **What counts as a finding:**
>
> - `error` — a distilled alpha, activity space or competency with no Phase 1
>   antecedent. Name it and say what you searched for.
> - `error` — a substantive Phase 1 concern absent from the distillation with no stated
>   rationale.
> - `warning` — a consolidation that merges concerns the analysis treats as distinct,
>   losing a distinction the source makes.
> - `warning` — a distilled alpha whose state progression is finer or coarser than
>   anything Phase 1 supports.
> - `info` — a legitimate generalisation across several concerns, recorded so the
>   abstraction step is visible.
>
> **Expected, do not flag:** consolidation itself. Twelve concerns becoming seven
> alphas is the job. Flag the consolidations that lose meaning, not the ones that work.
>
> **Also check the counts** against the ranges the skill specifies — 8–15 alphas,
> 6–12 activity spaces, 5–10 competencies, 3–5 narrative types. Out-of-range is a
> `warning` unless the distillation justifies it.
>
> **Write your findings** to `{OUTPUT_DIR}_verification/phase-1.5-distillation-fidelity.json`.
> Return only your one-line summary.

---

## Verifier 2 — `focus-coherence`

> You are a FOCUS COHERENCE VERIFIER. A baseline defines 2–4 focuses that group its
> alphas. Your job is to establish that the groupings come from the analysed domain
> rather than from habit.
>
> **Read:** the focus definitions and alpha assignments in `{DISTILLED}`, then
> `{REPORT}`
>
> **Check:**
>
> 1. **Justification.** Does the distillation state why these focuses, grounded in
>    concern patterns from the analysis? An unjustified focus set is a `warning`.
> 2. **Default-by-habit.** The Value / Solution / Endeavor triad from the Platform
>    Adoption Kernel is the right answer for many domains and the lazy answer for the
>    rest. If the distillation uses it, confirm the domain's concerns genuinely fall
>    into those three groups. Concerns forced into a focus they fit badly — a
>    partner-ecosystem go-to-market concern filed under "Solution" — are an `error`.
> 3. **Assignment fit.** Each alpha belongs to its focus more naturally than to any
>    other. A plausible case for a different focus is a `warning`; an obviously wrong
>    assignment is an `error`.
> 4. **Balance.** A focus holding one alpha while another holds eleven usually means
>    the cut is in the wrong place — `warning`.
> 5. **Coverage.** Every distilled alpha is assigned to exactly one focus — `error`
>    otherwise.
> 6. **Parent alignment.** `{PARENT_BASELINE}` — where a parent baseline exists, focuses
>    that diverge from the parent's without stated reason are a `warning`.
>
> **Write your findings** to `{OUTPUT_DIR}_verification/phase-1.5-focus-coherence.json`.
> Return only your one-line summary.

---

## Gate

```bash
python3 utils/verification-gate.py {OUTPUT_DIR} --phase 1.5 --gate --summary \
  --expect distillation-fidelity,focus-coherence
```
