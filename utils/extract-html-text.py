#!/usr/bin/env python3
"""Extract text from HTML pages, preserving heading structure in markdown format.

Replaces ad-hoc inline python3 -c scripts used in practice generation sessions
to extract documentation content from HTML pages (e.g. Red Hat product docs).

Strips script, style, nav, footer, and header elements. Converts headings to
markdown syntax, preserves paragraph and list boundaries, and cleans excessive
whitespace.

Usage examples:

    # Extract text from a URL
    python3 utils/extract-html-text.py http://localhost:8080/docs/.../index/ -o /tmp/content.txt

    # Extract text from a local file
    python3 utils/extract-html-text.py /tmp/page.html

    # Extract anchor ID map (heading text -> HTML id) as JSON
    python3 utils/extract-html-text.py http://localhost:8080/docs/.../index/ --anchors

    # Text to file + anchors to separate file
    python3 utils/extract-html-text.py http://localhost:8080/docs/.../index/ \\
        -o /tmp/content.txt --anchors-file /tmp/anchors.json

    # Table of contents only
    python3 utils/extract-html-text.py /tmp/page.html --headings-only
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

# Tags whose entire subtree should be discarded.
SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg"}

# Block-level tags that should produce paragraph breaks.
BLOCK_TAGS = {
    "p", "div", "section", "article", "aside", "main",
    "blockquote", "pre", "figure", "figcaption",
    "table", "tr", "td", "th",
    "dl", "dt", "dd",
    "details", "summary",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "br", "hr",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


class _StructuredHTMLParser(HTMLParser):
    """Parse HTML into a flat list of structural tokens.

    Produces a list of dicts, each one of:
        {"type": "heading", "level": int, "text": str, "anchor": str|None}
        {"type": "text", "text": str}
        {"type": "list_item", "text": str}
        {"type": "break"}
    """

    def __init__(self):
        super().__init__()
        self.tokens = []

        # State tracking
        self._skip_depth = 0          # > 0 means inside a SKIP_TAGS subtree
        self._heading_level = 0       # > 0 means inside <hN>
        self._heading_text = []       # accumulated heading text fragments
        self._heading_anchor = None   # resolved anchor id for current heading
        self._in_list_item = 0        # > 0 means inside <li>
        self._list_item_text = []     # accumulated list item text fragments
        self._pending_text = []       # accumulated inline text fragments

        # For anchor resolution: track the most recent id/name seen before
        # or on the heading element.
        self._last_anchor_name = None   # from <a name="...">
        self._last_element_id = None    # from id="..." on any element

    # -- helpers --

    def _flush_text(self):
        """Emit accumulated inline text as a text token."""
        joined = " ".join(self._pending_text).strip()
        if joined:
            self.tokens.append({"type": "text", "text": joined})
        self._pending_text = []

    def _flush_list_item(self):
        """Emit accumulated list item text."""
        joined = " ".join(self._list_item_text).strip()
        if joined:
            self.tokens.append({"type": "list_item", "text": joined})
        self._list_item_text = []

    # -- HTMLParser callbacks --

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)

        # Track id and anchor name for heading anchor resolution.
        if "id" in attrs_dict:
            self._last_element_id = attrs_dict["id"]
        if tag == "a" and "name" in attrs_dict:
            self._last_anchor_name = attrs_dict["name"]

        # Skip subtrees
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        # Headings
        if tag in HEADING_TAGS:
            self._flush_text()
            self._heading_level = int(tag[1])
            self._heading_text = []
            # Anchor: prefer id on the heading element itself.
            self._heading_anchor = attrs_dict.get("id")
            return

        # List items
        if tag == "li":
            self._flush_text()
            self._in_list_item += 1
            self._list_item_text = []
            return

        # Block elements produce a break
        if tag in BLOCK_TAGS:
            self._flush_text()
            self.tokens.append({"type": "break"})

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return

        # End of heading
        if tag in HEADING_TAGS and self._heading_level:
            text = " ".join(self._heading_text).strip()
            anchor = self._heading_anchor
            # Fallback anchor resolution: parent id, then preceding <a name>.
            if not anchor and self._last_element_id:
                anchor = self._last_element_id
            if not anchor and self._last_anchor_name:
                anchor = self._last_anchor_name
            self.tokens.append({
                "type": "heading",
                "level": self._heading_level,
                "text": text,
                "anchor": anchor,
            })
            self._heading_level = 0
            self._heading_text = []
            self._heading_anchor = None
            # Reset anchor trackers after consuming.
            self._last_element_id = None
            self._last_anchor_name = None
            return

        # End of list item
        if tag == "li" and self._in_list_item:
            self._flush_list_item()
            self._in_list_item = max(0, self._in_list_item - 1)
            return

        # Block close produces a break
        if tag in BLOCK_TAGS:
            self._flush_text()
            self.tokens.append({"type": "break"})

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = data.strip()
        if not text:
            return
        # Route text to the right accumulator.
        if self._heading_level:
            self._heading_text.append(text)
        elif self._in_list_item:
            self._list_item_text.append(text)
        else:
            self._pending_text.append(text)

    def close(self):
        super().close()
        self._flush_text()


def parse_html(html_content):
    """Parse HTML content into structural tokens.

    Returns:
        list[dict]: Sequence of heading / text / list_item / break tokens.
    """
    parser = _StructuredHTMLParser()
    parser.feed(html_content)
    parser.close()
    return parser.tokens


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _collapse_blank_lines(text):
    """Replace runs of 3+ newlines with exactly 2 (one blank line)."""
    return re.sub(r"\n{3,}", "\n\n", text)


def render_markdown(tokens):
    """Render parsed tokens as markdown-formatted text."""
    lines = []
    for tok in tokens:
        ttype = tok["type"]
        if ttype == "heading":
            prefix = "#" * tok["level"]
            lines.append(f"\n{prefix} {tok['text']}\n")
        elif ttype == "text":
            lines.append(tok["text"])
            lines.append("")  # paragraph break
        elif ttype == "list_item":
            lines.append(f"- {tok['text']}")
        elif ttype == "break":
            lines.append("")
    result = "\n".join(lines)
    return _collapse_blank_lines(result).strip() + "\n"


def render_headings_only(tokens):
    """Render only headings, indented to show structure."""
    lines = []
    for tok in tokens:
        if tok["type"] == "heading":
            prefix = "#" * tok["level"]
            lines.append(f"{prefix} {tok['text']}")
    return "\n".join(lines) + "\n" if lines else ""


def build_anchor_map(tokens):
    """Build a dict mapping heading text -> anchor id.

    Only includes headings that have a resolved anchor.
    """
    mapping = {}
    for tok in tokens:
        if tok["type"] == "heading" and tok.get("anchor"):
            mapping[tok["text"]] = tok["anchor"]
    return mapping


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

def load_html(source):
    """Load HTML from a URL or local file path.

    Args:
        source: An http/https URL or a filesystem path.

    Returns:
        str: Raw HTML content.
    """
    if source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(
            source,
            headers={"User-Agent": "extract-html-text/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset)
        except urllib.error.URLError as exc:
            print(f"Error fetching URL: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        path = Path(source)
        if not path.exists():
            print(f"File not found: {source}", file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract text from HTML pages, preserving heading structure "
            "in markdown format. Strips script/style/nav/footer elements."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s http://localhost:8080/docs/.../index/\n"
            "  %(prog)s /tmp/page.html -o /tmp/content.txt\n"
            "  %(prog)s http://localhost:8080/docs/.../index/ --anchors\n"
            "  %(prog)s http://localhost:8080/docs/.../index/ "
            "-o /tmp/content.txt --anchors-file /tmp/anchors.json\n"
            "  %(prog)s /tmp/page.html --headings-only\n"
        ),
    )
    parser.add_argument(
        "source",
        help="URL (http/https) or local file path to extract from",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write extracted text to FILE instead of stdout",
    )
    parser.add_argument(
        "--anchors",
        action="store_true",
        help=(
            "Output a JSON mapping of heading text to HTML anchor IDs. "
            "When used alone, prints JSON to stdout instead of text."
        ),
    )
    parser.add_argument(
        "--anchors-file",
        metavar="FILE",
        help=(
            "Write the anchor map JSON to FILE (implies --anchors). "
            "Text output still goes to stdout or -o."
        ),
    )
    parser.add_argument(
        "--headings-only",
        action="store_true",
        help="Output only the heading structure (table of contents)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # --anchors-file implies --anchors
    if args.anchors_file:
        args.anchors = True

    # Load and parse
    html_content = load_html(args.source)
    tokens = parse_html(html_content)

    # Determine what to output to stdout
    # Priority: if --anchors without -o or --anchors-file, JSON goes to stdout.
    # If --headings-only, heading outline goes to stdout/output file.
    # Otherwise, full text goes to stdout/output file.

    anchor_map = build_anchor_map(tokens) if args.anchors else None

    # Render text/headings
    if args.headings_only:
        text_output = render_headings_only(tokens)
    else:
        text_output = render_markdown(tokens)

    # Write anchor map
    if anchor_map is not None:
        anchor_json = json.dumps(anchor_map, indent=2, ensure_ascii=False) + "\n"
        if args.anchors_file:
            Path(args.anchors_file).write_text(anchor_json, encoding="utf-8")
        elif not args.output:
            # --anchors without --anchors-file or -o: JSON to stdout only
            sys.stdout.write(anchor_json)
            return

    # Write text output
    if args.output:
        Path(args.output).write_text(text_output, encoding="utf-8")
    else:
        sys.stdout.write(text_output)


if __name__ == "__main__":
    main()
