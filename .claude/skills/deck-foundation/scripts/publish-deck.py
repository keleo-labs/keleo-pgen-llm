#!/usr/bin/env python3
"""Publish a Slidev deck to Google Slides, and optionally PDF.

Chains the three steps that turn authored markdown into a shareable deck:
Slidev exports native PowerPoint shapes, Drive converts those to a Google
Slides deck with editable text, and Drive can then export a PDF.

The `pptx-editable` format is required. Plain `--format pptx` renders each
slide as a flat image, which converts into an uneditable picture per slide.

Usage:
    publish-deck.py slides.md --name "Platform Adoption"
    publish-deck.py slides.md --name "..." --pdf --review
    publish-deck.py slides.md --pptx-only -o build/deck.pptx

Exit codes: 0 ok, 1 runtime failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gwsclient import GwsError, export_file, file_link, upload_as_slides  # noqa: E402

PDF_MIME = "application/pdf"


class BuildError(RuntimeError):
    """The Slidev export step failed."""


def export_pptx(source: Path, output: Path, timeout: int = 600) -> Path:
    """Run `slidev export --format pptx-editable`.

    Resolved through npx so the skill works without a global Slidev install,
    but a project-local @slidev/cli and playwright-chromium must be present —
    Slidev's exporter is Playwright-driven and fails without a browser.
    """
    if shutil.which("npx") is None:
        raise BuildError("npx is not on PATH — Node.js 18+ is required")

    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx",
        "slidev",
        "export",
        str(source.name),
        "--format",
        "pptx-editable",
        "--output",
        str(output.resolve()),
    ]
    proc = subprocess.run(
        cmd, cwd=source.parent, capture_output=True, text=True, timeout=timeout
    )

    if proc.returncode != 0 or not output.is_file():
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        tail = "\n  ".join(detail[-6:]) if detail else "no output"
        if "playwright" in tail.lower():
            tail += "\n  fix: npm i -D playwright-chromium && npx playwright install chromium"
        raise BuildError(f"slidev export failed:\n  {tail}")

    return output


def publish(
    source: Path,
    name: str,
    *,
    want_pdf: bool,
    folder: str | None,
    workdir: Path,
) -> dict:
    pptx = export_pptx(source, workdir / f"{source.stem}.pptx")

    uploaded = upload_as_slides(str(pptx), name, folder)
    presentation_id = uploaded.get("id")
    if not presentation_id:
        raise GwsError("Drive upload returned no file ID")

    result = {
        "presentationId": presentation_id,
        "url": file_link(presentation_id),
        "pptx": str(pptx),
    }

    if want_pdf:
        pdf_path = workdir / f"{source.stem}.pdf"
        export_file(presentation_id, PDF_MIME, str(pdf_path))
        result["pdf"] = str(pdf_path)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Slidev markdown entry file")
    parser.add_argument("--name", help="deck name in Drive (default: file stem)")
    parser.add_argument("--folder", help="Drive folder ID to publish into")
    parser.add_argument("--pdf", action="store_true", help="also export a PDF")
    parser.add_argument(
        "--pptx-only",
        action="store_true",
        help="build the .pptx but do not upload to Drive",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="output path (with --pptx-only)"
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="build directory (default: <source dir>/build)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="after publishing, print the review command for visual QA",
    )
    parser.add_argument("--json", action="store_true", help="emit result as JSON")
    args = parser.parse_args()

    if not args.source.is_file():
        sys.stderr.write(f"no such file: {args.source}\n")
        return 2

    workdir = args.workdir or args.source.parent / "build"
    name = args.name or args.source.stem

    try:
        if args.pptx_only:
            target = args.output or workdir / f"{args.source.stem}.pptx"
            path = export_pptx(args.source, target)
            print(f"built {path}")
            return 0

        result = publish(
            args.source,
            name,
            want_pdf=args.pdf,
            folder=args.folder,
            workdir=workdir,
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"published: {result['url']}")
            if "pdf" in result:
                print(f"pdf:       {result['pdf']}")
            if args.review:
                script = Path(__file__).parent / "review-deck.py"
                print(f"\nreview with:\n  python3 {script} {result['presentationId']}")
        return 0

    except (BuildError, GwsError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except subprocess.TimeoutExpired:
        sys.stderr.write("slidev export timed out\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
