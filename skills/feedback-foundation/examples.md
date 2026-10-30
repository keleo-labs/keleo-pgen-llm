# Worked examples

Four register rows and the issues written from them. Read `drafting.md` for the five
moves and `sanitisation.md` for what may be said; this file shows both applied at once.

Each example gives the row as filed, the issue as published, and a note on what moved
where.

The rows are real in shape and invented in content. Practice, vendor and device names in
the "before" text are made up, because this file is itself distributed in a public
repository — a teaching example of what must not be published cannot be built out of
things that must not be published.

---

## 1. A tooling defect, nothing to redact

Most issues are this case. The defect is in public code, names no product and no
customer, and the only work is making it readable.

**Register row 41 — Issue — keleo-pgen-llm**

> `resolve-context.py` does not implement the element-level merge rules in merge.md 4.2,
> 4.3, 5.6 and 6.10. Description preservation takes last-writer-wins instead of
> re-stamping from the kernel; scalar first-writer-wins is not applied so `focusName`,
> `contributesTo`, `mapsTo` and `partOf` are owned by whichever layer wrote last;
> primitive arrays are replaced rather than unioned, so `personaNames` contributed by one
> practice is lost when another redeclares the group; assets merge field by field instead
> of replacing whole. Observed on a two-practice composition where a group with three
> members from each practice resolved to three.

Accurate and complete. It also opens on a filename and four specification section
numbers, so a reader who does not already know what the resolver does cannot get past
sentence one. The published issue keeps every fact and adds the paragraph that was
missing.

**Published as [keleo-pgen-llm#17]**

> **Title:** Merge lets a later practice silently take ownership of a baseline element
>
> Register row: 41
>
> A method is assembled by flattening a baseline and every practice that builds on it
> into one document — the effective context. That document is what the generation agents
> read as their picture of the baseline, so whatever it says an element is, is what they
> believe it is. `resolve-context.py` produces it.
>
> Four of the rules that decide which layer owns a value are not implemented, so the
> answer is currently "whichever practice was loaded last". A baseline alpha ends up
> carrying one extension practice's prose as its definition. A persona group that two
> practices each contribute three members to resolves with three members rather than six.
> An asset redefined with a URL keeps the path from the definition it replaced.
>
> The cost is that nobody reading an effective context can tell which layer a value came
> from, and the agents that read it cannot either. An extension's narrower wording
> arrives on a baseline element and is treated as the baseline's own definition, which is
> exactly the distinction the merge rules exist to protect.
>
> Expected: the four rules are implemented and `tests/check-merge-semantics.py` covers
> each. The corpus-wide effective context will change; the before-and-after corpus scan
> is the check that it changes for the better.
>
> ## Detail
>
> | Rule | merge.md | Current behaviour |
> |---|---|---|
> | Description preservation | 4.2, 7.4 | Last writer wins; no re-stamp pass from the kernel |
> | Scalar first-writer-wins | 4.3, 7.3 | Overlay taken unconditionally for `focusName`, `contributesTo`, `mapsTo`, `partOf` |
> | Primitive array union | 5.6, 6.7 | Arrays replaced rather than concatenated and deduplicated |
> | Atomic asset replacement | 6.10 | Assets merged field by field |
>
> Reproduced on a composition where two practices each contribute three members to one
> persona group; the resolved group carries three.

What changed: a first paragraph that says what the effective context is and who reads
it, consequences stated as things that happen to a document rather than as unimplemented
clauses, and the specification references moved into a table below the fold. Nothing was
removed.

---

## 2. A practice defect whose fix is in a prompt — published, heavily sanitised

This is the case the routing rule exists for. The row was observed in a practice, but
the fix lands in a generation prompt, so the issue is published with the practice,
the products and the circumstance of discovery left behind in the row.

**Register row 46 — Issue — observed in a practice, fix in Phase 2**

> Pattern across the Northwind Accelerator Platform Design practice and two others
> generated from the same prompt: strong on what to measure and why, absent on the
> identifiers an operator needs. The practice establishes which runtime signals matter
> and the attribution constraint around shared devices is excellent. What it does not
> carry is a single metric key, for the QX-900 or anything else. Observed while writing a
> reference architecture for a client sourced only from these practices — I could
> describe what to watch and had nothing to put in a dashboard.

**Published as [keleo-pgen-llm#23]**

> **Title:** Observability guidance names the signals to watch but no metric keys
>
> Register row: 46
>
> Phase 2 maps a source methodology onto a baseline and decides what the generated
> practice says about running the thing it describes. Where the source says what to watch
> in production, that guidance is what a downstream reader — someone writing a reference
> architecture or standing up a dashboard — has to work from.
>
> The generated guidance says which signals matter and why, and names no metric key for
> any of them. This holds across three practices produced from the same prompt, so it is
> the prompt rather than any one mapping.
>
> A reader can therefore understand what to watch and still have nothing to paste into a
> dashboard or an alert rule. They go back to the source material, which is the thing the
> practice was meant to save them doing.
>
> Expected: where the source names a signal, the mapping carries the metric key that
> exposes it and an indicative threshold where one can be stated. Where the source gives
> no key, the guidance says so rather than leaving the omission to look deliberate.

What was left in the register: the practice name, the vendor and hardware names, the
specific signals, and the engagement the reader was writing for. What survives is the
whole defect — the published version is shorter and no less actionable, because the
missing thing is generic.

Note that move 1 could not be reused from the row. The row orients by naming the
practice; the issue orients by naming the phase that produced it. That is normal, and it
is why the rule is rewrite rather than redact.

---

## 3. An enhancement, where the value carries the case

An RFE has no "what is wrong". Moves 2 and 3 do the work: what you cannot do today, and
what becomes possible. Resist writing the design — move 4 states the shape of an
acceptable answer and hands the open questions to triage.

**Register row 96 — Enhancement — keleo-language**

> Redeclaration of practiceElements works well, but the intent needs clarifying and the
> schema has no way to express it. Redeclaration does not narrow the scope of an element
> — it makes it more specific. Platform becomes a developer platform, which becomes a
> platform on a named runtime. There is currently no mechanism to call out that dimension
> of specificity. Proposed: a new array property on a redeclared element […] Touches the
> schema, the semantics, and the merge logic in resolve-context.py and the viewer.

**Published as [keleo-language#2]**

> **Title:** A practice cannot say what it makes an inherited element more specific about
>
> Register row: 96
>
> A practice can redeclare an element it inherits — take the generic definition of
> something and restate it for its own context. The generic concept of a platform becomes
> a developer platform, and a practice building on that makes it a platform on a
> particular runtime. Each layer says more about the same thing rather than replacing it.
>
> Nothing in the document records what each layer contributed. After composition you have
> one element carrying the most specific wording that happened to be applied last, and no
> way to ask which practices made it more specific or along what dimension.
>
> Two things become possible if it is recorded. A reader can see the lineage of an element
> rather than only its endpoint, which is the difference between understanding why a
> definition is narrow and guessing. And a composition can be explained in terms of what
> each practice contributed, which is what someone assembling a method is actually
> choosing between.
>
> Expected: a redeclaring practice can name the specificity it contributes, and
> composition resolves the accumulated chain across whichever practices are loaded, most
> specific first. The chain has to be derived at composition time rather than authored,
> because no author knows which practices a given method will load.
>
> Open for triage: how to order contributions when several practices add specificity to
> the same element without depending on one another, and whether an authored chain should
> be an error or merged.
>
> ## Detail
>
> Touches the schema (a new property on the element type), the semantics — specificity is
> not the same as narrowing scope, and the distinction needs stating — and the merge
> implementation in `resolve-context.py` and in the viewer.

What changed: the example carries the explanation rather than following it, the product
name is gone, and the proposal is stated as an outcome with its constraint rather than as
a design. The ordering question moved from a buried sentence to an explicit ask.

---

## 4. A row that cannot be published

**Register row 58 — Issue — a defect in practice content**

> The sizing table in [a named practice] gives per-node figures that contradict the
> vendor's published maximums for [a named appliance].

Nothing survives. The defect *is* the content: strip the practice, the vendor and the
appliance and what remains is "a table has wrong numbers in it", which tells a
maintainer nothing and still signals that the catalogue covers that vendor.

The row stays in the register, is worked from there, and gets Issue State `Not
Published` with the reason in Resolution Summary. Do not publish a vague version to have
something on the tracker.

---

## The pattern across all four

Move 1 is the one being added, and it is written fresh every time. The register row
orients an internal reader by naming the practice and the engagement; the issue orients a
public reader by naming the component and its job. Those are different sentences about
the same thing, which is why the row cannot be redacted into the issue.

Everything the row carried that the issue cannot is still in the row. The pointer back to
it is the first line of the body.
