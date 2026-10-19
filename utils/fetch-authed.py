#!/usr/bin/env python3
"""Fetch URLs that need a logged-in browser session, using a Playwright storage state.

Many Red Hat source systems (content.redhat.com, source.redhat.com,
saleshub.redhat.com, partnercentral.redhat.com) serve nothing useful to an
anonymous client. A Playwright MCP session already holds the cookies; dump them
once with

    await page.context().storageState({ path: '/tmp/state.json' })

and this utility replays them with plain HTTP, which is far cheaper per source
than driving the browser for every document.

What it does:
  * sends the cookies from a Playwright ``storageState`` JSON that match the
    request host
  * follows redirects, saves the raw body
  * optionally renders the body to text -- PDF via ``pdftotext -layout``,
    HTML via ``utils/extract-html-text.py``

Usage::

    # one URL, save raw bytes and a text rendering next to it
    python3 utils/fetch-authed.py --state /tmp/state.json \
        --out-dir /tmp/src https://content.redhat.com/.../guide.pdf --text

    # many URLs listed one per line (blank lines and #comments ignored);
    # an optional "<url> <slug>" second field names the output file
    python3 utils/fetch-authed.py --state /tmp/state.json \
        --out-dir /tmp/src --urls-file /tmp/urls.txt --text

    # print the text straight to stdout instead of writing files
    python3 utils/fetch-authed.py --state /tmp/state.json --stdout <url>

Exit status is 0 when every URL returned 2xx, 1 otherwise. A per-URL summary is
always printed to stderr so a failed source can be recorded rather than
silently dropped.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zlib
from http.cookiejar import Cookie, CookieJar
from pathlib import Path
from urllib.parse import urlparse, unquote

UTILS_DIR = Path(__file__).resolve().parent
HTML_EXTRACTOR = UTILS_DIR / "extract-html-text.py"

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


# --------------------------------------------------------------------------
# cookies
# --------------------------------------------------------------------------


def load_storage_state(path: Path) -> list[dict]:
    """Return the cookie list from a Playwright storageState JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    cookies = data.get("cookies")
    if not isinstance(cookies, list):
        raise ValueError(f"{path}: no 'cookies' array -- not a Playwright storage state")
    return cookies


def domain_matches(cookie_domain: str, host: str) -> bool:
    cookie_domain = cookie_domain.lstrip(".").lower()
    host = host.lower()
    return host == cookie_domain or host.endswith("." + cookie_domain)


def build_jar(cookies: list[dict], host: str) -> CookieJar:
    jar = CookieJar()
    for c in cookies:
        domain = str(c.get("domain", ""))
        if not domain or not domain_matches(domain, host):
            continue
        jar.set_cookie(
            Cookie(
                version=0,
                name=str(c.get("name", "")),
                value=str(c.get("value", "")),
                port=None,
                port_specified=False,
                domain=domain if domain.startswith(".") else "." + domain,
                domain_specified=True,
                domain_initial_dot=domain.startswith("."),
                path=str(c.get("path", "/")) or "/",
                path_specified=True,
                secure=bool(c.get("secure", True)),
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={},
                rfc2109=False,
            )
        )
    return jar


# --------------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------------


def decode_body(raw: bytes, encoding: str | None) -> bytes:
    if not encoding:
        return raw
    encoding = encoding.lower()
    try:
        if encoding == "gzip":
            return gzip.decompress(raw)
        if encoding == "deflate":
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    except Exception:
        return raw
    return raw


def fetch(url: str, cookies: list[dict], timeout: int = 90) -> tuple[int, str, bytes]:
    """Return (status, content_type, body). Raises on transport failure."""
    host = urlparse(url).hostname or ""
    jar = build_jar(cookies, host)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_UA,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
            body = decode_body(raw, resp.headers.get("Content-Encoding"))
            return resp.status, resp.headers.get("Content-Type", ""), body
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        body = decode_body(raw, exc.headers.get("Content-Encoding") if exc.headers else None)
        return exc.code, (exc.headers.get("Content-Type", "") if exc.headers else ""), body


# --------------------------------------------------------------------------
# text rendering
# --------------------------------------------------------------------------


def pdf_to_text(path: Path) -> str | None:
    if not shutil.which("pdftotext"):
        return None
    out = path.with_suffix(".txt")
    try:
        subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), str(out)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"  pdftotext failed: {exc.stderr.decode(errors='replace')[:200]}\n")
        return None
    return out.read_text(encoding="utf-8", errors="replace")


def html_to_text(path: Path) -> str | None:
    if not HTML_EXTRACTOR.exists():
        return strip_tags(path.read_text(encoding="utf-8", errors="replace"))
    try:
        proc = subprocess.run(
            [sys.executable, str(HTML_EXTRACTOR), str(path)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return strip_tags(path.read_text(encoding="utf-8", errors="replace"))
    return proc.stdout.decode("utf-8", errors="replace")


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# --------------------------------------------------------------------------
# naming
# --------------------------------------------------------------------------


def slugify(value: str) -> str:
    value = unquote(value)
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return value[:90] or "document"


def default_slug(url: str) -> str:
    parsed = urlparse(url)
    tail = parsed.path.rsplit("/", 1)[-1]
    if not tail or tail in ("index.html", "/"):
        tail = parsed.path.strip("/").replace("/", "-") or parsed.netloc
    stem = tail.rsplit(".", 1)[0] if "." in tail else tail
    if parsed.query:
        stem = f"{stem}-{parsed.query}"
    return slugify(stem)


def extension_for(content_type: str, body: bytes) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if body[:5] == b"%PDF-" or ct == "application/pdf":
        return ".pdf"
    if ct in ("text/html", "application/xhtml+xml"):
        return ".html"
    if ct == "application/json":
        return ".json"
    if ct.startswith("text/"):
        return ".txt"
    if body[:2] == b"PK":
        return ".zip"
    return ".bin"


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def read_url_list(path: Path) -> list[tuple[str, str | None]]:
    entries: list[tuple[str, str | None]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        url = parts[0]
        slug = slugify(parts[1]) if len(parts) > 1 else None
        entries.append((url, slug))
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fetch URLs using cookies from a Playwright storage state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("urls", nargs="*", help="URLs to fetch")
    ap.add_argument("--urls-file", type=Path, help="file of '<url> [slug]' lines")
    ap.add_argument("--state", type=Path, help="Playwright storageState JSON with cookies")
    ap.add_argument("--out-dir", type=Path, default=Path("."), help="directory for saved bodies")
    ap.add_argument("--text", action="store_true", help="also write a .txt rendering")
    ap.add_argument("--stdout", action="store_true", help="print the text rendering, write nothing")
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()

    targets: list[tuple[str, str | None]] = [(u, None) for u in args.urls]
    if args.urls_file:
        targets.extend(read_url_list(args.urls_file))
    if not targets:
        ap.error("no URLs given (positional arguments or --urls-file)")

    cookies: list[dict] = []
    if args.state:
        cookies = load_storage_state(args.state)

    if not args.stdout:
        args.out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for url, slug in targets:
        try:
            status, ctype, body = fetch(url, cookies, timeout=args.timeout)
        except Exception as exc:  # noqa: BLE001 -- report, do not abort the batch
            sys.stderr.write(f"FAIL  {url}\n      transport error: {exc}\n")
            failures += 1
            continue

        ok = 200 <= status < 300
        if not ok:
            failures += 1

        name = (slug or default_slug(url)) + extension_for(ctype, body)

        if args.stdout:
            if body[:5] == b"%PDF-":
                tmp = Path("/tmp") / name
                tmp.write_bytes(body)
                text = pdf_to_text(tmp) or ""
            else:
                text = strip_tags(body.decode("utf-8", errors="replace"))
            sys.stdout.write(text)
            sys.stderr.write(f"{'OK  ' if ok else 'FAIL'}  {status}  {len(body):>9,}B  {url}\n")
            continue

        path = args.out_dir / name
        path.write_bytes(body)
        rendered = ""
        if args.text and ok:
            if path.suffix == ".pdf":
                text = pdf_to_text(path)
            elif path.suffix in (".html", ".txt"):
                text = html_to_text(path)
                if text is not None:
                    path.with_suffix(".txt").write_text(text, encoding="utf-8")
            else:
                text = None
            if text is not None:
                rendered = f"  -> {len(text.split()):,} words"

        sys.stderr.write(
            f"{'OK  ' if ok else 'FAIL'}  {status}  {len(body):>9,}B  {path.name}{rendered}\n"
        )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
