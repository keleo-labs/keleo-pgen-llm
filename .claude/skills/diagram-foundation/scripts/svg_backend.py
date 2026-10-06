"""Scene → SVG.

Labels are native <text> rather than foreignObject: a standalone .svg loaded
through a markdown <img> does not render foreignObject content in most
browsers. Every diagram paints an opaque background rect because GitHub
renders images against dark page backgrounds too, and a transparent canvas
swallows dark text.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from diagram import THEME

_QUOT = {chr(34): "&quot;"}


def _fmt(value):
    """Trim float noise so the output diffs cleanly."""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _rect(item):
    parts = [
        f'<rect x="{_fmt(item["x"])}" y="{_fmt(item["y"])}" '
        f'width="{_fmt(item["w"])}" height="{_fmt(item["h"])}"',
        f'rx="{item["radius"]}" ry="{item["radius"]}" fill="{item["fill"]}" '
        f'stroke="{item["stroke"]}"',
        f'stroke-width="{_fmt(item["sw"])}"',
    ]
    if item.get("opacity") is not None:
        parts.append(f'opacity="{item["opacity"]}"')
    return "  " + " ".join(parts) + " />"


def _text(item):
    return (
        f'  <text x="{_fmt(item["x"])}" y="{_fmt(item["y"])}" '
        f'font-size="{item["size"]}" fill="{item["fill"]}" '
        f'font-weight="{item["weight"]}" text-anchor="{item["anchor"]}" '
        f'font-family="{escape(THEME["font"], _QUOT)}">'
        f"{escape(item['s'])}</text>"
    )


def _path(item):
    return (
        f'  <path d="M {_fmt(item["x1"])} {_fmt(item["y1"])} '
        f'C {_fmt(item["cp1x"])} {_fmt(item["cp1y"])}, '
        f'{_fmt(item["cp2x"])} {_fmt(item["cp2y"])}, '
        f'{_fmt(item["x2"])} {_fmt(item["y2"])}" fill="none" '
        f'stroke="{THEME["edge"]}" stroke-width="{THEME["edge_width"]}" '
        f'marker-end="url(#arrow)" />'
    )


def _line(item):
    return (
        f'  <line x1="{_fmt(item["x1"])}" y1="{_fmt(item["y1"])}" '
        f'x2="{_fmt(item["x2"])}" y2="{_fmt(item["y2"])}" '
        f'stroke="{THEME["edge"]}" stroke-width="{THEME["edge_width"]}" '
        f'marker-end="url(#arrow)" />'
    )


_EMIT = {"rect": _rect, "text": _text, "path": _path}


def render(scene, spec):
    """Return the SVG document for a laid-out scene."""
    width, height = scene["width"], scene["height"]

    body = []
    for item in scene["items"]:
        if item["t"] == "path" and item.get("straight"):
            body.append(_line(item))
        else:
            body.append(_EMIT[item["t"]](item))

    offset = scene.get("offset")
    if offset:
        dx, dy = offset
        body = ([f'  <g transform="translate({_fmt(dx)}, {_fmt(dy)})">']
                + body + ["  </g>"])

    # The title is metadata, not artwork. A diagram in a report sits under a
    # heading that already names it, so drawing it would repeat the line.
    title = spec.get("title", "")
    desc = spec.get("description", title)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_fmt(width)} {_fmt(height)}" '
        f'width="{_fmt(width)}" height="{_fmt(height)}" role="img" '
        f'aria-label="{escape(desc, _QUOT)}">',
    ]
    if title:
        out.append(f"  <title>{escape(title)}</title>")
    if desc and desc != title:
        out.append(f"  <desc>{escape(desc)}</desc>")
    out += [
        "  <defs>",
        '    <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" '
        'orient="auto">',
        f'      <polygon points="0 0, 8 3, 0 6" fill="{THEME["edge_arrow"]}" />',
        "    </marker>",
        "  </defs>",
        f'  <rect x="0" y="0" width="{_fmt(width)}" height="{_fmt(height)}" '
        f'fill="{THEME["canvas"]}" />',
    ]
    out += body
    out.append("</svg>")
    return "\n".join(out) + "\n"
