"""Structural edit operations for Google Docs, used by edit-gws-doc.py.

Find/replace preserves styling but cannot add a table row, merge a band
header, or rewrite a cell whose runs carry different styles. These operations
can. Each one fetches the document afresh, resolves its anchor by text, and
issues one batchUpdate, because every structural change shifts the indices
the next operation depends on.

Anchors are text, never indices: a row is found by the start of its Action
Item cell (column 1) or by text in a merged band row, a paragraph by a
substring. An anchor that matches nothing, or more than one thing, stops the
run — a silent wrong-row edit is the failure this design exists to prevent.

Indices are UTF-16 code units, as the Docs API counts them, so emoji such as
"🕒" occupy two.

Operations (every one takes "tab", the tab's exact title):

  setCell          {"table": 0, "row": ROW, "col": 1, "paragraphs": [PARA]}
  insertRow        {"table": 0, "after": ROW, "cells": {"1": [PARA], "2": [PARA]},
                    "checkbox": true}
  deleteRow        {"table": 0, "row": ROW}
  insertBand       {"table": 0, "after": ROW, "title": "...", "goal": "..."}
  setBand          {"table": 0, "row": ROW, "title": "...", "goal": "..."}
  restripe         {"table": 0}
  setParagraph     {"match": "text", "paragraph": PARA}
  insertParagraphs {"after": "text", "paragraphs": [PARA]}
  moveTab          {"index": 0}

ROW is a string matched against the start of column 1's text, then against
text anywhere in a merged band row; "#header" is row 0; {"index": n} is
literal. PARA is a string, a list of runs, or {"runs": [...], "style":
"HEADING_3", "bullet": "inherit" | "none" | "<preset>", "paragraphStyle":
{...}, "like": "text"} where paragraphStyle is raw Docs API fields such as
spaceAbove, and "like" copies indents and spacing from an existing paragraph
(the text of one in the same tab, or {"tab", "match"}). A run is a string or
{"text", "bold", "italic", "size", "color": "#rrggbb", "font", "link": url |
{"tabId": id}}; a link value of "#tab:<title>" resolves to that tab.
"""

from __future__ import annotations

import json

STRIPE = {"red": 0.98039216, "green": 0.98039216, "blue": 0.98039216}
BAND_FONT = "Red Hat Display"
BAND_SIZE = 13
BAND_MIN_HEIGHT_PT = 22
# The original band header paragraphs zero the heading style's spacing.
BAND_SPACING = {"spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 0, "unit": "PT"}}


class OpError(RuntimeError):
    """An operation could not be resolved against the document."""


def u16(text: str) -> int:
    """Length in UTF-16 code units, the unit Docs API indices use."""
    return len(text.encode("utf-16-le")) // 2


# --------------------------------------------------------------------------
# Document navigation
# --------------------------------------------------------------------------

def _all_tabs(tabs):
    for tab in tabs or []:
        yield tab
        yield from _all_tabs(tab.get("childTabs"))


def find_tab(document, title):
    for tab in _all_tabs(document.get("tabs")):
        if tab["tabProperties"].get("title") == title:
            return tab
    titles = [t["tabProperties"].get("title") for t in _all_tabs(document.get("tabs"))]
    raise OpError(f"no tab titled {title!r}; tabs are {titles}")


def tab_body(tab):
    return tab["documentTab"]["body"]["content"]


def tab_id(tab):
    return tab["tabProperties"]["tabId"]


def para_text(paragraph):
    return "".join(e.get("textRun", {}).get("content", "")
                   for e in paragraph.get("elements", []))


def cell_text(cell):
    return "".join(para_text(c["paragraph"]) for c in cell.get("content", [])
                   if "paragraph" in c)


def find_table(tab, index):
    tables = [e for e in tab_body(tab) if "table" in e]
    if index >= len(tables):
        raise OpError(f"tab {tab['tabProperties']['title']!r} has "
                      f"{len(tables)} table(s); asked for table {index}")
    return tables[index]


def is_band_row(row):
    return row["tableCells"][0].get("tableCellStyle", {}).get("columnSpan", 1) > 1


def is_data_row(row):
    first = row["tableCells"][0]["content"][0].get("paragraph", {})
    return bool(first.get("bullet")) and not is_band_row(row)


def find_row(table_element, ref):
    rows = table_element["table"]["tableRows"]
    if isinstance(ref, dict) and "index" in ref:
        return ref["index"]
    if ref == "#header":
        return 0
    hits = [i for i, r in enumerate(rows)
            if not is_band_row(r) and len(r["tableCells"]) > 1
            and cell_text(r["tableCells"][1]).strip().startswith(ref)]
    if not hits:
        hits = [i for i, r in enumerate(rows)
                if is_band_row(r) and ref in cell_text(r["tableCells"][0])]
    if len(hits) != 1:
        raise OpError(f"row anchor {ref!r} matched {len(hits)} rows")
    return hits[0]


def find_paragraph(tab, match):
    """A top-level (non-table) paragraph containing `match`."""
    hits = [e for e in tab_body(tab)
            if "paragraph" in e and match in para_text(e["paragraph"])]
    if len(hits) != 1:
        raise OpError(f"paragraph anchor {match!r} matched {len(hits)} "
                      f"paragraphs in tab {tab['tabProperties']['title']!r}")
    return hits[0]


# --------------------------------------------------------------------------
# Content specs
# --------------------------------------------------------------------------

def norm_para(spec):
    if isinstance(spec, str):
        return {"runs": [{"text": spec}]}
    if isinstance(spec, list):
        return {"runs": [r if isinstance(r, dict) else {"text": r} for r in spec]}
    runs = spec.get("runs", [])
    return {**spec, "runs": [r if isinstance(r, dict) else {"text": r} for r in runs]}


def _rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255,
            "blue": int(h[4:6], 16) / 255}


def run_style(run, document):
    """(textStyle, fields) for a run, or (None, None) if it sets nothing."""
    style, fields = {}, []
    for key in ("bold", "italic"):
        if key in run:
            style[key] = run[key]
            fields.append(key)
    if "size" in run:
        style["fontSize"] = {"magnitude": run["size"], "unit": "PT"}
        fields.append("fontSize")
    if "color" in run:
        style["foregroundColor"] = {"color": {"rgbColor": _rgb(run["color"])}}
        fields.append("foregroundColor")
    if "font" in run:
        style["weightedFontFamily"] = {"fontFamily": run["font"]}
        fields.append("weightedFontFamily")
    if "link" in run:
        link = run["link"]
        if isinstance(link, str) and link.startswith("#tab:"):
            link = {"tabId": tab_id(find_tab(document, link[5:]))}
        elif isinstance(link, str):
            link = {"url": link}
        style["link"] = link
        fields.append("link")
    return (style, ",".join(fields)) if fields else (None, None)


# Body text in a document whose NORMAL_TEXT style is bold — common in branded
# templates — is un-bolded run by run. Inheriting would render everything bold,
# so inserted text starts from an explicit non-bold baseline and a run that
# wants bold says so.
BASELINE = {"bold": False}
RESET_FIELDS = "bold,italic,underline,fontSize,foregroundColor,link,weightedFontFamily"


def write_paragraphs(start, paragraphs, tid, document, leading_newline=False):
    """Requests that insert `paragraphs` at `start` and style them.

    The caller has already cleared the target range. Order matters, and was
    learned the hard way: named paragraph styles and bullets go first, because
    applying a named style afterwards wipes the run styling; then the whole
    range is reset to the baseline; then each styled run is applied.
    """
    paras = [norm_para(p) for p in paragraphs]
    texts = ["".join(r["text"] for r in p["runs"]) for p in paras]
    body = "\n".join(texts)
    if leading_newline:
        body = "\n" + body
    requests = []
    if body:
        requests.append({"insertText": {"location": {"index": start, "tabId": tid},
                                        "text": body}})
    end = start + u16(body)

    # Pass 1: paragraph styles and bullets.
    cursor = start + (1 if leading_newline else 0)
    spans = []
    for para, text in zip(paras, texts):
        p_range = {"startIndex": cursor, "endIndex": cursor + u16(text) + 1, "tabId": tid}
        spans.append(cursor)
        if para.get("style"):
            requests.append({"updateParagraphStyle": {
                "range": p_range,
                "paragraphStyle": {"namedStyleType": para["style"]},
                "fields": "namedStyleType"}})
        if para.get("paragraphStyle"):
            # Applied after the named style, which would otherwise reset it.
            requests.append({"updateParagraphStyle": {
                "range": p_range, "paragraphStyle": para["paragraphStyle"],
                "fields": ",".join(para["paragraphStyle"])}})
        bullet = para.get("bullet", "inherit")
        if bullet == "none":
            requests.append({"deleteParagraphBullets": {"range": p_range}})
        elif bullet != "inherit":
            requests.append({"createParagraphBullets": {
                "range": p_range, "bulletPreset": bullet}})
        cursor += u16(text) + 1

    # Pass 2: baseline, then runs.
    if end > start:
        requests.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end, "tabId": tid},
            "textStyle": BASELINE, "fields": RESET_FIELDS}})
    for para, p_start in zip(paras, spans):
        cursor = p_start
        for run in para["runs"]:
            length = u16(run["text"])
            style, fields = run_style(run, document)
            if style and length:
                requests.append({"updateTextStyle": {
                    "range": {"startIndex": cursor, "endIndex": cursor + length,
                              "tabId": tid},
                    "textStyle": style, "fields": fields}})
            cursor += length
    return requests


def clear_cell(cell, tid):
    start = cell["content"][0]["startIndex"]
    end = cell["content"][-1]["endIndex"]
    requests = []
    if end - 1 > start:
        requests.append({"deleteContentRange": {
            "range": {"startIndex": start, "endIndex": end - 1, "tabId": tid}}})
    return start, requests


# --------------------------------------------------------------------------
# Operations
# --------------------------------------------------------------------------

# Text written into a cell gets explicit zero indents. A named style can carry
# an indent the original cells all override — one branded template sets
# NORMAL_TEXT's right indent to -55.5pt, so inherited text ran 55pt past the
# cell edge. The API omits named-style defaults, so this cannot be detected
# from the document JSON; setting it is the only reliable answer.
CELL_INDENTS = {"indentStart": {"magnitude": 0, "unit": "PT"},
                "indentEnd": {"magnitude": 0, "unit": "PT"},
                "indentFirstLine": {"magnitude": 0, "unit": "PT"}}


def op_set_cell(document, op):
    tab = find_tab(document, op["tab"])
    table = find_table(tab, op.get("table", 0))
    row = find_row(table, op["row"])
    cell = table["table"]["tableRows"][row]["tableCells"][int(op["col"])]
    start, requests = clear_cell(cell, tab_id(tab))
    paragraphs = []
    for spec in op["paragraphs"]:
        para = norm_para(spec)
        para["paragraphStyle"] = {**CELL_INDENTS, **para.get("paragraphStyle", {})}
        paragraphs.append(para)
    return requests + write_paragraphs(start, paragraphs, tab_id(tab), document)


def _location(table, tid, row, col=0):
    return {"tableStartLocation": {"index": table["startIndex"], "tabId": tid},
            "rowIndex": row, "columnIndex": col}


def op_insert_row(document, op, apply):
    tab = find_tab(document, op["tab"])
    tid = tab_id(tab)
    table = find_table(tab, op.get("table", 0))
    row = find_row(table, op["after"])
    apply([{"insertTableRow": {"tableCellLocation": _location(table, tid, row),
                               "insertBelow": True}}])
    new_row = {"index": row + 1}
    doc = apply.refetch()
    table = find_table(find_tab(doc, op["tab"]), op.get("table", 0))
    inserted = table["table"]["tableRows"][row + 1]
    if is_band_row(inserted):
        # A row inserted under a band header inherits its merge.
        span = inserted["tableCells"][0]["tableCellStyle"]["columnSpan"]
        apply([{"unmergeTableCells": {"tableRange": {
            "tableCellLocation": _location(table, tid, row + 1),
            "rowSpan": 1, "columnSpan": span}}}])
    width = len(inserted["tableCells"])
    blank = {"runs": [{"text": ""}], "style": "NORMAL_TEXT", "bullet": "none"}
    cells = {str(c): [blank] for c in range(width)}
    for col, paragraphs in op.get("cells", {}).items():
        cells[str(col)] = [{"style": "NORMAL_TEXT", "bullet": "none",
                            **norm_para(p)} for p in paragraphs]
    for col, paragraphs in sorted(cells.items()):
        apply(op_set_cell(apply.refetch(), {"tab": op["tab"],
                                             "table": op.get("table", 0),
                                             "row": new_row, "col": col,
                                             "paragraphs": paragraphs}))
    if op.get("checkbox", True):
        doc = apply.refetch()
        cell = find_table(find_tab(doc, op["tab"]), op.get("table", 0))[
            "table"]["tableRows"][row + 1]["tableCells"][0]
        first = cell["content"][0]
        p_range = {"startIndex": first["startIndex"], "endIndex": first["endIndex"],
                   "tabId": tid}
        requests = [{"createParagraphBullets": {"range": p_range,
                                                "bulletPreset": "BULLET_CHECKBOX"}}]
        indent = sibling_checkbox_indent(
            find_table(find_tab(doc, op["tab"]), op.get("table", 0)), row + 1)
        if indent:
            requests.append({"updateParagraphStyle": {
                "range": p_range, "paragraphStyle": indent,
                "fields": ",".join(indent)}})
        apply(requests)
    return []


def sibling_checkbox_indent(table_element, skip):
    """Indent of the nearest existing checkbox paragraph, to line a new one up."""
    rows = table_element["table"]["tableRows"]
    order = sorted(range(len(rows)), key=lambda i: abs(i - skip))
    for i in order:
        if i == skip or not is_data_row(rows[i]):
            continue
        style = rows[i]["tableCells"][0]["content"][0]["paragraph"]["paragraphStyle"]
        indent = {k: style[k] for k in ("indentStart", "indentFirstLine") if k in style}
        if indent:
            return indent
    return None


def op_delete_row(document, op):
    tab = find_tab(document, op["tab"])
    table = find_table(tab, op.get("table", 0))
    row = find_row(table, op["row"])
    return [{"deleteTableRow": {"tableCellLocation": _location(table, tab_id(tab), row)}}]


def op_insert_band(document, op, apply):
    tab = find_tab(document, op["tab"])
    tid = tab_id(tab)
    table = find_table(tab, op.get("table", 0))
    row = find_row(table, op["after"])
    apply([{"insertTableRow": {"tableCellLocation": _location(table, tid, row),
                               "insertBelow": True}}])
    doc = apply.refetch()
    table = find_table(find_tab(doc, op["tab"]), op.get("table", 0))
    new = table["table"]["tableRows"][row + 1]
    if not is_band_row(new):
        apply([{"mergeTableCells": {"tableRange": {
            "tableCellLocation": _location(table, tid, row + 1),
            "rowSpan": 1, "columnSpan": len(new["tableCells"])}}}])
    paragraphs = band_paragraphs(op)
    apply(op_set_cell(apply.refetch(), {"tab": op["tab"], "table": op.get("table", 0),
                                         "row": {"index": row + 1}, "col": 0,
                                         "paragraphs": paragraphs}))
    doc = apply.refetch()
    table = find_table(find_tab(doc, op["tab"]), op.get("table", 0))
    apply([{"updateTableRowStyle": {
        "tableStartLocation": {"index": table["startIndex"], "tabId": tid},
        "rowIndices": [row + 1],
        "tableRowStyle": {"minRowHeight": {"magnitude": BAND_MIN_HEIGHT_PT, "unit": "PT"}},
        "fields": "minRowHeight"}}])
    return []


def band_paragraphs(op):
    """The heading and Goal line of a band header, styled as the original."""
    return [
        {"runs": [{"text": op["title"], "font": BAND_FONT, "size": BAND_SIZE, "bold": True}],
         "style": "HEADING_3", "bullet": "none",
         "paragraphStyle": {**BAND_SPACING, "keepWithNext": True}},
        {"runs": [{"text": "Goal", "bold": True, "font": BAND_FONT},
                  {"text": ": ", "font": BAND_FONT},
                  {"text": op["goal"]}],
         "style": "NORMAL_TEXT", "bullet": "none", "paragraphStyle": BAND_SPACING},
    ]


def op_set_band(document, op):
    """Retitle an existing band header row in place."""
    return op_set_cell(document, {"tab": op["tab"], "table": op.get("table", 0),
                                  "row": op["row"], "col": 0,
                                  "paragraphs": band_paragraphs(op)})


def op_restripe(document, op):
    """Alternate data rows white then #FAFAFA, restarting under each band."""
    tab = find_tab(document, op["tab"])
    tid = tab_id(tab)
    table = find_table(tab, op.get("table", 0))
    rows = table["table"]["tableRows"]
    requests, position = [], 0
    for i, row in enumerate(rows):
        if i == 0:
            continue
        if is_band_row(row):
            position = 0
            colour, span = None, row["tableCells"][0]["tableCellStyle"].get("columnSpan", 1)
        elif is_data_row(row):
            colour, span = (STRIPE if position % 2 else None), len(row["tableCells"])
            position += 1
        else:
            continue
        style = {"backgroundColor": {"color": {"rgbColor": colour}}} if colour else {}
        requests.append({"updateTableCellStyle": {
            "tableRange": {"tableCellLocation": _location(table, tid, i),
                           "rowSpan": 1, "columnSpan": span},
            "tableCellStyle": style, "fields": "backgroundColor"}})
    return requests


# Paragraph geometry copied by "like". Indents and spacing are what make a new
# paragraph line up with its neighbours; templates often out-dent body text,
# so neither zero nor inherited is reliably right.
LIKE_KEYS = ("indentStart", "indentEnd", "indentFirstLine", "spaceAbove", "spaceBelow")


def resolve_like(document, tab, paragraphs):
    """Merge each paragraph's "like" reference into its paragraphStyle.

    "like" is the text of a paragraph in the same tab, or {"tab", "match"}
    for one elsewhere. Explicit paragraphStyle keys still win.
    """
    resolved = []
    for spec in paragraphs:
        para = norm_para(spec)
        like = para.pop("like", None)
        if like:
            source_tab = find_tab(document, like["tab"]) if isinstance(like, dict) else tab
            match = like["match"] if isinstance(like, dict) else like
            style = find_paragraph(source_tab, match)["paragraph"]["paragraphStyle"]
            copied = {k: style[k] for k in LIKE_KEYS if k in style}
            para["paragraphStyle"] = {**copied, **para.get("paragraphStyle", {})}
        resolved.append(para)
    return resolved


def op_set_paragraph(document, op):
    tab = find_tab(document, op["tab"])
    tid = tab_id(tab)
    element = find_paragraph(tab, op["match"])
    start, end = element["startIndex"], element["endIndex"]
    requests = []
    if end - 1 > start:
        requests.append({"deleteContentRange": {
            "range": {"startIndex": start, "endIndex": end - 1, "tabId": tid}}})
    return requests + write_paragraphs(
        start, resolve_like(document, tab, [op["paragraph"]]), tid, document)


def op_insert_paragraphs(document, op):
    tab = find_tab(document, op["tab"])
    element = find_paragraph(tab, op["after"])
    return write_paragraphs(element["endIndex"] - 1,
                            resolve_like(document, tab, op["paragraphs"]),
                            tab_id(tab), document, leading_newline=True)


def op_move_tab(document, op):
    tab = find_tab(document, op["tab"])
    return [{"updateDocumentTabProperties": {
        "tabProperties": {"tabId": tab_id(tab), "index": op["index"]},
        "fields": "index"}}]


SIMPLE = {
    "setCell": op_set_cell,
    "setBand": op_set_band,
    "deleteRow": op_delete_row,
    "restripe": op_restripe,
    "setParagraph": op_set_paragraph,
    "insertParagraphs": op_insert_paragraphs,
    "moveTab": op_move_tab,
}
COMPOUND = {"insertRow": op_insert_row, "insertBand": op_insert_band}
OPS = set(SIMPLE) | set(COMPOUND)


class Applier:
    """Sends request batches and refetches; passed to compound operations."""

    def __init__(self, document_id, run_gws, fetch):
        self.document_id = document_id
        self.run_gws = run_gws
        self.fetch = fetch

    def __call__(self, requests):
        if not requests:
            return
        self.run_gws(["docs", "documents", "batchUpdate",
                      "--params", json.dumps({"documentId": self.document_id}),
                      "--json", json.dumps({"requests": requests})])

    def refetch(self):
        return self.fetch(self.document_id)


def apply_op(op, applier):
    """Resolve and apply one structural operation against a fresh fetch."""
    name = op["op"]
    document = applier.refetch()
    if name in SIMPLE:
        applier(SIMPLE[name](document, op))
    elif name in COMPOUND:
        COMPOUND[name](document, op, applier)
    else:
        raise OpError(f"unknown op {name!r}")
