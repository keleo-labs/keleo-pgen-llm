#!/usr/bin/env python3
"""Resolve section references in practice JSON files to anchored URLs.

When references and citations point to long HTML documents, the URLs
typically point to the document root. This script uses an anchor map
(heading text -> anchor ID) to append #fragment identifiers based on
section references found in surrounding context (descriptions, names,
link text, pages fields).

The anchor map can come from a JSON file (produced by extract-html-text.py
--anchors) or be fetched live from a URL.

Usage:
    # Dry run with anchor map file
    python3 utils/resolve-doc-anchors.py practice.json --anchors /tmp/anchors.json

    # Fix mode: apply changes
    python3 utils/resolve-doc-anchors.py practice.json --anchors /tmp/anchors.json --fix

    # Fetch anchors from URL directly
    python3 utils/resolve-doc-anchors.py practice.json --url http://localhost:8080/docs/.../index/

    # Machine-readable output
    python3 utils/resolve-doc-anchors.py practice.json --anchors /tmp/anchors.json --json

    # Dump the heading -> anchor map for a document (no practice JSON needed).
    # Use this when authoring citations and references by hand so that URLs
    # carry a verified #fragment instead of pointing at the document root.
    python3 utils/resolve-doc-anchors.py --url https://docs.redhat.com/.../index --dump-anchors
    python3 utils/resolve-doc-anchors.py --url https://docs.redhat.com/.../index \\
        --dump-anchors --grep sigstore
"""

import argparse
import html.parser
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


# ---------------------------------------------------------------------------
# Section reference extraction
# ---------------------------------------------------------------------------

# "Section 5.4.1 'Creating the image set configuration'"
# "Section 5.4.1 \"Creating the image set configuration\""
# "(Section 5.4.1 'Title')" — parenthetical
_SECTION_TITLE_RE = re.compile(
    r"""(?:Section|section)\s+
        (\d+(?:\.\d+)*)                     # section number
        \s*['‘“"]\s*              # opening quote (straight or curly)
        ([^'"’”]+?)               # title text
        \s*['’”"]\s*              # closing quote
    """,
    re.VERBOSE,
)

# "Chapter N. Title" or "Chapter N Title"
_CHAPTER_RE = re.compile(
    r"""Chapter\s+(\d+)                     # chapter number
        \.?\s+                              # optional period + space
        ([A-Z][^.;,\n]{2,60})              # title (starts uppercase, reasonable length)
    """,
    re.VERBOSE,
)

# "Sections X.Y.Z and A.B.C" — multiple sections
_SECTIONS_AND_RE = re.compile(
    r"""(?:Sections?|sections?)\s+
        (\d+(?:\.\d+)*)                     # first section number
        (?:\s+and\s+|\s*,\s*)               # separator
        (\d+(?:\.\d+)*)                     # second section number
    """,
    re.VERBOSE,
)

# Bare section number in context: "see 5.4.1" or "5.4.1"
_BARE_SECTION_RE = re.compile(
    r"""(?:see\s+|per\s+|in\s+|from\s+)?    # optional lead-in
        (\d+\.\d+(?:\.\d+)*)               # section number (at least X.Y)
    """,
    re.VERBOSE,
)


def extract_section_refs(text):
    """Extract section references from text.

    Returns list of dicts with keys:
        - number: section/chapter number string (e.g. "5.4.1")
        - title: section title if present, else None
        - kind: "section", "chapter", or "bare"
    """
    if not text:
        return []

    refs = []
    seen = set()

    # Section with title (highest confidence)
    for m in _SECTION_TITLE_RE.finditer(text):
        number = m.group(1)
        title = m.group(2).strip()
        key = ("section", number, title)
        if key not in seen:
            seen.add(key)
            refs.append({"number": number, "title": title, "kind": "section"})

    # Chapter with title
    for m in _CHAPTER_RE.finditer(text):
        number = m.group(1)
        title = m.group(2).strip()
        key = ("chapter", number, title)
        if key not in seen:
            seen.add(key)
            refs.append({"number": number, "title": title, "kind": "chapter"})

    # "Sections X and Y" — extract both numbers without titles
    for m in _SECTIONS_AND_RE.finditer(text):
        for g in (1, 2):
            number = m.group(g)
            key = ("bare", number, None)
            if key not in seen:
                seen.add(key)
                refs.append({"number": number, "title": None, "kind": "bare"})

    # Bare section numbers (lowest confidence — only if nothing better matched)
    if not refs:
        for m in _BARE_SECTION_RE.finditer(text):
            number = m.group(1)
            key = ("bare", number, None)
            if key not in seen:
                seen.add(key)
                refs.append({"number": number, "title": None, "kind": "bare"})

    return refs


# ---------------------------------------------------------------------------
# Anchor matching
# ---------------------------------------------------------------------------

def _normalise(text):
    """Lowercase and collapse whitespace for fuzzy comparison."""
    return re.sub(r"\s+", " ", text.lower().strip())


def match_anchor(section_ref, anchor_map):
    """Match a section reference against the anchor map.

    Args:
        section_ref: dict with number, title, kind
        anchor_map: dict mapping heading text -> anchor ID

    Returns:
        (anchor_id, heading_text) or (None, None)
    """
    number = section_ref["number"]
    title = section_ref["title"]
    kind = section_ref["kind"]

    # Build the prefix to search for
    if kind == "chapter":
        prefix = f"chapter {number}"
    else:
        prefix = number

    best_match = None
    best_heading = None

    for heading, anchor_id in anchor_map.items():
        heading_norm = _normalise(heading)

        # Strategy 1: heading starts with the section/chapter number
        starts_with_number = False
        if kind == "chapter":
            # "chapter 1. about disconnected environments"
            starts_with_number = heading_norm.startswith(f"chapter {number}")
        else:
            # "5.4.1. Creating the image set configuration"
            # Also match "5.4.1 Creating..." (no period)
            starts_with_number = (
                heading_norm.startswith(f"{number}.") or
                heading_norm.startswith(f"{number} ") or
                heading_norm == number
            )

        if starts_with_number:
            # If we also have a title, verify it appears in the heading
            if title:
                title_norm = _normalise(title)
                if title_norm in heading_norm:
                    # Exact match on number + title — highest confidence
                    return anchor_id, heading
                else:
                    # Number matches but title doesn't — still a candidate
                    if best_match is None:
                        best_match = anchor_id
                        best_heading = heading
            else:
                # No title to verify, number match is sufficient
                if best_match is None:
                    best_match = anchor_id
                    best_heading = heading

        # Strategy 2: title appears in heading (even without number match)
        if title and not starts_with_number:
            title_norm = _normalise(title)
            if title_norm in heading_norm:
                # Title match without number — lower confidence, only if no
                # number-based match exists
                if best_match is None:
                    best_match = anchor_id
                    best_heading = heading

    return best_match, best_heading


# ---------------------------------------------------------------------------
# Anchor map fetching from URL
# ---------------------------------------------------------------------------

# Heading text picked up from rendered docs often carries UI affordances that
# are not part of the title, such as a copy-permalink control.
_HEADING_CHROME_RE = re.compile(
    r"\s*(?:Copy link)?\s*(?:Link copied to clipboard!?)\s*$",
    re.IGNORECASE,
)


def _strip_heading_chrome(text):
    """Remove rendered UI affordances from extracted heading text."""
    cleaned = _HEADING_CHROME_RE.sub("", text)
    cleaned = re.sub(r"\s*Copy link\s*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


class _AnchorExtractor(html.parser.HTMLParser):
    """Extract id-bearing headings from HTML.

    Handles two common layouts:

    1. The id sits on the heading itself, or on an <a> inside it.
    2. The id sits on a wrapping <section>/<div> and the heading follows
       inside it. DocBook-derived toolchains (docs.redhat.com, for one)
       render this way, so the heading text must be attached to the most
       recently opened id-bearing container.
    """

    _HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    _CONTAINER_TAGS = {"section", "div", "article"}

    def __init__(self):
        super().__init__()
        self.anchors = {}
        self._in_heading = False
        self._current_id = None
        self._current_text = []
        # Ids from enclosing containers that have not yet been claimed by a
        # heading, most recent last.
        self._pending_container_ids = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag in self._HEADING_TAGS:
            self._in_heading = True
            self._current_id = attrs_dict.get("id")
            self._current_text = []
        elif self._in_heading and tag == "a":
            # Some docs put the id on an <a> inside the heading
            if not self._current_id and attrs_dict.get("id"):
                self._current_id = attrs_dict["id"]
        elif tag in self._CONTAINER_TAGS and attrs_dict.get("id"):
            self._pending_container_ids.append(attrs_dict["id"])

    def handle_endtag(self, tag):
        if tag in self._HEADING_TAGS and self._in_heading:
            self._in_heading = False
            anchor_id = self._current_id
            if not anchor_id and self._pending_container_ids:
                anchor_id = self._pending_container_ids[-1]
            if anchor_id and self._current_text:
                text = " ".join("".join(self._current_text).split())
                text = _strip_heading_chrome(text)
                if text:
                    self.anchors.setdefault(text, anchor_id)
                # The container id is now spoken for.
                if (self._pending_container_ids
                        and self._pending_container_ids[-1] == anchor_id):
                    self._pending_container_ids.pop()
            self._current_id = None
            self._current_text = []

    def handle_data(self, data):
        if self._in_heading:
            self._current_text.append(data)

    def handle_entityref(self, name):
        if self._in_heading:
            self._current_text.append(" " if name == "nbsp" else f"&{name};")

    def handle_charref(self, name):
        if self._in_heading:
            self._current_text.append(" " if name in ("160", "xa0", "xA0") else f"&#{name};")


def fetch_anchors(url, timeout=30):
    """Fetch an HTML page and extract heading anchors.

    Returns dict mapping heading text -> anchor ID.
    """
    req = urllib.request.Request(url)
    # Some documentation CDNs (docs.redhat.com among them) answer HTTP 403 to
    # unrecognised user agents, and also to spoofed browser ones. A plain
    # library user agent is accepted, so keep the default rather than
    # inventing a product string.
    req.add_header("User-Agent", f"Python-urllib/{sys.version_info.major}.{sys.version_info.minor}")
    req.add_header("Accept", "text/html,application/xhtml+xml")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        html_bytes = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        html_text = html_bytes.decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)

    parser = _AnchorExtractor()
    parser.feed(html_text)
    return parser.anchors


# ---------------------------------------------------------------------------
# URL scanning
# ---------------------------------------------------------------------------

def _url_matches_base(url, base_urls):
    """Check if url matches any base URL (ignoring existing fragments)."""
    parsed = urlparse(url)
    url_no_frag = urlunparse(parsed._replace(fragment=""))
    for base in base_urls:
        base_no_frag = urlunparse(urlparse(base)._replace(fragment=""))
        # Exact match or url is a prefix of base (or vice versa)
        if url_no_frag == base_no_frag:
            return True
        # Allow trailing slash differences
        if url_no_frag.rstrip("/") == base_no_frag.rstrip("/"):
            return True
    return False


def _has_fragment(url):
    """Check if URL already has a fragment identifier."""
    return bool(urlparse(url).fragment)


def _append_fragment(url, anchor_id):
    """Append anchor fragment to URL."""
    parsed = urlparse(url)
    return urlunparse(parsed._replace(fragment=anchor_id))


def _gather_context_text(parts):
    """Concatenate non-None text parts for section reference extraction."""
    return " ".join(p for p in parts if p)


def scan_references(data, anchor_map, base_urls):
    """Scan references[].links[] and references[].evidenceBy[].links[] for resolvable URLs.

    Returns list of match dicts.
    """
    matches = []

    for ri, ref in enumerate(data.get("references", [])):
        ref_name = ref.get("name", "")
        ref_desc = ref.get("description", "")

        # Top-level links on the reference (AlphaInstance)
        for li, link in enumerate(ref.get("links", [])):
            uri = link.get("uri", "")
            if not uri or not uri.startswith("http"):
                continue
            if _has_fragment(uri):
                continue
            if not _url_matches_base(uri, base_urls):
                continue

            context_text = _gather_context_text([
                ref_name, ref_desc,
                link.get("name", ""), link.get("description", ""),
                link.get("pages", ""),
            ])
            section_refs = extract_section_refs(context_text)

            for sr in section_refs:
                anchor_id, heading = match_anchor(sr, anchor_map)
                if anchor_id:
                    matches.append({
                        "path": f"references[{ri}].links[{li}].uri",
                        "context_name": ref_name,
                        "link_name": link.get("name", ""),
                        "current_url": uri,
                        "new_url": _append_fragment(uri, anchor_id),
                        "section_ref": sr,
                        "matched_heading": heading,
                        "anchor_id": anchor_id,
                        "obj": link,
                        "field": "uri",
                    })
                    break  # one anchor per link

        # evidenceBy[].links[]
        for ei, ev in enumerate(ref.get("evidenceBy", [])):
            ev_name = ev.get("name", "")
            ev_desc = ev.get("description", "")

            for li, link in enumerate(ev.get("links", [])):
                uri = link.get("uri", "")
                if not uri or not uri.startswith("http"):
                    continue
                if _has_fragment(uri):
                    continue
                if not _url_matches_base(uri, base_urls):
                    continue

                context_text = _gather_context_text([
                    ref_name, ref_desc,
                    ev_name, ev_desc,
                    link.get("name", ""), link.get("description", ""),
                    link.get("pages", ""),
                ])
                section_refs = extract_section_refs(context_text)

                for sr in section_refs:
                    anchor_id, heading = match_anchor(sr, anchor_map)
                    if anchor_id:
                        matches.append({
                            "path": f"references[{ri}].evidenceBy[{ei}].links[{li}].uri",
                            "context_name": f"{ref_name} / {ev_name}",
                            "link_name": link.get("name", ""),
                            "current_url": uri,
                            "new_url": _append_fragment(uri, anchor_id),
                            "section_ref": sr,
                            "matched_heading": heading,
                            "anchor_id": anchor_id,
                            "obj": link,
                            "field": "uri",
                        })
                        break

    return matches


def scan_citations(data, anchor_map, base_urls):
    """Scan citations for URLs matching base documents.

    Checks citation url and source fields.

    Returns list of match dicts.
    """
    matches = []

    for ci, cit in enumerate(data.get("citations", [])):
        cit_name = cit.get("name", "")
        cit_desc = cit.get("description", "")

        # Check citation url field
        url = cit.get("url", "")
        if url and url.startswith("http") and not _has_fragment(url):
            if _url_matches_base(url, base_urls):
                context_text = _gather_context_text([
                    cit_name, cit_desc,
                    cit.get("source", ""),
                    cit.get("pages", ""),
                ])
                section_refs = extract_section_refs(context_text)

                for sr in section_refs:
                    anchor_id, heading = match_anchor(sr, anchor_map)
                    if anchor_id:
                        matches.append({
                            "path": f"citations[{ci}].url",
                            "context_name": cit_name,
                            "link_name": "",
                            "current_url": url,
                            "new_url": _append_fragment(url, anchor_id),
                            "section_ref": sr,
                            "matched_heading": heading,
                            "anchor_id": anchor_id,
                            "obj": cit,
                            "field": "url",
                        })
                        break

        # Check source field if it looks like a URL
        source = cit.get("source", "")
        if source and source.startswith("http") and not _has_fragment(source):
            if _url_matches_base(source, base_urls):
                context_text = _gather_context_text([
                    cit_name, cit_desc,
                    cit.get("pages", ""),
                ])
                section_refs = extract_section_refs(context_text)

                for sr in section_refs:
                    anchor_id, heading = match_anchor(sr, anchor_map)
                    if anchor_id:
                        matches.append({
                            "path": f"citations[{ci}].source",
                            "context_name": cit_name,
                            "link_name": "",
                            "current_url": source,
                            "new_url": _append_fragment(source, anchor_id),
                            "section_ref": sr,
                            "matched_heading": heading,
                            "anchor_id": anchor_id,
                            "obj": cit,
                            "field": "source",
                        })
                        break

    return matches


def find_unmatched(data, base_urls):
    """Find URLs matching base documents that have section context but no anchor.

    Returns list of unmatched entries for reporting.
    """
    unmatched = []

    for ri, ref in enumerate(data.get("references", [])):
        ref_name = ref.get("name", "")
        ref_desc = ref.get("description", "")

        for li, link in enumerate(ref.get("links", [])):
            uri = link.get("uri", "")
            if not uri or not uri.startswith("http"):
                continue
            if _has_fragment(uri):
                continue
            if not _url_matches_base(uri, base_urls):
                continue
            context_text = _gather_context_text([
                ref_name, ref_desc,
                link.get("name", ""), link.get("description", ""),
                link.get("pages", ""),
            ])
            section_refs = extract_section_refs(context_text)
            if section_refs:
                unmatched.append({
                    "path": f"references[{ri}].links[{li}].uri",
                    "context_name": ref_name,
                    "url": uri,
                    "section_refs": section_refs,
                })

        for ei, ev in enumerate(ref.get("evidenceBy", [])):
            ev_name = ev.get("name", "")
            ev_desc = ev.get("description", "")
            for li, link in enumerate(ev.get("links", [])):
                uri = link.get("uri", "")
                if not uri or not uri.startswith("http"):
                    continue
                if _has_fragment(uri):
                    continue
                if not _url_matches_base(uri, base_urls):
                    continue
                context_text = _gather_context_text([
                    ref_name, ref_desc,
                    ev_name, ev_desc,
                    link.get("name", ""), link.get("description", ""),
                    link.get("pages", ""),
                ])
                section_refs = extract_section_refs(context_text)
                if section_refs:
                    unmatched.append({
                        "path": f"references[{ri}].evidenceBy[{ei}].links[{li}].uri",
                        "context_name": f"{ref_name} / {ev_name}",
                        "url": uri,
                        "section_refs": section_refs,
                    })

    return unmatched


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Resolve section references in practice JSON files to anchored URLs"
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Practice/baseline/method JSON file to scan "
             "(not required with --dump-anchors)",
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--anchors",
        metavar="FILE",
        help="Anchor map JSON file (heading text -> anchor ID)",
    )
    source_group.add_argument(
        "--url",
        metavar="URL",
        help="URL to fetch and extract heading anchors from",
    )

    parser.add_argument(
        "--fix", action="store_true",
        help="Apply anchor fragments to matching URLs (default: dry-run report)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as machine-readable JSON",
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="HTTP fetch timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--dump-anchors", action="store_true",
        help="Print the heading -> anchored URL map and exit "
             "(no practice JSON required)",
    )
    parser.add_argument(
        "--grep", metavar="TEXT",
        help="With --dump-anchors, only show headings containing TEXT "
             "(case-insensitive)",
    )

    args = parser.parse_args()

    # Load or fetch anchor map
    if args.anchors:
        anchor_map = load_json(args.anchors)
    else:
        anchor_map = fetch_anchors(args.url, timeout=args.timeout)

    if not anchor_map:
        print("Error: anchor map is empty", file=sys.stderr)
        sys.exit(1)

    # --- Dump mode: report headings and the URLs that address them ---
    if args.dump_anchors:
        base = args.url.rstrip("/") if args.url else ""
        needle = args.grep.lower() if args.grep else None
        rows = [
            (heading, anchor_id)
            for heading, anchor_id in anchor_map.items()
            if needle is None or needle in heading.lower()
        ]
        if args.json:
            print(json.dumps(
                {
                    "base_url": base,
                    "count": len(rows),
                    "anchors": [
                        {
                            "heading": h,
                            "anchor_id": a,
                            "url": f"{base}#{a}" if base else f"#{a}",
                        }
                        for h, a in rows
                    ],
                },
                indent=2,
                ensure_ascii=False,
            ))
        else:
            for heading, anchor_id in rows:
                target = f"{base}#{anchor_id}" if base else f"#{anchor_id}"
                print(f"{heading}\n  {target}\n")
            print(f"{len(rows)} heading(s)")
        return

    if not args.json_file:
        parser.error("json_file is required unless --dump-anchors is used")

    # Load practice JSON
    data = load_json(args.json_file)

    # Determine base URLs from the anchor source
    # When using --url, the URL itself is the base
    # When using --anchors, extract base URLs from matching URLs in the practice JSON
    if args.url:
        base_urls = [args.url.rstrip("/")]
    else:
        # Collect all unique URL roots (scheme + netloc + path without fragment)
        # from the practice JSON that might match this anchor map
        base_urls = set()
        for ref in data.get("references", []):
            for link in ref.get("links", []):
                uri = link.get("uri", "")
                if uri and uri.startswith("http"):
                    parsed = urlparse(uri)
                    base_urls.add(urlunparse(parsed._replace(fragment="")).rstrip("/"))
            for ev in ref.get("evidenceBy", []):
                for link in ev.get("links", []):
                    uri = link.get("uri", "")
                    if uri and uri.startswith("http"):
                        parsed = urlparse(uri)
                        base_urls.add(urlunparse(parsed._replace(fragment="")).rstrip("/"))
        for cit in data.get("citations", []):
            for field in ("url", "source"):
                val = cit.get(field, "")
                if val and val.startswith("http"):
                    parsed = urlparse(val)
                    base_urls.add(urlunparse(parsed._replace(fragment="")).rstrip("/"))
        base_urls = list(base_urls)

    if not base_urls:
        if not args.json:
            print("No URLs found in practice JSON to resolve.")
        else:
            print(json.dumps({"matched": 0, "unmatched": 0, "results": []}))
        return

    # Scan for matches
    ref_matches = scan_references(data, anchor_map, base_urls)
    cit_matches = scan_citations(data, anchor_map, base_urls)
    all_matches = ref_matches + cit_matches

    # Find URLs with section context that didn't match
    all_unmatched = find_unmatched(data, base_urls)
    # Remove entries that did match
    matched_paths = {m["path"] for m in all_matches}
    unmatched = [u for u in all_unmatched if u["path"] not in matched_paths]

    # --- JSON output ---
    if args.json:
        output = {
            "matched": len(all_matches),
            "unmatched": len(unmatched),
            "results": [
                {
                    "path": m["path"],
                    "context_name": m["context_name"],
                    "current_url": m["current_url"],
                    "new_url": m["new_url"],
                    "anchor_id": m["anchor_id"],
                    "matched_heading": m["matched_heading"],
                    "section_ref": {
                        "number": m["section_ref"]["number"],
                        "title": m["section_ref"]["title"],
                        "kind": m["section_ref"]["kind"],
                    },
                }
                for m in all_matches
            ],
            "unresolved": [
                {
                    "path": u["path"],
                    "context_name": u["context_name"],
                    "url": u["url"],
                    "section_refs": u["section_refs"],
                }
                for u in unmatched
            ],
        }
        if args.fix:
            output["applied"] = len(all_matches)
        print(json.dumps(output, indent=2))
    else:
        # --- Text output ---
        if all_matches:
            action = "Applying" if args.fix else "Would resolve"
            print(f"{action} {len(all_matches)} URL(s):\n")
            for m in all_matches:
                sr = m["section_ref"]
                ref_label = sr["number"]
                if sr["title"]:
                    ref_label += f" '{sr['title']}'"
                print(f"  [{sr['kind']}] {m['context_name']}")
                print(f"    Section ref: {ref_label}")
                print(f"    Heading:     {m['matched_heading']}")
                print(f"    {m['path']}")
                print(f"    - {m['current_url']}")
                print(f"    + {m['new_url']}")
                print()
        else:
            print("No matching section references found.")

        if unmatched:
            print(f"\nUnresolved section references ({len(unmatched)}):\n")
            for u in unmatched:
                refs_str = ", ".join(
                    f"{sr['number']}" + (f" '{sr['title']}'" if sr.get("title") else "")
                    for sr in u["section_refs"]
                )
                print(f"  [MISS] {u['context_name']}")
                print(f"    Refs: {refs_str}")
                print(f"    URL:  {u['url']}")
                print()

    # --- Apply fixes ---
    if args.fix and all_matches:
        for m in all_matches:
            m["obj"][m["field"]] = m["new_url"]

        with open(args.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        if not args.json:
            print(f"Wrote {len(all_matches)} anchored URL(s) to {args.json_file}")

    if not args.fix and (all_matches or unmatched):
        if not args.json:
            hints = []
            if all_matches:
                hints.append("--fix to apply anchor fragments")
            print(f"\nRun with {', '.join(hints)}.")
        sys.exit(1 if unmatched else 0)


if __name__ == "__main__":
    main()
