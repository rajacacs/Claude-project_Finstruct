"""Validation checks — balance, completeness, small company criteria."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ValidationReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def fail(self, msg: str):
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)


def validate_mapping_complete(wtb_rows) -> ValidationReport:
    r = ValidationReport()
    unmapped = [row["ledger_name"] for row in wtb_rows
                if not row["mapping_code"] or not row["is_confirmed"]]
    if unmapped:
        r.fail(f"{len(unmapped)} ledger(s) not mapped/confirmed: {', '.join(unmapped[:5])}"
               + (" ..." if len(unmapped) > 5 else ""))
    return r


def validate_balance(totals: dict[str, tuple[float, float]],
                     entity_type: str) -> ValidationReport:
    from core.master_db import get_lookup_map
    r = ValidationReport()
    lm = get_lookup_map()
    bs_cy = bs_py = 0.0
    for code, (cy, py) in totals.items():
        e = lm.get(code)
        if not e or e.fs_tag != "BS":
            continue
        sign = 1 if e.sign == "CR_POSITIVE" else -1
        bs_cy += sign * cy
        bs_py += sign * py
    if abs(bs_cy) > 1:
        r.fail(f"Balance Sheet does not balance — CY difference: ₹{bs_cy:,.2f}")
    if abs(bs_py) > 1:
        r.warn(f"BS PY does not balance — difference: ₹{bs_py:,.2f}")
    return r


def is_small_company(paid_up_capital: float, turnover: float) -> bool:
    """Companies Act 2013 small company criteria (as amended 2021)."""
    return paid_up_capital <= 4_00_00_000 and turnover <= 40_00_00_000


def validate_cin(cin: str) -> bool:
    return len(cin.strip()) == 21 if cin.strip() else True


def validate_fy(fy: str) -> bool:
    import re
    return bool(re.match(r"^\d{4}-\d{2}$", fy.strip()))


def validate_pan(pan: str) -> bool:
    import re
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan.strip().upper())) if pan.strip() else True
