#!/usr/bin/env python3
"""Check that text is safe to publish to a public issue tracker.

The feedback register is internal and the keleo-labs repositories are public, so
anything crossing that boundary has to be checked. A published issue is indexed
and stays reachable by SHA after deletion, which makes this a one-way door.

The check is deny-by-default and mechanical — it makes no judgement about whether
a term is sensitive, only whether it appears. Judgement belongs to the human
reviewing the draft, and this exists so that review has a floor beneath it rather
than being the only safeguard.

Most of the denylist is harvested from the corpus rather than hand-written,
because a hand-written one is always out of date. Tested against the open
backlog, a curated vendor list missed DL380a, Alletra X10000, Aruba CX 6300M and
llm-d; the corpus caught four of those five, because the practices already cite
those products. The fifth was a term reported as *missing* from the corpus, which
no harvest can know about — hence the human gate.

Usage:
    python3 utils/issue-sanitiser.py --build-denylist
    python3 utils/issue-sanitiser.py --check draft.md
    python3 utils/issue-sanitiser.py --check draft.md --json
    echo "some text" | python3 utils/issue-sanitiser.py --check -

Exit codes: 0 clean, 1 findings, 2 could not run.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import get_project_root, load_json_pair

DENYLIST_CACHE = "bundles/.issue-denylist.json"
IDENTITY_SCAN = Path.home() / ".claude/skills/satools-git-guardrails/scripts/identity-scan.py"

# Terms short enough to collide with ordinary prose are skipped during harvest.
MIN_TERM_LENGTH = 4

# A harvested single word that is also ordinary English is dropped. The corpus
# names elements things like "Architecture", "Backlog" and "Benefits", and
# blocking those would flag every second sentence until the gate was ignored —
# which is worse than the narrow false negative it costs. Multi-word terms are
# kept regardless, being specific enough not to collide.
WORDLISTS = ("/usr/share/dict/words", "/usr/dict/words")

# Vendor and platform names that may not appear in the corpus but must never be
# published. A seed, not the whole list — the harvest is what makes it current.
VENDOR_SEED = [
    "Red Hat", "RHEL", "OpenShift", "Ansible", "Satellite", "Quay", "Keycloak",
    "NVIDIA", "Blackwell", "Hopper", "DGX", "HGX", "CUDA", "DCGM", "NVLink",
    "Cisco", "Nexus", "Intersight", "Meraki",
    "Hitachi", "Alletra", "PowerStore", "PowerFlex", "Nutanix", "Aruba",
    "Kyndryl", "Accenture", "Capgemini", "Atos", "Sopra", "Deloitte", "Wipro",
    "Infosys", "Kubernetes", "OpenStack", "VMware", "vSphere", "Proliant",
    "InstructLab", "Granite", "Llama", "Mixtral", "vLLM", "KServe",
]

# Patterns that are never acceptable in published text.
FORBIDDEN_PATTERNS = [
    ("email address",       r'[\w.+-]+@[\w-]+\.[\w.]+'),
    ("Google Workspace URL", r'(docs|drive|script|sheets)\.google\.com\S*'),
    ("internal Red Hat host", r'\b[\w.-]*\.cee\.redhat\.com\S*'),
    ("internal Red Hat site", r'\b(source|console|saleshub|content)\.redhat\.com\S*'),
    ("spreadsheet id",      r'\b[A-Za-z0-9_-]{30,}\b'),
    ("internal gitlab path", r'\bplanify/[\w-]+'),
]

# Engagement language. Not forbidden outright — "a client" can be generic — but a
# draft carrying it needs someone to confirm no real engagement is identifiable.
REVIEW_PATTERNS = [
    ("engagement reference", r"\b(client|customer|engagement|on behalf of|account team)\b"),
]


def _text_terms(value):
    """Yield name-like strings from a harvested value of unknown shape."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        if value.get("name"):
            yield value["name"]
    elif isinstance(value, list):
        for item in value:
            yield from _text_terms(item)


def load_wordlist():
    """Ordinary English words, for filtering generic single-word harvest hits.

    Returns an empty set where no system wordlist exists; the harvest then keeps
    single words, which is the safe direction to fail.
    """
    for path in WORDLISTS:
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                return {w.strip().lower() for w in fh if w.strip()}
        except OSError:
            continue
    return set()


def is_ordinary_word(term, words, protected):
    """Is this a single ordinary English word rather than a name?"""
    if not words or " " in term or "-" in term:
        return False
    if term.lower() in {p.lower() for p in protected}:
        return False
    lower = term.lower()
    # Check the singular too, since the corpus pluralises element names.
    return lower in words or (lower.endswith("s") and lower[:-1] in words)


def _run(cmd, cwd=None):
    """Run a helper utility, returning parsed JSON or None."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=cwd)
        return json.loads(out.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def build_denylist(root):
    """Harvest internal names from the corpus.

    Document names, outcome names and keywords come from library-index.py;
    element and citation names come from the practice JSON directly. Between them
    they cover both the methodology's own vocabulary and the vendor products it
    cites, which is why the harvest beats a curated list.
    """
    terms = set(VENDOR_SEED)
    sources = {"vendorSeed": len(VENDOR_SEED)}

    index = _run([sys.executable, str(root / "utils/library-index.py")], cwd=root)
    before = len(terms)
    for entry in index or []:
        for field in ("name", "outcomes", "keywords"):
            terms.update(_text_terms(entry.get(field)))
    sources["libraryIndex"] = len(terms) - before

    before = len(terms)
    for sub in ("practices", "baselines"):
        base = root / sub
        if not base.is_dir():
            continue
        for path in list(base.glob("*/*.json")) + list(base.glob("*.json")):
            if "backup" in str(path).lower() or path.name.startswith("_"):
                continue
            data, err = load_json_pair(path)
            if err or not isinstance(data, dict):
                continue
            for collection in ("alphas", "workProducts", "activities", "personas",
                               "personaGroups", "patterns", "citations", "outcomes"):
                terms.update(_text_terms(data.get(collection)))
            for citation in data.get("citations", []) or []:
                # Citation names carry vendor product names the practices depend on.
                if isinstance(citation, dict) and citation.get("source"):
                    terms.add(citation["source"])
    sources["corpusElements"] = len(terms) - before

    words = load_wordlist()
    candidates = {t.strip() for t in terms
                  if isinstance(t, str) and len(t.strip()) >= MIN_TERM_LENGTH}
    kept, dropped = set(), []
    for term in candidates:
        if is_ordinary_word(term, words, VENDOR_SEED):
            dropped.append(term)
        else:
            kept.add(term)

    sources["droppedAsOrdinaryEnglish"] = len(dropped)
    cleaned = sorted(kept, key=len, reverse=True)
    return {
        "terms": cleaned,
        "sources": sources,
        "count": len(cleaned),
        "droppedSample": sorted(dropped)[:25],
    }


def load_denylist(root, rebuild=False):
    cache = root / DENYLIST_CACHE
    if not rebuild and cache.exists():
        data, err = load_json_pair(cache)
        if not err and isinstance(data, dict) and data.get("terms"):
            return data
    data = build_denylist(root)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return data


def scan_identities(text):
    """Shell out to the identity scanner for named people and teams."""
    if not IDENTITY_SCAN.exists():
        return [], "identity-scan.py not found; people were not checked"
    try:
        tmp = Path("/tmp/.issue-sanitiser-identity.md")
        tmp.write_text(text, encoding="utf-8")
        out = subprocess.run(
            [sys.executable, str(IDENTITY_SCAN), str(tmp), "--json"],
            capture_output=True, text=True, timeout=120,
        )
        payload = json.loads(out.stdout) if out.stdout.strip() else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return [], f"identity scan failed: {exc}"
    findings = payload if isinstance(payload, list) else payload.get("findings", [])
    return [str(f.get("match", f)) if isinstance(f, dict) else str(f) for f in findings], None


def check(text, denylist):
    """Return (blocking, advisory, notes) for a draft."""
    blocking, advisory, notes = [], [], []

    for label, pattern in FORBIDDEN_PATTERNS:
        for m in re.finditer(pattern, text):
            # A long opaque token is usually a spreadsheet or document id, but a
            # long ordinary word is not — require a digit to cut the false rate.
            if label == "spreadsheet id" and not re.search(r'\d', m.group(0)):
                continue
            blocking.append({"kind": label, "match": m.group(0)[:80]})

    terms = denylist.get("terms", [])
    if terms:
        # One alternation over the whole list, longest first so the most specific
        # term wins rather than a short prefix of it.
        pattern = re.compile(
            r'(?<!\w)(' + '|'.join(re.escape(t) for t in terms) + r')(?!\w)', re.I)
        for m in pattern.finditer(text):
            blocking.append({"kind": "internal or vendor name", "match": m.group(0)[:80]})

    people, note = scan_identities(text)
    if note:
        notes.append(note)
    for p in people:
        blocking.append({"kind": "named person or team", "match": p[:80]})

    for label, pattern in REVIEW_PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            advisory.append({"kind": label, "match": m.group(0)[:80]})

    # Collapse repeats so a term used five times is reported once.
    def dedupe(items):
        seen, out = set(), []
        for i in items:
            key = (i["kind"], i["match"].lower())
            if key not in seen:
                seen.add(key)
                out.append(i)
        return out

    return dedupe(blocking), dedupe(advisory), notes


def main():
    parser = argparse.ArgumentParser(
        description="Check text is safe to publish to a public issue tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-denylist", action="store_true",
                       help="Harvest the denylist from the corpus and cache it")
    group.add_argument("--check", metavar="FILE",
                       help="Check a draft file; '-' reads stdin")
    parser.add_argument("--rebuild", action="store_true",
                        help="With --check: refresh the denylist before checking")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    root = get_project_root()

    if args.build_denylist:
        data = build_denylist(root)
        cache = root / DENYLIST_CACHE
        cache.parent.mkdir(parents=True, exist_ok=True)
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        if args.json:
            print(json.dumps({"cache": str(cache.relative_to(root)), **data, "terms": "<omitted>"}, indent=2))
        else:
            print(f"denylist: {data['count']} terms -> {cache.relative_to(root)}")
            for k, v in data["sources"].items():
                print(f"  {k}: {v}")
        return 0

    text = sys.stdin.read() if args.check == "-" else Path(args.check).read_text(encoding="utf-8")
    denylist = load_denylist(root, rebuild=args.rebuild)
    blocking, advisory, notes = check(text, denylist)

    result = {
        "source": args.check,
        "clean": not blocking,
        "blocking": blocking,
        "advisory": advisory,
        "notes": notes,
        "denylistTerms": denylist.get("count", len(denylist.get("terms", []))),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if blocking:
            print(f"BLOCKED — {len(blocking)} finding(s) must not be published:")
            for f in blocking:
                print(f"  [{f['kind']}] {f['match']}")
        else:
            print("clean — no blocking findings")
        for f in advisory:
            print(f"  review: [{f['kind']}] {f['match']}", file=sys.stderr)
        for n in notes:
            print(f"  note: {n}", file=sys.stderr)

    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
