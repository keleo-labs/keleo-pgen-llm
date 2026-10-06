#!/usr/bin/env python3
"""Render slides of a Google Slides presentation to PNG for visual review.

Google Slides lays text out slightly wider than a local Slidev/Chromium
render, so overflow and collision defects only show up on the published
deck. This downloads thumbnails of chosen slides so they can be looked at
directly.

Usage:
    # Render specific slides (1-indexed)
    python3 utils/render-gws-slides.py <presentation-id> --slides 1,19,23 -o .tmp

    # Render a range, and everything after a point
    python3 utils/render-gws-slides.py <presentation-id> --slides 1-6,30- -o .tmp

    # Render the whole deck
    python3 utils/render-gws-slides.py <presentation-id> --all -o .tmp

Output files are named `<prefix>-<n>.png` (default prefix `slide`).

Exit codes: 0 success, 1 render failure, 2 bad input.
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from _shared import GWS as GWS_PATH
TIMEOUT = 120
SIZES = {"small": "SMALL", "medium": "MEDIUM", "large": "LARGE"}


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


def parse_slides(spec, total):
    """Expand a spec like '1,4-6,30-' into a sorted list of slide numbers."""
    wanted = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            start = int(lo) if lo else 1
            end = int(hi) if hi else total
        else:
            start = end = int(part)
        wanted.update(range(start, end + 1))
    out = sorted(n for n in wanted if 1 <= n <= total)
    if not out:
        raise ValueError(f"no slides in range 1-{total} matched {spec!r}")
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Render Google Slides pages to PNG for visual review."
    )
    parser.add_argument("presentation_id", help="Google Slides presentation ID")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slides", help="slide numbers, e.g. '1,4-6,30-' (1-indexed)")
    group.add_argument("--all", action="store_true", help="render every slide")
    parser.add_argument("-o", "--output-dir", default=".",
                        help="directory for the PNGs")
    parser.add_argument("--prefix", default="slide", help="output filename prefix")
    parser.add_argument("--size", default="large", choices=sorted(SIZES),
                        help="thumbnail size (default: large)")
    args = parser.parse_args()

    presentation = run_gws(
        ["slides", "presentations", "get",
         "--params", json.dumps({"presentationId": args.presentation_id,
                                 "fields": "slides.objectId"})]
    )
    page_ids = [s["objectId"] for s in presentation.get("slides", [])]
    if not page_ids:
        print("ERROR: presentation has no slides", file=sys.stderr)
        sys.exit(1)

    try:
        numbers = (list(range(1, len(page_ids) + 1)) if args.all
                   else parse_slides(args.slides, len(page_ids)))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for n in numbers:
        path = out_dir / f"{args.prefix}-{n}.png"
        # getThumbnail returns a short-lived contentUrl, not image bytes.
        thumbnail = run_gws(
            ["slides", "presentations", "pages", "getThumbnail",
             "--params", json.dumps({
                 "presentationId": args.presentation_id,
                 "pageObjectId": page_ids[n - 1],
                 "thumbnailProperties.mimeType": "PNG",
                 "thumbnailProperties.thumbnailSize": SIZES[args.size],
             })]
        )
        url = thumbnail.get("contentUrl")
        if not url:
            print(f"ERROR: no contentUrl for slide {n}: {thumbnail}", file=sys.stderr)
            sys.exit(1)
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            path.write_bytes(response.read())
        print(f"slide {n:>3}  ->  {path}  ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
