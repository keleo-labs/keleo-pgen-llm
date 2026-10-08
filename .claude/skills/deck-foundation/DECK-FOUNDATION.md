# Deck Foundation

> **Vendored copy.** This tree is distributed with `keleo-pgen-llm` so the
> capability works from a clone without a user-level install. It tracks the
> global skill at `~/.claude/skills/deck-foundation/` version by version; the only
> intended difference is that paths are repo-relative rather than
> `~/.claude/skills/…`. If the two diverge otherwise, the global copy is
> upstream. Re-copy with `python3 utils/vendor-skills.py`.

Version: 2.5.0

> **2.0.0 changes the default.** A deck built from a source document now
> follows that document's structure instead of being re-argued into a
> narrative shape. Citations and speaker notes are required rather than
> optional. See §2.1 and §5.

Shared workflow for every deck-producing skill. Not a skill itself — the
`slide-deck`, `pitch-deck` and `exec-readout` skills each read this, then add
their own narrative shape and content rules on top.

Decks are authored as **Slidev markdown** and published to **Google Slides**
and **PDF**. Slidev is the design layer: it gives typographic control a
slide-by-slide API call cannot, and its `pptx-editable` export converts to
native, editable Google Slides shapes.

---

## 1. Pipeline

```
slides.md  ──slidev export──▶  .pptx  ──Drive upload──▶  Google Slides  ──▶  PDF
          (pptx-editable)            (convert on import)
```

`publish-deck.py` runs the whole chain. There is no direct Slidev → Google
Slides export; the pptx hop is required, which is why §4's constraints exist.

## 2. Workflow

| Step | Action |
|------|--------|
| 1. Plan | Establish subject, audience, decision being asked for, length. Agree the spine before writing slides. |
| 2. Scaffold | `new-deck.py <dir> --title "…"` — creates the project, copies the theme, installs Slidev + Playwright. |
| 3. Structure | **If there is a source document, derive the spine from it (§2.1).** Otherwise choose a narrative shape from `narrative-guide.md`. Either way, write the slide titles *first*, as a sequence of assertions, and check they read as an argument on their own. |
| 4. Write | Fill slides using the layouts in §3 and the rules in `slide-grammar.md`. Carry each slide's citations in `sources` and write its speaker notes as you go (§5). |
| 5. Publish | `publish-deck.py slides.md --name "…" --pdf --review` |
| 6. Review | Render and **look at every slide** (§7). Fix what reads badly. Never report a deck as done without this. |

Step 6 is not optional. Layout problems are invisible in markdown and obvious
in a thumbnail.

Steps 5 and 6 cycle: publishing is how you find the layout defects, so expect
several rounds. Drive cannot replace a deck in place, so each round uploads a
new file — `publish-deck.py` records the ID it created in
`<workdir>/.published.json` and trashes it on the next run, which is what
stops the cycle filling Drive with near-identical decks. Two consequences
worth knowing:

- **The URL changes every publish.** Give the user the link from the final
  run, not an earlier one.
- **Deleting the build directory loses the thread.** The next publish then
  has nothing to supersede and leaves the previous deck behind. `--prune`
  cleans that up by matching on deck name; `--keep-previous` opts out of
  replacement entirely when you want the versions kept.

### 2.1 Working from a source document

**The default is fidelity, not reinterpretation.** When the user supplies a
report, paper or memo, that document *is* the deck's structure. Walk its
sections in order and give each one the slides it needs. Do not treat it as
raw research to be mined for a fresh argument.

This matters because the author already made the structural decisions — what
leads, what supports, what is load-bearing, what was deliberately left out.
Re-arguing the material silently discards that work, and the usual symptom is
a deck that covers two thirds of the source and quietly drops the sections
that did not fit the imposed shape.

| Do | Don't |
|---|---|
| Map sections to slides, in the source's order | Impose SCQA or Before–After–Bridge over a document that already has a shape |
| Keep the author's emphasis and proportions | Promote a minor point because it makes a better hook |
| Use the source's own figures and claims | Harvest numbers the source did not assert (§2.2) |
| Propose a restructure, and apply it if accepted | Restructure silently |

Before writing, state the section-to-slide mapping. If a different order
would genuinely serve the audience better, **say so and give the reason** —
then follow the user's answer. Reshaping on request is fine; reshaping by
default is not.

Narrative shapes from `narrative-guide.md` still apply when there is no
source document, when the user asks for a reshape, or *within* a section that
has no internal order of its own.

### 2.2 Where a figure may come from

A figure may be used only if the source **asserts** it. Reference lists,
citation titles, footnotes, captions and appendix metadata are not
assertions — they are bibliographic furniture.

The failure is specific and easy to commit: a cited work titled *"X commits
five billion to …"* is a title, not a claim the document made. If the author
had wanted the figure in the argument they would have put it there. Lifting
it produces a headline number the source does not support and the audience
can challenge.

If a figure is genuinely needed and the source does not assert it, ask, or
mark it `illustrative` on the slide.

## 3. Layouts

Theme: `theme-redhat` (Red Hat brand). Set per-slide via `layout:` frontmatter.

| Layout | Use for | Key frontmatter |
|--------|---------|-----------------|
| `cover` | Opening slide | `variant` dark\|red\|light, `eyebrow`, `byline`, `date` |
| `section` | Divider between movements | `variant`, `number` |
| `default` | Assertion + supporting evidence | `eyebrow` |
| `columns` | 2–4 parallel, non-sequential items | `items[]` of `{heading, body}` |
| `steps` | A sequence or phased plan | `items[]` of `{heading, body, caption}`, `numbered` |
| `stats` | 1–3 headline figures | `items[]` of `{value, label, source}` |
| `quote` | Verbatim external voice | `variant`, `attribution`, `role` |
| `statement` | A single claim at a hinge point | `variant` |
| `split` | Claim beside its chart/image | `ratio`, `image`, or `::right::` slot |
| `closing` | The ask | `variant`, `actions[]`, `contact` |

Every content layout — `default`, `columns`, `steps`, `stats`, `quote`,
`split` — also accepts `sources`, the citation band described in §5.

Notes:
- `items` arrays are YAML in frontmatter, not markdown body.
- `statement` deliberately has no body slot. If the claim needs support on the
  same slide, it is not a statement slide.
- `stats` renders a single figure differently from a row of them — a lone
  number sits beside its reading rather than above it.

### Reserved frontmatter keys

Slidev consumes some keys as configuration before layouts see them. The
speaker's name is therefore `byline`, **not** `presenter` — `presenter` is a
Slidev config key and silently never reaches the layout. Others to avoid as
layout props: `title`, `theme`, `layout`, `transition`, `background`, `class`.

## 4. Conversion safety

The pptx hop constrains what can be used. These are empirically verified, not
inferred.

**Survives conversion**

- Text shapes with exact brand hex colours; Red Hat Display / Text / Mono
- Flex and grid positioning; explicit font sizes
- Solid fills, including per-slide dark and red backgrounds
- Solid borders used as rules
- `list-style` markers — they become real bulleted/numbered paragraphs
- **Speaker notes** — Slidev's trailing `<!-- … -->` block becomes a real
  PowerPoint notes slide and then a Google Slides speaker-notes box, mapped
  one-to-one per slide
- **Hyperlinks** — markdown links become real external link runs, in
  paragraphs and inside list items alike

**Does not survive**

| Avoid | Use instead |
|-------|-------------|
| Frontmatter `background:` | A fill class on the layout root (`variant` props do this) |
| `theme: none` | A real theme — without one there is no type scale |
| Markdown inside raw HTML blocks | Markdown at the top level of the slide |
| `display: contents` | Explicit markup for the special case |
| Pseudo-element `content` | A real character in the template |
| Gradients, shadows, border-radius, inline SVG | Flat fills and rules. For a *diagram*, use the `diagram` layout — the build rasterises it and the publish upgrades it to native shapes (§6) |
| `::marker` colour | Nothing — markers take the paragraph colour in PowerPoint. The marker survives, its colour does not, so do not rely on a red bullet as a brand device |
| Brand colour on link text | Nothing — Google Slides rewrites every link run to its own HYPERLINK blue and forces an underline. Keep links out of body copy and confine them to the `sources` band, where blue-underlined text reads as a citation |

**Text re-wraps on conversion, and the body does not move with it**

This is the sharpest form of the metric mismatch and the one most likely to
ruin a slide. The exporter emits each text element as a shape positioned
where Chromium put it. Google Slides then sets the same string *slightly
wider*, so a heading that fits one line in the browser can wrap to two after
conversion — and because the shape below it is already pinned, the second
line lands on top of it.

Two consequences:

- **Reserve space for the line that might appear.** The content layouts give
  their title a `min-height` of two lines rather than letting it size to its
  text, so a re-wrap is absorbed. A title long enough to need three lines
  defeats this, so keep titles to roughly **50 characters** — 51 has been
  observed fitting and 55 wrapping to three.
- **The same applies downward.** Anything pinned below the content — a
  `caption`, the `sources` band — is pushed off the slide entirely when the
  content above it runs long. See `slide-grammar.md` §4 for the per-column
  body budgets this implies.
- **Never trust the local render for this.** The browser is the engine that
  gets the wrap *wrong* relative to the deliverable.

**Leave vertical slack between stacked text**

The exporter measures each text element in Chromium and emits a PowerPoint
shape of that size. PowerPoint then lays the same string out in a slightly
taller line box, so text sized exactly to its content overruns its shape and
lands on whatever sits beneath it. In the browser the slide looks correct;
only the converted deck shows the collision.

Allow roughly `1.75rem` between a body and the caption or source line under
it, and about `1.1rem` between a heading and its body. Spacing that looks
merely adequate on screen is not enough. This is why §7 checks the
**published** deck and not the local render.

Font *embedding* does not survive: recipients without Red Hat fonts installed
see a substitute. The PDF export is unaffected, so send PDF when typography
must be guaranteed.

Adding a layout means re-verifying it through §7 — the table above is the
record of what has been tested, not a guarantee about untested constructs.

## 5. Citations and speaker notes

Both are required on a deck built from a source document, and both survive
conversion (§4).

### Citations

Content layouts take a `sources` array. Each entry is a `label` and an
optional `url`:

```yaml
---
layout: columns
sources:
  - label: Hellekson, 2026
    url: https://www.redhat.com/en/blog/lightwell-reality-check
  - label: Internal adoption review, 2026
---
```

It renders as a small grey line at the foot of the slide, links underlined.

- **Cite the slide, not the deck.** A reader looking at one slide should see
  where its claims came from without hunting for a references page.
- **Carry the source's own citation across.** If a sentence in the report
  cited Hellekson, the slide built from that sentence cites Hellekson.
- **Link where the source linked.** The `url` comes from the source
  document, not from a search.
- **Label by author and year**, matching the source's citation style — the
  foot line is too small for a full title.
- **Light slides only.** Google Slides forces its own blue on links, which
  has too little contrast on the dark and red variants. Covers, section
  dividers, statements and closings should not carry citations anyway.
- A figure with no citable origin is either the audience's own data or a
  figure that should not be on the slide (§2.2).

### Speaker notes

Anything after a `<!-- … -->` block at the end of a slide becomes the
speaker notes, one notes box per slide.

**Write notes for every content slide, derived from the source's own
prose.** This is what makes a source-faithful deck usable: the slide carries
the assertion and its evidence, and the notes carry the paragraph the
assertion came from — the reasoning, the qualifications, the detail that
would have crowded the slide.

- Draw on the **source's wording**, condensed. Notes are not a place to
  invent material the document does not contain.
- Two to five sentences. Enough to speak from, not a script to read.
- Put the caveats and the anticipated objections here.
- Where the source made a point the slide had to compress, the notes are
  where the full version belongs.

## 6. Diagrams and images

A deck can carry both. The difference is whether a **spec** exists.

**Which diagram to draw** is a separate decision from how to draw it, and
the wrong method costs more than a bad layout.
`diagram-foundation/references/method-catalogue.md` carries the selection
matrix; the `diagram` skill walks it. Reach for that before authoring a spec
by hand.

**Spec-backed diagram.** Reference a spec in the format
`diagram-foundation/scripts/render-diagram.py` reads — either a `.json`
native layout or a `.mmd` carrying Mermaid source:

```yaml
---
layout: diagram
diagram: ./assets/option-b-topology.json
eyebrow: Event-driven
---
# Remediation starts within minutes
```

Publishing then does three things on its own. `build-diagrams.py` fits the
spec to the slide's aspect and renders a PNG beside it, so the local preview
and a `--pptx-only` export are already right. Slidev carries that PNG into the
deck. Finally `upgrade-diagrams.py` replaces the picture with **native Google
Slides shapes** — rounded rectangles and arrowed connectors someone can select
and move.

The upgrade is additive. If it cannot find the slide, or the batch fails, the
deck keeps the picture and stays usable; the publish reports what it skipped.

**Not every diagram can become shapes.** A native spec and a Mermaid
flowchart both can. A sequence, ERD, class or state diagram cannot —
lifelines and attribute compartments have no Slides equivalent — so those
stay pictures and the upgrade pass says so rather than failing. The manifest
carries each diagram's laid-out scene, or `null` where there is none; it is
the handoff between `build-diagrams.py` and `upgrade-diagrams.py`, and the
scene travels in it because a Mermaid-backed diagram has no declarative spec
to rebuild from without invoking Mermaid a second time.

**Colour.** Diagrams render in the Red Hat palette on a slide rather than the
engine's default navigator blue, so a figure reads as part of the deck. Only
the colour family changes — the spec is untouched and the same spec still
renders in navigator colours for a report. `build-diagrams.py --palette
navigator` opts out; whatever is chosen, `upgrade-diagrams.py` must be given
the same one or the native shapes will not match the picture they replace.
See `diagram-foundation/DIAGRAM-FOUNDATION.md` → Palettes.

**Any other image** — a screenshot, a photo, an SVG with no spec — uses
`image:` on the same layout, or any layout that takes one. It is embedded as a
picture and no shape pass is attempted. Rasterise SVG yourself first; Slidev
will not carry it.

**Aspect.** A flow authored top-to-bottom for a report page is reconsidered
for 16:9 at build time. Where no orientation fits, the build says so rather
than mangling the diagram — a diagram that will not fit a slide is usually one
carrying more than one idea, and the fix is to split it. See
`diagram-foundation/DIAGRAM-FOUNDATION.md` for why wrapping was tried and
rejected.

## 7. Visual review

```bash
python3 scripts/publish-deck.py slides.md --name "…" --pdf --review
python3 scripts/review-deck.py <presentationId> --out /tmp/deck-review
```

Then **Read the PNGs**. Check each slide for:

- Text overflowing or colliding with another element
- Dead space concentrated at one edge rather than distributed
- Headlines that wrapped to an awkward single trailing word
- Colour that vanished into its background
- Missing elements — the usual cause is a frontmatter key that Slidev reserved

To iterate on design only, skip the upload: `npx slidev export slides.md
--format png --output png` is faster and renders the same layout engine.

## 8. Scripts

| Script | Purpose |
|--------|---------|
| `new-deck.py` | Scaffold a deck project against a brand theme |
| `publish-deck.py` | Build diagrams → export → upload → convert → upgrade diagrams → PDF, trashing the version it replaces |
| `build-diagrams.py` | Fit each referenced diagram spec to the slide and render it to PNG; writes `build/diagrams.json` |
| `upgrade-diagrams.py` | Replace published diagram pictures with native Slides shapes. Runs from `publish-deck.py`; skips rather than fails |
| `review-deck.py` | Render a published deck to local PNGs |
| `inspect-template.py` | Assess a .pptx as a branding donor |
| `slides-template.py` | Map a Google Slides template's layouts to semantic roles |
| `gwsclient.py` | `gws` CLI wrapper (module, not a command) |
| `templatecache.py` | Shared template-cache access (module) |

Needing a mechanical helper that does not exist means writing or extending one
here — not doing the work inline.

## 9. Adding a brand theme

Themes live at `theme-<name>/` and are selected with `new-deck.py --theme
<name>`. To derive one from an existing deck:

1. Export the source deck to .pptx; run `inspect-template.py` on it to harvest
   colours, fonts and layout inventory.
2. Build `theme-<name>/` with `package.json` (name must start
   `slidev-theme-`), `styles/base.css` holding brand tokens, and `layouts/`
   covering the roles in §3.
3. Verify every layout through §7 before using it for real work.

## 10. Related documents

- `slide-grammar.md` — how an individual slide should be written
- `narrative-guide.md` — deck-level narrative shapes
- `extension-template.md` — adding a new deck-type skill
