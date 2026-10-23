"""Shared access to cached template mappings.

A mapping is built once per branded template by slides-template.py and then
read by every renderer and exporter, so it lives here rather than in any one
script (`slides-template.py` is not importable — its name has a hyphen).
"""

from __future__ import annotations

import json
from pathlib import Path

CACHE_DIR = Path.home() / ".claude" / "deck-templates"


class TemplateNotFound(FileNotFoundError):
    """No cached mapping exists under the requested name."""


def cache_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.json"


def list_templates() -> list[tuple[str, dict]]:
    """Return (name, mapping) for every cached template."""
    if not CACHE_DIR.is_dir():
        return []
    out = []
    for path in sorted(CACHE_DIR.glob("*.json")):
        try:
            out.append((path.stem, json.loads(path.read_text())))
        except json.JSONDecodeError:
            continue
    return out


def save_mapping(mapping: dict, name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(name)
    path.write_text(json.dumps(mapping, indent=2) + "\n")
    return path


def load_mapping(name: str) -> dict:
    path = cache_path(name)
    if not path.is_file():
        known = ", ".join(n for n, _ in list_templates()) or "none"
        raise TemplateNotFound(
            f"no cached template '{name}' (cached: {known})\n"
            f"build one with: slides-template.py <slides-url> --map --name {name}"
        )
    return json.loads(path.read_text())
