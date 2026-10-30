#!/usr/bin/env python3
"""Resolve a Google Slides deck into a reusable semantic layout mapping.

A branded template exposes layouts by display name ("Interior title and body"),
often with several near-identical theme variants sharing one name, and with
content placeholders that are numbered SUBTITLEs rather than BODYs. Renderers
cannot rely on either. This tool reads the template once and writes a mapping
from stable semantic roles ("title-body", "chevrons-three") to concrete layout
object IDs and placeholder slots, which is then cached and reused.

Usage:
    slides-template.py <presentation-id-or-url> --list
    slides-template.py <presentation-id-or-url> --map [--name redhat] [--force]
    slides-template.py --show [--name redhat] [--role title-body]
    slides-template.py --templates          # list cached templates

Exit codes: 0 ok, 1 runtime failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gwsclient import GwsError, get_presentation  # noqa: E402
from templatecache import (  # noqa: E402
    CACHE_DIR,
    TemplateNotFound,
    cache_path,
    list_templates,
    load_mapping,
    save_mapping,
)

EMU_PER_INCH = 914400

# Only what the mapper needs — an unmasked get can exceed 10MB.
LAYOUT_FIELDS = (
    "title,pageSize,"
    "layouts(objectId,layoutProperties/displayName,"
    "pageElements(objectId,shape/placeholder,size,transform))"
)

# Semantic roles the deck spec may reference, matched against layout display
# names in order. First matching layout wins; alternates are recorded so the
# choice can be overridden without re-reading the template.
ROLE_PATTERNS: list[tuple[str, str]] = [
    ("title-image", r"^title slide with image$"),
    ("title", r"^title$"),
    ("webinar-title", r"^webinar title"),
    ("closing-image", r"^closing slide with image$"),
    ("closing", r"^closing$"),
    ("agenda", r"agenda"),
    ("overview", r"overview"),
    ("divider-subhead", r"^divider with title and subhead$"),
    ("divider", r"^divider with title$"),
    ("statement", r"callout$"),
    ("large-text", r"large text"),
    ("section-title", r"^interior title$"),
    ("title-subhead-body", r"title, subhead, and body"),
    ("title-body", r"title and body$"),
    ("body", r"^interior body$"),
    ("two-column", r"title and two column body"),
    ("column-body", r"title and column body"),
    # Anchored so they don't capture the "quote three column" variants, which
    # expose more slots and would otherwise win the capacity tie-break.
    ("three-column", r"^interior three column$"),
    ("four-column", r"^interior four column$"),
    ("two-by-two", r"two by two"),
    ("chevrons-three", r"three chevrons"),
    ("chevrons-two", r"two chevrons"),
    ("timeline-horizontal", r"timeline horizontal"),
    ("timeline-vertical", r"timeline vertical"),
    ("data-callouts-three", r"data three callouts"),
    ("data-callouts-two", r"data two callouts"),
    ("data-pie-large", r"data large pie"),
    ("data-pies-two", r"data two pies"),
    ("quote-large", r"quote large"),
    ("quote-three", r"quote three column"),
    ("quote-two", r"quote two column"),
    ("image-full", r"full-width image"),
    ("image-left", r"image left"),
    ("title-left", r"title left"),
    ("blank", r"blank"),
]


def parse_presentation_id(value: str) -> str:
    """Accept a bare ID or any Google Slides URL."""
    match = re.search(r"/presentation/d/([a-zA-Z0-9_-]+)", value)
    return match.group(1) if match else value


def rendered_box(element: dict) -> dict:
    """Compute a placeholder's on-slide box in inches.

    Slides reports an intrinsic size plus an affine transform; the rendered
    size is the product of the two, so neither alone is reliable.
    """
    size = element.get("size", {})
    transform = element.get("transform", {})
    width = size.get("width", {}).get("magnitude", 0) * transform.get("scaleX", 1)
    height = size.get("height", {}).get("magnitude", 0) * transform.get("scaleY", 1)
    return {
        "left": round(transform.get("translateX", 0) / EMU_PER_INCH, 2),
        "top": round(transform.get("translateY", 0) / EMU_PER_INCH, 2),
        "width": round(width / EMU_PER_INCH, 2),
        "height": round(height / EMU_PER_INCH, 2),
    }


def is_furniture(box: dict, slide_height: float) -> bool:
    """Flag footers, page numbers and logos so they aren't filled with content.

    Every layout in a branded template inherits a small strip near the bottom
    edge from the master. These are placeholders but never content targets.
    """
    short = box["height"] < 0.6
    near_bottom = box["top"] > slide_height * 0.82
    narrow = box["width"] < 2.5
    return short and (near_bottom or narrow)


def describe_layout(layout: dict, slide_height: float) -> dict:
    """Extract a layout's content placeholders in reading order."""
    name = layout.get("layoutProperties", {}).get("displayName", "")
    content, furniture = [], []

    for element in layout.get("pageElements", []):
        placeholder = element.get("shape", {}).get("placeholder")
        if not placeholder:
            continue
        box = rendered_box(element)
        entry = {
            "type": placeholder.get("type"),
            "index": placeholder.get("index", 0),
            "objectId": element.get("objectId"),
            **box,
        }
        (furniture if is_furniture(box, slide_height) else content).append(entry)

    # Reading order: top to bottom, then left to right, with the title first.
    content.sort(key=lambda p: (p["type"] != "TITLE", p["top"], p["left"]))

    return {
        "layoutId": layout.get("objectId"),
        "layoutName": name,
        "placeholders": content,
        "furniture": len(furniture),
    }


def assign_slots(placeholders: list[dict]) -> dict:
    """Name each content placeholder as a slot the deck spec can address.

    The title becomes `title`; remaining placeholders become `body1..bodyN` in
    reading order. Slot names are positional by design — a layout's meaning
    comes from its role, not from placeholder type, which is unreliable here.
    """
    slots: dict[str, dict] = {}
    body_n = 0
    for placeholder in placeholders:
        # Geometry travels with the slot so a spec author can tell a heading
        # strip from a body block without re-reading the template.
        ref = {
            "type": placeholder["type"],
            "index": placeholder["index"],
            "box": {
                "left": placeholder["left"],
                "top": placeholder["top"],
                "width": placeholder["width"],
                "height": placeholder["height"],
            },
        }
        if placeholder["type"] == "TITLE" and "title" not in slots:
            slots["title"] = ref
        else:
            body_n += 1
            slots[f"body{body_n}"] = ref
    return slots


def build_mapping(presentation_id: str) -> dict:
    """Read a template and map semantic roles onto its layouts."""
    data = get_presentation(presentation_id, LAYOUT_FIELDS)
    page = data.get("pageSize", {})
    slide_height = page.get("height", {}).get("magnitude", 0) / EMU_PER_INCH or 7.5
    slide_width = page.get("width", {}).get("magnitude", 0) / EMU_PER_INCH or 13.33

    layouts = [describe_layout(l, slide_height) for l in data.get("layouts", [])]

    roles: dict[str, dict] = {}
    for role, pattern in ROLE_PATTERNS:
        matches = [
            l for l in layouts if re.search(pattern, l["layoutName"], re.IGNORECASE)
        ]
        if not matches:
            continue
        # Prefer the variant offering the most content slots — the sparser
        # duplicates are usually alternate colourways with fewer fillable areas.
        best = max(matches, key=lambda l: len(l["placeholders"]))
        roles[role] = {
            "layoutId": best["layoutId"],
            "layoutName": best["layoutName"],
            "slots": assign_slots(best["placeholders"]),
            "capacity": len(best["placeholders"]),
            "alternates": [
                {"layoutId": m["layoutId"], "slots": len(m["placeholders"])}
                for m in matches
                if m["layoutId"] != best["layoutId"]
            ],
        }

    return {
        "presentationId": presentation_id,
        "title": data.get("title"),
        "slideSize": {"width_in": round(slide_width, 2), "height_in": round(slide_height, 2)},
        "layoutCount": len(layouts),
        "roles": roles,
        "unmappedLayouts": sorted(
            {
                l["layoutName"]
                for l in layouts
                if not any(
                    l["layoutId"] == r["layoutId"]
                    or any(a["layoutId"] == l["layoutId"] for a in r["alternates"])
                    for r in roles.values()
                )
            }
        ),
    }


def cache_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.json"


def save_mapping(mapping: dict, name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(name)
    path.write_text(json.dumps(mapping, indent=2) + "\n")
    return path


def load_mapping(name: str) -> dict:
    path = cache_path(name)
    if not path.is_file():
        raise GwsError(
            f"no cached template '{name}' — run: slides-template.py <url> --map --name {name}"
        )
    return json.loads(path.read_text())


def print_list(presentation_id: str) -> None:
    data = get_presentation(presentation_id, LAYOUT_FIELDS)
    page = data.get("pageSize", {})
    slide_height = page.get("height", {}).get("magnitude", 0) / EMU_PER_INCH or 7.5
    print(f"{data.get('title')}  ({len(data.get('layouts', []))} layouts)\n")
    for layout in data.get("layouts", []):
        described = describe_layout(layout, slide_height)
        slots = ", ".join(
            f"{p['type']}:{p['index']}" for p in described["placeholders"]
        )
        print(f"  {described['layoutName']:<38} {described['layoutId']}")
        print(f"      {len(described['placeholders'])} slots  [{slots}]")


def print_mapping(mapping: dict, role: str | None) -> None:
    print(f"{mapping['title']}")
    print(f"  id:      {mapping['presentationId']}")
    size = mapping["slideSize"]
    print(f"  size:    {size['width_in']}in x {size['height_in']}in")
    print(f"  roles:   {len(mapping['roles'])} mapped of {mapping['layoutCount']} layouts\n")

    roles = mapping["roles"]
    if role:
        if role not in roles:
            print(f"role '{role}' is not mapped. Available: {', '.join(sorted(roles))}")
            return
        roles = {role: roles[role]}

    for key, value in roles.items():
        alt = f"  (+{len(value['alternates'])} variants)" if value["alternates"] else ""
        print(f"  {key:<22} -> {value['layoutName']}{alt}")
        print(f"      {value['layoutId']}   slots: {', '.join(value['slots'])}")

    if not role and mapping.get("unmappedLayouts"):
        print(f"\n  unmapped layouts ({len(mapping['unmappedLayouts'])}):")
        for name in mapping["unmappedLayouts"]:
            print(f"      {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="presentation ID or Slides URL")
    parser.add_argument("--list", action="store_true", help="list raw layouts")
    parser.add_argument("--map", action="store_true", help="build and cache a mapping")
    parser.add_argument("--show", action="store_true", help="show a cached mapping")
    parser.add_argument("--templates", action="store_true", help="list cached templates")
    parser.add_argument("--name", default="default", help="cache name (default: default)")
    parser.add_argument("--role", help="with --show, inspect a single role")
    parser.add_argument("--force", action="store_true", help="overwrite an existing cache")
    args = parser.parse_args()

    try:
        if args.templates:
            if not CACHE_DIR.is_dir():
                print("no cached templates")
                return 0
            for path in sorted(CACHE_DIR.glob("*.json")):
                data = json.loads(path.read_text())
                print(f"  {path.stem:<18} {data.get('title')}  ({len(data.get('roles', {}))} roles)")
            return 0

        if args.show:
            print_mapping(load_mapping(args.name), args.role)
            return 0

        if not args.source:
            parser.error("a presentation ID or URL is required")

        presentation_id = parse_presentation_id(args.source)

        if args.list:
            print_list(presentation_id)
            return 0

        if args.map:
            path = cache_path(args.name)
            if path.exists() and not args.force:
                sys.stderr.write(f"{path} exists — pass --force to overwrite\n")
                return 1
            mapping = build_mapping(presentation_id)
            saved = save_mapping(mapping, args.name)
            print(f"mapped {len(mapping['roles'])} roles -> {saved}")
            print_mapping(mapping, None)
            return 0

        parser.error("choose one of --list, --map, --show, --templates")
    except GwsError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
