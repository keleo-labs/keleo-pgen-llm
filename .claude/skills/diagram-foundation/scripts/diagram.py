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


def use_palette(name):
    """Switch the colour family in place. Returns the palette applied.

    THEME and EMPHASIS are mutated rather than rebound because the backends
    bind them at import (`from diagram import THEME`); rebinding here would
    leave them pointing at the old dict.
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
    return palette

LAYOUTS = ("flow", "stack", "timeline", "hub")


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

def rect(x, y, w, h, fill, stroke, sw, radius, opacity=None):
    return {"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill,
            "stroke": stroke, "sw": sw, "radius": radius, "opacity": opacity}


def text(x, y, s, size, fill, weight="400", anchor="middle"):
    return {"t": "text", "x": x, "y": y, "s": s, "size": size, "fill": fill,
            "weight": weight, "anchor": anchor}


def node_block(node, x, y, w, h, centre_within=None):
    """Rounded rect plus wrapped label and optional sublabel.

    centre_within limits the band the text is centred in, measured from y.
    Callers that reserve space at the bottom of the box (stack tiers listing
    items) pass it so the label does not drift down into that space.
    """
    fill, stroke, stroke_width = EMPHASIS[node.get("emphasis", "default")]
    out = [rect(x, y, w, h, fill, stroke, stroke_width, THEME["radius_node"])]

    label_lines = node["_label_lines"]
    sub_lines = node.get("_sub_lines", [])
    lh = THEME["size_label"] * THEME["line_height"]
    sub_lh = THEME["size_sub"] * THEME["line_height"]

    block_h = len(label_lines) * lh + (len(sub_lines) * sub_lh if sub_lines else 0)
    band = centre_within if centre_within is not None else h
    cursor = y + (band - block_h) / 2 + THEME["size_label"] * 0.85
    cx = x + w / 2

    for line in label_lines:
        out.append(text(cx, cursor, line, THEME["size_label"], THEME["text"], "600"))
        cursor += lh
    for line in sub_lines:
        out.append(text(cx, cursor, line, THEME["size_sub"], THEME["text_muted"]))
        cursor += sub_lh
    return out


def measure_node(node, max_width=None):
    """Attach wrapped lines to a node and return its (width, height)."""
    max_width = max_width or THEME["node_w_max"]
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
    w = max(THEME["node_w"], min(max_width, widest + 28))
    content_h = (
        len(node["_label_lines"]) * THEME["size_label"] * THEME["line_height"]
        + len(node["_sub_lines"]) * THEME["size_sub"] * THEME["line_height"]
    )
    h = max(THEME["node_h"], content_h + 18)
    return w, h


def edge_path(x1, y1, x2, y2, exit_dir, entry_dir):
    """Cubic bezier mirroring computeEdgePath in the studio navigator."""
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
    return {"t": "path", "x1": x1, "y1": y1, "cp1x": cp1x, "cp1y": cp1y,
            "cp2x": cp2x, "cp2y": cp2y, "x2": x2, "y2": y2}


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

    cursor = pad
    for position, idx in enumerate(sorted(layers)):
        members = layers[idx]
        offset = pad + (breadth - breadth_extent[position]) / 2
        for n in members:
            if horizontal:
                n["_x"], n["_y"] = cursor, offset
                offset += n["_h"] + cross_gap
            else:
                n["_x"], n["_y"] = offset, cursor
                offset += n["_w"] + cross_gap
        cursor += layer_extent[position] + layer_gap

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
            gh = max(n["_y"] + n["_h"] for n in members) + THEME["group_pad_x"] - gy
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
        body.append(edge_path(x1, y1, x2, y2, exit_dir, entry_dir))
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


LAYOUT_FUNCS = {
    "flow": layout_flow,
    "stack": layout_stack,
    "timeline": layout_timeline,
    "hub": layout_hub,
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

    for item in spec.get("nodes", []) + spec.get("satellites", []):
        emphasis = item.get("emphasis", "default")
        if emphasis not in EMPHASIS:
            problems.append(f"unknown emphasis {emphasis!r} "
                            f"(use one of {', '.join(EMPHASIS)})")
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
