#!/usr/bin/env python3
"""
Read from and append to the Google Sheets feedback/issue register.

Shared by /report-issue (append new issues) and /plan-from-feedback (read
actionable issues). Wraps the `gws` CLI so skills never need inline shell
pipelines to touch the register.

Usage:
    # Show the register table schema (columns, row count, dropdown values)
    python3 utils/issue-register.py --schema

    # List issues, optionally filtered by status
    python3 utils/issue-register.py --list
    python3 utils/issue-register.py --list --status New --json

    # Validate a draft issue file without touching the register (offline)
    python3 utils/issue-register.py --validate drafts/issues.json

    # Check drafts against existing rows for near-duplicates
    python3 utils/issue-register.py --check-duplicates drafts/issues.json

    # Preview the rows that would be written
    python3 utils/issue-register.py --append drafts/issues.json --dry-run

    # Append the issues (Status is always written as "New")
    python3 utils/issue-register.py --append drafts/issues.json

    # Write resolution columns P-T back onto existing rows
    python3 utils/issue-register.py --resolve drafts/resolutions.json --dry-run
    python3 utils/issue-register.py --resolve drafts/resolutions.json

Resolution file format — a single object or an array of objects. Only `row`
and `status` are required; omitted change columns are written as "N/A":

    [
      {
        "row": 38,
        "status": "Resolved",
        "resolutionSummary": "Reworked the pattern so each view advances.",
        "practiceMethodChanges": "practices/red-hat-ai/train-prepare-ai-models.json: ...",
        "pgenChanges": "N/A",
        "languageChanges": "N/A"
      }
    ]

Draft issue file format — a single object or an array of objects:

    [
      {
        "type": "Issue",
        "summary": "Repeated states across pattern views",
        "description": "Every pattern view shows Discover at Published.",
        "documentName": "EcoTech Sales Foundations",
        "documentVersion": "1.0.2",
        "documentKind": "method",
        "selectedElement": "Partner Ecosystem Annual Operating Rhythm",
        "elementType": "pattern",
        "secondaryElement": "",
        "secondaryType": "",
        "page": "cli",
        "navigatorMode": "",
        "bundle": "",
        "email": "someone@example.com"
      }
    ]
"""

import argparse
import difflib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

from _shared import GWS, load_user_config

# Column order of the register's input zone (A-P). Resolution columns Q-T are
# written by /plan-from-feedback, never on append.
INPUT_COLUMNS = [
    ("timestamp", "Timestamp"),
    ("email", "Email"),
    ("type", "Type"),
    ("summary", "Summary"),
    ("description", "Description"),
    ("page", "Page"),
    ("documentName", "Document Name"),
    ("documentVersion", "Document Version"),
    ("documentKind", "Document Kind"),
    ("bundle", "Bundle"),
    ("navigatorMode", "Navigator Mode"),
    ("selectedElement", "Selected Element"),
    ("elementType", "Element Type"),
    ("secondaryElement", "Secondary Element"),
    ("secondaryType", "Secondary Type"),
    ("status", "Status"),
]

RESOLUTION_COLUMNS = [
    ("resolutionSummary", "Resolution Summary"),
    ("practiceMethodChanges", "Practice/Method Changes"),
    ("pgenChanges", "keleo-pgen-llm changes"),
    ("languageChanges", "keleo-language changes"),
]

ALL_COLUMNS = INPUT_COLUMNS + RESOLUTION_COLUMNS

VALID_TYPES = ["Issue", "Enhancement", "Question"]

# Status column dropdown. Writing anything else trips the sheet's own
# validation, so --resolve checks against this list before calling out.
VALID_STATUSES = ["New", "Planned", "In Progress", "Resolved", "Closed", "Declined"]
VALID_KINDS = ["practice", "practiceBaseline", "method"]

# Element types as named by the Practice Language schema. Used to warn on
# free-text element types that /plan-from-feedback could not act on.
VALID_ELEMENT_TYPES = [
    "alpha", "state", "checklistItem", "activity", "activitySpace",
    "workProduct", "levelOfDetail", "persona", "personaGroup", "pattern",
    "patternGroup", "patternView", "narrative", "narrativeType", "citation",
    "outcome", "focus", "competency", "asset", "reference", "alias", "practice",
]

SUMMARY_MAX = 120
DUPLICATE_THRESHOLD = 0.72


# --- gws plumbing ---

def run_gws(args, description):
    """Run a gws command and return parsed JSON stdout."""
    try:
        result = subprocess.run([GWS] + args, capture_output=True, text=True)
    except FileNotFoundError:
        fail(f"gws CLI not found at {GWS}. Install it to use the issue register.")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        if re.search(r"\b(401|403|unauthoriz|unauthenticat|invalid_grant|token)\b", detail, re.I):
            detail += "\nGoogle auth may have expired. Run `gws auth status`, then `gws auth login`."
        fail(f"{description} failed:\n{detail}")
    # gws prints a keyring backend notice before the JSON payload.
    stdout = result.stdout
    start = min((i for i in (stdout.find("{"), stdout.find("[")) if i != -1), default=-1)
    if start == -1:
        return {}
    try:
        return json.loads(stdout[start:])
    except json.JSONDecodeError:
        fail(f"{description} returned unparseable output:\n{stdout[:500]}")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def get_spreadsheet_id(override=None):
    """Resolve the register spreadsheet ID from the CLI arg or user config."""
    if override:
        return extract_spreadsheet_id(override)
    config = load_user_config()
    sid = config.get("issueRegisterSpreadsheetId")
    if not sid and config.get("issueRegisterUrl"):
        sid = extract_spreadsheet_id(config["issueRegisterUrl"])
    if not sid:
        fail("No issue register configured. Pass --spreadsheet <URL-or-ID> or set "
             "issueRegisterSpreadsheetId in .claude/user-config.json.")
    return sid


def extract_spreadsheet_id(url_or_id):
    """Accept a full Sheets URL or a bare spreadsheet ID."""
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_or_id)
    return match.group(1) if match else url_or_id


def get_table(spreadsheet_id):
    """Return (sheet_title, sheet_id, table) for the register's first table."""
    data = run_gws(
        ["sheets", "spreadsheets", "get", "--params",
         json.dumps({"spreadsheetId": spreadsheet_id, "includeGridData": False})],
        "Reading spreadsheet metadata",
    )
    sheets = data.get("sheets", [])
    if not sheets:
        fail("Spreadsheet contains no sheets.")
    sheet = sheets[0]
    props = sheet.get("properties", {})
    tables = sheet.get("tables", [])
    if not tables:
        fail("Register sheet has no structured table. Expected a table covering columns A-T.")
    return props.get("title", "Sheet1"), props.get("sheetId", 0), tables[0]


def read_rows(spreadsheet_id, sheet_title):
    """Read all register values. Returns (header, rows) where rows are padded lists."""
    data = run_gws(
        ["sheets", "+read", "--spreadsheet", spreadsheet_id, "--range", sheet_title],
        "Reading register values",
    )
    values = data.get("values", [])
    if not values:
        return [], []
    header = values[0]
    width = len(ALL_COLUMNS)
    rows = [row + [""] * (width - len(row)) for row in values[1:]]
    return header, rows


def row_to_issue(row, row_number):
    """Convert a raw sheet row into a keyed dict with its 1-based sheet row number."""
    issue = {"row": row_number}
    for index, (key, _label) in enumerate(ALL_COLUMNS):
        issue[key] = row[index] if index < len(row) else ""
    return issue


# --- draft loading and validation ---

def load_drafts(path):
    """Load a draft issue file (single object or array)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        fail(f"Cannot read draft file {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"Draft file {path} is not valid JSON: {exc}")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        fail("Draft file must contain an issue object or a non-empty array of them.")
    return data


def validate_drafts(drafts, default_email=None):
    """Validate drafts. Returns (errors, warnings) as lists of strings."""
    errors = []
    warnings = []
    for i, draft in enumerate(drafts, start=1):
        label = f"Issue {i}"
        if not isinstance(draft, dict):
            errors.append(f"{label}: entry is not an object")
            continue

        issue_type = (draft.get("type") or "").strip()
        if issue_type not in VALID_TYPES:
            errors.append(f"{label}: type must be one of {', '.join(VALID_TYPES)} (got '{issue_type}')")

        summary = (draft.get("summary") or "").strip()
        if not summary:
            errors.append(f"{label}: summary is required")
        elif len(summary) > SUMMARY_MAX:
            warnings.append(f"{label}: summary is {len(summary)} chars (over {SUMMARY_MAX}); "
                            "move detail into description")

        if not (draft.get("description") or "").strip():
            errors.append(f"{label}: description is required")

        if not (draft.get("email") or default_email or "").strip():
            errors.append(f"{label}: email is required (set it on the issue, pass --email, "
                          "or set issueReporterEmail in user-config.json)")

        if not (draft.get("documentName") or "").strip():
            warnings.append(f"{label}: no documentName — triage cannot locate the reported document")

        kind = (draft.get("documentKind") or "").strip()
        if kind and kind not in VALID_KINDS:
            warnings.append(f"{label}: documentKind '{kind}' is not one of {', '.join(VALID_KINDS)}")

        for field in ("elementType", "secondaryType"):
            value = (draft.get(field) or "").strip()
            if value and value not in VALID_ELEMENT_TYPES:
                warnings.append(f"{label}: {field} '{value}' is not a known Practice Language element type")

        if (draft.get("secondaryElement") or "").strip() and not (draft.get("selectedElement") or "").strip():
            warnings.append(f"{label}: secondaryElement set without selectedElement")

        if draft.get("status"):
            warnings.append(f"{label}: status is ignored on append — new issues are always written as 'New'")

    return errors, warnings


def normalize(text):
    return re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()


def similarity(a, b):
    return difflib.SequenceMatcher(None, " ".join(normalize(a)), " ".join(normalize(b))).ratio()


def find_duplicates(drafts, existing, threshold=DUPLICATE_THRESHOLD):
    """Match each draft summary against existing register rows."""
    results = []
    for i, draft in enumerate(drafts, start=1):
        matches = []
        for row in existing:
            score = similarity(draft.get("summary"), row.get("summary"))
            same_doc = (draft.get("documentName") or "").strip().lower() == \
                       (row.get("documentName") or "").strip().lower()
            if same_doc and draft.get("documentName"):
                score = min(1.0, score + 0.08)
            if score >= threshold:
                matches.append({
                    "row": row["row"],
                    "similarity": round(score, 3),
                    "summary": row.get("summary"),
                    "documentName": row.get("documentName"),
                    "status": row.get("status"),
                })
        matches.sort(key=lambda m: m["similarity"], reverse=True)
        results.append({"index": i, "summary": draft.get("summary"), "matches": matches})
    return results


# --- append ---

def build_row(draft, default_email):
    """Build the A-P cell values for one draft issue."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
    values = {
        "timestamp": timestamp,
        "email": (draft.get("email") or default_email or "").strip(),
        "type": (draft.get("type") or "").strip(),
        "summary": (draft.get("summary") or "").strip(),
        "description": (draft.get("description") or "").strip(),
        "page": (draft.get("page") or "cli").strip(),
        "documentName": (draft.get("documentName") or "").strip(),
        "documentVersion": (draft.get("documentVersion") or "").strip(),
        "documentKind": (draft.get("documentKind") or "").strip(),
        "bundle": (draft.get("bundle") or "").strip(),
        "navigatorMode": (draft.get("navigatorMode") or "").strip(),
        "selectedElement": (draft.get("selectedElement") or "").strip(),
        "elementType": (draft.get("elementType") or "").strip(),
        "secondaryElement": (draft.get("secondaryElement") or "").strip(),
        "secondaryType": (draft.get("secondaryType") or "").strip(),
        "status": "New",
    }
    return [values[key] for key, _label in INPUT_COLUMNS]


def column_letter(index):
    """0-based column index to A1 letter."""
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def validate_resolutions(resolutions, table):
    """Check resolution entries before any write. Returns a list of errors."""
    errors = []
    table_range = table.get("range", {})
    # endRowIndex is exclusive and 0-based; the header occupies the first row.
    first_data_row = table_range.get("startRowIndex", 0) + 2
    last_data_row = table_range.get("endRowIndex", 0)

    seen = set()
    for i, entry in enumerate(resolutions):
        label = f"resolution[{i}]"
        row = entry.get("row")
        if not isinstance(row, int):
            errors.append(f"{label}: 'row' must be an integer sheet row number")
        else:
            if row in seen:
                errors.append(f"{label}: row {row} appears more than once")
            seen.add(row)
            if not first_data_row <= row <= last_data_row:
                errors.append(
                    f"{label}: row {row} is outside the table's data rows "
                    f"({first_data_row}-{last_data_row})")

        status = entry.get("status")
        if not status:
            errors.append(f"{label}: 'status' is required")
        elif status not in VALID_STATUSES:
            errors.append(
                f"{label}: status '{status}' is not one of {', '.join(VALID_STATUSES)}")

        if not entry.get("resolutionSummary"):
            errors.append(f"{label}: 'resolutionSummary' is required")

        unknown = set(entry) - {"row", "status"} - {k for k, _ in RESOLUTION_COLUMNS}
        if unknown:
            errors.append(f"{label}: unknown field(s): {', '.join(sorted(unknown))}")

    return errors


def write_resolutions(spreadsheet_id, sheet_title, resolutions):
    """Write Status plus the resolution columns (P-T) for each row.

    Rows are written individually rather than as one range: they are rarely
    contiguous, and a per-row write keeps a failure from stranding the batch
    half-applied.
    """
    first_column = column_letter(len(INPUT_COLUMNS) - 1)   # P — Status
    last_column = column_letter(len(ALL_COLUMNS) - 1)      # T — language changes

    written = []
    for entry in resolutions:
        row = entry["row"]
        values = [entry["status"]] + [
            entry.get(key) or "N/A" for key, _label in RESOLUTION_COLUMNS
        ]
        run_gws(
            ["sheets", "spreadsheets", "values", "update",
             "--params", json.dumps({
                 "spreadsheetId": spreadsheet_id,
                 "range": f"{sheet_title}!{first_column}{row}:{last_column}{row}",
                 "valueInputOption": "USER_ENTERED",
             }),
             "--json", json.dumps({"values": [values]})],
            f"Writing resolution for row {row}",
        )
        written.append({"row": row, "status": entry["status"]})

    return written


def append_rows(spreadsheet_id, sheet_title, sheet_id, table, rows):
    """Write rows below the table and extend the table range to cover them."""
    table_range = table.get("range", {})
    end_row = table_range.get("endRowIndex", 1)
    first_row = end_row + 1  # 1-based sheet row for the first new entry
    last_column = column_letter(len(INPUT_COLUMNS) - 1)
    a1 = f"{sheet_title}!A{first_row}:{last_column}{first_row + len(rows) - 1}"

    run_gws(
        ["sheets", "spreadsheets", "values", "update",
         "--params", json.dumps({
             "spreadsheetId": spreadsheet_id,
             "range": a1,
             "valueInputOption": "USER_ENTERED",
         }),
         "--json", json.dumps({"values": rows})],
        "Writing issue rows",
    )

    run_gws(
        ["sheets", "spreadsheets", "batchUpdate",
         "--params", json.dumps({"spreadsheetId": spreadsheet_id}),
         "--json", json.dumps({"requests": [{
             "updateTable": {
                 "table": {
                     "tableId": table.get("tableId"),
                     "range": {
                         "sheetId": sheet_id,
                         "startRowIndex": table_range.get("startRowIndex", 0),
                         "endRowIndex": end_row + len(rows),
                         "startColumnIndex": table_range.get("startColumnIndex", 0),
                         "endColumnIndex": table_range.get("endColumnIndex", len(ALL_COLUMNS)),
                     },
                 },
                 "fields": "range",
             },
         }]})],
        "Extending table range",
    )

    return list(range(first_row, first_row + len(rows)))


# --- commands ---

def cmd_schema(spreadsheet_id, as_json):
    sheet_title, sheet_id, table = get_table(spreadsheet_id)
    columns = [
        {
            "index": col.get("columnIndex", i),
            "name": col.get("columnName", ""),
            "type": col.get("columnType", "TEXT"),
            "values": [v.get("userEnteredValue") for v in
                       col.get("dataValidationRule", {}).get("condition", {}).get("values", [])],
        }
        for i, col in enumerate(table.get("columnProperties", []))
    ]
    info = {
        "spreadsheetId": spreadsheet_id,
        "sheet": sheet_title,
        "sheetId": sheet_id,
        "tableName": table.get("name"),
        "tableId": table.get("tableId"),
        "range": table.get("range"),
        "dataRows": table.get("range", {}).get("endRowIndex", 1) - 1,
        "columns": columns,
    }
    if as_json:
        print(json.dumps(info, indent=2))
        return
    print(f"=== REGISTER SCHEMA ({info['tableName']}) ===")
    print(f"  Sheet: {sheet_title}  Table ID: {info['tableId']}  Data rows: {info['dataRows']}")
    for col in columns:
        suffix = f"  [{', '.join(v for v in col['values'] if v)}]" if col["values"] else ""
        print(f"  {column_letter(col['index'])} ({col['index']:>2}) {col['name']}{suffix}")


def cmd_list(spreadsheet_id, status, as_json, limit):
    sheet_title, _sheet_id, _table = get_table(spreadsheet_id)
    _header, rows = read_rows(spreadsheet_id, sheet_title)
    issues = [row_to_issue(row, i) for i, row in enumerate(rows, start=2)]
    if status:
        issues = [iss for iss in issues if iss["status"].strip().lower() == status.strip().lower()]
    if limit:
        issues = issues[-limit:]
    if as_json:
        print(json.dumps(issues, indent=2))
        return
    label = f" (status={status})" if status else ""
    print(f"=== REGISTER ISSUES{label} ({len(issues)}) ===")
    for iss in issues:
        print(f"  Row {iss['row']}: [{iss['type'] or '?'}] {iss['summary']}")
        target = " / ".join(x for x in [iss["documentName"], iss["selectedElement"]] if x)
        if target:
            print(f"    {target}  status: {iss['status'] or '(blank)'}")


def cmd_validate(drafts, default_email, as_json):
    errors, warnings = validate_drafts(drafts, default_email)
    if as_json:
        print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, indent=2))
    else:
        print(f"=== DRAFT VALIDATION ({len(drafts)} issue(s)) ===")
        for message in errors:
            print(f"  ERROR: {message}")
        for message in warnings:
            print(f"  WARN:  {message}")
        if not errors and not warnings:
            print("  All drafts valid.")
    return errors


def cmd_check_duplicates(spreadsheet_id, drafts, threshold, as_json):
    sheet_title, _sheet_id, _table = get_table(spreadsheet_id)
    _header, rows = read_rows(spreadsheet_id, sheet_title)
    existing = [row_to_issue(row, i) for i, row in enumerate(rows, start=2)]
    results = find_duplicates(drafts, existing, threshold)
    if as_json:
        print(json.dumps(results, indent=2))
        return results
    print(f"=== DUPLICATE CHECK ({len(drafts)} draft(s) vs {len(existing)} row(s)) ===")
    for result in results:
        if not result["matches"]:
            print(f"  Issue {result['index']}: no similar entries")
            continue
        print(f"  Issue {result['index']}: {result['summary']}")
        for match in result["matches"]:
            print(f"    ~{match['similarity']:.2f} row {match['row']} [{match['status']}] "
                  f"{match['summary']} ({match['documentName']})")
    return results


def cmd_append(spreadsheet_id, drafts, default_email, dry_run, as_json, skip_duplicate_check):
    errors, warnings = validate_drafts(drafts, default_email)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(1)
    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)

    sheet_title, sheet_id, table = get_table(spreadsheet_id)

    if not skip_duplicate_check:
        _header, rows = read_rows(spreadsheet_id, sheet_title)
        existing = [row_to_issue(row, i) for i, row in enumerate(rows, start=2)]
        dupes = [r for r in find_duplicates(drafts, existing) if r["matches"]]
        for result in dupes:
            top = result["matches"][0]
            print(f"WARN: Issue {result['index']} resembles row {top['row']} "
                  f"(~{top['similarity']:.2f}, {top['status']}): {top['summary']}", file=sys.stderr)

    rows_to_write = [build_row(draft, default_email) for draft in drafts]

    if dry_run:
        first_row = table.get("range", {}).get("endRowIndex", 1) + 1
        preview = {
            "dryRun": True,
            "spreadsheetId": spreadsheet_id,
            "targetRows": list(range(first_row, first_row + len(rows_to_write))),
            "values": rows_to_write,
        }
        if as_json:
            print(json.dumps(preview, indent=2))
        else:
            print(f"=== DRY RUN — would append {len(rows_to_write)} row(s) starting at row {first_row} ===")
            for row_number, row in zip(preview["targetRows"], rows_to_write):
                print(f"  Row {row_number}: [{row[2]}] {row[3]}")
                print(f"    document: {row[6] or '(none)'} v{row[7] or '?'} ({row[8] or '?'})"
                      f"  element: {row[11] or '(none)'} ({row[12] or '-'})")
        return

    written = append_rows(spreadsheet_id, sheet_title, sheet_id, table, rows_to_write)
    result = {"appended": len(written), "rows": written, "spreadsheetId": spreadsheet_id}
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"=== APPENDED {len(written)} ISSUE(S) ===")
        for row_number, row in zip(written, rows_to_write):
            print(f"  Row {row_number}: [{row[2]}] {row[3]}")


def cmd_resolve(spreadsheet_id, resolutions, dry_run, as_json):
    sheet_title, _sheet_id, table = get_table(spreadsheet_id)

    errors = validate_resolutions(resolutions, table)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        if as_json:
            print(json.dumps({"dryRun": True, "resolutions": resolutions}, indent=2))
        else:
            print(f"=== DRY RUN — {len(resolutions)} ROW(S) ===")
            for entry in resolutions:
                print(f"  Row {entry['row']}: [{entry['status']}] "
                      f"{entry['resolutionSummary'][:80]}")
        return resolutions

    written = write_resolutions(spreadsheet_id, sheet_title, resolutions)

    if as_json:
        print(json.dumps({"written": written}, indent=2))
    else:
        print(f"=== UPDATED {len(written)} ROW(S) ===")
        for entry in written:
            print(f"  Row {entry['row']}: {entry['status']}")
    return written


def main():
    parser = argparse.ArgumentParser(
        description="Read from and append to the Google Sheets feedback/issue register"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--schema", action="store_true",
                      help="Show the register table schema (columns, dropdowns, row count)")
    mode.add_argument("--list", action="store_true",
                      help="List register issues, optionally filtered by --status")
    mode.add_argument("--validate", metavar="FILE",
                      help="Validate a draft issue file without contacting the register")
    mode.add_argument("--check-duplicates", metavar="FILE",
                      help="Compare draft issues against existing register rows")
    mode.add_argument("--append", metavar="FILE",
                      help="Append draft issues to the register (Status is written as 'New')")
    mode.add_argument("--resolve", metavar="FILE",
                      help="Write Status and resolution columns (P-T) onto "
                           "existing rows from a resolution file")

    parser.add_argument("--spreadsheet", metavar="URL_OR_ID",
                        help="Override the register from .claude/user-config.json")
    parser.add_argument("--status", metavar="STATUS",
                        help="Filter --list by status (e.g. New, Resolved)")
    parser.add_argument("--limit", type=int, help="Show only the last N rows with --list")
    parser.add_argument("--email", metavar="ADDRESS",
                        help="Reporter email for issues that don't set one")
    parser.add_argument("--threshold", type=float, default=DUPLICATE_THRESHOLD,
                        help=f"Similarity threshold for duplicate detection (default {DUPLICATE_THRESHOLD})")
    parser.add_argument("--no-duplicate-check", action="store_true",
                        help="Skip the duplicate warning pass during --append")
    parser.add_argument("--dry-run", action="store_true",
                        help="With --append or --resolve: preview without writing")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    default_email = args.email or load_user_config().get("issueReporterEmail")

    if args.validate:
        errors = cmd_validate(load_drafts(args.validate), default_email, args.json)
        sys.exit(1 if errors else 0)

    spreadsheet_id = get_spreadsheet_id(args.spreadsheet)

    if args.schema:
        cmd_schema(spreadsheet_id, args.json)
    elif args.list:
        cmd_list(spreadsheet_id, args.status, args.json, args.limit)
    elif args.check_duplicates:
        cmd_check_duplicates(spreadsheet_id, load_drafts(args.check_duplicates),
                             args.threshold, args.json)
    elif args.append:
        cmd_append(spreadsheet_id, load_drafts(args.append), default_email,
                   args.dry_run, args.json, args.no_duplicate_check)
    elif args.resolve:
        cmd_resolve(spreadsheet_id, load_drafts(args.resolve), args.dry_run, args.json)


if __name__ == "__main__":
    main()
