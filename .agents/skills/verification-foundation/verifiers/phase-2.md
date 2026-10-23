# Phase 2 Verifier Briefs — Mapping

Four practice-scoped verifiers plus, for methods, one cross-practice verifier.

For a method with P practices, run the four practice-scoped verifiers **per practice**
and the cross-practice verifier **once**, respecting the four-at-a-time concurrency cap
in `../VERIFY-FOUNDATION.md` §3. Suffix the verifier slug with the practice slug so the
findings files do not collide: `phase-2-source-fidelity-<practice-slug>`.

Read `../VERIFY-FOUNDATION.md` §4–5 before dispatching.

**Substitutions:**

| Token | Value |
|---|---|
| `{OUTPUT_DIR}` | `practices/<name>/` or `baselines/<name>/` |
| `{GUIDE}` | `{OUTPUT_DIR}02-mapping-guide.md`, or the per-practice guide for methods |
| `{REPORT}` | `{OUTPUT_DIR}01-analysis-report.md` |
| `{CONTEXT}` | `_effective-context.json` from Step 0.5 |
| `{BASELINE}` | Leaf baseline JSON path |
| `{SOURCES}` | Source paths/URLs from `00-prompt-history.md` |
| `{PARENTS}` | Parent practice names, when any — else state "No parent practices" |
| `{SUFFIX}` | `-<practice-slug>` for methods, empty for a single practice |

Seed the mechanical findings first; they are an input to reconciliation:

```bash
python3 utils/verify-mapping-against-specs.py {GUIDE} --baseline {BASELINE} \
  --specs .claude/skills/<skill>/specs/specs-index.json
```

---

## Verifier 1 — `source-fidelity`

New at this gate. Phase 1 fidelity does not carry forward: mapping is a second
authoring step, and states, checklist criteria and narrative context get invented here.

> You are a SOURCE FIDELITY VERIFIER for a Phase 2 mapping guide. Phase 1 already
> established that the analysis traces to its sources. Your job is the next link in the
> chain: does the mapping guide trace to the analysis and the sources, or did new
> content appear during mapping?
>
> **Read:** `{GUIDE}`, then `{REPORT}`. Consult the sources `{SOURCES}` for anything
> you cannot resolve against the analysis.
>
> **Method:** for each element the guide introduces — alpha, state, checklist item,
> work product, level of detail, activity, persona, pattern, outcome — find its
> antecedent in the analysis report. Mapping legitimately renames, consolidates and
> restructures. It does not legitimately add substance.
>
> **What counts as a finding:**
>
> - `error` — an alpha, work product, activity or outcome with no antecedent in the
>   analysis and no support in the sources.
> - `error` — a state in a progression that the analysis does not describe, where the
>   state asserts a capability rather than marking a step. Mapping may add a step to
>   complete a progression; it may not assert a maturity level the source never claims.
> - `error` — an outcome `measureDescription` asserting a metric no source supports.
> - `warning` — checklist criteria that go beyond the analysis's observable criteria.
>   Rewording is fine; new requirements are not.
> - `warning` — narrative context prose stating facts about the methodology that appear
>   in neither the analysis nor the sources.
> - `warning` — a persona with responsibilities or decision authority the analysis does
>   not give it.
> - `info` — a deliberate inference the guide states and justifies.
>
> **Do not flag:** baseline elements brought in from `{BASELINE}` — those come from the
> framework, not the source. Nor structural scaffolding the Practice Language requires,
> such as a filler state added so a pattern has a two-step progression.
>
> **Write your findings** to
> `{OUTPUT_DIR}_verification/phase-2-source-fidelity{SUFFIX}.json`.
> Return only your one-line summary.

---

## Verifier 2 — `alpha-semantics`

> You are an ALPHA RELATIONSHIP VERIFIER. Read the Phase 2 mapping guide and verify
> that alpha relationships are semantically correct.
>
> **Read:** `{GUIDE}`, `{BASELINE}`
> **Parent practices:** `{PARENTS}` — some `contributesTo` targets may resolve to parent
> practice alphas. Do NOT flag those as errors.
>
> **Check:**
>
> 1. **`contributesTo` semantic correctness.** Does each new alpha's target make sense?
>    Reason about what the alpha *is responsible for* and what the target *is*, not
>    about word overlap in their descriptions. A "Cognitive Load" alpha contributing to
>    "Team" makes sense; a "Security Policy" contributing to "Requirements" is suspect.
> 2. **Target concentration.** More than two new alphas pointing at the same parent is
>    a mapping smell — agents default rather than choosing. Verify each independently
>    and flag the ones that do not hold up on their own.
> 3. **Intermediate preference.** Where a dependency practice already specialises a
>    baseline alpha, a new alpha should usually contribute to that intermediate alpha,
>    not jump past it to the root baseline.
> 4. **`mapsTo` vs `contributesTo`.** `mapsTo` means IS-A: the alpha is a named variant
>    of the parent with the same lifecycle. `contributesTo` means subset-of: a distinct
>    progression that advances the parent. Judge on the semantic relationship; state
>    alignment is a consequence of it, not the test. A `mapsTo` variant name that
>    repeats the parent type is redundant — flag it.
> 5. **Redeclaration scope.** A redeclaration must not narrow the baseline alpha's
>    scope to this practice's domain. If the added checklists only make sense for this
>    domain, it should be a `mapsTo` variant instead.
> 6. **`relatesTo` meaningfulness.** Genuine inter-alpha dependencies, each with a
>    `direction`, not vague or redundant links.
> 7. **State progression coherence.** States increase in capability or maturity from
>    initial to mature — not a list of unordered milestones.
> 8. **Granularity.** Not so fine it should be an activity, not so broad it should
>    split, not overlapping a sibling.
>
> **Only report genuine concerns.** Do not flag things that are clearly correct. Cite
> alpha names and state names. `error` for definite problems, `warning` for
> questionable choices.
>
> **Write your findings** to
> `{OUTPUT_DIR}_verification/phase-2-alpha-semantics{SUFFIX}.json`.
> Return only your one-line summary.

---

## Verifier 3 — `coverage`

> You are a COVERAGE AND COMPLETENESS VERIFIER. Read the Phase 2 mapping guide and
> verify mapping completeness.
>
> **Read:** `{GUIDE}`, `{REPORT}`, `{BASELINE}`
>
> **Check:**
>
> 1. **Concern coverage.** Every major concern from the analysis is addressed — as an
>    alpha, activity, work product contribution or explicit checklist item. Flag dropped
>    concerns.
> 2. **Activity–state gap.** For each alpha, every state beyond the first has at least
>    one activity whose `contributesTo` references it. States without activities are
>    paper states that can never be reached.
> 3. **Pattern completeness.** Patterns reference all the practice's alphas, not a
>    subset. A missing alpha makes the lifecycle view incomplete. An alpha that only
>    appears at the end needs a two-step progression, not deletion from the pattern.
> 4. **Work product coverage.** Major evidence artifacts are captured. Flag alphas with
>    states but no work product proving them.
> 5. **Competency coverage.** Activities reference appropriate competencies at
>    appropriate levels — not everything at "Masters", not everything at "Basic".
> 6. **Outcome contributions.** Each outcome has `metricContributions` or
>    `objectiveContributions` planned. Neither is an `error` for an extension practice.
>
> **Only report genuine gaps.** Some concerns are deliberately addressed through
> checklists rather than dedicated elements — that is valid. Be specific.
>
> **Write your findings** to `{OUTPUT_DIR}_verification/phase-2-coverage{SUFFIX}.json`.
> Return only your one-line summary.

---

## Verifier 4 — `naming-consistency`

> You are a NAMING AND CONSISTENCY VERIFIER. Read the Phase 2 mapping guide and verify
> naming quality and internal consistency.
>
> **Read:** `{GUIDE}`, `{BASELINE}`
>
> **Check:**
>
> 1. **Description quality.** Single sentences capturing WHAT an element is, not HOW it
>    works. Flag multi-sentence descriptions and descriptions that read as instructions.
> 2. **Name uniqueness.** Element names unique across the whole practice.
> 3. **Alias correctness.** An alias names what the element **is** across all
>    practices, not what this practice does with it — an alias that narrows scope is an
>    `error`. Verify alias names are never used in structural references
>    (`contributesTo`, `mapsTo`, `activitySpaceName` take canonical baseline names).
> 4. **Keyword appropriateness.** Domain-specific technical terms that aid discovery.
>    Flag generic words like "management" or "process", and terms absent from the
>    content.
> 5. **Checklist quality.** Items are verifiable assertions, positively framed as
>    achievements — never as the absence of something. No meta-items that summarise or
>    reference other checklist items; each must be independently assessable.
> 6. **Narrative structure.** Narratives use `narrativeTypeName` plus
>    `narrativeContexts`, carry `citationNames`, and sit on the element they describe.
>    A narrative whose name restates its type name is a defect.
>
> **Focus on naming and consistency**, not semantic correctness — that is another
> verifier's job. Be specific.
>
> **Write your findings** to
> `{OUTPUT_DIR}_verification/phase-2-naming-consistency{SUFFIX}.json`.
> Return only your one-line summary.

---

## Verifier 5 — `cross-practice-consistency` (methods only, run once)

Seed it first:

```bash
python3 utils/discover-dependencies.py --dependents "<baseline name>" --json
```

> You are a CROSS-PRACTICE CONSISTENCY VERIFIER. Check for naming conflicts, alias
> collisions and alpha overlap across the practices of this method and any existing
> practices sharing the baseline.
>
> **Read:** every per-practice mapping guide in `{OUTPUT_DIR}`, and `{BASELINE}`
>
> **Check:**
>
> 1. **Alpha name collisions.** Two practices defining NEW alphas with the same name
>    (redeclarations of the same baseline alpha are expected and correct) — `error`,
>    this is a merge conflict.
> 2. **Alias collisions.** Two practices aliasing different canonical elements to the
>    same alias name — `error`.
> 3. **Alias–alpha conflicts.** An alias name in one practice matching an alpha name in
>    another — `error`.
> 4. **Activity name collisions.** Identically named activities in *different* activity
>    spaces — `warning`. Same name in the same space is expected.
> 5. **Keyword overlap.** Above 50% between two practices suggests they should merge or
>    one is redundant — `warning`.
> 6. **Competency level inconsistency.** One practice using "Masters" where another
>    uses "Expert" for comparable work — `warning`.
> 7. **Persona duplication.** Two practices creating near-identical personas or persona
>    groups under different names — `warning`; prefer redeclaring the existing one.
>
> **Write your findings** to
> `{OUTPUT_DIR}_verification/phase-2-cross-practice-consistency.json`.
> Return only your one-line summary.

---

## Gate

```bash
python3 utils/verification-gate.py {OUTPUT_DIR} --phase 2 --gate --summary \
  --expect source-fidelity,alpha-semantics,coverage,naming-consistency
```

For methods, list every per-practice verifier slug in `--expect`, plus
`cross-practice-consistency`.
