#!/usr/bin/env python3
"""Extract text content from Google Workspace API JSON output (Slides and Docs)."""

import json
import sys
import argparse
from pathlib import Path


# --- Google Slides extraction ---

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


# --- Google Docs extraction ---

def extract_doc_text(json_path, output_path=None):
    """Extract all text from a Docs API JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    title = data.get('title', 'Untitled')
    body = data.get('body', {})
    content = body.get('content', [])

    lines = [f"# {title}\n"]

    for element in content:
        if 'paragraph' in element:
            para = element['paragraph']
            para_text = []
            for elem in para.get('elements', []):
                text_run = elem.get('textRun', {})
                text = text_run.get('content', '').rstrip('\n')
                if text.strip():
                    para_text.append(text)
            if para_text:
                # Check for heading style
                style = para.get('paragraphStyle', {}).get('namedStyleType', '')
                text = ' '.join(para_text)
                if style.startswith('HEADING_'):
                    level = int(style.split('_')[1])
                    lines.append(f"\n{'#' * (level + 1)} {text}\n")
                else:
                    lines.append(text)

        elif 'table' in element:
            table = element['table']
            for row in table.get('tableRows', []):
                row_texts = []
                for cell in row.get('tableCells', []):
                    cell_texts = []
                    for cell_content in cell.get('content', []):
                        if 'paragraph' in cell_content:
                            for elem in cell_content['paragraph'].get('elements', []):
                                text_run = elem.get('textRun', {})
                                text = text_run.get('content', '').strip()
                                if text:
                                    cell_texts.append(text)
                    row_texts.append(' '.join(cell_texts))
                if any(row_texts):
                    lines.append(' | '.join(row_texts))

    result = '\n'.join(lines)

    if output_path:
        Path(output_path).write_text(result)
        print(f"Extracted doc to {output_path}")
    else:
        print(result)

    return result


# --- Format detection and unified entry point ---

def detect_format(data):
    """Auto-detect whether JSON is from Slides or Docs API."""
    if 'slides' in data:
        return 'slides'
    elif 'body' in data and 'content' in data.get('body', {}):
        return 'docs'
    return None


def extract_text(json_path, output_path=None, format_override=None):
    """Extract text from either Slides or Docs API JSON."""
    with open(json_path) as f:
        data = json.load(f)

    fmt = format_override or detect_format(data)
    if fmt == 'slides':
        return extract_presentation_text(json_path, output_path)
    elif fmt == 'docs':
        return extract_doc_text(json_path, output_path)
    else:
        print(f"Error: Cannot detect format for {json_path}. Use --format slides|docs", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Extract text from Google Slides or Docs API JSON')
    parser.add_argument('input', nargs='+', help='Input JSON file(s)')
    parser.add_argument('-o', '--output-dir', help='Output directory for extracted text')
    parser.add_argument('--format', choices=['slides', 'docs'],
                        help='Force format (auto-detected if omitted)')
    args = parser.parse_args()

    for input_path in args.input:
        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stem = Path(input_path).stem
            output_path = out_dir / f"{stem}.md"
            extract_text(input_path, output_path, args.format)
        else:
            extract_text(input_path, format_override=args.format)
            if len(args.input) > 1:
                print("\n---\n")


if __name__ == '__main__':
    main()
