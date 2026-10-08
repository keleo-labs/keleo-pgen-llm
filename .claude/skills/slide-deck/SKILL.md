---
name: slide-deck
description: Create a presentation deck and publish it to Google Slides and PDF. Use for any deck request not covered by pitch-deck or exec-readout — talks, training, overviews, workshops, conference sessions.
metadata:
  version: "3.0.0"
---

# Slide Deck

> **Vendored copy.** This tree is distributed with `keleo-pgen-llm` so the
> capability works from a clone without a user-level install. It tracks the
> global skill at `~/.claude/skills/slide-deck/` version by version; the only
> intended difference is that paths are repo-relative rather than
> `~/.claude/skills/…`. If the two diverge otherwise, the global copy is
> upstream. Re-copy with `python3 utils/vendor-skills.py`.

General-purpose deck generation. For a value-proposition or partner pitch use
`pitch-deck`; for a status or findings readout use `exec-readout`.

**Read `.claude/skills/deck-foundation/DECK-FOUNDATION.md` first.** It
carries the pipeline, layouts, conversion constraints and the review loop.
This file adds only what is specific to general decks.

## Inputs to establish

Ask only for what is missing and material. Do not interrogate.

| Input | Needed because |
|---|---|
| Subject | — |
| Audience and their prior knowledge | Sets vocabulary and how much to explain |
| Speaking slot length | Sets slide budget (~1 slide/minute) |
| What the audience should do or believe afterwards | Determines the closing slide |
| Source material | Grounds the content — and, when it is a document, sets the structure |

If the user gives a subject and nothing else, pick sensible defaults (30
minutes, mixed-seniority technical audience), state them in one line, and
proceed. Do not block on questions.

## Workflow

Follow `DECK-FOUNDATION.md` §2, with these specifics:

**Structure — follow the source document if there is one.** A supplied
report, paper or memo *is* the deck's structure: walk its sections in order
and give each the slides it needs (DECK-FOUNDATION §2.1). State the
section-to-slide mapping before writing, and propose a reshape rather than
performing one. Only when there is no source document — or the user asks for
a reshape — choose a shape from `narrative-guide.md`; for general decks SCQA
suits persuasion and Pyramid suits explanation.

Either way, write the full slide title sequence before any bodies, and check
it reads as an argument.

**Write.** Apply `slide-grammar.md` throughout — assertion titles,
assertion–evidence bodies, one idea per slide. Carry each slide's citations
in `sources` and write its speaker notes as you go (DECK-FOUNDATION §5).

**Diagrams.** A diagram with a spec goes on a `diagram` slide and is
upgraded to native, editable Slides shapes after publishing; any other
image is embedded as a picture (DECK-FOUNDATION §6).

**Lint, then publish and review.** Run
`python3 .claude/skills/deck-foundation/scripts/lint-deck.py slides.md` and
clear its errors first, and read its `tone` warnings — they flag variables given agency over decisions, rhetorical titles and editorialising phrases (`slide-grammar.md` §5) — missing or duplicated titles, bodies over the column
budget, slides whose notes outweigh them. Then render the published deck and
read every slide. Fix what reads badly before reporting completion.

## Deck shape

Following a source document, the shape is the document's. Otherwise a general
deck runs:

1. `cover`
2. Framing — why this subject, for this audience, now (1–2 slides)
3. Body, divided by `section` slides into 2–4 movements
4. `closing` — the ask or the takeaway

Use `statement` slides at the turns in the argument. Use `section` dividers
whenever the deck changes movement — they are cheap and they keep a long deck
navigable. When following a source, its top-level headings are usually the
right dividers.

**Every movement runs divider → overview → members.** The divider carries a
sentence saying why the deck is turning; where three or more parallel members
follow, the overview names the set and each member's role before the first
one appears (DECK-FOUNDATION §3). Going straight from `Architecture options`
to Option A leaves the audience judging a design without knowing what it is
being judged against.

## Citations and speaker notes

Required on any deck built from a source (DECK-FOUNDATION §5). A training or
overview deck is often delivered by someone other than its author, and often
read by someone with no presenter at all — so the slide must carry its own
argument and the notes add the speaker's layer on top, never the half the
slide left out (`slide-grammar.md` §2, §12).

Figures must be ones the source **asserted**, not numbers lifted from
citation titles or reference lists (§2.2).

## Output

Report: the Google Slides link, the PDF path, the slide count, and the
structure used — the section-to-slide mapping when following a source, the
narrative shape otherwise. Flag anything the user should check: assumptions
made, figures that need a real source, source sections not turned into slides
and why, places where source material was thin.
