"""MS Office - inspired theme — design tokens + widget factories."""

import tkinter as tk
from tkinter import ttk
from config import THEME as T


def apply_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=T["bg"])

    # ── Notebook (tabs) ─────────────────────────────────────────────────
    style.configure("TNotebook", background=T["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=T["bg"], foreground=T["text"],
                    font=(T["font"], T["font_size"]), padding=[10, 4],
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", T["bg_white"])],
              foreground=[("selected", T["primary"])],
              expand=[("selected", [1, 1, 1, 0])])

    # ── Frame ────────────────────────────────────────────────────────────
    style.configure("TFrame", background=T["bg"])
    style.configure("Card.TFrame", background=T["bg_white"],
                    relief="flat", borderwidth=1)

    # ── Labels ───────────────────────────────────────────────────────────
    style.configure("TLabel", background=T["bg"], foreground=T["text"],
                    font=(T["font"], T["font_size"]))
    style.configure("Title.TLabel", background=T["bg_white"],
                    foreground=T["primary"],
                    font=(T["font"], T["font_title"], "bold"))
    style.configure("Sec.TLabel", background=T["bg_white"],
                    foreground=T["primary"],
                    font=(T["font"], T["font_head"], "bold"))
    style.configure("Muted.TLabel", background=T["bg"],
                    foreground=T["text_sec"],
                    font=(T["font"], T["font_size"]))

    # ── Buttons ──────────────────────────────────────────────────────────
    style.configure("TButton", background=T["primary"], foreground="white",
                    font=(T["font"], T["font_size"], "bold"),
                    padding=[10, 5], borderwidth=0, relief="flat")
    style.map("TButton",
              background=[("active", T["primary_dark"]),
                          ("pressed", T["primary_dark"]),
                          ("disabled", T["border"])],
              foreground=[("disabled", T["text_sec"])])

    style.configure("Secondary.TButton", background=T["bg_white"],
                    foreground=T["primary"], font=(T["font"], T["font_size"]),
                    padding=[8, 4], borderwidth=1, relief="solid")
    style.map("Secondary.TButton",
              background=[("active", T["primary_light"])],
              bordercolor=[("focus", T["primary"])])

    style.configure("Danger.TButton", background=T["error"], foreground="white",
                    font=(T["font"], T["font_size"]), padding=[8, 4])

    # ── Entry ────────────────────────────────────────────────────────────
    style.configure("TEntry", fieldbackground=T["bg_white"],
                    foreground=T["text"],
                    font=(T["font"], T["font_size"]),
                    insertcolor=T["primary"], borderwidth=1,
                    relief="solid")
    style.map("TEntry", bordercolor=[("focus", T["primary"])])

    # ── Combobox ─────────────────────────────────────────────────────────
    style.configure("TCombobox", fieldbackground=T["bg_white"],
                    foreground=T["text"],
                    font=(T["font"], T["font_size"]))

    # ── Treeview (FS grid) ───────────────────────────────────────────────
    style.configure("Treeview", background=T["bg_white"],
                    fieldbackground=T["bg_white"],
                    foreground=T["text"],
                    font=(T["font"], T["font_size"]),
                    rowheight=22, borderwidth=0)
    style.configure("Treeview.Heading", background=T["header_bg"],
                    foreground=T["header_fg"],
                    font=(T["font"], T["font_size"], "bold"),
                    relief="flat")
    style.map("Treeview",
              background=[("selected", T["primary_light"])],
              foreground=[("selected", T["primary"])])

    # Custom row tags applied at grid build time
    # "section", "total", "grand", "alt" tags → configured in FSGridView

    # ── Scrollbar ────────────────────────────────────────────────────────
    style.configure("TScrollbar", background=T["border"],
                    troughcolor=T["bg"], borderwidth=0, relief="flat")

    # ── Progressbar ──────────────────────────────────────────────────────
    style.configure("TProgressbar", background=T["primary"],
                    troughcolor=T["bg"])

    # ── Separator ────────────────────────────────────────────────────────
    style.configure("TSeparator", background=T["border"])

    # ── Checkbutton ──────────────────────────────────────────────────────
    style.configure("TCheckbutton", background=T["bg"], foreground=T["text"],
                    font=(T["font"], T["font_size"]))


def sidebar_btn(parent, text: str, command=None, width: int = 22) -> tk.Button:
    return tk.Button(parent, text=text, command=command, width=width,
                     anchor="w", pady=6, padx=10,
                     bg=T["bg"], fg=T["text"], relief="flat",
                     font=(T["font"], T["font_size"]),
                     activebackground=T["primary_light"],
                     activeforeground=T["primary"],
                     cursor="hand2", bd=0)


def primary_btn(parent, text: str, command=None, **kw) -> ttk.Button:
    b = ttk.Button(parent, text=text, command=command, **kw)
    return b


def secondary_btn(parent, text: str, command=None, **kw) -> ttk.Button:
    return ttk.Button(parent, text=text, command=command,
                      style="Secondary.TButton", **kw)


def label(parent, text: str, style: str = "TLabel", **kw) -> ttk.Label:
    return ttk.Label(parent, text=text, style=style, **kw)


def entry(parent, textvariable=None, width: int = 30, **kw) -> ttk.Entry:
    return ttk.Entry(parent, textvariable=textvariable, width=width, **kw)


def card(parent, **kw) -> ttk.Frame:
    f = ttk.Frame(parent, style="Card.TFrame", padding=10, **kw)
    return f


def separator(parent, orient="horizontal") -> ttk.Separator:
    return ttk.Separator(parent, orient=orient)


def scrolled_frame(parent):
    """Return (outer_frame, canvas, inner_frame) for a scrollable region."""
    outer = ttk.Frame(parent)
    canvas = tk.Canvas(outer, bg=T["bg"], highlightthickness=0)
    vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = ttk.Frame(canvas)
    win   = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _resize(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(win, width=canvas.winfo_width())

    inner.bind("<Configure>", _resize)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return outer, canvas, inner
