"""Zoho Books integration placeholder — OAuth2 flow deferred pending API credentials."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox


class ZohoConnectDialog(tk.Toplevel):
    """Modal dialog to configure Zoho Books connection (placeholder)."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.title("Connect Zoho Books")
        self.resizable(False, False)
        self.grab_set()
        self._db = db
        self._build()
        self.geometry("480x320")

    def _build(self):
        ttk.Label(self, text="Zoho Books Integration",
                  font=(None, 13, "bold")).pack(pady=(16, 4))
        ttk.Label(self,
                  text="Connect your Zoho Books account to import the Trial Balance directly.",
                  wraplength=430).pack(pady=(0, 8))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=8)

        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=20, pady=4)

        fields = [
            ("zoho_client_id",     "Client ID"),
            ("zoho_client_secret", "Client Secret"),
            ("zoho_org_id",        "Organisation ID"),
        ]
        self._vars: dict[str, tk.StringVar] = {}
        for key, lbl in fields:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=lbl, width=18, anchor="w").pack(side="left")
            v = tk.StringVar(value=self._db.get_meta(key) or "")
            self._vars[key] = v
            ttk.Entry(row, textvariable=v, width=34,
                      show="*" if "secret" in key else "").pack(side="left", padx=4)

        ttk.Label(self,
                  text="Zoho Books API integration is coming soon.\n"
                       "Save your credentials now — they will be used when the feature launches.",
                  wraplength=430, foreground="#605E5C", font=(None, 9)).pack(pady=(8, 4))

        btn = ttk.Frame(self)
        btn.pack(fill="x", padx=20, pady=8)
        ttk.Button(btn, text="Save Credentials", command=self._save).pack(side="left", padx=4)
        ttk.Button(btn, text="Test Connection (coming soon)",
                   state="disabled").pack(side="left", padx=4)
        ttk.Button(btn, text="Close", command=self.destroy).pack(side="right", padx=4)

    def _save(self):
        for key, v in self._vars.items():
            val = v.get().strip()
            if val:
                self._db.set_meta(key, val)
        messagebox.showinfo("Saved",
                            "Zoho credentials saved.\n"
                            "Import from Zoho Books will be available in a future update.")
        self.destroy()
