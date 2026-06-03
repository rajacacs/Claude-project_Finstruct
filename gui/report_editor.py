"""Word-processor style editor for Directors Report and Audit Report."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from ..config import THEME as T
from ..gui.theme import primary_btn, secondary_btn, label
from ..export.docx_exporter import (
    DIRECTORS_REPORT_TEMPLATE, AUDIT_REPORT_TEMPLATE, _fill
)


class ReportEditor(ttk.Frame):
    def __init__(self, parent, db, report_type: str = "directors"):
        super().__init__(parent)
        self._db   = db
        self._type = report_type  # "directors" or "audit"
        self._build()
        self._load_template()

    def _build(self):
        # Toolbar
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=4)
        title_text = ("8a.  Directors' Report" if self._type == "directors"
                      else "8b.  Independent Auditor's Report")
        label(bar, title_text, style="Sec.TLabel").pack(side="left")
        primary_btn(bar, "Load Template", command=self._load_template).pack(side="left", padx=8)
        secondary_btn(bar, "💾 Save Text", command=self._save).pack(side="left", padx=4)
        secondary_btn(bar, "↺ Reset to Template", command=self._reset).pack(side="left", padx=4)

        # Audit Report — opinion type dropdown
        if self._type == "audit":
            ttk.Label(bar, text="Opinion:").pack(side="left", padx=(16, 4))
            self._opinion_var = tk.StringVar(
                value=self._db.get_entity("opinion_type") or "Unmodified")
            opinion_cb = ttk.Combobox(
                bar, textvariable=self._opinion_var,
                values=["Unmodified", "Qualified", "Adverse", "Disclaimer"],
                state="readonly", width=12,
            )
            opinion_cb.pack(side="left", padx=4)
            opinion_cb.bind("<<ComboboxSelected>>", self._on_opinion_change)

        # Formatting toolbar
        fmt = ttk.Frame(self)
        fmt.pack(fill="x", padx=6, pady=2)
        tk.Button(fmt, text="B", font=(T["font"], 10, "bold"),
                  command=self._bold, relief="flat",
                  bg=T["bg"], cursor="hand2", padx=6).pack(side="left")
        tk.Button(fmt, text="I", font=(T["font"], 10, "italic"),
                  command=self._italic, relief="flat",
                  bg=T["bg"], cursor="hand2", padx=6).pack(side="left")
        ttk.Separator(fmt, orient="vertical").pack(side="left", fill="y", padx=4)
        for sz in (9, 10, 11, 12):
            tk.Button(fmt, text=str(sz), font=(T["font"], 9),
                      command=lambda s=sz: self._set_size(s),
                      relief="flat", bg=T["bg"], cursor="hand2", padx=4).pack(side="left")
        ttk.Separator(fmt, orient="vertical").pack(side="left", fill="y", padx=4)
        tk.Button(fmt, text="Find (Ctrl+F)", font=(T["font"], 9),
                  command=self._find, relief="flat", bg=T["bg"], cursor="hand2",
                  padx=6).pack(side="left")

        # Text editor + scrollbar
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=6, pady=4)
        vsb = ttk.Scrollbar(container, orient="vertical")
        self._text = tk.Text(
            container, wrap="word", undo=True,
            font=(T["font"], T["font_size"]),
            bg=T["bg_white"], fg=T["text"],
            insertbackground=T["primary"],
            selectbackground=T["primary_light"],
            relief="flat", bd=1,
            yscrollcommand=vsb.set,
            padx=12, pady=8,
        )
        vsb.config(command=self._text.yview)
        vsb.pack(side="right", fill="y")
        self._text.pack(side="left", fill="both", expand=True)

        # Configure text tags
        self._text.tag_configure("bold",   font=(T["font"], T["font_size"], "bold"))
        self._text.tag_configure("italic", font=(T["font"], T["font_size"], "italic"))
        self._text.tag_configure("h1",     font=(T["font"], 13, "bold"),
                                 foreground=T["primary"], spacing1=8, spacing3=4)
        self._text.tag_configure("h2",     font=(T["font"], 11, "bold"),
                                 foreground=T["primary_dark"], spacing1=6, spacing3=2)

        # Keyboard shortcuts
        self._text.bind("<Control-b>", lambda e: self._bold())
        self._text.bind("<Control-i>", lambda e: self._italic())
        self._text.bind("<Control-f>", lambda e: self._find())

        # Status
        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var,
                  style="Muted.TLabel").pack(fill="x", padx=6, pady=2)

    def _load_template(self):
        em = self._db.get_all_entity()
        if self._type == "directors":
            key = "directors_report_text"
            tpl = DIRECTORS_REPORT_TEMPLATE
        else:
            key = "audit_report_text"
            tpl = AUDIT_REPORT_TEMPLATE

        saved = self._db.get_entity(key)
        text  = saved if saved else _fill(tpl, em)
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)
        self._status_var.set("Template loaded — edit and save.")

    def _reset(self):
        em  = self._db.get_all_entity()
        tpl = (DIRECTORS_REPORT_TEMPLATE if self._type == "directors"
               else AUDIT_REPORT_TEMPLATE)
        text = _fill(tpl, em)
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)

    def _save(self):
        key  = ("directors_report_text" if self._type == "directors"
                else "audit_report_text")
        text = self._text.get("1.0", "end").rstrip()
        self._db.set_entity(key, text)
        self._status_var.set("✅ Report text saved.")

    def _bold(self):
        try:
            self._text.tag_add("bold", "sel.first", "sel.last")
        except tk.TclError:
            pass

    def _italic(self):
        try:
            self._text.tag_add("italic", "sel.first", "sel.last")
        except tk.TclError:
            pass

    def _set_size(self, sz: int):
        tag = f"sz{sz}"
        self._text.tag_configure(tag, font=(T["font"], sz))
        try:
            self._text.tag_add(tag, "sel.first", "sel.last")
        except tk.TclError:
            pass

    def _find(self):
        dlg = tk.Toplevel(self)
        dlg.title("Find")
        dlg.geometry("350x80")
        dlg.resizable(False, False)
        dlg.grab_set()
        var = tk.StringVar()
        ttk.Entry(dlg, textvariable=var, width=30).pack(side="left", padx=8, pady=20)
        def do_find():
            term = var.get()
            if not term:
                return
            start = self._text.search(term, "1.0", stopindex="end")
            if start:
                end = f"{start}+{len(term)}c"
                self._text.tag_remove("sel", "1.0", "end")
                self._text.tag_add("sel", start, end)
                self._text.see(start)
        ttk.Button(dlg, text="Find", command=do_find).pack(side="left", padx=4)

    def _on_opinion_change(self, *_):
        opinion = self._opinion_var.get()
        self._db.set_entity("opinion_type", opinion)
        # Reload template to reflect new opinion paragraph
        if messagebox.askyesno(
                "Reload Template?",
                f"Opinion set to '{opinion}'.\nReload audit report template with this opinion?"):
            self._reset()

    def get_text(self) -> str:
        return self._text.get("1.0", "end").rstrip()
