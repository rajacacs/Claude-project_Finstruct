# FinStruct User Guide

**FinStruct v2.0** — Financial Statement Automation for CA/CS Practice

This guide walks you through installation, setup, and all 9 workflow steps to generate ICAI-compliant financial statements from your trial balance in minutes.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Workflow Overview](#workflow-overview)
3. [Entity Type Selection](#entity-type-selection)
4. [9-Step Workflow Guide](#9-step-workflow-guide)
5. [Input Formats](#input-formats)
6. [Export & Output Formats](#export--output-formats)
7. [Advanced Features](#advanced-features)
8. [Best Practices for Multiple Projects](#best-practices-for-multiple-projects)
9. [FAQ & Troubleshooting](#faq--troubleshooting)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Glossary](#glossary)
12. [Detailed Walkthrough: Company Entity](#detailed-walkthrough-company-entity)

---

## Quick Start

### Installation

1. **Download & Install**
   - Download `FinStruct_v2.0_dist.zip` (45 MB)
   - Extract the `.zip` file to any location (e.g., `C:\Program Files\FinStruct`)
   - Double-click `FinStruct/FinStruct.exe` to launch

2. **System Requirements**
   - Windows 10 or later (64-bit)
   - 120 MB free disk space
   - Administrator privileges (first-run only)

3. **First Run**
   - The app creates a working directory: `C:\Users\[YourUser]\Documents\FinStruct\Projects\`
   - All your projects are stored here; you can back them up anytime

### Create Your First Project (3 Steps)

1. **File → New Project** (or `Ctrl+N`)
   - Choose entity type: **Company**, **LLP**, **Partnership**, **Proprietorship**, **AOP**, **Trust**, or **Section 8**
   - Enter financial year: e.g., `2024-25`
   - Click **Create**

2. **Step 1: Entity Setup**
   - Fill in entity name, address, contact details
   - Click **Save**

3. **Step 2: Import Trial Balance**
   - Click **Choose File** → select your TB export (XLSX, CSV, or Tally XML)
   - If column auto-detection fails, manually map columns (Ledger, Debit, Credit, Balance)
   - Click **Import**

**Done!** You're ready to proceed to Step 3 (Mapping). The app will save your project automatically.

---

## Workflow Overview

FinStruct guides you through **9 sequential steps** to generate financial statements from your trial balance:

```
┌─────────────────────────────────────────────────────────────────┐
│                      FinStruct Workflow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Entity Setup  ──→  Enter master data                   │
│  Step 2: Import TB     ──→  Load trial balance (xlsx/csv/xml)   │
│  Step 3: Map Ledgers   ──→  Classify ledgers → FS line items    │
│  Step 4: Review WTB    ──→  Confirm working TB, add adjustments |
│  Step 5: PPE Register  ──→  Calculate depreciation              │
│  Step 6: Generate FS   ──→  Generate Balance Sheet + P&L        │
│  Step 7: Notes         ──→  Auto-populate Notes to Accounts     │
│  Step 8: Reports       ──→  Edit Directors' + Audit Reports     │
│  Step 9: Export        ──→  Output PDF / Excel / Word           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Outputs by Step:**
- **Step 2:** Working Trial Balance (WTB) raw data
- **Step 4:** WTB after mapping + adjustments
- **Step 6:** Balance Sheet, P&L (or I&E for non-company entities)
- **Step 7:** 15–29 Notes to Accounts (auto-calculated & paginated)
- **Step 9:** Final PDF (filing-ready), Excel (for edits), Word (reports)

---

## Entity Type Selection

**Choose your entity type at Step 1.** Unsure? Use this decision tree:

```
Is your entity a listed / unlisted company registered under
the Companies Act, 2013?
  ├─ YES → Choose "Company" (uses Schedule III format)
  │         Generates: Balance Sheet, P&L, Cash Flow
  │
  └─ NO → Is it a Limited Liability Partnership (LLP)?
          ├─ YES → Choose "LLP" (uses ICAI notified LLP format)
          │         Generates: Balance Sheet, P&L, Partners' Capital Account
          │
          └─ NO → Is it a partnership / proprietorship / other structure?
                  ├─ Partnership (2+ owners) → "Partnership Firm"
                  │  Generates: Balance Sheet, P&L, Partners' Capital & Current A/c
                  │
                  ├─ Proprietorship (sole owner) → "Proprietorship"
                  │  Generates: Balance Sheet, Trading & P&L
                  │
                  ├─ Association/Club/RWA/AOP → "AOP"
                  │  Generates: Balance Sheet, Income & Expenditure, Receipt & Payment
                  │
                  ├─ Charitable Trust / NPO → "Trust"
                  │  Generates: Balance Sheet, Income & Expenditure, Receipt & Payment
                  │
                  └─ Section 8 Company (non-profit corp.) → "Section 8"
                     Generates: Balance Sheet, Income & Expenditure, Cash Flow
```

**Per-Entity Format Summary:**

| Entity Type | Primary Statements | Key Difference | Notes Count |
|---|---|---|---|
| **Company** | BS, P&L, CF | Schedule III (full disclosures) | 29 |
| **LLP** | BS, P&L, Partners' Cap | Separate capital accounts per partner | 13 |
| **Partnership** | BS, P&L, Partners' Cap/Current | Separate capital + current accounts | 13 |
| **Proprietorship** | BS, Trading, P&L | Single-owner format; trading a/c | 13 |
| **AOP/RWA/Club** | BS, I&E, R&P | Non-profit format; receipt & payment | 8 |
| **Trust/NPO** | BS, I&E, R&P | Trust deed fields; FCRA compliance | 8 |
| **Section 8** | BS, I&E, CF | Non-profit company; Schedule III variant | 15 |

---

## 9-Step Workflow Guide

### Step 1: Entity Setup
**What it does:** Record master data about your entity (name, registration details, contacts).

**Quick Actions:**
- [ ] Fill **Entity Name** (e.g., "ABC Limited")
- [ ] Enter **Entity Type** (selected at project creation; can change here)
- [ ] Fill **Address**, **CIN/LLPIN/PAN**, **Contact Email**
- [ ] Enter **Financial Year** (e.g., 2024-25)
- [ ] (Optional) Add director/partner names, auditor details, other metadata
- [ ] Click **Save**

**When to Proceed:** Once all mandatory fields are filled.  
**Key Tip:** You can edit this anytime. Saved data auto-persists.  
**Keyboard:** No shortcut; use mouse or Tab to navigate fields.

---

### Step 2: Import Trial Balance
**What it does:** Load your raw trial balance (ledger names + debit/credit + prior-year balances).

**Quick Actions:**
- [ ] Click **Choose File** → select TB export (XLSX, CSV, or Tally XML)
- [ ] FinStruct auto-detects columns: Ledger, Debit, Credit, Balance, Prior Year
- [ ] If auto-detect fails, **manually map columns** in the dialog
- [ ] Review imported ledgers in the grid (optional: scroll to check ledger names)
- [ ] Click **Import**
- [ ] Proceed to Step 3 (Mapping)

**Common Errors:**
- "Ledger column not found" → Manually select the Ledger column in the dialog
- Duplicate ledger names → Rename in your source file, re-import

**When to Proceed:** After confirming the ledger count matches your TB.  
**Key Tip:** FinStruct accepts XLSX (Excel), CSV (comma/tab/semicolon-delimited), or Tally XML exports.  
**Keyboard:** Ctrl+O to open recent projects anytime.

---

### Step 3: Map Ledgers
**What it does:** Classify each ledger to an ICAI Schedule III / notified format line item (e.g., "Bank Account" → "Cash & Cash Equivalents").

**Quick Actions:**
- [ ] View ledger grid: **Ledger Name | Suggested Code | Confidence | Is Confirmed**
- [ ] **Green** (≥85% confidence) = auto-confirmed; review or accept
- [ ] **Yellow** (65–84%) = review & confirm or override
- [ ] **Red** (<65%) = must manually select correct code
- [ ] For each Red/Yellow row, click the **Suggested Code** field → dropdown menu of valid codes
- [ ] Click correct code from list (filtered by entity type)
- [ ] Or type a ledger name to search codes
- [ ] Mark as **Confirmed** (checkbox)
- [ ] Repeat until all ledgers are confirmed
- [ ] Validate count: "N unmapped" should be 0
- [ ] Proceed to Step 4 (Review WTB)

**Confidence Scoring:**
- **Green (≥0.85):** Exact match or very high semantic similarity. Auto-confirmed; usually correct.
- **Yellow (0.65–0.84):** Plausible match; review to ensure correctness (e.g., "Bank" might be Cash or Short-term Investment).
- **Red (<0.65):** Low confidence. You must select the correct code manually from the dropdown.

**Common Mistakes:**
- Mapping "Bank Account" to "Trade Payables" (wrong debit/credit).
- Mapping "Provision for Tax" to "Tax Expense" (should be liability, not expense).

**When to Proceed:** When the status bar shows "All ledgers mapped" and no red/unmapped remain.  
**Key Tip:** Confirmed mappings are **learned** for future projects of the same entity type. Mapping gets faster!  
**Power User:** Click **Validate (F9)** to check if BS will balance before proceeding.

---

### Step 4: Review Working Trial Balance (WTB)
**What it does:** Review classified ledgers + add manual adjustments (if needed). The app calculates working trial balance totals.

**Quick Actions:**
- [ ] Review WTB grid: **Ledger | Code | Current Year | Prior Year**
- [ ] (Optional) Add adjustments: **Adjustments → New** (e.g., accrual entries, journal corrections)
- [ ] Fill: Ledger Name, Code, Dr/Cr Amount, Narration
- [ ] Click **Save**
- [ ] Recalculate: WTB totals update automatically
- [ ] Check balance: "BS Difference" should be ≤ ₹1 (or 0)
- [ ] If unbalanced, review for missing/duplicate ledgers
- [ ] Proceed to Step 5 (PPE)

**When to Proceed:** When BS is balanced (difference = 0) or within rounding tolerance.  
**Key Tip:** Adjustments are **not** posted to ledgers; they're temporary adjustments for FS purposes only.  
**Keyboard:** Alt+W to jump to WTB step.

---

### Step 5: PPE Register
**What it does:** Enter fixed assets and calculate depreciation (Straight-Line or Written-Down Value method).

**Quick Actions:**
- [ ] View PPE grid: **Asset Name | Category | Gross Opening | Additions | Disposals | Depreciation | NBV**
- [ ] Click **+ New Asset** → enter details:
  - Asset Name (e.g., "Office Building")
  - Category (dropdown: Buildings, Machinery, Vehicles, Computers, etc.)
  - Depreciation Method: **SLM** (Straight-Line) or **WDV** (Written-Down Value)
  - Useful Life (years): auto-populated per category; adjust if needed
  - Gross Opening, Additions, Disposals
- [ ] Click **Save**
- [ ] App auto-calculates:
  - Gross Closing = Opening + Additions − Disposals
  - Depreciation Charge (per method)
  - Net Block (Gross − Accumulated Depreciation)
- [ ] Repeat for all assets
- [ ] Totals appear at bottom (PPE Note will use these)
- [ ] Proceed to Step 6 (Generate FS)

**Depreciation Methods:**
- **SLM:** Depreciation = Gross Closing / Useful Life. Best for straight assets.
- **WDV:** Depreciation = Opening Written-Down Value × IT Rate / 100. Best for IT (computers, equipment). Half-year convention in year of purchase.

**Common Gotchas:**
- **Which method?** Follow your company's depreciation policy. If unsure, use company's prior-year FS.
- **IT Rate:** Preset per category (e.g., Computers = 40%, Vehicles = 15%). Match your IT Act schedule or company policy.

**When to Proceed:** After all PPE assets are entered and totals match your expected fixed assets.  
**Key Tip:** Leave blank if no fixed assets; skip to Step 6.  
**Keyboard:** Alt+A to jump to PPE (Assertion) step.

---

### Step 6: Generate Financial Statements
**What it does:** One-click generation of entity-appropriate FS (Balance Sheet + P&L or I&E, depending on entity type).

**Quick Actions:**
- [ ] Click **Generate FS**
- [ ] App validates: mappings complete, BS balanced, etc.
- [ ] FS appears in tabs: **Balance Sheet**, **P&L** (or **I&E** for non-company), **Notes** (auto-populated)
- [ ] Review for obvious errors (e.g., totals, debit/credit sides)
- [ ] If error found, go back to Step 3 or 4 to fix mapping/adjustment
- [ ] Proceed to Step 7 (Notes)

**FS Format by Entity:**
- **Company:** BS, P&L, Cash Flow (Schedule III)
- **LLP:** BS, P&L, Partners' Capital Schedule
- **Non-company (Prop/Part):** BS, Trading A/c, P&L
- **AOP/Trust:** BS, Income & Expenditure, Receipt & Payment

**When to Proceed:** When BS and all totals look correct.  
**Key Tip:** Use **F5** keyboard shortcut anytime to regenerate FS (e.g., if you edited Step 5 PPE).  
**Keyboard:** F5 = Generate; F9 = Validate.

---

### Step 7: Notes to Accounts
**What it does:** Auto-generate + edit Notes (footnotes) to FS (15–29 per entity type).

**Quick Actions:**
- [ ] App auto-populates notes with calculated values from BS/P&L
- [ ] Review auto-populated notes (e.g., Share Capital, Trade Payables, Trade Receivables ageing)
- [ ] Edit manually if needed (e.g., add narrative text, adjust note number/order)
- [ ] Fill missing fields (e.g., accounting policies, contingent liabilities, related-party transactions)
- [ ] Leave blank if not applicable
- [ ] Proceed to Step 8 (Reports)

**Standard Notes (Companies):**
- Notes 1–3: Accounting Policies, General Info, Share Capital
- Notes 4–7: Reserves, Borrowings, Payables, Provisions
- Notes 8–14: Assets (PPE, Investments, Receivables, Cash)
- Notes 15–29: Expense breakdowns, Related-party, Contingencies

**When to Proceed:** When mandatory notes are complete (or marked "Not Applicable").  
**Key Tip:** Notes auto-reference ledger balances. Edit them to add context, not numbers.  
**Keyboard:** Alt+N to jump to Notes.

---

### Step 8: Reports (Directors' + Audit)
**What it does:** Draft + edit narrative reports (Directors' Report, Audit Report).

**Quick Actions:**
- [ ] Two tabs: **Directors' Report**, **Audit Report**
- [ ] Click in text area → type/edit report text
- [ ] Use placeholder [ENTITY_NAME], [FY], [NET_PROFIT] which auto-fill
- [ ] Formatting: plain text (no colors/fonts in DOCX export)
- [ ] Leave blank if not required for your entity
- [ ] Proceed to Step 9 (Export)

**When to Proceed:** After reports are drafted/approved.  
**Key Tip:** Reports are optional; leave blank if not required.

---

### Step 9: Export
**What it does:** Output FS + Reports in PDF (print-ready), Excel (editable), or Word (reports) format.

**Quick Actions:**
- [ ] Click **Export**
- [ ] Choose file formats:
  - ☑ **PDF** (FS: Balance Sheet, P&L, Notes) — for filing/email
  - ☑ **Excel** (FS in separate sheets, WTB, PPE schedule) — for edits/analysis
  - ☑ **Word** (Directors' Report, Audit Report) — for typesetting
- [ ] Select destination folder (default: project folder)
- [ ] Click **Export**
- [ ] Files saved: `FinStruct_[EntityName]_[FY].pdf`, `.xlsx`, `.docx`

**Export Format Guide:**
- **PDF:** Print-ready, formatted with headers/footers, page numbers, entity logo. ~2–5 MB. **Use for:** Filing with ROC, sending to auditor, email to client.
- **Excel:** Fully editable, no formulas. Separate sheets: BS, P&L, Notes, WTB. **Use for:** Internal analysis, client review, rework.
- **Word:** Plain text reports (Directors' + Audit). **Use for:** Formatting, adding signatures, final typesetting.

**When Done:** Step 9 is the final step. Project is complete!  
**Key Tip:** Use **F12** keyboard shortcut to open Export dialog anytime.

---

## Input Formats

### Trial Balance Sources

**Excel (XLSX)**
- Export from Tally / SAP / QuickBooks as XLSX
- FinStruct auto-detects columns: Ledger, Debit, Credit, Balance, Prior Year
- Column headers can be: "Account", "Particulars", "Closing Debit", "CY Amount", "PY", etc.
- Sample structure:
  ```
  Ledger Name | Debit | Credit | Balance | PY Balance
  Bank A/c    | 50000 | 0      | 50000   | 40000
  Trade A/c   | 0     | 25000  | -25000  | -20000
  ```

**CSV (Comma/Tab/Semicolon)**
- Export trial balance as CSV with any delimiter (auto-detected)
- Same column structure as XLSX
- Useful for QuickBooks, cloud accounting software

**Tally XML**
- Export from Tally Prime: **Masters → Company → Export → XML (Ledger Summary)**
- FinStruct parses ledger hierarchy automatically
- Fastest import for Tally users

### Column Auto-Detection Fails?

If FinStruct can't find your Ledger column, you'll see a dialog:
```
Column Detection Failed

Please map the following columns manually:
- Ledger Name:     [Select from list]
- Debit Amount:    [Select from list]
- Credit Amount:   [Select from list]
- Net/Balance:     [Select from list]
- Prior Year:      [Select from list]
```
- Click each dropdown → select the column from your file
- Click **Confirm** → import proceeds

---

## Export & Output Formats

### PDF (Print-Ready Financial Statements)

**What's included:**
- Balance Sheet (heading + schedules)
- P&L or Income & Expenditure Account
- Notes to Accounts (1–29)
- Header/footer with entity name, FY, page numbers
- Professional formatting (fonts, spacing, colors)

**File size:** ~2–5 MB per FS  
**Use cases:** Filing with ROC, auditor review, email to stakeholders  
**Edit:** PDF is read-only. Use Export → Excel if you need to edit numbers.

### Excel (XLSX — Editable FS)

**What's included:**
- **FS Sheet:** Balance Sheet, P&L, Notes (all in one sheet or separate tabs, depending on preference)
- **WTB Sheet:** Raw Working Trial Balance (for audit trail)
- **PPE Schedule:** Fixed assets list + depreciation detail (if applicable)

**Formulas:** None (values only). Safe to edit and send to client.  
**Use cases:** Client review, rework/sensitivity analysis, archival  
**Edit:** Open in Excel, edit numbers freely.

### Word (DOCX — Narrative Reports)

**What's included:**
- Directors' Report (from Step 8)
- Audit Report (from Step 8)
- Placeholder text (e.g., signature lines, date fields)

**Format:** Plain text, no tables. Ready for typesetting.  
**Use cases:** Final document for filing, adding logos/signatures  
**Edit:** Open in Word, format/sign as needed.

---

## Advanced Features

### Smart Project Rollover (Next FY)
**What it does:** Copies current project to next year, carrying forward:
- **ALL Master Details** (Entity info, Auditor, Directors)
- Prior-Year (PY) balances from current year (CY)
- Learned ledger mappings
- PPE closing balances → opening balances
- **Auto-incrementing Financial Year** (e.g., 2024-25 → 2025-26)

**How to use:** Menu: **Project → Rollover to Next FY**.

### Dashboard Enhancements
- **Text Wrapping:** Long entity names and paths now wrap automatically in the recent projects list.
- **Delete from Disk:** Permanently delete a project folder and its `.finstruct` file directly from the dashboard.
- **Folder Deletion:** Use the "Delete from list" button (red) to wipe a project folder entirely.

### Multi-Provider AI Assistance
FinStruct now supports multiple AI providers for ledger mapping:
- **Claude (Anthropic)**
- **OpenAI (GPT-4o)**
- **Gemini (Google)**
Configure your preferred provider and API keys via **Help → AI Assistance Settings**.

---

## Best Practices for Multiple Projects

### Folder Structure
**Recommended:**
```
~/Documents/FinStruct/Projects/
  ├── XYZ_Ltd_2024-25/           (Company A, FY 2024-25)
  │   └── XYZ_Ltd_2024-25.finstruct
  ├── XYZ_Ltd_2025-26/           (Company A, FY 2025-26) ← Rollover
  │   └── XYZ_Ltd_2025-26.finstruct
  ├── ABC_LLP_2024-25/           (LLP B, FY 2024-25)
  │   └── ABC_LLP_2024-25.finstruct
  └── ...
```

**Why?** Each project is a separate folder; keeps exports organized by client/year.

### Rollover Strategy

**Scenario 1: Audit + Filing Done**
→ Finalize FY 2024-25 project (Lock)  
→ Rollover to FY 2025-26 (mappings auto-imported)  
→ Import new TB for 2025-26  
→ 60% of mapping time saved

**Scenario 2: Frequent Changes**
→ Don't lock yet if client is still making journal entries  
→ Import updated TB in Step 2, re-validate  
→ Re-generate FS (F5) with latest balances  
→ Lock only after final signoff

### Batch Processing (10+ Projects)

**Workflow for handling multiple clients in one session:**

1. **Import Phase:** Create 10 projects → import all TBs (Steps 1–2)
2. **Mapping Phase:** Map ledgers for all 10 (Step 3)
   - Mappings learned → 2nd client's mapping 50% faster than 1st
3. **Validation Phase:** Validate all 10 (F9) for balance
4. **Generation Phase:** Generate FS for all 10 (F5)
5. **Export Phase:** Export all 10 in one batch (Step 9)

**Tip:** Dashboard shows recent projects. Ctrl+O to switch between projects quickly.

### Archiving Strategy

**After Filing + Approval:**
1. Lock project (Project → Lock)
2. Export all formats (PDF, Excel, Word)
3. Zip the project folder: `[ProjectName]_FINAL.zip`
4. Move to external drive or cloud storage (e.g., OneDrive, Google Drive)
5. Delete from local `~/Documents/FinStruct/` to save space (keep backup!)

**Storage:** A typical project folder is ~5–10 MB. Keep 2–3 years locally; archive older projects.

### Team Workflow

**Role Division:**
- **Accountant A:** Import TB (Step 2) + Review WTB (Step 4)
- **Accountant B:** Map Ledgers (Step 3) + Add Adjustments (Step 4)
- **Manager:** Review FS (Step 6) + Edit Reports (Step 8)
- **Export:** Accountant A exports (Step 9) + delivers to client

**Handoff:** Save project after each step. Accounting team member A can open and continue.

---

## FAQ & Troubleshooting

### Database Locked Error

**"Error: Database Locked"**

**Cause:** Another instance of FinStruct has the same project open.

**Fix:**
1. Check if another window/session has the project open
2. Close that window
3. Re-open project in current session

---

### FS Shows Zeros in Notes

**"Note 4 (Reserves) shows ₹0 even though my P&L has profit."**

**Cause:** PPE data incomplete, or Reserves ledger not mapped.

**Fix:**
1. Go to Step 5 (PPE) → ensure all fixed assets entered
2. Go to Step 3 (Mapping) → search "Reserve" or "Surplus" ledger → confirm mapped to correct code
3. Re-generate FS (F9 or Step 6)

---

### PDF Date Format Wrong

**"PDF shows 'Balance Sheet as at 31st March, 24' instead of '2025'."**

**Note:** This was a bug in v1.0. Fixed in v1.1. Re-export your project with the latest FinStruct version.

---

### Depreciation Calculation Question

**Q: Should I use SLM or WDV?**

**A:**
- **SLM (Straight-Line):** Most assets (buildings, furniture, fixtures). Depreciation = cost / life. Simpler.
- **WDV (Written-Down Value):** Per IT Act (India). Applies declining rate to opening WDV. Use if filing IT returns in India.

**Check your prior year FS** to see which method your company used. Keep it consistent.

---

### Export Fails or File Not Found

**"Error: Cannot write to export path."**

**Cause:** File path is not writable, or antivirus is blocking write.

**Fix:**
1. Choose export folder (Step 9 dialog) → ensure you have write permission
2. Try a different folder (e.g., Desktop, My Documents)
3. Disable antivirus temporarily, then export
4. Check file manager to confirm files were created

---

### Ledger Not Found in Mapping Dropdown

**"I want to map 'Salient Features' but it's not in the suggested codes."**

**Cause:** Ledger type doesn't match entity (e.g., LLP code in Company FS).

**Fix:**
1. Check entity type: Is it really a Company? Or LLP/Trust?
2. Search dropdown by typing first letters: "Sale" → finds "Sales A/c"
3. If ledger is truly not applicable (e.g., "Salient Features" is a label), leave unmapped or mark as "Not Applicable"

---

### Can I Consolidate Multiple Subsidiaries?

**Q: Can FinStruct generate consolidated FS?**

**A:** No. FinStruct works on single-entity basis. For consolidation, export subsidiary FS to Excel → manually consolidate in a new workbook.

---

### Can I Import from Google Sheets?

**Q: My TB is in Google Sheets. Can I import directly?**

**A:** No. Export Google Sheet as `.xlsx` (File → Download → Excel) → then import into FinStruct.

---

### Is FinStruct ICAI-Compliant?

**Q: Are the FS formats ICAI-approved?**

**A:** Yes. FinStruct uses Schedule III (Companies Act 2013) and ICAI Notified Formats (NCE entities). Formats are published by ICAI and included in the app code.

---

### Can I Save Draft Projects?

**Q: Do projects auto-save?**

**A:** Yes. FinStruct auto-saves after each step. You can close anytime and re-open later. No data is lost.

---

## Keyboard Shortcuts

| Shortcut | Action | When to Use |
|----------|--------|------------|
| **Ctrl+N** | New Project | Create new project |
| **Ctrl+O** | Open Project | Open existing file |
| **F5** | Generate FS | Re-calculate statements |
| **F9** | Validate | Check balance & mapping |
| **F10** | Go to Notes | Jump to Step 7 |
| **F12** | Export | Open export dialog |
| **Alt+M** | Go to Mapping | Jump to Step 3 |
| **Alt+W** | Go to WTB | Jump to Step 4 |
| **Alt+A** | Go to PPE | Jump to Step 5 |
| **Alt+B / Alt+P** | Go to FS | Jump to Step 6 |
| **Alt+N** | Go to Notes | Jump to Step 7 |
| **Alt+E** | Export Dialog | Jump to Step 9 |

---

## Glossary

| Term | Definition |
|------|-----------|
| **Working Trial Balance (WTB)** | Trial balance after ledger classification (mapping) and adjustments. Used to generate FS. |
| **Confidence Score** | ML model's confidence (0–1) that a ledger mapping is correct. Green ≥0.85, Yellow 0.65–0.84, Red <0.65. |
| **SLM (Straight-Line Method)** | Depreciation = (Cost − Salvage) / Useful Life. Annual expense is constant. |
| **WDV (Written-Down Value)** | Depreciation = Opening WDV × IT Rate / 100. Declining balance per IT Act. |
| **Schedule III** | Format for company financial statements under Companies Act 2013. Includes BS, P&L, Cash Flow. |
| **NCE** | ICAI Notified Format for Non-Corporate Entities (Prop, Part, LLP, AOP, Trust). |
| **ICAI** | Institute of Chartered Accountants of India. Regulator; prescribes FS formats. |
| **PPE** | Property, Plant & Equipment. Fixed assets (land, buildings, machinery, vehicles). |
| **Rollover** | Year-end process to copy current FY project to next FY, carrying forward balances + mappings. |
| **Entity Master** | Core information about the company (name, address, contact, registration numbers). |
| **Adjustment** | Manual entry to TB in Step 4 (e.g., accrual, provision). Not posted to ledgers; FS-only. |
| **Note** | Footnote to FS explaining line items (e.g., Note 4: Share Capital breakdown). |
| **Audit Trail** | Log of all project actions (create, import, generate, lock) with timestamps. |

---

## Detailed Walkthrough: Company Entity

**Scenario:** ABC Limited, a software services company, for FY 2024-25.  
**Goal:** Generate audited FS from trial balance in 1 hour.

### Setup (5 min)

**Step 1: Entity Setup**
```
Entity Name:          ABC Limited
Entity Type:          Company
Registration:         CIN: U7299DL2020PTC100001
Address:              123, Tech Park, New Delhi 110001
Financial Year:       2024-25
Auditor Name:         XYZ & Co (Chartered Accountants)
Auditor Partner:      Mr. Rajesh Kumar
Auditor Mem No:       000001
```
→ Click **Save**

---

**Step 2: Import Trial Balance**

Export TB from Tally:
- File → Tally Prime → Ledgers/Groups → Export (XLSX)
- Save as: `ABC_Ltd_TB_2024-25.xlsx`
- Columns: Ledger, Opening Debit, Opening Credit, Debit, Credit

In FinStruct:
- Step 2 → Choose File → `ABC_Ltd_TB_2024-25.xlsx`
- Auto-detects columns ✓
- Review: 45 ledgers imported (Bank, Cash, Receivables, Payables, etc.)
- Click **Import** → WTB generated with 45 rows

→ Proceed to Step 3

---

### Mapping (15 min)

**Step 3: Classify Ledgers**

Grid appears:
```
Ledger Name          | Suggested Code    | Confidence | Action
─────────────────────────────────────────────────────
Bank A/c-HDFC        | AS024 Cash        | 0.97 (Green) | ✓ Accept
ICICI OD             | EL020 Short-term  | 0.89 (Green) | ✓ Accept
Cash in Hand         | AS023 Cash        | 0.98 (Green) | ✓ Accept
Receivables-Trade    | AS021 TR Rec      | 0.92 (Green) | ✓ Accept
Payables-Trade       | EL026 TP-Others   | 0.78 (Yellow)| ⚠ Review → Select EL026 ✓
Advances to Vendor   | AS030 ST Loan     | 0.42 (Red)   | ✗ Manual: Select AS027
Software License     | AS004 Intangible  | 0.85 (Green) | ✓ Accept
Employee Advances    | AS030 ST Loan     | 0.72 (Yellow)| ⚠ Review → Select AS028 ✓
Salary Payable       | EL029 Other Curr  | 0.68 (Yellow)| ⚠ Review → Select EL029 ✓
...
```

- 30 ledgers auto-confirmed (Green)
- 12 ledgers reviewed + confirmed (Yellow → Yellow/Green)
- 3 ledgers manually mapped (Red)
- Total: **45/45 mapped** ✓

→ Proceed to Step 4

---

### Review & Adjust (5 min)

**Step 4: Review WTB + Adjustments**

WTB summary:
```
Total Assets (Current + Non-Current):     ₹5,50,00,000
Total Equity & Liabilities:               ₹5,50,00,010
Difference:                               ₹10 (rounding ok)
```

Add adjustment (deferred interest accrual):
- Click **+ New Adjustment**
- Ledger: Interest Payable | Code: EL030 | Dr: 0 | Cr: 1,50,000 | Narration: "Accrued for Q4"
- Click **Save**

Updated WTB:
```
Total Assets:        ₹5,50,00,000
Total Liabilities:   ₹5,50,01,510 (updated)
Difference:          ₹1,510 (recheck → found: Retention payable not mapped)
```

Re-check mapping for "Retention A/c" → map to **EL029**  
Re-generate WTB → difference = 0 ✓

→ Proceed to Step 5

---

### Fixed Assets (5 min)

**Step 5: PPE Register**

Add assets:
```
Asset Name            | Category     | SLM/WDV | Life | Gross Op  | Additions | Disposals
─────────────────────────────────────────────────────────────────
Office Building       | Buildings    | SLM     | 60   | 60,00,000 | 0         | 0
Server Computers      | Computers    | WDV     | 3    | 8,00,000  | 2,00,000  | 0
Office Furniture      | Furniture    | SLM     | 10   | 5,00,000  | 50,000    | 0
Software Licenses     | Intangible   | SLM     | 5    | 3,00,000  | 75,000    | 0
```

App auto-calculates:
```
Asset                 | Gross Closing | Acc Dep (CY) | NBV
─────────────────────────────────────
Office Building       | 60,00,000     | 1,00,000     | 59,00,000
Server Computers      | 10,00,000     | 3,20,000     | 6,80,000
Office Furniture      | 5,50,000      | 55,000       | 4,95,000
Software Licenses     | 3,75,000      | 75,000       | 3,00,000
─────────────────────────────────────
Total PPE (Net Block) | —             | —            | 73,75,000
```

→ Proceed to Step 6

---

### Generate FS (5 min)

**Step 6: One-Click FS Generation**

Click **Generate FS** → 3 seconds later:

```
┌────────────────────────────────────────────────┐
│  ABC LIMITED - BALANCE SHEET                   │
│  As at 31st March, 2025                        │
│  (₹ unless otherwise stated)                   │
├────────────────────────────────────────────────┤
│ EQUITY & LIABILITIES              CY  PY       │
├────────────────────────────────────────────────┤
│ I. Shareholders' Funds                         │
│    Share Capital (Note 3)        10,00,000     │
│    Reserves & Surplus (Note 4)  2,85,00,000    │
│    Sub-total (A)                2,95,00,000    │
│                                                │
│ II. Non-Current Liabilities                    │
│     Long-term Borrowings (Note 5) 50,00,000    │
│     Sub-total (B)                 50,00,000    │
│                                                │
│ III. Current Liabilities                       │
│      Trade Payables (Note 9)     1,20,00,000   │
│      Other Current Liab (Note 10) 35,00,000    │
│      Short-term Provisions          10,010     │
│      Sub-total (C)               1,55,00,010   │
│                                                │
│ TOTAL EQUITY & LIABILITIES (A+B+C) 5,00,00,010 │
├────────────────────────────────────────────────┤
│ ASSETS                           CY     PY     │
├────────────────────────────────────────────────┤
│ I. Non-Current Assets                          │
│    Fixed Assets (Note 12)       73,75,000      │
│    Non-Current Inv (Note 13)     8,50,000      │
│    Sub-total (D)                82,25,000      │
│                                                │
│ II. Current Assets                             │
│     Inventories                 10,00,000      │
│     Trade Receivables (Note 17) 2,80,00,000    │
│     Cash & Equivalents (Note 18) 1,35,00,000   │
│     Other Current Assets         2,75,010      │
│     Sub-total (E)              4,27,75,010     │
│                                                │
│ TOTAL ASSETS (D+E)              5,10,00,010    │
└────────────────────────────────────────────────┘
```

**P&L:** Generated with 29 notes auto-populated.

→ Proceed to Step 7

---

### Notes (5 min)

**Step 7: Auto-Populate Notes**

App fills:
- **Note 3 (Share Capital):** 10,00,000 (from EL001+EL002 mapping)
- **Note 4 (Reserves):** 2,85,00,000 (from EL003-EL008 aggregate)
- **Note 9 (Trade Payables):** 1,20,00,000 with ageing schedule (auto-calculated)
- **Note 12 (PPE):** Table with Asset, Gross, Depreciation, NBV (from PPE register)
- **Note 17 (Trade Receivables):** 2,80,00,000 with ageing schedule

Manually edit:
- **Note 1 (Accounting Policies):** Add specific policies (SLM for buildings, WDV for IT, FIFO for stock)
- **Note 2 (General Info):** Add incorporation date, registered office, principal business

→ Proceed to Step 8

---

### Reports (5 min)

**Step 8: Directors' Report + Audit Report**

**Directors' Report:**
```
The Directors have pleasure in submitting the Annual Report for FY 2024-25.

Your Company's revenue from operations has grown by 15% to ₹8,50,00,000. 
Net profit after tax is ₹2,85,00,000 (PY: ₹2,50,00,000).

The Board recommends a dividend of ₹2 per share.

[... other disclosures ...]

Signed: Mr. Arvind Mehta, Managing Director
        Ms. Priya Sharma, Whole-Time Director
```

**Audit Report:**
```
Independent Auditor's Report

To the Members of ABC Limited,

We have audited the financial statements of ABC Limited for FY 2024-25.

In our opinion, the financial statements present a true and fair view...

[... audit opinion ...]

Signed: XYZ & Co
        Chartered Accountants
        (Rajesh Kumar, Partner — MemNo. 000001)
```

→ Proceed to Step 9

---

### Export (2 min)

**Step 9: Export in All Formats**

Check boxes:
- ☑ **PDF** (print-ready FS + notes)
- ☑ **Excel** (editable FS + WTB)
- ☑ **Word** (narrative reports)

Click **Export** → files saved:
```
~/Documents/FinStruct/Projects/ABC_Ltd_2024-25/
  ├── ABC_Limited_2024-25.pdf       (5.2 MB)
  ├── ABC_Limited_2024-25.xlsx      (850 KB)
  ├── ABC_Limited_2024-25.docx      (120 KB)
```

**PDF Preview:**
- Front matter: Entity name, FY, signed declarations
- Page 1: Balance Sheet with notes references
- Page 2: P&L with notes references
- Pages 3–10: Notes 1–29 (detailed schedules)
- Footer: "Prepared with FinStruct | Page 1 of 10"

→ **Complete!** Auditor receives PDF. Client gets Excel for records.

---

### Final Checks

**Lock project:**
- Menu → Project → Lock / Finalize Project
- Timestamp recorded in Audit Log
- Project now read-only

**Next Year:**
- Menu → Project → Rollover to Next FY (FY 2025-26)
- PY balances + mappings auto-carried forward
- New project ready for FY 2025-26 TB import
- Mapping speed: 50% faster (learned mappings!)

---

## Support & Resources

- **GitHub:** https://github.com/rajacacs/Claude-project_Finstruct
- **Issues / Feedback:** File issue on GitHub
- **ICAI FS Formats:** Refer ICAI website for Schedule III and notified NCE formats

---

**FinStruct v1.1** — Automate your financial statements. Save 80% of FS prep time.

*Last Updated: May 2026*
