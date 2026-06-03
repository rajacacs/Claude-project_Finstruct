"""Dashboard — project list and new project wizard."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from ..config import THEME as T, PROJECTS_DIR
from ..core.entity_types import EntityType, ENTITY_LABELS
from ..gui.theme import primary_btn, secondary_btn, label, card


class Dashboard(ttk.Frame):
    def __init__(self, parent, settings_db, on_open_project: callable):
        super().__init__(parent)
        self._sdb       = settings_db
        self._on_open   = on_open_project
        self._build()
        self._refresh()

    def _build(self):
        # Header
        hdr = ttk.Frame(self, style="Card.TFrame", padding=16)
        hdr.pack(fill="x", padx=0, pady=0)
        label(hdr, "FinStruct", style="Title.TLabel").pack(side="left")
        label(hdr, "Financial Statement Automation",
              style="Muted.TLabel").pack(side="left", padx=12)
        primary_btn(hdr, "+ New Project", command=self._new_project).pack(side="right", padx=4)
        secondary_btn(hdr, "Open .finstruct …", command=self._browse_open).pack(side="right", padx=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Recent projects
        label(self, "Recent Projects", style="Sec.TLabel").pack(
            anchor="w", padx=16, pady=(12, 4))

        self._list_frame = ttk.Frame(self)
        self._list_frame.pack(fill="both", expand=True, padx=16, pady=4)

    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        recent = self._sdb.get_recent(15)
        if not recent:
            label(self._list_frame,
                  "No recent projects. Click '+ New Project' to begin.",
                  style="Muted.TLabel").pack(pady=20)
            return
        cols = [("name","Entity Name",240),("type","Type",180),
                ("fy","FY",80),("opened","Last Opened",160),("path","Path",300)]
        tree = ttk.Treeview(self._list_frame,
                            columns=[c[0] for c in cols],
                            show="headings", height=14)
        for cid, hdr, w in cols:
            tree.heading(cid, text=hdr)
            tree.column(cid, width=w, anchor="w")
        vsb = ttk.Scrollbar(self._list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        for r in recent:
            opened = r["last_opened"][:16].replace("T"," ") if r["last_opened"] else ""
            tree.insert("", "end", iid=r["path"],
                        values=(r["entity_name"], r["entity_type"],
                                r["fy"], opened, r["path"]))
        tree.bind("<Double-Button-1>", lambda e: self._open_selected(tree))
        tree.bind("<Return>", lambda e: self._open_selected(tree))

        btn_row = ttk.Frame(self._list_frame)
        btn_row.pack(side="bottom", fill="x", pady=6)
        secondary_btn(btn_row, "Remove from list",
                      command=lambda: self._remove(tree)).pack(side="left", padx=4)

    def _open_selected(self, tree: ttk.Treeview):
        sel = tree.selection()
        if not sel:
            return
        path = sel[0]
        if not Path(path).exists():
            messagebox.showerror("Not found", f"Project file not found:\n{path}")
            self._sdb.remove_recent(path)
            self._refresh()
            return
        self._on_open(Path(path))

    def _browse_open(self):
        path = filedialog.askopenfilename(
            title="Open FinStruct Project",
            filetypes=[("FinStruct Project", "*.finstruct"), ("All", "*.*")],
            initialdir=str(PROJECTS_DIR))
        if path:
            self._on_open(Path(path))

    def _remove(self, tree: ttk.Treeview):
        sel = tree.selection()
        if sel:
            self._sdb.remove_recent(sel[0])
            self._refresh()

    def _new_project(self):
        NewProjectDialog(self, self._sdb, self._on_open)


class NewProjectDialog(tk.Toplevel):
    def __init__(self, parent, settings_db, on_create: callable):
        super().__init__(parent)
        self._sdb      = settings_db
        self._on_create = on_create
        self.title("New Project")
        self.geometry("480x320")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=T["bg"])
        self._build()

    def _build(self):
        ttk.Label(self, text="Create New FinStruct Project",
                  style="Sec.TLabel").pack(padx=16, pady=(16, 6), anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=4)

        grid = ttk.Frame(self)
        grid.pack(fill="x", padx=20, pady=6)

        def row(r, lbl, widget):
            ttk.Label(grid, text=lbl).grid(row=r, column=0, sticky="w", pady=4, padx=4)
            widget.grid(row=r, column=1, sticky="ew", pady=4, padx=4)
        grid.columnconfigure(1, weight=1)

        self._name_var = tk.StringVar()
        self._fy_var   = tk.StringVar(value="2024-25")
        self._etype_var= tk.StringVar()
        self._path_var = tk.StringVar(value=str(PROJECTS_DIR))

        row(0, "Entity Name *", ttk.Entry(grid, textvariable=self._name_var, width=36))
        row(1, "Financial Year *", ttk.Entry(grid, textvariable=self._fy_var, width=16))
        etype_cb = ttk.Combobox(grid, textvariable=self._etype_var,
                                values=list(ENTITY_LABELS.values()),
                                state="readonly", width=34)
        etype_cb.set(list(ENTITY_LABELS.values())[0])
        row(2, "Entity Type *", etype_cb)

        path_row = ttk.Frame(grid)
        ttk.Entry(path_row, textvariable=self._path_var, width=28,
                  state="readonly").pack(side="left")
        secondary_btn(path_row, "…", command=self._pick_folder).pack(side="left", padx=4)
        row(3, "Project Folder", path_row)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=8)
        btn = ttk.Frame(self)
        btn.pack(pady=8)
        primary_btn(btn, "Create Project", command=self._create).pack(side="left", padx=8)
        secondary_btn(btn, "Cancel", command=self.destroy).pack(side="left")

        self._etype_map = {v: k for k, v in ENTITY_LABELS.items()}

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Project Location",
                                         initialdir=self._path_var.get())
        if folder:
            self._path_var.set(folder)

    def _create(self):
        name = self._name_var.get().strip()
        fy   = self._fy_var.get().strip()
        etype_lbl = self._etype_var.get()

        if not name:
            messagebox.showerror("Error", "Entity Name is required."); return
        from ..core.validator import validate_fy
        if not validate_fy(fy):
            messagebox.showerror("Error", "FY format must be YYYY-YY (e.g. 2024-25)."); return

        etype = self._etype_map.get(etype_lbl, "COMPANY")
        safe  = "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()
        folder = Path(self._path_var.get()) / f"{safe}_{fy}"
        folder.mkdir(parents=True, exist_ok=True)
        proj_path = folder / f"{safe}_{fy}.finstruct"

        from ..data.project_db import ProjectDB
        db = ProjectDB(proj_path)
        db.connect()
        db.set_meta("entity_type", etype)
        db.set_meta("financial_year", fy)
        db.set_meta("created_at", datetime.now().isoformat())
        db.set_entity("entity_name", name)
        db.set_entity("financial_year", fy)
        db.log("PROJECT_CREATED", f"{name} | {etype} | {fy}")
        db.close()

        self._sdb.add_recent(str(proj_path), name, ENTITY_LABELS[etype], fy)
        self.destroy()
        self._on_create(proj_path)
