#!/usr/bin/env python3
"""Lint a Slidev deck against the deck-foundation rules before publishing.

Checks the mechanical half of `slide-grammar.md`. It cannot tell whether a
sentence explains anything — that is what reading the deck is for — but it
reliably catches the defects that survive into a published artifact:

  titles      Every slide carries a visible `# ` heading; no two consecutive
              slides share one; titles stay inside the ~50-character budget
              that Google Slides wraps at (DECK-FOUNDATION §4).
  density     Body text per item against the per-column budgets in
              slide-grammar §6, and item counts against the §3 maximum.
  balance     A content slide whose speaker notes dwarf its body has put the
              explanation on the wrong side of the line (§11). The slide is
              supposed to stand alone.
  fragments   Bullets with no finite verb — the "Pay for the link" shape.
              Always a warning, never an error: the test is a heuristic and a
              false positive must not block a publish.
  sources     Content slides carrying a claim need a `sources` entry (§10).
  notes       Content slides need a speaker-notes block (§11).

Slidev separates slides with a `---` line. Frontmatter is YAML; the body is
markdown; anything inside a trailing `<!-- … -->` is speaker notes.

Usage:
    python3 scripts/lint-deck.py slides.md
    python3 scripts/lint-deck.py slides.md --checks titles density
    python3 scripts/lint-deck.py slides.md --json
    python3 scripts/lint-deck.py slides.md --max-title 50

Exit status is 1 if any error-severity finding is reported, 2 on a usage or
read error, else 0.
"""

import argparse
import json
import re
import sys

# Measured in DECK-FOUNDATION §4: 51 characters has been observed fitting the
# two-line title zone and 55 wrapping to three, which collides with the body.
DEFAULT_MAX_TITLE = 50

# The budget exists because a third title line lands on the content pinned
# beneath it. A cover, section, statement or closing has nothing pinned below,
# so a long title there costs nothing and the tight budget would be noise.
CHROME_MAX_TITLE = 90

# slide-grammar §6. Index by the number of items in a columns/steps array.
BODY_BUDGET = {1: 260, 2: 200, 3: 140, 4: 100}
BODY_BUDGET_DEFAULT = 100

# slide-grammar §3: three is the working maximum, four at a push.
MAX_ITEMS = 4

# Layouts that carry an argument, and so need a title, notes and citations.
CONTENT_LAYOUTS = {"default", "columns", "steps", "stats", "split", "diagram", "quote"}

# Layouts that are structural furniture rather than evidence.
CHROME_LAYOUTS = {"cover", "section", "statement", "closing"}

# Layouts whose argument is in a picture rather than in words.
VISUAL_LAYOUTS = {"diagram", "split"}

CHECKS = ["titles", "density", "balance", "fragments", "movements",
          "tone", "sources", "notes"]

# --- Register (slide-grammar §5) ----------------------------------------
# All three lists produce warnings, never errors. Each is context-dependent:
# a human subject makes an agency verb correct, and a source may be quoted
# verbatim. A false positive that blocks a publish costs more than a missed
# phrase — the same call made for the fragment heuristic.

# A variable given agency over a decision. Matched with a preceding word so
# "the team decides" can be read and dismissed by eye.
RE_AGENCY = re.compile(
    r"\b(\w+)\s+(decides?|choose|chooses|picks?|drives?|dictates?|"
    r"determines?|wants?|knows?)\b", re.I)
# "...rather than to choose between good ones" is an infinitive, not agency.
INFINITIVE_MARKERS = {"to", "cannot", "can", "could", "will", "would", "may",
                      "might", "must", "should", "helps", "help", "not",
                      "never", "also", "only", "then", "and", "or"}
# Subjects for which the verb is correct, so the finding is suppressed.
HUMAN_SUBJECTS = {
    "you", "we", "they", "i", "he", "she", "who", "team", "teams", "architect",
    "architects", "operator", "operators", "engineer", "engineers", "owner",
    "owners", "customer", "customers", "organisation", "organization",
    "organisations", "organizations", "board", "sponsor", "someone", "nobody",
    "anyone", "everyone", "people", "person", "reader", "audience", "author",
    "presenter", "stakeholder", "stakeholders", "business", "client",
}

# Rhetorical heading shapes.
RE_CONTRARIAN = [
    (re.compile(r",\s+not\s+\w", re.I), "an \"X, not Y\" construction"),
    (re.compile(r"\bis not a\b|\bare not\b|\bis not\b", re.I),
     "a negated assertion"),
    (re.compile(r"^why\b.*\b(fail|fails|failed|breaks?|does ?n[o']t)\b", re.I),
     "a \"Why X fails\" construction"),
    (re.compile(r"^the (two|three|four|five|only) (things?|numbers?|reasons?)\b",
                re.I), "a \"the N things that matter\" construction"),
]

# Framing that editorialises instead of naming a mechanism.
DRAMATIC_PHRASES = [
    "well understood", "works on paper", "work on paper", "in the real world",
    "start to fail", "starts to fail", "survives a mistake",
    "the hard part", "breaks the assumption", "breaks down",
    "nobody tells you", "the dirty secret", "what nobody",
]

# A bullet with none of these is probably a noun phrase. Deliberately broad:
# this only ever raises a warning, so over-matching is the safe direction.
AUXILIARIES = {
    "is", "are", "was", "were", "be", "been", "being", "am",
    "has", "have", "had", "do", "does", "did",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "needs", "need", "requires", "require", "means", "gives", "gets",
}
VERB_SUFFIX = re.compile(r"\w+(?:s|es|ed|ing)$", re.I)
# Words ending in -s or -ing that are nouns far more often than verbs.
NOT_VERBS = {
    "is", "this", "its", "sites", "clusters", "services", "options", "costs",
    "jobs", "needs", "means", "times", "windows", "images", "updates",
    "nothing", "something", "everything", "during", "operations", "logs",
    "metrics", "policies", "resources", "workloads", "boundaries", "versions",
}


def split_slides(text):
    """Slidev slides, as (index, frontmatter_lines, body_lines, start_line).

    A `---` on its own line separates slides, and also delimits the document's
    opening frontmatter — so the first block is headmatter plus slide one.
    """
    lines = text.splitlines()
    blocks, current, start = [], [], 1
    for n, line in enumerate(lines, 1):
        if line.strip() == "---":
            blocks.append((start, current))
            current, start = [], n + 1
        else:
            current.append(line)
    blocks.append((start, current))
    # The file opens with `---`, so the first block is empty. An empty block
    # between two separators is not a slide either.
    blocks = [(s, b) for s, b in blocks if any(l.strip() for l in b)]

    slides = []
    pending_fm = None
    for start, block in blocks:
        if pending_fm is None and not slides and _looks_like_frontmatter(block):
            pending_fm = (start, block)
            continue
        if _looks_like_frontmatter(block):
            pending_fm = (start, block)
            continue
        fm_start, fm = pending_fm if pending_fm else (start, [])
        slides.append({
            "index": len(slides) + 1,
            "line": fm_start,
            "frontmatter": fm,
            "body": block,
        })
        pending_fm = None
    return slides


def _looks_like_frontmatter(block):
    """A YAML block, as opposed to markdown. Keys at column zero, no heading."""
    meaningful = [l for l in block if l.strip()]
    if not meaningful:
        return False
    if any(l.startswith("#") for l in meaningful):
        return False
    return bool(re.match(r"^[a-zA-Z_][\w-]*:", meaningful[0]))


def fm_value(frontmatter, key):
    for line in frontmatter:
        m = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("'\"")
    return None


def fm_has_block(frontmatter, key):
    return any(re.match(rf"^{re.escape(key)}:\s*$", l) for l in frontmatter)


def fm_items(frontmatter):
    """Body strings from an `items:` array, for the density check."""
    bodies, in_items = [], False
    for line in frontmatter:
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            break
        if in_items:
            m = re.match(r"^\s+(?:- )?body:\s*(.*)$", line)
            if m:
                bodies.append(m.group(1).strip().strip("'\""))
    return bodies


def fm_text_values(frontmatter):
    """Every reader-facing string in an `items:` array.

    `columns` and `steps` put their prose in `body`, but `stats` puts it in
    `value` and `label` — counting only `body` would read a stats slide as
    having no content at all.
    """
    out, in_items = [], False
    for line in frontmatter:
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            break
        if in_items:
            m = re.match(r"^\s+(?:- )?(body|label|value|heading|caption):\s*(.*)$",
                         line)
            if m:
                out.append(m.group(2).strip().strip("'\""))
    return out


def fm_item_count(frontmatter):
    count, in_items = 0, False
    for line in frontmatter:
        if re.match(r"^items:\s*$", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            break
        if in_items and re.match(r"^\s+- ", line):
            count += 1
    return count


def split_notes(body):
    """(content_lines, notes_lines) — notes are the trailing HTML comment."""
    text = "\n".join(body)
    m = re.search(r"<!--(.*?)-->\s*$", text, re.S)
    if not m:
        return body, []
    content = text[:m.start()].splitlines()
    return content, m.group(1).strip().splitlines()


def heading_of(content):
    for line in content:
        m = re.match(r"^#\s+(.*\S)\s*$", line)
        if m:
            return m.group(1)
    return None


def bullets_of(content):
    return [(n, m.group(1).strip())
            for n, line in enumerate(content)
            if (m := re.match(r"^\s*[-*]\s+(.*\S)\s*$", line))]


def words(text):
    return re.findall(r"[\w'-]+", text)


def looks_like_fragment(text):
    """No finite verb found. Heuristic — warning only."""
    toks = [w.lower() for w in words(text)]
    if len(toks) < 3:
        return True
    for t in toks:
        if t in AUXILIARIES:
            return False
        if t in NOT_VERBS:
            continue
        if VERB_SUFFIX.match(t) and len(t) > 3:
            return False
    return True


def finding(slide, check, severity, message):
    return {"slide": slide["index"], "line": slide["line"],
            "check": check, "severity": severity, "message": message}


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_titles(slides, max_title):
    out, previous = [], None
    for s in slides:
        title = s["_title"]
        budget = (CHROME_MAX_TITLE if s["_layout"] in CHROME_LAYOUTS
                  else max_title)
        if not title:
            out.append(finding(s, "titles", "error",
                               f"{s['_layout']} slide has no `# ` heading"))
        else:
            if len(title) > budget:
                out.append(finding(
                    s, "titles", "error",
                    f"title is {len(title)} characters, over the {budget} "
                    f"budget for a {s['_layout']} slide — it will wrap onto "
                    f"what sits beneath it: {title!r}"))
            if previous and title.lower() == previous.lower():
                out.append(finding(
                    s, "titles", "error",
                    f"title repeats the previous slide's: {title!r}"))
        previous = title
    return out


def check_density(slides):
    out = []
    for s in slides:
        count = fm_item_count(s["frontmatter"])
        if count > MAX_ITEMS:
            out.append(finding(s, "density", "error",
                               f"{count} items, over the {MAX_ITEMS} maximum"))
        budget = BODY_BUDGET.get(count, BODY_BUDGET_DEFAULT) if count else None
        if budget:
            for body in fm_items(s["frontmatter"]):
                if len(body) > budget:
                    out.append(finding(
                        s, "density", "error",
                        f"item body is {len(body)} characters against a "
                        f"{budget} budget at {count} items — it will push the "
                        f"caption or sources band off the slide"))
        bullets = bullets_of(s["_content"])
        if len(bullets) > MAX_ITEMS:
            out.append(finding(s, "density", "error",
                               f"{len(bullets)} bullets, over the "
                               f"{MAX_ITEMS} maximum"))
    return out


def check_balance(slides, ratio):
    out = []
    for s in slides:
        # A diagram or an image carries its argument in the picture, so a
        # body-word count says nothing about whether it stands alone — and
        # its notes legitimately carry the walkthrough. `split` is the same.
        if s["_layout"] not in CONTENT_LAYOUTS or s["_layout"] in VISUAL_LAYOUTS:
            continue
        body_words = len(words("\n".join(
            l for l in s["_content"] if not l.startswith("#"))))
        body_words += sum(len(words(b))
                          for b in fm_text_values(s["frontmatter"]))
        note_words = len(words("\n".join(s["_notes"])))
        if note_words and body_words * ratio < note_words:
            out.append(finding(
                s, "balance", "error",
                f"notes carry {note_words} words against {body_words} on the "
                f"slide — the explanation is on the wrong side of the line. "
                f"Move what a reader needs onto the slide"))
    return out


def check_fragments(slides):
    out = []
    for s in slides:
        candidates = [b for _, b in bullets_of(s["_content"])]
        candidates += fm_items(s["frontmatter"])
        for text in candidates:
            if looks_like_fragment(text):
                out.append(finding(
                    s, "fragments", "warning",
                    f"no finite verb, so this may be a fragment rather than a "
                    f"statement: {text!r}"))
    return out


def check_movements(slides):
    """A movement must introduce itself before its first member.

    Two symptoms, both mechanical. A divider carrying only a heading leaves
    the reader to work out why the deck turned. A divider followed straight
    by a diagram drops the audience into a member of a set they have not been
    told exists — the shape that prompted this check.

    Whether the slides after a divider are "a parallel set" needing an
    overview is a judgement, so the rule for that lives in the instructions
    and only its commonest symptom is detected here.
    """
    out = []
    for i, s in enumerate(slides):
        if s["_layout"] != "section":
            continue
        body = [l for l in s["_content"]
                if l.strip() and not l.lstrip().startswith("#")]
        if not body:
            out.append(finding(
                s, "movements", "error",
                "section divider carries only a heading — add a sentence "
                "saying what this movement settles and why it follows the "
                "last one"))
        nxt = slides[i + 1] if i + 1 < len(slides) else None
        if nxt and nxt["_layout"] in VISUAL_LAYOUTS:
            out.append(finding(
                nxt, "movements", "warning",
                f"a {nxt['_layout']} slide opens this movement — if it is one "
                f"of a set, the audience meets a member before being told the "
                f"set exists. Put an overview slide first"))
    return out


def tone_findings(text, where):
    """Register violations in one string (slide-grammar §5). Warnings only."""
    out = []
    for subject, verb in RE_AGENCY.findall(text):
        if subject.lower() in HUMAN_SUBJECTS:
            continue
        if subject.lower() in INFINITIVE_MARKERS:
            continue
        # "Choose B, because..." is an imperative addressed to the reader, and
        # a capital mid-sentence is a sentence start rather than a subject.
        if verb[0].isupper():
            continue
        out.append(f"{where}: \"{subject} {verb}\" gives a decision to "
                   f"something that cannot make one — name the person "
                   f"choosing and make this an input to their choice")
    for phrase in DRAMATIC_PHRASES:
        if phrase in text.lower():
            out.append(f"{where}: {phrase!r} editorialises rather than naming "
                       f"a mechanism — say what has to be satisfied instead")
    return out


def check_tone(slides):
    out = []
    for s in slides:
        title = s["_title"] or ""
        for pattern, label in RE_CONTRARIAN:
            if pattern.search(title):
                out.append(finding(
                    s, "tone", "warning",
                    f"title uses {label}, so it withholds rather than states: "
                    f"{title!r}"))
                break
        body = " ".join(
            [title]
            + [l for l in s["_content"] if not l.lstrip().startswith("#")]
            + fm_text_values(s["frontmatter"]))
        for message in tone_findings(body, "slide copy"):
            out.append(finding(s, "tone", "warning", message))
    return out


def check_sources(slides):
    return [finding(s, "sources", "warning",
                    f"{s['_layout']} slide has no `sources` entry")
            for s in slides
            if s["_layout"] in CONTENT_LAYOUTS
            and not fm_has_block(s["frontmatter"], "sources")]


def check_notes(slides):
    return [finding(s, "notes", "error",
                    f"{s['_layout']} slide has no speaker notes")
            for s in slides
            if s["_layout"] in CONTENT_LAYOUTS and not s["_notes"]]


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Lint a Slidev deck against the deck-foundation rules.")
    parser.add_argument("deck", nargs="+", help="slides.md to check")
    parser.add_argument("--checks", nargs="+", choices=CHECKS, default=CHECKS,
                        help="Checks to run (default: all)")
    parser.add_argument("--max-title", type=int, default=DEFAULT_MAX_TITLE,
                        help=f"Title character budget (default {DEFAULT_MAX_TITLE})")
    parser.add_argument("--notes-ratio", type=float, default=2.0,
                        help="Flag when notes exceed body words by this "
                             "multiple (default 2.0)")
    parser.add_argument("--json", action="store_true",
                        help="Emit findings as JSON")
    args = parser.parse_args()

    results = []
    for path in args.deck:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError as err:
            print(f"Error: cannot read {path}: {err}", file=sys.stderr)
            return 2

        slides = split_slides(text)
        for s in slides:
            content, notes = split_notes(s["body"])
            s["_content"], s["_notes"] = content, notes
            s["_title"] = heading_of(content)
            s["_layout"] = fm_value(s["frontmatter"], "layout") or "default"

        findings = []
        if "titles" in args.checks:
            findings += check_titles(slides, args.max_title)
        if "density" in args.checks:
            findings += check_density(slides)
        if "balance" in args.checks:
            findings += check_balance(slides, args.notes_ratio)
        if "fragments" in args.checks:
            findings += check_fragments(slides)
        if "movements" in args.checks:
            findings += check_movements(slides)
        if "tone" in args.checks:
            findings += check_tone(slides)
        if "sources" in args.checks:
            findings += check_sources(slides)
        if "notes" in args.checks:
            findings += check_notes(slides)

        findings.sort(key=lambda f: (f["slide"], f["check"]))
        results.append({"deck": path, "slideCount": len(slides),
                        "findings": findings})

    errors = sum(1 for r in results for f in r["findings"]
                 if f["severity"] == "error")
    warnings = sum(1 for r in results for f in r["findings"]
                   if f["severity"] == "warning")

    if args.json:
        print(json.dumps({"decks": results}, indent=2))
        return 1 if errors else 0

    for r in results:
        print(f"{r['deck']}: {r['slideCount']} slides")
        if not r["findings"]:
            print("  no issues found")
        for f in r["findings"]:
            print(f"  [{f['severity']}] slide {f['slide']} "
                  f"({f['check']}): {f['message']}")
        print()
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
