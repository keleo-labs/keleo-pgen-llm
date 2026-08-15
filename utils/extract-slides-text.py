#!/usr/bin/env python3
"""Extract text content from Google Slides API JSON output."""

import json
import sys
import argparse
from pathlib import Path


def extract_text_from_element(element):
    """Extract text from a page element recursively."""
    texts = []

    shape = element.get('shape', {})
    text_field = shape.get('text', {})

    for te in text_field.get('textElements', []):
        tr = te.get('textRun', {})
        content = tr.get('content', '').strip()
        if content:
            texts.append(content)

    table = element.get('table', {})
    for row in table.get('tableRows', []):
        row_texts = []
        for cell in row.get('tableCells', []):
            cell_text = cell.get('text', {})
            for te in cell_text.get('textElements', []):
                tr = te.get('textRun', {})
                content = tr.get('content', '').strip()
                if content:
                    row_texts.append(content)
        if row_texts:
            texts.append(' | '.join(row_texts))

    for child in element.get('children', []):
        texts.extend(extract_text_from_element(child))

    return texts


def extract_presentation_text(json_path, output_path=None):
    """Extract all text from a Slides API JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    title = data.get('title', 'Untitled')
    slides = data.get('slides', [])

    lines = [f"# {title}\n"]
    lines.append(f"**Slides:** {len(slides)}\n")

    for i, slide in enumerate(slides):
        slide_texts = []
        notes_texts = []

        for elem in slide.get('pageElements', []):
            slide_texts.extend(extract_text_from_element(elem))

        notes = slide.get('slideProperties', {}).get('notesPage', {})
        for elem in notes.get('pageElements', []):
            shape = elem.get('shape', {})
            placeholder = shape.get('placeholder', {})
            if placeholder.get('type') == 'BODY':
                text_field = shape.get('text', {})
                for te in text_field.get('textElements', []):
                    tr = te.get('textRun', {})
                    content = tr.get('content', '').strip()
                    if content:
                        notes_texts.append(content)

        if slide_texts or notes_texts:
            lines.append(f"\n## Slide {i + 1}\n")
            for t in slide_texts:
                lines.append(t)
            if notes_texts:
                lines.append(f"\n**Speaker Notes:**")
                for t in notes_texts:
                    lines.append(f"> {t}")

    result = '\n'.join(lines)

    if output_path:
        Path(output_path).write_text(result)
        print(f"Extracted {len(slides)} slides to {output_path}")
    else:
        print(result)

    return result


def main():
    parser = argparse.ArgumentParser(description='Extract text from Slides API JSON')
    parser.add_argument('input', nargs='+', help='Input JSON file(s)')
    parser.add_argument('-o', '--output-dir', help='Output directory for extracted text')
    args = parser.parse_args()

    for input_path in args.input:
        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stem = Path(input_path).stem
            output_path = out_dir / f"{stem}.md"
            extract_presentation_text(input_path, output_path)
        else:
            extract_presentation_text(input_path)
            if len(args.input) > 1:
                print("\n---\n")


if __name__ == '__main__':
    main()
