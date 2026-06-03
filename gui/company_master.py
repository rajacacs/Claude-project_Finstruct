"""Entity Master form — all entity types."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from ..config import THEME as T
from ..gui.theme import label, entry, card, primary_btn, secondary_btn
from ..core.entity_types import EntityType, ENTITY_LABELS, AOP_SUBTYPES, TRUST_SUBTYPES
from ..core.validator import validate_cin, validate_fy, validate_pan


class CompanyMasterForm(ttk.Frame):
    def __init__(self, parent, db, on_save: callable = None):
        super().__init__(parent)
        self._db    = db
        self._on_save = on_save
        self._vars: dict[str, tk.StringVar] = {}
        self.configure(style="TFrame")
        self._build()
        self._load()

    def _field(self, parent, row: int, key: str, label_text: str, width: int = 40,
               required: bool = False) -> ttk.Entry:
        lbl = "*" + label_text if required else label_text
        ttk.Label(parent, text=lbl, style="TLabel").grid(
            row=row, column=0, sticky="w", padx=6, pady=3)
        var = tk.StringVar()
        self._vars[key] = var
        e = ttk.Entry(parent, textvariable=var, width=width)
        e.grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        return e

    def _combo(self, parent, row: int, key: str, label_text: str,
               values: list) -> ttk.Combobox:
        ttk.Label(parent, text=label_text, style="TLabel").grid(
            row=row, column=0, sticky="w", padx=6, pady=3)
        var = tk.StringVar()
        self._vars[key] = var
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=38)
        cb.grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        return cb

    def _build(self):
        entity_type = self._db.get_meta("entity_type") or "COMPANY"

        # Scrollable canvas
        canvas = tk.Canvas(self, bg=T["bg"], highlightthickness=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        r = 0
        # ── Entity Info ─────────────────────────────────────────────────
        ttk.Label(inner, text="Entity Information",
                  style="Sec.TLabel").grid(row=r, column=0, columnspan=2,
                                           sticky="ew", pady=(8, 4), padx=6)
        r += 1
        self._field(inner, r, "entity_name", "Entity / Company Name", required=True); r += 1
        self._field(inner, r, "financial_year", "Financial Year (YYYY-YY)", required=True); r += 1
        self._field(inner, r, "pan", "PAN"); r += 1
        self._field(inner, r, "address", "Registered / Principal Office", width=50); r += 1

        if entity_type == "COMPANY":
            self._field(inner, r, "cin",  "CIN (21 chars)"); r += 1
            self._field(inner, r, "date_of_incorp", "Date of Incorporation"); r += 1
            self._combo(inner, r, "entity_subtype", "Company Subtype",
                        ["Regular Company", "Small Company", "OPC", "Dormant"]); r += 1
        elif entity_type == "LLP":
            self._field(inner, r, "llpin", "LLPIN"); r += 1
            self._field(inner, r, "date_of_reg", "Date of Registration"); r += 1
        elif entity_type in ("PROP",):
            self._field(inner, r, "prop_name", "Proprietor Name"); r += 1
        elif entity_type == "PART":
            self._field(inner, r, "partner1_name", "Partner 1 Name"); r += 1
            self._field(inner, r, "partner1_ratio", "Partner 1 P/L Ratio (%)"); r += 1
            self._field(inner, r, "partner2_name", "Partner 2 Name"); r += 1
            self._field(inner, r, "partner2_ratio", "Partner 2 P/L Ratio (%)"); r += 1
        elif entity_type == "AOP":
            self._combo(inner, r, "entity_subtype", "AOP Subtype", AOP_SUBTYPES); r += 1
            self._field(inner, r, "reg_no", "Registration No."); r += 1
            self._field(inner, r, "president_name", "President / Chairperson"); r += 1
            self._field(inner, r, "secretary_name", "Honorary Secretary"); r += 1
            self._field(inner, r, "treasurer_name", "Treasurer"); r += 1
        elif entity_type in ("TRUST", "SEC8"):
            self._field(inner, r, "trust_deed_date", "Trust Deed / Reg Date"); r += 1
            self._field(inner, r, "reg_no", "Registration No."); r += 1

        ttk.Separator(inner, orient="horizontal").grid(
            row=r, column=0, columnspan=2, sticky="ew", pady=8, padx=6)
        r += 1

        # ── Directors / Signatories ──────────────────────────────────────
        if entity_type in ("COMPANY", "SEC8"):
            ttk.Label(inner, text="Directors & KMP",
                      style="Sec.TLabel").grid(row=r, column=0, columnspan=2,
                                               sticky="ew", pady=(4, 2), padx=6)
            r += 1

            # Directors Treeview panel
            dir_frame = ttk.Frame(inner)
            dir_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
            r += 1

            dir_cols = ("name", "designation", "din", "signs")
            self._dir_tree = ttk.Treeview(dir_frame, columns=dir_cols,
                                          show="headings", height=5)
            self._dir_tree.heading("name",        text="Name")
            self._dir_tree.heading("designation", text="Designation")
            self._dir_tree.heading("din",         text="DIN")
            self._dir_tree.heading("signs",       text="Signs FS?")
            self._dir_tree.column("name",        width=180)
            self._dir_tree.column("designation", width=130)
            self._dir_tree.column("din",         width=90)
            self._dir_tree.column("signs",       width=70, anchor="center")
            self._dir_tree.pack(side="left", fill="x", expand=True)

            dir_sb = ttk.Scrollbar(dir_frame, orient="vertical",
                                   command=self._dir_tree.yview)
            self._dir_tree.configure(yscrollcommand=dir_sb.set)
            dir_sb.pack(side="left", fill="y")

            dir_btns = ttk.Frame(inner)
            dir_btns.grid(row=r, column=0, columnspan=2, sticky="w", padx=6, pady=(0,4))
            r += 1
            ttk.Button(dir_btns, text="➕ Add",    command=self._dir_add).pack(side="left", padx=2)
            ttk.Button(dir_btns, text="✏ Edit",   command=self._dir_edit).pack(side="left", padx=2)
            ttk.Button(dir_btns, text="🗑 Remove", command=self._dir_remove).pack(side="left", padx=2)

            self._field(inner, r, "cfo_name", "CFO Name"); r += 1
            self._field(inner, r, "cs_name",  "Company Secretary Name"); r += 1
            self._field(inner, r, "cs_memno", "CS Membership No."); r += 1
            ttk.Separator(inner, orient="horizontal").grid(
                row=r, column=0, columnspan=2, sticky="ew", pady=8, padx=6)
            r += 1

        # ── Auditor Block ────────────────────────────────────────────────
        ttk.Label(inner, text="Auditor Details",
                  style="Sec.TLabel").grid(row=r, column=0, columnspan=2,
                                           sticky="ew", pady=(4, 2), padx=6)
        r += 1
        self._field(inner, r, "auditor_firm",    "Auditor Firm Name"); r += 1
        self._field(inner, r, "auditor_frn",     "Firm Reg No (FRN)"); r += 1
        self._field(inner, r, "auditor_partner", "Partner Name"); r += 1
        self._field(inner, r, "auditor_mrn",     "Membership No (MRN)"); r += 1
        self._field(inner, r, "signing_place",   "Signing Place"); r += 1
        self._field(inner, r, "signing_date",    "Signing Date (DD-Mon-YYYY)"); r += 1
        r += 1

        # ── Buttons ──────────────────────────────────────────────────────
        btn_frame = ttk.Frame(inner)
        btn_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=10)
        primary_btn(btn_frame, "💾  Save", command=self._save).pack(side="left", padx=4)
        secondary_btn(btn_frame, "↺  Reset", command=self._load).pack(side="left", padx=4)

        inner.columnconfigure(1, weight=1)

    def _load(self):
        data = self._db.get_all_entity()
        for key, var in self._vars.items():
            var.set(data.get(key, ""))
        self._load_directors()

    def _save(self):
        data = {k: v.get().strip() for k, v in self._vars.items()}

        errors = []
        if not data.get("entity_name"):
            errors.append("Entity Name is mandatory.")
        if data.get("financial_year") and not validate_fy(data["financial_year"]):
            errors.append("Financial Year must be YYYY-YY format (e.g. 2024-25).")
        if data.get("cin") and not validate_cin(data["cin"]):
            errors.append("CIN must be exactly 21 characters.")
        if data.get("pan") and not validate_pan(data["pan"]):
            errors.append("PAN format invalid (e.g. ABCDE1234F).")

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        self._db.save_entity_batch(data)
        if data.get("financial_year"):
            self._db.set_meta("financial_year", data["financial_year"])
        self._db.log("ENTITY_MASTER_SAVED", "")
        messagebox.showinfo("Saved", "Entity master saved successfully.")
        if self._on_save:
            self._on_save(data)

    def _load_directors(self):
        if not hasattr(self, '_dir_tree'):
            return
        for item in self._dir_tree.get_children():
            self._dir_tree.delete(item)
        try:
            for d in self._db.get_directors():
                signs = "✔ Yes" if d["is_signing_auth"] else "No"
                self._dir_tree.insert("", "end", iid=str(d["id"]),
                                      values=(d["name"], d["designation"],
                                              d["din"] or "", signs))
        except Exception:
            pass

    def _dir_add(self):
        self._dir_dialog(None)

    def _dir_edit(self):
        sel = self._dir_tree.selection()
        if not sel:
            from tkinter import messagebox
            messagebox.showinfo("Select", "Select a director to edit.")
            return
        dir_id = int(sel[0])
        rows = self._db.get_directors()
        d = next((dict(r) for r in rows if r["id"] == dir_id), None)
        if d:
            self._dir_dialog(d)

    def _dir_remove(self):
        sel = self._dir_tree.selection()
        if not sel:
            return
        from tkinter import messagebox
        if messagebox.askyesno("Remove", "Remove selected director?"):
            self._db.delete_director(int(sel[0]))
            self._load_directors()

    def _dir_dialog(self, d: dict | None):
        from tkinter import Toplevel, StringVar, BooleanVar, messagebox
        top = Toplevel(self)
        top.title("Add Director" if d is None else "Edit Director")
        top.resizable(False, False)
        top.grab_set()

        fields = [
            ("name",        "Name *",        d["name"]        if d else ""),
            ("designation", "Designation",   d["designation"] if d else "Director"),
            ("din",         "DIN",           d["din"]         if d else ""),
            ("pan",         "PAN",           d["pan"]         if d else ""),
        ]
        vars_ = {}
        for i, (key, lbl, val) in enumerate(fields):
            ttk.Label(top, text=lbl).grid(row=i, column=0, padx=8, pady=4, sticky="w")
            v = StringVar(value=val)
            vars_[key] = v
            ttk.Entry(top, textvariable=v, width=30).grid(row=i, column=1, padx=8, pady=4)

        signs_var = BooleanVar(value=bool(d["is_signing_auth"]) if d else True)
        ttk.Checkbutton(top, text="Signs Financial Statements?",
                        variable=signs_var).grid(row=len(fields), column=0,
                                                 columnspan=2, padx=8, pady=4)

        def _ok():
            name = vars_["name"].get().strip()
            if not name:
                messagebox.showerror("Required", "Name is required.")
                return
            rec = {
                "name":            name,
                "designation":     vars_["designation"].get().strip() or "Director",
                "din":             vars_["din"].get().strip(),
                "pan":             vars_["pan"].get().strip(),
                "is_signing_auth": int(signs_var.get()),
                "sort_order":      d.get("sort_order", 0) if d else 0,
            }
            if d:
                rec["id"] = d["id"]
            self._db.upsert_director(rec)
            self._load_directors()
            top.destroy()

        btn_row = len(fields) + 1
        ttk.Button(top, text="Save", command=_ok).grid(row=btn_row, column=0, padx=8, pady=8)
        ttk.Button(top, text="Cancel", command=top.destroy).grid(row=btn_row, column=1, padx=8, pady=8)
