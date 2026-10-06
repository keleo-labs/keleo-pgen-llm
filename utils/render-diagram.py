#!/usr/bin/env python3
"""Render declarative diagram specs into styled SVG for markdown reports.

Four layouts cover what reports need: flow (layered boxes and directed edges),
stack (vertical tiers), timeline (sequential phases), hub (centre plus
satellites). The visual language is lifted from the keleo-studio-gas navigator
diagrams so reports, the studio UI, and the deck theme read as one system.

Two deliberate divergences from the studio implementation:

  * Studio labels nodes with foreignObject holding HTML. A standalone .svg
    loaded through a markdown <img> does not render foreignObject content in
    most browsers, so labels here are native <text>/<tspan> with wrapping done
    in this module.
  * Each diagram paints an opaque background rect. GitHub renders images
    against both light and dark page backgrounds and a transparent canvas
    makes dark text vanish on the dark theme.

Usage:
    python3 utils/render-diagram.py <spec>.json -o <out>.svg
    python3 utils/render-diagram.py <spec>.json --stdout
    python3 utils/render-diagram.py --dir reports/assets/<report-slug>/
    python3 utils/render-diagram.py --spec-help
"""

import argparse
import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json_pair  # noqa: E402


# --------------------------------------------------------------------------
# Design tokens — keleo-studio-gas navigator (src/scripts/views/Navigator*.html,
# src/templates/navigator.html, src/styles/navigator.html)
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
    "size_title": 13,
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
# SVG primitives
# --------------------------------------------------------------------------

def _fmt(value):
    """Trim float noise so the output diffs cleanly."""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def svg_rect(x, y, w, h, fill, stroke, stroke_width, radius, opacity=None):
    parts = [
        f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}"',
        f'rx="{radius}" ry="{radius}" fill="{fill}" stroke="{stroke}"',
        f'stroke-width="{_fmt(stroke_width)}"',
    ]
    if opacity is not None:
        parts.append(f'opacity="{opacity}"')
    return "  " + " ".join(parts) + " />"


def svg_text(x, y, content, size, fill, weight="400", anchor="middle"):
    return (
        f'  <text x="{_fmt(x)}" y="{_fmt(y)}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}" '
        f'font-family="{escape(THEME["font"], {chr(34): "&quot;"})}">'
        f"{escape(content)}</text>"
    )


def node_block(node, x, y, w, h, centre_within=None):
    """Rounded rect plus wrapped label and optional sublabel.

    centre_within limits the band the text is centred in, measured from y.
    Callers that reserve space at the bottom of the box (stack tiers listing
    items) pass it so the label does not drift down into that space.
    """
    fill, stroke, stroke_width = EMPHASIS[node.get("emphasis", "default")]
    out = [svg_rect(x, y, w, h, fill, stroke, stroke_width, THEME["radius_node"])]

    label_lines = node["_label_lines"]
    sub_lines = node.get("_sub_lines", [])
    lh = THEME["size_label"] * THEME["line_height"]
    sub_lh = THEME["size_sub"] * THEME["line_height"]

    block_h = len(label_lines) * lh + (len(sub_lines) * sub_lh if sub_lines else 0)
    band = centre_within if centre_within is not None else h
    cursor = y + (band - block_h) / 2 + THEME["size_label"] * 0.85
    cx = x + w / 2

    for line in label_lines:
        out.append(svg_text(cx, cursor, line, THEME["size_label"], THEME["text"], "600"))
        cursor += lh
    for line in sub_lines:
        out.append(svg_text(cx, cursor, line, THEME["size_sub"], THEME["text_muted"]))
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
    return (f'  <path d="M {_fmt(x1)} {_fmt(y1)} C {_fmt(cp1x)} {_fmt(cp1y)}, '
            f'{_fmt(cp2x)} {_fmt(cp2y)}, {_fmt(x2)} {_fmt(y2)}" fill="none" '
            f'stroke="{THEME["edge"]}" stroke-width="{THEME["edge_width"]}" '
            f'marker-end="url(#arrow)" />')


def edge_label(x, y, text):
    if not text:
        return []
    size = THEME["size_edge"]
    w = text_width(text, size) + 8
    return [
        svg_rect(x - w / 2, y - size, w, size + 5, THEME["canvas"], "none", 0, 2),
        svg_text(x, y, text, size, THEME["text_muted"]),
    ]


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
            body.append(svg_rect(gx, gy, gw, gh, THEME["group_fill"], THEME["group_stroke"],
                                 1, THEME["radius_group"], THEME["group_opacity"]))
            body.append(svg_text(gx + 8, gy + 16, group_defs[gid].get("label", gid),
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
    if abs(dx) > 0.01 or abs(dy) > 0.01:
        body = [f'  <g transform="translate({_fmt(dx)}, {_fmt(dy)})">'] + body + ["  </g>"]

    return body, (max_x - min_x) + pad * 2, (max_y - min_y) + pad * 2


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
            rendered.append(svg_text(pad + tier_w / 2, cursor, line,
                                     THEME["size_sub"], THEME["text_muted"]))
        y += h + gap

    return rendered, tier_w + pad * 2, y - gap + pad


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
            body.append(svg_text(x + p["_w"] / 2, cursor, line,
                                 THEME["size_sub"], THEME["text_muted"]))
            cursor += sub_lh
        x += p["_w"] + gap

    for i in range(len(positions) - 1):
        ax = positions[i][0] + positions[i][1]
        bx = positions[i + 1][0]
        y = pad + band_h / 2
        body.append(edge_path(ax, y, bx, y, "right", "left"))

    return body, x - gap + pad, pad * 2 + band_h + item_h


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
        body.append(
            f'  <line x1="{_fmt(x1)}" y1="{_fmt(y1)}" x2="{_fmt(x2)}" y2="{_fmt(y2)}" '
            f'stroke="{THEME["edge"]}" stroke-width="{THEME["edge_width"]}" '
            f'marker-end="url(#arrow)" />'
        )
        labels.extend(edge_label((x1 + x2) / 2, (y1 + y2) / 2, s.get("edgeLabel")))

    body.extend(node_block(centre, cx - cw / 2, cy - ch / 2, cw, ch))
    for s in satellites:
        body.extend(node_block(s, s["_x"], s["_y"], s["_w"], s["_h"]))

    # Labels paint last so a short edge does not hide its own label under a box.
    return body + labels, width, height


LAYOUT_FUNCS = {
    "flow": layout_flow,
    "stack": layout_stack,
    "timeline": layout_timeline,
    "hub": layout_hub,
}


# --------------------------------------------------------------------------
# Validation and assembly
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


def render(spec):
    """Return the SVG document for a validated spec."""
    body, width, height = LAYOUT_FUNCS[spec["layout"]](spec)

    title = spec.get("title", "")
    if title:
        lines = wrap_text(title, THEME["size_title"], width - THEME["pad"] * 2, max_lines=2)
        title_h = len(lines) * THEME["size_title"] * THEME["line_height"] + 10
        shifted = [f'  <g transform="translate(0, {_fmt(title_h)})">'] + body + ["  </g>"]
        header = []
        cursor = THEME["pad"] + THEME["size_title"]
        for line in lines:
            header.append(svg_text(width / 2, cursor, line, THEME["size_title"],
                                   THEME["text"], "700"))
            cursor += THEME["size_title"] * THEME["line_height"]
        body = header + shifted
        height += title_h

    desc = spec.get("description", title)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(width)} {_fmt(height)}" '
        f'width="{_fmt(width)}" height="{_fmt(height)}" role="img" '
        f'aria-label="{escape(desc, {chr(34): "&quot;"})}">',
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


SPEC_HELP = """\
Diagram spec reference
======================

Every spec is a JSON object with a "layout" plus optional "title" and
"description". The description becomes the SVG aria-label; it falls back to the
title when omitted.

Shared node fields (flow nodes, stack tiers, timeline phases, hub centre and
satellites all accept these):

  label      required  Short noun phrase. Wrapped to at most 3 lines.
  sublabel   optional  Secondary line in muted grey, at most 2 lines.
  emphasis   optional  default | muted | accent | selected

layout: "flow"
--------------
Layered boxes with directed edges. The workhorse: topologies, pipelines,
process flows, data paths.

  direction  "TB" (default) or "LR"
  nodes      [{id, label, sublabel?, emphasis?, group?, rank?}]
  edges      [{from, to, label?}]
  groups     [{id, label}]     draws a cluster rect behind member nodes

Rank is derived from the edge graph (longest path from a source). Setting
"rank" on a node pins that node and pushes its descendants below it; use it to
place a node that has no incoming edge, such as an out-of-band path joining
partway down.

layout: "stack"
---------------
Vertical tiers, top to bottom. Layer models, maturity stacks.

  tiers      [{label, sublabel?, emphasis?, items?: [str]}]
  width      optional band width in px (default 460)

layout: "timeline"
------------------
Sequential phase bands joined by arrows. Roadmaps, adoption journeys.

  phases     [{label, sublabel?, emphasis?, items?: [str]}]

layout: "hub"
-------------
Centre node with satellites on an ellipse. Relationship maps, fan-out.

  centre     {label, sublabel?, emphasis?}
  satellites [{label, sublabel?, emphasis?, edgeLabel?}]

Example
-------
{
  "layout": "flow",
  "direction": "TB",
  "title": "Controller-centric scheduled remediation",
  "groups": [{"id": "onprem", "label": "On-premises"}],
  "nodes": [
    {"id": "lw",   "label": "Lightwell Network",
     "sublabel": "signed packages, SBOMs", "emphasis": "accent"},
    {"id": "repo", "label": "Artifactory / Nexus", "group": "onprem"},
    {"id": "ctrl", "label": "Automation controller", "group": "onprem"}
  ],
  "edges": [
    {"from": "lw",   "to": "repo", "label": "remote repository"},
    {"from": "repo", "to": "ctrl", "label": "scheduled scan"}
  ]
}
"""


def render_file(spec_path, out_path):
    """Render one spec file. Returns (ok, message)."""
    spec, error = load_json_pair(spec_path)
    if error:
        return False, error
    problems = validate(spec)
    if problems:
        return False, f"{spec_path}: " + "; ".join(problems)
    try:
        svg = render(spec)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return False, f"{spec_path}: could not render ({exc})"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    return True, f"{out_path} ({svg.count(chr(10))} lines)"


def main():
    parser = argparse.ArgumentParser(
        description="Render diagram specs into styled SVG for markdown reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run --spec-help for the full spec reference.",
    )
    parser.add_argument("spec", nargs="?", help="Path to a diagram spec JSON file")
    parser.add_argument("-o", "--output", help="Output SVG path (default: spec path with .svg)")
    parser.add_argument("--dir", dest="directory",
                        help="Render every *.json spec in a directory alongside itself")
    parser.add_argument("--stdout", action="store_true", help="Write SVG to stdout")
    parser.add_argument("--spec-help", action="store_true",
                        help="Print the diagram spec reference and exit")
    args = parser.parse_args()

    if args.spec_help:
        print(SPEC_HELP)
        return 0

    if args.directory:
        specs = sorted(Path(args.directory).glob("*.json"))
        if not specs:
            print(f"No .json specs found in {args.directory}", file=sys.stderr)
            return 1
        failures = 0
        for spec_path in specs:
            ok, message = render_file(spec_path, spec_path.with_suffix(".svg"))
            print(("rendered " if ok else "FAILED   ") + message,
                  file=sys.stdout if ok else sys.stderr)
            failures += 0 if ok else 1
        return 1 if failures else 0

    if not args.spec:
        parser.error("provide a spec file, --dir, or --spec-help")

    if args.stdout:
        spec, error = load_json_pair(args.spec)
        if error:
            print(error, file=sys.stderr)
            return 1
        problems = validate(spec)
        if problems:
            print("; ".join(problems), file=sys.stderr)
            return 1
        sys.stdout.write(render(spec))
        return 0

    out_path = Path(args.output) if args.output else Path(args.spec).with_suffix(".svg")
    ok, message = render_file(Path(args.spec), out_path)
    print(("rendered " if ok else "FAILED   ") + message,
          file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
