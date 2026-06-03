"""Spreadsheet-style editable grid for Financial Statements and Mapping."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable
from ..config import THEME as T


class EditableGrid(ttk.Frame):
    """
    Treeview-based editable grid.
    Columns: list of (id, header, width, anchor).
    on_cell_change(row_iid, col_id, new_value) called on edit commit.
    """

    def __init__(self, parent, columns: list[tuple], on_cell_change: Callable | None = None,
                 editable_cols: set | None = None, **kw):
        super().__init__(parent, **kw)
        self._on_change  = on_cell_change
        self._edit_cols  = editable_cols or set()
        self._edit_entry: tk.Entry | None = None
        self._edit_iid   = None
        self._edit_col   = None

        self._build(columns)
        self._bind_shortcuts()

    def _build(self, columns):
        col_ids = [c[0] for c in columns]
        self._tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                  selectmode="extended")

        vsb = ttk.Scrollbar(self, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal",  command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        for cid, hdr, width, anchor in columns:
            self._tree.heading(cid, text=hdr,
                               command=lambda c=cid: self._sort_col(c))
            self._tree.column(cid, width=width, anchor=anchor, stretch=(cid == columns[0][0]))

        # Row colour tags
        self._tree.tag_configure("section",  background=T["section_bg"],
                                 foreground=T["section_fg"], font=(T["font"], T["font_size"], "bold"))
        self._tree.tag_configure("total",    background=T["total_bg"],
                                 foreground="white", font=(T["font"], T["font_size"], "bold"))
        self._tree.tag_configure("grand",    background=T["primary"],
                                 foreground="white", font=(T["font"], T["font_size"], "bold"))
        self._tree.tag_configure("header",   background=T["primary"],
                                 foreground="white", font=(T["font"], T["font_head"], "bold"))
        self._tree.tag_configure("alt",      background=T["bg_alt"])
        self._tree.tag_configure("green",    background="#E6F4EA", foreground="#107C10")
        self._tree.tag_configure("yellow",   background="#FFF4CE", foreground="#8A5700")
        self._tree.tag_configure("red",      background="#FDE7E9", foreground="#A4262C")

        self._tree.bind("<Double-Button-1>", self._on_double_click)
        self._tree.bind("<F2>",              self._on_f2)
        self._tree.bind("<Return>",          self._on_return)
        self._tree.bind("<Escape>",          lambda e: self._cancel_edit())
        self._tree.bind("<Tab>",             self._on_tab)

    def _bind_shortcuts(self):
        self._tree.bind("<Control-Home>", lambda e: self._tree.yview_moveto(0))
        self._tree.bind("<Control-End>",  lambda e: self._tree.yview_moveto(1))
        self._tree.bind("<Control-c>",    self._copy_selection)
        self._tree.bind("<Delete>",       self._delete_selected_value)

    def load_rows(self, rows: list[dict]):
        """rows: list of {values: [...], tag: str, iid: str}"""
        self._tree.delete(*self._tree.get_children())
        for i, row in enumerate(rows):
            tag = row.get("tag", "alt" if i % 2 == 0 else "")
            iid = row.get("iid", str(i))
            values = row.get("values", [])
            self._tree.insert("", "end", iid=iid, values=values, tags=(tag,))

    def update_row(self, iid: str, values: list):
        self._tree.item(iid, values=values)

    def get_selected_iid(self) -> str | None:
        sel = self._tree.selection()
        return sel[0] if sel else None

    def get_all_rows(self) -> list[tuple]:
        return [self._tree.item(iid)["values"]
                for iid in self._tree.get_children()]

    def _col_at_x(self, event) -> str | None:
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return None
        return self._tree.identify_column(event.x)

    def _on_double_click(self, event):
        iid = self._tree.identify_row(event.y)
        col = self._col_at_x(event)
        if iid and col:
            col_id = self._tree["columns"][int(col.lstrip("#")) - 1]
            if col_id in self._edit_cols:
                self._start_edit(iid, col_id, col)

    def _on_f2(self, event):
        sel = self._tree.selection()
        if not sel:
            return
        iid = sel[0]
        cols = self._tree["columns"]
        for i, c in enumerate(cols):
            if c in self._edit_cols:
                self._start_edit(iid, c, f"#{i+1}")
                break

    def _on_return(self, event):
        if self._edit_entry:
            self._commit_edit()
        else:
            self._on_f2(event)

    def _on_tab(self, event):
        if self._edit_entry:
            self._commit_edit()

    def _start_edit(self, iid: str, col_id: str, col_num: str):
        self._cancel_edit()
        bbox = self._tree.bbox(iid, col_num)
        if not bbox:
            return
        x, y, w, h = bbox
        values = self._tree.item(iid)["values"]
        cols   = list(self._tree["columns"])
        idx    = cols.index(col_id)
        cur    = str(values[idx]) if idx < len(values) else ""

        self._edit_entry = tk.Entry(self._tree, font=(T["font"], T["font_size"]),
                                    relief="solid", bd=1,
                                    highlightthickness=1,
                                    highlightcolor=T["primary"])
        self._edit_entry.insert(0, cur)
        self._edit_entry.select_range(0, "end")
        self._edit_entry.place(x=x, y=y, width=w, height=h)
        self._edit_entry.focus_set()
        self._edit_iid = iid
        self._edit_col = col_id
        self._edit_entry.bind("<Return>",  lambda e: self._commit_edit())
        self._edit_entry.bind("<Escape>",  lambda e: self._cancel_edit())
        self._edit_entry.bind("<Tab>",     lambda e: self._commit_edit())
        self._edit_entry.bind("<FocusOut>",lambda e: self._commit_edit())

    def _commit_edit(self):
        if not self._edit_entry:
            return
        new_val = self._edit_entry.get()
        iid     = self._edit_iid
        col_id  = self._edit_col
        self._cancel_edit()

        values = list(self._tree.item(iid)["values"])
        cols   = list(self._tree["columns"])
        idx    = cols.index(col_id)
        values[idx] = new_val
        self._tree.item(iid, values=values)

        if self._on_change:
            self._on_change(iid, col_id, new_val)

    def _cancel_edit(self):
        if self._edit_entry:
            self._edit_entry.destroy()
            self._edit_entry = None
        self._edit_iid = None
        self._edit_col = None

    def _sort_col(self, col_id: str):
        items = [(self._tree.set(k, col_id), k)
                 for k in self._tree.get_children()]
        try:
            items.sort(key=lambda x: float(x[0].replace(",", "")) if x[0] else 0)
        except ValueError:
            items.sort(key=lambda x: x[0].lower())
        for idx, (_, k) in enumerate(items):
            self._tree.move(k, "", idx)

    def _copy_selection(self, event):
        sel = self._tree.selection()
        if not sel:
            return
        lines = []
        for iid in sel:
            vals = self._tree.item(iid)["values"]
            lines.append("\t".join(str(v) for v in vals))
        self._tree.clipboard_clear()
        self._tree.clipboard_append("\n".join(lines))

    def _delete_selected_value(self, event):
        sel = self._tree.selection()
        if not sel:
            return
        for iid in sel:
            cols = list(self._tree["columns"])
            for c in cols:
                if c in self._edit_cols:
                    values = list(self._tree.item(iid)["values"])
                    idx = cols.index(c)
                    values[idx] = ""
                    self._tree.item(iid, values=values)

    @property
    def tree(self) -> ttk.Treeview:
        return self._tree
