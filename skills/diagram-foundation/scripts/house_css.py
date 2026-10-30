"""House style, expressed the two ways Mermaid will accept it.

One source of truth with the native route: everything here is derived from
`THEME`, `EMPHASIS` and `ROLES`, so switching palette moves the Mermaid output
with it and no colour is written down twice.

Two products:

`mermaid_config()` is the JSON handed to mermaid-cli with `-c`. It gets the
font, type scale and base colours in before layout happens, which matters —
Mermaid sizes its boxes from the font it thinks it is using.

`house_css()` is a stylesheet appended to the `<style>` block Mermaid writes
inside its own SVG. That placement is deliberate. `-C/--cssFile` is fed in as
Mermaid's `themeCSS` and does not reliably survive into the output, and
`classDef` emits `!important` rules that would beat it anyway. Appending to
the emitted block puts the house rules last in the cascade, which wins without
rewriting a single attribute — and so keeps working across Mermaid versions.
"""

from __future__ import annotations

from diagram import ROLES, THEME

# Mermaid wants a bare family list, not the CSS-quoted form THEME carries.
FONT_STACK = THEME["font"].replace("'", "")


def mermaid_config(direction_curve="basis"):
    """The `-c` config for mermaid-cli."""
    return {
        # `neo` is Mermaid 12's default and brings its own fills and a drop
        # shadow, overriding several themeVariables. The flat register needs
        # classic.
        "look": "classic",
        "theme": "base",
        # Also at the root, not only under `flowchart`: Mermaid 12 reads the
        # top-level key for several diagram types and still emits
        # foreignObject labels when only the nested one is set. A standalone
        # SVG loaded through a markdown <img> does not render foreignObject,
        # which is the same reason svg_backend avoids it.
        "htmlLabels": False,
        "themeVariables": {
            "fontFamily": FONT_STACK,
            "fontSize": f"{THEME['size_label']}px",
            "primaryColor": THEME["node_fill"],
            "primaryBorderColor": THEME["border"],
            "primaryTextColor": THEME["text"],
            "secondaryColor": THEME["node_fill_muted"],
            "tertiaryColor": THEME["canvas"],
            "background": THEME["canvas"],
            "mainBkg": THEME["node_fill"],
            "nodeBorder": THEME["border"],
            "lineColor": THEME["edge_arrow"],
            "textColor": THEME["text"],
            "clusterBkg": THEME["group_fill"],
            "clusterBorder": THEME["group_stroke"],
            "edgeLabelBackground": THEME["canvas"],
            "titleColor": THEME["text"],
            # Sequence and ERD specifics. Mermaid keys these separately and
            # falls back to saturated defaults when they are absent.
            "actorBkg": THEME["node_fill"],
            "actorBorder": THEME["border"],
            "actorTextColor": THEME["text"],
            "actorLineColor": THEME["border"],
            "signalColor": THEME["text_muted"],
            "signalTextColor": THEME["text_muted"],
            "labelBoxBkgColor": THEME["node_fill_muted"],
            "labelBoxBorderColor": THEME["border"],
            "labelTextColor": THEME["text"],
            "noteBkgColor": THEME["node_fill_muted"],
            "noteBorderColor": THEME["border"],
            "noteTextColor": THEME["text"],
            "activationBkgColor": THEME["node_fill_accent"],
            "activationBorderColor": THEME["border_accent"],
            "attributeBackgroundColorOdd": THEME["canvas"],
            "attributeBackgroundColorEven": THEME["node_fill_muted"],
        },
        "flowchart": {
            # Native <text>, not foreignObject: a standalone SVG loaded through
            # a markdown <img> does not render foreignObject in most browsers,
            # which is the same reason svg_backend avoids it.
            "htmlLabels": False,
            "curve": direction_curve,
            "padding": 12,
            "nodeSpacing": 44,
            "rankSpacing": 56,
        },
        "sequence": {"useMaxWidth": False, "mirrorActors": False,
                     "actorMargin": 56, "boxMargin": 10},
        "er": {"useMaxWidth": False, "entityPadding": 12},
        "class": {"useMaxWidth": False},
        "state": {"useMaxWidth": False},
    }


def _role_rules():
    """One rule per role, so `:::storm.event` in a source lands house colour.

    Mermaid class names cannot contain a dot, so a role is written with a
    hyphen in the source — `:::storm-event` — and mapped back here.
    """
    out = []
    for role, (fill, stroke) in sorted(ROLES.items()):
        css_class = role.replace(".", "-")
        out.append(
            f".{css_class} > rect, .{css_class} > polygon, "
            f".{css_class} > path, .{css_class} > circle, "
            f".{css_class} > ellipse "
            f"{{ fill: {fill} !important; stroke: {stroke} !important; }}"
        )
    return out


def house_css():
    """The stylesheet appended to Mermaid's own <style> block."""
    rules = [
        "/* --- house style (diagram-foundation) --- */",
        # Mermaid 12 attaches a drop shadow through a filter def. Flat means
        # flat, and a CSS property beats a presentation attribute.
        "* { filter: none !important; }",
        f"text, .nodeLabel, .edgeLabel, .cluster-label, .label "
        f"{{ font-family: {FONT_STACK} !important; }}",
        f".nodeLabel, .label text, .node text "
        f"{{ fill: {THEME['text']} !important; "
        f"font-size: {THEME['size_label']}px !important; }}",
        f".edgeLabel, .edgeLabel text "
        f"{{ fill: {THEME['text_muted']} !important; "
        f"font-size: {THEME['size_edge']}px !important; }}",
        f".edgeLabel rect {{ fill: {THEME['canvas']} !important; "
        f"stroke: none !important; }}",
        f".node rect, .node polygon, .node circle, .node ellipse, .node path "
        f"{{ stroke-width: {THEME['stroke_default']}px !important; }}",
        f".node rect {{ rx: {THEME['radius_node']}px; "
        f"ry: {THEME['radius_node']}px; }}",
        f".cluster rect {{ fill: {THEME['group_fill']} !important; "
        f"stroke: {THEME['group_stroke']} !important; stroke-width: 1px "
        f"!important; rx: {THEME['radius_group']}px; "
        f"ry: {THEME['radius_group']}px; }}",
        f".cluster-label, .cluster text "
        f"{{ fill: {THEME['text_muted']} !important; "
        f"font-size: {THEME['size_group']}px !important; }}",
        f".flowchart-link, .messageLine0, .messageLine1, .relationshipLine "
        f"{{ stroke: {THEME['edge']} !important; "
        f"stroke-width: {THEME['edge_width']}px !important; }}",
        f"marker path, marker polygon "
        f"{{ fill: {THEME['edge_arrow']} !important; "
        f"stroke: {THEME['edge_arrow']} !important; }}",
        # An ERD's crow's feet are line work, not solid heads. The blanket
        # marker fill above turns each one into a dark blob, so put them back
        # to stroke-only. Mermaid names them `<svgId>_er-<cardinality>`.
        f'marker[id*="_er-"] path, marker[id*="_er-"] polygon, '
        f'marker[id*="_er-"] circle '
        f"{{ fill: none !important; stroke: {THEME['edge_arrow']} !important; "
        f"stroke-width: {THEME['edge_width']}px !important; }}",
        # Sequence diagram furniture.
        f".actor {{ fill: {THEME['node_fill']} !important; "
        f"stroke: {THEME['border']} !important; "
        f"rx: {THEME['radius_node']}px; ry: {THEME['radius_node']}px; }}",
        f".actor-line {{ stroke: {THEME['border']} !important; }}",
        f"#arrowhead path, .arrowheadPath "
        f"{{ fill: {THEME['edge_arrow']} !important; "
        f"stroke: {THEME['edge_arrow']} !important; }}",
        # Emphasis, so a `:::accent` in any Mermaid source means what it means
        # everywhere else.
        f".accent > rect, .accent > polygon, .accent > path "
        f"{{ fill: {THEME['node_fill_accent']} !important; "
        f"stroke: {THEME['border_accent']} !important; "
        f"stroke-width: {THEME['stroke_accent']}px !important; }}",
        f".muted > rect, .muted > polygon, .muted > path "
        f"{{ fill: {THEME['node_fill_muted']} !important; "
        f"stroke: {THEME['border']} !important; }}",
    ]
    return "\n".join(rules + _role_rules())
