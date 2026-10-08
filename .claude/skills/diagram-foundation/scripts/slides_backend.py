"""Scene → Google Slides batchUpdate requests.

Produces genuinely editable shapes rather than a picture: every box is a
ROUND_RECTANGLE with its own fill, outline and text, every edge a line with an
arrow head. Someone can open the deck and move a node.

One fidelity difference from the SVG backend. SVG edges are cubic béziers;
`createLine` offers STRAIGHT, BENT and CURVED but not arbitrary béziers, so
edges here are straight segments. Every vertical and horizontal hop — the
large majority — is identical either way; a diagonal that curves in the SVG
is a straight diagonal on the slide.

Colours arrive as CSS strings from THEME and are converted to the rgbColor
floats the API wants. The `rgba(...)` edge colour loses its alpha: Slides
takes opacity on the line's own property rather than in the colour, so the
alpha is applied there instead.
"""

from __future__ import annotations

from diagram import THEME

EMU_PER_PX = 9525          # 96 dpi CSS pixel
EMU_PER_PT = 12700


def _rgb(css):
    """CSS colour string → {red, green, blue} floats, plus an alpha."""
    css = css.strip()
    if css.startswith("rgba") or css.startswith("rgb"):
        inner = css[css.index("(") + 1:css.rindex(")")]
        parts = [p.strip() for p in inner.split(",")]
        r, g, b = (int(parts[i]) / 255 for i in range(3))
        alpha = float(parts[3]) if len(parts) > 3 else 1.0
        return {"red": r, "green": g, "blue": b}, alpha
    css = css.lstrip("#")
    if len(css) == 3:
        css = "".join(ch * 2 for ch in css)
    r, g, b = (int(css[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return {"red": r, "green": g, "blue": b}, 1.0


def _pt(px_size, scale):
    """Scene font size in px → points on the slide, eased by FONT_FIT."""
    return px_size * scale * EMU_PER_PX / EMU_PER_PT * FONT_FIT


def _element_properties(page_id, x, y, w, h, scale_x=1, scale_y=1):
    return {
        "pageObjectId": page_id,
        "size": {"width": {"magnitude": max(w, 1), "unit": "EMU"},
                 "height": {"magnitude": max(h, 1), "unit": "EMU"}},
        "transform": {"scaleX": scale_x, "scaleY": scale_y,
                      "translateX": x, "translateY": y, "unit": "EMU"},
    }


def _line_properties(page_id, x1, y1, x2, y2):
    """Element properties for a line running x1,y1 → x2,y2.

    A Slides line always runs from the origin of its own box to the opposite
    corner, so a box plus positive size can only ever draw down-and-right.
    Direction is carried by negating the scale and anchoring the transform at
    the start point — without this, every edge heading up or left renders
    reversed, arrowhead and all.
    """
    return _element_properties(
        page_id, x1, y1, abs(x2 - x1) or 1, abs(y2 - y1) or 1,
        scale_x=1 if x2 >= x1 else -1,
        scale_y=1 if y2 >= y1 else -1,
    )


# Google sets text wider than Chromium, which is what the deck foundation
# warns about for converted slides. Box geometry here comes from metrics
# calibrated against Chromium, so the type is eased down a touch to stop a
# two-line label becoming three and overflowing the box it was sized for.
FONT_FIT = 0.92

# An edge label's white plate is sized from the same Chromium metrics, so it
# needs the matching slack or Slides wraps the label inside it.
LABEL_PLATE_SLACK = 1.35

# House body shape → Google Slides shape type. Every one of these is a real
# Slides shape, so a node stays selectable and movable rather than degrading
# to a picture. See references/visual-language.md for the table this matches.
SHAPE_TYPE = {
    "rounded": "ROUND_RECTANGLE",
    "rect": "RECTANGLE",
    "stadium": "FLOW_CHART_TERMINATOR",
    "cylinder": "FLOW_CHART_MAGNETIC_DISK",
    "hexagon": "HEXAGON",
    "diamond": "DIAMOND",
    "event": "ELLIPSE",
    "note": "FOLDED_CORNER",
    "sticky": "RECTANGLE",
    "person": "ROUND_RECTANGLE",
}

# Slides carries dash on the line's own property rather than in the colour.
DASH_STYLE = {"solid": "SOLID", "dashed": "DASH", "dotted": "DOT"}

# Crow's foot has no Slides arrow head. An ERD never reaches this backend —
# it renders as a picture — but degrade to an open head rather than throw if
# one ever does.
END_ARROW = {
    "arrow": "FILL_ARROW",
    "open": "OPEN_ARROW",
    "none": "NONE",
    "diamond": "FILL_DIAMOND",
    "crowsfoot": "OPEN_ARROW",
}


def scene_requests(scene, page_id, box, prefix="dg"):
    """Return batchUpdate requests drawing a scene inside an EMU box.

    box is (x, y, width, height) in EMU. The scene is scaled uniformly to fit
    and centred, so the diagram keeps its proportions whatever frame it is
    given.
    """
    box_x, box_y, box_w, box_h = box
    off_x, off_y = scene.get("offset") or (0.0, 0.0)

    scale = min(box_w / (scene["width"] * EMU_PER_PX),
                box_h / (scene["height"] * EMU_PER_PX))
    draw_w = scene["width"] * EMU_PER_PX * scale
    draw_h = scene["height"] * EMU_PER_PX * scale
    pad_x = box_x + (box_w - draw_w) / 2
    pad_y = box_y + (box_h - draw_h) / 2

    def ex(px):
        return int(pad_x + (px + off_x) * EMU_PER_PX * scale)

    def ey(px):
        return int(pad_y + (px + off_y) * EMU_PER_PX * scale)

    def size(px):
        return int(px * EMU_PER_PX * scale)

    requests = []
    counter = 0

    # Text items are folded into the box they sit inside: a Slides shape owns
    # its own text, so emitting them as separate text boxes would produce a
    # pile of unanchored labels that drift when someone moves a node.
    boxes = [i for i in scene["items"] if i["t"] == "rect"]

    def owning_box(item):
        for b in boxes:
            if (b["x"] <= item["x"] <= b["x"] + b["w"]
                    and b["y"] <= item["y"] <= b["y"] + b["h"]):
                return b
        return None

    pending = {}
    for item in scene["items"]:
        if item["t"] != "text":
            continue
        owner = owning_box(item)
        key = id(owner) if owner else None
        pending.setdefault(key, []).append(item)

    for item in scene["items"]:
        counter += 1
        # Slides rejects an object id shorter than five characters.
        oid = f"{prefix}{counter:04d}"

        if item["t"] == "rect":
            fill, fill_alpha = _rgb(item["fill"])
            width, left = size(item["w"]), ex(item["x"])
            if item.get("kind") == "label_bg":
                grown = int(width * LABEL_PLATE_SLACK)
                left -= (grown - width) // 2
                width = grown
            shape = item.get("shape")
            shape_type = (SHAPE_TYPE.get(shape) if shape
                          else ("ROUND_RECTANGLE" if item["radius"] else "RECTANGLE"))
            requests.append({
                "createShape": {
                    "objectId": oid,
                    "shapeType": shape_type or "ROUND_RECTANGLE",
                    "elementProperties": _element_properties(
                        page_id, left, ey(item["y"]), width, size(item["h"])),
                }
            })

            props = {"shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": fill}}}}
            fields = ["shapeBackgroundFill.solidFill.color"]
            if item.get("opacity") is not None:
                props["shapeBackgroundFill"]["solidFill"]["alpha"] = item["opacity"]
                fields.append("shapeBackgroundFill.solidFill.alpha")
            if item["stroke"] == "none" or not item["sw"]:
                props["outline"] = {"propertyState": "NOT_RENDERED"}
                fields.append("outline.propertyState")
            else:
                stroke, _ = _rgb(item["stroke"])
                props["outline"] = {
                    "outlineFill": {"solidFill": {"color": {"rgbColor": stroke}}},
                    "weight": {"magnitude": int(item["sw"] * EMU_PER_PX * scale),
                               "unit": "EMU"},
                }
                fields += ["outline.outlineFill.solidFill.color", "outline.weight"]
            requests.append({"updateShapeProperties": {
                "objectId": oid, "fields": ",".join(fields), "shapeProperties": props}})

            owned = pending.get(id(item), [])
            if owned:
                body = "\n".join(t["s"] for t in owned)
                requests.append({"insertText": {"objectId": oid, "text": body}})
                requests.append({"updateShapeProperties": {
                    "objectId": oid, "fields": "contentAlignment",
                    "shapeProperties": {"contentAlignment": "MIDDLE"},
                }})
                # Style each line over its own character range. A single ALL
                # range would push the label's bold onto the sublabel, which
                # is meant to recede.
                cursor = 0
                for line in owned:
                    start, end = cursor, cursor + len(line["s"])
                    cursor = end + 1          # the newline between lines
                    if start == end:
                        continue
                    colour, _ = _rgb(line["fill"])
                    requests.append({"updateTextStyle": {
                        "objectId": oid,
                        "style": {
                            "fontSize": {"magnitude": _pt(line["size"], scale),
                                         "unit": "PT"},
                            "bold": line["weight"] == "600",
                            "foregroundColor": {"opaqueColor": {"rgbColor": colour}},
                        },
                        "fields": "fontSize,bold,foregroundColor",
                        "textRange": {"type": "FIXED_RANGE",
                                      "startIndex": start, "endIndex": end},
                    }})
                requests.append({"updateParagraphStyle": {
                    "objectId": oid,
                    "style": {"alignment": "CENTER"},
                    "fields": "alignment",
                    "textRange": {"type": "ALL"},
                }})

        elif item["t"] == "path":
            # A routed edge becomes one connector per leg. Slides has no
            # polyline, and a single straight hop between the endpoints would
            # throw away the routing and drive the line through whatever it
            # was drawn to avoid. Only the final leg carries the arrow head.
            route = item.get("points") or [(item["x1"], item["y1"]),
                                           (item["x2"], item["y2"])]
            colour, alpha = _rgb(THEME["edge"])
            for leg, (a, b) in enumerate(zip(route, route[1:])):
                leg_id = oid if leg == 0 else f"{oid}s{leg:02d}"
                x1, y1, x2, y2 = ex(a[0]), ey(a[1]), ex(b[0]), ey(b[1])
                requests.append({"createLine": {
                    "objectId": leg_id,
                    "lineCategory": "STRAIGHT",
                    "elementProperties": _line_properties(page_id, x1, y1, x2, y2),
                }})
                last = leg == len(route) - 2
                requests.append({"updateLineProperties": {
                    "objectId": leg_id,
                    "fields": "lineFill.solidFill.color,lineFill.solidFill.alpha,"
                              "weight,endArrow,dashStyle",
                    "lineProperties": {
                        "lineFill": {"solidFill": {"color": {"rgbColor": colour},
                                                   "alpha": alpha}},
                        "weight": {"magnitude": int(THEME["edge_width"]
                                                    * EMU_PER_PX * scale),
                                   "unit": "EMU"},
                        "endArrow": (END_ARROW.get(item.get("arrow", "arrow"),
                                                   "FILL_ARROW")
                                     if last else "NONE"),
                        "dashStyle": DASH_STYLE.get(item.get("dash", "solid"),
                                                    "SOLID"),
                    },
                }})

        elif item["t"] == "text" and owning_box(item) is None:
            # A label with no box of its own — a group caption or an edge
            # label whose backing rect was emitted separately.
            width = size(max(len(item["s"]) * item["size"] * 0.62, 40))
            height = size(item["size"] * 1.8)
            left = ex(item["x"]) - (width // 2 if item["anchor"] == "middle" else 0)
            requests.append({"createShape": {
                "objectId": oid, "shapeType": "TEXT_BOX",
                "elementProperties": _element_properties(
                    page_id, left, ey(item["y"]) - height // 2, width, height),
            }})
            requests.append({"insertText": {"objectId": oid, "text": item["s"]}})
            colour, _ = _rgb(item["fill"])
            requests.append({"updateTextStyle": {
                "objectId": oid,
                "style": {
                    "fontSize": {"magnitude": _pt(item["size"], scale),
                                 "unit": "PT"},
                    "bold": item["weight"] == "600",
                    "foregroundColor": {"opaqueColor": {"rgbColor": colour}},
                },
                "fields": "fontSize,bold,foregroundColor",
                "textRange": {"type": "ALL"},
            }})
            requests.append({"updateParagraphStyle": {
                "objectId": oid,
                "style": {"alignment": "CENTER" if item["anchor"] == "middle"
                          else "START"},
                "fields": "alignment",
                "textRange": {"type": "ALL"},
            }})

    return requests
