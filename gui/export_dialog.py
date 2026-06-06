"""Export dialog — PDF, XLSX, DOCX."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from datetime import datetime
from config import THEME as T
from gui.theme import primary_btn, secondary_btn, label
from core.fs_engine import FSEngine, FSDocument
from core.notes_engine import NotesEngine
from core.wtb_engine import aggregate_by_code, build_wtb_lines
from core.ppe_engine import recalc_asset


def _safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in s).strip()


class ExportDialog(tk.Toplevel):
    def __init__(self, parent, db, report_texts: dict | None = None):
        super().__init__(parent)
        self._db     = db
        self._rtexts = report_texts or {}
        self.title("Export Financial Statements")
        self.geometry("520x400")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=T["bg"])
        self._build()

    def _build(self):
        ttk.Label(self, text="Export Financial Statements",
                  style="Sec.TLabel").pack(padx=16, pady=(14, 4), anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=4)

        # Get entity type and turnover to determine which report options to show
        em = self._db.get_all_entity()
        meta = self._db.get_all_meta()
        entity_type = meta.get("entity_type", "COMPANY")

        # Calculate turnover from trial balance (PL001 = Revenue from Operations)
        turnover = 0.0
        try:
            wtb_rows = self._db.get_wtb()
            for row in wtb_rows:
                if row.get("mapping_code") == "PL001":
                    turnover = float(row.get("cy_net", 0) or 0)
                    break
        except Exception:
            pass

        # Format checkboxes
        self._do_pdf  = tk.BooleanVar(value=True)
        self._do_xlsx = tk.BooleanVar(value=True)
        self._do_docx = tk.BooleanVar(value=False)
        self._is_draft= tk.BooleanVar(value=True)

        ttk.Checkbutton(self, text="📄  PDF (Print-ready Financial Statements)",
                       variable=self._do_pdf, style="TCheckbutton").pack(anchor="w", padx=24, pady=3)
        ttk.Checkbutton(self, text="📊  XLSX (Excel — FS + Notes workbook)",
                       variable=self._do_xlsx, style="TCheckbutton").pack(anchor="w", padx=24, pady=3)

        # DOCX options: show Audit Report for Companies and LLPs with turnover > 40 lacs
        # Show Directors Report only for Companies
        docx_label = "📝  DOCX ("
        if entity_type == "COMPANY":
            docx_label += "Directors Report + Audit Report)"
        elif entity_type == "LLP" and turnover > 4000000:
            docx_label += "Audit Report)"
        else:
            docx_label += "Audit Report - Not Applicable)"
            self._do_docx.set(False)

        docx_enabled = (entity_type == "COMPANY") or (entity_type == "LLP" and turnover > 4000000)
        ttk.Checkbutton(self, text=docx_label,
                       variable=self._do_docx, style="TCheckbutton",
                       state="normal" if docx_enabled else "disabled").pack(anchor="w", padx=24, pady=3)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=8)

        # Font selection
        font_frame = ttk.Frame(self)
        font_frame.pack(fill="x", padx=16, pady=4)
        ttk.Label(font_frame, text="Font:").pack(side="left", padx=4)
        self._font_var = tk.StringVar(value="Calibri")
        font_combo = ttk.Combobox(
            font_frame,
            textvariable=self._font_var,
            values=["Aptos", "Aptos Narrow", "Calibri", "Cambria", "Arial",
                   "Times New Roman", "Tahoma", "Verdana", "Segoe UI"],
            state="readonly",
            width=20
        )
        font_combo.pack(side="left", padx=4)

        ttk.Checkbutton(self, text="Mark as DRAFT (watermark on PDF)",
                        variable=self._is_draft, style="TCheckbutton").pack(anchor="w", padx=24, pady=2)

        # Output folder
        folder_frame = ttk.Frame(self)
        folder_frame.pack(fill="x", padx=16, pady=6)
        label(folder_frame, "Output Folder:").pack(side="left", padx=4)
        self._folder_var = tk.StringVar(
            value=str(Path.home() / "Documents" / "FinStruct" / "exports"))
        ttk.Entry(folder_frame, textvariable=self._folder_var,
                  width=36, state="readonly").pack(side="left", padx=4)
        secondary_btn(folder_frame, "Browse",
                      command=self._browse_folder).pack(side="left", padx=4)

        # Progress
        self._prog = ttk.Progressbar(self, mode="indeterminate", length=300)
        self._prog.pack(pady=8)
        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var,
                  style="Muted.TLabel").pack()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=12)
        primary_btn(btn_frame, "Export", command=self._export).pack(side="left", padx=8)
        secondary_btn(btn_frame, "Cancel", command=self.destroy).pack(side="left")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Export Folder")
        if folder:
            self._folder_var.set(folder)

    def _export(self):
        if not any([self._do_pdf.get(), self._do_xlsx.get(), self._do_docx.get()]):
            messagebox.showinfo("Nothing selected", "Select at least one format.")
            return
        self._prog.start(12)
        self._status_var.set("Preparing …")
        threading.Thread(target=self._do_export, daemon=True).start()

    def _do_export(self):
        try:
            folder = Path(self._folder_var.get())
            folder.mkdir(parents=True, exist_ok=True)

            em   = self._db.get_all_entity()
            meta = self._db.get_all_meta()
            fy   = meta.get("financial_year", em.get("financial_year", "FY"))
            et   = meta.get("entity_type", "COMPANY")
            div  = int(meta.get("rounding_divisor", "1"))

            # Build FS document (with adjustments)
            wtb_rows = self._db.get_wtb()
            raw_rows = self._db.get_raw_tb()
            lines    = build_wtb_lines(wtb_rows, raw_rows)
            totals   = aggregate_by_code(lines)
            adj_rows = self._db.get_adjustments()
            if adj_rows:
                totals = apply_adjustments(totals, adj_rows, get_lookup_map())
            engine   = FSEngine(et, totals, em, fy, div)
            doc      = engine.generate()

            # PPE data
            ppe_data = [dict(r) for r in self._db.get_ppe()]
            for a in ppe_data:
                a.update(recalc_asset(a))

            # Notes (with dynamic numbering — also updates doc's note references)
            ne     = NotesEngine(totals, et, ppe_data, div, em)
            notes, _ = ne.generate_dynamic(doc)

            # Apply overrides
            for section in ("BS","PL","IE","RP","CF"):
                overrides = self._db.get_overrides(section)
                lines_list = getattr(doc, section.lower(), [])
                for ln in lines_list:
                    if ln.code in overrides:
                        cy_v, py_v = overrides[ln.code]
                        ln.cy = cy_v; ln.py = py_v

            name = _safe_name(em.get("entity_name", em.get("Company_Name", "Entity")))
            stem = f"{name}_{fy}"
            is_draft = self._is_draft.get()

            if self._do_pdf.get():
                self.after(0, lambda: self._status_var.set("Generating PDF …"))
                from export.pdf_exporter import export_pdf
                export_pdf(doc, notes, folder / f"{stem}_FS.pdf",
                           is_draft=is_draft, db=self._db)

            if self._do_xlsx.get():
                self.after(0, lambda: self._status_var.set("Generating XLSX …"))
                from export.xlsx_exporter import export_xlsx
                export_xlsx(doc, notes, folder / f"{stem}_FS.xlsx")

            if self._do_docx.get():
                self.after(0, lambda: self._status_var.set("Generating DOCX …"))
                from export.docx_exporter import export_docx
                export_docx(
                    em, folder / f"{stem}_Reports.docx",
                    directors_report_text=self._rtexts.get("directors"),
                    audit_report_text=self._rtexts.get("audit"),
                )

            self._db.log("EXPORTED", f"{stem} → {folder}")
            self.after(0, lambda: self._status_var.set(f"✅ Done → {folder}"))
            self.after(0, self._prog.stop)
            self.after(200, lambda: messagebox.showinfo(
                "Export Complete",
                f"✅ Files saved to:\n{folder}"))

        except Exception as e:
            import traceback
            self.after(0, self._prog.stop)
            self.after(0, lambda: self._status_var.set(f"Error: {e}"))
            self.after(0, lambda: messagebox.showerror("Export Error",
                f"Export failed:\n{e}\n\n{traceback.format_exc()[-600:]}"))
