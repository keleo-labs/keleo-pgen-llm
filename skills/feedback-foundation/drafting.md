# Writing the issue

This governs both halves of the pipeline: the register row a reporter files, and the
tracker issue published from it. One structure, two audiences — so publication is a
redaction of something already readable rather than a rescue of something that is not.

Read it with `sanitisation.md` when drafting for a public tracker. Sanitisation decides
what may be said; this decides how well it is said. Both apply — an issue can be
perfectly safe and still useless. A register row has nothing to sanitise and needs this
file alone.

Load the available house writing-style skill and follow it. An issue is prose for a
human audience, so the house style applies to it exactly as it does to a report.

Worked examples — a register row, the issue written from it, and the redaction step —
are in `examples.md`. Read them once before your first draft rather than working from
the structure alone.

## Who you are writing for

Assume a competent engineer who has never opened the file you are writing about. They
might be a maintainer picking this up in six months, a contributor looking for something
to work on, or whoever has to decide it matters more than the other forty open issues.

None of them can act on an issue that opens in the middle:

> `resolve-context.py` does not implement the specificity chain accumulation in merge.md
> section 7.2e, so `specificity` is unpopulated on merged elements.

That is precise, verifiable, and opaque to everyone who does not already know what the
resolver produces or who reads it. The detail is not the problem. The missing first
paragraph is.

**Orient, then specify.** Say where the thing sits and what it is for before you say
what is wrong with it. File paths, symbol names and specification sections are welcome —
after the reader knows what they are looking at, not before.

## The shape

Five moves. The first four are plain English and carry the issue on their own. The fifth
is for whoever picks it up.

**1. Where this sits.** One or two sentences: what the component or document is, what job
it does, and what depends on it. Introduce here, in plain words, every term of art you
intend to use later. This is the move that is almost always missing.

**2. What happens, or what you cannot do today.** For an issue, the observable behaviour
stated as fact — not "there appears to be a potential inconsistency", but what happens.
For an enhancement, the capability gap, described as a gap rather than as your proposal.
The proposal is move 4.

**3. Why it matters.** The consequence, for someone you can name by role. For an
enhancement, the same question from the other side: what becomes possible, and what that
is worth. A defect with no consequence is a note. An enhancement with no value is a
preference.

**4. What would close it.** The condition under which someone can tell they have
finished. For an enhancement, the shape of an acceptable answer rather than a design,
plus any open questions you want triage to settle.

**5. Detail**, under its own heading. Paths, symbols, specification sections, counts,
reproduction — everything a reader can skip once they have decided whether they care.
Reproduction goes last, and only where it can be given without internal detail; a command
anyone can run is worth more than a paragraph describing one.

A three-sentence defect does not need headings, and moves collapse into single clauses
when there is little to say. The order holds at every length.

### The same shape in a register row

A row runs the same five moves, with two differences. It keeps everything publication
cannot — the practice, the products, the engagement, who asked — because that detail is
what makes triage possible and the row is where it legitimately lives. And it orients
differently: a row says which practice and which element, where an issue has to say
which component and what job it does.

Keep them separate as you write. The reporter who folds the detail into move 1 produces
a row whose orientation cannot be published, and the publisher then writes that
paragraph again from nothing. Put the orientation in move 1 and the identifying detail
in move 5, and publication becomes a matter of dropping move 5 and rewriting one
paragraph.

## Two tests before you file

**The orientation test.** Read only the title and the first paragraph. Can someone who
has never seen this codebase say what the thing is for and why they would care? If the
first paragraph names a file, a function or a specification section before saying what
any of them do, it fails.

**The jargon test.** Mark every term specific to this system. Each one either appears in
move 1 with a plain-English gloss, or does not appear until the detail section. "The
effective context — the single flattened document the mapping agents read as their
picture of the baseline" passes. "The effective context", unglossed in sentence one,
does not.

## Titles

Sentence case. Specific enough to be recognised in a list of forty, short enough to read
at a glance. The title states the defect or the gap, not the area it lives in.

| Weak | Better |
|---|---|
| Issue with forecast weights | Forecast weight curve decreases toward the recognised point |
| Documentation improvements needed | Validation instructions recommend a command that fails under PEP 668 |
| Bug in the sanitiser | Denylist harvest misses terms reported as missing from the corpus |
| Specificity chain accumulation | A practice cannot say what it makes an inherited element more specific about |

A title only an insider can parse is the first sign the body has the same problem.

## Rewrite, never transform

Register descriptions are written for an internal reader who already has the context, and
some were generated rather than written. They arrive long, hedged, and full of AI tells —
scene-setting openers, relentless triads, "it's not just X, it's Y", section closers that
restate the section.

Redacting such a description word by word produces something worse than the original: the
tells survive, the specifics vanish, and the reader gets `[…]` where the meaning was.
Read the row, understand the defect, then write the issue from scratch against the five
moves.

A row already written to the five moves makes this shorter rather than unnecessary. Move
1 is usually the part that cannot survive publication unchanged, because the internal
version orients by naming the practice.

## Voice

Plain English. Short paragraphs on a single point. Prose rather than bullets, except
where there are genuinely three or more parallel items or a sequence of steps.

Never claim something is "secure" — say "security focused". Never use "ensures". No
hyperbole, no marketing language, no hedged non-claims like "can help to potentially
improve".

Write as a person to a person. "You" for the reader. Avoid "we" unless you can name who
"we" is, which in an issue you usually cannot.

## What to cut

- Openers that set the scene or restate the title. Move 1 orients the reader, which is
  not the same thing as warming them up
- Closing paragraphs that summarise what was just said
- Three adjectives where one is true
- Anything about where you were or what you were doing when you found it — that belongs
  to the register row, and is usually unpublishable anyway
