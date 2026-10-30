#!/usr/bin/env python3
"""Render a Google Slides deck to local PNGs for visual review.

Text that fits in a spec can still overflow, collide or sit off-grid once the
deck is built. Thumbnails close that loop: generate images, look at them, fix
the spec, re-render. This is the only check that catches layout faults, since
the API reports success for text that visibly overruns its box.

Usage:
    review-deck.py <presentation-id-or-url> [--out DIR] [--slides 1,3,5]
    review-deck.py <id> --size LARGE --out /tmp/review

Exit codes: 0 ok, 1 runtime failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gwsclient import GwsError, get_presentation, get_thumbnail  # noqa: E402

SIZES = ("SMALL", "MEDIUM", "LARGE")


def parse_presentation_id(value: str) -> str:
    match = re.search(r"/presentation/d/([a-zA-Z0-9_-]+)", value)
    return match.group(1) if match else value


def parse_selection(value: str | None, total: int) -> list[int]:
    """Turn '1,3,5-7' into zero-based indices, defaulting to every slide."""
    if not value:
        return list(range(total))
    picked: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, _, end = part.partition("-")
            picked.update(range(int(start) - 1, int(end)))
        else:
            picked.add(int(part) - 1)
    return sorted(i for i in picked if 0 <= i < total)


def download(url: str, dest: Path) -> int:
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    dest.write_bytes(data)
    return len(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="presentation ID or Slides URL")
    parser.add_argument("--out", type=Path, default=Path("/tmp/deck-review"))
    parser.add_argument("--size", choices=SIZES, default="LARGE")
    parser.add_argument("--slides", help="1-based selection, e.g. 1,3,5-7")
    args = parser.parse_args()

    presentation_id = parse_presentation_id(args.source)

    try:
        data = get_presentation(presentation_id, "title,slides(objectId)")
    except GwsError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    slides = data.get("slides", [])
    if not slides:
        sys.stderr.write("presentation has no slides\n")
        return 1

    indices = parse_selection(args.slides, len(slides))
    if not indices:
        sys.stderr.write("slide selection matched nothing\n")
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{data.get('title')} — rendering {len(indices)} of {len(slides)} slides")

    written = []
    for i in indices:
        object_id = slides[i]["objectId"]
        try:
            url = get_thumbnail(presentation_id, object_id, args.size)
            if not url:
                sys.stderr.write(f"  slide {i + 1}: no thumbnail URL returned\n")
                continue
            dest = args.out / f"slide-{i + 1:02d}.png"
            size = download(url, dest)
            written.append(dest)
            print(f"  slide {i + 1:>2}  {dest}  ({size // 1024}KB)")
        except (GwsError, OSError) as exc:
            sys.stderr.write(f"  slide {i + 1}: {exc}\n")

    if not written:
        return 1
    print(f"\n{len(written)} image(s) in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
