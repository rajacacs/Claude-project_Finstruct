"""FS Viewer — tabbed spreadsheet view of all generated statements."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME as T
from core.fs_engine import FSDocument, FSLine
from gui.theme import primary_btn, secondary_btn, label
from gui.fs_grid_view import EditableGrid


def _fmt(v: float | None) -> str:
    if v is None or v == 0:
        return "-"
    return f"{v:,.2f}"


class FSViewer(ttk.Frame):
    def __init__(self, parent, doc: FSDocument, db,
                 on_proceed: callable = None,
                 rebuild_cf: callable = None,
                 is_small_company: bool = False):
        super().__init__(parent)
        self._doc = doc
        self._db  = db
        self._on_proceed = on_proceed
        self._rebuild_cf = rebuild_cf
        self._is_small   = is_small_company
        self._grids: dict[str, EditableGrid] = {}
        self._nb: ttk.Notebook | None = None
        self._include_cf = tk.BooleanVar(value=True)
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        label(top, "6.  Financial Statements", style="Sec.TLabel").pack(side="left")
        secondary_btn(top, "Save Overrides", command=self._save_overrides).pack(side="left", padx=8)

        # Cash Flow toggle — visible for COMPANY/SEC8 with small-co note
        et = self._doc.entity_type
        if et in ("COMPANY", "SEC8"):
            cf_frame = ttk.Frame(top)
            cf_frame.pack(side="left", padx=12)
            cb = ttk.Checkbutton(cf_frame, text="Include Cash Flow Statement",
                                 variable=self._include_cf,
                                 command=self._on_cf_toggle,
                                 style="TCheckbutton")
            cb.pack(side="left")
            if self._is_small:
                label(cf_frame, "(optional — small company)", style="Muted.TLabel").pack(side="left", padx=4)

        primary_btn(top, "→ Generate Notes  F10", command=self._go_notes).pack(side="right", padx=4)

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=8, pady=4)
        self._populate_tabs()
        self._build_signatory_panel()

    def _populate_tabs(self):
        nb = self._nb
        # Remove all existing tabs
        for tab in nb.tabs():
            nb.forget(tab)
        self._grids.clear()

        statement_map = [
            ("bs", "Balance Sheet"),
            ("pl", "Profit & Loss"),
            ("ie", "Income & Expenditure"),
            ("rp", "Receipt & Payment"),
            ("cf", "Cash Flow"),
        ]
        for attr, title in statement_map:
            if attr == "cf" and not self._include_cf.get():
                continue
            lines = getattr(self._doc, attr, [])
            if not lines:
                continue
            frame = ttk.Frame(nb)
            nb.add(frame, text=title)
            grid = self._make_grid(frame, lines, attr)
            self._grids[attr] = grid

    def _on_cf_toggle(self):
        include = self._include_cf.get()
        if self._rebuild_cf:
            self._doc.cf = self._rebuild_cf(include)
        else:
            # Fallback: if no rebuild callback, just hide/show existing data
            if not include:
                self._doc.cf = []
        self._populate_tabs()

    def _make_grid(self, parent, lines: list[FSLine], section: str) -> EditableGrid:
        cols = [
            ("label", "Particulars",        420, "w"),
            ("note",  "Note",                50, "center"),
            ("cy",    "Current Year ₹",     140, "e"),
            ("py",    "Previous Year ₹",    140, "e"),
        ]
        grid = EditableGrid(parent, columns=cols,
                            on_cell_change=lambda iid, col, val:
                                self._on_cell_edit(section, iid, col, val),
                            editable_cols={"cy", "py"})
        grid.pack(fill="both", expand=True)

        rows = []
        for i, ln in enumerate(lines):
            indent = "    " * ln.indent
            cy_s = _fmt(ln.cy) if ln.row_type not in ("SECTION","HEADER","BLANK","TEXT") else ""
            py_s = _fmt(ln.py) if ln.row_type not in ("SECTION","HEADER","BLANK","TEXT") else ""
            note_s = str(ln.note) if ln.note else ""
            tag_map = {
                "HEADER":  "header",
                "SECTION": "section",
                "TOTAL":   "total",
                "GRAND":   "grand",
                "BLANK":   "",
                "TEXT":    "red",
            }
            tag = tag_map.get(ln.row_type, "alt" if i % 2 == 0 else "")
            rows.append({
                "iid":    f"{section}_{i}",
                "tag":    tag,
                "values": [indent + ln.label, note_s, cy_s, py_s],
            })
        grid.load_rows(rows)
        return grid

    def _on_cell_edit(self, section: str, iid: str, col: str, new_val: str):
        try:
            v = float(str(new_val).replace(",", ""))
        except ValueError:
            return
        # Store override — extract line index from iid
        try:
            idx = int(iid.split("_")[1])
        except (IndexError, ValueError):
            return
        lines = getattr(self._doc, section.lower() if section not in ("ie","rp","cf") else section, [])
        if idx < len(lines):
            ln = lines[idx]
            if col == "cy":
                ln.cy = v
            elif col == "py":
                ln.py = v

    def _save_overrides(self):
        for section, grid in self._grids.items():
            rows = grid.get_all_rows()
            lines = getattr(self._doc, section, [])
            for i, (row, ln) in enumerate(zip(rows, lines)):
                try:
                    cy = float(str(row[2]).replace(",","")) if row[2] not in ("","-") else ln.cy
                    py = float(str(row[3]).replace(",","")) if row[3] not in ("","-") else ln.py
                    if cy != ln.cy or py != ln.py:
                        self._db.set_override(section, f"{section}_{i}", cy, py, "Manual edit")
                except (ValueError, IndexError):
                    pass
        messagebox.showinfo("Saved", "Overrides saved.")

    def _go_notes(self):
        if self._on_proceed:
            self._on_proceed()

    def _build_signatory_panel(self):
        """Collapsible signatory summary panel at the bottom of the viewer."""
        self._sig_visible = tk.BooleanVar(value=False)

        toggle = ttk.Frame(self)
        toggle.pack(fill="x", padx=8, pady=(0, 2))
        ttk.Checkbutton(toggle, text="▼  Signing Details",
                        variable=self._sig_visible,
                        command=self._toggle_signatory,
                        style="TCheckbutton").pack(side="left")
        ttk.Button(toggle, text="Edit", width=5,
                   command=self._edit_signatories).pack(side="left", padx=4)

        self._sig_frame = ttk.Frame(self, relief="groove", borderwidth=1)
        # Not packed yet — shown only when checkbox is ticked

    def _toggle_signatory(self):
        if self._sig_visible.get():
            self._refresh_signatory()
            self._sig_frame.pack(fill="x", padx=8, pady=(0, 4))
        else:
            self._sig_frame.pack_forget()

    def _refresh_signatory(self):
        for w in self._sig_frame.winfo_children():
            w.destroy()
        em = self._db.get_all_entity()
        rows = [
            ("Auditor Firm",    em.get("auditor_firm", "") + (f"  FRN: {em.get('auditor_frn','')}" if em.get("auditor_frn") else "")),
            ("Partner",         em.get("auditor_partner", "") + (f"  M.No: {em.get('auditor_mrn','')}" if em.get("auditor_mrn") else "")),
            ("Signing Place",   em.get("signing_place", "")),
            ("Signing Date",    em.get("signing_date", "")),
        ]
        try:
            dirs = [d for d in self._db.get_directors() if d["is_signing_auth"]]
            for i, d in enumerate(dirs):
                rows.insert(i + 2, (f"Director {i+1}", f"{d['name']}  {d['designation']}  DIN: {d['din'] or '—'}"))
        except Exception:
            pass

        for key, val in rows:
            r = ttk.Frame(self._sig_frame)
            r.pack(fill="x", padx=8, pady=1)
            ttk.Label(r, text=key + ":", width=18, anchor="w",
                      font=(None, 9, "bold")).pack(side="left")
            ttk.Label(r, text=val or "—", font=(None, 9)).pack(side="left")

        if not any(v for _, v in rows):
            ttk.Label(self._sig_frame,
                      text="⚠ Signatory details not filled. Please complete Entity Setup (Step 1).",
                      foreground="#C50F1F").pack(padx=8, pady=4)

    def _edit_signatories(self):
        messagebox.showinfo("Edit Signatories",
                            "Go to Step 1 (Entity Setup) to update signatory details.")
