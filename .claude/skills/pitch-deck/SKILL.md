---
name: pitch-deck
description: Create a persuasive pitch deck — value proposition, partner or GSI pitch, solution proposal, business case — and publish it to Google Slides and PDF.
metadata:
  version: "1.0.0"
---

# Pitch Deck

> **Vendored copy.** This tree is distributed with `keleo-pgen-llm` so the
> capability works from a clone without a user-level install. It tracks the
> global skill at `~/.claude/skills/pitch-deck/` version by version; the only
> intended difference is that paths are repo-relative rather than
> `~/.claude/skills/…`. If the two diverge otherwise, the global copy is
> upstream. Re-copy with `python3 utils/vendor-skills.py`.

Version: 2.0.0

Decks whose job is to **win a decision**: value propositions, partner and GSI
pitches, solution proposals, business cases.

**Read `.claude/skills/deck-foundation/DECK-FOUNDATION.md` first.** This
file adds only what is specific to pitching.

## Inputs to establish

| Input | Needed because |
|---|---|
| What is being pitched | — |
| Whether there is a source document | Decides the deck's structure — see below |
| Who decides, and what they control | A pitch aimed at the wrong altitude fails |
| The decision being asked for | Becomes the closing slide |
| The audience's current alternative | Including doing nothing — this is what you argue against |
| Proof available | Customer evidence, benchmarks, references |
| Commercial constraints | Budget cycle, procurement route, timing |

If the decision being asked for is unclear, ask — a pitch without a specific
ask cannot be written well. Everything else can take a stated default.

## Structure

**With a source document — follow it.** A report, value proposition or
business case supplied by the user already argues the case; the deck presents
that argument, it does not rebuild it. Walk the source's sections in order
and give each the slides it needs. Full rules in DECK-FOUNDATION §2.1.

State the section-to-slide mapping before writing. A pitch document usually
*is* already a pitch — if its order genuinely undersells the case for this
audience, say which sections you would move and why, then follow the answer.
The common failure here is quietly dropping the sections that did not fit an
imposed narrative arc, and in a pitch those are often the ones the decision
actually turns on: the commercial terms, the engagement model, the sections
that answer "and what do I have to do?".

**Without a source document — choose a shape.** Default to
**Before–After–Bridge** for a single decision, or **SCQA** when the audience
does not yet agree there is a problem. Use **Sparkline** only for
vision-level pitches with time to spare. See `narrative-guide.md`. Then:

1. `cover`
2. The world as it is, with its cost **quantified** (`stats` or `default`)
3. `statement` — the turn
4. What becomes possible (`columns` or `steps`)
5. Proof — customer evidence, benchmark, reference (`quote`, `stats`)
6. How it works, briefly — enough to be credible, not a product tour
7. The bridge: what it takes, and what it costs (`steps`)
8. `closing` — the specific decision, owner and date

Either way the deck ends on the ask.

## Rules specific to pitching

- **Quantify the cost of inaction.** A pitch that only describes upside
  competes against doing nothing and loses. Where the source quantifies it,
  use the source's figure; where it does not, do not invent one.
- **Name the alternative honestly.** Including the incumbent and status quo.
  A pitch that pretends there is no alternative reads as a brochure.
- **Proof before mechanism.** Evidence it works, then how it works. Leading
  with mechanism invites objections before the audience wants the outcome.
  When following a source that orders them the other way, propose the swap
  rather than making it silently.
- **One ask.** Multiple asks split the decision and nothing is agreed.
- **No unsourced figures.** Every claim needs a source or an explicit
  "illustrative" marker. Flag any figure the user must substantiate.
- **A figure must be one the source asserted** — not one lifted from a
  citation title, reference list, footnote or caption. Those are
  bibliographic furniture, not claims (DECK-FOUNDATION §2.2). In a pitch this
  matters more than anywhere else: an unsupported headline number is the
  easiest thing in the room for a sceptical audience to pull on.

## Citations and speaker notes

Both are required, not optional. See DECK-FOUNDATION §5.

- Every content slide carrying a claim gets a `sources` entry, carrying the
  source document's own citation and link.
- Every content slide gets speaker notes derived from the source's prose —
  the reasoning, the qualifications, and the answer to the objection the
  slide invites. A pitch is delivered by a person who must handle pushback;
  the notes are where that preparation lives.

### Positioning constraints

Red Hat and partner positioning is **complementary to hyperscalers, not
competitive**. Avoid anti-cloud or migration-away framing. Do not cite
competitors as sources; use analysts, independent experts and integrators.

## Diagrams

A diagram with a spec goes on a `diagram` slide and is upgraded to native,
editable Slides shapes after publishing; any other image is embedded as a
picture (DECK-FOUNDATION §6).

## Output

Report: the Google Slides link, the PDF path, the structure used (the
section-to-slide mapping when following a source, the narrative shape
otherwise), the single ask, and an explicit list of every figure needing
substantiation before the deck is used.

Also report any source section you did **not** turn into slides, and why. A
dropped section is a decision, and the user should get to overrule it.
