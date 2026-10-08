#!/usr/bin/env python3
"""Replace published diagram pictures with native Google Slides shapes.

Runs after a deck is published. For each diagram in `build/diagrams.json` it
finds the slide carrying that diagram's marker caption, takes the picture's
position and size, deletes both, and draws the diagram as real shapes in the
same box — rounded rectangles with their own fill, outline and text, and lines
with arrow heads. Someone can then open the deck and move a node.

Matching is by marker caption rather than slide index, because a deck's slide
numbering shifts whenever a slide is added. `layouts/diagram.vue` emits the
caption; this pass consumes and removes it.

The upgrade is strictly additive: if it cannot find a slide, or the batch
fails, the deck keeps the picture Slidev already embedded and stays usable.

Usage:
    upgrade-diagrams.py <presentation-id> --manifest build/diagrams.json

Exit codes: 0 ok (including nothing to do), 1 runtime failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAGRAM_SCRIPTS = HERE.parent.parent / "diagram-foundation" / "scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DIAGRAM_SCRIPTS))

from diagram import use_palette  # noqa: E402
from gwsclient import GwsError, run  # noqa: E402
from slides_backend import scene_requests  # noqa: E402

MARKER_PREFIX = "diagram:"


def get_presentation(presentation_id: str) -> dict:
    return run([
        "slides", "presentations", "get",
        "--params", json.dumps({
            "presentationId": presentation_id,
            "fields": "slides(objectId,pageElements(objectId,size,transform,"
                      "shape(text(textElements(textRun(content)))),image(contentUrl)))",
        }),
    ], timeout=300)


def element_text(element: dict) -> str:
    runs = (element.get("shape", {}).get("text", {}) or {}).get("textElements", [])
    return "".join(
        r.get("textRun", {}).get("content", "") for r in runs
    ).strip()


def element_box(element: dict) -> tuple[float, float, float, float]:
    """Position and size in EMU, accounting for the element's own scale."""
    transform = element.get("transform", {})
    size = element.get("size", {})
    width = size.get("width", {}).get("magnitude", 0) * transform.get("scaleX", 1)
    height = size.get("height", {}).get("magnitude", 0) * transform.get("scaleY", 1)
    return (transform.get("translateX", 0), transform.get("translateY", 0),
            abs(width), abs(height))


def locate(presentation: dict, marker: str) -> tuple[str, list[str], tuple] | None:
    """Find (pageId, objectIds to delete, target box) for a marker."""
    wanted = f"{MARKER_PREFIX}{marker}"
    for slide in presentation.get("slides", []):
        elements = slide.get("pageElements", [])
        if not any(element_text(e) == wanted for e in elements):
            continue
        images = [e for e in elements if "image" in e]
        if not images:
            return None
        picture = max(images, key=lambda e: element_box(e)[2] * element_box(e)[3])
        doomed = [picture["objectId"]]
        doomed += [e["objectId"] for e in elements if element_text(e) == wanted]
        return slide["objectId"], doomed, element_box(picture)
    return None


def upgrade(presentation_id: str, manifest: list[dict]) -> tuple[int, list[str]]:
    presentation = get_presentation(presentation_id)
    upgraded, skipped = 0, []

    for entry in manifest:
        marker = entry["marker"]
        # A diagram that renders as a picture has no geometry to turn into
        # shapes — a sequence diagram's lifelines and an ERD's attribute rows
        # have no Slides equivalent. The picture stays, and the deck is fine.
        if not entry.get("scene"):
            skipped.append(f"{marker}: renders as a picture, kept as one")
            continue
        found = locate(presentation, marker)
        if not found:
            skipped.append(f"{marker}: no slide carries its marker")
            continue
        page_id, doomed, box = found

        try:
            scene = entry["scene"]
            requests = [{"deleteObject": {"objectId": oid}} for oid in doomed]
            requests += scene_requests(scene, page_id, box,
                                       prefix=f"d{entry['order']:02d}")
            run([
                "slides", "presentations", "batchUpdate",
                "--params", json.dumps({"presentationId": presentation_id}),
                "--json", json.dumps({"requests": requests}),
            ], timeout=300)
            upgraded += 1
        except (GwsError, KeyError, TypeError, ValueError) as exc:
            # The picture is still on the slide, so the deck is intact.
            skipped.append(f"{marker}: {str(exc)[:160]}")

    return upgraded, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("presentation_id")
    parser.add_argument("--palette", default="redhat",
                        help="colour family; must match the one build-diagrams.py "
                             "used, or the native shapes will not match the PNG "
                             "they replace")
    parser.add_argument("--manifest", type=Path, required=True,
                        help="build/diagrams.json written by build-diagrams.py")
    args = parser.parse_args()

    if not args.manifest.exists():
        print("no diagram manifest — nothing to upgrade")
        return 0

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: unreadable manifest: {exc}", file=sys.stderr)
        return 1

    try:
        use_palette(args.palette)
        upgraded, skipped = upgrade(args.presentation_id, manifest)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except GwsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"upgraded {upgraded} of {len(manifest)} diagram(s) to native shapes")
    for note in skipped:
        print(f"  left as a picture — {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
