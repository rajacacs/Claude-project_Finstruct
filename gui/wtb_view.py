"""Working Trial Balance review grid."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME as T
from gui.theme import primary_btn, secondary_btn, label
from core.wtb_engine import build_wtb_lines, aggregate_by_code, validate_balance
from gui.fs_grid_view import EditableGrid


class WTBView(ttk.Frame):
    def __init__(self, parent, db, on_proceed: callable = None):
        super().__init__(parent)
        self._db = db
        self._on_proceed = on_proceed
        self._build()
        self._load()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        label(top, "4.  Working Trial Balance / Mapped TB", style="Sec.TLabel").pack(side="left")
        secondary_btn(top, "Add Adjustment Entry", command=self._add_adj).pack(side="left", padx=8)
        primary_btn(top, "✔ Proceed to PPE →", command=self._proceed).pack(side="right", padx=4)
        primary_btn(top, "Validate F9", command=self._validate).pack(side="right", padx=4)

        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var,
                  style="Muted.TLabel").pack(fill="x", padx=8)

        cols = [
            ("group",   "Group",            160, "w"),
            ("heading", "Heading",          200, "w"),
            ("ledger",  "Ledger Name",      220, "w"),
            ("code",    "Code",              70, "center"),
            ("cy",      "CY Net ₹",         120, "e"),
            ("py",      "PY Net ₹",         120, "e"),
            ("fs_tag",  "BS/PL/IE",          60, "center"),
        ]
        self._grid = EditableGrid(self, columns=cols,
                                  on_cell_change=None,
                                  editable_cols={"cy","py"})
        self._grid.pack(fill="both", expand=True, padx=8, pady=4)

        # Adjustment entries sub-view
        adj_frame = ttk.LabelFrame(self, text="Adjustment Entries")
        adj_frame.pack(fill="x", padx=8, pady=4)
        self._adj_list = tk.Text(adj_frame, height=4, state="disabled",
                                 bg=T["bg_white"], font=(T["font"], 9), relief="flat")
        self._adj_list.pack(fill="x", padx=4, pady=4)

    def _load(self):
        try:
            wtb_rows = self._db.get_wtb()
            raw_rows = self._db.get_raw_tb()

            # Validate WTB has data
            if not raw_rows:
                self._grid.load_rows([])
                self._status_var.set("⚠ No Trial Balance data found. Please import TB first (Step 2).")
                self._adj_list.configure(state="normal")
                self._adj_list.delete("1.0", "end")
                self._adj_list.insert("end", "(No adjustments)")
                self._adj_list.configure(state="disabled")
                return

            lines    = build_wtb_lines(wtb_rows, raw_rows)
            from core.master_db import get_lookup_map
            lm = get_lookup_map()
            grid_rows = []
            for i, ln in enumerate(lines):
                e = lm.get(ln.mapping_code)
                group   = e.group    if e else ""
                heading = e.heading  if e else ""
                fs_tag  = e.fs_tag   if e else ""
                cy_s = f"{ln.cy_net:,.2f}" if ln.cy_net else "—"
                py_s = f"{ln.py_net:,.2f}" if ln.py_net else "—"
                tag = "alt" if i % 2 else ""
                grid_rows.append({
                    "iid": str(ln.raw_tb_id),
                    "tag": tag,
                    "values": [group, heading, ln.ledger_name,
                               ln.mapping_code, cy_s, py_s, fs_tag],
                })
            self._grid.load_rows(grid_rows)

            # Show adjustments
            adjs = self._db.get_adjustments()
            self._adj_list.configure(state="normal")
            self._adj_list.delete("1.0", "end")
            for a in adjs:
                dr = f"Dr ₹{a['dr_amount']:,.2f}" if a["dr_amount"] else ""
                cr = f"Cr ₹{a['cr_amount']:,.2f}" if a["cr_amount"] else ""
                self._adj_list.insert("end",
                    f"{a['adj_id']}  |  {a['ledger_name']}  |  {dr}{cr}  |  {a['narration']}\n")
            self._adj_list.configure(state="disabled")

            # Balance
            totals = aggregate_by_code(lines)
            et = self._db.get_meta("entity_type") or "COMPANY"
            r  = validate_balance(totals, et)
            if r.ok:
                self._status_var.set(
                    f"✅ {len(lines)} ledgers  |  Balance Sheet balances  |  "
                    f"Total mapped codes: {len(totals)}")
            else:
                self._status_var.set("⚠ " + " | ".join(r.errors + r.warnings))
        except Exception as e:
            import traceback
            err_msg = f"Failed to load Working Trial Balance: {str(e)}"
            self._status_var.set(f"❌ {err_msg}")
            messagebox.showerror("System Error", 
                                f"{err_msg}\n\nTechnical details:\n{traceback.format_exc()}")

    def _validate(self):
        wtb_rows = self._db.get_wtb()
        raw_rows = self._db.get_raw_tb()
        lines    = build_wtb_lines(wtb_rows, raw_rows)
        totals   = aggregate_by_code(lines)
        et = self._db.get_meta("entity_type") or "COMPANY"
        r  = validate_balance(totals, et)
        if r.ok:
            messagebox.showinfo("✅ Balanced", "Balance Sheet balances correctly!")
        else:
            messagebox.showerror("Imbalance", "\n".join(r.errors + r.warnings))

    def _add_adj(self):
        AdjDialog(self, self._db, on_save=self._load)

    def _proceed(self):
        if self._on_proceed:
            self._on_proceed()


class AdjDialog(tk.Toplevel):
    def __init__(self, parent, db, on_save: callable = None):
        super().__init__(parent)
        self._db = db
        self._on_save = on_save
        self.title("Add Adjustment Entry")
        self.geometry("480x320")
        self.grab_set()
        self.configure(bg=T["bg"])
        self._build()

    def _build(self):
        g = ttk.Frame(self, padding=16)
        g.pack(fill="both", expand=True)
        g.columnconfigure(1, weight=1)
        fields = [
            ("adj_id",    "Entry ID (auto)"),
            ("ledger",    "Ledger Name"),
            ("code",      "Mapping Code"),
            ("dr",        "Debit Amount (₹)"),
            ("cr",        "Credit Amount (₹)"),
            ("narration", "Narration"),
        ]
        self._vars: dict[str, tk.StringVar] = {}
        import datetime
        adj_id = f"AJE-{datetime.datetime.now().strftime('%d%m%H%M')}"
        for i, (k, lbl) in enumerate(fields):
            ttk.Label(g, text=lbl).grid(row=i, column=0, sticky="w", pady=4, padx=4)
            var = tk.StringVar(value=adj_id if k == "adj_id" else "")
            self._vars[k] = var
            ttk.Entry(g, textvariable=var, width=36).grid(
                row=i, column=1, sticky="ew", pady=4, padx=4)

        btn = ttk.Frame(g)
        btn.grid(row=len(fields), column=0, columnspan=2, pady=12)
        primary_btn(btn, "Save Entry", command=self._save).pack(side="left", padx=8)
        secondary_btn(btn, "Cancel", command=self.destroy).pack(side="left")

    def _save(self):
        v = {k: var.get().strip() for k, var in self._vars.items()}
        if not v["ledger"] or not v["code"]:
            messagebox.showerror("Error", "Ledger and Code are required."); return
        try:
            dr = float(v["dr"] or 0)
            cr = float(v["cr"] or 0)
        except ValueError:
            messagebox.showerror("Error", "Dr/Cr must be numeric."); return
        self._db.add_adjustment(v["adj_id"], v["ledger"], v["code"],
                                dr, cr, v["narration"])
        self.destroy()
        if self._on_save:
            self._on_save()
