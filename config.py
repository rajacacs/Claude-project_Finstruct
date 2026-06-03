"""FinStruct — Application-level constants and paths."""

import os
from pathlib import Path

APP_NAME    = "FinStruct"
APP_VERSION = "1.0.0"

APPDATA     = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
APP_DIR     = APPDATA / APP_NAME
MODELS_DIR  = APP_DIR / "models"
SETTINGS_DB = APP_DIR / "settings.db"

PROJECTS_DIR = Path.home() / "Documents" / APP_NAME / "Projects"

APP_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

SBERT_MODEL = "all-MiniLM-L6-v2"

ROUNDING_OPTIONS = {
    "Rupees (₹)":     1,
    "Thousands":   1_000,
    "Lakhs":     100_000,
    "Crores":  10_000_000,
}

THEME = {
    "primary":       "#0078D4",
    "primary_dark":  "#106EBE",
    "primary_light": "#C7E0F4",
    "bg":            "#F3F2F1",
    "bg_white":      "#FFFFFF",
    "bg_alt":        "#EFF6FC",
    "text":          "#201F1E",
    "text_sec":      "#605E5C",
    "border":        "#EDEBE9",
    "success":       "#107C10",
    "warning":       "#D83B01",
    "error":         "#A4262C",
    "header_bg":     "#0078D4",
    "header_fg":     "#FFFFFF",
    "total_bg":      "#106EBE",
    "total_fg":      "#FFFFFF",
    "section_bg":    "#C7E0F4",
    "section_fg":    "#003087",
    "subtotal_bg":   "#EFF6FC",
    "font":          "Segoe UI",
    "font_size":     10,
    "font_head":     11,
    "font_title":    13,
}

PPE_CATEGORIES = [
    "Buildings", "Plant & Machinery", "Furniture & Fixtures",
    "Vehicles", "Office Equipment", "Computers & Peripherals",
    "Electrical Installations", "Leasehold Improvements",
    "Intangible – Software", "Intangible – Goodwill",
    "Capital Work-in-Progress", "Others",
]

PPE_USEFUL_LIFE = {
    "Buildings": 60, "Plant & Machinery": 15, "Furniture & Fixtures": 10,
    "Vehicles": 8, "Office Equipment": 5, "Computers & Peripherals": 3,
    "Electrical Installations": 10, "Leasehold Improvements": 10,
    "Intangible – Software": 3, "Intangible – Goodwill": 10, "Others": 5,
    "Capital Work-in-Progress": 0,
}

PPE_IT_RATES = {
    "Buildings": 10, "Plant & Machinery": 15, "Furniture & Fixtures": 10,
    "Vehicles": 15, "Office Equipment": 15, "Computers & Peripherals": 40,
    "Electrical Installations": 10, "Intangible – Software": 40,
}
