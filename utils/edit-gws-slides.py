#!/usr/bin/env python3
"""Apply edits to a Google Slides presentation via the gws CLI.

Edits slide body copy, speaker notes and deck structure in place, preserving
layout, theme and formatting. Intended for copy passes and restructures over
an already-published deck (style fixes, terminology changes, citation
relabelling, adding slides cloned from existing layouts) where regenerating
from source is not available or not wanted.

Every edit is verified before and after the write:

  * Pre-flight counts each `find` string across body text and notes text.
    A string that matches nothing is an error by default, because a silent
    no-op edit is the common failure mode of a bulk copy pass.
  * Post-flight re-fetches the deck and reports any edit that did not take,
    which catches ordering collisions between edits.

Usage:
    # List the shapes (objectIds and text) on slides 4 and 7, to address edits
    python3 utils/edit-gws-slides.py <presentation-id> --shapes 4,7

    # Report what would change, write nothing
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json --dry-run

    # Apply the edits
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json

    # Apply and rename the Drive file
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json \
        --rename "Coordinating updates across a multi-vendor OpenShift stack"

    # Tolerate edits that match nothing (e.g. re-running a partly applied set)
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json --allow-missing

Edits file format — a JSON array, applied in order. Content edits:

    [
      {"find": "old text", "replace": "new text", "note": "deck-wide"},
      {"find": "SLIDE X", "replace": "SLIDE 8", "slide": 8, "note": "one slide only"},
      {"notesForSlide": 11, "replace": "full replacement notes", "note": "slide 11"},
      {"setText": "p7_i12", "text": "**Storage Array:** same array\\n**Map:** offload",
       "note": "rewrite a card body, keeping its fonts"},
      {"setText": "g1_table", "cell": [2, 4], "text": "Not applicable"},
      {"deleteElement": "p5_i30", "note": "remove a badge"},
      {"objectId": "p1_i5", "fontSize": 44, "note": "shrink title to fit"},
      {"objectId": "p6_i13", "widthInches": 8.8, "note": "widen citation band"}
    ]

Structure edits (a file holding these may hold nothing else, because they
renumber slides and content edits address slides by number):

    [
      {"duplicateSlide": 4, "newId": "qualify", "note": "clone the fork layout"},
      {"deleteSlide": 17, "note": "blank slide"},
      {"reorder": [1, 2, 3, "qualify", 4, 5]}
    ]

`find` edits do a case-sensitive replace across slide body copy only, optionally
restricted to the slides listed in `slide` (a number or a list); speaker notes
are deliberately out of scope so a body edit cannot silently rewrite a note.
A replacement takes the style of the first matched character, so use it for
runs of uniform style.

`setText` replaces the whole text of one shape, or of one table cell given
`cell: [row, column]` (0-indexed), and re-applies the shape's original text and
paragraph style so the new copy keeps the deck's fonts, sizes and colours.
Two inline marks are understood: `**bold**` takes the style of the shape's
first bold run (or the base style made bold), and `[label](url)` becomes a
hyperlink. Use `\\n` for a paragraph break. In a table, `styleFromCell:
[row, column]` takes the style from another cell instead — useful when a
cloned table's per-cell colours carried meaning the new content does not.

`notesForSlide` replaces a slide's entire speaker-note body (1-indexed).
Replacing whole notes rather than fragments is the right default: exported
decks carry vertical-tab soft line breaks mid-sentence, so a fragment that
looks contiguous on screen often will not match.

`objectId` edits reshape one element and take `fontSize`, `widthInches`, or
both — the two remedies for copy that no longer fits the box an export sized
around the old wording. Widening only changes the element's horizontal scale.

`duplicateSlide` clones a slide (with its notes) directly after the original;
`newId` names the clone so `reorder` can place it in the same run. `reorder`
must list every slide exactly once, by current number or objectId, in the
final order.

Exit codes: 0 success, 1 pre-flight or post-flight failure, 2 bad input.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from _shared import GWS as GWS_PATH
TIMEOUT = 120

CONTENT_KINDS = ("find", "notesForSlide", "objectId", "setText", "deleteElement")
STRUCTURE_KINDS = ("duplicateSlide", "deleteSlide", "reorder")


def run_gws(args, parse=True):
    """Invoke the gws CLI and return parsed JSON, stripping its stdout preamble."""
    result = subprocess.run(
        [GWS_PATH, *args], capture_output=True, text=True, timeout=TIMEOUT
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"gws {' '.join(args[:3])} failed: {detail[:800]}")
    if not parse:
        return result.stdout
    # gws prints "Using keyring backend: ..." before the JSON body.
    raw = result.stdout
    start = next((i for i, ch in enumerate(raw) if ch in "{["), None)
    if start is None:
        return {}
    try:
        return json.loads(raw[start:])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gws returned unparseable output: {raw[start:][:300]}") from exc


def fetch_presentation(presentation_id):
    return run_gws(
        ["slides", "presentations", "get",
         "--params", json.dumps({"presentationId": presentation_id})]
    )


def _text_runs(node):
    """Yield every textRun content string nested anywhere under `node`."""
    if isinstance(node, dict):
        run = node.get("textRun")
        if isinstance(run, dict) and "content" in run:
            yield run["content"]
        for value in node.values():
            yield from _text_runs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _text_runs(item)


def slide_corpus(presentation, slide_numbers=None):
    """Return (body_text, notes_text), optionally for selected slides only."""
    body, notes = [], []
    for number, slide in enumerate(presentation.get("slides", []), 1):
        if slide_numbers and number not in slide_numbers:
            continue
        notes_page = slide.get("slideProperties", {}).get("notesPage", {})
        notes.extend(_text_runs(notes_page))
        body.extend(
            _text_runs({k: v for k, v in slide.items() if k != "slideProperties"})
        )
    return "".join(body), "".join(notes)


def slide_page_ids(presentation):
    return [s["objectId"] for s in presentation.get("slides", [])]


def slide_scope(edit):
    """Return the set of slide numbers a `find` edit is restricted to, or None."""
    scope = edit.get("slide")
    if scope is None:
        return None
    return set(scope) if isinstance(scope, list) else {scope}


def notes_body_shape(presentation, slide_number):
    """Return (objectId, current_text) for a slide's speaker-note body."""
    slides = presentation.get("slides", [])
    if not 1 <= slide_number <= len(slides):
        raise ValueError(
            f"slide {slide_number} out of range (deck has {len(slides)} slides)"
        )
    notes_page = slides[slide_number - 1].get("slideProperties", {}).get("notesPage", {})
    for element in notes_page.get("pageElements", []):
        placeholder = element.get("shape", {}).get("placeholder", {})
        if placeholder.get("type") == "BODY":
            return element["objectId"], "".join(_text_runs(element))
    raise ValueError(f"slide {slide_number} has no speaker-note body placeholder")


EMU_PER_INCH = 914400


def _walk_elements(elements):
    """Yield page elements, descending into groups."""
    for element in elements:
        yield element
        yield from _walk_elements(element.get("elementGroup", {}).get("children", []))


def find_element(presentation, object_id):
    """Return the page element with `object_id`, or None."""
    for slide in presentation.get("slides", []):
        for element in _walk_elements(slide.get("pageElements", [])):
            if element.get("objectId") == object_id:
                return element
    return None


def element_text(element, cell=None):
    """Return the `text` object of a shape, or of one table cell."""
    if element is None:
        return None
    if cell is None:
        return element.get("shape", {}).get("text")
    rows = element.get("table", {}).get("tableRows", [])
    try:
        return rows[cell[0]]["tableCells"][cell[1]].get("text", {})
    except (IndexError, KeyError):
        return None


def plain_text(text_obj):
    if not text_obj:
        return ""
    return "".join(_text_runs(text_obj))


def shape_font_sizes(presentation, object_id):
    """Return the set of fontSize magnitudes used by a shape's text runs."""
    element = find_element(presentation, object_id)
    sizes = set()
    for item in (element_text(element) or {}).get("textElements", []):
        run = item.get("textRun")
        if run:
            sizes.add(run.get("style", {}).get("fontSize", {}).get("magnitude"))
    return sizes


def shape_width_inches(presentation, object_id):
    """Return a shape's rendered width in inches, or None."""
    element = find_element(presentation, object_id)
    if element is None:
        return None
    width = element.get("size", {}).get("width", {}).get("magnitude", 0)
    return width * element.get("transform", {}).get("scaleX", 1) / EMU_PER_INCH


# --- setText markup -------------------------------------------------------

MARK_RE = re.compile(r"\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)\s]+)\)")


def parse_markup(text):
    """Return (plain, bold_ranges, link_ranges) with UTF-16 offsets."""
    plain, bold, links = [], [], []
    pos = 0  # UTF-16 offset into plain

    def u16(s):
        return len(s.encode("utf-16-le")) // 2

    last = 0
    for match in MARK_RE.finditer(text):
        before = text[last:match.start()]
        plain.append(before)
        pos += u16(before)
        if match.group(1) is not None:
            chunk = match.group(1)
            bold.append((pos, pos + u16(chunk)))
        else:
            chunk = match.group(2)
            links.append((pos, pos + u16(chunk), match.group(3)))
        plain.append(chunk)
        pos += u16(chunk)
        last = match.end()
    plain.append(text[last:])
    return "".join(plain), bold, links


STYLE_SKIP = {"link"}


def captured_styles(text_obj):
    """Return (base_style, bold_style, paragraph_style) from existing text."""
    runs = [e["textRun"] for e in (text_obj or {}).get("textElements", [])
            if "textRun" in e and e["textRun"].get("content", "").strip()]
    base = next((r.get("style", {}) for r in runs
                 if not r.get("style", {}).get("bold")), None)
    if base is None:
        base = runs[0].get("style", {}) if runs else {}
    bold = next((r.get("style", {}) for r in runs
                 if r.get("style", {}).get("bold")), None)
    base = {k: v for k, v in base.items() if k not in STYLE_SKIP}
    bold = dict(bold) if bold else dict(base)
    bold = {k: v for k, v in bold.items() if k not in STYLE_SKIP}
    bold["bold"] = True
    para = next((e["paragraphMarker"].get("style", {})
                 for e in (text_obj or {}).get("textElements", [])
                 if "paragraphMarker" in e), {})
    return base, bold, para


def set_text_requests(edit, presentation):
    object_id = edit["setText"]
    cell = edit.get("cell")
    element = find_element(presentation, object_id)
    text_obj = element_text(element, cell)
    style_source = text_obj
    if edit.get("styleFromCell"):
        style_source = element_text(element, edit["styleFromCell"])
    base, bold, para = captured_styles(style_source)
    plain, bold_ranges, link_ranges = parse_markup(edit["text"])
    loc = {"cellLocation": {"rowIndex": cell[0], "columnIndex": cell[1]}} if cell else {}

    def target(**kw):
        return {"objectId": object_id, **loc, **kw}

    requests = []
    if plain_text(text_obj).strip():
        requests.append({"deleteText": target(textRange={"type": "ALL"})})
    if not plain:
        return requests
    requests.append({"insertText": target(insertionIndex=0, text=plain)})
    if base:
        requests.append({"updateTextStyle": target(
            textRange={"type": "ALL"}, style=base, fields=",".join(base))})
    if not base.get("bold"):
        requests.append({"updateTextStyle": target(
            textRange={"type": "ALL"}, style={"bold": False}, fields="bold")})
    if para:
        requests.append({"updateParagraphStyle": target(
            textRange={"type": "ALL"}, style=para, fields=",".join(para))})
    for start, end in bold_ranges:
        requests.append({"updateTextStyle": target(
            textRange={"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            style=bold, fields=",".join(bold))})
    for start, end, url in link_ranges:
        requests.append({"updateTextStyle": target(
            textRange={"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            style={"link": {"url": url}}, fields="link")})
    return requests


# --- structure ------------------------------------------------------------

def resolve_slide(presentation, ref):
    """Return the objectId of a slide given its 1-indexed number or objectId."""
    ids = slide_page_ids(presentation)
    if isinstance(ref, int):
        if not 1 <= ref <= len(ids):
            raise ValueError(f"slide {ref} out of range (deck has {len(ids)} slides)")
        return ids[ref - 1]
    return ref


def structure_requests(edits, presentation):
    requests = []
    ids = slide_page_ids(presentation)
    for edit in edits:
        if "duplicateSlide" in edit:
            source = resolve_slide(presentation, edit["duplicateSlide"])
            req = {"objectId": source}
            if edit.get("newId"):
                req["objectIds"] = {source: edit["newId"]}
                ids.insert(ids.index(source) + 1, edit["newId"])
            else:
                ids.insert(ids.index(source) + 1, f"<copy of {source}>")
            requests.append({"duplicateObject": req})
        elif "deleteSlide" in edit:
            target = resolve_slide(presentation, edit["deleteSlide"])
            requests.append({"deleteObject": {"objectId": target}})
            ids.remove(target)
        elif "reorder" in edit:
            order = [resolve_slide(presentation, r) for r in edit["reorder"]]
            if sorted(order) != sorted(ids):
                missing = set(ids) - set(order)
                extra = set(order) - set(ids)
                raise ValueError(
                    f"reorder must list every slide once; missing {sorted(missing)}, "
                    f"unknown {sorted(extra)}"
                )
            current = list(ids)
            for index, object_id in enumerate(order):
                at = current.index(object_id)
                if at != index:
                    requests.append({"updateSlidesPosition": {
                        "slideObjectIds": [object_id], "insertionIndex": index}})
                    current.pop(at)
                    current.insert(index, object_id)
            ids = current
    return requests, ids


# --- content --------------------------------------------------------------

def preflight(edits, presentation, body, notes, allow_missing):
    """Report what each edit will do. Returns True when all are applicable."""
    ok = True
    print(f"{'#':>3}  {'kind':<7} {'hits':>4}  edit")
    print("-" * 72)
    for i, edit in enumerate(edits, 1):
        label = edit.get("note") or ""
        if "objectId" in edit:
            changes = []
            if "fontSize" in edit:
                changes.append(f"{edit['fontSize']}pt")
            if "widthInches" in edit:
                changes.append(f"{edit['widthInches']}in wide")
            label = label or f"{edit['objectId']} -> {', '.join(changes)}"
            flag = ""
            if find_element(presentation, edit["objectId"]) is None:
                flag = f"  <-- NO SHAPE {edit['objectId']}"
                ok = False
            print(f"{i:>3}  shape   {'':>4}  {label}{flag}")
            continue

        if "setText" in edit or "deleteElement" in edit:
            object_id = edit.get("setText") or edit.get("deleteElement")
            element = find_element(presentation, object_id)
            flag = ""
            if element is None:
                flag = f"  <-- NO ELEMENT {object_id}"
                ok = False
            elif "setText" in edit and element_text(element, edit.get("cell")) is None:
                flag = f"  <-- {object_id} has no text" + (
                    f" cell {edit['cell']}" if edit.get("cell") else "")
                ok = False
            kind = "settext" if "setText" in edit else "delete"
            print(f"{i:>3}  {kind:<7} {'':>4}  {label or object_id}{flag}")
            continue

        if "notesForSlide" in edit:
            try:
                _, current = notes_body_shape(presentation, edit["notesForSlide"])
            except ValueError as exc:
                print(f"{i:>3}  notes       ?  {label}  <-- {exc}")
                ok = False
                continue
            label = label or f"slide {edit['notesForSlide']} notes"
            status = "" if current.strip() else "  (notes currently empty)"
            print(f"{i:>3}  notes   {len(current):>4}  {label}{status}")
            continue

        find = edit["find"]
        scope = slide_scope(edit)
        scoped_body = slide_corpus(presentation, scope)[0] if scope else body
        hits = scoped_body.count(find)
        label = label or (find[:46] + ("…" if len(find) > 46 else ""))
        flag = ""
        if hits == 0:
            flag = "  <-- NO MATCH IN BODY" + (f" ON SLIDE(S) {sorted(scope)}" if scope else "")
            if notes.count(find):
                flag += f" (appears {notes.count(find)}x in notes, out of scope)"
            if not allow_missing:
                ok = False
        print(f"{i:>3}  body    {hits:>4}  {label}{flag}")
    return ok


def build_requests(edits, presentation):
    """Translate content edits into Slides API requests, preserving file order."""
    page_ids = slide_page_ids(presentation)
    requests = []
    for edit in edits:
        if "objectId" in edit:
            if "fontSize" in edit:
                requests.append(
                    {
                        "updateTextStyle": {
                            "objectId": edit["objectId"],
                            "textRange": {"type": "ALL"},
                            "style": {"fontSize": {"magnitude": edit["fontSize"],
                                                   "unit": "PT"}},
                            "fields": "fontSize",
                        }
                    }
                )
            if "widthInches" in edit:
                element = find_element(presentation, edit["objectId"])
                transform = dict(element.get("transform", {}))
                base = element.get("size", {}).get("width", {}).get("magnitude", 0)
                if not base:
                    raise ValueError(f"{edit['objectId']} has no base width to scale")
                transform["scaleX"] = edit["widthInches"] * EMU_PER_INCH / base
                requests.append(
                    {
                        "updatePageElementTransform": {
                            "objectId": edit["objectId"],
                            "applyMode": "ABSOLUTE",
                            "transform": transform,
                        }
                    }
                )
        elif "setText" in edit:
            requests.extend(set_text_requests(edit, presentation))
        elif "deleteElement" in edit:
            requests.append({"deleteObject": {"objectId": edit["deleteElement"]}})
        elif "notesForSlide" in edit:
            object_id, current = notes_body_shape(presentation, edit["notesForSlide"])
            if current.strip():
                requests.append(
                    {"deleteText": {"objectId": object_id,
                                    "textRange": {"type": "ALL"}}}
                )
            requests.append(
                {"insertText": {"objectId": object_id,
                                "insertionIndex": 0,
                                "text": edit["replace"]}}
            )
        else:
            scope = slide_scope(edit)
            pages = ([page_ids[n - 1] for n in sorted(scope)] if scope else page_ids)
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": edit["find"], "matchCase": True},
                        "replaceText": edit["replace"],
                        "pageObjectIds": pages,
                    }
                }
            )
    return requests


def verify_content(edits, after):
    """Return the edits that did not take effect."""
    body2, _ = slide_corpus(after)
    residual = []
    for e in edits:
        if "find" in e:
            scope = slide_scope(e)
            scoped = slide_corpus(after, scope)[0] if scope else body2
            if scoped.count(e["find"]) > 0 and e["find"] not in e["replace"]:
                residual.append(e)
        elif "notesForSlide" in e:
            _, now = notes_body_shape(after, e["notesForSlide"])
            if now.replace("\x0b", " ").strip() != e["replace"].strip():
                residual.append(e)
        elif "setText" in e:
            expected = parse_markup(e["text"])[0]
            now = plain_text(element_text(find_element(after, e["setText"]), e.get("cell")))
            if now.replace("\x0b", "\n").rstrip("\n") != expected.rstrip("\n"):
                residual.append(e)
        elif "deleteElement" in e:
            if find_element(after, e["deleteElement"]) is not None:
                residual.append(e)
        elif "objectId" in e:
            if "fontSize" in e and shape_font_sizes(after, e["objectId"]) != {e["fontSize"]}:
                residual.append(e)
            elif "widthInches" in e and abs(
                (shape_width_inches(after, e["objectId"]) or 0) - e["widthInches"]
            ) > 0.01:
                residual.append(e)
    return residual


def load_edits(path):
    try:
        edits = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read edits file {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(edits, list):
        print("ERROR: edits file must contain a JSON array", file=sys.stderr)
        sys.exit(2)
    seen_structure = seen_content = False
    for i, edit in enumerate(edits, 1):
        if not isinstance(edit, dict):
            print(f"ERROR: edit {i} must be an object", file=sys.stderr)
            sys.exit(2)
        kinds = [k for k in CONTENT_KINDS + STRUCTURE_KINDS if k in edit]
        if len(kinds) != 1:
            print(f"ERROR: edit {i} needs exactly one of "
                  f"{', '.join(CONTENT_KINDS + STRUCTURE_KINDS)}", file=sys.stderr)
            sys.exit(2)
        kind = kinds[0]
        if kind in STRUCTURE_KINDS:
            seen_structure = True
        else:
            seen_content = True
        if kind == "objectId" and not {"fontSize", "widthInches"} & set(edit):
            print(f"ERROR: edit {i} needs 'fontSize' and/or 'widthInches'",
                  file=sys.stderr)
            sys.exit(2)
        if kind in ("find", "notesForSlide") and "replace" not in edit:
            print(f"ERROR: edit {i} needs a 'replace' field", file=sys.stderr)
            sys.exit(2)
        if kind == "duplicateSlide" and edit.get("newId") and not re.fullmatch(
                r"[A-Za-z0-9_][A-Za-z0-9_:-]{4,49}", edit["newId"]):
            print(f"ERROR: edit {i} newId must be 5-50 characters of letters, digits, "
                  "'_', '-' or ':' (a Slides API rule)", file=sys.stderr)
            sys.exit(2)
        if kind == "setText" and "text" not in edit:
            print(f"ERROR: edit {i} needs a 'text' field", file=sys.stderr)
            sys.exit(2)
    if seen_structure and seen_content:
        print("ERROR: structure edits (duplicateSlide, deleteSlide, reorder) renumber "
              "slides; put them in a separate edits file from content edits",
              file=sys.stderr)
        sys.exit(2)
    return edits, seen_structure


def parse_slide_list(spec, total):
    numbers = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            numbers.update(range(int(lo), (int(hi) if hi else total) + 1))
        elif part:
            numbers.add(int(part))
    return sorted(n for n in numbers if 1 <= n <= total)


def print_shapes(presentation, spec):
    slides = presentation.get("slides", [])
    for number in parse_slide_list(spec, len(slides)):
        slide = slides[number - 1]
        print(f"=== slide {number}  [{slide['objectId']}] ===")
        for element in _walk_elements(slide.get("pageElements", [])):
            oid = element.get("objectId")
            if "table" in element:
                rows = element["table"].get("tableRows", [])
                print(f"  {oid}  table {len(rows)}x{element['table'].get('columns')}")
                for r, row in enumerate(rows):
                    cells = [plain_text(c.get("text")).strip().replace("\n", " / ")
                             for c in row.get("tableCells", [])]
                    print(f"      r{r}: " + " | ".join(cells))
                continue
            text = plain_text(element_text(element)).strip()
            if not text:
                continue
            runs = [e["textRun"] for e in element_text(element).get("textElements", [])
                    if "textRun" in e and e["textRun"].get("content", "").strip()]
            size = runs[0].get("style", {}).get("fontSize", {}).get("magnitude") if runs else None
            bold = any(r.get("style", {}).get("bold") for r in runs)
            flat = text.replace("\n", " / ").replace("\x0b", " / ")
            print(f"  {oid}  [{size}pt{' +bold' if bold else ''}]  {flat[:150]}")
        try:
            _, notes = notes_body_shape(presentation, number)
            print(f"  notes: {len(notes.strip())} chars")
        except ValueError:
            print("  notes: (no notes body)")


def main():
    parser = argparse.ArgumentParser(
        description="Apply edits to a Google Slides deck in place."
    )
    parser.add_argument("presentation_id", help="Google Slides presentation ID")
    parser.add_argument("--edits", help="JSON file of edits")
    parser.add_argument("--shapes", metavar="SLIDES",
                        help="list shapes on these slides (e.g. '4,7-9' or '1-') and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="report match counts and exit without writing")
    parser.add_argument("--allow-missing", action="store_true",
                        help="do not fail when an edit matches nothing")
    parser.add_argument("--rename", metavar="TITLE",
                        help="also rename the Drive file to TITLE")
    args = parser.parse_args()

    if not args.edits and not args.shapes:
        parser.error("one of --edits or --shapes is required")

    print(f"Fetching presentation {args.presentation_id} ...")
    presentation = fetch_presentation(args.presentation_id)

    if args.shapes:
        print_shapes(presentation, args.shapes)
        return

    edits, is_structure = load_edits(args.edits)
    body, notes = slide_corpus(presentation)
    print(f"Title: {presentation.get('title', '?')}")
    print(f"Slides: {len(presentation.get('slides', []))}  "
          f"body chars: {len(body)}  notes chars: {len(notes)}\n")

    if is_structure:
        try:
            requests, final_ids = structure_requests(edits, presentation)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        for i, edit in enumerate(edits, 1):
            print(f"{i:>3}  {edit.get('note') or json.dumps(edit)[:70]}")
        print(f"\nResulting order ({len(final_ids)} slides): {final_ids}")
    else:
        if not preflight(edits, presentation, body, notes, args.allow_missing):
            print("\nERROR: one or more edits cannot apply. Fix them or pass "
                  "--allow-missing for unmatched 'find' strings.", file=sys.stderr)
            sys.exit(1)
        requests = build_requests(edits, presentation)

    if args.dry_run:
        print(f"\nDry run: {len(edits)} edit(s), {len(requests)} request(s). Nothing written.")
        return

    print(f"\nApplying {len(edits)} edit(s) as {len(requests)} request(s) ...")
    if requests:
        result = run_gws(
            ["slides", "presentations", "batchUpdate",
             "--params", json.dumps({"presentationId": args.presentation_id}),
             "--json", json.dumps({"requests": requests})]
        )
        changed = sum(
            r.get("replaceAllText", {}).get("occurrencesChanged", 0)
            for r in result.get("replies", [])
        )
        if changed:
            print(f"Occurrences changed: {changed}")

    if args.rename:
        run_gws(
            ["drive", "files", "update",
             "--params", json.dumps({"fileId": args.presentation_id, "fields": "id,name"}),
             "--json", json.dumps({"name": args.rename})]
        )
        print(f"Renamed to: {args.rename}")

    print("\nVerifying ...")
    after = fetch_presentation(args.presentation_id)
    if is_structure:
        now = slide_page_ids(after)
        expected = [i for i in final_ids if not i.startswith("<copy of")]
        if len(now) != len(final_ids) or [i for i in now if i in expected] != expected:
            print(f"WARNING: slide order differs from expected.\n  now: {now}",
                  file=sys.stderr)
            sys.exit(1)
        print(f"Structure verified: {len(now)} slides.")
        return
    residual = verify_content(edits, after)
    if residual:
        print(f"WARNING: {len(residual)} edit(s) did not take effect:", file=sys.stderr)
        for e in residual:
            label = (e.get("note") or e.get("find", "")[:60] or e.get("setText")
                     or e.get("objectId", ""))
            print(f"  - {label}", file=sys.stderr)
        sys.exit(1)
    print("All edits verified applied.")


if __name__ == "__main__":
    main()
