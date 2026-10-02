# Slide Grammar

Version: 2.1.0

How to write an individual slide. Read alongside `DECK-FOUNDATION.md`.

A deck is not a document. Everything here follows from one fact: the audience
is *listening to a person* while *looking at a slide*, and cannot do both
well. The slide carries the claim and its evidence; the speaker carries the
reasoning.

---

## 1. Action titles

**Every slide title is an assertion, not a topic.**

When the deck comes from a source document, the assertion is *the source's*
— the point that section was making — sharpened into a sentence. It is not a
new claim invented because it sounds stronger. See DECK-FOUNDATION §2.1.

**Keep titles to about 50 characters.** The title zone reserves two lines at
`max-width: 22ch`, and Google Slides wraps a little earlier than the browser
does: 51 characters has been observed fitting and 55 wrapping to three lines,
which collides with the content beneath. Treat 50 as the budget and verify in
the published deck, never the local render.

| Topic title (weak) | Assertion title (strong) |
|---|---|
| Adoption metrics | Adoption flattens without an owning team |
| Architecture overview | Three services carry all the latency risk |
| Next steps | Decide the owner, and the rest follows |

Test: read the titles alone, in order. If they tell the argument end to end,
the deck has a spine. If they read as a table of contents, it does not.

This is the single highest-leverage rule here. A deck of topic titles cannot
be fixed by better visuals.

## 2. Assertion–evidence structure

The title asserts; the body shows why it is true. The body is evidence —
data, an example, a mechanism — not a restatement of the title in smaller
type, and not a list of sub-topics.

If the body does not support the title, one of them is wrong.

## 3. Density

- **One idea per slide.** Two ideas means two slides.
- **Three to five bullets maximum**, each a single line where possible.
- **No sub-bullets.** A sub-bullet means the parent should have been the
  slide title.
- **Sentence fragments, not sentences.** The speaker supplies the grammar.
- If a slide needs a paragraph, it is a document, not a slide. Write the
  paragraph in the presenter notes.

A sparse slide is a content signal, not a layout defect. Three short bullets
on a half-empty slide usually means the slide should be merged with its
neighbour or carry stronger evidence — do not pad it, and do not inflate the
type to fill space.

## 4. Choosing a slide form

| The content is | Use |
|---|---|
| A claim plus its evidence | `default` |
| 2–4 things that are peers, in no order | `columns` |
| Stages that happen in order | `steps` |
| One to three numbers that matter | `stats` |
| Someone else's words, verbatim | `quote` |
| A turn in the argument | `statement` |
| A claim that only makes sense beside an image | `split` |
| A boundary between movements | `section` |

Reaching for `default` with bullets every time is the most common failure.
Bullets are the right form for a short list of peers — not for a sequence
(`steps`), a comparison (`columns`), or a number (`stats`).

**Budget the body text to the column count.** A `columns` or `steps` body
gets narrower as the count rises, and anything below it — a `caption`, the
`sources` band — is pushed off the slide when the bodies run long.

| Count | Body budget | Heading |
|---|---|---|
| 2 | ~200 characters | — |
| 3 | ~140 characters | 2 words where possible |
| 4 | ~100 characters | 1–2 words |

Four columns carrying both a caption and a citation band is the tightest
case in the theme. If the content will not fit that budget, the slide is
carrying too much: cut an item or split it in two.

## 5. Numbers

- Every figure needs a **label** saying what it means. A number alone is
  decoration.
- Every figure needs a **source**, unless it is the audience's own data.
- The source must be a claim the document **asserted**, not a number lifted
  from a citation title or reference list — DECK-FOUNDATION §2.2.
- Round to the precision that matters. `62%` not `61.8431%`.
- Keep values short — `62%`, `3x`, `£1.4m`. Long strings break the display
  face's tight setting.

## 6. Quotes

Verbatim or not at all. A paraphrase inside quotation marks is a
misattribution. Attribute to a person or a role; anonymise only when the
source requires it, and say which organisation type if so.

## 7. Openings and closings

**Cover** states the subject and why this audience should care, in one line.

**Closing is the ask, never "Thank you".** It names the specific decisions or
actions wanted, and who owns them. A deck that ends without an ask has wasted
its most-remembered slide.

## 8. Citations

Every content slide carrying a claim from a source gets a `sources` entry —
author and year, linked where the source linked. Cite per slide, not once at
the end of the deck. Full guidance in DECK-FOUNDATION §5.

On a `stats` slide, use the band rather than the per-item `source` when the
whole slide shares one citation; otherwise the attribution prints twice.
Per-item `source` is for a row of figures with different origins.

## 9. Presenter notes

**Every content slide gets notes.** Put the reasoning, the caveats and the
anticipated objections in presenter notes (any markdown after a `<!-- -->`
comment block in the slide). The slide stays sparse; the speaker stays
equipped.

When working from a source document, the notes are where the source's prose
goes. The slide compresses a section to an assertion and three bullets; the
notes carry the two or three sentences that explain it, in the author's own
terms. A deck whose slides are sparse and whose notes are empty has simply
lost the content.

## 10. Length

Roughly one slide per minute of speaking time, with section dividers on top.
A 20-minute readout is ~15 content slides plus 3 dividers. When over budget,
cut whole slides rather than compressing every slide — compression costs
legibility everywhere, cutting costs one idea.
