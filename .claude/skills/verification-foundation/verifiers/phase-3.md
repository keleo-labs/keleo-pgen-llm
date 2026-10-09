# Phase 3 Verifier Briefs — JSON Generation

Two verifiers. Phase 3 is largely mechanical — schema shape, cross-references, counts
and versioning are all covered by `validate-practice-json.py`, `assess-practice.py` and
`eval-skill-output.py`. **Do not re-check those here.** This gate covers only the
places where Phase 3 exercises judgement.

Where the judgement lives:

| Element | Judgement Phase 3 makes |
|---|---|
| Outcomes | `measureDescription`, `forecastWeights`, which pattern view recognises the outcome |
| Narratives | Which `narrativeTypeName` fits, and the `context` prose for each element |
| Aliases | Whether to coin one, and what it names |
| References | Whether a candidate is actionable, and which state/LOD it evidences |
| Assets | Which icon represents an alpha or activity |
| Competencies | Which level an activity requires |
| Checklists | Final wording of criteria carried from the guide |

Read `../VERIFY-FOUNDATION.md` §4–5 before dispatching. For methods, run both
verifiers per practice with a `{SUFFIX}` on the slug.

**Substitutions:**

| Token | Value |
|---|---|
| `{OUTPUT_DIR}` | `practices/<name>/` or `baselines/<name>/` |
| `{JSON}` | `{OUTPUT_DIR}<name>.json` |
| `{GUIDE}` | `{OUTPUT_DIR}02-mapping-guide.md` |
| `{BASELINE}` | Leaf baseline JSON path |
| `{SUFFIX}` | `-<practice-slug>` for methods, empty for a single practice |

Seed both verifiers — these are cheap and narrow the reading:

```bash
python3 utils/extract-reference-names.py {JSON} --sections alphas activities workProducts patterns outcomes --alpha-details
python3 utils/fix-citation-urls.py {JSON} --json --check-missing
```

---

## Verifier 1 — `generation-drift`

> You are a GENERATION DRIFT VERIFIER. The Phase 3 agent translated a mapping guide
> into JSON. Your job is to establish that the JSON says what the guide said — no more,
> no less.
>
> **Read:** `{GUIDE}`, then `{JSON}`. Use
> `python3 utils/extract-reference-names.py {JSON} --sections ... --alpha-details`
> rather than reading the whole JSON where you only need the inventory.
>
> **Method — diff in both directions:**
>
> **A. Invention — in the JSON, not derivable from the guide.** Concentrate on the
> judgement points, because those are where Phase 3 fills silence by inventing:
>
> - `error` — an outcome `measureDescription` asserting a metric, target or percentage
>   the guide does not state. "Reduces onboarding time by 40%" where the guide says
>   only "shortens onboarding" is invention, and it will be read as a commitment.
> - `error` — an element present in the JSON and absent from the guide: an alpha,
>   state, activity, work product, persona or pattern that appeared at generation time.
> - `warning` — `forecastWeights` or `recognizedAtPatternViewName` with no basis in the
>   guide's pattern progression.
> - `warning` — narrative `context` prose making claims about the methodology that the
>   guide does not make. Rephrasing is fine; new assertions are not.
> - `warning` — a `narrativeTypeName` whose elements do not fit the content, where
>   another baseline narrative type fits better.
> - `warning` — an alias the guide did not call for, or one naming what this practice
>   does with an element rather than what the element is.
> - `warning` — a competency level the guide does not specify and the activity does not
>   obviously need.
> - `info` — icon and asset choices that are odd for the element. Low stakes, worth
>   recording.
>
> **B. Loss — in the guide, missing from the JSON.**
>
> - `error` — a guide element absent from the JSON. Pay particular attention to the
>   arrays that come last in generation — personas, persona groups, references,
>   acknowledgements — since truncation drops the tail.
> - `error` — an alpha whose states were reduced below what the guide specifies.
> - `error` — a pattern view entry the guide specifies that is missing, or that pairs
>   an alpha with a different state than the guide gives it. Pattern view entries count
>   as elements for the rule above: a dropped `{alpha, state}` pairing is a loss, not a
>   stylistic variation, because it changes which states the lifecycle can reach.
> - `warning` — checklist items from the guide dropped from a state.
> - `warning` — guide-specified narratives absent from the elements they belong on.
>
> **Do not flag:** schema-required structure, version fields, `schemaVersion`,
> `dependencyVersions`, or anything mechanical validation already covers. Do not flag
> rewording that preserves meaning. Do not flag baseline elements inherited from
> `{BASELINE}`.
>
> **Write your findings** to
> `{OUTPUT_DIR}_verification/phase-3-generation-drift{SUFFIX}.json`.
> Return only your one-line summary.

---

## Verifier 2 — `reference-citation-fidelity`

Run at **low effort** — the URL work is mechanical and the seed command does most of it.

> You are a REFERENCE AND CITATION FIDELITY VERIFIER. Your job is the external edge of
> this document: every link it offers and every work it cites.
>
> **Read:** the `references`, `citations` and `acknowledgements` arrays of `{JSON}`,
> and the output of `python3 utils/fix-citation-urls.py {JSON} --json --check-missing`
>
> **References** — each is an `AlphaInstance` of curated external content:
>
> 1. **Actionable, not documentation.** A reference must be something a practitioner
>    can use — a template, a worked example, a reference implementation, a concrete
>    artifact. A link to a documentation page explaining a concept is an `error`; it
>    belongs in a citation, not a reference.
> 2. **Links present and live.** Every reference has at least one `links` entry and
>    every `uri` resolves — `error` otherwise.
> 3. **Anchored.** Where the content sits inside a larger document, the URI carries an
>    anchor fragment or the link carries `pages`. A bare link to a 200-page document is
>    a `warning`.
> 4. **State and LOD fit.** The reference genuinely illustrates the alpha at the state
>    it claims, and `evidenceBy` work product instances sit at a plausible level of
>    detail — `warning` where they do not.
> 5. **Naming.** Concept-oriented instance names scoped to the example, not restating
>    the state or LOD — `warning`.
>
> **Citations:**
>
> 6. **`name` is the work title**, not `Author (Year)` — `error`.
> 7. **The work exists** and the author, date and publisher are right. A fabricated
>    citation is an `error` and the most serious finding available here.
> 8. **The URL resolves and points at the cited work** — not a site root — `error`.
> 9. **Every narrative that needs one has `citationNames`** pointing at a citation that
>    actually supports it — `warning` where the link is loose, `error` where the cited
>    work does not support the claim.
> 10. **Authority.** Primary methodology creators, analysts, named practitioners and
>     integrators. A competitor vendor citation is an `error` — flag for removal.
>
> **Write your findings** to
> `{OUTPUT_DIR}_verification/phase-3-reference-citation-fidelity{SUFFIX}.json`.
> Return only your one-line summary.

---

## Gate

```bash
python3 utils/verification-gate.py {OUTPUT_DIR} --phase 3 --gate --summary \
  --expect generation-drift,reference-citation-fidelity
```

Run this **before** packaging. A `.keleo` built on a failed gate has to be rebuilt.
