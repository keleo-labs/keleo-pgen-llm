# Slide Grammar

Version: 4.0.0

> **4.0.0 sets the register.** Decisions belong to people rather than to variables, titles state
> their subject plainly rather than rhetorically, problems are framed as prerequisites rather than
> as failures, and domain terms replace shorthand. See §5.
>
> **3.0.0 inverted the voice.** Slides carry complete sentences and stand on their own;
> fragments and notes-dependent hooks are out. Fullness is paid for by cutting the item
> count, not by letting slides run longer. See §2 and §3.

How to write an individual slide. Read alongside `DECK-FOUNDATION.md`.

**A deck is read at least as often as it is presented.** It gets forwarded, skimmed before a
meeting, and opened months later by someone who was not in the room. So a slide has to make its
point without a narrator: the slide states the claim *and* enough of the reasoning to be
understood, and the notes add what a speaker would say on top.

That is a deliberate reversal of the older rule that the speaker supplies the grammar. The cost of
a slide nobody can read without you is higher than the cost of a few more words on it.

---

## 1. Action titles

**Every slide title is an assertion, not a topic.**

When the deck comes from a source document, the assertion is *the source's* — the point that
section was making, sharpened into a sentence. It is not a new claim invented because it sounds
stronger. See DECK-FOUNDATION §2.1.

**Keep titles to about 50 characters.** The title zone reserves two lines at `max-width: 22ch`, and
Google Slides wraps a little earlier than the browser does: 51 characters has been observed fitting
and 55 wrapping to three lines, which collides with the content beneath. Treat 50 as the budget and
verify in the published deck, never the local render.

This is the one place terseness still wins, and it is a measured conversion limit rather than a
stylistic preference.

| Topic title (weak) | Assertion title (strong) |
|---|---|
| Adoption metrics | Adoption flattens without an owning team |
| Architecture overview | Three services carry all the latency risk |
| Next steps | Ownership is the first decision; sequencing follows from it |

**No two slides share a title, and consecutive slides must not come close.** The `eyebrow` repeats
across a movement by design — that is what marks the movement — so the title underneath it carries
the whole burden of distinguishing one slide from the next. Four slides reading *Content supply
chain* over four different titles is correct; four slides whose titles also blur together is not.

Test: read the titles alone, in order. If they tell the argument end to end, the deck has a spine.
If they read as a table of contents, it does not.

This is the single highest-leverage rule here. A deck of topic titles cannot be fixed by better
visuals.

## 2. Every line stands on its own

**A reader with no speaker and no notes must be able to understand each bullet.**

The failure this prevents has a shape: a compressed, dramatic line that sounds like a claim but
defers its meaning to something the reader cannot see. It reads as confident on screen and as
nonsense in an inbox.

| Defers its meaning | Stands on its own |
|---|---|
| Pay for the link | Synchronous replication needs high bandwidth and low latency, which makes the inter-site link expensive |
| Rehearse inside the gap | An air gap has no cloud region to test against, so rehearsal means using the recovery site itself |
| Two numbers decide this | Site separation and recovery point objective together narrow the choice to one design |

If a bullet needs its notes to make sense, the explanation is on the wrong side of the line. Move
it up (§12).

## 3. Complete sentences, fewer of them

**Write subject–verb–object statements.** Not noun fragments, not telegraphic shorthand, not a
headline with the verb removed.

This costs characters, and characters are constrained — so buy them by cutting items rather than by
letting the slide grow. A slide that would have carried five fragments carries three sentences.

- **One idea per slide.** Two ideas means two slides.
- **Three bullets is the working maximum**, four at a push. Each may run to two lines.
- **No sub-bullets.** A sub-bullet means the parent should have been the slide title.
- **Prefer two or three columns to four.** Four columns leaves ~100 characters per body, which is
  not enough for a sentence that explains anything.
- If a slide needs a paragraph, it is a document, not a slide. Tighten the sentence or split the
  slide.

A sparse slide is a content signal, not a layout defect. Two short sentences on a half-empty slide
usually means the slide should be merged with its neighbour or carry stronger evidence — do not
pad it, and do not inflate the type to fill space.

## 4. Connect the facts

**Use the connective that names the relationship**: *because*, *therefore*, *consequently*, *so*,
*in contrast*, *which means*. A constraint and its consequence belong in one sentence, joined.

Facts listed side by side leave the reader to infer the link, and different readers infer
different links. Writing "Synchronous replication caps site separation at roughly 100 km, **so** a
regional event can take both sites" is one claim. Writing the two halves as separate bullets is
two facts and an exercise.

This applies across slides as well as within them. A `section` divider must say why the deck is
turning, not just name the next movement, and a movement presenting three or more parallel members
opens with an overview of the set before the first member — see DECK-FOUNDATION §3.

A member slide arriving with no overview is the commonest form of a disconnected fact: the audience
is shown Option A without knowing that B and C exist, so they cannot judge what they are looking
at until the movement ends.

## 5. Register

Four rules that govern every title and every line of body copy. They apply to the deliverable,
not to the reasoning behind it — this document says "an assertion, not a topic" freely, and that
is fine, because nobody is reading it from a projector.

### Decisions belong to people

**A variable is an input to a choice, never the maker of one.** Distance does not pick an
architecture; an architect weighs distance and picks one. The fix is not to avoid the verb but to
name the human decision the variable feeds.

| Instead of | Write |
|---|---|
| Distance and tolerable loss pick the design | Site separation and recovery point objective are the primary inputs to the design choice |
| Your two numbers choose the design | Two measurements narrow the choice to a single viable design |
| Rehearsal decides whether any of it works | Rehearsal is what establishes whether the mechanism performs as designed |

The verb is only wrong when its subject is a thing. "The platform team decides the update window"
is correct and should stay.

### Titles state their subject

An assertion title is still required (§1). What is out is the **rhetorical device** — the title
that withholds, inverts or needles instead of stating.

| Instead of | Write |
|---|---|
| Three designs are viable, not one | Three viable disaster recovery designs |
| Resilience is phase four, not phase one | Resilience depends on four preceding phases |
| A mechanism is not a capability until proven | Validation converts a mechanism into a capability |
| Why air-gapped DR fails | Disaster recovery constraints in isolated environments |

The banned shapes are specific: `X, not Y`; `Why X fails`; `The two things that matter`; anything
that reads as a conversational aside. A title can assert strongly and still be plain.

### Frame problems pragmatically

Describe what has to be satisfied, not who was naive. Phrases like *well understood*, *works on
paper*, *in the real world*, *breaks the assumption* and *the hard part* editorialise about the
reader's competence and add nothing an architect can act on.

| Instead of | Write |
|---|---|
| Combining them is where designs that work on paper start to fail | Combining them introduces prerequisites that each approach must satisfy independently |
| An air gap breaks the DR rebuild assumption | Site isolation removes the external dependencies recovery procedures normally assume |
| The only one that survives a mistake | The only approach that protects against logical corruption as well as site loss |

The replacement is usually longer and always more useful, because it names the mechanism instead
of gesturing at a difficulty.

### Use the domain's terminology

Prefer the industry term over the shorthand, especially in headings and column labels where the
shorthand loses its antecedent.

| Instead of | Write |
|---|---|
| the gap | the site isolation boundary |
| Metro sync | Synchronous metro replication |
| Backup | Backup and restore |
| two numbers | site separation and recovery point objective |

Shorthand is acceptable in speaker notes, where a presenter has already established the term.

`scripts/lint-deck.py --checks tone` flags the common cases. It reports warnings rather than
errors, because every one of these is context-dependent.

## 6. Assertion–evidence structure

The title asserts; the body shows why it is true. The body is evidence — data, an example, a
mechanism — not a restatement of the title in smaller type, and not a list of sub-topics.

If the body does not support the title, one of them is wrong.

## 7. Choosing a slide form

| The content is | Use |
|---|---|
| A claim plus its evidence | `default` |
| 2–3 things that are peers, in no order | `columns` |
| Stages that happen in order | `steps` |
| One to three numbers that matter | `stats` |
| Someone else's words, verbatim | `quote` |
| A turn in the argument | `statement` |
| A claim that only makes sense beside an image | `split` |
| A boundary between movements | `section` |

Reaching for `default` with bullets every time is the most common failure. Bullets are the right
form for a short list of peers — not for a sequence (`steps`), a comparison (`columns`), or a
number (`stats`).

**Budget the body text to the column count.** A `columns` or `steps` body gets narrower as the
count rises, and anything below it — a `caption`, the `sources` band — is pushed off the slide when
the bodies run long.

| Count | Body budget | Heading |
|---|---|---|
| 2 | ~200 characters | — |
| 3 | ~140 characters | 2 words where possible |
| 4 | ~100 characters | 1–2 words |

Since §3 asks for complete sentences, treat 4 columns as unavailable for anything needing
explanation: at ~100 characters a body is one short sentence and no more. Three is the practical
ceiling for explanatory content, and two is better.

**`statement` carries no body**, which makes it the layout most likely to strand a reader. Use it
only where the title alone is genuinely complete — a claim nobody needs help with. If the turn in
the argument needs a reason, it is a `default` slide.

## 8. Numbers

- Every figure needs a **label** saying what it means. A number alone is decoration.
- Every figure needs a **source**, unless it is the audience's own data.
- The source must be a claim the document **asserted**, not a number lifted from a citation title
  or reference list — DECK-FOUNDATION §2.2.
- Round to the precision that matters. `62%` not `61.8431%`.
- Keep values short — `62%`, `3x`, `£1.4m`. Long strings break the display face's tight setting.

## 9. Quotes

Verbatim or not at all. A paraphrase inside quotation marks is a misattribution. Attribute to a
person or a role; anonymise only when the source requires it, and say which organisation type if
so.

## 10. Openings and closings

**Cover** states the subject and why this audience should care, in one line.

**Closing is the ask, never "Thank you".** It names the specific decisions or actions wanted, and
who owns them. A deck that ends without an ask has wasted its most-remembered slide.

## 11. Citations

Every content slide carrying a claim from a source gets a `sources` entry — author and year, linked
where the source linked. Cite per slide, not once at the end of the deck. Full guidance in
DECK-FOUNDATION §5.

On a `stats` slide, use the band rather than the per-item `source` when the whole slide shares one
citation; otherwise the attribution prints twice. Per-item `source` is for a row of figures with
different origins.

## 12. Presenter notes

**Every content slide gets notes, and they are additive.** Anything a reader needs in order to
understand the slide belongs on the slide (§2). The notes carry what a *speaker* would add on top:

- the anticipated objection and the answer to it
- the caveat, the exception, the edge case
- secondary data — the sizing table behind the one figure on screen
- where this point came from, and what the source qualified it with

Two to five sentences. Enough to speak from, not a script to read.

The test is subtraction: delete the notes and reread the slide. If a reader would now be confused
rather than merely less informed, move something up.

## 13. Length

Roughly one slide per minute of speaking time, with section dividers on top. A 20-minute readout is
~15 content slides plus 3 dividers. When over budget, cut whole slides rather than compressing
every slide — compression costs legibility everywhere, cutting costs one idea.

## 14. Checking it

`scripts/lint-deck.py slides.md` catches the mechanical half: missing or duplicated titles, titles
over budget, bodies over the column budget, slides whose notes outweigh them, and bullets that look
like fragments. It does not judge whether a sentence explains anything — read the deck.
