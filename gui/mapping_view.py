"""ML Mapping Grid — ledger → ICAI head with confidence colours."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from config import THEME as T
from core.mapper import Mapper, CONF_GREEN, CONF_YELLOW
from core.master_db import get_group_tree, get_lookup_map
from gui.theme import primary_btn, secondary_btn, label


class MappingView(ttk.Frame):
    def __init__(self, parent, db, settings_db, entity_type: str,
                 on_complete: callable = None):
        super().__init__(parent)
        self._db         = db
        self._sdb        = settings_db
        self._etype      = entity_type
        self._on_complete = on_complete
        self._mapper: Mapper | None = None
        self._rows: list[dict] = []
        self._lookup = get_lookup_map()
        self._build()
        self._load_async()

    # ── UI Build ─────────────────────────────────────────────────────────
    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        label(top, "3.  Mapping Review", style="Sec.TLabel").pack(side="left")
        primary_btn(top, "▶ Auto-Map All", command=self._run_mapping).pack(side="left", padx=6)
        secondary_btn(top, "☁ AI Assist (unresolved)", command=self._run_ai_assist).pack(side="left", padx=4)
        secondary_btn(top, "✔ Confirm All Green", command=self._confirm_all_green).pack(side="left", padx=4)
        primary_btn(top, "✔ Confirm & Proceed  F9", command=self._confirm_all).pack(side="right", padx=4)

        # Status bar
        self._status_var = tk.StringVar(value="Loading …")
        ttk.Label(self, textvariable=self._status_var,
                  style="Muted.TLabel").pack(fill="x", padx=8)

        # Grid
        cols = [
            ("ledger",   "Ledger Name (TB)",         240, "w"),
            ("group",    "TB Group",                  120, "w"),
            ("mapped",   "Mapped Head (Schedule III)", 280, "w"),
            ("conf",     "Confidence",                 80,  "center"),
            ("source",   "Source",                     70,  "center"),
            ("cy",       "CY Amount ₹",                110, "e"),
            ("py",       "PY Amount ₹",                110, "e"),
        ]
        from gui.fs_grid_view import EditableGrid
        self._grid = EditableGrid(self, columns=cols,
                                  on_cell_change=self._on_cell_change,
                                  editable_cols={"py"})
        self._grid.pack(fill="both", expand=True, padx=8, pady=4)

        # Hint: PY editing
        ttk.Label(self,
                  text="💡 Double-click any 'PY Amount ₹' cell to enter Previous Year figures.",
                  style="Muted.TLabel").pack(fill="x", padx=8, pady=(0, 4))

        # Override panel (shown when row is selected)
        self._ovr_frame = ttk.Frame(self, style="Card.TFrame", padding=6)
        self._ovr_frame.pack(fill="x", padx=8, pady=4)
        label(self._ovr_frame, "Override Mapping:").grid(row=0, column=0, padx=4)
        self._grp_var  = tk.StringVar()
        self._hdg_var  = tk.StringVar()
        self._sub_var  = tk.StringVar()
        self._grp_cb = ttk.Combobox(self._ovr_frame, textvariable=self._grp_var,
                                    state="readonly", width=28)
        self._hdg_cb = ttk.Combobox(self._ovr_frame, textvariable=self._hdg_var,
                                    state="readonly", width=28)
        self._sub_cb = ttk.Combobox(self._ovr_frame, textvariable=self._sub_var,
                                    state="readonly", width=32)
        self._grp_cb.grid(row=0, column=1, padx=4)
        self._hdg_cb.grid(row=0, column=2, padx=4)
        self._sub_cb.grid(row=0, column=3, padx=4)
        primary_btn(self._ovr_frame, "Apply", command=self._apply_override).grid(
            row=0, column=4, padx=6)

        self._tree_var = get_group_tree()
        self._grp_cb["values"] = list(self._tree_var.keys())
        self._grp_var.trace_add("write", self._on_group_change)
        self._hdg_var.trace_add("write", self._on_heading_change)

        self._grid.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Data ─────────────────────────────────────────────────────────────
    def _load_async(self):
        def work():
            self._mapper = Mapper(self._etype, self._sdb)
            raw_rows  = self._db.get_raw_tb()
            wtb_rows  = self._db.get_wtb()
            wtb_by_id = {w["raw_tb_id"]: w for w in wtb_rows}
            self._rows = []
            for raw in raw_rows:
                w = wtb_by_id.get(raw["id"])
                self._rows.append({
                    "raw_tb_id":  raw["id"],
                    "ledger":     raw["ledger_name"],
                    "group":      raw["group_name"] or "",
                    "code":       (w["mapping_code"] if w else "") or "",
                    "conf":       (w["confidence"]   if w else 0.0) or 0.0,
                    "source":     (w["confidence_source"] if w else "") or "",
                    "cy":         (w["cy_net"] if w else 0.0) or raw["cy_net"] or 0.0,
                    "py":         (w["py_net"] if w else 0.0) or raw["py_net"] or 0.0,
                    "confirmed":  bool(w["is_confirmed"] if w else 0),
                })
            self.after(0, self._render)
        threading.Thread(target=work, daemon=True).start()

    def _run_mapping(self):
        if not self._mapper:
            return
        self._status_var.set("Running ML mapping …")
        def work():
            for row in self._rows:
                if row["confirmed"]:
                    continue
                res = self._mapper.map_ledger(row["ledger"])
                row["code"]   = res.code
                row["conf"]   = res.confidence
                row["source"] = res.source
                row["confirmed"] = (res.confidence >= CONF_GREEN)
            self.after(0, self._render)
            self.after(0, self._save_to_db)
        threading.Thread(target=work, daemon=True).start()

    def _run_ai_assist(self):
        unresolved = [r["ledger"] for r in self._rows
                      if r["conf"] < CONF_YELLOW and not r["confirmed"]]
        if not unresolved:
            messagebox.showinfo("AI Assist", "No unresolved mappings."); return
            
        provider = self._sdb.get_ai_provider()
        self._status_var.set(f"Sending {len(unresolved)} ledgers to {provider} API …")
        def work():
            result = self._mapper.map_via_ai(unresolved)
            for row in self._rows:
                code = result.get(row["ledger"])
                if code and code in self._lookup:
                    row["code"]   = code
                    row["conf"]   = 0.90
                    row["source"] = "API"
            self.after(0, self._render)
            self.after(0, self._save_to_db)
        threading.Thread(target=work, daemon=True).start()

    def _render(self):
        grid_rows = []
        g = 0; y = 0; r = 0
        for row in self._rows:
            entry = self._lookup.get(row["code"])
            mapped_label = entry.lookup_name if entry else (row["code"] or "— Not Mapped —")
            conf   = row["conf"]
            conf_s = f"{conf:.0%}" if conf else "—"
            tag    = "green" if conf >= CONF_GREEN else ("yellow" if conf >= CONF_YELLOW else "red")
            if conf < CONF_GREEN: r += 1
            if conf < CONF_YELLOW: y += 1
            cy_s = f"{row['cy']:,.2f}" if row["cy"] else "—"
            py_s = f"{row['py']:,.2f}" if row["py"] else "—"
            grid_rows.append({
                "iid":    str(row["raw_tb_id"]),
                "tag":    tag,
                "values": [row["ledger"], row["group"], mapped_label,
                           conf_s, row["source"], cy_s, py_s],
            })
            if tag == "green": g += 1
        self._grid.load_rows(grid_rows)
        total = len(self._rows)
        self._status_var.set(
            f"Total: {total}  |  ✅ Confirmed: {g}  |  ⚠ Review: {y-r}  |  🔴 Unresolved: {r}"
        )

    def _save_to_db(self):
        for row in self._rows:
            entry = self._lookup.get(row["code"])
            sign  = entry.sign if entry else "DR_POSITIVE"
            cy    = row["cy"]
            py    = row["py"]
            self._db.upsert_wtb(
                row["raw_tb_id"], row["code"],
                row["conf"], row["source"],
                cy, py, int(row["confirmed"])
            )
            if row["confirmed"] and row["code"]:
                self._mapper.confirm_and_learn(row["ledger"], row["code"])

    def _confirm_all_green(self):
        for row in self._rows:
            if row["conf"] >= CONF_GREEN:
                row["confirmed"] = True
        self._save_to_db()
        self._render()

    def _confirm_all(self):
        unmapped = [r for r in self._rows if not r["code"]]
        if unmapped:
            messagebox.showerror("Cannot Proceed",
                f"{len(unmapped)} ledger(s) not mapped. Resolve red rows first.")
            return
        for row in self._rows:
            row["confirmed"] = True
        self._save_to_db()
        self._render()
        if self._on_complete:
            self._on_complete()

    # ── Override Panel ────────────────────────────────────────────────────
    def _on_select(self, event):
        pass  # override panel reactive on group change

    def _on_group_change(self, *_):
        grp = self._grp_var.get()
        hdgs = list(self._tree_var.get(grp, {}).keys())
        self._hdg_cb["values"] = hdgs
        if hdgs:
            self._hdg_var.set(hdgs[0])

    def _on_heading_change(self, *_):
        grp = self._grp_var.get(); hdg = self._hdg_var.get()
        subs = self._tree_var.get(grp, {}).get(hdg, [])
        self._sub_cb["values"] = subs
        if subs:
            self._sub_var.set(subs[0])

    def _apply_override(self):
        grp = self._grp_var.get()
        hdg = self._hdg_var.get()
        sub = self._sub_var.get()
        if not (grp and hdg and sub):
            return
        # Find code
        target = f"{grp} > {hdg} > {sub}"
        code = next((e.code for e in self._lookup.values()
                     if e.lookup_name == target), None)
        if not code:
            return
        iid = self._grid.get_selected_iid()
        if not iid:
            return
        for row in self._rows:
            if str(row["raw_tb_id"]) == iid:
                row["code"]      = code
                row["conf"]      = 1.0
                row["source"]    = "MANUAL"
                row["confirmed"] = True
                break
        self._save_to_db()
        self._render()

    def _on_cell_change(self, iid: str, col_id: str, new_val: str):
        if col_id != "py":
            return
        try:
            cleaned = new_val.replace(",", "").replace("₹", "").strip()
            py_val = float(cleaned) if cleaned and cleaned != "—" else 0.0
        except ValueError:
            return
        for row in self._rows:
            if str(row["raw_tb_id"]) == iid:
                row["py"] = py_val
                # Save immediately so PY persists even before "Confirm"
                self._db.upsert_wtb(
                    row["raw_tb_id"], row["code"],
                    row["conf"], row["source"],
                    row["cy"], py_val, int(row["confirmed"]),
                )
                break
