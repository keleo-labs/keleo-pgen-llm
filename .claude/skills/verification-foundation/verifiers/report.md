# Report Verifier Briefs

Used by all five reporting skills — `method-based-report`, `reference-architecture`,
`project-plan`, `decision-analysis`, `document-review`.

Reports have **one gate**, not four. The reporting workflow has four steps but only
one durable artifact: Steps 1–2 produce in-context analysis rather than files, and
Step 0 is already user-gated in plan mode, so scope and narrative choice are approved
before writing starts. There is nothing to verify until Step 3 writes the markdown.

The gate runs **before** any PDF export or Google Doc publish. Publishing a report
that fails means republishing it.

Read `../VERIFY-FOUNDATION.md` §4–5 for the findings contract and severity
calibration before dispatching. Four base verifiers plus one type-specific, launched
together.

**Substitutions:**

| Token | Value |
|---|---|
| `{REPORT_DIR}` | `reports/<report-slug>/` |
| `{REPORT}` | `{REPORT_DIR}<report-slug>.md` |
| `{CONTEXT}` | `_effective-context.json` from Step 1 |
| `{FRAMEWORKS}` | Practice/method names the report claims as its analytical framework |
| `{SOURCES}` | Source documents supplied by the user, from `00-prompt-history.md` |
| `{TYPE_CONCERN}` | The row for this skill from the per-type table below |

Seed the verifiers first — this is cheap and narrows what they have to read:

```bash
python3 utils/lint-report.py {REPORT} --json
```

---

## Verifier 1 — `source-fidelity`

> You are a SOURCE FIDELITY VERIFIER for a generated report. Your job is to establish
> whether the report's claims are grounded, or whether some were invented.
>
> **Read:** `{REPORT}`, then `{CONTEXT}` and the sources `{SOURCES}`.
>
> **Method:** work through the report claim by claim. For each factual claim,
> statistic, benchmark, timescale, cost figure or attributed recommendation, decide
> which of three things it is:
>
> 1. **Grounded in a source** — trace it to the specific place and confirm the source
>    says what the report says it says.
> 2. **The report's own analysis** — synthesis, judgement or recommendation the report
>    is making itself. This is legitimate and deliberately uncited: the reporting
>    foundation tells authors not to cite their own synthesis. It must still be
>    *supportable* by what the report has established, and must read as analysis
>    rather than as established fact.
> 3. **Invented** — stated as fact, traceable to nothing.
>
> Separating (2) from (3) is the whole job. A recommendation that follows from the
> analysis is category 2. A number that appears from nowhere is category 3, however
> reasonable it sounds.
>
> **What counts as a finding:**
>
> - `error` — a quantified claim (percentage, cost, duration, throughput, headcount)
>   with no source. Invented numbers are the most damaging thing a report can carry,
>   because readers act on them. Name the figure and say where you looked.
> - `error` — a claim that contradicts its source, or that attributes to a source
>   something the source does not say.
> - `error` — a claim presented as established industry fact that is actually the
>   report's own inference.
> - `warning` — a claim traceable in substance but overstated: the source describes
>   one deployment, the report generalises to all.
> - `warning` — the report's own analysis stated with more confidence than its
>   grounding supports.
> - `info` — legitimate synthesis across several sources that no single source states,
>   recorded so it is visible as the report's contribution.
>
> **Do not flag:** general knowledge, widely accepted technical facts, or the report's
> recommendations where they follow from what it has established. Reports are *meant*
> to contribute analysis.
>
> Tag every finding with `"rule": "report-720"`.
>
> **Write your findings** to `{REPORT_DIR}_verification/report-source-fidelity.json`
> in the shape given in VERIFY-FOUNDATION.md §4. Return only your one-line summary.

---

## Verifier 2 — `citation-integrity`

Run at **low effort** — the seed output does most of the mechanical work.

> You are a CITATION INTEGRITY VERIFIER for a generated report.
>
> **Read:** the `## References` section of `{REPORT}`, the in-text citations, and the
> output of `python3 utils/lint-report.py {REPORT} --json`.
>
> `lint-report.py` already checks that every in-text citation has a References entry
> and vice versa. **Do not re-check correspondence.** Your job is whether the cited
> works are real and whether they support what is attached to them.
>
> **Check each citation:**
>
> 1. **The work exists.** Author, date, title and publisher match a real publication.
>    A plausible-looking citation for a work that does not exist is an `error` and the
>    most serious finding available here.
> 2. **The URL resolves and points at the work** — not a site root, not a search page
>    standing in for a document. `error` otherwise.
>
>    **Distinguish link rot from a bad citation.** Vendor documentation sites rotate
>    versions: a URL that was correct when the report was written now redirects to a
>    product landing page because that version is no longer served. If the work plainly
>    exists and only the link has rotted, that is a `warning` — the author did nothing
>    wrong, and a report older than one docs release cycle would otherwise fail the
>    gate on link rot alone. Reserve `error` for a URL that never pointed at the cited
>    work. Where you can find the live equivalent, name it in your evidence so the fix
>    is a copy-paste.
> 3. **Anchored where the claim is specific.** A citation supporting a claim about one
>    section of a long document should link to that section. Missing anchor is a
>    `warning`.
> 4. **The source supports the claim.** For each in-text citation, confirm the cited
>    work actually says what the sentence attributes to it. Fetch the source where you
>    can. A citation attached to a claim it does not support is an `error` — this is
>    the failure mode that makes a report look rigorous while being wrong.
> 5. **Authority.** Primary creators of the methodology, analysts, named practitioners,
>    integrators. A competitor vendor citation is an `error` — flag for removal, not
>    rewording.
> 6. **Density.** 5–15 in-text citations for a standard report. Materially outside that
>    band is a `warning`, not an error — a short focused report may legitimately sit low.
>
> Tag every finding with `"rule": "report-721"`.
>
> **Write your findings** to
> `{REPORT_DIR}_verification/report-citation-integrity.json`.
> Return only your one-line summary.

---

## Verifier 3 — `domain-grounding`

The report-specific verifier. A report can be fluent, plausible prose that quietly
ignores the practice it claims to be built on, and nothing else catches that.

> You are a DOMAIN GROUNDING VERIFIER. A report claims to be structured by a narrative
> framework and informed by a practice or method. Your job is to establish that it
> actually is, rather than being generic prose with a framework named at the end.
>
> **Read:** `{REPORT}`, then `{CONTEXT}`. The frameworks the report claims are
> `{FRAMEWORKS}`.
>
> **Check:**
>
> 1. **Narrative structure actually shaped the report** (`report-601`). Each top-level
>    section should map to an element of the selected narrative type, in order. A
>    report whose sections are generic — Introduction, Background, Conclusion — where a
>    specific narrative type was selected has not used it. `error` if the mapping
>    cannot be reconstructed at all; `warning` if sections drift from the element
>    sequence.
> 2. **Practice knowledge is present** (`report-602`). The analytical dimensions,
>    evaluation criteria and recommendations should visibly derive from the practice's
>    alphas, states, work products and activities — translated into plain language, but
>    traceable back. `error` if the report would read identically with no practice at
>    all. Name which parts of the effective context went unused.
> 3. **Attribution is accurate** (`report-603`, `report-610`). The closing line names
>    frameworks the report genuinely drew on — not every framework in the effective
>    context, and not one it ignored. `error` for a framework named but unused.
> 4. **No Keleo vocabulary leaked** (`report-600`). `lint-report.py --checks
>    terminology` catches the obvious terms; you are looking for the subtler cases —
>    a sentence that is structurally a state progression or a checklist in disguise,
>    or an element name carried over unaltered as a heading.
> 5. **Audience fit.** The report's depth and vocabulary match the audience named in
>    `00-prompt-history.md`. `warning` where they do not.
>
> Tag every finding with `"rule": "report-722"`, except Keleo vocabulary leaks, which
> are `report-600`.
>
> **Write your findings** to `{REPORT_DIR}_verification/report-domain-grounding.json`.
> Return only your one-line summary.

---

## Verifier 4 — `register-and-style`

Run at **low effort**.

> You are a REGISTER AND STYLE VERIFIER for a prose deliverable written for a human
> audience.
>
> **First, load the house style.** Try to read `~/.claude/skills/writing-style/SKILL.md`.
> **If it is not present, do not fail and do not skip this check** — that skill is
> deliberately not vendored into this repository, so its absence is expected in a
> clone. Fall back to the non-negotiables below, which hold either way.
>
> **Read:** `{REPORT}`, and the output of
> `python3 utils/lint-report.py {REPORT} --json` so you do not repeat its findings.
>
> **The non-negotiables** — these are errors:
>
> - **Never "ensures".** Use what the thing actually does.
> - **Never claims something is "secure".** "Security focused", "strengthens your
>   security posture".
> - **Sentence case headings**, cascading from h2. No h1 in the body.
> - **Unsupported claims and hyperbole.** Any superlative or marketing register that
>   the report has not earned.
>
> **These are warnings:**
>
> - **Bullets where prose belongs.** Lists are for three or more parallel items, steps
>   or checklists. Analysis belongs in short paragraphs of two to three sentences on a
>   single point.
> - **AI tells** — scene-setting openers, relentless triads, "it's not just X, it's Y",
>   hedged non-claims, a summary sentence closing every section.
> - **Pronoun drift** — "you" for the reader, "I" for the author, "we" only where you
>   can name who "we" is.
>
> Quote the offending text in your evidence. A style finding without the sentence it
> refers to cannot be acted on.
>
> **Write your findings** to `{REPORT_DIR}_verification/report-register-and-style.json`.
> Return only your one-line summary.

---

## Verifier 5 — type-specific

One additional verifier, briefed from the row for the invoking skill. Use the slug
`report-type-specific.json` regardless of which skill, so the gate command is the same
everywhere.

| Skill | What this verifier checks |
|---|---|
| `method-based-report` | No additional concern — **skip this verifier** and omit it from `--expect` |
| `reference-architecture` | Options are genuinely distinct rather than variations of one design; each is evaluated against the stated evaluation framework, not a different one per option; sizing figures and capacity numbers are sourced rather than silently estimated |
| `project-plan` | Every estimate traces to a stated assumption; the assumptions are listed, not implied; where a SOW is produced, its scope matches the activities and deliverables in the plan and does not quietly widen or narrow them |
| `decision-analysis` | Options receive balanced depth — no option is strawmanned by thin treatment; stated trade-offs are real rather than token weaknesses on a favoured option; the verdict follows from the analysis rather than the analysis being arranged to reach a predetermined verdict |
| `document-review` | Every criticism cites the specific part of the reviewed document it refers to; recommendations are actionable rather than restatements of the gap ("add a section on X" is actionable, "the security coverage is weak" is not); strengths are identified as well as gaps |

> You are a <TYPE> REPORT VERIFIER. Read `{REPORT}` and check the concerns below,
> which are specific to this report type. Everything else — source fidelity,
> citations, domain grounding, house style — is another verifier's job; do not
> duplicate it.
>
> **Concerns:** {TYPE_CONCERN}
>
> Be specific and quote the report. Severity per VERIFY-FOUNDATION.md §5.
>
> **Write your findings** to `{REPORT_DIR}_verification/report-type-specific.json`.
> Return only your one-line summary.

---

## Gate

Mechanical first, then the gate:

```bash
python3 utils/lint-report.py {REPORT}
python3 utils/verification-gate.py {REPORT_DIR} --phase report --gate --summary \
  --expect source-fidelity,citation-integrity,domain-grounding,register-and-style,type-specific
```

Drop `type-specific` from `--expect` for `method-based-report`, which has no
type-specific verifier.

**Parallel multi-report generation:** one full verifier set per report, four agents at
a time, and one gate per report directory. No report ships unverified.
