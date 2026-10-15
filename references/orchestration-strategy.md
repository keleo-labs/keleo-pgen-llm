# Orchestration Strategy

How to decide whether a practice needs a `PatternOrchestration` at all, and when one
already exists that should be extended or embedded instead of duplicated.

Read at Phase 2 Step 8.5, which only applies when a practice has two or more patterns.

## Read first

The decision framework is in the language semantics, not here. This document is the
procedure; those sections are the reasoning, and the procedure makes no sense without
them.

| Section | What it settles |
|---|---|
| [`semantics/execution-and-patterns.md` §9.5.1](semantics/execution-and-patterns.md#951-how-a-stage-is-placed) | `sequential`, `concurrent`, `nested`, `onDemand` — how a stage is placed |
| §9.5.4 Embedding an Orchestration | Naming another orchestration as a stage; cross-document resolution; the two deliberate limits |
| §9.5.5 Baseline-Published Shells | Shells with no stages, and why extension is additive |
| §9.5.6 Choosing the Level | Embed against nest; extend against embed against author new |

## 1. Does this practice need one at all?

An orchestration is warranted when the practice defines **two or more patterns** and the
source material says something about how they relate **in time** — one precedes another,
one repeats inside the phases of another, one is entered only when circumstances call for
it.

It is not warranted when the patterns are simply several independent lifecycles the
practice happens to own. Independent patterns need no orchestration, patterns named in
none remain valid, and inventing an order the source does not state is worse than leaving
them unrelated. A practice with one pattern never needs one.

## 2. Inventory before you judge

The gate below is only honest if you know what already exists. Build the effective
context and read its orchestrations:

```bash
python3 utils/resolve-context.py <practice-or-baseline> --transitive -o _effective-context.json
python3 utils/practice-summary.py _effective-context.json --show patternOrchestrations
```

The output gives each orchestration's name, description, owner and stages, with embedded
orchestrations marked `⊂`. Answering "nothing in scope describes this" without running
this is the proliferation case, and it is the one failure this whole document exists to
prevent.

Record what you found in the mapping guide alongside the route you chose. A reader should
be able to see that the alternatives were considered.

## 3. The authoring gate

Three routes. Take the **first** that fits — a new orchestration is authored only when
routes 1 and 2 genuinely do not reach.

| Check | Route |
|---|---|
| An orchestration in scope already describes this shape, and what this practice adds serves the purpose **its description states** | **Extend by name** — redeclare the name, contribute only your own stages |
| This practice's patterns form a self-contained sub-endeavour of a shape in scope | **Author your own and let it be embedded** — or embed it yourself if you own the host |
| Nothing in scope describes this shape | **Author new** — and say in the description what makes it distinct |

For route 2, apply the three-question test in §9.5.6 before embedding rather than nesting:
the sub-endeavour needs its own owner, its own completion, and plausible reuse by more
than one host. Any no means a `nested` pattern stage inside the host, not an embedded
orchestration.

## 4. Extending without breaking what you extend

**The scope test comes first.** Read the host orchestration's `description`. It states
the endeavour that orchestration is for. Extension is for contributions that fit that
purpose — a practice bringing assurance, risk or enablement tracks to a delivery shape
that always implied them. If what you are adding would make the host's description
untrue, you are in route 3, not route 1.

**Then the authoring move.** The mechanics are §9.5.5 and the validator enforces them, so
what matters here is the shape a contribution naturally takes: place your stages
`relativeTo` the inherited ones. `concurrent` for a track running alongside, `nested` for
one bounded by an inherited phase, `onDemand` for one entered on recognition. None of the
three disturbs an order you do not own. A `sequential` stage appends after the inherited
sequence.

**The reorder impulse is diagnostic.** Wanting to renumber, re-place or rewrite what you
inherited means the shape you have in mind is not the shape that was published. Author a
new orchestration and say in its description what makes it different. A second honest
orchestration costs less than a shared one that no longer means what its author wrote.

`validate-practice.py` rejects a restated inherited stage and a sequential stage inserted
below the inherited maximum `seq`. If either fires, the answer is almost never to
renumber around it — it is that you are in route 3.

## 5. Ownership

Both kinds of name resolve across the baseline chain and declared dependencies, so a
stage may name another document's pattern. Prefer embedding the orchestration that owns
that pattern: the ordering stays with its author and follows any change they make.
Placing the foreign pattern directly validates, and warns, and the warning names the
orchestration to embed instead.

Hosting a stage against an inherited pattern via `relativeTo` is not this case. That is
the sanctioned way to contribute, and nothing warns about it.

## 6. Anti-patterns

| Anti-pattern | Instead |
|---|---|
| An orchestration per practice, by reflex | Run the inventory. Most practices contribute stages to a shape that exists |
| An orchestration restating one pattern's phases | That is the pattern's own `patternViews`. An orchestration sequences whole patterns |
| A sequential chain where the source states no order | Leave the patterns unrelated. Independent patterns need no orchestration |
| A shell extended with stages unrelated to the shape it published | Author your own orchestration. The shell's description has to stay true |
| Extension used to quietly repurpose a shared orchestration | Route 3. Name the different endeavour and say what makes it different |
| A foreign pattern placed directly where its owner already sequenced it | Embed that orchestration |
