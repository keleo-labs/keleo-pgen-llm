"""Scene → SVG.

Labels are native <text> rather than foreignObject: a standalone .svg loaded
through a markdown <img> does not render foreignObject content in most
browsers. Every diagram paints an opaque background rect because GitHub
renders images against dark page backgrounds too, and a transparent canvas
swallows dark text.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from diagram import THEME, cylinder_ry

_QUOT = {chr(34): "&quot;"}


def _fmt(value):
    """Trim float noise so the output diffs cleanly."""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _paint(item):
    """The fill/stroke/opacity attributes every body shape shares."""
    out = (f'fill="{item["fill"]}" stroke="{item["stroke"]}" '
           f'stroke-width="{_fmt(item["sw"])}"')
    if item.get("opacity") is not None:
        out += f' opacity="{item["opacity"]}"'
    return out


def _points(pairs):
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pairs)


def _shape(item):
    """A node body. Every shape fills the item's bounding box exactly."""
    x, y, w, h = item["x"], item["y"], item["w"], item["h"]
    kind = item.get("shape")

    if kind == "diamond":
        pts = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
        return f'  <polygon points="{_points(pts)}" {_paint(item)} />'

    if kind == "hexagon":
        inset = min(w * 0.18, h * 0.5)
        pts = [(x + inset, y), (x + w - inset, y), (x + w, y + h / 2),
               (x + w - inset, y + h), (x + inset, y + h), (x, y + h / 2)]
        return f'  <polygon points="{_points(pts)}" {_paint(item)} />'

    if kind == "note":
        fold = min(14.0, w * 0.22, h * 0.45)
        pts = [(x, y), (x + w - fold, y), (x + w, y + fold),
               (x + w, y + h), (x, y + h)]
        return f'  <polygon points="{_points(pts)}" {_paint(item)} />'

    if kind == "event":
        return (f'  <ellipse cx="{_fmt(x + w / 2)}" cy="{_fmt(y + h / 2)}" '
                f'rx="{_fmt(w / 2)}" ry="{_fmt(h / 2)}" {_paint(item)} />')

    if kind == "cylinder":
        # Shared with node_block, which insets the label past these caps.
        ry = cylinder_ry(h)
        # Body first — the silhouette from the top of the cap to the bottom
        # of the base — then the lid as a *filled* ellipse rather than a bare
        # arc. An unfilled lid leaves the cap reading as see-through, and an
        # edge routed behind the shape appears to pass through it.
        body = (f"M {_fmt(x)} {_fmt(y + ry)} "
                f"L {_fmt(x)} {_fmt(y + h - ry)} "
                f"A {_fmt(w / 2)} {_fmt(ry)} 0 0 0 {_fmt(x + w)} {_fmt(y + h - ry)} "
                f"L {_fmt(x + w)} {_fmt(y + ry)} Z")
        return (f'  <path d="{body}" {_paint(item)} />\n'
                f'  <ellipse cx="{_fmt(x + w / 2)}" cy="{_fmt(y + ry)}" '
                f'rx="{_fmt(w / 2)}" ry="{_fmt(ry)}" {_paint(item)} />')

    return None


def _rect(item):
    drawn = _shape(item)
    if drawn is not None:
        return drawn
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


# Connector styling. Omitted from the emitted attributes when it matches the
# solid filled-arrow default, so an existing spec renders byte-identically.
_DASH_ARRAY = {"dashed": "6 4", "dotted": "2 3"}

_MARKER_ID = {"arrow": "arrow", "open": "arrowopen", "diamond": "arrowdiamond"}


def _stroke_attrs(item):
    out = (f'stroke="{THEME["edge"]}" stroke-width="{THEME["edge_width"]}"')
    dash = _DASH_ARRAY.get(item.get("dash"))
    if dash:
        out += f' stroke-dasharray="{dash}"'
    arrow = item.get("arrow", "arrow")
    # Crow's foot has no Slides or marker equivalent here; it is a route C
    # notation only, so it degrades to an open head rather than vanishing.
    marker = _MARKER_ID.get("open" if arrow == "crowsfoot" else arrow)
    if marker:
        out += f' marker-end="url(#{marker})"'
    return out


def _route(points):
    """A rounded polyline through a route: quadratics via the midpoints.

    Each interior point becomes a control point and the curve passes through
    the midpoint between consecutive ones, which rounds every corner without
    needing a corner radius or any knowledge of the angle.
    """
    out = [f'M {_fmt(points[0][0])} {_fmt(points[0][1])}']
    for i in range(1, len(points) - 1):
        (cx, cy), (nx, ny) = points[i], points[i + 1]
        out.append(f'Q {_fmt(cx)} {_fmt(cy)}, '
                   f'{_fmt((cx + nx) / 2)} {_fmt((cy + ny) / 2)}')
    out.append(f'L {_fmt(points[-1][0])} {_fmt(points[-1][1])}')
    return " ".join(out)


def _path(item):
    points = item.get("points")
    if points and len(points) > 2:
        geometry = _route(points)
    else:
        geometry = (
            f'M {_fmt(item["x1"])} {_fmt(item["y1"])} '
            f'C {_fmt(item["cp1x"])} {_fmt(item["cp1y"])}, '
            f'{_fmt(item["cp2x"])} {_fmt(item["cp2y"])}, '
            f'{_fmt(item["x2"])} {_fmt(item["y2"])}'
        )
    return f'  <path d="{geometry}" fill="none" {_stroke_attrs(item)} />'


def _line(item):
    return (
        f'  <line x1="{_fmt(item["x1"])}" y1="{_fmt(item["y1"])}" '
        f'x2="{_fmt(item["x2"])}" y2="{_fmt(item["y2"])}" '
        f'{_stroke_attrs(item)} />'
    )


def _marker_defs(scene):
    """Only the arrow heads the scene actually uses.

    Emitting the full set would change the output of every existing diagram
    for no visible gain, and unused defs are noise in a file people read.
    """
    wanted = set()
    for item in scene["items"]:
        if item["t"] != "path":
            continue
        arrow = item.get("arrow", "arrow")
        wanted.add("open" if arrow == "crowsfoot" else arrow)

    colour = THEME["edge_arrow"]
    shapes = {
        "arrow": f'<polygon points="0 0, 8 3, 0 6" fill="{colour}" />',
        "open": f'<path d="M 0 0 L 8 3 L 0 6" fill="none" stroke="{colour}" '
                'stroke-width="1.2" />',
        "diamond": f'<polygon points="0 3, 4 0, 8 3, 4 6" fill="{colour}" />',
    }
    out = []
    for name in ("arrow", "open", "diamond"):
        if name not in wanted:
            continue
        out += [
            f'    <marker id="{_MARKER_ID[name]}" markerWidth="8" '
            'markerHeight="6" refX="8" refY="3" orient="auto">',
            f"      {shapes[name]}",
            "    </marker>",
        ]
    return out


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
    markers = _marker_defs(scene)
    if markers:
        out += ["  <defs>"] + markers + ["  </defs>"]
    out += [
        f'  <rect x="0" y="0" width="{_fmt(width)}" height="{_fmt(height)}" '
        f'fill="{THEME["canvas"]}" />',
    ]
    out += body
    out.append("</svg>")
    return "\n".join(out) + "\n"
