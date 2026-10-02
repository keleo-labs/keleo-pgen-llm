---
name: exec-readout
description: Create an executive readout deck — status report, findings, review outcome, programme update — and publish it to Google Slides and PDF.
---

# Exec Readout

Version: 2.0.0

Decks that **report to a decision-maker**: status updates, findings, review
outcomes, programme reviews, incident summaries.

**Read `.claude/skills/deck-foundation/DECK-FOUNDATION.md` first.** This
file adds only what is specific to readouts.

## Inputs to establish

| Input | Needed because |
|---|---|
| What is being reported on | — |
| Seniority of the audience | Sets altitude and detail |
| Decisions needed from them | Readouts that need nothing still need a "no action required" slide |
| Period covered | Scopes what counts as news |
| Source material | Status data, findings, metrics |

Take defaults for anything unstated and say so in one line. Do not block.

## Structure

**Always Pyramid.** Answer first, then supporting arguments, then evidence.
A senior audience may interrupt at slide three or read only the first few —
a readout that builds to its conclusion fails both. See `narrative-guide.md`.

### The one deliberate exception to source fidelity

DECK-FOUNDATION §2.1 makes following the source document's structure the
default. A readout is the standing exception, and only in one respect:
**the conclusion is promoted to the front.** A findings report or status
document almost always builds to its answer; a readout cannot.

Everything else about §2.1 still holds, and it is the part most often lost:

- The supporting movements follow the **source's** sections, in the source's
  order, below the bottom line.
- Every section of the source is represented. Promoting the conclusion is
  not licence to drop the sections that did not fit.
- The emphasis is the source's. If the document treats something as the
  principal finding, so does the bottom line — the deck does not elect a
  different headline because it reads better.

Say in the plan that you are promoting the conclusion, and name the source
section it came from. That makes the one reordering visible rather than
silent, which is the whole point of §2.1.

## Deck shape

1. `cover`
2. **Bottom line** (`statement` or `default`) — the answer, on slide two.
   Status, headline finding, or recommendation. Never later than slide two.
3. **Decisions needed** (`columns` or `steps`) — what you want from them,
   early, while they are still paying attention
4. Supporting detail, one movement per argument, `section`-divided
5. **Risks and what is off track** — explicit, never buried
6. `closing` — decisions restated with owners and dates

## Rules specific to readouts

- **Answer on slide two.** Non-negotiable. Everything after it is support.
- **Decisions early, not last.** A decision slide at the end gets reached
  after the audience has stopped listening.
- **Report bad news plainly.** State what is off track, by how much, and what
  is being done. Hedged status reporting destroys the readout's credibility
  and is worse than the bad news itself.
- **RAG status needs a definition.** "Amber" means nothing without the
  threshold that produced it.
- **Numbers over adjectives.** "Three weeks behind" not "slightly delayed".
- **No surprises in the detail.** Anything material in the supporting slides
  must already have appeared in the bottom line.
- **Figures must be ones the source asserted** — not numbers lifted from
  citation titles, reference lists or footnotes (DECK-FOUNDATION §2.2). A
  readout's figures get checked.

## Citations and speaker notes

Both required (DECK-FOUNDATION §5).

- Carry the source's own citations onto the slides built from them. A senior
  audience asks "says who?" of exactly the claims a readout makes.
- Write speaker notes for every content slide from the source's prose. For a
  readout these carry the detail behind a RAG status, the threshold that
  produced it, and the answer to the obvious follow-up question — the
  material that would otherwise force a hedge onto the slide itself.

## Output

Report: the Google Slides link, the PDF path, the bottom-line statement and
which source section it came from, the decisions requested, anything
reported as off track, and any source section not turned into slides with
the reason.
