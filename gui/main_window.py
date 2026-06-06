"""FinStruct Main Window — sidebar workflow + content area."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from config import THEME as T, APP_NAME, APP_VERSION
from data.project_db import ProjectDB
from data.settings_db import SettingsDB
from gui.theme import apply_theme, primary_btn, secondary_btn, label, sidebar_btn
from gui.dashboard import Dashboard

STEPS = [
    ("1", "Entity Setup"),
    ("2", "Import TB"),
    ("3", "Map Ledgers"),
    ("4", "Review WTB"),
    ("5", "PPE Register"),
    ("5b","Annexures"),
    ("6", "Generate FS"),
    ("7", "Notes"),
    ("8", "Reports"),
    ("9", "Export"),
]


class MainWindow:
    def __init__(self, root: tk.Tk):
        self._root     = root
        self._db: ProjectDB | None = None
        self._sdb      = SettingsDB.instance()
        self._step_btns: list[tk.Button] = []
        self._current_step = 0
        self._report_texts: dict = {}

        apply_theme(root)
        root.title(f"{APP_NAME} v{APP_VERSION}")
        root.geometry("1280x820")
        root.minsize(1024, 700)
        root.configure(bg=T["bg"])

        self._build_menu()
        self._build_layout()
        self._show_dashboard()
        self._bind_global_shortcuts()
        self._root.protocol("WM_DELETE_WINDOW", self._on_exit)

    # ── Menu Bar ─────────────────────────────────────────────────────────
    def _build_menu(self):
        mb = tk.Menu(self._root, bg=T["bg_white"], fg=T["text"],
                     activebackground=T["primary_light"],
                     activeforeground=T["primary"], relief="flat")
        self._root.configure(menu=mb)

        # File
        fm = tk.Menu(mb, tearoff=0, bg=T["bg_white"], fg=T["text"],
                     activebackground=T["primary_light"])
        mb.add_cascade(label="File", menu=fm)
        fm.add_command(label="New Project        Ctrl+N", command=self._new_project)
        fm.add_command(label="Open Project …     Ctrl+O", command=self._open_project)
        fm.add_separator()
        fm.add_command(label="Dashboard",          command=self._show_dashboard)
        fm.add_separator()
        fm.add_command(label="Exit", command=self._on_exit)

        # Project
        pm = tk.Menu(mb, tearoff=0, bg=T["bg_white"], fg=T["text"],
                     activebackground=T["primary_light"])
        mb.add_cascade(label="Project", menu=pm)
        pm.add_command(label="Rollover to Next FY", command=self._rollover)
        pm.add_command(label="Lock / Finalize Project", command=self._lock_project)
        pm.add_command(label="Audit Log", command=self._show_audit)

        # Generate
        gm = tk.Menu(mb, tearoff=0, bg=T["bg_white"], fg=T["text"],
                     activebackground=T["primary_light"])
        mb.add_cascade(label="Generate", menu=gm)
        gm.add_command(label="Validate TB          F9",  command=self._validate)
        gm.add_command(label="Generate FS          F5",  command=self._generate_fs)
        gm.add_command(label="Generate Notes       F10", command=self._go_notes)

        # Export
        em = tk.Menu(mb, tearoff=0, bg=T["bg_white"], fg=T["text"],
                     activebackground=T["primary_light"])
        mb.add_cascade(label="Export", menu=em)
        em.add_command(label="Export Dialog …     F12", command=self._export)

        # Help
        hm = tk.Menu(mb, tearoff=0, bg=T["bg_white"], fg=T["text"],
                     activebackground=T["primary_light"])
        mb.add_cascade(label="Help", menu=hm)
        hm.add_command(label="AI Assistance Settings", command=self._show_ai_settings)
        hm.add_command(label="About FinStruct      F1", command=self._about)

    # ── Layout ───────────────────────────────────────────────────────────
    def _build_layout(self):
        # Header bar
        self._hdr = tk.Frame(self._root, bg=T["primary"], height=40)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)
        tk.Label(self._hdr, text=f"  {APP_NAME}",
                 bg=T["primary"], fg="white",
                 font=(T["font"], T["font_head"], "bold")).pack(side="left")
        self._project_label = tk.Label(self._hdr, text="",
                                       bg=T["primary"], fg=T["primary_light"],
                                       font=(T["font"], 9))
        self._project_label.pack(side="left", padx=12)
        self._fy_label = tk.Label(self._hdr, text="",
                                  bg=T["primary"], fg="white",
                                  font=(T["font"], 9))
        self._fy_label.pack(side="right", padx=12)

        # Main content
        body = tk.Frame(self._root, bg=T["bg"])
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = tk.Frame(body, bg=T["bg"], width=200)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        tk.Label(self._sidebar, text="WORKFLOW", bg=T["bg"],
                 fg=T["text_sec"],
                 font=(T["font"], 8, "bold")).pack(anchor="w", padx=12, pady=(12, 4))

        self._step_btns = []
        for i, (num, name) in enumerate(STEPS):
            btn = sidebar_btn(self._sidebar, f"  {num}.  {name}", width=24,
                              command=lambda idx=i: self._go_step(idx))
            btn.pack(fill="x", padx=4, pady=1)
            self._step_btns.append(btn)

        ttk.Separator(self._sidebar, orient="horizontal").pack(
            fill="x", padx=8, pady=10)
        sidebar_btn(self._sidebar, "  🏠  Dashboard",
                    command=self._show_dashboard).pack(fill="x", padx=4, pady=1)
        sidebar_btn(self._sidebar, "  ✅  Validate  F9",
                    command=self._validate).pack(fill="x", padx=4, pady=1)
        sidebar_btn(self._sidebar, "  ▶  Generate FS  F5",
                    command=self._generate_fs).pack(fill="x", padx=4, pady=1)
        sidebar_btn(self._sidebar, "  📤  Export  F12",
                    command=self._export).pack(fill="x", padx=4, pady=1)

        # Status bar at bottom
        self._status_var = tk.StringVar(value="Welcome to FinStruct")
        status_bar = tk.Frame(self._root, bg=T["border"], height=24)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar, textvariable=self._status_var,
                 bg=T["border"], fg=T["text_sec"],
                 font=(T["font"], 8), anchor="w").pack(side="left", padx=8)

        # Content area
        self._content = tk.Frame(body, bg=T["bg"])
        self._content.pack(side="left", fill="both", expand=True)

    # ── Content Switcher ─────────────────────────────────────────────────
    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _show_dashboard(self):
        self._clear_content()
        self._highlight_step(-1)
        dash = Dashboard(self._content, self._sdb,
                         on_open_project=self._open_db)
        dash.pack(fill="both", expand=True)
        self._status_var.set("Dashboard")

    def _go_step(self, idx: int):
        if self._db is None:
            messagebox.showinfo("Open Project", "Please open or create a project first.")
            return
        self._highlight_step(idx)
        steps = [
            self._show_entity,
            self._show_tb_import,
            self._show_mapping,
            self._show_wtb,
            self._show_ppe,
            self._show_annexures,
            self._show_fs,
            self._go_notes,
            self._show_reports,
            self._export,
        ]
        if idx < len(steps):
            steps[idx]()

    def _highlight_step(self, idx: int):
        for i, btn in enumerate(self._step_btns):
            btn.configure(
                bg=T["primary_light"] if i == idx else T["bg"],
                fg=T["primary"]       if i == idx else T["text"],
                font=(T["font"], T["font_size"], "bold" if i == idx else "normal")
            )

    # ── Project Management ────────────────────────────────────────────────
    def _open_db(self, path: Path):
        if self._db:
            self._db.close()
        self._db = ProjectDB(path)
        self._db.connect()
        name = self._db.get_entity("entity_name") or path.stem
        fy   = self._db.get_meta("financial_year") or ""
        etype= self._db.get_meta("entity_type") or ""
        self._project_label.configure(text=f"  {name}  |  {etype}")
        self._fy_label.configure(text=f"FY {fy}  ")
        self._sdb.add_recent(str(path), name, etype, fy)
        self._status_var.set(f"Opened: {path.name}")
        self._show_entity()

    def _new_project(self):
        self._show_dashboard()
        # Dashboard opens New Project dialog via its own button

    def _open_project(self):
        from tkinter import filedialog
        from config import PROJECTS_DIR
        path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("FinStruct Project","*.finstruct"),("All","*.*")],
            initialdir=str(PROJECTS_DIR))
        if path:
            self._open_db(Path(path))

    def _rollover(self):
        if not self._db:
            messagebox.showinfo("No Project", "Open a project first."); return
        from tkinter.simpledialog import askstring
        fy = self._db.get_meta("financial_year") or "2024-25"
        
        # Handle YYYY-YY or YYYY formats
        if "-" in fy:
            parts = fy.split("-")
            try:
                new_start = int(parts[0]) + 1
                new_fy_default = f"{new_start}-{str(new_start+1)[-2:]}"
            except ValueError:
                new_fy_default = fy
        else:
            try:
                new_fy_default = str(int(fy) + 1)
            except ValueError:
                new_fy_default = fy
                
        new_fy = askstring("Rollover", f"New Financial Year:", initialvalue=new_fy_default)
        if not new_fy:
            return
        from core.rollover import rollover_project
        from config import PROJECTS_DIR
        old_path = self._db.path
        name = self._db.get_entity("entity_name") or old_path.stem.split("_")[0]
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()
        new_path = old_path.parent.parent / f"{safe}_{new_fy}" / f"{safe}_{new_fy}.finstruct"
        try:
            rollover_project(old_path, new_path, new_fy, self._sdb)
            messagebox.showinfo("Rollover", f"✅ New project created for FY {new_fy}.\nOpening now …")
            self._open_db(new_path)
        except FileExistsError:
            messagebox.showerror("Exists", f"Project for FY {new_fy} already exists.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _lock_project(self):
        if not self._db: return
        if messagebox.askyesno("Lock", "Lock and finalize this project? No further edits allowed."):
            self._db.set_meta("is_locked", "1")
            self._db.set_meta("is_finalized", "1")
            self._db.log("PROJECT_FINALIZED", "")
            messagebox.showinfo("Locked", "Project finalized and locked.")

    def _show_audit(self):
        if not self._db: return
        rows = self._db.get_audit_log()
        dlg = tk.Toplevel(self._root)
        dlg.title("Audit Log")
        dlg.geometry("700x400")
        tree = ttk.Treeview(dlg, columns=("ts","action","detail"), show="headings")
        tree.heading("ts",     text="Timestamp")
        tree.heading("action", text="Action")
        tree.heading("detail", text="Detail")
        tree.column("ts", width=150); tree.column("action", width=200); tree.column("detail", width=320)
        for r in rows:
            tree.insert("", "end", values=(r["ts"], r["action"], r["detail"] or ""))
        vsb = ttk.Scrollbar(dlg, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=8, pady=8)

    # ── Step Views ────────────────────────────────────────────────────────
    def _show_entity(self):
        self._clear_content()
        self._highlight_step(0)
        from gui.company_master import CompanyMasterForm
        f = CompanyMasterForm(self._content, self._db,
                              on_save=lambda _: self._status_var.set("Entity master saved."))
        f.pack(fill="both", expand=True)

    def _show_tb_import(self):
        self._clear_content()
        self._highlight_step(1)
        from gui.tb_import_view import TBImportView
        f = TBImportView(self._content, self._db,
                         on_complete=lambda: self._go_step(2))
        f.pack(fill="both", expand=True)

    def _show_mapping(self):
        self._clear_content()
        self._highlight_step(2)
        from gui.mapping_view import MappingView
        et = self._db.get_meta("entity_type") or "COMPANY"
        f  = MappingView(self._content, self._db, self._sdb, et,
                         on_complete=lambda: self._go_step(3))
        f.pack(fill="both", expand=True)

    def _show_wtb(self):
        self._clear_content()
        self._highlight_step(3)
        from gui.wtb_view import WTBView
        f = WTBView(self._content, self._db,
                    on_proceed=lambda: self._go_step(4))
        f.pack(fill="both", expand=True)

    def _show_ppe(self):
        self._clear_content()
        self._highlight_step(4)
        from gui.ppe_view import PPEView
        f = PPEView(self._content, self._db,
                    on_dep_posted=lambda _: self._status_var.set("Depreciation posted."))
        f.pack(fill="both", expand=True)

    def _show_annexures(self):
        self._clear_content()
        self._highlight_step(5)
        from gui.annexures_view import AnnexuresView
        f = AnnexuresView(self._content, self._db, self._sdb)
        f.pack(fill="both", expand=True)
        self._status_var.set("Custom Annexures — fill buckets, tie out to TB.")

    def _show_fs(self):
        self._clear_content()
        self._highlight_step(6)
        try:
            doc, engine, _ = self._build_fs_doc()
        except Exception as e:
            messagebox.showerror("FS Error", str(e)); return

        et = self._db.get_meta("entity_type") or "COMPANY"
        small = False
        if et == "COMPANY":
            try:
                from core.validator import is_small_company
                em = self._db.get_all_entity()
                paid_up = float(em.get("paid_up_capital") or 0)
                turnover = float(em.get("turnover") or 0)
                small = is_small_company(paid_up, turnover)
            except Exception:
                pass

        def _rebuild_cf(include: bool):
            return engine.generate(include_cf=include).cf

        from gui.fs_viewer import FSViewer
        f = FSViewer(self._content, doc, self._db,
                     on_proceed=lambda: self._go_notes(),
                     rebuild_cf=_rebuild_cf,
                     is_small_company=small)
        f.pack(fill="both", expand=True)
        self._status_var.set("Financial Statements generated.")

    def _build_fs_doc(self):
        from core.fs_engine import FSEngine
        from core.wtb_engine import aggregate_by_code, build_wtb_lines, apply_adjustments
        from core.master_db import get_lookup_map
        wtb_rows = self._db.get_wtb()
        raw_rows = self._db.get_raw_tb()
        lines    = build_wtb_lines(wtb_rows, raw_rows)
        totals   = aggregate_by_code(lines)
        adj_rows = self._db.get_adjustments()
        if adj_rows:
            totals = apply_adjustments(totals, adj_rows, get_lookup_map())
        em     = self._db.get_all_entity()
        fy     = self._db.get_meta("financial_year") or ""
        et     = self._db.get_meta("entity_type") or "COMPANY"
        div    = int(self._db.get_meta("rounding_divisor") or "1")
        engine = FSEngine(et, totals, em, fy, div)
        return engine.generate(), engine, totals

    def _go_notes(self):
        self._clear_content()
        self._highlight_step(7)
        from gui.notes_view import NotesView
        from core.ppe_engine import recalc_asset
        try:
            doc, _, totals = self._build_fs_doc()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        ppe_data = [dict(r) for r in self._db.get_ppe()]
        for a in ppe_data:
            a.update(recalc_asset(a))
        et  = self._db.get_meta("entity_type") or "COMPANY"
        div = int(self._db.get_meta("rounding_divisor") or "1")
        em  = self._db.get_all_entity()
        from core.notes_engine import NotesEngine
        ne    = NotesEngine(totals, et, ppe_data, div, em)
        notes, _ = ne.generate_dynamic(doc)
        f = NotesView(self._content, notes, self._db)
        f.pack(fill="both", expand=True)
        self._status_var.set(f"Notes generated ({len(notes)} notes, auto-numbered).")

    def _show_reports(self):
        self._clear_content()
        self._highlight_step(8)
        et = (self._db.get_meta("entity_type") or "COMPANY").upper()

        # Determine which report tabs to show
        show_directors = (et in ("COMPANY", "SEC8"))
        show_audit = False
        if et in ("COMPANY", "SEC8"):
            show_audit = True
        elif et == "LLP":
            try:
                em = self._db.get_all_entity()
                turnover = float(em.get("turnover") or 0)
                if turnover > 4_000_000:
                    show_audit = True
            except (ValueError, TypeError):
                pass

        if not (show_directors or show_audit):
            from tkinter import messagebox
            ttk.Label(self._content,
                      text=f"Reports not applicable for entity type: {et}",
                      style="Muted.TLabel").pack(padx=12, pady=24)
            self._report_texts = {}
            return

        nb = ttk.Notebook(self._content)
        nb.pack(fill="both", expand=True)
        from gui.report_editor import ReportEditor
        self._report_texts = {}
        if show_directors:
            dr = ReportEditor(nb, self._db, "directors")
            nb.add(dr, text="Directors' Report")
            self._report_texts["directors_editor"] = dr
        if show_audit:
            ar = ReportEditor(nb, self._db, "audit")
            nb.add(ar, text="Independent Auditor's Report")
            self._report_texts["audit_editor"] = ar

    def _validate(self):
        if not self._db:
            messagebox.showinfo("No Project", "Open a project first."); return
        from core.validator import validate_mapping_complete, validate_balance
        from core.wtb_engine import aggregate_by_code, build_wtb_lines
        wtb_rows = self._db.get_wtb()
        raw_rows = self._db.get_raw_tb()
        lines    = build_wtb_lines(wtb_rows, raw_rows)
        r1 = validate_mapping_complete(list(self._db.get_wtb()))
        totals = aggregate_by_code(lines)
        et = self._db.get_meta("entity_type") or "COMPANY"
        r2 = validate_balance(totals, et)
        errors   = r1.errors + r2.errors
        warnings = r1.warnings + r2.warnings
        if errors:
            messagebox.showerror("Validation Failed",
                                 "Errors:\n" + "\n".join(errors) +
                                 ("\n\nWarnings:\n" + "\n".join(warnings) if warnings else ""))
        elif warnings:
            messagebox.showwarning("Validation Passed with Warnings",
                                   "\n".join(warnings))
        else:
            messagebox.showinfo("✅ Validation Passed",
                                "Balance Sheet balances.\nAll ledgers mapped.")
        self._status_var.set("Validation complete.")

    def _generate_fs(self):
        if not self._db:
            messagebox.showinfo("No Project", "Open a project first."); return
        self._show_fs()

    def _export(self):
        if not self._db:
            messagebox.showinfo("No Project", "Open a project first."); return
        rtexts = {}
        if self._report_texts:
            de = self._report_texts.get("directors_editor")
            ae = self._report_texts.get("audit_editor")
            if de: rtexts["directors"] = de.get_text()
            if ae: rtexts["audit"]     = ae.get_text()
        from gui.export_dialog import ExportDialog
        ExportDialog(self._root, self._db, rtexts)

    def _show_ai_settings(self):
        from gui.ai_settings_dialog import AISettingsDialog
        AISettingsDialog(self._root, self._sdb)

    def _about(self):
        messagebox.showinfo(f"About {APP_NAME}",
                            f"{APP_NAME} v{APP_VERSION}\n\n"
                            "Financial Statement Automation\n"
                            "for CA / CS Practice\n\n"
                            "Supports: Companies Act 2013, LLP,\n"
                            "Prop, Part, AOP, Trust, Section 8\n\n"
                            "ICAI Notified Formats\n"
                            "© 2026 rajacacs")

    def _on_exit(self):
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass
        self._root.quit()

    # ── Keyboard Shortcuts ────────────────────────────────────────────────
    def _bind_global_shortcuts(self):
        root = self._root
        root.bind("<Control-n>",  lambda e: self._new_project())
        root.bind("<Control-o>",  lambda e: self._open_project())
        root.bind("<Control-s>",  lambda e: self._status_var.set("Auto-saved."))
        root.bind("<F1>",         lambda e: self._about())
        root.bind("<F5>",         lambda e: self._generate_fs())
        root.bind("<F9>",         lambda e: self._validate())
        root.bind("<F10>",        lambda e: self._go_notes())
        root.bind("<F12>",        lambda e: self._export())
        root.bind("<Alt-b>",      lambda e: self._go_step(6))   # Generate FS
        root.bind("<Alt-n>",      lambda e: self._go_step(7))   # Notes
        root.bind("<Alt-m>",      lambda e: self._go_step(2))   # Mapping
        root.bind("<Alt-w>",      lambda e: self._go_step(3))   # WTB review
        root.bind("<Alt-e>",      lambda e: self._export())
        root.bind("<Alt-a>",      lambda e: self._go_step(5))   # Annexures
