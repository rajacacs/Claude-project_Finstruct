"""PDF export using ReportLab — professional print-ready FS."""

from __future__ import annotations
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from ..core.fs_engine import FSLine, FSDocument, RowType
from ..core.notes_engine import Note

# ── Colours (NSE/BSE listed-company neutral grey palette) ──────────────
C_HDR_BG    = colors.HexColor("#333333")    # Dark grey headers
C_HDR_TEXT  = colors.white                  # White text on headers
C_CY_TINT   = colors.HexColor("#F2F2F2")    # Light grey for CY column
C_PY_BG     = colors.white                  # White for PY column
C_ALT_ROW   = colors.HexColor("#F9F9F9")    # Very light grey alternating rows
C_BORDER    = colors.HexColor("#CCCCCC")    # Grey borders
C_BG        = colors.HexColor("#F3F2F1")    # Page background
C_WHITE     = colors.white
C_TEXT      = colors.HexColor("#201F1E")
C_WARN      = colors.HexColor("#A4262C")
C_SEC_BG    = colors.HexColor("#F5F5F5")    # Light grey for section rows
# Legacy names for compatibility
C_PRIMARY   = C_HDR_BG
C_DARK      = C_BORDER
C_LIGHT     = C_SEC_BG
C_TOTAL_BG  = C_BORDER
C_GRAND_BG  = C_BORDER
C_ALT       = C_ALT_ROW

W = A4[0] - 40*mm
COL_LABEL = W * 0.58
COL_CY    = W * 0.21
COL_PY    = W * 0.21


def _styles():
    ss = getSampleStyleSheet()
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=9, textColor=C_TEXT, leading=12)
    return {
        "base":    base,
        "title":   ParagraphStyle("title",  parent=base, fontSize=13, fontName="Helvetica-Bold",
                                  alignment=TA_CENTER, spaceAfter=2),
        "entity":  ParagraphStyle("entity", parent=base, fontSize=11, fontName="Helvetica-Bold",
                                  alignment=TA_CENTER, spaceAfter=2),
        "sub":     ParagraphStyle("sub",    parent=base, fontSize=8,  alignment=TA_CENTER,
                                  textColor=colors.HexColor("#605E5C")),
        "note":    ParagraphStyle("note",   parent=base, fontSize=9,  fontName="Helvetica",
                                  spaceAfter=3),
        "draft":   ParagraphStyle("draft",  parent=base, fontSize=40, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#EDEBE9"), alignment=TA_CENTER),
    }


def _fmt(v: float, div: int = 1) -> str:
    if v is None or v == 0:
        return "-"
    return f"{v:,.2f}"


def _fs_table(lines: list[FSLine], section: str, cy_label: str = "Current Year Rs.", py_label: str = "Previous Year Rs.") -> Table:
    data = [["Particulars", "Note", cy_label, py_label]]
    row_styles = []

    for i, ln in enumerate(lines, start=1):
        if ln.row_type == "BLANK":
            data.append(["", "", "", ""])
            continue
        if ln.row_type == "HEADER":
            data.append([Paragraph(f"<b>{ln.label}</b>", ParagraphStyle(
                "hdr", fontSize=10, fontName="Helvetica-Bold", textColor=C_WHITE,
                leftIndent=0)), "", "", ""])
            row_styles += [
                ("BACKGROUND", (0, i), (-1, i), C_PRIMARY),
                ("TEXTCOLOR",  (0, i), (-1, i), C_WHITE),
                ("SPAN",       (0, i), (-1, i)),
            ]
            continue
        if ln.row_type == "SECTION":
            data.append([Paragraph(f"<b>{ln.label}</b>", ParagraphStyle(
                "sec", fontSize=9, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#333333"),
                leftIndent=ln.indent * 6)), "", "", ""])
            row_styles += [
                ("BACKGROUND", (0, i), (-1, i), C_SEC_BG),
                ("SPAN",       (0, i), (-1, i)),
            ]
            continue
        if ln.row_type == "TEXT":
            data.append([Paragraph(ln.label, ParagraphStyle(
                "txt", fontSize=8, fontName="Helvetica-Oblique",
                textColor=colors.HexColor("#A4262C"),
                leftIndent=6)), "", "", ""])
            row_styles += [("SPAN", (0, i), (-1, i))]
            continue

        indent = ln.indent * 6
        label_style = ParagraphStyle("lbl", fontSize=9, fontName=(
            "Helvetica-Bold" if ln.row_type in ("TOTAL", "GRAND", "SUBTOTAL") else "Helvetica"),
            leftIndent=indent, textColor=C_TEXT)
        cy_str = _fmt(ln.cy) if ln.row_type not in ("SECTION", "HEADER", "BLANK") else ""
        py_str = _fmt(ln.py) if ln.row_type not in ("SECTION", "HEADER", "BLANK") else ""
        note_str = str(ln.note) if ln.note else ""
        data.append([Paragraph(ln.label, label_style), note_str, cy_str, py_str])

        if ln.row_type == "GRAND":
            row_styles += [
                ("FONTNAME",   (0, i), (-1, i), "Helvetica-Bold"),
                ("LINEABOVE",  (0, i), (-1, i), 0.5, C_BORDER),
                ("LINEBELOW",  (0, i), (-1, i), 0.5, C_BORDER),
            ]
        elif ln.row_type == "TOTAL":
            row_styles += [
                ("FONTNAME",   (0, i), (-1, i), "Helvetica-Bold"),
                ("LINEABOVE",  (0, i), (-1, i), 0.5, C_BORDER),
            ]
        elif i % 2 == 0:
            row_styles += [
                ("BACKGROUND", (0, i), (1, i), C_WHITE),
                ("BACKGROUND", (2, i), (2, i), C_ALT_ROW),
                ("BACKGROUND", (3, i), (-1, i), C_WHITE),
            ]
        else:
            row_styles += [
                ("BACKGROUND", (2, i), (2, i), C_CY_TINT),
            ]

    col_widths = [COL_LABEL, 18*mm, COL_CY, COL_PY]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    base_style = [
        ("BACKGROUND",  (0, 0), (-1, 0), C_HDR_BG),
        ("TEXTCOLOR",   (0, 0), (-1, 0), C_HDR_TEXT),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("ALIGN",       (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN",       (1, 0), (1, -1), "CENTER"),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.HexColor("#EDEBE9")),
        # CY column (index 2) gets light grey tint
        ("BACKGROUND",  (2, 1), (2, -1), C_CY_TINT),
        # PY column (index 3) stays white
        ("BACKGROUND",  (3, 1), (3, -1), C_WHITE),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]
    t.setStyle(TableStyle(base_style + row_styles))
    return t


def _note_table(note: Note, cy_label: str = "Current Year Rs.", py_label: str = "Previous Year Rs.") -> Table:
    data = [[Paragraph(f"<b>Note {note.number}: {note.title}</b>",
                        ParagraphStyle("nh", fontSize=9, fontName="Helvetica-Bold",
                                       textColor=C_WHITE)),
             cy_label, py_label]]
    row_styles: list = []
    for i, ln in enumerate(note.lines, start=1):
        if ln.row_type == "BLANK":
            data.append(["", "", ""]); continue
        if ln.row_type == "TEXT":
            p = Paragraph(ln.label, ParagraphStyle("nt", fontSize=8,
                fontName="Helvetica-Oblique", leftIndent=ln.indent*6))
            data.append([p, "", ""])
            row_styles += [("SPAN", (0, i), (-1, i))]
            continue
        if ln.row_type == "SECTION":
            p = Paragraph(f"<b>{ln.label}</b>", ParagraphStyle("ns", fontSize=8.5,
                fontName="Helvetica-Bold", leftIndent=ln.indent*6))
            data.append([p, "", ""])
            row_styles += [("BACKGROUND", (0, i), (-1, i), C_SEC_BG),
                           ("SPAN", (0, i), (-1, i))]
            continue
        fn = "Helvetica-Bold" if ln.row_type in ("TOTAL","GRAND") else "Helvetica"
        p = Paragraph(ln.label, ParagraphStyle("nd", fontSize=8.5, fontName=fn,
                       leftIndent=ln.indent*6))
        cy = _fmt(ln.cy); py = _fmt(ln.py)
        data.append([p, cy, py])
        if ln.row_type in ("TOTAL", "GRAND"):
            row_styles += [
                ("FONTNAME",   (0, i), (-1, i), "Helvetica-Bold"),
                ("LINEABOVE",  (0, i), (-1, i), 0.5, C_BORDER),
            ]
        elif i % 2 == 0:
            row_styles += [
                ("BACKGROUND", (0, i), (0, i), C_WHITE),
                ("BACKGROUND", (1, i), (1, i), C_ALT_ROW),
                ("BACKGROUND", (2, i), (-1, i), C_WHITE),
            ]
        else:
            row_styles += [
                ("BACKGROUND", (1, i), (1, i), C_CY_TINT),
            ]

    cw = [COL_LABEL + 18*mm, COL_CY, COL_PY]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), C_HDR_BG),
        ("TEXTCOLOR",   (0, 0), (-1, 0), C_HDR_TEXT),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN",       (1, 0), (-1, -1), "RIGHT"),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.HexColor("#EDEBE9")),
        # CY column (index 1 in notes table) gets light grey tint
        ("BACKGROUND",  (1, 1), (1, -1), C_CY_TINT),
        # PY column (index 2) stays white
        ("BACKGROUND",  (2, 1), (2, -1), C_WHITE),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ] + row_styles))
    return t


def export_pdf(doc: FSDocument, notes: list[Note], output_path: Path,
               is_draft: bool = True, db=None):
    st = _styles()
    em = doc.entity_master
    entity_name = em.get("entity_name", em.get("Company_Name", "Entity"))
    address     = em.get("address", em.get("Registered_Office", ""))
    fy          = doc.fy
    # Derive FY labels: "2024-25" → cy_label = "Rs. FY 2024-25", py_label = "Rs. FY 2023-24"
    try:
        fy_parts = fy.split("-")
        fy_start_cy = int(fy_parts[0])
        fy_end_cy = int(fy_parts[1])
        fy_start_py = fy_start_cy - 1
        fy_end_py = fy_end_cy - 1
        cy_label = f"Rs. FY {fy_start_cy}-{fy_end_cy:02d}"
        py_label = f"Rs. FY {fy_start_py}-{fy_end_py:02d}"
    except (IndexError, ValueError):
        cy_label = "Rs. Current Year"
        py_label = "Rs. Previous Year"
    divisor_label = {1: "Rs.", 1000: "Rs. in Thousands",
                     100000: "Rs. in Lakhs", 10000000: "Rs. in Crores"}.get(doc.divisor, "Rs.")
    auditor_firm    = em.get("auditor_firm", em.get("Auditor_Firm", "[Auditor Firm]"))
    auditor_partner = em.get("auditor_partner", em.get("Auditor_Partner", "[Partner Name]"))
    auditor_mrn     = em.get("auditor_mrn", em.get("Auditor_MemNo", ""))
    auditor_frn     = em.get("auditor_frn", em.get("Auditor_Firm_Reg", ""))
    sign_place      = em.get("signing_place", em.get("Signing_Place", ""))
    sign_date       = em.get("signing_date", em.get("Signing_Date",
                             datetime.now().strftime("%d-%b-%Y")))
    pdf = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f"FinStruct – {entity_name} – FY {fy}",
    )

    def _page_header_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#605E5C"))
        canvas.drawString(20*mm, 10*mm, f"{entity_name}  |  FY {fy}  |  Prepared with FinStruct")
        canvas.drawRightString(A4[0]-20*mm, 10*mm, f"Page {doc_obj.page}")
        if is_draft:
            canvas.setFont("Helvetica-Bold", 60)
            canvas.setFillColor(colors.HexColor("#EDEBE9"))
            canvas.saveState()
            canvas.translate(A4[0]/2, A4[1]/2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DRAFT")
            canvas.restoreState()
        canvas.restoreState()

    # FY "2024-25" → year_end = 2025 (balance sheet / year-end date)
    try:
        _fy_parts = fy.split("-")
        year_end = str(int(_fy_parts[0]) + 1)
    except Exception:
        year_end = _fy_parts[0] if _fy_parts else fy

    story = []

    def _entity_header(title: str):
        story.append(Paragraph(entity_name.upper(), st["entity"]))
        if address:
            story.append(Paragraph(address, st["sub"]))
        story.append(Paragraph(title, st["title"]))
        story.append(Paragraph(f"(All amounts in {divisor_label}, unless otherwise stated)",
                                st["sub"]))
        story.append(Spacer(1, 4*mm))

    def _footer_table():
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "<i>The accompanying notes form an integral part of the financial statements.</i>",
            ParagraphStyle("fi", fontSize=8, fontName="Helvetica-Oblique", alignment=TA_CENTER)))
        story.append(Spacer(1, 4*mm))
        # Dynamic signing directors
        signing_dirs = []
        try:
            if db is not None:
                signing_dirs = [dict(d) for d in db.get_directors() if d["is_signing_auth"]]
        except Exception:
            pass
        # Fallback: build from legacy entity_master fields if directors table unavailable
        if not signing_dirs:
            for i in (1, 2):
                n = em.get(f"dir{i}_name", "").strip()
                if n:
                    signing_dirs.append({
                        "name": n,
                        "designation": em.get(f"dir{i}_desig", "Director"),
                        "din": em.get(f"dir{i}_din", ""),
                    })

        # Build signing block rows (auditor left, directors right in pairs)
        fdata = [
            ["As per our report of even date", "", "For and on behalf of the Board", ""],
            [f"For {auditor_firm}", "", entity_name.upper(), ""],
            ["Chartered Accountants", "", f"FRN: {auditor_frn}", ""],
        ]
        # Pair up signing directors
        for idx in range(0, max(len(signing_dirs), 1), 2):
            d1 = signing_dirs[idx] if idx < len(signing_dirs) else None
            d2 = signing_dirs[idx+1] if idx+1 < len(signing_dirs) else None
            fdata.append(["", "", "", ""])
            fdata.append(["", "", "", ""])
            fdata.append([
                auditor_partner if idx == 0 else "",
                "",
                d1["name"] if d1 else "",
                d2["name"] if d2 else "",
            ])
            fdata.append([
                "Partner" if idx == 0 else "",
                "",
                d1.get("designation","Director") if d1 else "",
                d2.get("designation","") if d2 else "",
            ])
            fdata.append([
                f"M No: {auditor_mrn}" if idx == 0 else "",
                "",
                f"DIN: {d1['din']}" if d1 and d1.get("din") else "",
                f"DIN: {d2['din']}" if d2 and d2.get("din") else "",
            ])
        fdata.append(["", "", "", ""])
        fdata.append([f"Place: {sign_place}", "", "", ""])
        fdata.append([f"Date: {sign_date}", "", "", ""])

        ft = Table(fdata, colWidths=[W*0.3, W*0.05, W*0.32, W*0.33])
        style_cmds = [
            ("FONTSIZE",  (0,0), (-1,-1), 8),
            ("FONTNAME",  (0,0), (0,0), "Helvetica-Bold"),
            ("TOPPADDING",(0,0),(-1,-1),2),
        ]
        # Bold the name rows
        for r_idx, row in enumerate(fdata):
            if r_idx >= 3 and row[0] and row[0] not in ("", f"M No: {auditor_mrn}", f"Place: {sign_place}", f"Date: {sign_date}"):
                style_cmds.append(("FONTNAME", (0,r_idx),(0,r_idx),"Helvetica-Bold"))
                style_cmds.append(("LINEABOVE",(0,r_idx),(-1,r_idx),0.5,C_DARK))
            if r_idx >= 3 and row[2] and row[2] not in (entity_name.upper(), f"FRN: {auditor_frn}"):
                if not row[2].startswith("DIN:"):
                    style_cmds.append(("FONTNAME",(2,r_idx),(3,r_idx),"Helvetica-Bold"))
        ft.setStyle(TableStyle(style_cmds))
        story.append(ft)

    # Balance Sheet
    if doc.bs:
        _entity_header(f"Balance Sheet as at 31st March, {year_end}")
        story.append(_fs_table(doc.bs, "BS", cy_label, py_label))
        _footer_table()
        story.append(PageBreak())

    # P&L or I&E
    if doc.pl:
        _entity_header(f"Statement of Profit and Loss for the year ended 31st March, {year_end}")
        story.append(_fs_table(doc.pl, "PL", cy_label, py_label))
        _footer_table()
        story.append(PageBreak())
    if doc.ie:
        _entity_header(f"Income and Expenditure Account for the year ended 31st March, {year_end}")
        story.append(_fs_table(doc.ie, "IE", cy_label, py_label))
        _footer_table()
        story.append(PageBreak())

    # R&P
    if doc.rp:
        _entity_header(f"Receipt and Payment Account for the year ended 31st March, {year_end}")
        story.append(_fs_table(doc.rp, "RP", cy_label, py_label))
        story.append(PageBreak())

    # Cash Flow
    if doc.cf:
        _entity_header(f"Cash Flow Statement for the year ended 31st March, {year_end}")
        story.append(_fs_table(doc.cf, "CF", cy_label, py_label))
        story.append(PageBreak())

    # Notes
    if notes:
        story.append(Paragraph("Notes to Financial Statements", st["title"]))
        story.append(Spacer(1, 4*mm))
        for note in notes:
            story.append(_note_table(note, cy_label, py_label))
            story.append(Spacer(1, 4*mm))

    pdf.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)
