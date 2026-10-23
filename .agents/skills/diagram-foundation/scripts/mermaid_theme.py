"""Route C: keep Mermaid's picture, make it look like ours.

For the notations Mermaid knows better than we do — sequence, ERD, class,
state. Lifelines, activation bars and attribute compartments have no Google
Slides equivalent, so there is nothing to be gained by reading the geometry
back; the diagram stays a picture and gets styled in place.

Three fixes, in order of how much they matter:

1. Append the house stylesheet inside Mermaid's own `<style>` block. Last in
   the cascade beats both Mermaid's defaults and the `!important` rules its
   `classDef` emits, without rewriting any attribute.
2. Set absolute `width`/`height`. Mermaid writes `width="100%"` with a
   `max-width` style, and `-w` only moves the max-width — so a markdown `<img>`
   or a Google Docs import has no intrinsic size to lay out against.
3. Drop the drop-shadow filter definitions Mermaid 12 emits. Rule 1 already
   neutralises them visually; removing the defs keeps the file honest.
"""

from __future__ import annotations

import re

from house_css import house_css

_STYLE_CLOSE = re.compile(r"</style>", re.IGNORECASE)
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_VIEWBOX = re.compile(r'viewBox="([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"')
_SHADOW_DEF = re.compile(r"<filter\b[^>]*drop-shadow.*?</filter>", re.S | re.I)

# With htmlLabels off, Mermaid puts each word of a label in its own inner
# tspan and relies on the browser's whitespace handling to space them — which
# a standalone SVG does not do, so "appears in" renders as "appearsin". The
# words are siblings inside one outer tspan, so a space goes before every
# inner tspan after the first.
_INNER_TSPAN = re.compile(r'(</tspan>)\s*(<tspan[^>]*class="[^"]*text-inner-tspan)')


def _space_inner_tspans(svg):
    # One global pass, not a loop. `re.sub` resumes scanning after each match,
    # so it never re-reads the `</tspan>` it just inserted; looping until the
    # string stops changing would keep matching its own output and never
    # terminate.
    return _INNER_TSPAN.sub(r'\1<tspan xml:space="preserve"> </tspan>\2', svg)


def viewbox_size(svg):
    """(width, height) in px from the viewBox, or None if it has none."""
    found = _VIEWBOX.search(svg)
    if not found:
        return None
    return float(found.group(3)), float(found.group(4))


def _set_dimensions(svg, width, height):
    """Rewrite the root element's width/height and strip the max-width style."""
    opening = _SVG_OPEN.search(svg)
    if not opening:
        return svg
    tag = opening.group(0)
    new = re.sub(r'\swidth="[^"]*"', "", tag)
    new = re.sub(r'\sheight="[^"]*"', "", new)
    # The inline max-width is what actually constrains the rendered size in a
    # browser, so leaving it would override the attributes just written.
    new = re.sub(r'\sstyle="[^"]*"', "", new)
    new = new[:-1].rstrip() + (f' width="{width:.0f}" height="{height:.0f}">')
    return svg[:opening.start()] + new + svg[opening.end():]


def apply(svg, title=None, description=None, scale=1.0):
    """Return the themed SVG."""
    svg = _SHADOW_DEF.sub("", svg)
    svg = _space_inner_tspans(svg)

    css = "\n" + house_css() + "\n"
    if _STYLE_CLOSE.search(svg):
        svg = _STYLE_CLOSE.sub(lambda _: css + "</style>", svg, count=1)
    else:
        # No style block to append to — an unusual diagram type, or a future
        # Mermaid that inlines everything. Insert one rather than give up.
        opening = _SVG_OPEN.search(svg)
        if opening:
            svg = (svg[:opening.end()] + f"<style>{css}</style>"
                   + svg[opening.end():])

    size = viewbox_size(svg)
    if size:
        svg = _set_dimensions(svg, size[0] * scale, size[1] * scale)

    # The title is metadata, not artwork, exactly as in svg_backend: the
    # heading above the diagram already names it.
    if title or description:
        opening = _SVG_OPEN.search(svg)
        if opening:
            meta = ""
            if title:
                meta += f"<title>{_escape(title)}</title>"
            caption = description or title
            if caption:
                meta += f"<desc>{_escape(caption)}</desc>"
            tag = opening.group(0)
            if caption:
                # Mermaid already sets role="graphics-document document" and
                # an aria-roledescription. Appending a second role attribute
                # makes the document malformed, and every SVG rasteriser
                # rejects it outright — so replace rather than add.
                tag = re.sub(r'\srole="[^"]*"', "", tag)
                tag = re.sub(r'\saria-label="[^"]*"', "", tag)
                tag = (tag[:-1].rstrip()
                       + f' role="img" aria-label="{_escape(caption, True)}">')
            svg = svg[:opening.start()] + tag + meta + svg[opening.end():]
    return svg


def _escape(value, attribute=False):
    out = (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return out.replace('"', "&quot;") if attribute else out
