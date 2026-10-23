"""Run mermaid-cli over a source string and hand back the SVG.

Shared by both Mermaid routes: the one that reads the geometry back and
redraws it in house shapes, and the one that keeps the picture and themes it.

mermaid-cli is fetched on demand through `npx` rather than installed, which is
the same arrangement `google-doc` uses for sharp-cli. The major version is
pinned: an unpinned fetch would silently move the class names and element ids
that `mermaid_import` reads geometry out of.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from house_css import mermaid_config

PACKAGE = "@mermaid-js/mermaid-cli@12"

# The SVG element id, which prefixes every node, cluster and edge id Mermaid
# emits. Fixed here so mermaid_import can rely on it.
SVG_ID = "dg"

# First-run fetches the package, which is slow on a cold npx cache.
TIMEOUT = 180


class MermaidUnavailable(RuntimeError):
    """npx is missing, or mermaid-cli could not be fetched or run."""


def available():
    """Is the Mermaid route usable on this machine?"""
    return shutil.which("npx") is not None


def render(source, background=None):
    """Mermaid source → SVG text.

    No size is requested. mermaid-cli 12 offers only `--size`, a single
    maximum dimension that for SVG output moves `max-width` and nothing else
    — and `mermaid_theme` rewrites the dimensions from the viewBox anyway.
    Whether the result suits a frame is judged afterwards, from the geometry
    Mermaid actually produced.
    """
    if not available():
        raise MermaidUnavailable(
            "npx is not on PATH, so Mermaid-backed diagrams cannot be rendered. "
            "Install Node.js 18+ (nodejs.org, or your distribution's package), "
            "or author the diagram as a native .json spec instead.")

    with tempfile.TemporaryDirectory(prefix="dg-mermaid-") as tmp:
        work = Path(tmp)
        (work / "in.mmd").write_text(source, encoding="utf-8")
        (work / "config.json").write_text(
            json.dumps(mermaid_config()), encoding="utf-8")

        cmd = ["npx", "--yes", PACKAGE,
               "-i", str(work / "in.mmd"),
               "-o", str(work / "out.svg"),
               "-c", str(work / "config.json"),
               "-I", SVG_ID,
               "-b", background or "white"]

        try:
            done = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            raise MermaidUnavailable(
                f"mermaid-cli did not finish within {TIMEOUT}s. The first run "
                "downloads the package and a browser; try again once it is "
                "cached.") from None

        out = work / "out.svg"
        if done.returncode != 0 or not out.exists():
            detail = (done.stderr or done.stdout or "").strip()
            # Mermaid reports a syntax error on stderr and still exits non-zero;
            # surfacing it verbatim is more use than a wrapper's paraphrase.
            raise MermaidUnavailable(
                f"mermaid-cli failed:\n{detail}" if detail
                else "mermaid-cli failed with no output")
        return out.read_text(encoding="utf-8")
