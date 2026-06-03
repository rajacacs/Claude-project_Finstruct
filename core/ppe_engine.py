"""PPE Register engine — SLM/WDV depreciation, IT schedule."""

from __future__ import annotations
from ..config import PPE_USEFUL_LIFE, PPE_IT_RATES


def calc_slm(gross_op: float, additions: float, disposals: float,
             dep_op: float, dep_disposal: float,
             rate: float | None = None, life_yrs: int = 10) -> dict:
    gross_cl = gross_op + additions - disposals
    annual_dep = gross_cl / life_yrs if life_yrs else 0
    dep_charge = round(annual_dep, 2)
    dep_cl = dep_op + dep_charge - dep_disposal
    nbv_cy = gross_cl - dep_cl
    return {"gross_cl": gross_cl, "dep_charge": dep_charge,
            "dep_cl": dep_cl, "nbv_cy": nbv_cy}


def calc_wdv(gross_op: float, additions: float, disposals: float,
             dep_op: float, dep_disposal: float,
             rate: float = 15.0) -> dict:
    gross_cl = gross_op + additions - disposals
    wdv = gross_op - dep_op
    dep_charge = round(wdv * rate / 100, 2)
    dep_cl = dep_op + dep_charge - dep_disposal
    nbv_cy = gross_cl - dep_cl
    return {"gross_cl": gross_cl, "dep_charge": dep_charge,
            "dep_cl": dep_cl, "nbv_cy": nbv_cy}


def calc_it_dep(it_wdv_op: float, it_add_gt180: float, it_add_lt180: float,
                it_del_gt180: float, it_del_lt180: float, rate: float) -> dict:
    full = max(0, (it_wdv_op + it_add_gt180 - it_del_lt180) * rate / 100)
    half = max(0, (it_add_lt180 - it_del_gt180) * rate / 100 * 0.5)
    total = round(full + half, 2)
    cl = max(0, it_wdv_op + it_add_gt180 + it_add_lt180 - it_del_gt180 - it_del_lt180 - total)
    return {"it_dep_full": full, "it_dep_half": half, "it_dep": total, "it_wdv_cl": cl}


def recalc_asset(asset: dict) -> dict:
    method = asset.get("method", "SLM").upper()
    cat    = asset.get("category", "")
    life   = int(asset.get("useful_life_yrs") or PPE_USEFUL_LIFE.get(cat, 10))
    rate   = float(asset.get("it_rate") or PPE_IT_RATES.get(cat, 15))

    gross_op   = float(asset.get("gross_op", 0))
    additions  = float(asset.get("additions", 0))
    disposals  = float(asset.get("disposals", 0))
    dep_op     = float(asset.get("dep_op", 0))
    dep_disp   = float(asset.get("dep_disposal", 0))

    if method == "WDV":
        res = calc_wdv(gross_op, additions, disposals, dep_op, dep_disp, rate)
    else:
        res = calc_slm(gross_op, additions, disposals, dep_op, dep_disp, life_yrs=life)

    it = calc_it_dep(
        float(asset.get("it_wdv_op", 0)), additions, 0, 0, 0, rate
    )
    return {**asset, **res, **it,
            "useful_life_yrs": life, "it_rate": rate}


def summarize_ppe(assets: list[dict]) -> dict:
    """Return totals for PPE note."""
    totals = {k: 0.0 for k in ["gross_op","additions","disposals","gross_cl",
                                 "dep_op","dep_charge","dep_disposal","dep_cl",
                                 "nbv_cy","nbv_py","it_dep"]}
    for a in assets:
        r = recalc_asset(a)
        totals["gross_op"]   += r.get("gross_op", 0)
        totals["additions"]  += r.get("additions", 0)
        totals["disposals"]  += r.get("disposals", 0)
        totals["gross_cl"]   += r.get("gross_cl", 0)
        totals["dep_op"]     += r.get("dep_op", 0)
        totals["dep_charge"] += r.get("dep_charge", 0)
        totals["dep_disposal"]+= r.get("dep_disposal", 0)
        totals["dep_cl"]     += r.get("dep_cl", 0)
        totals["nbv_cy"]     += r.get("nbv_cy", 0)
        totals["nbv_py"]     += float(a.get("nbv_py", 0))
        totals["it_dep"]     += r.get("it_dep", 0)
    return totals
