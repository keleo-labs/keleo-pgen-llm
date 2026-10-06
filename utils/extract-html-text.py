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

    # Batch: many sources into a directory, one .txt per source, plus a manifest
    python3 utils/extract-html-text.py --sources-file /tmp/urls.txt \\
        --output-dir /tmp/docs --anchors --manifest /tmp/docs/_manifest.json
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


#: A line that is an ATX markdown heading, e.g. "### Some heading".
MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
#: A line that is a markdown list item, bulleted or numbered.
MD_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
#: Any HTML-ish tag, used to decide which parser a source needs.
HTML_TAG_RE = re.compile(r"<\s*(?:!doctype|html|head|body|div|p|h[1-6]|span|a|ul|ol|li|table)\b",
                         re.IGNORECASE)


def parse_markdown(text):
    """Parse markdown into the same token shape as parse_html.

    This utility renders markdown, so it must also be able to read it back:
    pointing it at its own output (or any markdown file) to pull a heading
    outline is a natural thing to do, and silently returning nothing for that
    is worse than not supporting it.
    """
    tokens = []
    for line in text.splitlines():
        heading = MD_HEADING_RE.match(line)
        if heading:
            tokens.append({
                "type": "heading",
                "level": len(heading.group(1)),
                "text": heading.group(2).strip(),
                "anchor": None,
            })
            continue
        item = MD_LIST_RE.match(line)
        if item:
            tokens.append({"type": "list_item", "text": item.group(1).strip()})
            continue
        stripped = line.strip()
        if stripped:
            tokens.append({"type": "text", "text": stripped})
        else:
            tokens.append({"type": "break"})
    return tokens


def parse_source(content):
    """Parse content as HTML or markdown, whichever it actually is.

    Sniffs for HTML tags rather than trusting the file extension, so a .txt
    holding HTML and a .html holding markdown both do the right thing.
    """
    if HTML_TAG_RE.search(content):
        return parse_html(content)
    return parse_markdown(content)


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


def read_sources_file(path):
    """Read a newline-delimited list of sources, ignoring blanks and # comments."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def source_stem(source):
    """Derive a filesystem-safe stem from a URL or path.

    Picks the last meaningful path segment, skipping generic trailing segments
    ("index", "index.html") that carry no identifying information. Documentation
    URLs such as .../html-single/configuring_the_thing/index/index.html reduce to
    "configuring_the_thing".
    """
    generic = {"", "index", "index.html", "index.htm"}
    segments = [seg for seg in re.split(r"[/\\]", source.split("?")[0].split("#")[0]) if seg]
    for seg in reversed(segments):
        if seg.lower() not in generic:
            stem = re.sub(r"\.(x?html?|htm)$", "", seg, flags=re.IGNORECASE)
            return re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-") or "page"
    return "page"


def extract_batch(sources, output_dir, want_anchors=False, headings_only=False):
    """Extract many sources into one directory, one text file per source.

    Returns:
        list[dict]: One manifest entry per source, with its stem, output paths,
        character count and heading count. Failed sources carry an ``error`` key
        instead of output paths so one bad URL does not abort the batch.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    seen = {}
    for source in sources:
        stem = source_stem(source)
        # Disambiguate collisions rather than silently overwriting.
        seen[stem] = seen.get(stem, 0) + 1
        if seen[stem] > 1:
            stem = f"{stem}-{seen[stem]}"

        entry = {"source": source, "stem": stem}
        try:
            tokens = parse_source(load_html_or_raise(source))
        except Exception as exc:  # noqa: BLE001 - report and continue the batch
            entry["error"] = str(exc)
            entries.append(entry)
            print(f"WARN  {stem}: {exc}", file=sys.stderr)
            continue

        text = render_headings_only(tokens) if headings_only else render_markdown(tokens)
        text_path = out_dir / f"{stem}.txt"
        text_path.write_text(text, encoding="utf-8")
        entry["textPath"] = str(text_path)
        entry["chars"] = len(text)
        entry["headings"] = sum(1 for t in tokens if t["type"] == "heading")

        if want_anchors:
            anchor_path = out_dir / f"{stem}.anchors.json"
            anchor_path.write_text(
                json.dumps(build_anchor_map(tokens), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            entry["anchorsPath"] = str(anchor_path)

        entries.append(entry)
    return entries


def load_html_or_raise(source):
    """Like load_html, but raises instead of calling sys.exit (batch-safe)."""
    if source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(source, headers={"User-Agent": "extract-html-text/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return path.read_text(encoding="utf-8", errors="replace")


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
            "  %(prog)s --sources-file /tmp/urls.txt --output-dir /tmp/docs "
            "--anchors --manifest /tmp/docs/_manifest.json\n"
        ),
    )
    parser.add_argument(
        "sources",
        nargs="*",
        help="One or more URLs (http/https) or local file paths to extract from",
    )
    parser.add_argument(
        "--sources-file",
        metavar="FILE",
        help="Read sources from FILE, one per line (blank lines and # comments ignored)",
    )
    parser.add_argument(
        "-d", "--output-dir",
        metavar="DIR",
        help=(
            "Batch mode: write one <stem>.txt per source into DIR. Required when "
            "more than one source is given."
        ),
    )
    parser.add_argument(
        "--manifest",
        metavar="FILE",
        help="In batch mode, write a JSON manifest of extracted sources to FILE",
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

    sources = list(args.sources)
    if args.sources_file:
        sources.extend(read_sources_file(args.sources_file))
    if not sources:
        parser.error("no sources given (pass positional sources or --sources-file)")

    # Batch mode: many sources, or an explicit output directory.
    if args.output_dir or len(sources) > 1:
        if not args.output_dir:
            parser.error("--output-dir is required when more than one source is given")
        entries = extract_batch(
            sources,
            args.output_dir,
            want_anchors=args.anchors,
            headings_only=args.headings_only,
        )
        summary = {
            "outputDir": args.output_dir,
            "requested": len(sources),
            "extracted": sum(1 for e in entries if "textPath" in e),
            "failed": sum(1 for e in entries if "error" in e),
            "totalChars": sum(e.get("chars", 0) for e in entries),
            "entries": entries,
        }
        if args.manifest:
            Path(args.manifest).write_text(
                json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        print(json.dumps({k: v for k, v in summary.items() if k != "entries"}, indent=2))
        return

    # Single-source mode
    html_content = load_html(sources[0])
    tokens = parse_source(html_content)

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
