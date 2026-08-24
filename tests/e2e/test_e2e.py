#!/usr/bin/env python3
"""
FinStruct E2E Verification Test
Manufacturing Pvt Ltd — Schedule III Non-Ind AS
Tests: Import → Map → Validate → FS Generation → Export → Imbalanced TB Warning
"""

import sys
import os
from pathlib import Path

# Add repo root to path
REPO = Path("/home/user/Claude-project_Finstruct")
sys.path.insert(0, str(REPO))

TEST_DIR   = Path("/tmp/finstruct_test")
OUT_DIR    = TEST_DIR / "output"
TB_CSV     = TEST_DIR / "TB_Manufacturing_PvtLtd.csv"
PROJECT_DB = TEST_DIR / "mfg_test.finstruct"
IMBAL_CSV  = TEST_DIR / "TB_Imbalanced.csv"

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️ WARN"
INFO = "ℹ️ INFO"

results = []

def check(label, cond, detail=""):
    status = PASS if cond else FAIL
    msg = f"  {status}  {label}"
    if detail:
        msg += f"\n         {detail}"
    print(msg)
    results.append((status, label))
    return cond

def section(title):
    print(f"\n{'═'*65}")
    print(f"  {title}")
    print('═'*65)


section("STEP 1 — Import TB (CSV with SubType column)")

from finstruct.core.tb_importer import import_csv

result = import_csv(TB_CSV)

check("Import completed without errors", len(result.errors) == 0,
      str(result.errors) if result.errors else "")
check("Rows imported", len(result.rows) > 30,
      f"Imported {len(result.rows)} rows")
check("Balancing line skipped",
      any("Skipped" in w for w in result.warnings),
      f"Warnings: {result.warnings}")
check("SubType auto-mapping triggered",
      any("Auto-mapped" in w for w in result.warnings),
      f"Hints: {len(result.subtype_hints)} ledgers")

auto_mapped_count = len(result.subtype_hints)
total_rows = len(result.rows)
print(f"\n  {INFO}  SubType auto-map: {auto_mapped_count}/{total_rows} = "
      f"{auto_mapped_count/total_rows*100:.0f}%")

from finstruct.core.master_db import get_lookup_map
lm = get_lookup_map()
r0_hint = result.subtype_hints.get(0)
check("EL001 auto-mapped for Equity Share Capital",
      r0_hint == "EL001", f"Got: {r0_hint}")
tp_row = next((i for i, r in enumerate(result.rows)
               if "Trade Payables" in r["ledger_name"]), None)
tp_hint = result.subtype_hints.get(tp_row)
check("EL026 auto-mapped for Trade Payables", tp_hint == "EL026",
      f"Row {tp_row} hint: {tp_hint}")


section("STEP 2 — Persist to ProjectDB (Schema v3)")

if PROJECT_DB.exists():
    PROJECT_DB.unlink()

from finstruct.data.project_db import ProjectDB
db = ProjectDB(PROJECT_DB)
db.connect()

entity = {
    "entity_type":    "COMPANY",
    "entity_name":    "Vidya Manufacturing Pvt Ltd",
    "fy":             "2024-25",
    "cin":            "U12345MH2010PTC123456",
    "pan":            "AABCV1234D",
    "paid_up_capital":5000000,
    "auditor_name":   "M/s. Joshi & Associates",
    "director1_name": "Mr. Rajesh Sharma",
    "director2_name": "Mrs. Priya Mehta",
    "opinion_type":   "Unmodified",
    "reg_office":     "123, MIDC Industrial Area, Pune - 411 028",
}
for k, v in entity.items():
    db.set_entity(k, str(v) if not isinstance(v, str) else v)

db.insert_raw_tb_batch(result.rows)
raw_tb_after = db.get_raw_tb()
raw_ids = [r["id"] for r in raw_tb_after]

check("Raw TB rows inserted", len(raw_ids) == total_rows,
      f"Inserted {len(raw_ids)} rows")


section("STEP 3 — Map Ledgers (SubType auto + Schedule III manual)")

auto_count = 0
for row_idx, code in result.subtype_hints.items():
    raw_id = raw_ids[row_idx]
    src_row = result.rows[row_idx]
    db.upsert_wtb(raw_id, code, 1.0, "SUBTYPE",
                  src_row["cy_net"], src_row.get("py_net", 0), confirmed=1)
    auto_count += 1

check("SubType auto-map saved to WTB", auto_count == auto_mapped_count,
      f"{auto_count} auto-mapped")

MANUAL_MAP = {
    "Equity Share Capital":              "EL001",
    "General Reserve":                   "EL006",
    "Retained Earnings / Surplus":       "EL007",
    "Term Loan from SBI":                "EL010",
    "Trade Payables – Creditors":        "EL026",
    "Statutory Dues Payable":            "EL028",
    "Employee Payables":                 "EL029",
    "Provision for Income Tax":          "EL032",
    "Accumulated Depreciation":          "AS002",
    "Plant & Machinery – Gross Block":   "AS001",
    "Raw Material Stock":                "AS015",
    "Work-in-Progress":                  "AS016",
    "Finished Goods":                    "AS017",
    "Trade Receivables (< 6 months)":    "AS021",
    "Cash in Hand":                      "AS023",
    "Bank Current Account – HDFC":       "AS024",
    "Advance to Suppliers":              "AS027",
    "Advance Tax & TDS Receivable":      "AS029",
    "GST Input Tax Credit":              "AS032",
    "Sales – Manufactured Goods":        "PL001",
    "Interest Income on FD":             "PL005",
    "Opening Stock – Finished Goods":    "PL013",
    "Closing Stock – Finished Goods":    "PL015",
    "Raw Material Consumed":             "PL010",
    "Salaries & Wages":                  "PL017",
    "PF and ESI Contribution":           "PL019",
    "Interest on Term Loan":             "PL022",
    "Bank Charges":                      "PL024",
    "Depreciation on Plant":             "PL025",
    "Power & Fuel":                      "PL027",
    "Repairs & Maintenance":             "PL029",
    "Professional & Legal Fees":         "PL034",
    "Audit Fees":                        "PL035",
    "Miscellaneous Expenses":            "PL039",
    "Current Income Tax":                "PL040",
}

wtb_existing = {row["raw_tb_id"] for row in db.get_wtb()}
manual_count = 0
for row_idx, row in enumerate(result.rows):
    raw_id = raw_ids[row_idx]
    if raw_id in wtb_existing:
        continue
    ledger = row["ledger_name"]
    code = MANUAL_MAP.get(ledger)
    if code:
        db.upsert_wtb(raw_id, code, 1.0, "MANUAL",
                      row["cy_net"], row.get("py_net", 0), confirmed=1)
        manual_count += 1
    else:
        print(f"  {WARN}  No mapping for: '{ledger}'")

all_wtb = db.get_wtb()
mapped = [r for r in all_wtb if r["mapping_code"] and r["is_confirmed"]]
unmapped = [r for r in all_wtb if not r["mapping_code"] or not r["is_confirmed"]]
check("All ledgers mapped & confirmed", len(unmapped) == 0,
      f"Mapped: {len(mapped)}, Unmapped: {len(unmapped)}")
check("Total WTB rows = imported rows", len(all_wtb) == total_rows,
      f"WTB: {len(all_wtb)}, Rows: {total_rows}")


section("STEP 4 — Aggregate WTB & Validate TB Balance")

from finstruct.core.wtb_engine import build_wtb_lines, aggregate_by_code, validate_balance, apply_adjustments

raw_tb_rows = db.get_raw_tb()
wtb_rows    = db.get_wtb()
lines       = build_wtb_lines(wtb_rows, raw_tb_rows)
totals      = aggregate_by_code(lines)
adj_rows    = db.get_adjustments()
totals      = apply_adjustments(totals, adj_rows)

check("Totals computed", len(totals) > 0, f"{len(totals)} codes with values")

from finstruct.core.master_db import get_lookup_map
eq_share = totals.get("EL001", (0, 0))[0]
check("Share Capital EL001 = ₹50,00,000", abs(abs(eq_share) - 5000000) < 1,
      f"Got: ₹{eq_share:,.0f}")
plant_gross = totals.get("AS001", (0, 0))[0]
check("Plant Gross Block AS001 = ₹80,00,000", abs(plant_gross - 8000000) < 1,
      f"Got: ₹{plant_gross:,.0f}")
sales = totals.get("PL001", (0, 0))[0]
check("Sales PL001 = ₹1,50,00,000", abs(abs(sales) - 15000000) < 1,
      f"Got: ₹{sales:,.0f}")

val = validate_balance(totals, "COMPANY")
check("BS balances (CY)", val.ok or abs(val.balance_diff_cy) < 1,
      f"Balance diff: ₹{val.balance_diff_cy:,.2f}")


section("STEP 5 — Generate Financial Statements (Schedule III Non-Ind AS)")

from finstruct.core.fs_engine import FSEngine
em = db.get_all_entity()
engine = FSEngine("COMPANY", totals, em, "2024-25", divisor=1)
doc    = engine.generate()

check("BS generated", len(doc.bs) > 10, f"{len(doc.bs)} BS lines")
check("P&L generated", len(doc.pl) > 10, f"{len(doc.pl)} P&L lines")
check("CF generated", len(doc.cf) > 5, f"{len(doc.cf)} CF lines")
bs_totals = [l for l in doc.bs if l.row_type in ("TOTAL", "GRAND")]
check("BS has Grand Total lines", len(bs_totals) > 0, f"{len(bs_totals)} total/grand lines")
check("PAT line in P&L", any("tax" in l.label.lower() for l in doc.pl), "")
revenue_line = next((l for l in doc.pl if "revenue from operations" in l.label.lower()), None)
if revenue_line:
    check("Revenue from Operations = ₹1,50,00,000",
          abs(abs(revenue_line.cy) - 15000000) < 100, f"Got: ₹{revenue_line.cy:,.0f}")
dep_line = next((l for l in doc.pl if "depreciation" in l.label.lower()
                 and l.row_type not in ("HEADER","SECTION")), None)
if dep_line:
    check("Depreciation = ₹5,00,000", abs(dep_line.cy - 500000) < 100,
          f"Got: ₹{dep_line.cy:,.0f}")


section("STEP 6 — Generate Notes to Accounts (Auto-Numbered)")

from finstruct.core.notes_engine import NotesEngine
ne = NotesEngine(totals, "COMPANY", divisor=1, entity_master=em)
notes, note_map = ne.generate_dynamic(doc)

check("Notes generated", len(notes) > 0, f"{len(notes)} Note objects")
check("Auto-number map built", isinstance(note_map, dict),
      f"{len(note_map)} mappings")
non_reserved = [k for k in note_map.keys() if k not in (1, 2)]
check("Note renumbering from 3 onwards",
      all(v >= 3 for v in [note_map[k] for k in non_reserved]) or not non_reserved,
      f"non-reserved: {list(note_map.items())[:8]}")
print(f"\n  {INFO}  Notes: {sorted(n.number for n in notes)}")


section("STEP 7 — Export FS Output")

OUT_DIR.mkdir(exist_ok=True)
out_file = OUT_DIR / "FS_Manufacturing_PvtLtd_FY2024-25.txt"

def fmt(val): return f"₹{val:>15,.0f}"
def rule(n=65): return "─" * n

with open(out_file, "w", encoding="utf-8") as f:
    company = em.get("entity_name", "Vidya Manufacturing Pvt Ltd")
    fy = em.get("fy", "2024-25")
    f.write(f"{'='*65}\n  {company.upper()}\n  Schedule III FS | FY {fy}\n{'='*65}\n\n")
    for section_name, lines_data in [("BALANCE SHEET", doc.bs), ("PROFIT & LOSS", doc.pl)]:
        f.write(f"\n{rule()}\n  {section_name}\n{rule()}\n")
        for l in lines_data:
            if l.row_type == "BLANK": f.write("\n"); continue
            indent = "  " * l.indent
            note_s = str(l.note) if l.note else ""
            if l.row_type in ("HEADER", "SECTION"):
                f.write(f"  {indent}{l.label.upper()}\n")
            elif l.row_type in ("TOTAL", "GRAND", "SUBTOTAL"):
                f.write(f"  {indent}{l.label:<35} {note_s:>4}  {fmt(l.cy):>15}  {fmt(l.py):>15}\n  {rule()}\n")
            else:
                f.write(f"  {indent}{l.label:<35} {note_s:>4}  {fmt(l.cy):>15}  {fmt(l.py):>15}\n")
    f.write(f"\n{rule()}\n  NOTES TO ACCOUNTS\n{rule()}\n")
    for note_obj in sorted(notes, key=lambda n: n.number):
        if not note_obj.lines: continue
        f.write(f"\n  Note {note_obj.number}: {note_obj.title}\n  {'─'*55}\n")
        for nl in note_obj.lines:
            if nl.row_type == "BLANK": f.write("\n"); continue
            indent = "  " * nl.indent
            if nl.row_type in ("HEADER", "SECTION"): f.write(f"  {indent}{nl.label.upper()}\n")
            elif nl.row_type in ("TOTAL", "GRAND"):
                f.write(f"  {indent}{nl.label:<40}  {fmt(nl.cy):>15}  {fmt(nl.py):>15}\n  {'─'*55}\n")
            else:
                f.write(f"  {indent}{nl.label:<40}  {fmt(nl.cy):>15}  {fmt(nl.py):>15}\n")
    f.write(f"\n{'='*65}\n  Generated by FinStruct | {fy}\n  Auto-mapped: {auto_mapped_count}  Manual: {manual_count}  Notes: {len(notes)}\n{'='*65}\n")

check("FS text output written", out_file.exists(), str(out_file))
check("Output file non-empty", out_file.stat().st_size > 1000,
      f"Size: {out_file.stat().st_size:,} bytes")


section("STEP 8 — Imbalanced TB Warning (assets ≠ liabilities)")

extra = "Unaccounted Asset,Other Assets,Tangible Assets – Gross Block,1000000,0\n"
IMBAL_CSV.write_text(TB_CSV.read_text(encoding="utf-8").rstrip() + "\n" + extra, encoding="utf-8")

result_imbal = import_csv(IMBAL_CSV)
imbal_db = Path("/tmp/finstruct_test/mfg_imbal.finstruct")
if imbal_db.exists(): imbal_db.unlink()
db_imbal = ProjectDB(imbal_db)
db_imbal.connect()
for k, v in entity.items():
    db_imbal.set_entity(k, str(v))

db_imbal.insert_raw_tb_batch([r for r in result_imbal.rows])
raw_imbal = db_imbal.get_raw_tb()
raw_ids_imbal = [r["id"] for r in raw_imbal]
for row_idx, code in result_imbal.subtype_hints.items():
    if row_idx < len(raw_ids_imbal):
        src = result_imbal.rows[row_idx]
        db_imbal.upsert_wtb(raw_ids_imbal[row_idx], code, 1.0, "SUBTYPE",
                             src["cy_net"], src.get("py_net", 0), confirmed=1)

wtb_imbal = db_imbal.get_wtb()
lines_imbal = build_wtb_lines(wtb_imbal, raw_imbal)
totals_imbal = aggregate_by_code(lines_imbal)
totals_imbal = apply_adjustments(totals_imbal, db_imbal.get_adjustments())

engine_imbal = FSEngine("COMPANY", totals_imbal, entity, "2024-25", divisor=1)
doc_imbal    = engine_imbal.generate()

lm = get_lookup_map()
bs_diff = sum(
    (1 if lm[c].sign == "CR_POSITIVE" else -1) * cy
    for c, (cy, _) in totals_imbal.items()
    if c in lm and lm[c].fs_tag == "BS"
)
print(f"\n  {INFO}  Imbalanced BS diff = ₹{bs_diff:,.0f}")

check("BS imbalance detected", abs(bs_diff) > 0.5,
      f"BS net diff: ₹{bs_diff:,.0f}")
bs_warn = [l for l in doc_imbal.bs if l.row_type == "TEXT" and "does not balance" in l.label]
check("FS engine flags BS imbalance", len(bs_warn) > 0,
      bs_warn[0].label if bs_warn else "no warning line")
print(f"\n  {WARN}  GUI shows: 'BS does not balance — diff ₹{abs(bs_diff):,.0f}. Proceed at own risk?'")
db_imbal.close()


db.close()

section("FINAL VERIFICATION SUMMARY")
passed = [r for r in results if r[0].startswith("✅")]
failed = [r for r in results if r[0].startswith("❌")]
print(f"\n  Total: {len(results)}  Passed: {len(passed)}  Failed: {len(failed)}")
if failed:
    print("\n  FAILED CHECKS:")
    for _, label in failed:
        print(f"    ✗ {label}")
print(f"\n  {'✅ ALL CHECKS PASSED — BUILD READY FOR .EXE' if not failed else '❌ SOME CHECKS FAILED'}")
print()
