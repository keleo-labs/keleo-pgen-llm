# Narrative Guide

Version: 1.1.0

Deck-level narrative shapes. Pick one before writing slides; it determines
the order of the argument, which is harder to change later than any slide.

Read alongside `slide-grammar.md`, which governs the individual slide.

---

## When a shape applies

**A source document outranks every shape here.** When the user supplies a
report, paper or memo, its structure is the deck's and these shapes do not
override it — see DECK-FOUNDATION §2.1. A document already embodies its
author's structural decisions; imposing SCQA over the top discards them.

Reach for a shape when:

- there is no source document;
- the user asked for a reshape, or accepted one you proposed;
- the source is fragments — notes, data, a thread — rather than a document;
- you are ordering content *within* a section that has no order of its own.

The one standing exception is `exec-readout`, which always promotes the
conclusion to the front and says so.

## Choosing

| Purpose | Shape |
|---|---|
| Win agreement to act on a problem | SCQA |
| Sell a change against the status quo | Sparkline |
| Report status or findings to a decision-maker | Pyramid |
| Make the case for a specific choice | Before–After–Bridge |
| Tell what happened, to people who were not there | Story Spine |
| Pitch under severe time pressure | 10/20/30 |

When unsure: **Pyramid** for reporting, **SCQA** for persuading.

---

## SCQA

Minto's situation–complication–question–answer. The audience arrives at the
question themselves, so the answer lands as a conclusion rather than a pitch.

| Movement | Content | Slides |
|---|---|---|
| Situation | What everyone already agrees is true | 1–2 |
| Complication | What changed, or what is breaking | 1–3 |
| Question | The question the complication forces | 1 (`statement`) |
| Answer | The recommendation, then its support | the rest |

Best for: proposals, business cases, anything where the audience must accept
a problem before they will accept a solution.

## Pyramid

Minto's pyramid principle. Answer first, then the supporting arguments, then
the evidence under each. Respects a senior audience's time and survives being
interrupted at slide three.

```
Recommendation
├── Argument 1 → evidence
├── Argument 2 → evidence
└── Argument 3 → evidence
```

Best for: exec readouts, status reports, any audience who may stop you early
or only read the first three slides.

**Do not bury the answer.** If the deck builds to a conclusion at the end, a
senior audience will ask for it on slide two and the structure collapses.

## Sparkline

Duarte's shape: alternate between *what is* and *what could be*, with the gap
widening each time, closing on a "new bliss".

```
what is ─┐   ┌─ what could be ─┐   ┌─ what could be ──── new bliss
         └───┘                 └───┘
```

Each oscillation raises the tension. Use `statement` slides at the turns.

Best for: change advocacy, vision pitches, keynote-style talks. Costs more
slides than SCQA — avoid under tight time.

## Before–After–Bridge

Three movements: the world now, the world after, and the bridge between.
The simplest persuasive shape and the easiest to keep honest.

| Movement | Content |
|---|---|
| Before | The current state, with its cost quantified |
| After | The specific, concrete end state |
| Bridge | What it takes to get there — the ask |

Best for: short pitches, single-decision proposals.

## Story Spine

"Once upon a time… every day… until one day… because of that… until finally…"

Chronological with causal links. Each step must be caused by the previous
one, which is what separates it from a timeline.

Best for: post-incident narratives, case studies, project retrospectives.

## 10/20/30

Kawasaki's constraint: 10 slides, 20 minutes, 30-point minimum type. Not a
narrative so much as a discipline — pair it with Before–After–Bridge or SCQA.

Best for: investor-style pitches and any slot under 20 minutes.

---

## Applying a shape

1. Write the movement names as section dividers.
2. Write every slide title as an assertion (`slide-grammar.md` §1).
3. Read the titles alone, in order. They must form the argument without the
   bodies. Fix the structure here, not after the slides are written.
4. Only then fill the bodies.

Mixing shapes within a deck produces an argument the audience cannot follow.
Pick one and keep it.
