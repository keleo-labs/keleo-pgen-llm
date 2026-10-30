#!/usr/bin/env python3
"""Collect configured news mail by actual headers, with pagination and a resumable cache.

Version: 2.1.0. Read-only Google operations; writes evidence under --out-dir.
Usage: collect-news-mail.py --start RFC3339 --end RFC3339 --out-dir PATH
The series-local --state is required. No third-party packages.
"""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from email.utils import getaddresses
import json
from pathlib import Path
import re
import subprocess
import threading
import time

REQUEST_LOCK = threading.Lock()
LAST_REQUEST = 0.0


def gws(resource, params):
    global LAST_REQUEST
    with REQUEST_LOCK:
        time.sleep(max(0, 1.0 - (time.monotonic() - LAST_REQUEST)))
        LAST_REQUEST = time.monotonic()
    result = subprocess.run(
        ["gws", "gmail", "users", *resource, "--params", json.dumps(params)],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])
    return json.loads(result.stdout)


def qualifies(headers, sources):
    fields = {}
    for header in headers:
        fields.setdefault(header["name"].lower(), []).append(header["value"])
    senders = {address.lower() for _, address in getaddresses(fields.get("from", []))}
    allowed = set(sources["senderEmails"])
    allowed.update(sources.get("leadershipRoster", {}).get("emails", []))
    if senders & {address.lower() for address in allowed}:
        return True
    recipients = " ".join(value for name in ("to", "cc", "delivered-to", "list-id", "list-post")
                          for value in fields.get(name, []))
    # List-Id commonly uses group.domain rather than group@domain.
    locals_ = re.findall(r"([a-z0-9_+.-]+)(?:@|\.redhat\.)", recipients.lower())
    return any(local in sources["groupLocalParts"] or
               any(part.lower() in local for part in sources["groupLocalPartContains"])
               for local in locals_)


def body_text(part):
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        raw = part["body"]["data"]
        return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8", "replace")
    return "\n".join(body_text(child) for child in part.get("parts", []))


def selected_ids(messages, cached, sources, all_candidates=False):
    if all_candidates:
        return list(messages)
    return [identity for identity in messages if identity in cached and
            qualifies(cached[identity].get("payload", {}).get("headers", []), sources)]


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def collect(args):
    sources = json.loads(Path(args.state).read_text())["sources"]
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=True)
    start = int(datetime.fromisoformat(args.start.replace("Z", "+00:00")).timestamp())
    end = int(datetime.fromisoformat(args.end.replace("Z", "+00:00")).timestamp())
    if end <= start:
        raise ValueError("--end must be after --start")
    query = f"after:{start} before:{end}" + (f" ({args.query})" if args.query else "")
    messages, pages, cursor = {}, 0, None
    while True:
        params = {"userId": "me", "q": query, "maxResults": 500}
        if cursor:
            params["pageToken"] = cursor
        page = gws(["messages", "list"], params)
        messages.update({message["id"]: message for message in page.get("messages", [])})
        pages += 1
        cursor = page.get("nextPageToken")
        if not cursor:
            break
    print(f"Window contains {len(messages)} messages across {pages} pages", flush=True)
    metadata_path = output / "mail-metadata.json"
    cached = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    errors = []
    missing = [] if args.all_candidates else [identity for identity in messages if identity not in cached]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(gws, ["messages", "get"], {
            "userId": "me", "id": identity, "format": "metadata",
            "metadataHeaders": ["From", "To", "Cc", "Delivered-To", "List-Id", "List-Post", "Subject", "Date"],
        }): identity for identity in missing}
        for index, future in enumerate(as_completed(futures), 1):
            identity = futures[future]
            try:
                cached[identity] = future.result()
            except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                errors.append({"id": identity, "error": str(error)})
                if len(errors) <= 3:
                    print(f"Metadata error: {error}", flush=True)
            if index % 100 == 0:
                write_json(metadata_path, cached)
                write_json(output / "mail-errors.json", errors)
                print(f"Checked {index}/{len(missing)} headers; {len(errors)} errors", flush=True)
    write_json(metadata_path, cached)
    selected = selected_ids(messages, cached, sources, args.all_candidates)
    full_path = output / "mail-messages.json"
    full = json.loads(full_path.read_text()) if full_path.exists() else {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(gws, ["messages", "get"], {
            "userId": "me", "id": identity, "format": "full",
        }): identity for identity in selected if identity not in full}
        for index, future in enumerate(as_completed(futures), 1):
            identity = futures[future]
            try:
                full[identity] = future.result()
            except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                errors.append({"id": identity, "error": str(error)})
            if index % 100 == 0:
                write_json(full_path, full)
                print(f"Read {index}/{len(futures)} message bodies; {len(errors)} errors", flush=True)
    write_json(full_path, full)
    summary = []
    for identity in selected:
        if identity not in full:
            continue
        message = full[identity]
        headers = {header["name"].lower(): header["value"]
                   for header in message.get("payload", {}).get("headers", [])}
        text = body_text(message.get("payload", {}))
        # Retain bottom-posted responses; remove quoted lines, not everything after "On".
        unquoted = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))
        summary.append({"id": identity, "threadId": message["threadId"],
                        "internalDate": message.get("internalDate"), "headers": headers,
                        "text": unquoted, "snippet": message.get("snippet", "")})
    summary.sort(key=lambda message: int(message.get("internalDate") or 0))
    write_json(output / "mail-selected.json", summary)
    write_json(output / "mail-errors.json", errors)
    coverage = {"version": "1.0.0", "start": args.start, "end": args.end,
                "query": query, "pages": pages, "windowMessages": len(messages),
                "headersRead": len([identity for identity in messages if identity in cached or identity in full]),
                "selectedMessages": len(selected), "bodiesRead": len(summary), "errors": errors,
                "leadershipRosterResolved": bool(sources.get("leadershipRoster"))}
    write_json(output / "mail-coverage.json", coverage)
    print(json.dumps({**coverage, "errors": len(errors)}), flush=True)


def self_test():
    sources = {"senderEmails": ["leader@example.com"], "groupLocalParts": ["cloud-strategy"],
               "groupLocalPartContains": ["announcements", "emea-techsales"]}
    assert qualifies([{"name": "To", "value": "Team <x-emea-techsales-ecotech@example.com>"}], sources)
    assert qualifies([{"name": "List-Id", "value": "<cloud-strategy.redhat.com>"}], sources)
    assert qualifies([{"name": "From", "value": "Leader <leader@example.com>"}], sources)
    assert not qualifies([{"name": "Subject", "value": "cloud-strategy announcements"}], sources)
    assert not qualifies([{"name": "To", "value": "not-cloud-strategy@example.com"}], sources)
    assert body_text({"mimeType": "text/plain", "body": {"data": "SGVsbG8"}}) == "Hello"
    assert selected_ids({"a": {}, "b": {}}, {}, sources, True) == ["a", "b"]
    assert selected_ids({"a": {}}, {}, sources) == []
    print("8 checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="2.1.0")
    parser.add_argument("--state")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--out-dir")
    parser.add_argument("--query", help="Optional Gmail candidate query; actual headers still determine inclusion")
    parser.add_argument("--all-candidates", action="store_true", help="Collect all matches of the required --query without a sender/group filter")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_test:
        self_test()
    elif arguments.all_candidates and not arguments.query:
        parser.error("--all-candidates requires an explicit --query")
    elif not all((arguments.state, arguments.start, arguments.end, arguments.out_dir)):
        parser.error("--state, --start, --end and --out-dir are required")
    else:
        collect(arguments)
