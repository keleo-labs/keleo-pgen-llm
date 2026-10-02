#!/usr/bin/env python3
"""Lint a generated markdown report against the reporting-foundation rules.

Checks the mechanical constraints every reporting skill must satisfy before a
report is handed over:

  terminology  Keleo / Practice Language vocabulary must not leak into the
               output (@rule:report-600). High-confidence terms are errors;
               ordinary-English words that are also Keleo terms (baseline,
               practice, persona) are reported only under --strict.
  citations    Every ## References entry needs a matching in-text citation and
               every in-text citation needs an entry (@rule:report-607/608).
               Author-year keys are matched on surnames, so "Naikwadi &
               Kulari, 2023" matches "Naikwadi, S., & Kulari, V. B. (2023)".
  length       Body word count (excluding References and the attribution line)
               against the target band.
  structure    Lists top-level headings so the narrative mapping can be eyeballed.

Usage:
    python3 utils/lint-report.py reports/my-report.md
    python3 utils/lint-report.py reports/my-report.md --min-words 3000 --max-words 6000
    python3 utils/lint-report.py reports/my-report.md --checks citations --json
    python3 utils/lint-report.py reports/my-report.md --strict

Exit status is 1 if any error-severity finding is reported, else 0.
"""

import argparse
import json
import re
import sys

# Terms that have no innocent reading in a plain-English report.
LEAK_TERMS = [
    "alpha", "alphas", "activityspace", "activity space", "activity spaces",
    "workproduct", "work product", "work products", "narrativetype",
    "narrative type", "narrative types", "narrative element",
    "narrative elements", "contributesto", "mapsto", "partof", "relatesto",
    "worksonalpha", "baselinepracticename", "practiceelement",
    "practice element", "levelofdetail", "level of detail", "levels of detail",
    "practice language", "keleo", "baseline practice", "practice baseline",
    "effective context", "persona group", "pattern group", "pattern view",
    "activity ledby", "schemaversion",
]

# Keleo terms that are also ordinary English — only flagged under --strict.
AMBIGUOUS_TERMS = [
    "baseline", "practice", "practices", "persona", "personas",
    "competency", "competencies", "pattern", "patterns", "outcome", "outcomes",
]

# ([Author, 2024a](url)) and (Author, 2024a) — parenthetical form.
RE_CITE_PAREN = re.compile(
    r"\((?:\[)?([^()\[\]]+?),\s*(\d{4}[a-z]?)(?:\]\([^()]*\))?\)")
# Author (2024a) — narrative form.
RE_CITE_NARRATIVE = re.compile(
    r"(?<![(\[])\b([A-Z][\w.&'-]*(?:\s+(?:&|and|et|al\.|[A-Z][\w.&'-]*))*)\s+"
    r"\((\d{4}[a-z]?)\)")
# Reference entry: "Author, A., & Other, B. (2024a). *Title*. ..."
RE_REF_ENTRY = re.compile(r"^(.+?)\.?\s*\((\d{4}[a-z]?)\)\.\s")

RE_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")


def surnames(author_text):
    """Reduce an author string to a tuple of lowercase surnames.

    Handles corporate authors with no initials ("Red Hat"), reference-list form
    ("Naikwadi, S., & Kulari, V. B.") and in-text form ("Naikwadi & Kulari").
    """
    text = author_text.replace(" and ", " & ").strip()
    names = []
    for chunk in re.split(r"\s*&\s*|;\s*", text):
        chunk = chunk.strip().rstrip(",.")
        if not chunk or chunk.lower() in ("et al", "et al."):
            continue
        # "Naikwadi, S." -> "Naikwadi"; corporate names have no initials.
        head = chunk.split(",")[0].strip()
        # Drop trailing initials left in forms like "Kulari V. B.".
        head = re.sub(r"(\s+[A-Z]\.)+$", "", head).strip()
        if head:
            names.append(head.casefold())
    return tuple(names)


def parse_sections(lines):
    """Split the document into (body_lines, reference_lines).

    Everything from the ## References heading onward is the reference section.
    """
    for i, line in enumerate(lines):
        if re.match(r"^##\s+References\s*$", line.strip(), re.IGNORECASE):
            return lines[:i], lines[i + 1:]
    return lines, []


def find_in_text_citations(body_lines):
    """Return {(surnames, year): [line numbers]} for in-text citations."""
    cites = {}
    for n, line in enumerate(body_lines, 1):
        for pattern in (RE_CITE_PAREN, RE_CITE_NARRATIVE):
            for match in pattern.finditer(line):
                author, year = match.group(1), match.group(2)
                key = (surnames(author), year)
                if not key[0]:
                    continue
                cites.setdefault(key, []).append(n)
    return cites


def find_reference_entries(ref_lines, offset):
    """Return {(surnames, year): line number} for reference-list entries."""
    refs = {}
    for n, line in enumerate(ref_lines, offset + 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-", "*", "|", ">")):
            continue
        match = RE_REF_ENTRY.match(stripped)
        if not match:
            continue
        key = (surnames(match.group(1)), match.group(2))
        if key[0]:
            refs[key] = n
    return refs


def _label(key):
    return f"{' & '.join(s.title() for s in key[0])}, {key[1]}"


def check_terminology(lines, strict):
    """Flag Keleo vocabulary appearing in the report text."""
    findings = []
    terms = [(t, "error") for t in LEAK_TERMS]
    if strict:
        terms += [(t, "warning") for t in AMBIGUOUS_TERMS]
    patterns = [(re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE), t, sev)
                for t, sev in terms]

    in_code = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for pattern, term, severity in patterns:
            if pattern.search(line):
                findings.append({
                    "check": "terminology", "severity": severity, "line": n,
                    "message": f"Keleo vocabulary '{term}' appears in report text",
                })
    return findings


def check_citations(cites, refs, min_count, max_count):
    """Check bidirectional in-text <-> reference-list correspondence."""
    findings = []
    for key, line_numbers in sorted(cites.items()):
        if key not in refs:
            findings.append({
                "check": "citations", "severity": "error",
                "line": line_numbers[0],
                "message": (f"in-text citation ({_label(key)}) has no entry in "
                            f"## References"),
            })
    for key, line_number in sorted(refs.items(), key=lambda kv: kv[1]):
        if key not in cites:
            findings.append({
                "check": "citations", "severity": "error", "line": line_number,
                "message": (f"reference entry ({_label(key)}) is never cited "
                            f"in the text"),
            })
    if min_count is not None and len(refs) < min_count:
        findings.append({
            "check": "citations", "severity": "warning", "line": 0,
            "message": f"{len(refs)} references, below the target of {min_count}",
        })
    if max_count is not None and len(refs) > max_count:
        findings.append({
            "check": "citations", "severity": "warning", "line": 0,
            "message": f"{len(refs)} references, above the target of {max_count}",
        })
    return findings


def count_body_words(body_lines):
    """Count words in the body, excluding the trailing attribution line."""
    words = 0
    for line in body_lines:
        stripped = line.strip()
        if stripped == "---" or (stripped.startswith("*Structured using")):
            continue
        words += len(stripped.split())
    return words


def check_length(word_count, min_words, max_words):
    findings = []
    if min_words is not None and word_count < min_words:
        findings.append({
            "check": "length", "severity": "warning", "line": 0,
            "message": f"{word_count} words, below the target band of {min_words}",
        })
    if max_words is not None and word_count > max_words:
        findings.append({
            "check": "length", "severity": "warning", "line": 0,
            "message": f"{word_count} words, above the target band of {max_words}",
        })
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Lint a generated markdown report against reporting rules")
    parser.add_argument("report", help="Path to the markdown report")
    parser.add_argument("--checks", nargs="+",
                        choices=["terminology", "citations", "length", "structure"],
                        default=["terminology", "citations", "length", "structure"],
                        help="Which checks to run (default: all)")
    parser.add_argument("--min-words", type=int,
                        help="Lower bound of the target word band")
    parser.add_argument("--max-words", type=int,
                        help="Upper bound of the target word band")
    parser.add_argument("--min-citations", type=int,
                        help="Lower bound of the target citation count")
    parser.add_argument("--max-citations", type=int,
                        help="Upper bound of the target citation count")
    parser.add_argument("--strict", action="store_true",
                        help="Also flag ordinary-English words that are Keleo terms")
    parser.add_argument("--json", action="store_true",
                        help="Emit findings as JSON")
    args = parser.parse_args()

    try:
        with open(args.report, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as err:
        print(f"Error: cannot read {args.report}: {err}", file=sys.stderr)
        return 2

    body_lines, ref_lines = parse_sections(lines)
    cites = find_in_text_citations(body_lines)
    refs = find_reference_entries(ref_lines, len(body_lines))
    word_count = count_body_words(body_lines)
    headings = [(n, m.group(1), m.group(2))
                for n, line in enumerate(lines, 1)
                if (m := RE_HEADING.match(line))]

    findings = []
    if "terminology" in args.checks:
        findings += check_terminology(body_lines, args.strict)
    if "citations" in args.checks:
        findings += check_citations(cites, refs,
                                    args.min_citations, args.max_citations)
    if "length" in args.checks:
        findings += check_length(word_count, args.min_words, args.max_words)

    errors = sum(1 for f in findings if f["severity"] == "error")

    if args.json:
        print(json.dumps({
            "report": args.report,
            "wordCount": word_count,
            "inTextCitations": len(cites),
            "referenceEntries": len(refs),
            "headings": [{"line": n, "level": len(h), "text": t}
                         for n, h, t in headings],
            "findings": findings,
        }, indent=2, ensure_ascii=False))
        return 1 if errors else 0

    print(f"{args.report}: {word_count} words, {len(cites)} distinct in-text "
          f"citations, {len(refs)} reference entries")

    if "structure" in args.checks:
        print("\nHeadings:")
        for n, hashes, text in headings:
            print(f"  {'  ' * (len(hashes) - 1)}{hashes} {text}  (line {n})")

    if findings:
        print()
        for f in sorted(findings, key=lambda f: (f["check"], f["line"])):
            where = f"line {f['line']}" if f["line"] else "document"
            print(f"  [{f['severity']}] {f['check']} ({where}): {f['message']}")
        warnings = len(findings) - errors
        print(f"\n{errors} error(s), {warnings} warning(s)")
    else:
        print("\nNo issues found.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
