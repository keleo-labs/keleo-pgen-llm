#!/usr/bin/env python3
"""Rasterise report diagrams to PNG so they can be eyeballed for defects.

`render-diagram.py` emits SVG, but a rendered SVG can still be wrong in ways
only visible as pixels: labels clipped to an ellipsis, edge labels colliding,
cluster rects overlapping. The reporting skills are told to check their
diagrams; this is what they check them with.

macOS `qlmanage -t` is not a substitute. It fits to width on a square canvas,
so a tall diagram is silently cropped — the bottom half of a topology simply
is not in the thumbnail, and a broken diagram reads as a clean one.

This sizes each raster from the SVG's own viewBox, so the whole diagram is in
frame at a legible scale whatever its aspect.

Usage:
    python3 utils/preview-diagram.py <diagram>.svg
    python3 utils/preview-diagram.py --dir reports/assets/<report-slug>/
    python3 utils/preview-diagram.py --report reports/<name>.md
    python3 utils/preview-diagram.py --dir <dir> -o /tmp/previews --width 1200

Writes <name>.png beside the SVG unless -o names an output directory.
Requires a Chromium build: Playwright's bundled chrome-headless-shell, a
`chromium`/`chrome` on PATH, or Google Chrome on macOS. Install one with
`python3 -m playwright install chromium` or your platform's package manager.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / ".claude" / "skills" / "diagram-foundation" / "scripts"
sys.path.insert(0, str(ENGINE))

try:
    from diagram import svg_aspect
except ImportError:
    print(f"Error: diagram engine missing at {ENGINE}\n"
          f"Re-copy it from ~/.claude/skills/diagram-foundation/",
          file=sys.stderr)
    sys.exit(1)

# Markdown image embeds pointing at an SVG, e.g. ![alt](assets/slug/x.svg)
EMBED = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")


def find_browser():
    """Path to a Chromium-family binary, or None."""
    cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    if not cache.is_dir():
        cache = Path.home() / ".cache" / "ms-playwright"
    if cache.is_dir():
        for pattern in ("chromium_headless_shell-*/*/chrome-headless-shell",
                        "chromium-*/chrome-linux/chrome",
                        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"):
            found = sorted(cache.glob(pattern))
            if found:
                return str(found[-1])

    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        path = shutil.which(name)
        if path:
            return path

    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    return str(mac_chrome) if mac_chrome.exists() else None


# Loaded directly, an SVG renders at its intrinsic px size and sits in the
# corner of a larger window. Wrapping it in a page that stretches it to the
# viewport is what makes the raster fill the frame.
WRAPPER = """<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;background:#fff}}
img{{display:block;width:100vw;height:auto}}</style>
<img src="{src}">
"""


def shoot(browser, svg, png, width):
    """Screenshot one SVG at `width` px, height derived from its aspect."""
    height = max(1, round(width * svg_aspect(svg)))
    with tempfile.TemporaryDirectory() as work:
        page = Path(work) / "page.html"
        page.write_text(WRAPPER.format(src=svg.resolve().as_uri()),
                        encoding="utf-8")
        result = subprocess.run(
            [browser, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--user-data-dir={work}/profile",
             "--allow-file-access-from-files",
             "--default-background-color=FFFFFFFF",
             f"--window-size={width},{height}",
             f"--screenshot={png}", page.as_uri()],
            capture_output=True, text=True, timeout=120)
    if not png.exists():
        tail = (result.stderr or result.stdout or "").strip().splitlines()
        raise RuntimeError(tail[-1] if tail else "screenshot produced no file")
    return width, height


def collect(args):
    """Resolve the argument forms into a list of SVG paths."""
    if args.report:
        report = Path(args.report)
        text = report.read_text(encoding="utf-8")
        found = []
        for target in EMBED.findall(text):
            if target.startswith(("http://", "https://")):
                continue
            svg = (report.parent / target).resolve()
            if svg not in found:
                found.append(svg)
        return found
    if args.dir:
        return sorted(Path(args.dir).glob("*.svg"))
    return [Path(args.svg)]


def main():
    parser = argparse.ArgumentParser(
        description="Rasterise report diagrams to PNG for visual checking")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("svg", nargs="?", help="Path to a single .svg")
    source.add_argument("--dir", help="Rasterise every .svg in a directory")
    source.add_argument("--report", help="Rasterise every .svg a report embeds")
    parser.add_argument("-o", "--output-dir",
                        help="Write PNGs here (default: beside each SVG)")
    parser.add_argument("--width", type=int, default=1100,
                        help="Raster width in px (default: 1100)")
    args = parser.parse_args()

    browser = find_browser()
    if not browser:
        print("Error: no Chromium-family browser found.\n"
              "Install one with `python3 -m playwright install chromium`, or\n"
              "  Debian/Ubuntu: sudo apt install chromium\n"
              "  Fedora/RHEL:   sudo dnf install chromium\n"
              "  Arch:          sudo pacman -S chromium\n"
              "  macOS:         Google Chrome, or the Playwright command above",
              file=sys.stderr)
        return 1

    svgs = collect(args)
    if not svgs:
        print("No SVGs found for that input", file=sys.stderr)
        return 1

    out_dir = Path(args.output_dir) if args.output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for svg in svgs:
        if not svg.exists():
            print(f"missing  {svg}", file=sys.stderr)
            failures += 1
            continue
        png = (out_dir / f"{svg.stem}.png") if out_dir else svg.with_suffix(".png")
        try:
            width, height = shoot(browser, svg, png, args.width)
        except Exception as exc:
            print(f"failed   {svg.name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        print(f"previewed {png}  ({width}x{height})")

    if failures:
        print(f"\n{failures} diagram(s) could not be rasterised", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
