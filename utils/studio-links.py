#!/usr/bin/env python3
"""Build Studio document links after names have been verified through MCP."""

import argparse
from urllib.parse import quote


__version__ = "1.0.0"


def attribution(url, names):
    links = [f"[{name}]({url}?doc={quote(name, safe='')})" for name in names]
    if len(links) == 1:
        return f"*Structured using the {links[0]} framework.*"
    joined = f"{', '.join(links[:-1])}{',' if len(links) > 2 else ''} and {links[-1]}"
    return f"*Structured using the {joined} frameworks.*"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Studio deployment /exec URL")
    parser.add_argument("names", nargs="+", help="Published document names verified with Studio MCP")
    args = parser.parse_args()
    if not args.url.startswith("https://") or "?" in args.url or "#" in args.url:
        parser.error("--url must be an HTTPS deployment URL without a query or fragment")
    print(attribution(args.url.rstrip("/"), args.names))


if __name__ == "__main__":
    main()
