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
  attribution  The closing framework attribution line must name each practice
               or method as a keleo-studio-gas deep link (@rule:report-610).
  length       Body word count (excluding References and the attribution line)
               against the target band.
  structure    Lists top-level headings so the narrative mapping can be eyeballed.
  consistency  Across a set of reports, fixed names (play, TDP, tactic, product)
               must be used identically. Only runs when two or more reports are
               given together with --consistent-terms.

Usage:
    python3 utils/lint-report.py reports/my-report.md
    python3 utils/lint-report.py reports/my-report.md --min-words 3000 --max-words 6000
    python3 utils/lint-report.py reports/my-report.md --checks citations --json
    python3 utils/lint-report.py reports/my-report.md --checks attribution
    python3 utils/lint-report.py reports/my-report.md --strict
    python3 utils/lint-report.py reports/a.md reports/b.md \
        --consistent-terms "Run Commercial Applications" "COTS Application Hosting TDP"

Exit status is 1 if any error-severity finding is reported, else 0.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_user_config

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
# [Author, 2024a](url) — hyperlinked form. Matched independently of the
# enclosing parenthesis so that semicolon-separated groups are seen, e.g.
# ([Red Hat, 2025e](u1); [Red Hat, 2024a](u2)), which RE_CITE_PAREN cannot span.
RE_CITE_LINKED = re.compile(r"\[([^()\[\]]+?),\s*(\d{4}[a-z]?)\]\([^()\s]*\)")
# Author (2024a) — narrative form.
RE_CITE_NARRATIVE = re.compile(
    r"(?<![(\[])\b([A-Z][\w.&'-]*(?:\s+(?:&|and|et|al\.|[A-Z][\w.&'-]*))*)\s+"
    r"\((\d{4}[a-z]?)\)")
# [Author (2024a)](url) — hyperlinked narrative form. The author sits inside
# the link text, so RE_CITE_NARRATIVE's lookbehind rejects it.
RE_CITE_NARRATIVE_LINKED = re.compile(
    r"\[([A-Z][\w.&'-]*(?:\s+(?:&|and|et|al\.|[A-Z][\w.&'-]*))*)\s+"
    r"\((\d{4}[a-z]?)\)\]\([^()\s]*\)")
# Reference entry: "Author, A., & Other, B. (2024a). *Title*. ..."
RE_REF_ENTRY = re.compile(r"^(.+?)\.?\s*\((\d{4}[a-z]?)\)\.\s")

RE_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")

# Closing attribution: a whole-line italic that names the framework(s) used.
# "* " (bullet) and "**" (bold) are excluded by the lookahead.
RE_ITALIC_LINE = re.compile(r"^\*(?![\s*])(.+?)\*$")
RE_ATTRIBUTION_HINT = re.compile(r"\b(?:structured using|frameworks?)\b", re.I)
RE_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# Two or more consecutive capitalised words — a framework name left unlinked.
RE_PROPER_NAME = re.compile(r"\b[A-Z][\w.&-]*(?:\s+[A-Z][\w.&-]*)+")
# How far back from the end of the body the attribution line may sit.
ATTRIBUTION_TAIL_LINES = 5


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
        for pattern in (RE_CITE_PAREN, RE_CITE_LINKED, RE_CITE_NARRATIVE,
                        RE_CITE_NARRATIVE_LINKED):
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


def find_attribution(lines):
    """Return (line number, text) of the closing framework attribution, if any.

    The attribution is a whole-line italic near the end of the report that
    mentions the framework(s) it was structured with. Only the last few
    non-empty lines are considered, so an italic pull-quote earlier in the body
    is not mistaken for it. The line is optional (@rule:report-603), so a
    missing one is not a finding.
    """
    seen = 0
    for n in range(len(lines), 0, -1):
        stripped = lines[n - 1].strip()
        if not stripped:
            continue
        seen += 1
        if seen > ATTRIBUTION_TAIL_LINES:
            break
        match = RE_ITALIC_LINE.match(stripped)
        if match and RE_ATTRIBUTION_HINT.search(match.group(1)):
            return n, match.group(1)
    return None


def count_body_words(body_lines):
    """Count words in the body, excluding the trailing attribution line."""
    attribution = find_attribution(body_lines)
    skip = attribution[0] if attribution else None
    words = 0
    for n, line in enumerate(body_lines, 1):
        stripped = line.strip()
        if stripped == "---" or n == skip:
            continue
        words += len(stripped.split())
    return words


def check_attribution(lines, studio_url):
    """Framework names in the attribution line must be studio deep links.

    A reader who sees "structured using X" should be able to open X. Names are
    detected as runs of two or more capitalised words left outside a markdown
    link (@rule:report-610).
    """
    attribution = find_attribution(lines)
    if not attribution:
        return []

    line_number, text = attribution
    findings = []

    for label, url in RE_MD_LINK.findall(text):
        if "doc=" not in url:
            findings.append({
                "check": "attribution", "severity": "warning", "line": line_number,
                "message": (f"attribution link for {label!r} is not a studio "
                            f"deep link (expected a ?doc= URL)"),
            })
        elif studio_url and not url.startswith(studio_url):
            findings.append({
                "check": "attribution", "severity": "warning", "line": line_number,
                "message": (f"attribution link for {label!r} does not point at "
                            f"the configured studio deployment"),
            })

    remainder = RE_MD_LINK.sub(" ", text)
    for name in RE_PROPER_NAME.findall(remainder):
        findings.append({
            "check": "attribution",
            "severity": "error" if studio_url else "warning",
            "line": line_number,
            "message": (f"framework {name!r} in the attribution line is not a "
                        f"hyperlink — build one with "
                        f"'python3 utils/studio-client.py --link \"{name}\" "
                        f"--markdown'"),
        })
    return findings


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


def check_consistency(docs, terms):
    """Cross-document check: each fixed term must appear in every report.

    A document set (play guide + TDP brief + tactic guides + battle card, or a
    multi-report batch from one method) has to name the same things the same
    way. Reports that each lint clean individually can still disagree.
    """
    findings = []
    for term in terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        counts = {path: len(pattern.findall("\n".join(body)))
                  for path, body in docs}
        missing = [path for path, c in counts.items() if c == 0]
        if missing and len(missing) < len(docs):
            present = ", ".join(f"{Path(p).name}×{c}"
                                for p, c in counts.items() if c)
            findings.append({
                "check": "consistency", "severity": "error", "line": 0,
                "message": f"term {term!r} is absent from "
                           f"{', '.join(Path(p).name for p in missing)} "
                           f"but present in {present}",
            })
        elif not any(counts.values()):
            findings.append({
                "check": "consistency", "severity": "warning", "line": 0,
                "message": f"term {term!r} appears in none of the reports",
            })
    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Lint generated markdown reports against reporting rules")
    parser.add_argument("report", nargs="+",
                        help="Path to the markdown report(s)")
    parser.add_argument("--consistent-terms", nargs="+", metavar="TERM",
                        help="Fixed names (play, TDP, tactic, product) that "
                             "must appear in every report given")
    parser.add_argument("--checks", nargs="+",
                        choices=["terminology", "citations", "attribution",
                                 "length", "structure"],
                        default=["terminology", "citations", "attribution",
                                 "length", "structure"],
                        help="Which checks to run (default: all)")
    parser.add_argument("--studio-url", metavar="URL",
                        help="keleo-studio-gas deployment URL attribution links "
                             "must point at (default: keleoStudioGasUrl from "
                             ".claude/user-config.json)")
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
    studio_url = args.studio_url or load_user_config().get("keleoStudioGasUrl")

    results, bodies = [], []
    for path in args.report:
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError as err:
            print(f"Error: cannot read {path}: {err}", file=sys.stderr)
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
        if "attribution" in args.checks:
            findings += check_attribution(body_lines, studio_url)
        if "length" in args.checks:
            findings += check_length(word_count, args.min_words, args.max_words)

        bodies.append((path, body_lines))
        results.append({
            "report": path,
            "wordCount": word_count,
            "inTextCitations": len(cites),
            "referenceEntries": len(refs),
            "headings": [{"line": n, "level": len(h), "text": t}
                         for n, h, t in headings],
            "findings": findings,
            "_headings": headings,
        })

    shared = (check_consistency(bodies, args.consistent_terms)
              if args.consistent_terms else [])

    errors = sum(1 for r in results for f in r["findings"]
                 if f["severity"] == "error")
    errors += sum(1 for f in shared if f["severity"] == "error")

    if args.json:
        payload = {"reports": [{k: v for k, v in r.items()
                                if not k.startswith("_")} for r in results]}
        if args.consistent_terms:
            payload["consistency"] = shared
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1 if errors else 0

    for i, r in enumerate(results):
        if i:
            print()
        print(f"{r['report']}: {r['wordCount']} words, "
              f"{r['inTextCitations']} distinct in-text citations, "
              f"{r['referenceEntries']} reference entries")

        if "structure" in args.checks:
            print("\nHeadings:")
            for n, hashes, text in r["_headings"]:
                print(f"  {'  ' * (len(hashes) - 1)}{hashes} {text}  (line {n})")

        if r["findings"]:
            print()
            for f in sorted(r["findings"], key=lambda f: (f["check"], f["line"])):
                where = f"line {f['line']}" if f["line"] else "document"
                print(f"  [{f['severity']}] {f['check']} ({where}): {f['message']}")
        else:
            print("\nNo issues found.")

    if args.consistent_terms:
        print(f"\nCross-document consistency ({len(args.report)} reports):")
        if shared:
            for f in shared:
                print(f"  [{f['severity']}] {f['check']}: {f['message']}")
        else:
            print("  All terms used consistently.")

    total = sum(len(r["findings"]) for r in results) + len(shared)
    if total:
        print(f"\n{errors} error(s), {total - errors} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
