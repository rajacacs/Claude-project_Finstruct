"""Notes to Accounts viewer — tabbed per-note editable grids."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog
from config import THEME as T
from core.notes_engine import Note
from core.fs_engine import FSLine
from gui.theme import label, primary_btn, secondary_btn, scrolled_frame


def _fmt(v):
    if v is None or v == 0: return "-"
    return f"{float(v):,.2f}"


class NotesGrid(ttk.Frame):
    """Custom grid for Notes that supports text wrapping and auto-height."""
    def __init__(self, parent, fy_labels):
        super().__init__(parent)
        self._outer, self._canvas, self._inner = scrolled_frame(self)
        self._outer.pack(fill="both", expand=True)
        self._fy_labels = fy_labels
        self._rows_data = []  # (l_var, c_var, p_var, tag)
        self._label_widgets = []

        self._inner.columnconfigure(0, weight=1)
        self._inner.columnconfigure(1, minsize=150)
        self._inner.columnconfigure(2, minsize=150)

        # Header
        h_style = {
            "font": (T["font"], T["font_size"], "bold"),
            "background": T["header_bg"],
            "foreground": T["header_fg"],
            "padx": 10, "pady": 5
        }
        tk.Label(self._inner, text="Particulars", anchor="w", **h_style).grid(row=0, column=0, sticky="ew")
        tk.Label(self._inner, text=fy_labels[0], anchor="e", **h_style).grid(row=0, column=1, sticky="ew")
        tk.Label(self._inner, text=fy_labels[1], anchor="e", **h_style).grid(row=0, column=2, sticky="ew")

        self._inner.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        # Update wraplength for all labels based on Particulars column width
        w = self._inner.winfo_width() - 320
        if w < 100: w = 100
        for lbl in self._label_widgets:
            lbl.configure(wraplength=w)

    def load_rows(self, rows_list):
        for i, row in enumerate(rows_list):
            vals = row["values"]
            tag = row.get("tag", "")

            l_var = tk.StringVar(value=vals[0])
            c_var = tk.StringVar(value=vals[1])
            p_var = tk.StringVar(value=vals[2])

            bg = T["bg_white"]
            fg = T["text"]
            font = (T["font"], T["font_size"])

            if tag == "section":
                bg, fg, font = T["section_bg"], T["section_fg"], (T["font"], T["font_size"], "bold")
            elif tag == "total":
                bg, fg, font = T["total_bg"], "white", (T["font"], T["font_size"], "bold")
            elif tag == "grand":
                bg, fg, font = T["primary"], "white", (T["font"], T["font_size"], "bold")
            elif tag == "header":
                bg, fg, font = T["primary"], "white", (T["font"], T["font_head"], "bold")
            elif tag == "alt":
                bg = T["bg_alt"]

            # Label for particulars (wrapped)
            lbl = tk.Label(self._inner, textvariable=l_var, background=bg, foreground=fg, font=font,
                           anchor="w", justify="left", padx=10, pady=5)
            lbl.grid(row=i+1, column=0, sticky="nsew", padx=1, pady=1)
            self._label_widgets.append(lbl)

            # Double-click to edit label
            lbl.bind("<Double-Button-1>", lambda e, v=l_var: self._edit_label(v))

            # Entry for CY/PY
            c_ent = tk.Entry(self._inner, textvariable=c_var, background=bg, foreground=fg, font=font,
                             justify="right", relief="flat", width=15)
            c_ent.grid(row=i+1, column=1, sticky="nsew", padx=1, pady=1)

            p_ent = tk.Entry(self._inner, textvariable=p_var, background=bg, foreground=fg, font=font,
                             justify="right", relief="flat", width=15)
            p_ent.grid(row=i+1, column=2, sticky="nsew", padx=1, pady=1)

            self._rows_data.append((l_var, c_var, p_var, tag))

    def _edit_label(self, var):
        new_val = simpledialog.askstring("Edit Particulars", "Enter text:", initialvalue=var.get())
        if new_val is not None:
            var.set(new_val)

    def get_all_rows(self):
        return [(l.get(), c.get(), p.get()) for l, c, p, t in self._rows_data]


class NotesView(ttk.Frame):
    def __init__(self, parent, notes: list[Note], db):
        super().__init__(parent)
        self._notes = notes or []
        self._db    = db
        self._page_size = 5
        self._current_page = 0
        self._grids: dict[int, NotesGrid] = {}
        self._note_frames: list[ttk.Frame] = []
        # Derive FY labels
        self._fy_labels = self._derive_fy_labels()
        self._build()

    def _derive_fy_labels(self) -> tuple[str, str]:
        """Derive FY labels from metadata."""
        meta = self._db.get_all_meta()
        fy = meta.get("financial_year", "")
        try:
            fy_parts = fy.split("-")
            fy_start_cy = int(fy_parts[0])
            fy_end_cy = int(fy_parts[1])
            fy_start_py = fy_start_cy - 1
            fy_end_py = fy_end_cy - 1
            return (f"Rs. FY {fy_start_cy}-{fy_end_cy:02d}",
                   f"Rs. FY {fy_start_py}-{fy_end_py:02d}")
        except (IndexError, ValueError):
            return ("Rs. Current Year", "Rs. Previous Year")

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        label(top, "7.  Notes to Financial Statements", style="Sec.TLabel").pack(side="left")
        primary_btn(top, "Save All Note Edits", command=self._save_all).pack(side="right", padx=4)
        self._counter_lbl = label(top, "", style="Muted.TLabel")
        self._counter_lbl.pack(side="right", padx=20)

        # Validation: check if notes exist
        if not self._notes:
            status_frame = ttk.Frame(self)
            status_frame.pack(fill="both", expand=True, padx=16, pady=16)
            ttk.Label(status_frame,
                     text="⚠  No notes generated yet.\n\nEnsure that:\n"
                          "1. Trial Balance has been imported (Step 2)\n"
                          "2. Financial Statements are generated (Step 6)\n"
                          "3. Working TB is balanced",
                     style="Muted.TLabel", wraplength=400, justify="left").pack(anchor="w", pady=20)
            return

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=8, pady=4)

        self._prev_frame = ttk.Frame(self._nb)
        self._next_frame = ttk.Frame(self._nb)

        self._grids = {}
        self._note_frames = []
        for note in self._notes:
            frame = ttk.Frame(self._nb)
            self._build_note_tab(frame, note)
            self._note_frames.append(frame)

        self._update_tabs()

    def _update_tabs(self, select_index=None):
        """Rebuild the visible tabs based on current page."""
        self._nb.unbind("<<NotebookTabChanged>>")
        for tab in self._nb.tabs():
            self._nb.forget(tab)

        start = self._current_page * self._page_size
        end = start + self._page_size

        if self._current_page > 0:
            self._nb.add(self._prev_frame, text="« Prev")

        for i in range(start, min(end, len(self._notes))):
            self._nb.add(self._note_frames[i], text=f"Note {self._notes[i].number}")

        if end < len(self._notes):
            self._nb.add(self._next_frame, text="Next »")

        if select_index is not None:
            try:
                self._nb.select(select_index)
            except tk.TclError:
                self._nb.select(0)
        else:
            idx = 1 if self._current_page > 0 else 0
            self._nb.select(idx)

        self._update_counter()
        self._nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _update_counter(self):
        """Update the 'Note X of XX' label."""
        if not self._notes: return
        sel = self._nb.select()
        if not sel: return
        
        # Identify which note frame is selected
        sel_widget = self._nb.nametowidget(sel)
        try:
            idx = self._note_frames.index(sel_widget)
            self._counter_lbl.configure(text=f"Note {idx + 1} of {len(self._notes)}")
        except ValueError:
            # Not a note frame (likely Prev/Next nav tab)
            pass

    def _on_tab_changed(self, event):
        sel = self._nb.select()
        if not sel: return
        txt = self._nb.tab(sel, "text")
        if txt == "« Prev":
            self._current_page -= 1
            target = self._page_size if self._current_page > 0 else self._page_size - 1
            self._update_tabs(select_index=target)
        elif txt == "Next »":
            self._current_page += 1
            self._update_tabs(select_index=1)
        else:
            self._update_counter()

    def _build_note_tab(self, parent, note: Note):
        ttk.Label(parent, text=f"Note {note.number}: {note.title}",
                  style="Sec.TLabel").pack(anchor="w", padx=8, pady=4)
        grid = NotesGrid(parent, self._fy_labels)
        grid.pack(fill="both", expand=True, padx=8, pady=4)
        rows = []
        for i, ln in enumerate(note.lines):
            cy_s = _fmt(ln.cy) if ln.row_type not in ("SECTION","HEADER","BLANK","TEXT") else ""
            py_s = _fmt(ln.py) if ln.row_type not in ("SECTION","HEADER","BLANK","TEXT") else ""
            tag = {
                "TOTAL": "total", "GRAND": "grand",
                "SECTION": "section", "HEADER": "header",
                "TEXT": "alt",
            }.get(ln.row_type, "alt" if i % 2 else "")
            rows.append({
                "iid":    f"n{note.number}_{i}",
                "tag":    tag,
                "values": ["  " * ln.indent + ln.label, cy_s, py_s],
            })
        grid.load_rows(rows)
        self._grids[note.number] = grid

    def _save_all(self):
        for note in self._notes:
            grid = self._grids.get(note.number)
            if not grid:
                continue
            rows = grid.get_all_rows()
            for seq, (row, ln) in enumerate(zip(rows, note.lines)):
                try:
                    cy = float(str(row[1]).replace(",","")) if row[1] not in ("","-") else 0.0
                    py = float(str(row[2]).replace(",","")) if row[2] not in ("","-") else 0.0
                    lbl = str(row[0]).strip()
                    self._db._conn.execute("""
                        INSERT OR REPLACE INTO note_data(note_no,sequence,label,cy_value,py_value,row_type)
                        VALUES(?,?,?,?,?,?)
                    """, (note.number, seq, lbl, cy, py, ln.row_type))
                except (ValueError, IndexError):
                    pass
        self._db._conn.commit()
        from tkinter import messagebox
        messagebox.showinfo("Saved", "Notes saved successfully.")
