#!/usr/bin/env python3
"""Flag Google Slides text that probably collides with the element below it.

A copy pass over an exported deck is the usual way a layout breaks: the
exporter sized every box around the original wording, so longer replacement
text wraps to an extra line. Google Slides does not clip, so the extra line
renders outside the box — harmless over whitespace, a defect when something
sits underneath.

So the check is collision, not box fit. For each text shape it estimates the
rendered height at the shape's own font size and width, then compares the
resulting bottom edge against the top of the nearest element below it that
overlaps horizontally, and against the bottom of the slide.

The estimate uses an average glyph advance, so it is a triage tool, not a
layout engine. Treat the output as the shortlist of slides worth rendering
with `render-gws-slides.py` and looking at.

Two limitations worth knowing. Text that wraps into empty space is not
flagged, even though an extra line can still break a design grid — a
one-line citation band becoming two is invisible to this check. And box
fit deliberately is not tested: pptx export sizes boxes tighter than one
line of their own text, so almost every shape would flag. Visual review
of the published deck is still the thing that catches layout defects.

Usage:
    python3 utils/check-gws-slides-fit.py <presentation-id>
    python3 utils/check-gws-slides-fit.py <presentation-id> --all
    python3 utils/check-gws-slides-fit.py <presentation-id> --advance 0.55

Exit codes: 0 nothing flagged, 1 at least one shape flagged, 2 bad input.
"""

import argparse
import json
import subprocess
import sys

from _shared import GWS as GWS_PATH
TIMEOUT = 120
EMU_PER_INCH = 914400
POINTS_PER_INCH = 72
# Average glyph advance as a fraction of the font size. Red Hat Text sits
# near 0.50 for mixed-case prose; 0.52 leaves a little headroom without
# flagging every box.
DEFAULT_ADVANCE = 0.52
DEFAULT_LINE_HEIGHT = 1.2


def run_gws(args):
    result = subprocess.run(
        [GWS_PATH, *args], capture_output=True, text=True, timeout=TIMEOUT
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"gws {' '.join(args[:3])} failed: {detail[:500]}")
    raw = result.stdout
    start = next((i for i, ch in enumerate(raw) if ch in "{["), None)
    return json.loads(raw[start:]) if start is not None else {}


def paragraphs(shape):
    """Split a shape's text into (text, font_size) pairs, one per paragraph."""
    out, current, size = [], [], None
    for item in shape.get("text", {}).get("textElements", []):
        if "paragraphMarker" in item and current:
            out.append(("".join(current), size))
            current, size = [], None
        run = item.get("textRun")
        if run:
            current.append(run.get("content", ""))
            size = size or run.get("style", {}).get("fontSize", {}).get("magnitude")
    if current:
        out.append(("".join(current), size))
    return [(t, s) for t, s in out if t.strip()]


def needed_lines(text, font_size, width_inches, advance):
    """Greedy word wrap at an estimated glyph advance."""
    limit = width_inches * POINTS_PER_INCH / (font_size * advance)
    if limit < 1:
        return len(text)
    # Soft line breaks from pptx import arrive as vertical tabs. A trailing
    # newline terminates the paragraph rather than starting another line.
    segments = text.replace("\x0b", "\n").rstrip("\n").split("\n")
    lines, current = 1, 0
    for index, segment in enumerate(segments):
        if index:
            lines += 1
            current = 0
        for word in segment.split():
            step = len(word) + (1 if current else 0)
            if current + step > limit and current:
                lines += 1
                current = len(word)
            else:
                current += step
    return lines


def box(element):
    """Return (left, top, width, height) in inches."""
    transform = element.get("transform", {})
    size = element.get("size", {})
    return (
        transform.get("translateX", 0) / EMU_PER_INCH,
        transform.get("translateY", 0) / EMU_PER_INCH,
        size.get("width", {}).get("magnitude", 0)
        * transform.get("scaleX", 1) / EMU_PER_INCH,
        size.get("height", {}).get("magnitude", 0)
        * transform.get("scaleY", 1) / EMU_PER_INCH,
    )


def rendered_height(shape, width, advance, line_height):
    """Estimate how tall a shape's text renders, in inches."""
    total = 0.0
    for paragraph, font_size in paragraphs(shape):
        font_size = font_size or 14
        lines = needed_lines(paragraph, font_size, width, advance)
        total += lines * font_size * line_height / POINTS_PER_INCH
    return total


def obstruction_top(element, siblings):
    """Top edge of the nearest element below `element` that overlaps it in x."""
    left, top, width, _ = box(element)
    best = None
    for other in siblings:
        if other is element:
            continue
        o_left, o_top, o_width, o_height = box(other)
        # Full-bleed panels sit behind everything, so they never collide.
        if o_top <= top + 0.05 or o_height > 4:
            continue
        if o_left >= left + width or o_left + o_width <= left:
            continue
        if best is None or o_top < best:
            best = o_top
    return best


def inspect(presentation, advance, line_height):
    """Yield (slide, object_id, bottom, limit, reason, text) per text shape."""
    page_height = (presentation.get("pageSize", {})
                   .get("height", {}).get("magnitude", 0) / EMU_PER_INCH)
    for number, slide in enumerate(presentation.get("slides", []), 1):
        siblings = slide.get("pageElements", [])
        for element in siblings:
            shape = element.get("shape")
            if not shape or not paragraphs(shape):
                continue
            left, top, width, _ = box(element)
            if width <= 0:
                continue
            bottom = top + rendered_height(shape, width, advance, line_height)
            limit, reason = page_height, "runs off the slide"
            neighbour = obstruction_top(element, siblings)
            if neighbour is not None and neighbour < limit:
                limit, reason = neighbour, "overlaps the element below"
            text = " / ".join(p.strip() for p, _ in paragraphs(shape))
            yield number, element["objectId"], bottom, limit, reason, text


def main():
    parser = argparse.ArgumentParser(
        description="Flag Google Slides text boxes whose copy likely overflows."
    )
    parser.add_argument("presentation_id", help="Google Slides presentation ID")
    parser.add_argument("--all", action="store_true",
                        help="report every text shape, not just the flagged ones")
    parser.add_argument("--advance", type=float, default=DEFAULT_ADVANCE,
                        help=f"average glyph advance in em (default {DEFAULT_ADVANCE})")
    parser.add_argument("--line-height", type=float, default=DEFAULT_LINE_HEIGHT,
                        help=f"line height multiple (default {DEFAULT_LINE_HEIGHT})")
    parser.add_argument("--tolerance", type=float, default=0.1,
                        help="inches of overlap to allow before flagging")
    args = parser.parse_args()

    presentation = run_gws(
        ["slides", "presentations", "get",
         "--params", json.dumps({"presentationId": args.presentation_id})]
    )

    flagged = set()
    print(f"{'slide':>5}  {'shape':<10} {'bottom':>6} {'limit':>6}  text")
    print("-" * 100)
    for number, object_id, bottom, limit, reason, text in inspect(
        presentation, args.advance, args.line_height
    ):
        clash = bottom > limit + args.tolerance
        if clash:
            flagged.add(number)
        elif not args.all:
            continue
        mark = f"  <-- {reason}" if clash else ""
        print(f"{number:>5}  {object_id:<10} {bottom:>6.2f} {limit:>6.2f}  "
              f"{text[:52]!r}{mark}")

    if flagged:
        print(f"\n{len(flagged)} slide(s) flagged: "
              f"{','.join(str(n) for n in sorted(flagged))}")
        print("Render them and look: "
              f"python3 utils/render-gws-slides.py {args.presentation_id} "
              f"--slides {','.join(str(n) for n in sorted(flagged))} -o .tmp")
    else:
        print("\nNothing flagged.")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
