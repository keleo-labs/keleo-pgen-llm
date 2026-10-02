"""Thin wrapper around the `gws` CLI for Slides and Drive calls.

Exists because two things bite every caller:

1. `gws` prints a human preamble ("Using keyring backend: keyring") to stdout
   before the JSON body, so `json.loads` on raw stdout fails.
2. An unmasked `presentations.get` on a real deck returns tens of megabytes.
   Callers must pass a `fields` mask; `get_presentation` makes that mandatory.
"""

from __future__ import annotations

import json
import shutil
import subprocess

GWS = "gws"
# Drive export ceiling for Google-native files; larger decks need /export instead.
EXPORT_SIZE_LIMIT = 10 * 1024 * 1024


class GwsError(RuntimeError):
    """A gws invocation failed or returned something unparseable."""


def _require_cli() -> None:
    if shutil.which(GWS) is None:
        raise GwsError(
            "the `gws` CLI is not on PATH — install it or run `gws auth login`"
        )


def _strip_preamble(raw: str) -> str:
    """Drop any non-JSON lines gws emits before the payload."""
    for i, ch in enumerate(raw):
        if ch in "{[":
            return raw[i:]
    return raw.strip()


def run(args: list[str], *, parse: bool = True, timeout: int = 120):
    """Invoke gws and return parsed JSON (or raw text when parse=False)."""
    _require_cli()
    proc = subprocess.run(
        [GWS, *args], capture_output=True, text=True, timeout=timeout
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise GwsError(f"gws {' '.join(args[:3])} failed: {detail[:500]}")

    if not parse:
        return proc.stdout

    body = _strip_preamble(proc.stdout)
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise GwsError(
            f"gws {' '.join(args[:3])} returned unparseable output: {body[:300]}"
        ) from exc


def _params(obj: dict) -> list[str]:
    return ["--params", json.dumps(obj)]


# --- Slides -----------------------------------------------------------------


def get_presentation(presentation_id: str, fields: str) -> dict:
    """Fetch a presentation. `fields` is required to keep responses small."""
    if not fields:
        raise ValueError("a fields mask is required — unmasked gets can exceed 10MB")
    return run(
        [
            "slides",
            "presentations",
            "get",
            *_params({"presentationId": presentation_id, "fields": fields}),
        ]
    )


def batch_update(presentation_id: str, requests: list[dict]) -> dict:
    """Apply a batch of update requests. Slides validates all-or-nothing."""
    if not requests:
        return {}
    return run(
        [
            "slides",
            "presentations",
            "batchUpdate",
            *_params({"presentationId": presentation_id}),
            "--json",
            json.dumps({"requests": requests}),
        ]
    )


def get_thumbnail(presentation_id: str, page_object_id: str, size: str = "MEDIUM") -> str:
    """Return a short-lived URL for a rendered thumbnail of one slide."""
    result = run(
        [
            "slides",
            "presentations",
            "pages",
            "getThumbnail",
            *_params(
                {
                    "presentationId": presentation_id,
                    "pageObjectId": page_object_id,
                    "thumbnailProperties.thumbnailSize": size,
                }
            ),
        ]
    )
    return result.get("contentUrl", "")


# --- Drive ------------------------------------------------------------------


def copy_file(file_id: str, name: str, parent: str | None = None) -> dict:
    """Copy a Drive file. Copying a Slides deck carries its masters and theme."""
    body: dict = {"name": name}
    if parent:
        body["parents"] = [parent]
    return run(
        [
            "drive",
            "files",
            "copy",
            *_params({"fileId": file_id, "fields": "id,name,webViewLink"}),
            "--json",
            json.dumps(body),
        ]
    )


def upload_as_slides(path: str, name: str, parent: str | None = None) -> dict:
    """Upload a .pptx and have Drive convert it to a native Slides deck.

    Conversion is what makes the result editable in Slides rather than an
    attached Office file, and it is requested by naming the Google MIME type
    in the metadata body while the upload itself stays .pptx.
    """
    body: dict = {"name": name, "mimeType": "application/vnd.google-apps.presentation"}
    if parent:
        body["parents"] = [parent]
    return run(
        [
            "drive",
            "files",
            "create",
            "--upload",
            path,
            *_params({"fields": "id,name,webViewLink"}),
            "--json",
            json.dumps(body),
        ],
        timeout=300,
    )


def trash_file(file_id: str) -> dict:
    """Move a file to the Drive trash (recoverable, unlike a hard delete)."""
    return run(
        [
            "drive",
            "files",
            "update",
            *_params({"fileId": file_id, "fields": "id,trashed"}),
            "--json",
            json.dumps({"trashed": True}),
        ]
    )


def export_file(file_id: str, mime_type: str, output: str) -> str:
    """Export a Google-native file to `output`, returning the path."""
    run(
        [
            "drive",
            "files",
            "export",
            *_params({"fileId": file_id, "mimeType": mime_type}),
            "--output",
            output,
        ],
        parse=False,
        timeout=300,
    )
    return output


def file_link(file_id: str) -> str:
    return f"https://docs.google.com/presentation/d/{file_id}/edit"
