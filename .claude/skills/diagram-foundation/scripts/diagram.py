"""Diagram layout engine — specs in, backend-neutral scenes out.

Four layouts cover what reports and decks need: flow (layered boxes and
directed edges), stack (vertical tiers), timeline (sequential phases), hub
(centre plus satellites). The visual language is lifted from the
keleo-studio-gas navigator diagrams so reports, decks and the studio UI read
as one system.

Layout is separated from rendering so the same geometry can become an SVG for
a markdown report or native shapes for a Google Slides deck. A layout returns
a Scene — an ordered list of primitives in pixel coordinates — and a backend
turns that into output. Ordering is load-bearing: items paint in sequence, so
edge labels come last and sit above the boxes their edges pass under.

Scene:
    {"items": [...], "width": float, "height": float, "offset": (dx, dy)}

Items:
    {"t": "rect", x, y, w, h, fill, stroke, sw, radius, opacity}
    {"t": "text", x, y, s, size, fill, weight, anchor}
    {"t": "path", x1, y1, cp1x, cp1y, cp2x, cp2y, x2, y2}   # edge, arrow-ended
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

# --------------------------------------------------------------------------
# Design tokens — keleo-studio-gas navigator
# (src/scripts/views/Navigator*.html, src/templates/navigator.html,
#  src/styles/navigator.html)
# --------------------------------------------------------------------------

THEME = {
    "accent": "#0066cc",
    "canvas": "#ffffff",
    "node_fill": "#ffffff",
    "node_fill_muted": "#f5f5f5",
    "node_fill_accent": "#f0f0ff",
    "node_fill_selected": "#edf1ff",
    "border": "#d2d2d2",
    "border_accent": "#0066cc",
    "stroke_default": 1.5,
    "stroke_accent": 2.0,
    "text": "#151515",
    "text_muted": "#6a6e73",
    "edge": "rgba(102,102,102,0.6)",
    "edge_arrow": "rgba(102,102,102,0.7)",
    "edge_width": 1.5,
    "group_fill": "#f5f5f5",
    "group_stroke": "#d2d2d2",
    "group_opacity": 0.5,
    "radius_node": 4,
    "radius_group": 6,
    "radius_sticky": 2,
    "lane_header": 112,
    "lane_fill": "#fafafa",
    "band_stroke": "#e4e4e4",
    "axis": "#8a8d90",
    "font": "'Red Hat Text', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
    "size_label": 11,
    "size_sub": 9,
    "size_edge": 10,
    "size_group": 11,
    "node_w": 160,
    "node_h": 48,
    "node_w_max": 220,
    "col_gap": 60,
    "row_gap": 16,
    "group_pad_x": 16,
    "group_pad_y": 28,
    "group_pad_bottom": 16,
    "group_gap": 24,
    "pad": 16,
    "line_height": 1.3,
}

EMPHASIS = {
    # name: (fill, stroke, stroke_width)
    "default": (THEME["node_fill"], THEME["border"], THEME["stroke_default"]),
    "muted": (THEME["node_fill_muted"], THEME["border"], THEME["stroke_default"]),
    "accent": (THEME["node_fill_accent"], THEME["border_accent"], THEME["stroke_accent"]),
    "selected": (THEME["node_fill_selected"], THEME["border_accent"], THEME["stroke_accent"]),
}


# --------------------------------------------------------------------------
# Semantic colour roles
#
# A second, independent axis to `emphasis`. Emphasis says how much a node
# matters in *this* diagram; a role says what the node *is* under a notation
# that assigns meaning to colour. A role decides the fill and border; the
# node's emphasis still decides the stroke weight, so an accented sticky is a
# sticky with a heavier border.
#
# See references/visual-language.md, which is the table these must match.
# --------------------------------------------------------------------------

# Event Storming. These hues ARE the notation — a facilitator reads the wall
# by colour — so they are fixed and do not follow the palette. Softened from
# the sticky-note originals to sit in the flat register, hue relationships
# intact.
STORM_ROLES = {
    "storm.event":     ("#ffe0b2", "#e8a33d"),   # orange — a domain event
    "storm.command":   ("#d6e8fb", "#5b9bd5"),   # blue — a requested action
    "storm.actor":     ("#fff3c4", "#dcc054"),   # small yellow — who commands
    "storm.aggregate": ("#fdf6d8", "#d9c97a"),   # pale yellow — state holder
    "storm.policy":    ("#e6ddf5", "#9b85c9"),   # lilac — reactive logic
    "storm.readmodel": ("#d9eedc", "#6cab77"),   # green — a projection
    "storm.external":  ("#fbdce8", "#d481a5"),   # pink — outside our control
    "storm.hotspot":   ("#fcd9d9", "#d96a6a"),   # red — unknown or conflict
}

# Capability heat, 1 healthy to 5 critical. Fixed rather than palette-derived:
# neither palette carries a diverging scale, and a heat map whose meaning
# shifted with the deck theme would be worse than no heat map. Always draw the
# legend.
HEAT_ROLES = {
    "heat.1": ("#dcefdc", "#7fae7f"),
    "heat.2": ("#eaf2d6", "#a8b878"),
    "heat.3": ("#fdf2cf", "#d4bb63"),
    "heat.4": ("#fbe0cc", "#d89a63"),
    "heat.5": ("#f9d2d2", "#cf6f6f"),
}

ROLES = {}


def _mix(css_a, css_b, t):
    """Blend two #rrggbb colours, t=0 gives a, t=1 gives b."""
    def parts(css):
        css = css.lstrip("#")
        return [int(css[i:i + 2], 16) for i in (0, 2, 4)]
    a, b = parts(css_a), parts(css_b)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def _graded_roles():
    """Roles that read as 'how settled', so they follow the palette.

    Wardley evolution and Gartner pace both describe a position on a single
    axis from new-and-volatile to old-and-stable. That is a house-style
    gradient from the accent colour toward neutral, not a fixed semantic, so
    unlike the Event Storming set these do change with the palette.
    """
    accent, neutral = THEME["border_accent"], THEME["border"]
    graded = {}
    steps = (("genesis", 0.0), ("custom", 0.33), ("product", 0.66),
             ("commodity", 1.0))
    for name, t in steps:
        stroke = _mix(accent, neutral, t)
        graded[f"evolution.{name}"] = (_mix(stroke, THEME["node_fill"], 0.84), stroke)
    for name, t in (("innovation", 0.0), ("differentiation", 0.5), ("record", 1.0)):
        stroke = _mix(accent, neutral, t)
        graded[f"pace.{name}"] = (_mix(stroke, THEME["node_fill"], 0.84), stroke)
    return graded


# --------------------------------------------------------------------------
# Palettes
#
# Geometry, type scale and spacing are fixed — only the colour family varies.
# A diagram embedded in a report or the studio UI reads as part of that
# surface; the same spec rendered onto a branded slide should read as part of
# the deck. The deck build swaps the palette before laying anything out, so
# the PNG and the native Slides shapes it is upgraded to agree.
# --------------------------------------------------------------------------

PALETTES = {
    # keleo-studio-gas navigator. The default: reports and the studio UI.
    "navigator": {
        "accent": "#0066cc",
        "border_accent": "#0066cc",
        "node_fill_accent": "#f0f0ff",
        "node_fill_selected": "#edf1ff",
        "node_fill_muted": "#f5f5f5",
        "group_fill": "#f5f5f5",
    },
    # Red Hat brand, matching deck-foundation/theme-redhat/styles/base.css.
    "redhat": {
        "accent": "#ee0000",
        "border_accent": "#ee0000",
        "node_fill_accent": "#fdeaea",
        "node_fill_selected": "#fdf4f4",
        "node_fill_muted": "#f2f2f2",
        "group_fill": "#f2f2f2",
    },
}


def _rebuild_roles():
    """Refresh ROLES in place. Fixed families first, graded ones from THEME."""
    ROLES.clear()
    ROLES.update(STORM_ROLES)
    ROLES.update(HEAT_ROLES)
    ROLES.update(_graded_roles())


def use_palette(name):
    """Switch the colour family in place. Returns the palette applied.

    THEME, EMPHASIS and ROLES are mutated rather than rebound because the
    backends bind them at import (`from diagram import THEME`); rebinding here
    would leave them pointing at the old dict.
    """
    try:
        palette = PALETTES[name]
    except KeyError:
        raise ValueError(
            f"unknown palette {name!r} (use one of {', '.join(PALETTES)})") from None

    THEME.update(palette)
    EMPHASIS.update({
        "default": (THEME["node_fill"], THEME["border"], THEME["stroke_default"]),
        "muted": (THEME["node_fill_muted"], THEME["border"], THEME["stroke_default"]),
        "accent": (THEME["node_fill_accent"], THEME["border_accent"],
                   THEME["stroke_accent"]),
        "selected": (THEME["node_fill_selected"], THEME["border_accent"],
                     THEME["stroke_accent"]),
    })
    _rebuild_roles()
    return palette


_rebuild_roles()

LAYOUTS = ("flow", "stack", "timeline", "hub", "matrix", "wardley",
           "swimlane", "canvas")

# Node body shapes. All occupy the same bounding box, so a layout measures a
# node the same way whatever shape it wears. See references/visual-language.md.
SHAPES = ("rounded", "rect", "stadium", "cylinder", "hexagon", "diamond",
          "event", "note", "sticky", "person")

DASHES = ("solid", "dashed", "dotted")
ARROWS = ("arrow", "open", "none", "diamond", "crowsfoot")


# --------------------------------------------------------------------------
# Text metrics
# --------------------------------------------------------------------------

# Approximate advance widths as a fraction of font size, for a humanist sans.
# More faithful than a flat per-character constant, which overshoots on
# lowercase-heavy strings and undershoots on capitalised product names.
_NARROW = set("iljtfIr.,:;'!|()[]{}/\\ ")
_WIDE = set("mwMW@%")
_CAPS = set("ABCDEFGHJKLNOPQRSTUVXYZ0123456789")

BOLD_FACTOR = 1.06


def text_width(text, size, bold=False):
    """Estimate rendered width of a string in pixels."""
    total = 0.0
    for ch in text:
        if ch == " ":
            total += 0.28
        elif ch in _NARROW:
            total += 0.33
        elif ch in _WIDE:
            total += 0.90
        elif ch in _CAPS:
            total += 0.64
        else:
            total += 0.52
    return total * size * (BOLD_FACTOR if bold else 1.0)


def wrap_text(text, size, max_width, max_lines=3, bold=False):
    """Greedy word wrap. Over-long final line is truncated with an ellipsis."""
    words = text.split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if text_width(candidate, size, bold) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_width(last + "…", size, bold) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = last + "…"
    return lines


# --------------------------------------------------------------------------
# Scene primitives
# --------------------------------------------------------------------------

def rect(x, y, w, h, fill, stroke, sw, radius, opacity=None, shape=None):
    """A box in the scene.

    `shape` names a body shape from SHAPES; it stays absent for a plain
    rectangle so existing specs render byte-identically. Every shape fills the
    same bounding box, so a layout measures a node without caring which one it
    wears, and the backends decide how to draw it.
    """
    item = {"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill,
            "stroke": stroke, "sw": sw, "radius": radius, "opacity": opacity}
    if shape and shape not in ("rounded", "rect"):
        item["shape"] = shape
    return item


def resolve_style(node):
    """(fill, stroke, stroke_width) for a node, from its role then emphasis.

    A role names what the node is and wins on colour; emphasis says how much
    it matters here and keeps the stroke weight either way.
    """
    _, _, weight = EMPHASIS[node.get("emphasis", "default")]
    role = node.get("role")
    if role:
        fill, stroke = ROLES[role]
        return fill, stroke, weight
    fill, stroke, _ = EMPHASIS[node.get("emphasis", "default")]
    return fill, stroke, weight


def shape_of(node):
    """The body shape a node asks for, defaulting to the house rounded box."""
    return node.get("shape", "rounded")


def text(x, y, s, size, fill, weight="400", anchor="middle"):
    return {"t": "text", "x": x, "y": y, "s": s, "size": size, "fill": fill,
            "weight": weight, "anchor": anchor}


def node_block(node, x, y, w, h, centre_within=None):
    """Rounded rect plus wrapped label and optional sublabel.

    centre_within limits the band the text is centred in, measured from y.
    Callers that reserve space at the bottom of the box (stack tiers listing
    items) pass it so the label does not drift down into that space.
    """
    fill, stroke, stroke_width = resolve_style(node)
    shape = shape_of(node)

    # A person is a head over a body, the C4 convention. The head sits *inside*
    # the node's own box rather than above it: a glyph drawn outside the
    # bounding box is invisible to every layout's extent calculation and gets
    # clipped at the canvas edge.
    head_band = PERSON_HEAD + 4 if shape == "person" else 0
    body_y, body_h = y + head_band, h - head_band

    radius = {"rect": 0, "sticky": THEME["radius_sticky"],
              "stadium": body_h / 2}.get(shape, THEME["radius_node"])
    out = [rect(x, body_y, w, body_h, fill, stroke, stroke_width, radius,
                shape=shape)]
    if head_band:
        out.append(rect(x + w / 2 - PERSON_HEAD / 2, y, PERSON_HEAD, PERSON_HEAD,
                        fill, stroke, stroke_width, PERSON_HEAD / 2, shape="event"))

    label_lines = node["_label_lines"]
    sub_lines = node.get("_sub_lines", [])
    lh = THEME["size_label"] * THEME["line_height"]
    sub_lh = THEME["size_sub"] * THEME["line_height"]

    block_h = len(label_lines) * lh + (len(sub_lines) * sub_lh if sub_lines else 0)
    band = centre_within if centre_within is not None else body_h
    cursor = body_y + (band - block_h) / 2 + THEME["size_label"] * 0.85
    cx = x + w / 2

    for line in label_lines:
        out.append(text(cx, cursor, line, THEME["size_label"], THEME["text"], "600"))
        cursor += lh
    for line in sub_lines:
        out.append(text(cx, cursor, line, THEME["size_sub"], THEME["text_muted"]))
        cursor += sub_lh
    return out


# How much bigger a shape's bounding box must be than the text it holds.
# A rhombus of a given box only offers about half that box to a horizontal
# line of text, so sizing it like a rectangle squashes the label against the
# sloped sides. `rounded` and `rect` are absent, which keeps every existing
# spec measuring exactly as before.
SHAPE_SLACK = {
    "diamond": (1.65, 1.6),
    "hexagon": (1.25, 1.0),
    "event": (1.35, 1.3),
    "stadium": (1.22, 1.0),
    "cylinder": (1.0, 1.3),
    "note": (1.1, 1.0),
}

# Diameter of the head on a `person`, and the band reserved for it at the top
# of that node's box.
PERSON_HEAD = 15.0

# Flat additions, applied after SHAPE_SLACK: space a shape needs that does not
# scale with the label.
SHAPE_PAD = {"person": (0.0, PERSON_HEAD + 4)}


def measure_node(node, max_width=None, min_width=None, min_height=None):
    """Attach wrapped lines to a node and return its (width, height).

    The returned box accounts for the node's shape: see SHAPE_SLACK.

    `min_width` and `min_height` default to the house node size, which is
    what keeps a row of boxes even in our own layouts. A caller placing nodes
    into a layout computed elsewhere should pass 0 for both: imposing our
    minimum on someone else's geometry makes every box wider than the one the
    edges were routed around, and the routing then runs through the shape.
    """
    max_width = max_width or THEME["node_w_max"]
    min_width = THEME["node_w"] if min_width is None else min_width
    min_height = THEME["node_h"] if min_height is None else min_height
    inner = max_width - 28
    node["_label_lines"] = wrap_text(node.get("label", ""), THEME["size_label"], inner,
                                     bold=True)
    sub = node.get("sublabel")
    node["_sub_lines"] = wrap_text(sub, THEME["size_sub"], inner, max_lines=2) if sub else []

    widest = max(
        [text_width(l, THEME["size_label"], bold=True) for l in node["_label_lines"]]
        + [text_width(l, THEME["size_sub"]) for l in node["_sub_lines"]]
        + [0]
    )
    w = max(min_width, min(max_width, widest + 28))
    content_h = (
        len(node["_label_lines"]) * THEME["size_label"] * THEME["line_height"]
        + len(node["_sub_lines"]) * THEME["size_sub"] * THEME["line_height"]
    )
    h = max(min_height, content_h + 18)
    shape = shape_of(node)
    slack_w, slack_h = SHAPE_SLACK.get(shape, (1.0, 1.0))
    pad_w, pad_h = SHAPE_PAD.get(shape, (0.0, 0.0))
    return w * slack_w + pad_w, h * slack_h + pad_h


def polyline_path(points, dash=None, arrow=None):
    """An edge that follows a route rather than a single curve.

    Used when something upstream has already worked out how to get past the
    nodes in between — collapsing that to a straight hop between endpoints
    throws the avoidance away and drives the line through whatever it was
    routing around. `points` are in scene coordinates, start to end.
    """
    (x1, y1), (x2, y2) = points[0], points[-1]
    item = {"t": "path", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "cp1x": x1, "cp1y": y1, "cp2x": x2, "cp2y": y2,
            "points": [tuple(p) for p in points]}
    if dash and dash != "solid":
        item["dash"] = dash
    if arrow and arrow != "arrow":
        item["arrow"] = arrow
    return item


def simplify_path(points, tolerance=8.0):
    """Ramer–Douglas–Peucker. Drops sample points that carry no shape.

    A renderer that samples a curve hands back a dozen points for a line that
    is visually straight. Keeping them all would turn one edge into a dozen
    connectors on a slide, so only the points that actually bend survive.
    """
    if len(points) < 3:
        return list(points)

    (ax, ay), (bx, by) = points[0], points[-1]
    dx, dy = bx - ax, by - ay
    span = math.hypot(dx, dy)

    worst, index = 0.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if span < 1e-9:
            gap = math.hypot(px - ax, py - ay)
        else:
            gap = abs(dy * px - dx * py + bx * ay - by * ax) / span
        if gap > worst:
            worst, index = gap, i

    if worst <= tolerance:
        return [points[0], points[-1]]
    return (simplify_path(points[:index + 1], tolerance)[:-1]
            + simplify_path(points[index:], tolerance))


def edge_path(x1, y1, x2, y2, exit_dir, entry_dir, dash=None, arrow=None):
    """Cubic bezier mirroring computeEdgePath in the studio navigator.

    `dash` and `arrow` are omitted from the item unless they differ from the
    solid filled-arrow default, so an existing spec renders byte-identically.
    """
    span = max(abs(x2 - x1), abs(y2 - y1), 1)
    offset = span * 0.45
    cp1x, cp1y = x1, y1
    cp2x, cp2y = x2, y2
    # Both control points are pushed *outward* from their own endpoint, along
    # the side the edge leaves or arrives on — the studio computeEdgePath rule.
    for direction, (px, py) in (("right", (1, 0)), ("left", (-1, 0)),
                                ("bottom", (0, 1)), ("top", (0, -1))):
        if exit_dir == direction:
            cp1x, cp1y = x1 + px * offset, y1 + py * offset
        if entry_dir == direction:
            cp2x, cp2y = x2 + px * offset, y2 + py * offset
    item = {"t": "path", "x1": x1, "y1": y1, "cp1x": cp1x, "cp1y": cp1y,
            "cp2x": cp2x, "cp2y": cp2y, "x2": x2, "y2": y2}
    if dash and dash != "solid":
        item["dash"] = dash
    if arrow and arrow != "arrow":
        item["arrow"] = arrow
    return item


def edge_label(x, y, label):
    if not label:
        return []
    size = THEME["size_edge"]
    w = text_width(label, size) + 8
    backing = rect(x - w / 2, y - size, w, size + 5, THEME["canvas"], "none", 0, 2)
    # Marks the white plate an edge label sits on. The SVG backend ignores it;
    # the Slides backend needs it because Google sets text wider than Chromium
    # and the plate has to grow to match.
    backing["kind"] = "label_bg"
    return [backing, text(x, y, label, size, THEME["text_muted"])]


# --------------------------------------------------------------------------
# Layouts
# --------------------------------------------------------------------------

def layout_flow(spec):
    """Layered DAG. Rank by longest path from a source; lay out by direction."""
    nodes = spec["nodes"]
    edges = spec.get("edges", [])
    by_id = {n["id"]: n for n in nodes}
    horizontal = spec.get("direction", "TB").upper() == "LR"

    incoming = {n["id"]: [] for n in nodes}
    outgoing = {n["id"]: [] for n in nodes}
    for e in edges:
        outgoing[e["from"]].append(e["to"])
        incoming[e["to"]].append(e["from"])

    # Explicit ranks seed the memo so descendants rank *below* them. Applying
    # them afterwards would leave a child computed from the old value and
    # collapse it into the same layer as its parent.
    rank = {n["id"]: n["rank"] for n in nodes if "rank" in n}

    def resolve(nid, seen):
        if nid in rank:
            return rank[nid]
        if nid in seen or not incoming[nid]:
            rank[nid] = 0
            return 0
        value = 1 + max(resolve(p, seen | {nid}) for p in incoming[nid])
        rank[nid] = value
        return value

    for n in nodes:
        resolve(n["id"], set())

    layers = {}
    for n in nodes:
        layers.setdefault(rank[n["id"]], []).append(n)

    for n in nodes:
        n["_w"], n["_h"] = measure_node(n)

    pad = THEME["pad"]
    cross_gap = THEME["row_gap"] + 8
    # Vertical flows need less room between layers than horizontal ones: the
    # arrow is short and the eye tracks downward without help.
    layer_gap = THEME["col_gap"] if horizontal else 44

    # Depth is along the flow direction; breadth is across it.
    layer_extent, breadth_extent = [], []
    for idx in sorted(layers):
        members = layers[idx]
        if horizontal:
            layer_extent.append(max(n["_w"] for n in members))
            breadth_extent.append(sum(n["_h"] for n in members) + cross_gap * (len(members) - 1))
        else:
            layer_extent.append(max(n["_h"] for n in members))
            breadth_extent.append(sum(n["_w"] for n in members) + cross_gap * (len(members) - 1))

    breadth = max(breadth_extent) if breadth_extent else 0

    # A cluster rect is drawn by inflating its members' bounding box, so it
    # reaches beyond the layer its nodes sit in. Left to the plain layer gap,
    # one group's rect ends exactly where the next one's begins and the two
    # read as a single box with a line through it. Widen the gap at every
    # boundary where a rect actually ends or starts.
    ordered = sorted(layers)
    group_ids = {g["id"] for g in spec.get("groups", [])}
    layer_groups = [
        {n.get("group") for n in layers[idx] if n.get("group") in group_ids}
        for idx in ordered
    ]
    if horizontal:
        lead_pad = trail_pad = THEME["group_pad_x"]
    else:
        lead_pad, trail_pad = THEME["group_pad_y"], THEME["group_pad_bottom"]

    def boundary_gap(position):
        """Extra room between layer `position` and the one after it."""
        if position + 1 >= len(ordered):
            return 0
        here, nxt = layer_groups[position], layer_groups[position + 1]
        ending = {g for g in here - nxt
                  if all(g not in later for later in layer_groups[position + 1:])}
        starting = {g for g in nxt - here
                    if all(g not in before for before in layer_groups[:position + 1])}
        extra = (trail_pad if ending else 0) + (lead_pad if starting else 0)
        return extra + THEME["group_gap"] if extra else 0

    cursor = pad
    for position, idx in enumerate(ordered):
        members = layers[idx]
        offset = pad + (breadth - breadth_extent[position]) / 2
        for n in members:
            if horizontal:
                n["_x"], n["_y"] = cursor, offset
                offset += n["_h"] + cross_gap
            else:
                n["_x"], n["_y"] = offset, cursor
                offset += n["_w"] + cross_gap
        cursor += layer_extent[position] + layer_gap + boundary_gap(position)

    body = []
    extents = [(n["_x"], n["_y"], n["_x"] + n["_w"], n["_y"] + n["_h"]) for n in nodes]

    group_defs = {g["id"]: g for g in spec.get("groups", [])}
    if group_defs:
        clusters = {}
        for n in nodes:
            if n.get("group") in group_defs:
                clusters.setdefault(n["group"], []).append(n)
        for gid, members in clusters.items():
            gx = min(n["_x"] for n in members) - THEME["group_pad_x"]
            gy = min(n["_y"] for n in members) - THEME["group_pad_y"]
            gw = max(n["_x"] + n["_w"] for n in members) + THEME["group_pad_x"] - gx
            gh = max(n["_y"] + n["_h"] for n in members) + THEME["group_pad_bottom"] - gy
            extents.append((gx, gy, gx + gw, gy + gh))
            body.append(rect(gx, gy, gw, gh, THEME["group_fill"], THEME["group_stroke"],
                             1, THEME["radius_group"], THEME["group_opacity"]))
            body.append(text(gx + 8, gy + 16, group_defs[gid].get("label", gid),
                             THEME["size_group"], THEME["text_muted"], anchor="start"))

    labels = []
    for e in edges:
        a, b = by_id[e["from"]], by_id[e["to"]]
        if horizontal:
            x1, y1 = a["_x"] + a["_w"], a["_y"] + a["_h"] / 2
            x2, y2 = b["_x"], b["_y"] + b["_h"] / 2
            exit_dir, entry_dir = "right", "left"
        else:
            x1, y1 = a["_x"] + a["_w"] / 2, a["_y"] + a["_h"]
            x2, y2 = b["_x"] + b["_w"] / 2, b["_y"]
            exit_dir, entry_dir = "bottom", "top"
        body.append(edge_path(x1, y1, x2, y2, exit_dir, entry_dir,
                              e.get("dash"), e.get("arrow")))
        # Anchor the label in the gap just after the source rather than at the
        # midpoint: an edge that skips a layer would otherwise drop its label
        # on top of a node in the layer it passes through.
        span = (x2 - x1) if horizontal else (y2 - y1)
        t = min(0.5, (layer_gap / 2) / abs(span)) if abs(span) > 1 else 0.5
        labels.extend(edge_label(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, e.get("label")))

    for n in nodes:
        body.extend(node_block(n, n["_x"], n["_y"], n["_w"], n["_h"]))
    # Labels paint last so a short edge does not hide its own label under a box.
    body.extend(labels)

    # Group rects extend beyond their members, so size the canvas from the real
    # drawn extent and shift content back to a uniform margin.
    min_x = min(e[0] for e in extents)
    min_y = min(e[1] for e in extents)
    max_x = max(e[2] for e in extents)
    max_y = max(e[3] for e in extents)
    dx, dy = pad - min_x, pad - min_y
    offset = (dx, dy) if (abs(dx) > 0.01 or abs(dy) > 0.01) else None

    return body, (max_x - min_x) + pad * 2, (max_y - min_y) + pad * 2, offset


def layout_stack(spec):
    """Vertical tiers, optionally each holding a row of items."""
    tiers = spec["tiers"]
    pad = THEME["pad"]
    gap = 10
    tier_w = spec.get("width", 460)

    rendered, y = [], pad
    for tier in tiers:
        items = tier.get("items", [])
        node = {"label": tier.get("label", ""), "sublabel": tier.get("sublabel"),
                "emphasis": tier.get("emphasis", "default")}
        measure_node(node, max_width=tier_w)
        text_h = (
            len(node["_label_lines"]) * THEME["size_label"] * THEME["line_height"]
            + len(node["_sub_lines"]) * THEME["size_sub"] * THEME["line_height"]
        )
        chips = wrap_text("  ·  ".join(items), THEME["size_sub"], tier_w - 24,
                          max_lines=2) if items else []
        sub_lh = THEME["size_sub"] * THEME["line_height"]
        h = max(THEME["node_h"], text_h + 18) + (len(chips) * sub_lh + 8 if chips else 0)

        rendered.extend(node_block(node, pad, y, tier_w, h,
                                   centre_within=h - len(chips) * sub_lh))
        cursor = y + h - len(chips) * sub_lh - 4
        for line in chips:
            cursor += sub_lh
            rendered.append(text(pad + tier_w / 2, cursor, line,
                                 THEME["size_sub"], THEME["text_muted"]))
        y += h + gap

    return rendered, tier_w + pad * 2, y - gap + pad, None


def layout_timeline(spec):
    """Sequential phase bands joined by arrows."""
    phases = spec["phases"]
    pad = THEME["pad"]
    gap = 34

    sub_lh = THEME["size_sub"] * THEME["line_height"]
    for p in phases:
        p["label"] = p.get("label", "")
        p["_w"], p["_h"] = measure_node(p, max_width=190)
        p["_chips"] = (wrap_text("  ·  ".join(p["items"]), THEME["size_sub"],
                                 p["_w"] - 16, max_lines=3) if p.get("items") else [])
    band_h = max(p["_h"] for p in phases)
    item_h = max([14 + len(p["_chips"]) * sub_lh for p in phases if p["_chips"]] or [0])

    body, x = [], pad
    positions = []
    for p in phases:
        positions.append((x, p["_w"]))
        body.extend(node_block(p, x, pad, p["_w"], band_h))
        cursor = pad + band_h + 14
        for line in p["_chips"]:
            body.append(text(x + p["_w"] / 2, cursor, line,
                             THEME["size_sub"], THEME["text_muted"]))
            cursor += sub_lh
        x += p["_w"] + gap

    for i in range(len(positions) - 1):
        ax = positions[i][0] + positions[i][1]
        bx = positions[i + 1][0]
        y = pad + band_h / 2
        body.append(edge_path(ax, y, bx, y, "right", "left"))

    return body, x - gap + pad, pad * 2 + band_h + item_h, None


def layout_hub(spec):
    """Centre node with satellites placed on an ellipse (studio relates-to shape)."""
    centre = dict(spec["centre"])
    centre.setdefault("emphasis", "accent")
    satellites = [dict(s) for s in spec["satellites"]]

    cw, ch = measure_node(centre, max_width=200)
    for s in satellites:
        s["_w"], s["_h"] = measure_node(s, max_width=190)

    max_sw = max(s["_w"] for s in satellites)
    max_sh = max(s["_h"] for s in satellites)
    count = len(satellites)

    # Radii must clear half the centre plus half a satellite, with enough slack
    # left over for an edge label to sit between them.
    rx = max(190.0, (cw + max_sw) / 2 + 92, count * 26.0)
    ry = max(130.0, (ch + max_sh) / 2 + 58, count * 17.0)
    pad = THEME["pad"]

    cx = pad + max_sw / 2 + rx
    cy = pad + max_sh / 2 + ry
    width, height = cx * 2, cy * 2

    for i, s in enumerate(satellites):
        angle = (2 * math.pi * i / count) - math.pi / 2
        s["_cx"] = cx + rx * math.cos(angle)
        s["_cy"] = cy + ry * math.sin(angle)
        s["_x"] = s["_cx"] - s["_w"] / 2
        s["_y"] = s["_cy"] - s["_h"] / 2

    def rect_edge(ox, oy, hw, hh, tx, ty):
        dx, dy = tx - ox, ty - oy
        if dx == 0 and dy == 0:
            return ox, oy
        sx = hw / abs(dx) if dx else 1e9
        sy = hh / abs(dy) if dy else 1e9
        s = min(sx, sy)
        return ox + dx * s, oy + dy * s

    body, labels = [], []
    for s in satellites:
        x1, y1 = rect_edge(cx, cy, cw / 2, ch / 2, s["_cx"], s["_cy"])
        x2, y2 = rect_edge(s["_cx"], s["_cy"], s["_w"] / 2, s["_h"] / 2, cx, cy)
        body.append({"t": "path", "x1": x1, "y1": y1, "cp1x": x1, "cp1y": y1,
                     "cp2x": x2, "cp2y": y2, "x2": x2, "y2": y2, "straight": True})
        labels.extend(edge_label((x1 + x2) / 2, (y1 + y2) / 2, s.get("edgeLabel")))

    body.extend(node_block(centre, cx - cw / 2, cy - ch / 2, cw, ch))
    for s in satellites:
        body.extend(node_block(s, s["_x"], s["_y"], s["_w"], s["_h"]))

    # Labels paint last so a short edge does not hide its own label under a box.
    return body + labels, width, height, None


def layout_matrix(spec):
    """A grid with row and column headers. Zachman, pace layering, heat maps.

    Cells carry a `role`, which is how a capability map becomes a heat map
    without the spec ever naming a colour.
    """
    columns = spec["columns"]
    rows = spec["rows"]
    pad = THEME["pad"]
    gap = 6
    cell_w = spec.get("cellWidth", 150)
    head_w = spec.get("headerWidth", 130)

    def measure(entry, width):
        node = dict(entry)
        node["label"] = node.get("label", "")
        node["_w"], node["_h"] = measure_node(node, max_width=width)
        return node

    col_nodes = [measure(c, cell_w) for c in columns]
    row_nodes = [measure(r, head_w) for r in rows]

    # One height per row, driven by its tallest cell, so the grid stays square.
    row_heights, grid = [], []
    for row in rows:
        raw = row.get("cells", [])
        cells = [measure(raw[i], cell_w) if i < len(raw) and raw[i] else None
                 for i in range(len(columns))]
        row_heights.append(max([THEME["node_h"]]
                               + [c["_h"] for c in cells if c]))
        grid.append(cells)

    head_h = max([THEME["node_h"] * 0.8] + [c["_h"] for c in col_nodes])

    body = []
    x0 = pad + head_w + gap
    y0 = pad + head_h + gap

    for i, col in enumerate(col_nodes):
        cx = x0 + i * (cell_w + gap)
        col.setdefault("emphasis", "muted")
        body.extend(node_block(col, cx, pad, cell_w, head_h))

    y = y0
    for r, row in enumerate(row_nodes):
        row.setdefault("emphasis", "muted")
        body.extend(node_block(row, pad, y, head_w, row_heights[r]))
        for c, cell in enumerate(grid[r]):
            cx = x0 + c * (cell_w + gap)
            if cell is None:
                # An empty cell is drawn, faintly. In a Zachman audit the gap
                # is the finding, so it has to be visible as a gap.
                body.append(rect(cx, y, cell_w, row_heights[r],
                                 THEME["canvas"], THEME["band_stroke"], 1,
                                 THEME["radius_node"]))
                continue
            cell.setdefault("shape", "rect")
            body.extend(node_block(cell, cx, y, cell_w, row_heights[r]))
        y += row_heights[r] + gap

    width = x0 + len(columns) * (cell_w + gap) - gap + pad
    height = y - gap + pad

    legend = spec.get("legend", [])
    if legend:
        body.extend(_legend(legend, pad, height - pad + 10, width - pad * 2))
        height += 30

    return body, width, height, None


def _legend(entries, x, y, max_width):
    """A row of swatch-and-label pairs. Required whenever a role carries
    meaning the reader cannot infer — a heat scale most of all."""
    out = []
    swatch, gap, text_gap = 12, 18, 6
    cursor = x
    for entry in entries:
        fill, stroke = ROLES[entry["role"]]
        label = entry.get("label", entry["role"])
        out.append(rect(cursor, y, swatch, swatch, fill, stroke,
                        THEME["stroke_default"], 2))
        cursor += swatch + text_gap
        out.append(text(cursor, y + swatch - 2, label, THEME["size_sub"],
                        THEME["text_muted"], anchor="start"))
        cursor += text_width(label, THEME["size_sub"]) + gap
    return out


# Wardley's horizontal axis. Four phases of evolution, each occupying a
# quarter of the span, labelled along the bottom.
EVOLUTION_BANDS = (
    (0.00, "Genesis"), (0.25, "Custom-built"),
    (0.50, "Product"), (0.75, "Commodity"),
)


def layout_wardley(spec):
    """Components on a value-chain / evolution grid.

    Visibility runs 0 (invisible infrastructure) to 1 (the user anchor) up the
    y axis; evolution runs 0 (genesis) to 1 (commodity) along x. Components
    are dots with labels beside them, not boxes — a Wardley map is read as a
    landscape, and boxes make it look like a flow.
    """
    components = spec["components"]
    pad = THEME["pad"]
    plot_w = spec.get("width", 760)
    plot_h = spec.get("height", 420)
    left = pad + 86          # room for the y axis caption
    top = pad + 24
    bottom = top + plot_h

    def px(component):
        return left + plot_w * max(0.0, min(1.0, component.get("evolution", 0.0)))

    def py(component):
        return bottom - plot_h * max(0.0, min(1.0, component.get("visibility", 0.0)))

    body = []

    # Evolution bands, drawn first so everything else sits over them.
    for frac, label in EVOLUTION_BANDS:
        bx = left + plot_w * frac
        if frac > 0:
            body.append({"t": "path", "x1": bx, "y1": top, "cp1x": bx, "cp1y": top,
                         "cp2x": bx, "cp2y": bottom, "x2": bx, "y2": bottom,
                         "straight": True, "arrow": "none", "dash": "dotted"})
        body.append(text(bx + 6, bottom + 16, label, THEME["size_sub"],
                         THEME["text_muted"], anchor="start"))

    # Axes.
    for x1, y1, x2, y2 in ((left, top, left, bottom), (left, bottom, left + plot_w, bottom)):
        body.append({"t": "path", "x1": x1, "y1": y1, "cp1x": x1, "cp1y": y1,
                     "cp2x": x2, "cp2y": y2, "x2": x2, "y2": y2,
                     "straight": True, "arrow": "none"})
    body.append(text(left - 10, top + 10, "Visible", THEME["size_sub"],
                     THEME["text_muted"], anchor="end"))
    body.append(text(left - 10, bottom, "Invisible", THEME["size_sub"],
                     THEME["text_muted"], anchor="end"))
    body.append(text(left + plot_w, bottom + 32, "Evolution →", THEME["size_sub"],
                     THEME["text_muted"], anchor="end"))
    # The anchor names whose value chain this is. It is the one piece of a
    # Wardley map that cannot be read off the axes, so it is stated, not drawn.
    if spec.get("anchor"):
        body.append(text(left, pad + 8, f"Value chain for {spec['anchor']}",
                         THEME["size_sub"], THEME["text_muted"], anchor="start"))

    by_id = {c["id"]: c for c in components}
    for edge in spec.get("edges", []):
        a, b = by_id[edge["from"]], by_id[edge["to"]]
        body.append({"t": "path", "x1": px(a), "y1": py(a), "cp1x": px(a),
                     "cp1y": py(a), "cp2x": px(b), "cp2y": py(b),
                     "x2": px(b), "y2": py(b), "straight": True, "arrow": "none"})

    for move in spec.get("movements", []):
        c = by_id[move["from"]]
        target = left + plot_w * max(0.0, min(1.0, move["to"]))
        body.append({"t": "path", "x1": px(c) + 9, "y1": py(c), "cp1x": px(c) + 9,
                     "cp1y": py(c), "cp2x": target, "cp2y": py(c),
                     "x2": target, "y2": py(c), "straight": True, "dash": "dashed"})

    labels = []
    for c in components:
        cx, cy = px(c), py(c)
        fill, stroke, weight = resolve_style(c)
        dot = 11
        body.append(rect(cx - dot / 2, cy - dot / 2, dot, dot, fill, stroke,
                         weight, dot / 2, shape="event"))
        labels.append(text(cx, cy - 11, c.get("label", ""), THEME["size_label"],
                           THEME["text"], "600"))
        if c.get("sublabel"):
            labels.append(text(cx, cy + 20, c["sublabel"], THEME["size_sub"],
                               THEME["text_muted"]))

    return body + labels, left + plot_w + pad, bottom + 44 + pad, None


def layout_swimlane(spec):
    """Lanes of steps, left to right, with edges crossing between them.

    Columns are ranked from the edge graph exactly as `flow` does, so an
    author writes the handoffs and the engine lines the steps up.
    """
    lanes = spec["lanes"]
    edges = spec.get("edges", [])
    pad = THEME["pad"]
    head_w = THEME["lane_header"]
    col_gap = 44
    lane_pad = 14

    steps, lane_of = [], {}
    for index, lane in enumerate(lanes):
        for step in lane.get("steps", []):
            steps.append(step)
            lane_of[step["id"]] = index
    by_id = {s["id"]: s for s in steps}

    incoming = {s["id"]: [] for s in steps}
    for e in edges:
        incoming[e["to"]].append(e["from"])

    column = {s["id"]: s["column"] for s in steps if "column" in s}

    def resolve(sid, seen):
        if sid in column:
            return column[sid]
        if sid in seen or not incoming[sid]:
            column[sid] = 0
            return 0
        column[sid] = 1 + max(resolve(p, seen | {sid}) for p in incoming[sid])
        return column[sid]

    for s in steps:
        resolve(s["id"], set())

    for s in steps:
        s["_w"], s["_h"] = measure_node(s, max_width=THEME["node_w_max"])

    col_count = max(column.values()) + 1 if column else 1
    col_w = [max([s["_w"] for s in steps if column[s["id"]] == c] or [THEME["node_w"]])
             for c in range(col_count)]
    col_x = []
    cursor = pad + head_w
    for width in col_w:
        col_x.append(cursor + lane_pad)
        cursor += width + lane_pad * 2 + col_gap
    total_w = cursor - col_gap + pad

    lane_h, lane_y = [], []
    y = pad
    for index, lane in enumerate(lanes):
        members = [s for s in steps if lane_of[s["id"]] == index]
        # A lane holding two steps in one column has to grow to hold both.
        stacked = {}
        for s in members:
            stacked.setdefault(column[s["id"]], []).append(s)
        height = max(
            [THEME["node_h"] + lane_pad * 2]
            + [sum(x["_h"] for x in group) + lane_pad * (len(group) + 1)
               for group in stacked.values()]
        )
        lane_y.append(y)
        lane_h.append(height)
        for group in stacked.values():
            block = sum(x["_h"] for x in group) + 10 * (len(group) - 1)
            top = y + (height - block) / 2
            for s in group:
                s["_x"] = col_x[column[s["id"]]]
                s["_y"] = top
                top += s["_h"] + 10
        y += height

    body = []
    for index, lane in enumerate(lanes):
        fill = THEME["lane_fill"] if index % 2 == 0 else THEME["canvas"]
        body.append(rect(pad, lane_y[index], total_w - pad * 2, lane_h[index],
                         fill, THEME["band_stroke"], 1, 0))
        body.append(rect(pad, lane_y[index], head_w, lane_h[index],
                         THEME["group_fill"], THEME["band_stroke"], 1, 0))
        caption = {"label": lane.get("label", ""), "emphasis": "muted"}
        measure_node(caption, max_width=head_w)
        for i, line in enumerate(caption["_label_lines"]):
            body.append(text(pad + head_w / 2,
                             lane_y[index] + lane_h[index] / 2 + i * 14
                             - (len(caption["_label_lines"]) - 1) * 7 + 4,
                             line, THEME["size_label"], THEME["text"], "600"))

    labels = []
    for e in edges:
        a, b = by_id[e["from"]], by_id[e["to"]]
        same_lane = lane_of[e["from"]] == lane_of[e["to"]]
        if same_lane:
            x1, y1 = a["_x"] + a["_w"], a["_y"] + a["_h"] / 2
            x2, y2 = b["_x"], b["_y"] + b["_h"] / 2
            exit_dir, entry_dir = "right", "left"
        elif b["_y"] > a["_y"]:
            x1, y1 = a["_x"] + a["_w"] / 2, a["_y"] + a["_h"]
            x2, y2 = b["_x"] + b["_w"] / 2, b["_y"]
            exit_dir, entry_dir = "bottom", "top"
        else:
            x1, y1 = a["_x"] + a["_w"] / 2, a["_y"]
            x2, y2 = b["_x"] + b["_w"] / 2, b["_y"] + b["_h"]
            exit_dir, entry_dir = "top", "bottom"
        body.append(edge_path(x1, y1, x2, y2, exit_dir, entry_dir,
                              e.get("dash"), e.get("arrow")))
        labels.extend(edge_label((x1 + x2) / 2, (y1 + y2) / 2, e.get("label")))

    for s in steps:
        body.extend(node_block(s, s["_x"], s["_y"], s["_w"], s["_h"]))
    body.extend(labels)

    return body, total_w, y + pad, None


# Event Storming reads top to bottom in a fixed order, so the same kind of
# sticky lands on the same row in every column. A facilitator scans one row to
# follow the commands, another to follow the events.
STORM_ROWS = ("storm.actor", "storm.command", "storm.aggregate", "storm.event",
              "storm.policy", "storm.readmodel", "storm.external",
              "storm.hotspot")

STORM_ROW_LABEL = {
    "storm.actor": "Actors", "storm.command": "Commands",
    "storm.aggregate": "Aggregates", "storm.event": "Events",
    "storm.policy": "Policies", "storm.readmodel": "Read models",
    "storm.external": "External", "storm.hotspot": "Hot spots",
}


def layout_canvas(spec):
    """An Event Storming wall: a left-to-right timeline of coloured stickies.

    Only the rows actually used are drawn, so a big-picture session showing
    events and hot spots does not carry six empty bands.
    """
    columns = spec["columns"]
    pad = THEME["pad"]
    sticky_w = spec.get("stickyWidth", 128)
    col_gap, row_gap, stack_gap = 14, 12, 8
    head_w = 92

    for col in columns:
        for sticky in col.get("stickies", []):
            sticky.setdefault("role", "storm.event")
            sticky.setdefault("shape", "sticky")
            # An actor is physically a smaller sticky on a real wall, which is
            # most of how it is told apart from a pale-yellow aggregate.
            width = sticky_w * (0.72 if sticky["role"] == "storm.actor" else 1.0)
            sticky["_w"] = width
            measure_node(sticky, max_width=width)
            sticky["_h"] = max(
                48.0,
                len(sticky["_label_lines"]) * THEME["size_label"] * THEME["line_height"]
                + len(sticky["_sub_lines"]) * THEME["size_sub"] * THEME["line_height"]
                + 18)

    used = [r for r in STORM_ROWS
            if any(s["role"] == r for c in columns for s in c.get("stickies", []))]
    if not used:
        used = ["storm.event"]

    row_h = {}
    for role in used:
        tallest = 0.0
        for col in columns:
            group = [s for s in col.get("stickies", []) if s["role"] == role]
            if group:
                tallest = max(tallest,
                              sum(s["_h"] for s in group)
                              + stack_gap * (len(group) - 1))
        row_h[role] = max(48.0, tallest)

    body, labels = [], []
    header_h = 26 if any(c.get("label") for c in columns) else 0
    y0 = pad + header_h
    row_y, y = {}, y0
    for role in used:
        row_y[role] = y
        body.append(text(pad, y + row_h[role] / 2 + 3, STORM_ROW_LABEL[role],
                         THEME["size_sub"], THEME["text_muted"], anchor="start"))
        y += row_h[role] + row_gap
    total_h = y - row_gap + pad

    x = pad + head_w
    for col in columns:
        if col.get("label"):
            labels.append(text(x + sticky_w / 2, pad + 14, col["label"],
                               THEME["size_group"], THEME["text"], "600"))
        for role in used:
            group = [s for s in col.get("stickies", []) if s["role"] == role]
            cursor = row_y[role]
            for sticky in group:
                body.extend(node_block(sticky, x + (sticky_w - sticky["_w"]) / 2,
                                       cursor, sticky["_w"], sticky["_h"]))
                cursor += sticky["_h"] + stack_gap
        x += sticky_w + col_gap

    return body + labels, x - col_gap + pad, total_h, None


LAYOUT_FUNCS = {
    "flow": layout_flow,
    "stack": layout_stack,
    "timeline": layout_timeline,
    "hub": layout_hub,
    "matrix": layout_matrix,
    "wardley": layout_wardley,
    "swimlane": layout_swimlane,
    "canvas": layout_canvas,
}


# --------------------------------------------------------------------------
# Validation and scene assembly
# --------------------------------------------------------------------------

def validate(spec):
    """Return a list of human-readable problems with the spec."""
    problems = []
    layout = spec.get("layout")
    if layout not in LAYOUTS:
        problems.append(f"layout must be one of {', '.join(LAYOUTS)} (got {layout!r})")
        return problems

    if layout == "flow":
        nodes = spec.get("nodes")
        if not nodes:
            problems.append("flow layout requires a non-empty 'nodes' array")
            return problems
        ids, seen = set(), set()
        for n in nodes:
            nid = n.get("id")
            if not nid:
                problems.append("every node needs an 'id'")
            elif nid in seen:
                problems.append(f"duplicate node id {nid!r}")
            else:
                seen.add(nid)
            ids.add(nid)
        group_ids = {g.get("id") for g in spec.get("groups", [])}
        for n in nodes:
            if n.get("group") and n["group"] not in group_ids:
                problems.append(f"node {n.get('id')!r} references unknown group {n['group']!r}")
        for e in spec.get("edges", []):
            for end in ("from", "to"):
                if e.get(end) not in ids:
                    problems.append(f"edge {end} {e.get(end)!r} is not a declared node id")
    elif layout == "stack" and not spec.get("tiers"):
        problems.append("stack layout requires a non-empty 'tiers' array")
    elif layout == "timeline" and not spec.get("phases"):
        problems.append("timeline layout requires a non-empty 'phases' array")
    elif layout == "hub":
        if not spec.get("centre"):
            problems.append("hub layout requires a 'centre' object")
        if not spec.get("satellites"):
            problems.append("hub layout requires a non-empty 'satellites' array")
    elif layout == "matrix":
        if not spec.get("columns"):
            problems.append("matrix layout requires a non-empty 'columns' array")
        if not spec.get("rows"):
            problems.append("matrix layout requires a non-empty 'rows' array")
        for i, row in enumerate(spec.get("rows", [])):
            overflow = len(row.get("cells", [])) - len(spec.get("columns", []))
            if overflow > 0:
                problems.append(
                    f"row {i} ({row.get('label', '?')!r}) has {overflow} more "
                    f"cell(s) than there are columns")
        for entry in spec.get("legend", []):
            if entry.get("role") not in ROLES:
                problems.append(f"legend entry has unknown role {entry.get('role')!r}")
    elif layout == "wardley":
        components = spec.get("components")
        if not components:
            problems.append("wardley layout requires a non-empty 'components' array")
            return problems
        ids = set()
        for c in components:
            if not c.get("id"):
                problems.append("every wardley component needs an 'id'")
            ids.add(c.get("id"))
            for axis in ("visibility", "evolution"):
                value = c.get(axis)
                if value is None:
                    problems.append(
                        f"component {c.get('id')!r} needs a '{axis}' between 0 and 1")
                elif not 0 <= value <= 1:
                    problems.append(
                        f"component {c.get('id')!r} has {axis} {value}, "
                        "which is outside 0 to 1")
        for e in spec.get("edges", []):
            for end in ("from", "to"):
                if e.get(end) not in ids:
                    problems.append(f"edge {end} {e.get(end)!r} is not a component id")
        for m in spec.get("movements", []):
            if m.get("from") not in ids:
                problems.append(f"movement from {m.get('from')!r} is not a component id")
    elif layout == "swimlane":
        lanes = spec.get("lanes")
        if not lanes:
            problems.append("swimlane layout requires a non-empty 'lanes' array")
            return problems
        ids, seen = set(), set()
        for lane in lanes:
            for step in lane.get("steps", []):
                sid = step.get("id")
                if not sid:
                    problems.append("every swimlane step needs an 'id'")
                elif sid in seen:
                    problems.append(f"duplicate step id {sid!r}")
                else:
                    seen.add(sid)
                ids.add(sid)
        if not ids:
            problems.append("swimlane layout needs at least one step in a lane")
        for e in spec.get("edges", []):
            for end in ("from", "to"):
                if e.get(end) not in ids:
                    problems.append(f"edge {end} {e.get(end)!r} is not a declared step id")
    elif layout == "canvas":
        columns = spec.get("columns")
        if not columns:
            problems.append("canvas layout requires a non-empty 'columns' array")
            return problems
        if not any(c.get("stickies") for c in columns):
            problems.append("canvas layout needs at least one sticky")
        for col in columns:
            for sticky in col.get("stickies", []):
                role = sticky.get("role", "storm.event")
                if role not in STORM_ROWS:
                    problems.append(
                        f"sticky {sticky.get('label', '?')!r} has role {role!r}; "
                        f"a canvas takes one of {', '.join(STORM_ROWS)}")

    problems += _check_vocabulary(spec)
    return problems


def _nodes_anywhere(spec):
    """Every node-shaped object in a spec, whatever the layout calls them."""
    found = []
    for key in ("nodes", "satellites", "tiers", "phases", "components",
                "columns", "rows"):
        found += [n for n in spec.get(key, []) if isinstance(n, dict)]
    for lane in spec.get("lanes", []):
        found += [n for n in lane.get("steps", []) if isinstance(n, dict)]
    for row in spec.get("rows", []):
        found += [c for c in row.get("cells", []) if isinstance(c, dict)]
    for col in spec.get("columns", []):
        if isinstance(col, dict):
            found += [s for s in col.get("stickies", []) if isinstance(s, dict)]
    if isinstance(spec.get("centre"), dict):
        found.append(spec["centre"])
    return found


def _check_vocabulary(spec):
    """Emphasis, role, shape and connector styling, across every layout."""
    problems = []
    for item in _nodes_anywhere(spec):
        emphasis = item.get("emphasis", "default")
        if emphasis not in EMPHASIS:
            problems.append(f"unknown emphasis {emphasis!r} "
                            f"(use one of {', '.join(EMPHASIS)})")
        if "role" in item and item["role"] not in ROLES:
            problems.append(f"unknown role {item['role']!r} "
                            f"(use one of {', '.join(sorted(ROLES))})")
        if "shape" in item and item["shape"] not in SHAPES:
            problems.append(f"unknown shape {item['shape']!r} "
                            f"(use one of {', '.join(SHAPES)})")
    for e in spec.get("edges", []):
        if "dash" in e and e["dash"] not in DASHES:
            problems.append(f"unknown dash {e['dash']!r} "
                            f"(use one of {', '.join(DASHES)})")
        if "arrow" in e and e["arrow"] not in ARROWS:
            problems.append(f"unknown arrow {e['arrow']!r} "
                            f"(use one of {', '.join(ARROWS)})")
    return problems


def build_scene(spec):
    """Lay a spec out. Returns a Scene dict."""
    items, width, height, offset = LAYOUT_FUNCS[spec["layout"]](spec)
    return {"items": items, "width": width, "height": height, "offset": offset}


# --------------------------------------------------------------------------
# Aspect fitting
# --------------------------------------------------------------------------

def _fill_score(scene_w, scene_h, target_ratio):
    """How much of a target box a scene fills once scaled to fit it.

    1.0 means it fills the box exactly; 0.25 means three quarters of the box
    is whitespace. Scale-invariant, so it compares shapes rather than sizes.
    """
    if scene_w <= 0 or scene_h <= 0:
        return 0.0
    scene_ratio = scene_w / scene_h
    return min(scene_ratio / target_ratio, target_ratio / scene_ratio)


POOR_FIT = 0.45


def fit_to_aspect(spec, target_ratio):
    """Reshape a flow to fill a target aspect ratio as well as it can.

    Returns (spec, note). Only `flow` can be reshaped; the other layouts are
    returned untouched and are simply scaled to fit by the caller.

    Both orientations are laid out and scored; the better one wins. Each holds
    the same nodes, edges and labels, so the flip is lossless — that is what
    makes applying it unattended reasonable.

    Transposition helps less often than it looks like it should. Each extra
    rank costs a node width (160-220px) in LR but only a node height (48-66px)
    in TB, so flipping a *deep* flow yields a thin ribbon that scores worse
    than the original: across the three Lightwell topologies TB won every time.
    The flip pays off only for a shallow flow with wide ranks.

    When neither orientation fits, this says so rather than reshaping harder.
    Wrapping a deep flow into columns does fill the frame - it took one
    seven-rank topology from 23% to 77% - but cross-column edges have no sane
    route and loop off the canvas, and a cluster group cannot span columns. A
    diagram that will not fit a slide is usually a diagram carrying more than
    one idea, and that fix belongs with the author.
    """
    if spec.get("layout") != "flow":
        return spec, None

    current = spec.get("direction", "TB").upper()
    other = "LR" if current == "TB" else "TB"
    candidates = [
        (dict(spec), None),
        (dict(spec, direction=other), f"transposed {current}→{other}"),
    ]

    scored = []
    for candidate, note in candidates:
        scene = build_scene(dict(candidate))
        scored.append((_fill_score(scene["width"], scene["height"], target_ratio),
                       candidate, note))

    base_score = scored[0][0]
    best_score, best_spec, best_note = max(scored, key=lambda row: row[0])

    # Only reshape for a clear win. A marginal gain is not worth changing a
    # reading order the audience may already know from the report.
    if best_note and best_score > base_score * 1.25:
        note = (f"{best_note} to fit the frame "
                f"({base_score:.0%}→{best_score:.0%} of it used)")
        return best_spec, note

    if base_score < POOR_FIT:
        return spec, (
            f"fills only {base_score:.0%} of the frame and no reshape improves "
            f"it — consider splitting this diagram across slides or raising "
            f"its level of abstraction"
        )
    return spec, None


# --------------------------------------------------------------------------
# SVG source introspection (used when sizing a raster for a target box)
# --------------------------------------------------------------------------

def svg_aspect(path):
    """Height / width for an SVG, from its viewBox or width+height."""
    root = ET.parse(path).getroot()

    box = root.get("viewBox")
    if box:
        parts = box.replace(",", " ").split()
        if len(parts) == 4:
            width, height = float(parts[2]), float(parts[3])
            if width > 0:
                return height / width

    def dim(name):
        raw = (root.get(name) or "").strip().rstrip("px")
        return float(raw) if raw else 0.0

    width, height = dim("width"), dim("height")
    if width > 0 and height > 0:
        return height / width
    raise ValueError(f"{path}: no viewBox or width/height to size from")
