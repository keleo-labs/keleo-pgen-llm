#!/usr/bin/env python3
"""Extract text from Office Open XML (.docx) documents as markdown.

Source methodology material frequently arrives as Word documents — solution
builds, statements of work, partner proposals, internal design notes. This
extracts their readable content without a third-party dependency: a .docx is a
ZIP archive, and `word/document.xml` carries the body text.

Headings map to markdown `#` levels from the paragraph style (Heading1..9,
Title, Subtitle). Numbered and bulleted paragraphs become markdown lists.
Tables become markdown pipe tables. Everything else becomes a paragraph.

Usage examples:

    # Extract to stdout
    python3 utils/extract-docx-text.py scratch/doc.docx

    # Extract to a file
    python3 utils/extract-docx-text.py scratch/doc.docx -o scratch/doc.md

    # Headings only, to review document structure before reading it all
    python3 utils/extract-docx-text.py scratch/doc.docx --headings-only

    # Batch: many documents into a directory, one .md per source
    python3 utils/extract-docx-text.py scratch/*.docx --output-dir scratch/md
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Paragraph style IDs that denote a heading, mapped to a markdown level.
# Word writes these without spaces ("Heading2"); some producers use "heading 2".
_HEADING_RE = re.compile(r"^heading\s*([1-9])$", re.IGNORECASE)
_TITLE_STYLES = {"title": 1, "subtitle": 2}


# ---------------------------------------------------------------------------
# Paragraph-level extraction
# ---------------------------------------------------------------------------

def _style_id(para):
    """Return the lowercase style ID of a paragraph, or '' when unstyled."""
    ppr = para.find(f"{W}pPr")
    if ppr is None:
        return ""
    style = ppr.find(f"{W}pStyle")
    if style is None:
        return ""
    return (style.get(f"{W}val") or "").strip()


def _heading_level(style_id):
    """Return the markdown heading level for a style ID, or None."""
    normalised = style_id.lower()
    if normalised in _TITLE_STYLES:
        return _TITLE_STYLES[normalised]
    match = _HEADING_RE.match(normalised)
    return int(match.group(1)) if match else None


def _is_list(para):
    """True when the paragraph carries numbering properties (bullet or number)."""
    ppr = para.find(f"{W}pPr")
    return ppr is not None and ppr.find(f"{W}numPr") is not None


def _list_indent(para):
    """Return the list nesting level (0-based) for a numbered paragraph."""
    ppr = para.find(f"{W}pPr")
    if ppr is None:
        return 0
    numpr = ppr.find(f"{W}numPr")
    if numpr is None:
        return 0
    ilvl = numpr.find(f"{W}ilvl")
    if ilvl is None:
        return 0
    try:
        return int(ilvl.get(f"{W}val") or 0)
    except ValueError:
        return 0


def _para_text(para):
    """Concatenate the visible text of a paragraph, honouring breaks and tabs."""
    parts = []
    for node in para.iter():
        tag = node.tag
        if tag == f"{W}t":
            parts.append(node.text or "")
        elif tag == f"{W}tab":
            parts.append("\t")
        elif tag in (f"{W}br", f"{W}cr"):
            parts.append(" ")
    return re.sub(r"[ \t]+", " ", "".join(parts)).strip()


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------

def _cell_text(cell):
    """Flatten a table cell to a single line, escaping pipes."""
    lines = [_para_text(p) for p in cell.findall(f"{W}p")]
    text = " ".join(line for line in lines if line)
    return text.replace("|", r"\|")


def _table_markdown(table):
    """Render a w:tbl element as a markdown pipe table."""
    rows = []
    for row in table.findall(f"{W}tr"):
        cells = [_cell_text(c) for c in row.findall(f"{W}tc")]
        if cells:
            rows.append(cells)
    if not rows:
        return []

    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]

    out = ["| " + " | ".join(rows[0]) + " |",
           "|" + "|".join([" --- "] * width) + "|"]
    for row in rows[1:]:
        out.append("| " + " | ".join(row) + " |")
    return out


# ---------------------------------------------------------------------------
# Document walk
# ---------------------------------------------------------------------------

def extract(path, headings_only=False):
    """Return the markdown rendering of a .docx file as a string."""
    with zipfile.ZipFile(path) as archive:
        try:
            xml = archive.read("word/document.xml")
        except KeyError:
            raise ValueError(f"{path}: not a Word document (no word/document.xml)")

    root = ElementTree.fromstring(xml)
    body = root.find(f"{W}body")
    if body is None:
        return ""

    blocks = []
    for child in body:
        if child.tag == f"{W}p":
            text = _para_text(child)
            if not text:
                continue
            level = _heading_level(_style_id(child))
            if level:
                blocks.append("#" * level + " " + text)
            elif headings_only:
                continue
            elif _is_list(child):
                blocks.append("  " * _list_indent(child) + "- " + text)
            else:
                blocks.append(text)
        elif child.tag == f"{W}tbl" and not headings_only:
            blocks.extend(_table_markdown(child))

    # Collapse consecutive list items into one block, separate everything else
    # by a blank line.
    out = []
    for i, block in enumerate(blocks):
        out.append(block)
        if i + 1 < len(blocks):
            both_list = block.lstrip().startswith("- ") and blocks[i + 1].lstrip().startswith("- ")
            both_table = block.startswith("|") and blocks[i + 1].startswith("|")
            if not (both_list or both_table):
                out.append("")
    return "\n".join(out).strip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract text from .docx documents as markdown")
    parser.add_argument("input", nargs="+", help="Input .docx file(s)")
    parser.add_argument("-o", "--output", help="Output file (single input only)")
    parser.add_argument("--output-dir", help="Output directory, one .md per input")
    parser.add_argument("--headings-only", action="store_true",
                        help="Emit only the heading structure")
    args = parser.parse_args()

    if args.output and len(args.input) > 1:
        parser.error("--output takes a single input; use --output-dir for several")

    out_dir = Path(args.output_dir) if args.output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for raw in args.input:
        path = Path(raw)
        try:
            text = extract(path, headings_only=args.headings_only)
        except (OSError, ValueError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failures += 1
            continue

        if out_dir:
            target = out_dir / (path.stem + ".md")
            target.write_text(text, encoding="utf-8")
            print(f"Wrote {target} ({len(text):,} chars)")
        elif args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"Wrote {args.output} ({len(text):,} chars)")
        else:
            sys.stdout.write(text)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
