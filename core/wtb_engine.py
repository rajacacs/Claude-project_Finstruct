"""Working Trial Balance — compute, validate, aggregate.

Ported from Engine_WTB.gs logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from core.master_db import get_lookup_map, MappingEntry


@dataclass
class WTBLine:
    raw_tb_id: int
    ledger_name: str
    group_name: str
    mapping_code: str
    entry: MappingEntry | None
    confidence: float
    source: str
    cy_net: float
    py_net: float
    is_confirmed: bool


@dataclass
class ValidationResult:
    ok: bool
    balance_diff_cy: float = 0.0
    balance_diff_py: float = 0.0
    unmapped_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_wtb_lines(wtb_rows, raw_tb_rows) -> list[WTBLine]:
    lookup = get_lookup_map()
    raw_map = {r["id"]: r for r in raw_tb_rows}
    lines = []
    for w in wtb_rows:
        raw = raw_map.get(w["raw_tb_id"])
        entry = lookup.get(w["mapping_code"]) if w["mapping_code"] else None
        lines.append(WTBLine(
            raw_tb_id    = w["raw_tb_id"],
            ledger_name  = raw["ledger_name"] if raw else "",
            group_name   = raw["group_name"] if raw else "",
            mapping_code = w["mapping_code"] or "",
            entry        = entry,
            confidence   = w["confidence"] or 0.0,
            source       = w["confidence_source"] or "",
            cy_net       = w["cy_net"] or 0.0,
            py_net       = w["py_net"] or 0.0,
            is_confirmed = bool(w["is_confirmed"]),
        ))
    return lines


def aggregate_by_code(lines: list[WTBLine]) -> dict[str, tuple[float, float]]:
    """Sum CY and PY net amounts by mapping_code."""
    result: dict[str, list[float]] = {}
    for l in lines:
        if not l.mapping_code:
            continue
        result.setdefault(l.mapping_code, [0.0, 0.0])
        result[l.mapping_code][0] += l.cy_net
        result[l.mapping_code][1] += l.py_net
    return {k: (v[0], v[1]) for k, v in result.items()}


def apply_adjustments(
    totals: dict[str, tuple[float, float]],
    adj_rows: list,
    lookup: dict | None = None,
) -> dict[str, tuple[float, float]]:
    """Fold adjustment journal entries (dr/cr) into CY totals by mapping_code."""
    if lookup is None:
        from core.master_db import get_lookup_map
        lookup = get_lookup_map()
    result: dict[str, list[float]] = {k: list(v) for k, v in totals.items()}
    for adj in adj_rows:
        code = adj["mapping_code"] if adj["mapping_code"] else ""
        if not code:
            continue
        dr  = float(adj["dr_amount"] or 0)
        cr  = float(adj["cr_amount"] or 0)
        entry = lookup.get(code)
        net = (dr - cr) if (not entry or entry.sign == "DR_POSITIVE") else (cr - dr)
        if code not in result:
            result[code] = [0.0, 0.0]
        result[code][0] += net
    return {k: (v[0], v[1]) for k, v in result.items()}


def validate_balance(
    totals: dict[str, tuple[float, float]],
    entity_type: str,
) -> ValidationResult:
    """Check BS balance and P&L tie-out."""
    from core.master_db import MASTER

    lookup = get_lookup_map()
    bs_cy = 0.0
    bs_py = 0.0
    pl_net_cy = 0.0
    pl_net_py = 0.0

    for code, (cy, py) in totals.items():
        e = lookup.get(code)
        if not e:
            continue
        if e.fs_tag in ("BS",):
            sign = 1 if e.sign == "CR_POSITIVE" else -1
            bs_cy += sign * cy
            bs_py += sign * py
        elif e.fs_tag in ("PL", "IE"):
            sign = 1 if e.sign == "CR_POSITIVE" else -1
            pl_net_cy += sign * cy
            pl_net_py += sign * py

    errors = []
    warnings = []

    if abs(bs_cy) > 1:
        errors.append(f"BS does not balance — CY difference: ₹{bs_cy:,.2f}")
    if abs(bs_py) > 1:
        warnings.append(f"BS PY does not balance — difference: ₹{bs_py:,.2f}")

    return ValidationResult(
        ok              = not errors,
        balance_diff_cy = bs_cy,
        balance_diff_py = bs_py,
        errors          = errors,
        warnings        = warnings,
    )


def compute_net_from_raw(row: dict, sign: str) -> float:
    """Apply sign convention: DR_POSITIVE → cy_debit - cy_credit."""
    dr = float(row.get("cy_debit", 0) or 0)
    cr = float(row.get("cy_credit", 0) or 0)
    net = float(row.get("cy_net", 0) or 0)
    if net != 0:
        return net
    return (dr - cr) if sign == "DR_POSITIVE" else (cr - dr)
