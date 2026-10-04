#!/usr/bin/env python3
"""Apply find/replace edits to a Google Slides presentation via the gws CLI.

Edits slide body copy and speaker notes in place, preserving all layout,
theme and formatting. Intended for copy passes over an already-published
deck (style fixes, terminology changes, citation relabelling) where
regenerating from source is not available or not wanted.

Every edit is verified before and after the write:

  * Pre-flight counts each `find` string across body text and notes text.
    A string that matches nothing is an error by default, because a silent
    no-op edit is the common failure mode of a bulk copy pass.
  * Post-flight re-fetches the deck and reports any `find` string that
    survived, which catches ordering collisions between edits.

Usage:
    # Report what would change, write nothing
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json --dry-run

    # Apply the edits
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json

    # Apply and rename the Drive file
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json \
        --rename "Coordinating updates across a multi-vendor OpenShift stack"

    # Tolerate edits that match nothing (e.g. re-running a partly applied set)
    python3 utils/edit-gws-slides.py <presentation-id> --edits edits.json --allow-missing

Edits file format — a JSON array, applied in order, with three edit forms:

    [
      {"find": "old text", "replace": "new text", "note": "slide 1 title"},
      {"notesForSlide": 11, "replace": "full replacement notes", "note": "slide 11"},
      {"objectId": "p1_i5", "fontSize": 44, "note": "shrink title to fit"},
      {"objectId": "p6_i13", "widthInches": 8.8, "note": "widen citation band"}
    ]

`find` edits do a case-sensitive replace across slide body copy only; speaker
notes are deliberately out of scope so a body edit cannot silently rewrite a
note. `notesForSlide` replaces a slide's entire speaker-note body (1-indexed).
`objectId` edits reshape one element and take `fontSize`, `widthInches`, or
both — the two remedies for copy that no longer fits the box an export sized
around the old wording. Widening only changes the element's horizontal scale;
position, height and vertical scale are preserved.

Replacing whole notes rather than fragments is the right default: exported
decks carry vertical-tab soft line breaks mid-sentence, so a fragment that
looks contiguous on screen often will not match.

Exit codes: 0 success, 1 pre-flight or post-flight failure, 2 bad input.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

GWS_PATH = "/opt/homebrew/bin/gws"
TIMEOUT = 120


def run_gws(args, parse=True):
    """Invoke the gws CLI and return parsed JSON, stripping its stdout preamble."""
    result = subprocess.run(
        [GWS_PATH, *args], capture_output=True, text=True, timeout=TIMEOUT
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"gws {' '.join(args[:3])} failed: {detail[:500]}")
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


def slide_corpus(presentation):
    """Return (body_text, notes_text) for the whole presentation."""
    body, notes = [], []
    for slide in presentation.get("slides", []):
        notes_page = slide.get("slideProperties", {}).get("notesPage", {})
        notes.extend(_text_runs(notes_page))
        body.extend(
            _text_runs({k: v for k, v in slide.items() if k != "slideProperties"})
        )
    return "".join(body), "".join(notes)


def slide_page_ids(presentation):
    return [s["objectId"] for s in presentation.get("slides", [])]


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


def find_element(presentation, object_id):
    """Return the page element with `object_id`, or None."""
    for slide in presentation.get("slides", []):
        for element in slide.get("pageElements", []):
            if element.get("objectId") == object_id:
                return element
    return None


def shape_font_sizes(presentation, object_id):
    """Return the set of fontSize magnitudes used by a shape's text runs."""
    element = find_element(presentation, object_id)
    if element is None:
        return set()
    sizes = set()
    for item in element.get("shape", {}).get("text", {}).get("textElements", []):
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


def preflight(edits, presentation, body, notes, allow_missing):
    """Report what each edit will do. Returns True when all are applicable."""
    ok = True
    print(f"{'#':>3}  {'kind':<6} {'hits':>4}  edit")
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
            print(f"{i:>3}  shape  {'':>4}  {label}{flag}")
            continue

        if "notesForSlide" in edit:
            try:
                _, current = notes_body_shape(presentation, edit["notesForSlide"])
            except ValueError as exc:
                print(f"{i:>3}  notes      ?  {label}  <-- {exc}")
                ok = False
                continue
            label = label or f"slide {edit['notesForSlide']} notes"
            status = "" if current.strip() else "  <-- notes currently empty"
            print(f"{i:>3}  notes  {len(current):>4}  {label}{status}")
            continue

        find = edit["find"]
        hits = body.count(find)
        label = label or (find[:46] + ("…" if len(find) > 46 else ""))
        flag = ""
        if hits == 0:
            flag = "  <-- NO MATCH IN BODY"
            if notes.count(find):
                flag += f" (appears {notes.count(find)}x in notes, out of scope)"
            if not allow_missing:
                ok = False
        print(f"{i:>3}  body   {hits:>4}  {label}{flag}")
    return ok


def build_requests(edits, presentation):
    """Translate edits into Slides API requests, preserving file order."""
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
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": edit["find"], "matchCase": True},
                        "replaceText": edit["replace"],
                        "pageObjectIds": page_ids,
                    }
                }
            )
    return requests


def load_edits(path):
    try:
        edits = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read edits file {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(edits, list):
        print("ERROR: edits file must contain a JSON array", file=sys.stderr)
        sys.exit(2)
    for i, edit in enumerate(edits, 1):
        if not isinstance(edit, dict):
            print(f"ERROR: edit {i} must be an object", file=sys.stderr)
            sys.exit(2)
        kinds = [k for k in ("find", "notesForSlide", "objectId") if k in edit]
        if len(kinds) != 1:
            print(f"ERROR: edit {i} needs exactly one of 'find', 'notesForSlide' "
                  "or 'objectId'", file=sys.stderr)
            sys.exit(2)
        if kinds[0] == "objectId":
            if not {"fontSize", "widthInches"} & set(edit):
                print(f"ERROR: edit {i} needs 'fontSize' and/or 'widthInches'",
                      file=sys.stderr)
                sys.exit(2)
        elif "replace" not in edit:
            print(f"ERROR: edit {i} needs a 'replace' field", file=sys.stderr)
            sys.exit(2)
    return edits


def main():
    parser = argparse.ArgumentParser(
        description="Apply find/replace edits to a Google Slides deck in place."
    )
    parser.add_argument("presentation_id", help="Google Slides presentation ID")
    parser.add_argument("--edits", required=True, help="JSON file of edits")
    parser.add_argument("--dry-run", action="store_true",
                        help="report match counts and exit without writing")
    parser.add_argument("--allow-missing", action="store_true",
                        help="do not fail when an edit matches nothing")
    parser.add_argument("--rename", metavar="TITLE",
                        help="also rename the Drive file to TITLE")
    args = parser.parse_args()

    edits = load_edits(args.edits)

    print(f"Fetching presentation {args.presentation_id} ...")
    presentation = fetch_presentation(args.presentation_id)
    body, notes = slide_corpus(presentation)
    print(f"Title: {presentation.get('title', '?')}")
    print(f"Slides: {len(presentation.get('slides', []))}  "
          f"body chars: {len(body)}  notes chars: {len(notes)}\n")

    if not preflight(edits, presentation, body, notes, args.allow_missing):
        print("\nERROR: one or more edits matched nothing. Fix the 'find' strings "
              "or pass --allow-missing.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"\nDry run: {len(edits)} edit(s) would be applied. Nothing written.")
        return

    print(f"\nApplying {len(edits)} edit(s) ...")
    result = run_gws(
        ["slides", "presentations", "batchUpdate",
         "--params", json.dumps({"presentationId": args.presentation_id}),
         "--json", json.dumps({"requests": build_requests(edits, presentation)})]
    )
    changed = sum(
        r.get("replaceAllText", {}).get("occurrencesChanged", 0)
        for r in result.get("replies", [])
    )
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
    body2, notes2 = slide_corpus(after)
    residual = [
        e for e in edits
        if "find" in e
        and body2.count(e["find"]) > 0
        and e["find"] not in e["replace"]
    ]
    for e in edits:
        if "notesForSlide" in e:
            _, now = notes_body_shape(after, e["notesForSlide"])
            if now.replace("\x0b", " ").strip() != e["replace"].strip():
                residual.append(e)
        elif "objectId" in e:
            if "fontSize" in e and shape_font_sizes(after, e["objectId"]) != {e["fontSize"]}:
                residual.append(e)
            elif "widthInches" in e and abs(
                (shape_width_inches(after, e["objectId"]) or 0) - e["widthInches"]
            ) > 0.01:
                residual.append(e)
    if residual:
        print(f"WARNING: {len(residual)} edit(s) did not take effect:", file=sys.stderr)
        for e in residual:
            label = e.get("note") or e.get("find", "")[:60] or e.get("objectId", "")
            print(f"  - {label}", file=sys.stderr)
        sys.exit(1)
    print("All edits verified applied.")


if __name__ == "__main__":
    main()
