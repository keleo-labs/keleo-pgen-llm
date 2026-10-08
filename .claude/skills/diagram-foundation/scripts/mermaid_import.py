"""Route B: let Mermaid do the layout, draw the result ourselves.

Graph layout is the hard part of a diagram and Mermaid is good at it. Drawing
is the part the house cares about. So for flowchart-family sources we render
with Mermaid, read the geometry back out of its SVG, and rebuild a Scene from
house tokens — the same Scene a native layout produces, which means the same
SVG backend and the same editable Google Slides shapes.

Semantics come from the **source**, geometry from the **SVG**. That split is
what makes this sturdy: labels, shapes and roles are read from text we were
given, and only coordinates are scraped. A Mermaid upgrade that renames a CSS
class costs us positions, not meaning.

Where it stops. `sequenceDiagram`, `erDiagram`, `classDiagram` and
`stateDiagram` are not importable and are not meant to be: lifelines,
activation bars and attribute compartments have no Google Slides equivalent,
so reading them back yields a heap of loose rectangles that is worse than the
picture. Anything this module cannot read raises `ImportUnsupported` and the
caller falls back to route C.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from diagram import (ROLES, SHAPES, THEME, edge_label, edge_path,
                     measure_node, node_block, polyline_path, rect,
                     simplify_path, text)

SVG_NS = "http://www.w3.org/2000/svg"


class ImportUnsupported(Exception):
    """This diagram cannot become house shapes; keep the picture instead."""


# --------------------------------------------------------------------------
# Source — what each node means
# --------------------------------------------------------------------------

# Longest wrapper first: `[(` must be tried before `[`, or a cylinder parses
# as a rectangle whose label starts with a bracket.
NODE_WRAPPERS = (
    ("[(", ")]", "cylinder"),
    ("([", "])", "stadium"),
    ("((", "))", "event"),
    ("{{", "}}", "hexagon"),
    ("[/", "/]", "rounded"),     # parallelogram — no house equivalent
    ("[\\", "\\]", "rounded"),
    ("[", "]", "rounded"),       # Mermaid's rectangle is the house default
    ("(", ")", "rounded"),
    ("{", "}", "diamond"),
    (">", "]", "note"),
)

_ID = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
_FLOWCHART = re.compile(r"^\s*(flowchart|graph)\b", re.M)
_SUBGRAPH = re.compile(
    rf'^\s*subgraph\s+(?P<id>{_ID})\s*(?:\[\s*"?(?P<label>[^"\]]*)"?\s*\])?\s*$',
    re.M)
_CLASS_STMT = re.compile(rf"^\s*class\s+(?P<ids>{_ID}(?:\s*,\s*{_ID})*)\s+"
                         r"(?P<cls>[A-Za-z0-9_-]+)\s*$", re.M)
_INLINE_CLASS = re.compile(r":::([A-Za-z0-9_-]+)")


def importable(source):
    """Is this a flowchart? Only flowcharts can become house shapes."""
    return bool(_FLOWCHART.search(source))


# Mermaid lets a label carry simple markup — `<br>` for a hard break, and
# `<b>`/`<i>` for weight. Mermaid honours it; taking the label verbatim from
# the source would print the tag.
_BREAK = re.compile(r"<\s*br\s*/?\s*>", re.I)
_MARKUP = re.compile(r"</?\s*(?:b|i|em|strong|span|p)\s*/?\s*>", re.I)


def clean_label(text):
    """Label text as a reader should see it.

    A `<br>` becomes a space rather than a forced break: the house wrapper
    measures the real string and breaks where it actually fits, which is the
    same rule every native layout follows. Honouring the author's break
    position would mean carrying hand-set line breaks the house type scale
    has no way to validate.
    """
    text = _BREAK.sub(" ", text)
    text = _MARKUP.sub("", text)
    return " ".join(text.split())


def _strip_comments(source):
    return "\n".join(line for line in source.splitlines()
                     if not line.strip().startswith("%%"))


def _find_nodes(source):
    """{node id: {label, shape, class}} for every declaration in the source."""
    found = {}
    for open_tok, close_tok, shape in NODE_WRAPPERS:
        pattern = re.compile(
            rf"({_ID})\s*{re.escape(open_tok)}\s*"
            rf'(?:"(?P<quoted>[^"]*)"|(?P<bare>.*?))\s*{re.escape(close_tok)}'
            r"(?:\s*:::([A-Za-z0-9_-]+))?")
        for match in pattern.finditer(source):
            nid = match.group(1)
            if nid in found:
                continue
            label = match.group("quoted")
            if label is None:
                label = match.group("bare") or ""
            found[nid] = {"label": clean_label(label), "shape": shape,
                          "cls": match.group(4)}
        # Blank out what was just consumed so a shorter wrapper cannot
        # re-match the inside of a longer one.
        source = pattern.sub(lambda m: " " * len(m.group(0)), source)
    return found, source


def parse_source(source):
    """Semantics only: what the nodes are called and what they are."""
    source = _strip_comments(source)
    subgraphs = {m.group("id"): clean_label(m.group("label") or m.group("id"))
                 for m in _SUBGRAPH.finditer(source)}

    nodes, remainder = _find_nodes(source)

    # A bare id with no wrapper is still a node: `A --> B` declares both.
    for match in re.finditer(rf"(?<![\w.-]){_ID}(?![\w.-])", remainder):
        nid = match.group(0)
        if nid in nodes or nid in subgraphs or nid in _KEYWORDS:
            continue
        nodes[nid] = {"label": nid, "shape": "rounded", "cls": None}

    for match in _CLASS_STMT.finditer(source):
        for nid in (part.strip() for part in match.group("ids").split(",")):
            if nid in nodes:
                nodes[nid]["cls"] = match.group("cls")
    for nid, info in nodes.items():
        if info["cls"] is None:
            tail = re.search(rf"(?<![\w.-]){re.escape(nid)}(?![\w.-])\s*:::",
                             source)
            if tail:
                inline = _INLINE_CLASS.search(source, tail.end() - 3)
                if inline:
                    info["cls"] = inline.group(1)
    return nodes, subgraphs


_KEYWORDS = {
    "flowchart", "graph", "subgraph", "end", "class", "classDef", "style",
    "click", "linkStyle", "direction", "TB", "TD", "BT", "LR", "RL",
}


def _style_from_class(name):
    """A Mermaid class name → house role or emphasis.

    Mermaid class names cannot contain a dot, so a role is written with a
    hyphen — `:::storm-event` — and restored here.
    """
    if not name:
        return {}
    dotted = name.replace("-", ".", 1)
    if dotted in ROLES:
        return {"role": dotted}
    if name in ("accent", "muted", "selected"):
        return {"emphasis": name}
    return {}


# --------------------------------------------------------------------------
# SVG — where Mermaid put everything
# --------------------------------------------------------------------------

_TRANSLATE = re.compile(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)")
_NUMBER = re.compile(r"-?\d+\.?\d*(?:e-?\d+)?")


def _tag(element):
    return element.tag.split("}")[-1]


def _translate(element):
    found = _TRANSLATE.search(element.get("transform") or "")
    return (float(found.group(1)), float(found.group(2))) if found else (0.0, 0.0)


def _local_bbox(group, offset=(0.0, 0.0)):
    """Union bounding box of a node's geometry, in the node group's own space.

    Transforms are accumulated on the way down, including one on the geometry
    element itself. Mermaid draws a cylinder as a path that starts at its left
    edge and then recentres it with `transform="translate(-w/2, …)"` on the
    path; reading only the node group's transform leaves the shape half its
    own width to the right of where it belongs.

    Paths go through `_path_bbox`, which walks the commands properly. Reading
    a path as a flat list of number pairs would put arc flags and radii into
    the box and make it several times too large.
    """
    xs, ys = [], []

    def visit(element, dx, dy):
        # The label subtree is text, not shape. It is replaced wholesale by
        # our own, so letting it widen the box would size the shape twice.
        if _tag(element) == "g" and (element.get("class") or "") == "label":
            return
        tdx, tdy = _translate(element)
        dx, dy = dx + tdx, dy + tdy
        kind = _tag(element)
        if kind == "rect" and element.get("width"):
            x, y = float(element.get("x", 0)), float(element.get("y", 0))
            xs.extend([dx + x, dx + x + float(element.get("width"))])
            ys.extend([dy + y, dy + y + float(element.get("height"))])
        elif kind == "polygon" and element.get("points"):
            for pair in element.get("points").split():
                px, _, py = pair.partition(",")
                xs.append(dx + float(px))
                ys.append(dy + float(py))
        elif kind in ("ellipse", "circle"):
            cx, cy = float(element.get("cx", 0)), float(element.get("cy", 0))
            rx = float(element.get("rx") or element.get("r") or 0)
            ry = float(element.get("ry") or element.get("r") or 0)
            xs.extend([dx + cx - rx, dx + cx + rx])
            ys.extend([dy + cy - ry, dy + cy + ry])
        elif kind == "path" and element.get("d"):
            box = _path_bbox(element.get("d"))
            if box:
                xs.extend([dx + box[0], dx + box[2]])
                ys.extend([dy + box[1], dy + box[3]])
        for child in element:
            visit(child, dx, dy)

    # The node group's own transform is the caller's origin, so start inside.
    for child in group:
        visit(child, offset[0], offset[1])

    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _path_points(d):
    numbers = [float(v) for v in _NUMBER.findall(d)]
    return list(zip(numbers[0::2], numbers[1::2]))


# How many parameters each path command takes, and which of those pairs are
# coordinates. Reading a path as a flat list of number pairs is wrong: an arc
# carries two radii, a rotation and two flags before its endpoint, so the
# flags get read as coordinates and the box comes out several times too big.
_PARAMS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4,
           "Q": 4, "T": 2, "A": 7, "Z": 0}
_COMMAND = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")


def _arc_extent(chunk, x, y, nx, ny, xs, ys):
    """Add the span an elliptical arc sweeps into, beyond its chord.

    Mermaid's arcs are axis-aligned half-ellipses — a cylinder's lid and base
    — so the sweep flag alone says which side of the chord the bulge is on.
    Expanding both ways instead would make a cylinder a full radius too tall
    at each end. Anything not axis-aligned falls back to both sides, which is
    only ever too generous.
    """
    # sweep=1 is the positive-angle direction, which with y pointing down is
    # clockwise on screen. Left to right clockwise passes through 12 o'clock,
    # so sweep=1 bulges up and sweep=0 bulges down — which is how Mermaid
    # draws a cylinder's base.
    rx, ry, sweep = abs(chunk[0]), abs(chunk[1]), int(chunk[4])
    if abs(ny - y) < 0.01:                      # horizontal chord
        downward = (sweep == 0) == (nx >= x)
        ys.append(y + ry if downward else y - ry)
    elif abs(nx - x) < 0.01:                    # vertical chord
        rightward = (sweep == 1) == (ny >= y)
        xs.append(x + rx if rightward else x - rx)
    else:
        xs += [min(x, nx) - rx, max(x, nx) + rx]
        ys += [min(y, ny) - ry, max(y, ny) + ry]
    return xs, ys


def _path_bbox(d):
    """Bounding box of an SVG path, arcs included.

    Control points are counted as if they were on the curve, which slightly
    overestimates a bezier's box. For sizing a node that is the safe
    direction to be wrong in.
    """
    xs, ys = [], []
    x = y = 0.0
    start = (0.0, 0.0)

    for letter, raw in _COMMAND.findall(d):
        upper = letter.upper()
        relative = letter.islower()
        count = _PARAMS[upper]
        args = [float(v) for v in _NUMBER.findall(raw)]
        if count == 0:
            x, y = start
            continue
        # A repeated parameter group continues the same command, which is how
        # `L 1,2 3,4` and a polyline-style path are written.
        for i in range(0, max(len(args) - count + 1, 0), count):
            chunk = args[i:i + count]
            if len(chunk) < count:
                break
            if upper == "H":
                nx, ny = (x + chunk[0] if relative else chunk[0]), y
            elif upper == "V":
                nx, ny = x, (y + chunk[0] if relative else chunk[0])
            else:
                dx, dy = chunk[-2], chunk[-1]
                nx, ny = (x + dx, y + dy) if relative else (dx, dy)
                # Bezier control points, which bound the curve.
                for j in range(0, count - 2, 2):
                    if upper == "A":
                        break
                    cx_, cy_ = chunk[j], chunk[j + 1]
                    xs.append(x + cx_ if relative else cx_)
                    ys.append(y + cy_ if relative else cy_)
            if upper == "A":
                xs, ys = _arc_extent(chunk, x, y, nx, ny, xs, ys)
            xs += [x, nx]
            ys += [y, ny]
            if upper == "M":
                start = (nx, ny)
            x, y = nx, ny

    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def parse_geometry(svg, svg_id):
    """Positions and sizes, keyed by the ids Mermaid derives from the source."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ImportUnsupported(f"Mermaid produced unparseable SVG: {exc}") from None

    node_prefix = f"{svg_id}-flowchart-"
    nodes, clusters, edges, labels = {}, {}, [], []

    for group in root.iter():
        if _tag(group) != "g":
            continue
        classes = (group.get("class") or "").split()
        gid = group.get("id") or ""

        if "node" in classes and gid.startswith(node_prefix):
            # `dg-flowchart-<id>-<n>`; the id itself may contain hyphens, so
            # strip the trailing counter rather than splitting on every dash.
            key = re.sub(r"-\d+$", "", gid[len(node_prefix):])
            cx, cy = _translate(group)
            box = _local_bbox(group)
            if box:
                nodes[key] = (cx + (box[0] + box[2]) / 2,
                              cy + (box[1] + box[3]) / 2,
                              box[2] - box[0], box[3] - box[1])
            else:
                # Path-only shape: trust the centre, measure the box ourselves.
                nodes[key] = (cx, cy, 0.0, 0.0)

        elif "cluster" in classes and gid.startswith(f"{svg_id}-"):
            frame = next((c for c in group.iter()
                          if _tag(c) == "rect" and c.get("width")), None)
            if frame is None:
                continue
            clusters[gid[len(svg_id) + 1:]] = (
                float(frame.get("x")), float(frame.get("y")),
                float(frame.get("width")), float(frame.get("height")))

        elif "edgeLabel" in classes:
            body = " ".join(
                (t.text or "").strip() for t in group.iter()
                if _tag(t) in ("tspan", "text") and (t.text or "").strip())
            if body:
                lx, ly = _translate(group)
                labels.append((lx, ly, body))

    for element in root.iter():
        if _tag(element) != "path":
            continue
        classes = (element.get("class") or "").split()
        if "flowchart-link" not in classes:
            continue
        points = _path_points(element.get("d") or "")
        if len(points) < 2:
            continue
        dash = next((c.split("-")[-1] for c in classes
                     if c.startswith("edge-pattern-")), "solid")
        edges.append({"points": points,
                      "dash": dash if dash in ("dashed", "dotted") else "solid"})

    return nodes, clusters, edges, labels


# --------------------------------------------------------------------------
# Scene
# --------------------------------------------------------------------------

def _direction(a, b):
    """Which side of its box an edge leaves from, given two points."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) >= abs(dy):
        return "right" if dx >= 0 else "left"
    return "bottom" if dy >= 0 else "top"


def build_scene(source, svg, svg_id):
    """Mermaid source plus its SVG → a house Scene.

    Raises ImportUnsupported when the two do not line up, which is the signal
    to keep the picture rather than draw something wrong.
    """
    if not importable(source):
        raise ImportUnsupported(
            "only a flowchart can become house shapes; this source is a "
            "different Mermaid diagram type")

    declared, subgraphs = parse_source(source)
    positions, clusters, edges, labels = parse_geometry(svg, svg_id)

    if not positions:
        raise ImportUnsupported("no nodes found in the rendered SVG")

    unknown = sorted(set(positions) - set(declared))
    if unknown:
        raise ImportUnsupported(
            "the rendered SVG has nodes the source parser did not find: "
            + ", ".join(unknown[:5]))

    pad = THEME["pad"]
    body, overlays = [], []

    # Size every node first. Edges are snapped to these boxes, so they have to
    # exist before any edge is drawn.
    placed = {}
    for key, (cx, cy, mw, mh) in positions.items():
        info = declared[key]
        node = {"label": info["label"], "shape": info["shape"]}
        node.update(_style_from_class(info["cls"]))
        if node["shape"] not in SHAPES:
            node["shape"] = "rounded"
        # Mermaid sized this box and routed the edges around it, so its size
        # is the one to keep. Measure our own text with no house minimum and
        # grow only where the label genuinely would not fit — applying the
        # minimum here would widen every node past what the routing clears,
        # and the edges would then cut through the shapes.
        own_w, own_h = measure_node(node, max_width=max(mw, THEME["node_w_max"]),
                                    min_width=0, min_height=0)
        w, h = max(mw, own_w), max(mh, own_h)
        placed[key] = (node, cx - w / 2, cy - h / 2, w, h)

    boxes = [(x, y, w, h) for _, x, y, w, h in placed.values()]

    # Clusters first: they are background, and painting order is the only
    # layering the Scene contract has.
    for cid, (x, y, w, h) in clusters.items():
        body.append(rect(x, y, w, h, THEME["group_fill"], THEME["group_stroke"],
                         1, THEME["radius_group"], THEME["group_opacity"]))
        body.append(text(x + 8, y + 16, subgraphs.get(cid, cid),
                         THEME["size_group"], THEME["text_muted"], anchor="start"))

    for edge in edges:
        points = edge["points"]
        start, exit_side = _snap(points[0], points[1], boxes)
        end, entry_side = _snap(points[-1], points[-2], boxes)
        # Mermaid already routed this edge past whatever sits between its
        # ends. Keep that route — reducing it to one curve between endpoints
        # sends the line straight through the nodes it was avoiding.
        route = simplify_path([start] + points[1:-1] + [end])
        if len(route) > 2:
            body.append(polyline_path(route, dash=edge["dash"]))
        else:
            body.append(edge_path(start[0], start[1], end[0], end[1],
                                  exit_side, entry_side, dash=edge["dash"]))

    extents = []
    for node, x, y, w, h in placed.values():
        body.extend(node_block(node, x, y, w, h))
        extents.append((x, y, x + w, y + h))

    # Edge labels paint last, over the boxes their edges pass under.
    for lx, ly, body_text in labels:
        overlays.extend(edge_label(lx, ly, body_text))

    items = body + overlays
    for x, y, w, h in clusters.values():
        extents.append((x, y, x + w, y + h))
    for edge in edges:
        for px, py in edge["points"]:
            extents.append((px, py, px, py))

    min_x = min(e[0] for e in extents)
    min_y = min(e[1] for e in extents)
    max_x = max(e[2] for e in extents)
    max_y = max(e[3] for e in extents)
    dx, dy = pad - min_x, pad - min_y
    offset = (dx, dy) if (abs(dx) > 0.01 or abs(dy) > 0.01) else None

    return {"items": items,
            "width": (max_x - min_x) + pad * 2,
            "height": (max_y - min_y) + pad * 2,
            "offset": offset}


def _snap(endpoint, neighbour, boxes):
    """Put an edge endpoint on the boundary of its box. Returns (point, side).

    Mermaid routed to the box *it* sized. Where our box differs — a cylinder
    most of all — the arrow stops short of the shape or buries its head
    inside it. Snapping to the box actually drawn fixes every such case at
    once, rather than trying to make our sizing match Mermaid's.

    The side is which face the edge leaves or arrives on, which is what
    `edge_path` needs to curve outward from the box rather than across it.
    """
    box = _nearest_box(endpoint, boxes)
    if box is None:
        return endpoint, _direction(neighbour, endpoint)
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    # Toward the rest of the path, not along it. At the start of an edge the
    # neighbour is the next point and at the end it is the previous one, so
    # this always points out of the box on the side the edge uses. Taking the
    # direction of travel instead lands on the opposite face, which hides the
    # line and its arrow head under the node painted over them.
    dx, dy = neighbour[0] - endpoint[0], neighbour[1] - endpoint[1]
    if abs(dx) < 0.01 and abs(dy) < 0.01:
        return endpoint, "bottom"
    # Walk out from the centre to the edge of the box, the same rule
    # layout_hub uses to meet a rectangle.
    scale_x = (w / 2) / abs(dx) if dx else float("inf")
    scale_y = (h / 2) / abs(dy) if dy else float("inf")
    scale = min(scale_x, scale_y)
    if scale_x <= scale_y:
        side = "right" if dx > 0 else "left"
    else:
        side = "bottom" if dy > 0 else "top"
    return (cx + dx * scale, cy + dy * scale), side


def _nearest_box(point, boxes, tolerance=90.0):
    """The box this endpoint is plausibly touching, or None."""
    best, best_gap = None, tolerance
    for x, y, w, h in boxes:
        gap = max(x - point[0], point[0] - (x + w), 0.0) + \
              max(y - point[1], point[1] - (y + h), 0.0)
        if gap < best_gap:
            best, best_gap = (x, y, w, h), gap
    return best
