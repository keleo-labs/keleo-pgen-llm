#!/usr/bin/env python3
"""Extract text content from Google Slides presentations via gws CLI.

Fetches a presentation by ID using the gws CLI tool and outputs
clean text content from all slides, organized by slide with speaker notes.

Usage:
    # Extract text from a presentation
    python3 utils/extract-gws-slides.py <presentation-id>

    # Output to file
    python3 utils/extract-gws-slides.py <presentation-id> -o output.md

    # Include speaker notes
    python3 utils/extract-gws-slides.py <presentation-id> --notes

    # JSON output (raw extracted data)
    python3 utils/extract-gws-slides.py <presentation-id> --json

Output: Markdown-formatted slide content to stdout (or file with -o).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

GWS_PATH = "/opt/homebrew/bin/gws"


def fetch_presentation(presentation_id):
    result = subprocess.run(
        [GWS_PATH, "slides", "presentations", "get",
         "--params", json.dumps({"presentationId": presentation_id})],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"gws CLI failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return json.loads(result.stdout)


def extract_text_from_elements(elements):
    texts = []
    for elem in elements:
        if "shape" in elem:
            shape = elem["shape"]
            tf = shape.get("text", {})
            for te in tf.get("textElements", []):
                run = te.get("textRun", {})
                content = run.get("content", "")
                if content.strip():
                    texts.append(content.strip())
        if "table" in elem:
            table = elem["table"]
            for row in table.get("tableRows", []):
                row_cells = []
                for cell in row.get("tableCells", []):
                    cell_text = []
                    for te in cell.get("text", {}).get("textElements", []):
                        run = te.get("textRun", {})
                        content = run.get("content", "")
                        if content.strip():
                            cell_text.append(content.strip())
                    row_cells.append(" ".join(cell_text))
                if any(row_cells):
                    texts.append(" | ".join(row_cells))
        if "elementGroup" in elem:
            group = elem["elementGroup"]
            texts.extend(extract_text_from_elements(group.get("children", [])))
    return texts


def extract_notes(slide):
    notes_page = slide.get("slideProperties", {}).get("notesPage", {})
    notes_elements = notes_page.get("pageElements", [])
    return extract_text_from_elements(notes_elements)


def extract_slides(presentation, include_notes=False):
    title = presentation.get("title", "Untitled Presentation")
    slides_data = []

    for i, slide in enumerate(presentation.get("slides", []), 1):
        elements = slide.get("pageElements", [])
        texts = extract_text_from_elements(elements)
        notes = extract_notes(slide) if include_notes else []
        slides_data.append({
            "slideNumber": i,
            "objectId": slide.get("objectId", ""),
            "content": texts,
            "notes": notes,
        })

    return {"title": title, "slideCount": len(slides_data), "slides": slides_data}


def format_markdown(extracted):
    lines = [f"# {extracted['title']}", ""]
    for slide in extracted["slides"]:
        lines.append(f"## Slide {slide['slideNumber']}")
        lines.append("")
        for text in slide["content"]:
            lines.append(text)
        if slide.get("notes"):
            lines.append("")
            lines.append("**Speaker Notes:**")
            for note in slide["notes"]:
                lines.append(f"> {note}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text content from Google Slides via gws CLI"
    )
    parser.add_argument("presentation_id",
                        help="Google Slides presentation ID")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--notes", action="store_true",
                        help="Include speaker notes")
    parser.add_argument("--json", action="store_true",
                        help="Output raw extracted data as JSON")
    args = parser.parse_args()

    if not Path(GWS_PATH).exists():
        print(f"Error: gws CLI not found at {GWS_PATH}", file=sys.stderr)
        sys.exit(1)

    presentation = fetch_presentation(args.presentation_id)
    extracted = extract_slides(presentation, include_notes=args.notes)

    if args.json:
        output = json.dumps(extracted, indent=2, ensure_ascii=False)
    else:
        output = format_markdown(extracted)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Extracted {extracted['slideCount']} slides to {args.output}",
              file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
