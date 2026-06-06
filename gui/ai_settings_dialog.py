"""AI Settings Dialog — Configure LLM providers and API keys."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME as T
from gui.theme import primary_btn, secondary_btn, label

class AISettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings_db):
        super().__init__(parent)
        self._sdb = settings_db
        self.title("AI Assistance Settings")
        self.geometry("500x400")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=T["bg"])
        self._build()

    def _build(self):
        ttk.Label(self, text="Configure AI Assistance",
                  style="Sec.TLabel").pack(padx=16, pady=(16, 6), anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=4)

        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        # Provider selection
        ttk.Label(container, text="Preferred AI Provider:").grid(row=0, column=0, sticky="w", pady=8)
        self._provider_var = tk.StringVar(value=self._sdb.get_ai_provider())
        provider_cb = ttk.Combobox(container, textvariable=self._provider_var,
                                   values=["Claude", "OpenAI", "Gemini"],
                                   state="readonly", width=20)
        provider_cb.grid(row=0, column=1, sticky="w", padx=10, pady=8)
        provider_cb.bind("<<ComboboxSelected>>", self._on_provider_change)

        # API Keys
        self._keys_frame = ttk.LabelFrame(container, text="API Keys (Stored Encrypted)", padding=10)
        self._keys_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=15)
        
        self._claude_var = tk.StringVar(value=self._sdb.get_api_key("Claude"))
        self._openai_var = tk.StringVar(value=self._sdb.get_api_key("OpenAI"))
        self._gemini_var = tk.StringVar(value=self._sdb.get_api_key("Gemini"))

        self._add_key_row(0, "Claude (Anthropic):", self._claude_var)
        self._add_key_row(1, "OpenAI (GPT-4o):", self._openai_var)
        self._add_key_row(2, "Gemini (Google):", self._gemini_var)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        primary_btn(btn_frame, "Save Settings", command=self._save).pack(side="left", padx=10)
        secondary_btn(btn_frame, "Cancel", command=self.destroy).pack(side="left")

    def _add_key_row(self, row, lbl, var):
        ttk.Label(self._keys_frame, text=lbl).grid(row=row, column=0, sticky="w", pady=4)
        ent = ttk.Entry(self._keys_frame, textvariable=var, width=30, show="*")
        ent.grid(row=row, column=1, sticky="w", padx=10, pady=4)

    def _on_provider_change(self, event):
        pass

    def _save(self):
        provider = self._provider_var.get()
        self._sdb.set_ai_provider(provider)
        self._sdb.set_api_key(self._claude_var.get(), "Claude")
        self._sdb.set_api_key(self._openai_var.get(), "OpenAI")
        self._sdb.set_api_key(self._gemini_var.get(), "Gemini")
        
        messagebox.showinfo("Settings Saved", 
                            f"AI settings updated. Preferred provider set to {provider}.")
        self.destroy()
