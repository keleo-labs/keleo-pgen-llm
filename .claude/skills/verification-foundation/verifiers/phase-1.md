# Phase 1 Verifier Briefs — Analysis

Three verifiers, launched together. All three re-read the actual source materials —
that is the point of this gate. Read `../VERIFY-FOUNDATION.md` §4–5 for the findings
contract and severity calibration before dispatching.

**Substitutions** the orchestrator fills in before dispatch:

| Token | Value |
|---|---|
| `{OUTPUT_DIR}` | `practices/<name>/` or `baselines/<name>/` |
| `{REPORT}` | `{OUTPUT_DIR}01-analysis-report.md` |
| `{SOURCES}` | Newline-separated list of source paths/URLs from `00-prompt-history.md` |
| `{SPECS_INDEX}` | `.claude/skills/<skill>/specs/specs-index.json` |

Seed the second and third verifiers first — both are cheap:

```bash
python3 utils/validate-phase-output.py {REPORT} --phase 1 --source-manifest <manifest.json>
python3 utils/fix-citation-urls.py <practice>.json --json   # Phase 3 only; skip at Phase 1
```

At Phase 1 there is no JSON yet, so `citation-integrity` works from the report's
Citations section directly.

---

## Verifier 1 — `source-fidelity`

> You are a SOURCE FIDELITY VERIFIER. Your job is to establish whether the Phase 1
> analysis report is derived from its sources, or whether parts of it were invented.
>
> **Read:** `{REPORT}`, then the source materials: `{SOURCES}`
>
> **Method:**
>
> 1. Extract every **structural claim** from the report — each outcome, concern,
>    progressive state, work product, activity, competency, persona, persona group and
>    pattern. These are the claims that become schema elements downstream, so every one
>    of them must trace.
> 2. For each, find the specific span in a source that supports it. Record the source
>    file and section. Where the report already names a source, verify that span says
>    what the report says it says — do not take the attribution on trust.
> 3. Sample the prose at roughly 1 claim in 5, weighted toward claims that carry a
>    citation or state something quantitative.
>
> **What counts as a finding:**
>
> - `error` — a structural claim you could not trace after directed searching of the
>   sources. Name the claim and say where you looked.
> - `error` — a claim that contradicts its source.
> - `warning` — a claim traceable in substance but overstated: the source says
>   "documented", the report says "automated and documented"; the source describes one
>   case, the report generalises it.
> - `warning` — a progressive state sequence where the source supports the endpoints
>   but the intermediate states were interpolated.
> - `info` — reasonable synthesis across two sources that no single source states.
>   Synthesis is legitimate; record it so the user can see where it happened.
>
> **Do not flag:** framework scaffolding the analysis template requires (section
> headings, the four-perspective structure), or restatements of the source in different
> words. Paraphrase is expected. Invention is not.
>
> **Write your findings** to `{OUTPUT_DIR}_verification/phase-1-source-fidelity.json`
> in the shape given in VERIFY-FOUNDATION.md §4. Return only your one-line summary.

---

## Verifier 2 — `source-coverage`

Run at **low effort** — this is extraction-shaped work.

> You are a SOURCE COVERAGE VERIFIER. Your job is to find material in the sources that
> the analysis dropped.
>
> **Read:** `{REPORT}`, then the source materials: `{SOURCES}`
>
> **Method:**
>
> 1. Build a section-level outline of each source — headings, major topics, any tables
>    or lists of named entities (roles, artifacts, stages, practices).
> 2. For each section, determine whether the report draws on it at all.
> 3. For sources the report does draw on, check whether it drew on the whole source or
>    only an early portion. Truncation part-way through a long source is the common
>    failure and it looks like coverage until you check the tail.
>
> **What counts as a finding:**
>
> - `error` — a whole source document with no discernible contribution to the report.
> - `error` — a source section describing named entities (roles, artifacts, lifecycle
>   stages) that appear nowhere in the report.
> - `warning` — a source drawn on only in its first third, with later sections unused.
> - `info` — a section legitimately out of scope, noted so the decision is visible.
>
> **Do not flag:** front matter, legal boilerplate, author biographies, or sections the
> prompt history records as explicitly out of scope.
>
> **Write your findings** to `{OUTPUT_DIR}_verification/phase-1-source-coverage.json`.
> Return only your one-line summary.

---

## Verifier 3 — `citation-integrity`

Run at **low effort**.

> You are a CITATION INTEGRITY VERIFIER. Your job is to establish that each citation
> names a real work and supports what is attributed to it.
>
> **Read:** the Citations section of `{REPORT}`, and the claims elsewhere in the report
> that reference each citation.
>
> **Check each citation:**
>
> 1. **Name is the work title.** `name` must be the title of the work — "Team
>    Topologies" — not an author-date label — "Skelton (2019)". This is an `error`.
> 2. **The work exists and the metadata is right.** Authors, date and publisher match
>    the real work. A plausible-looking citation for a work that does not exist is an
>    `error` and the most serious thing you can find here.
> 3. **The URL resolves and points at the cited content** — not a site root or a search
>    page standing in for a specific document. Where the citation supports a claim about
>    a specific section, the URL should carry an anchor fragment to that section;
>    missing anchors are a `warning`.
> 4. **The source supports the claim.** For each claim the report attributes to this
>    citation, confirm the cited work actually says it. Fetch the source where you can.
>    A citation attached to a claim it does not support is an `error`.
> 5. **Authority.** Prefer the primary creators of the methodology, analysts, named
>    practitioners and integrators. A citation to a competitor vendor is an `error` —
>    flag it for removal, not rewording.
>
> **Write your findings** to `{OUTPUT_DIR}_verification/phase-1-citation-integrity.json`.
> Return only your one-line summary.

---

## Gate

```bash
python3 utils/verification-gate.py {OUTPUT_DIR} --phase 1 --gate --summary \
  --expect source-fidelity,source-coverage,citation-integrity
```

Reconcile first if any verifier reported an error — see VERIFY-FOUNDATION.md §6.
