# Adding a Deck Type

Version: 1.1.0

How to add a new deck-type skill on top of this foundation.

---

## When a new type is justified

Add one only when a deck category has **its own structural rules** — a fixed
narrative shape, a required slide, or content constraints that would be wrong
for other decks.

| Signal | Example |
|---|---|
| A mandated narrative shape | Readouts must use Pyramid |
| A required slide | Pitches must close on a single ask |
| Content rules that do not generalise | Readouts must quantify variance |

Not justified: a different subject, audience or length. Those are inputs to
`slide-deck`, not new skills. Three thin skills that differ only in tone are
worse than one skill with good inputs.

## Steps

1. **Create `.claude/skills/<name>/`** with `SKILL.md` and
   `contract.feature`.
2. **Write the contract first.** Express the type's rules as Gherkin
   scenarios. A rule that cannot be written as Given/When/Then is too vague
   to enforce — drop it or sharpen it.
3. **Write `SKILL.md` from the template below.** Keep it thin: it must add
   only what differs from `DECK-FOUNDATION.md`. Repeating the foundation is
   how the two drift apart.
4. **Check the layouts cover it.** If the type needs a slide form that
   `theme-redhat/layouts/` lacks, add the layout, then verify it through
   `DECK-FOUNDATION.md` §7 before shipping. Adding a layout is a MINOR bump
   to the theme. A content layout must also accept `sources` and render
   `<SourceNote>` (§5).
5. **Test it** on a real request end to end, including visual review.

## SKILL.md template

```markdown
---
name: <skill-name>
description: <one line — what it makes and when to use it. This is what
  routes a user request here rather than to a sibling skill, so name the
  deck category explicitly.>
---

# <Skill Name>

Version: 1.0.0

<One sentence: what decision or job this deck type serves.>

**Read `.claude/skills/deck-foundation/DECK-FOUNDATION.md` first.** This
file adds only what is specific to <type>.

## Inputs to establish

| Input | Needed because |
|---|---|
| … | … |

<State which inputs are blocking and which take defaults. Default to
proceeding; block only where proceeding would make the deck useless.>

## Structure

<Following the source document is the default — DECK-FOUNDATION §2.1. State
here only how this type departs from that, if it does, and why. Any
departure must be declared to the user when it is applied, not performed
silently; `exec-readout` promoting the conclusion is the worked example.>

<Then: which shape from narrative-guide.md applies when there is no source
document, and the numbered slide sequence with layouts.>

## Rules specific to <type>

- <Rules that would be wrong for other deck types. Each one must trace to a
  scenario in contract.feature.>

## Citations and speaker notes

<Both are required by DECK-FOUNDATION §5. Add only what this type needs
beyond that — which claims get cited most insistently, what the notes must
carry for this audience. Omit the section if there is nothing type-specific
to say.>

## Output

<What to report on completion. Include the structure used, and any source
section not turned into slides with the reason.>
```

## Versioning

Each skill versions independently against its `contract.feature`:

- **PATCH** — wording, clarification, no behavioural change
- **MINOR** — a new capability or a new scenario
- **MAJOR** — changed inputs or outputs, or a removed behaviour

`DECK-FOUNDATION.md` and `theme-redhat` version separately. A breaking change
to either is a MAJOR bump there, and every dependent skill must be checked.

## Keeping the foundation shared

Anything true of **all** deck types belongs in the foundation, not in a
skill. When the same guidance appears in two skills, move it down:

| Content | Home |
|---|---|
| Pipeline, layouts, conversion rules, review loop | `DECK-FOUNDATION.md` |
| How to write any slide | `slide-grammar.md` |
| Narrative shapes | `narrative-guide.md` |
| Rules for one deck type only | that skill's `SKILL.md` |
| Mechanical helpers | `scripts/` |
