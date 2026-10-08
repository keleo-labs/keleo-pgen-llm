"""One call that turns any spec file into something renderable.

Three routes reach the same two outputs — an SVG, and (where possible) a Scene
the Slides backend can turn into editable shapes. Callers should not have to
know which route a given file takes, so they ask here:

    diagram = load(Path("topology.mmd"), fit_ratio=16/9)
    diagram.svg()        # always
    diagram.scene()      # None when the diagram is a picture

Two spec forms:

    <name>.json   a declarative spec — native layouts (route A)
    <name>.mmd    YAML frontmatter, then Mermaid source (routes B and C)

A `.mmd` takes route B — Mermaid lays out, we draw — when it is a flowchart
and the frontmatter does not say otherwise. Anything else, or any surprise
during the import, falls back to route C: Mermaid's own picture, themed. The
reason is recorded in `note` rather than swallowed, because silently producing
a different kind of artifact than the author expected is how a deck ends up
with one diagram that cannot be edited and nobody knows why.
"""

from __future__ import annotations

import json
from pathlib import Path

import mermaid_import
import mermaid_render
import mermaid_theme
import svg_backend
from diagram import build_scene, fit_to_aspect, validate

# Frontmatter keys a .mmd may carry. Anything else is a typo worth reporting.
MMD_KEYS = {"method", "title", "description", "render", "palette"}

RENDER_MODES = ("scene", "picture")


class SpecError(ValueError):
    """The spec file is malformed or will not validate."""


class Diagram:
    """A loaded spec, ready to render. Produced by `load`."""

    def __init__(self, kind, spec, scene=None, svg_text=None, note=None):
        self.kind = kind              # "native" | "scene" | "picture"
        self.spec = spec              # title/description and, if native, layout
        self._scene = scene
        self._svg = svg_text
        self.note = note

    @property
    def editable(self):
        """Can this become native Google Slides shapes?"""
        return self._scene is not None

    def scene(self):
        return self._scene

    def svg(self):
        if self._svg is None:
            self._svg = svg_backend.render(self._scene, self.spec)
        return self._svg


# --------------------------------------------------------------------------
# .mmd — frontmatter plus Mermaid source
# --------------------------------------------------------------------------

def parse_mmd(body, where="spec"):
    """Split a .mmd into (frontmatter dict, Mermaid source)."""
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SpecError(
            f"{where}: a .mmd spec opens with a '---' frontmatter block "
            "carrying at least a 'method' and a 'title'")
    try:
        close = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise SpecError(f"{where}: frontmatter block is never closed with '---'") from None

    meta = {}
    for number, line in enumerate(lines[1:close], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise SpecError(f"{where} line {number}: expected 'key: value'")
        key = key.strip()
        if key not in MMD_KEYS:
            raise SpecError(
                f"{where} line {number}: unknown frontmatter key {key!r} "
                f"(use one of {', '.join(sorted(MMD_KEYS))})")
        # Strip an inline comment, then surrounding quotes.
        value = value.split("  #")[0].strip().strip("'\"")
        meta[key] = value

    if not meta.get("method"):
        raise SpecError(f"{where}: frontmatter needs a 'method'")
    mode = meta.get("render", "scene")
    if mode not in RENDER_MODES:
        raise SpecError(
            f"{where}: render must be one of {', '.join(RENDER_MODES)} "
            f"(got {mode!r})")

    source = "\n".join(lines[close + 1:]).strip()
    if not source:
        raise SpecError(f"{where}: no Mermaid source after the frontmatter")
    return meta, source


def _load_mmd(path, fit_ratio):
    meta, source = parse_mmd(path.read_text(encoding="utf-8"), path.name)
    spec = {"title": meta.get("title", ""),
            "description": meta.get("description", meta.get("title", "")),
            "method": meta["method"]}

    # Mermaid is not asked to aim at the frame: its CLI has no target size,
    # only a maximum. Whether the result fits is judged afterwards, from the
    # geometry it produced, and reported rather than forced.
    svg = mermaid_render.render(source)

    if meta.get("render", "scene") == "scene":
        try:
            scene = mermaid_import.build_scene(source, svg, mermaid_render.SVG_ID)
            return Diagram("scene", spec, scene=scene,
                           note=_fit_note(scene["width"], scene["height"], fit_ratio))
        except mermaid_import.ImportUnsupported as exc:
            note = (f"kept as a picture rather than editable shapes: {exc}")
    else:
        note = None

    themed = mermaid_theme.apply(svg, spec["title"], spec["description"])
    size = mermaid_theme.viewbox_size(themed)
    if size and fit_ratio:
        fit = _fit_note(size[0], size[1], fit_ratio)
        note = "; ".join(part for part in (note, fit) if part)
    return Diagram("picture", spec, svg_text=themed, note=note)


def _fit_note(width, height, fit_ratio):
    """Report a bad fit rather than reshaping the diagram to force one.

    Same decision as `fit_to_aspect` makes for a native flow, for the same
    reason: a diagram that will not fit a frame is usually one carrying more
    than one idea, and that fix belongs with the author.
    """
    if not fit_ratio or not height:
        return None
    ratio = width / height
    fill = min(ratio / fit_ratio, fit_ratio / ratio)
    if fill >= 0.45:
        return None
    shape = "much wider" if ratio > fit_ratio else "much taller"
    return (f"fills only {fill:.0%} of the frame — the diagram is {shape} "
            "than the space. Split it, or raise its level of abstraction")


# --------------------------------------------------------------------------

def load(path, fit_ratio=None):
    """Load any spec file. Raises SpecError, or mermaid_render.MermaidUnavailable."""
    path = Path(path)
    try:
        body = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SpecError(f"File not found: {path}") from None

    if path.suffix.lower() == ".mmd":
        return _load_mmd(path, fit_ratio)

    try:
        spec = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SpecError(f"Invalid JSON in {path}: {exc}") from None

    problems = validate(spec)
    if problems:
        raise SpecError(f"{path}: " + "; ".join(problems))

    note = None
    if fit_ratio:
        spec, note = fit_to_aspect(spec, fit_ratio)
    return Diagram("native", spec, scene=build_scene(spec), note=note)


def is_spec(path):
    """Does this path look like a diagram spec?"""
    return Path(path).suffix.lower() in (".json", ".mmd")
