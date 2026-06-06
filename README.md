# FinStruct

Financial Statement Automation for CA / CS Practice — local-first desktop app built with Python + Tkinter.

---

## What It Does

FinStruct takes a Trial Balance, maps ledgers to Schedule III / ICAI NCE line items, and generates print-ready financial statements for seven entity types: **Company, LLP, Proprietary, Partnership, AOP, Trust, Section 8**.

### Workflow
1. **Entity Setup** — register entity name, type, financial year
2. **Import TB** — paste or import Trial Balance from CSV / XLSX (with auto-template detection)
3. **Map Ledgers** — AI-assisted mapping (Claude, OpenAI, or Gemini) to Schedule III codes
4. **Review WTB** — confirm / override the working trial balance
5. **PPE Register** — compute depreciation (SLM / WDV) and IT WDV
6. **Generate FS** — one-click Balance Sheet + P&L
7. **Notes** — auto-populated Notes to Accounts (1–29) with pagination support
8. **Reports** — Directors' Report and Audit Report editors
9. **Export** — PDF, DOCX, or XLSX output

---

## Quick Start

### Prerequisites
- Python 3.10 or later — <https://www.python.org/downloads/>
- On Windows: tick **"Add Python to PATH"** during installation

### Install

```cmd
git clone https://github.com/rajacacs/Claude-project_Finstruct.git
cd Claude-project_Finstruct

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### Run

```cmd
python finstruct_app.py
```

---

## Building a Standalone .exe (Windows)

```cmd
pip install pyinstaller
pyinstaller finstruct.spec
```

Output: `dist\FinStruct\FinStruct.exe`

Copy the entire `dist\FinStruct\` folder to any Windows PC — no Python required.
Log file (windowed .exe): `%APPDATA%\FinStruct\app.log`

---

## Project Structure

```
Claude-project_Finstruct/
├── finstruct_app.py            Entry point
├── finstruct.spec              PyInstaller build spec
├── config.py                   App constants, paths, theme tokens
├── requirements.txt            Python dependencies
├── core/
│   ├── master_db.py            Schedule III + NCE mapping master
│   ├── entity_types.py         Entity type enums / labels
│   ├── fs_engine.py            FS generation engine
│   ├── wtb_engine.py           Working TB aggregation
│   ├── ppe_engine.py           Depreciation calculator (SLM/WDV)
│   ├── notes_engine.py         Notes to Accounts generator
│   ├── mapper.py               AI-assisted ledger mapper
│   ├── tb_importer.py          CSV / XLSX TB importer
│   ├── tb_template_generator.py TB XLSX template generator
│   ├── validator.py            TB validation rules
│   ├── ai_service.py           Multi-provider AI abstraction (Claude/OpenAI/Gemini)
│   └── rollover.py             Smart FY rollover (carries master details)
├── data/
│   ├── project_db.py           Per-project SQLite DB (encrypted PII)
│   ├── settings_db.py          Global settings DB (recent projects)
│   └── encryption.py           Fernet AES-128 for PII fields
├── export/
│   ├── pdf_exporter.py         ReportLab PDF output
│   ├── docx_exporter.py        python-docx Word output
│   └── xlsx_exporter.py        openpyxl Excel output
└── gui/
    ├── theme.py                Design tokens + custom widget factories (Ticks/Wrap)
    ├── main_window.py          Root window, sidebar, menu
    ├── dashboard.py            Dashboard (Wrapped list + Disk deletion)
    ├── company_master.py       Step 1: Entity Setup
    ├── tb_import_view.py       Step 2: TB import
    ├── mapping_view.py         Step 3: Ledger mapping
    ├── wtb_view.py             Step 4: WTB review
    ├── ppe_view.py             Step 5: PPE register
    ├── fs_viewer.py            Step 6: FS viewer
    ├── notes_view.py           Step 7: Notes editor (Paginated)
    ├── report_editor.py        Step 8: Report editor
    ├── export_dialog.py        Step 9: Export dialog
    ├── ai_settings_dialog.py   AI provider & API key configuration
    └── zoho_connect_dialog.py  Zoho Books integration (beta)
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `cryptography` | Fernet AES-128 encryption for PII fields |
| `keyring` | Stores encryption key in OS credential store |
| `openpyxl` | Read/write .xlsx Trial Balance and exports |
| `reportlab` | PDF financial statement generation |
| `python-docx` | Word document export |
| `lxml` | XML processing (docx internals) |
| `scikit-learn` | Fallback cosine-similarity ledger mapper |
| `sentence-transformers` | AI-assisted ledger mapping (optional) |
| `anthropic` | Claude API integration (optional) |
| `openai` | OpenAI GPT-4o integration (optional) |
| `google-generativeai` | Gemini 1.5 Pro/Flash integration (optional) |

`tkinter` and `sqlite3` ship with Python — no extra install needed.

---

## Data & Security

- Project data stored in `.finstruct` SQLite files (one file per client / FY)
- PII fields (PAN, DIN, addresses, director names) encrypted with Fernet AES-128
- Encryption key stored in Windows Credential Manager / macOS Keychain (file fallback)
- No network calls except optional AI APIs (user-configured and encrypted)

---

*FinStruct v2.0 · ICAI Notified Formats · Companies Act 2013 · © 2026 rajacacs*
