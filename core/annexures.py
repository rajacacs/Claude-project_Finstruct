"""Custom Annexures / Sub-schedules with TB tie-out reconciliation.

Each annexure defines:
  - source codes (for TB tie-out total)
  - bucket structure (rows the user fills)
  - reconciliation tolerance (user-configurable, default 10)

Stored per-project in `note_data` table (existing schema).
"""

from __future__ import annotations
from dataclasses import dataclass, field

ANNEXURE_DEFS: dict[str, dict] = {
    "TR_AGEING": {
        "title":      "Trade Receivables Ageing Schedule (Sch III amendment)",
        "note_no":    17,
        "source_codes": ["AS020", "AS021"],
        "less_codes": ["AS022"],
        "rows": [
            "Undisputed – Considered Good – Less than 6 months",
            "Undisputed – Considered Good – 6 months to 1 year",
            "Undisputed – Considered Good – 1 to 2 years",
            "Undisputed – Considered Good – 2 to 3 years",
            "Undisputed – Considered Good – More than 3 years",
            "Undisputed – Considered Doubtful",
            "Disputed – Considered Good",
            "Disputed – Considered Doubtful",
        ],
    },
    "TP_AGEING": {
        "title":      "Trade Payables Ageing Schedule (MSME + Others)",
        "note_no":    9,
        "source_codes": ["EL025", "EL026"],
        "less_codes": [],
        "rows": [
            "MSME – Less than 1 year",
            "MSME – 1 to 2 years",
            "MSME – 2 to 3 years",
            "MSME – More than 3 years",
            "Others – Less than 1 year",
            "Others – 1 to 2 years",
            "Others – 2 to 3 years",
            "Others – More than 3 years",
            "Disputed dues – MSME",
            "Disputed dues – Others",
        ],
    },
    "SHARE_CAPITAL": {
        "title":      "Share Capital Working — Movement & Top Shareholders",
        "note_no":    3,
        "source_codes": ["EL001", "EL002"],
        "less_codes": [],
        "rows": [
            "Authorised — Equity Shares (Nos.)",
            "Authorised — Equity Shares (₹ value)",
            "Issued, Subscribed & Paid-up — Equity Shares (Nos.)",
            "Issued, Subscribed & Paid-up — Equity Shares (₹ value)",
            "Movement — Opening Balance",
            "Movement — Add: Shares Issued",
            "Movement — Less: Buyback / Forfeiture",
            "Movement — Closing Balance",
            "Shareholders > 5% — Name 1",
            "Shareholders > 5% — Holding %",
            "Promoter Holding — Total Nos.",
            "Promoter Holding — % of Total",
        ],
    },
    "BORROWINGS": {
        "title":      "Borrowings Disclosure — Security, Terms, Rate",
        "note_no":    5,
        "source_codes": ["EL010", "EL011", "EL012", "EL013", "EL014", "EL015",
                         "EL020", "EL021", "EL022", "EL023", "EL024"],
        "less_codes": [],
        "rows": [
            "Long-Term — Term Loans from Banks (Secured)",
            "Long-Term — Term Loans from Banks (Unsecured)",
            "Long-Term — Term Loans from FIs",
            "Long-Term — Bonds / Debentures",
            "Long-Term — Deposits",
            "Long-Term — Loans from Related Parties",
            "Long-Term — Others",
            "Short-Term — Cash Credit / OD",
            "Short-Term — Loans from Banks",
            "Short-Term — Current Maturities of LT Debt",
            "Short-Term — Loans from Directors / Related Parties",
            "Short-Term — Others",
        ],
    },
}


@dataclass
class AnnexureRow:
    label: str
    cy_value: float = 0.0
    py_value: float = 0.0


@dataclass
class AnnexureData:
    code: str                       # e.g. "TR_AGEING"
    title: str
    note_no: int
    tb_total_cy: float
    tb_total_py: float
    rows: list[AnnexureRow] = field(default_factory=list)
    variance_cy: float = 0.0
    variance_py: float = 0.0
    tolerance: float = 10.0
    is_balanced: bool = True

    def recompute(self):
        sum_cy = sum(r.cy_value for r in self.rows)
        sum_py = sum(r.py_value for r in self.rows)
        self.variance_cy = round(self.tb_total_cy - sum_cy, 2)
        self.variance_py = round(self.tb_total_py - sum_py, 2)
        self.is_balanced = (abs(self.variance_cy) <= self.tolerance and
                            abs(self.variance_py) <= self.tolerance)


def compute_tb_total(code: str, totals: dict[str, tuple[float, float]]) -> tuple[float, float]:
    """Sum CY and PY from totals for a specific annexure's source codes minus less_codes."""
    defn = ANNEXURE_DEFS.get(code)
    if not defn:
        return 0.0, 0.0
    cy = sum(totals.get(c, (0.0, 0.0))[0] for c in defn["source_codes"])
    py = sum(totals.get(c, (0.0, 0.0))[1] for c in defn["source_codes"])
    cy -= sum(totals.get(c, (0.0, 0.0))[0] for c in defn.get("less_codes", []))
    py -= sum(totals.get(c, (0.0, 0.0))[1] for c in defn.get("less_codes", []))
    return round(cy, 2), round(py, 2)


def build_blank_annexure(code: str, totals: dict[str, tuple[float, float]],
                         tolerance: float = 10.0) -> AnnexureData:
    """Construct a blank AnnexureData with TB totals + empty rows."""
    defn = ANNEXURE_DEFS[code]
    cy_total, py_total = compute_tb_total(code, totals)
    return AnnexureData(
        code        = code,
        title       = defn["title"],
        note_no     = defn["note_no"],
        tb_total_cy = cy_total,
        tb_total_py = py_total,
        rows        = [AnnexureRow(label=r) for r in defn["rows"]],
        tolerance   = tolerance,
    )


def load_annexure(code: str, db, totals: dict[str, tuple[float, float]],
                  tolerance: float = 10.0) -> AnnexureData:
    """Load existing annexure rows from note_data, or return blank if none saved."""
    defn = ANNEXURE_DEFS[code]
    note_no = defn["note_no"]
    annx = build_blank_annexure(code, totals, tolerance)
    rows = db.get_annexure_rows(code) if hasattr(db, "get_annexure_rows") else []
    if rows:
        by_label = {r["label"]: (r["cy_value"], r["py_value"]) for r in rows}
        for row in annx.rows:
            if row.label in by_label:
                row.cy_value = float(by_label[row.label][0] or 0)
                row.py_value = float(by_label[row.label][1] or 0)
    annx.recompute()
    return annx


def save_annexure(annx: AnnexureData, db):
    if hasattr(db, "save_annexure_rows"):
        db.save_annexure_rows(annx.code, [
            {"label": r.label, "cy_value": r.cy_value, "py_value": r.py_value}
            for r in annx.rows
        ])
