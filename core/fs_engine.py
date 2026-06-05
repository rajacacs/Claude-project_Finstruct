"""Financial Statement generation engine — all 8 entity types.

Ported from Engine_FS.gs, NCE_PROP, NCE_PART, NCE_AOP, NCE_NPO.
Produces structured FS line data; GUI and export layers render it.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

from core.master_db import get_lookup_map, MappingEntry


RowType = Literal["HEADER", "SECTION", "DATA", "SUBTOTAL", "TOTAL", "GRAND", "TEXT", "BLANK"]


@dataclass
class FSLine:
    label: str
    cy: float
    py: float
    note: int | None
    indent: int
    row_type: RowType
    code: str = ""


@dataclass
class FSDocument:
    entity_type: str
    fy: str
    entity_master: dict
    divisor: int
    bs: list[FSLine]    = field(default_factory=list)
    pl: list[FSLine]    = field(default_factory=list)
    ie: list[FSLine]    = field(default_factory=list)
    rp: list[FSLine]    = field(default_factory=list)
    cf: list[FSLine]    = field(default_factory=list)
    notes: dict[int, list[FSLine]] = field(default_factory=dict)
    is_balanced: bool   = True
    balance_diff_cy: float = 0.0


def _r(v: float, div: int) -> float:
    return round(v / div, 2) if div else v


def _line(label, cy, py, note=None, indent=0, row_type: RowType = "DATA", code="") -> FSLine:
    return FSLine(label, cy, py, note, indent, row_type, code)


def _sec(label) -> FSLine:
    return FSLine(label, 0, 0, None, 0, "SECTION")


def _hdr(label) -> FSLine:
    return FSLine(label, 0, 0, None, 0, "HEADER")


def _tot(label, cy, py, note=None) -> FSLine:
    return FSLine(label, cy, py, note, 0, "TOTAL")


def _grand(label, cy, py) -> FSLine:
    return FSLine(label, cy, py, None, 0, "GRAND")


def _blank() -> FSLine:
    return FSLine("", 0, 0, None, 0, "BLANK")


class FSEngine:
    def __init__(self, entity_type: str, totals: dict[str, tuple[float, float]],
                 entity_master: dict, fy: str, divisor: int = 1):
        self._etype   = entity_type
        self._totals  = totals         # {code: (cy_net, py_net)}
        self._master  = entity_master
        self._fy      = fy
        self._div     = divisor
        self._lookup  = get_lookup_map()

    def _cy(self, code: str) -> float:
        v = self._totals.get(code, (0.0, 0.0))[0]
        return _r(v, self._div)

    def _py(self, code: str) -> float:
        v = self._totals.get(code, (0.0, 0.0))[1]
        return _r(v, self._div)

    def _sum_cy(self, codes: list[str]) -> float:
        return round(sum(self._cy(c) for c in codes), 2)

    def _sum_py(self, codes: list[str]) -> float:
        return round(sum(self._py(c) for c in codes), 2)

    def generate(self, include_cf: bool = True) -> FSDocument:
        doc = FSDocument(self._etype, self._fy, self._master, self._div)
        if self._etype in ("COMPANY", "SEC8"):
            doc.bs = self._company_bs()
            if self._etype == "SEC8":
                doc.ie = self._sec8_ie()
            else:
                doc.pl = self._company_pl()
            if include_cf:
                doc.cf = self._company_cf()
        elif self._etype == "LLP":
            doc.bs = self._llp_bs()
            doc.pl = self._llp_pl()
        elif self._etype == "PROP":
            doc.bs = self._nce_bs()
            doc.pl = self._nce_pl(["NC", "NP"])
        elif self._etype == "PART":
            doc.bs = self._nce_bs()
            doc.pl = self._nce_pl(["NC", "NP"])
        elif self._etype == "AOP":
            doc.bs = self._aop_bs()
            doc.ie = self._aop_ie()
            doc.rp = self._aop_rp()
        elif self._etype == "TRUST":
            doc.bs = self._trust_bs()
            doc.ie = self._trust_ie()
            doc.rp = self._trust_rp()
        return doc

    # ─── COMPANY BALANCE SHEET (Schedule III Part I) ──────────────────────────

    def _company_bs(self) -> list[FSLine]:
        t = self._totals
        lines: list[FSLine] = []

        # Header
        lines += [_hdr("BALANCE SHEET")]

        # ── EQUITY & LIABILITIES ──────────────────────────────────────────
        lines.append(_sec("I.  EQUITY AND LIABILITIES"))

        # Shareholders' Funds
        lines.append(_line("1.  Shareholders' Funds", 0, 0, indent=1, row_type="SECTION"))
        sc_cy = self._cy("EL001") + self._cy("EL002")
        sc_py = self._py("EL001") + self._py("EL002")
        lines.append(_line("    (a) Share Capital", sc_cy, sc_py, note=3, indent=2))
        rs_cy = sum(self._cy(c) for c in ["EL003","EL004","EL005","EL006","EL007","EL008"])
        rs_py = sum(self._py(c) for c in ["EL003","EL004","EL005","EL006","EL007","EL008"])
        lines.append(_line("    (b) Reserves & Surplus", rs_cy, rs_py, note=4, indent=2))
        sam_cy = self._cy("EL009"); sam_py = self._py("EL009")
        lines.append(_line("    (c) Money received against Share Warrants", sam_cy, sam_py, indent=2))
        tot_sf_cy = sc_cy + rs_cy + sam_cy
        tot_sf_py = sc_py + rs_py + sam_py
        lines.append(_tot("    Sub-total — Shareholders' Funds (A)", tot_sf_cy, tot_sf_py))

        # Non-Current Liabilities
        lines.append(_line("2.  Non-Current Liabilities", 0, 0, indent=1, row_type="SECTION"))
        ltb_cy = self._sum_cy(["EL010","EL011","EL012","EL013","EL014","EL015"])
        ltb_py = self._sum_py(["EL010","EL011","EL012","EL013","EL014","EL015"])
        lines.append(_line("    (a) Long-term Borrowings", ltb_cy, ltb_py, note=5, indent=2))
        dtl_cy = self._cy("EL016"); dtl_py = self._py("EL016")
        lines.append(_line("    (b) Deferred Tax Liabilities (Net)", dtl_cy, dtl_py, indent=2))
        otl_cy = self._cy("EL017"); otl_py = self._py("EL017")
        lines.append(_line("    (c) Other Long-term Liabilities", otl_cy, otl_py, note=6, indent=2))
        ltp_cy = self._cy("EL018") + self._cy("EL019")
        ltp_py = self._py("EL018") + self._py("EL019")
        lines.append(_line("    (d) Long-term Provisions", ltp_cy, ltp_py, note=7, indent=2))
        tot_ncl_cy = ltb_cy + dtl_cy + otl_cy + ltp_cy
        tot_ncl_py = ltb_py + dtl_py + otl_py + ltp_py
        lines.append(_tot("    Sub-total — Non-Current Liabilities (B)", tot_ncl_cy, tot_ncl_py))

        # Current Liabilities
        lines.append(_line("3.  Current Liabilities", 0, 0, indent=1, row_type="SECTION"))
        stb_cy = self._sum_cy(["EL020","EL021","EL022","EL023","EL024"])
        stb_py = self._sum_py(["EL020","EL021","EL022","EL023","EL024"])
        lines.append(_line("    (a) Short-term Borrowings", stb_cy, stb_py, note=8, indent=2))
        tp_cy = self._cy("EL025") + self._cy("EL026")
        tp_py = self._py("EL025") + self._py("EL026")
        lines.append(_line("    (b) Trade Payables", tp_cy, tp_py, note=9, indent=2))
        ocl_cy = self._sum_cy(["EL027","EL028","EL029","EL030","EL031"])
        ocl_py = self._sum_py(["EL027","EL028","EL029","EL030","EL031"])
        lines.append(_line("    (c) Other Current Liabilities", ocl_cy, ocl_py, note=10, indent=2))
        stp_cy = self._sum_cy(["EL032","EL033","EL034"])
        stp_py = self._sum_py(["EL032","EL033","EL034"])
        lines.append(_line("    (d) Short-term Provisions", stp_cy, stp_py, note=11, indent=2))
        tot_cl_cy = stb_cy + tp_cy + ocl_cy + stp_cy
        tot_cl_py = stb_py + tp_py + ocl_py + stp_py
        lines.append(_tot("    Sub-total — Current Liabilities (C)", tot_cl_cy, tot_cl_py))

        tot_el_cy = tot_sf_cy + tot_ncl_cy + tot_cl_cy
        tot_el_py = tot_sf_py + tot_ncl_py + tot_cl_py
        lines.append(_grand("TOTAL — EQUITY AND LIABILITIES (A+B+C)", tot_el_cy, tot_el_py))

        # ── ASSETS ────────────────────────────────────────────────────────
        lines.append(_sec("II.  ASSETS"))

        # Non-Current Assets
        lines.append(_line("1.  Non-Current Assets", 0, 0, indent=1, row_type="SECTION"))
        ppe_gross = self._cy("AS001") + self._cy("AS004")
        ppe_dep   = self._cy("AS002") + self._cy("AS005")
        ppe_cwip  = self._cy("AS003")  # CWIP is not depreciated; added after net block calc
        ppe_net   = ppe_gross - ppe_dep + ppe_cwip
        ppe_gross_py = self._py("AS001") + self._py("AS004")
        ppe_dep_py   = self._py("AS002") + self._py("AS005")
        ppe_cwip_py  = self._py("AS003")
        ppe_net_py   = ppe_gross_py - ppe_dep_py + ppe_cwip_py
        lines.append(_line("    (a) Fixed Assets (Net Block)", ppe_net, ppe_net_py, note=12, indent=2))
        nci_cy = self._sum_cy(["AS006","AS007","AS008"])
        nci_py = self._sum_py(["AS006","AS007","AS008"])
        lines.append(_line("    (b) Non-Current Investments", nci_cy, nci_py, note=13, indent=2))
        dta_cy = self._cy("AS009"); dta_py = self._py("AS009")
        lines.append(_line("    (c) Deferred Tax Assets (Net)", dta_cy, dta_py, indent=2))
        ltla_cy = self._sum_cy(["AS010","AS011","AS012"])
        ltla_py = self._sum_py(["AS010","AS011","AS012"])
        lines.append(_line("    (d) Long-term Loans & Advances", ltla_cy, ltla_py, note=14, indent=2))
        onca_cy = self._cy("AS013") + self._cy("AS014")
        onca_py = self._py("AS013") + self._py("AS014")
        lines.append(_line("    (e) Other Non-Current Assets", onca_cy, onca_py, note=15, indent=2))
        tot_nca_cy = ppe_net + nci_cy + dta_cy + ltla_cy + onca_cy
        tot_nca_py = ppe_net_py + nci_py + dta_py + ltla_py + onca_py
        lines.append(_tot("    Sub-total — Non-Current Assets (D)", tot_nca_cy, tot_nca_py))

        # Current Assets
        lines.append(_line("2.  Current Assets", 0, 0, indent=1, row_type="SECTION"))
        inv_cy = self._sum_cy(["AS015","AS016","AS017","AS018","AS019"])
        inv_py = self._sum_py(["AS015","AS016","AS017","AS018","AS019"])
        lines.append(_line("    (a) Inventories", inv_cy, inv_py, note=16, indent=2))
        tr_cy  = self._cy("AS020") + self._cy("AS021") - self._cy("AS022")
        tr_py  = self._py("AS020") + self._py("AS021") - self._py("AS022")
        lines.append(_line("    (b) Trade Receivables", tr_cy, tr_py, note=17, indent=2))
        cash_cy = self._sum_cy(["AS023","AS024","AS025","AS026"])
        cash_py = self._sum_py(["AS023","AS024","AS025","AS026"])
        lines.append(_line("    (c) Cash and Cash Equivalents", cash_cy, cash_py, note=18, indent=2))
        stla_cy = self._sum_cy(["AS027","AS028","AS029","AS030"])
        stla_py = self._sum_py(["AS027","AS028","AS029","AS030"])
        lines.append(_line("    (d) Short-term Loans & Advances", stla_cy, stla_py, note=19, indent=2))
        oca_cy = self._cy("AS031") + self._cy("AS032") + self._cy("AS033")
        oca_py = self._py("AS031") + self._py("AS032") + self._py("AS033")
        lines.append(_line("    (e) Other Current Assets", oca_cy, oca_py, note=20, indent=2))
        tot_ca_cy = inv_cy + tr_cy + cash_cy + stla_cy + oca_cy
        tot_ca_py = inv_py + tr_py + cash_py + stla_py + oca_py
        lines.append(_tot("    Sub-total — Current Assets (E)", tot_ca_cy, tot_ca_py))

        tot_as_cy = tot_nca_cy + tot_ca_cy
        tot_as_py = tot_nca_py + tot_ca_py
        lines.append(_grand("TOTAL — ASSETS (D+E)", tot_as_cy, tot_as_py))

        diff_cy = round(tot_el_cy - tot_as_cy, 2)
        diff_py = round(tot_el_py - tot_as_py, 2)
        if abs(diff_cy) > 0.5:
            lines.append(_line(
                f"⚠ BS does not balance — CY diff: {diff_cy:,.2f}  PY diff: {diff_py:,.2f}",
                0, 0, row_type="TEXT"
            ))
        return lines

    # ─── COMPANY P&L (Schedule III Part II) ──────────────────────────────

    def _company_pl(self) -> list[FSLine]:
        lines: list[FSLine] = [_hdr("STATEMENT OF PROFIT AND LOSS"), _blank()]

        rev_cy = self._sum_cy(["PL001","PL002","PL003"]) - self._cy("PL004")
        rev_py = self._sum_py(["PL001","PL002","PL003"]) - self._py("PL004")
        lines.append(_line("I.   Revenue from Operations", rev_cy, rev_py, note=21, indent=1))
        oi_cy = self._sum_cy(["PL005","PL006","PL007","PL008","PL009"])
        oi_py = self._sum_py(["PL005","PL006","PL007","PL008","PL009"])
        lines.append(_line("II.  Other Income", oi_cy, oi_py, note=22, indent=1))
        tot_rev_cy = rev_cy + oi_cy
        tot_rev_py = rev_py + oi_py
        lines.append(_tot("III. Total Revenue (I + II)", tot_rev_cy, tot_rev_py))
        lines.append(_blank())

        lines.append(_line("IV.  Expenses:", 0, 0, row_type="SECTION"))
        cmc_cy = self._cy("PL010") + self._cy("PL011")
        cmc_py = self._py("PL010") + self._py("PL011")
        lines.append(_line("     Cost of Materials Consumed", cmc_cy, cmc_py, note=23, indent=2))
        pur_cy = self._cy("PL012"); pur_py = self._py("PL012")
        lines.append(_line("     Purchases of Stock-in-Trade", pur_cy, pur_py, note=24, indent=2))
        inv_ch_cy = self._sum_cy(["PL013","PL014"]) - self._sum_cy(["PL015","PL016"])
        inv_ch_py = self._sum_py(["PL013","PL014"]) - self._sum_py(["PL015","PL016"])
        lines.append(_line("     Changes in Inventories", inv_ch_cy, inv_ch_py, note=25, indent=2))
        emp_cy = self._sum_cy(["PL017","PL018","PL019","PL020","PL021"])
        emp_py = self._sum_py(["PL017","PL018","PL019","PL020","PL021"])
        lines.append(_line("     Employee Benefit Expenses", emp_cy, emp_py, note=26, indent=2))
        fin_cy = self._sum_cy(["PL022","PL023","PL024"])
        fin_py = self._sum_py(["PL022","PL023","PL024"])
        lines.append(_line("     Finance Costs", fin_cy, fin_py, note=27, indent=2))
        dep_cy = self._cy("PL025") + self._cy("PL026")
        dep_py = self._py("PL025") + self._py("PL026")
        lines.append(_line("     Depreciation & Amortisation", dep_cy, dep_py, note=28, indent=2))
        oe_cy = self._sum_cy([f"PL{i:03d}" for i in range(27,40)])
        oe_py = self._sum_py([f"PL{i:03d}" for i in range(27,40)])
        lines.append(_line("     Other Expenses", oe_cy, oe_py, note=29, indent=2))
        tot_exp_cy = cmc_cy + pur_cy + inv_ch_cy + emp_cy + fin_cy + dep_cy + oe_cy
        tot_exp_py = cmc_py + pur_py + inv_ch_py + emp_py + fin_py + dep_py + oe_py
        lines.append(_tot("     Total Expenses (IV)", tot_exp_cy, tot_exp_py))
        lines.append(_blank())

        pbt_cy = tot_rev_cy - tot_exp_cy
        pbt_py = tot_rev_py - tot_exp_py
        lines.append(_grand("V.   Profit/(Loss) before Tax (III – IV)", pbt_cy, pbt_py))
        tax_cy = self._cy("PL040") + self._cy("PL041")
        tax_py = self._py("PL040") + self._py("PL041")
        lines.append(_line("VI.  Tax Expense", tax_cy, tax_py, indent=1))
        pat_cy = pbt_cy - tax_cy
        pat_py = pbt_py - tax_py
        lines.append(_grand("VII. Profit/(Loss) after Tax (V – VI)", pat_cy, pat_py))
        return lines

    # ─── NCE BALANCE SHEET (Prop / Part / LLP) ────────────────────────────

    def _nce_bs(self) -> list[FSLine]:
        lines = [_hdr("BALANCE SHEET"), _blank()]

        lines.append(_sec("FUNDS & LIABILITIES"))
        cap_cy = self._sum_cy(["NC001","NC002"]) - self._cy("NC003")
        cap_py = self._sum_py(["NC001","NC002"]) - self._py("NC003")
        lines.append(_line("I.   Capital Account", cap_cy, cap_py, note=1, indent=1))
        res_cy = self._cy("NC004"); res_py = self._py("NC004")
        lines.append(_line("II.  Reserves & Surplus", res_cy, res_py, note=2, indent=1))
        sl_cy = self._cy("NC005");  sl_py = self._py("NC005")
        lines.append(_line("III. Secured Loans", sl_cy, sl_py, note=3, indent=1))
        ul_cy = self._cy("NC006");  ul_py = self._py("NC006")
        lines.append(_line("IV.  Unsecured Loans", ul_cy, ul_py, note=4, indent=1))
        tp_cy = self._cy("NC007");  tp_py = self._py("NC007")
        ocl_cy= self._sum_cy(["NC008","NC009","NC010"]); ocl_py = self._sum_py(["NC008","NC009","NC010"])
        prov_cy = self._cy("NC011"); prov_py = self._py("NC011")
        cl_cy  = tp_cy + ocl_cy + prov_cy
        cl_py  = tp_py + ocl_py + prov_py
        lines.append(_line("V.   Current Liabilities & Provisions", cl_cy, cl_py, note=5, indent=1))
        tot_fl_cy = cap_cy + res_cy + sl_cy + ul_cy + cl_cy
        tot_fl_py = cap_py + res_py + sl_py + ul_py + cl_py
        lines.append(_grand("TOTAL — FUNDS & LIABILITIES", tot_fl_cy, tot_fl_py))
        lines.append(_blank())

        lines.append(_sec("ASSETS"))
        fa_gross_cy = self._cy("NC012") + self._cy("NC013")
        fa_gross_py = self._py("NC012") + self._py("NC013")
        lines.append(_line("I.   Fixed Assets (Net Block)", fa_gross_cy, fa_gross_py, note=8, indent=1))
        inv_cy = self._cy("NC014"); inv_py = self._py("NC014")
        lines.append(_line("II.  Investments", inv_cy, inv_py, note=9, indent=1))
        cash_cy = self._cy("NC015") + self._cy("NC016")
        cash_py = self._py("NC015") + self._py("NC016")
        lines.append(_line("III. Cash & Bank Balances", cash_cy, cash_py, note=10, indent=1))
        stock_cy = self._cy("NC017"); stock_py = self._py("NC017")
        lines.append(_line("IV.  Inventories", stock_cy, stock_py, note=11, indent=1))
        tr_cy = self._cy("NC018");  tr_py = self._py("NC018")
        lines.append(_line("V.   Trade Receivables (Debtors)", tr_cy, tr_py, note=12, indent=1))
        la_cy = self._cy("NC019");  la_py = self._py("NC019")
        lines.append(_line("VI.  Loans & Advances", la_cy, la_py, note=13, indent=1))
        oca_cy = self._cy("NC020"); oca_py = self._py("NC020")
        lines.append(_line("VII. Other Current Assets", oca_cy, oca_py, note=14, indent=1))
        tot_as_cy = fa_gross_cy + inv_cy + cash_cy + stock_cy + tr_cy + la_cy + oca_cy
        tot_as_py = fa_gross_py + inv_py + cash_py + stock_py + tr_py + la_py + oca_py
        lines.append(_grand("TOTAL — ASSETS", tot_as_cy, tot_as_py))
        return lines

    def _nce_pl(self, prefixes: list[str]) -> list[FSLine]:
        lines = [_hdr("PROFIT AND LOSS ACCOUNT"), _blank()]
        rev_cy = self._cy("NP001"); rev_py = self._py("NP001")
        lines.append(_line("I.   Gross Revenue from Operations", rev_cy, rev_py, note=15, indent=1))
        oi_cy  = self._cy("NP002"); oi_py  = self._py("NP002")
        lines.append(_line("II.  Other Income", oi_cy, oi_py, note=16, indent=1))
        tot_i_cy = rev_cy + oi_cy; tot_i_py = rev_py + oi_py
        lines.append(_tot("III. Total Income", tot_i_cy, tot_i_py))
        lines.append(_blank())

        lines.append(_sec("IV.  Expenses:"))
        cog_cy = self._cy("NP003") + self._cy("NP004") - self._cy("NP005")
        cog_py = self._py("NP003") + self._py("NP004") - self._py("NP005")
        lines.append(_line("     Cost of Goods / Material", cog_cy, cog_py, note=17, indent=2))
        emp_cy = self._cy("NP006"); emp_py = self._py("NP006")
        lines.append(_line("     Employee Expenses", emp_cy, emp_py, note=18, indent=2))
        fin_cy = self._cy("NP007"); fin_py = self._py("NP007")
        lines.append(_line("     Finance Costs", fin_cy, fin_py, note=19, indent=2))
        dep_cy = self._cy("NP008"); dep_py = self._py("NP008")
        lines.append(_line("     Depreciation", dep_cy, dep_py, note=20, indent=2))
        oe_cy  = self._cy("NP009"); oe_py  = self._py("NP009")
        lines.append(_line("     Administrative & Other Expenses", oe_cy, oe_py, note=21, indent=2))
        tot_e_cy = cog_cy + emp_cy + fin_cy + dep_cy + oe_cy
        tot_e_py = cog_py + emp_py + fin_py + dep_py + oe_py
        lines.append(_tot("     Total Expenses", tot_e_cy, tot_e_py))
        lines.append(_blank())
        net_cy = tot_i_cy - tot_e_cy; net_py = tot_i_py - tot_e_py
        label = "V.   Net Profit / (Loss) for the year" if net_cy >= 0 else "V.   Net Loss for the year"
        lines.append(_grand(label, net_cy, net_py))
        return lines

    # ─── LLP BS ───────────────────────────────────────────────────────────

    def _llp_bs(self) -> list[FSLine]:
        lines = [_hdr("BALANCE SHEET"), _blank()]
        lines.append(_sec("FUNDS & LIABILITIES"))
        cap_cy = self._cy("LL001") + self._cy("LL002")
        cap_py = self._py("LL001") + self._py("LL002")
        lines.append(_line("I.   Partners' Capital Account", cap_cy, cap_py, note=1, indent=1))
        res_cy = self._cy("LL003"); res_py = self._py("LL003")
        lines.append(_line("II.  Reserves & Surplus", res_cy, res_py, note=2, indent=1))
        sl_cy  = self._cy("LL004"); sl_py  = self._py("LL004")
        lines.append(_line("III. Secured Loans", sl_cy, sl_py, note=3, indent=1))
        ul_cy  = self._cy("LL005") + self._cy("LL006")
        ul_py  = self._py("LL005") + self._py("LL006")
        lines.append(_line("IV.  Unsecured Loans", ul_cy, ul_py, note=4, indent=1))
        tp_cy  = self._cy("LL007"); tp_py  = self._py("LL007")
        ocl_cy = self._cy("LL008"); ocl_py = self._py("LL008")
        prov_cy= self._cy("LL009"); prov_py= self._py("LL009")
        cl_cy  = tp_cy + ocl_cy + prov_cy
        cl_py  = tp_py + ocl_py + prov_py
        lines.append(_line("V.   Current Liabilities & Provisions", cl_cy, cl_py, note=5, indent=1))
        tot_fl_cy = cap_cy + res_cy + sl_cy + ul_cy + cl_cy
        tot_fl_py = cap_py + res_py + sl_py + ul_py + cl_py
        lines.append(_grand("TOTAL — LIABILITIES", tot_fl_cy, tot_fl_py))
        lines.append(_blank())
        lines.append(_sec("ASSETS"))
        fa_cy = self._cy("LL010") + self._cy("LL011"); fa_py = self._py("LL010") + self._py("LL011")
        lines.append(_line("I.   Fixed Assets (Net Block)", fa_cy, fa_py, note=8, indent=1))
        inv_cy= self._cy("LL012"); inv_py = self._py("LL012")
        lines.append(_line("II.  Investments", inv_cy, inv_py, note=9, indent=1))
        cash_cy = self._cy("LL013") + self._cy("LL014"); cash_py = self._py("LL013") + self._py("LL014")
        lines.append(_line("III. Cash & Bank Balances", cash_cy, cash_py, note=10, indent=1))
        tr_cy = self._cy("LL015"); tr_py = self._py("LL015")
        lines.append(_line("IV.  Trade Receivables", tr_cy, tr_py, note=11, indent=1))
        la_cy = self._cy("LL016"); la_py = self._py("LL016")
        lines.append(_line("V.   Loans & Advances", la_cy, la_py, note=12, indent=1))
        oca_cy= self._cy("LL017"); oca_py= self._py("LL017")
        lines.append(_line("VI.  Other Current Assets", oca_cy, oca_py, note=13, indent=1))
        tot_as_cy = fa_cy + inv_cy + cash_cy + tr_cy + la_cy + oca_cy
        tot_as_py = fa_py + inv_py + cash_py + tr_py + la_py + oca_py
        lines.append(_grand("TOTAL — ASSETS", tot_as_cy, tot_as_py))
        return lines

    # ─── AOP / RWA ────────────────────────────────────────────────────────

    def _aop_bs(self) -> list[FSLine]:
        lines = [_hdr("BALANCE SHEET"), _blank()]
        lines.append(_sec("FUNDS & LIABILITIES"))
        cf_cy = self._cy("AO001"); cf_py = self._py("AO001")
        lines.append(_line("I.   Capital / Members' Fund", cf_cy, cf_py, note=1, indent=1))
        em_cy = self._cy("AO002") + self._cy("AO003"); em_py = self._py("AO002") + self._py("AO003")
        lines.append(_line("II.  Earmarked / Specific Funds", em_cy, em_py, note=2, indent=1))
        res_cy= self._cy("AO004"); res_py = self._py("AO004")
        lines.append(_line("III. Reserves & Surplus", res_cy, res_py, note=3, indent=1))
        sl_cy = self._cy("AO005"); sl_py = self._py("AO005")
        lines.append(_line("IV.  Secured Loans", sl_cy, sl_py, note=4, indent=1))
        dep_cy= self._cy("AO006"); dep_py = self._py("AO006")
        lines.append(_line("V.   Member Deposits (Refundable)", dep_cy, dep_py, note=5, indent=1))
        ocl_cy= self._cy("AO007") + self._cy("AO008"); ocl_py = self._py("AO007") + self._py("AO008")
        lines.append(_line("VI.  Other Current Liabilities", ocl_cy, ocl_py, note=6, indent=1))
        tot_fl_cy = cf_cy + em_cy + res_cy + sl_cy + dep_cy + ocl_cy
        tot_fl_py = cf_py + em_py + res_py + sl_py + dep_py + ocl_py
        lines.append(_grand("TOTAL (A)", tot_fl_cy, tot_fl_py))
        lines.append(_blank())
        lines.append(_sec("ASSETS"))
        fa_cy = self._cy("AO009"); fa_py = self._py("AO009")
        lines.append(_line("I.   Fixed Assets (Net Block)", fa_cy, fa_py, note=7, indent=1))
        inv_cy= self._cy("AO010"); inv_py = self._py("AO010")
        lines.append(_line("II.  Investments", inv_cy, inv_py, note=8, indent=1))
        cash_cy = self._cy("AO011") + self._cy("AO012"); cash_py = self._py("AO011") + self._py("AO012")
        lines.append(_line("III. Cash & Bank Balances", cash_cy, cash_py, note=9, indent=1))
        tr_cy = self._cy("AO013"); tr_py = self._py("AO013")
        lines.append(_line("IV.  Debtors (Maintenance Dues)", tr_cy, tr_py, note=10, indent=1))
        la_cy = self._cy("AO014"); la_py = self._py("AO014")
        lines.append(_line("V.   Loans & Advances", la_cy, la_py, note=11, indent=1))
        oca_cy= self._cy("AO015"); oca_py = self._py("AO015")
        lines.append(_line("VI.  Other Current Assets", oca_cy, oca_py, note=12, indent=1))
        tot_as_cy = fa_cy + inv_cy + cash_cy + tr_cy + la_cy + oca_cy
        tot_as_py = fa_py + inv_py + cash_py + tr_py + la_py + oca_py
        lines.append(_grand("TOTAL (B)", tot_as_cy, tot_as_py))
        return lines

    def _aop_ie(self) -> list[FSLine]:
        lines = [_hdr("INCOME AND EXPENDITURE ACCOUNT"), _blank()]
        lines.append(_sec("INCOME"))
        mi_cy = self._cy("AI001"); mi_py = self._py("AI001")
        lines.append(_line("I.   Maintenance Income", mi_cy, mi_py, note=13, indent=1))
        oi_cy = self._cy("AI002") + self._cy("AI003"); oi_py = self._py("AI002") + self._py("AI003")
        lines.append(_line("II.  Other Income", oi_cy, oi_py, note=14, indent=1))
        tot_i_cy = mi_cy + oi_cy; tot_i_py = mi_py + oi_py
        lines.append(_grand("TOTAL INCOME (I)", tot_i_cy, tot_i_py))
        lines.append(_blank())
        lines.append(_sec("EXPENDITURE"))
        est_cy = self._cy("AE001"); est_py = self._py("AE001")
        lines.append(_line("III. Establishment Expenses", est_cy, est_py, note=15, indent=1))
        me_cy  = self._cy("AE002"); me_py  = self._py("AE002")
        lines.append(_line("IV.  Maintenance Expenses", me_cy, me_py, note=16, indent=1))
        adm_cy = self._cy("AE003"); adm_py = self._py("AE003")
        lines.append(_line("V.   Administrative Expenses", adm_cy, adm_py, note=17, indent=1))
        dep_cy = self._cy("AE004"); dep_py = self._py("AE004")
        lines.append(_line("VI.  Depreciation", dep_cy, dep_py, note=18, indent=1))
        tot_e_cy = est_cy + me_cy + adm_cy + dep_cy
        tot_e_py = est_py + me_py + adm_py + dep_py
        lines.append(_grand("TOTAL EXPENDITURE (II)", tot_e_cy, tot_e_py))
        lines.append(_blank())
        sur_cy = tot_i_cy - tot_e_cy; sur_py = tot_i_py - tot_e_py
        label = "SURPLUS FOR THE YEAR (I–II)" if sur_cy >= 0 else "DEFICIT FOR THE YEAR (II–I)"
        lines.append(_grand(label, abs(sur_cy), abs(sur_py)))
        return lines

    def _aop_rp(self) -> list[FSLine]:
        lines = [_hdr("RECEIPT AND PAYMENT ACCOUNT"), _blank()]
        lines.append(_sec("RECEIPTS"))
        cash_op_cy = self._py("AO011") + self._py("AO012")
        lines.append(_line("Opening Balance (Cash & Bank)", cash_op_cy, 0, indent=1))
        mi_cy = self._cy("AI001")
        lines.append(_line("Maintenance Charges Received", mi_cy, 0, indent=1))
        oi_cy = self._cy("AI002") + self._cy("AI003")
        lines.append(_line("Other Receipts", oi_cy, 0, indent=1))
        tot_rec = cash_op_cy + mi_cy + oi_cy
        lines.append(_grand("TOTAL RECEIPTS (A)", tot_rec, 0))
        lines.append(_blank())
        lines.append(_sec("PAYMENTS"))
        est_cy = self._cy("AE001")
        lines.append(_line("Establishment Expenses", est_cy, 0, indent=1))
        me_cy  = self._cy("AE002")
        lines.append(_line("Maintenance Expenses", me_cy, 0, indent=1))
        adm_cy = self._cy("AE003")
        lines.append(_line("Administrative Expenses", adm_cy, 0, indent=1))
        cash_cl = self._cy("AO011") + self._cy("AO012")
        tot_pay = est_cy + me_cy + adm_cy + cash_cl
        lines.append(_line("Closing Balance (Cash & Bank)", cash_cl, 0, indent=1))
        lines.append(_grand("TOTAL PAYMENTS (B)", tot_pay, 0))
        return lines

    # ─── TRUST / NPO ──────────────────────────────────────────────────────

    def _trust_bs(self) -> list[FSLine]:
        lines = [_hdr("BALANCE SHEET"), _blank()]
        lines.append(_sec("CORPUS & LIABILITIES"))
        corp_cy = self._cy("TR001") + self._cy("TR002"); corp_py = self._py("TR001") + self._py("TR002")
        lines.append(_line("I.   Corpus Fund", corp_cy, corp_py, note=1, indent=1))
        em_cy = self._cy("TR003") + self._cy("TR004"); em_py = self._py("TR003") + self._py("TR004")
        lines.append(_line("II.  Earmarked Funds", em_cy, em_py, note=2, indent=1))
        loan_cy= self._cy("TR005"); loan_py = self._py("TR005")
        lines.append(_line("III. Loans & Liabilities", loan_cy, loan_py, note=3, indent=1))
        cl_cy  = self._cy("TR006"); cl_py   = self._py("TR006")
        lines.append(_line("IV.  Current Liabilities", cl_cy, cl_py, note=4, indent=1))
        tot_fl_cy = corp_cy + em_cy + loan_cy + cl_cy
        tot_fl_py = corp_py + em_py + loan_py + cl_py
        lines.append(_grand("TOTAL", tot_fl_cy, tot_fl_py))
        lines.append(_blank())
        lines.append(_sec("ASSETS"))
        fa_cy = self._cy("TR007"); fa_py = self._py("TR007")
        lines.append(_line("I.   Fixed Assets (Net Block)", fa_cy, fa_py, note=5, indent=1))
        inv_cy= self._cy("TR008"); inv_py = self._py("TR008")
        lines.append(_line("II.  Corpus Investments", inv_cy, inv_py, note=6, indent=1))
        cash_cy = self._cy("TR009") + self._cy("TR010"); cash_py = self._py("TR009") + self._py("TR010")
        lines.append(_line("III. Cash & Bank Balances", cash_cy, cash_py, note=7, indent=1))
        oca_cy = self._cy("TR011"); oca_py = self._py("TR011")
        lines.append(_line("IV.  Other Current Assets", oca_cy, oca_py, note=8, indent=1))
        tot_as_cy = fa_cy + inv_cy + cash_cy + oca_cy
        tot_as_py = fa_py + inv_py + cash_py + oca_py
        lines.append(_grand("TOTAL", tot_as_cy, tot_as_py))
        return lines

    def _trust_ie(self) -> list[FSLine]:
        lines = [_hdr("INCOME AND EXPENDITURE ACCOUNT"), _blank()]
        lines.append(_sec("INCOME"))
        don_cy = self._cy("TI001") + self._cy("TI002"); don_py = self._py("TI001") + self._py("TI002")
        lines.append(_line("I.   Donations & Grants", don_cy, don_py, note=9, indent=1))
        act_cy = self._cy("TI003"); act_py = self._py("TI003")
        lines.append(_line("II.  Income from Activities", act_cy, act_py, note=10, indent=1))
        oi_cy  = self._cy("TI004"); oi_py  = self._py("TI004")
        lines.append(_line("III. Interest & Investment Income", oi_cy, oi_py, note=11, indent=1))
        tot_i_cy = don_cy + act_cy + oi_cy; tot_i_py = don_py + act_py + oi_py
        lines.append(_grand("TOTAL INCOME (I)", tot_i_cy, tot_i_py))
        lines.append(_blank())
        lines.append(_sec("EXPENDITURE"))
        prog_cy = self._cy("TE001"); prog_py = self._py("TE001")
        lines.append(_line("IV.  Programme & Project Expenses", prog_cy, prog_py, note=12, indent=1))
        adm_cy = self._cy("TE002") + self._cy("TE003"); adm_py = self._py("TE002") + self._py("TE003")
        lines.append(_line("V.   Administrative Expenses", adm_cy, adm_py, note=13, indent=1))
        dep_cy = self._cy("TE004"); dep_py = self._py("TE004")
        lines.append(_line("VI.  Depreciation", dep_cy, dep_py, note=14, indent=1))
        tot_e_cy = prog_cy + adm_cy + dep_cy; tot_e_py = prog_py + adm_py + dep_py
        lines.append(_grand("TOTAL EXPENDITURE (II)", tot_e_cy, tot_e_py))
        sur_cy = tot_i_cy - tot_e_cy; sur_py = tot_i_py - tot_e_py
        label = "SURPLUS FOR THE YEAR" if sur_cy >= 0 else "DEFICIT FOR THE YEAR"
        lines.append(_grand(label, abs(sur_cy), abs(sur_py)))
        return lines

    def _trust_rp(self) -> list[FSLine]:
        lines = [_hdr("RECEIPT AND PAYMENT ACCOUNT"), _blank()]
        lines.append(_sec("RECEIPTS"))
        cash_op_cy = self._py("TR009") + self._py("TR010")
        lines.append(_line("Opening Balance (Cash & Bank)", cash_op_cy, 0, indent=1))
        don_cy = self._cy("TI001") + self._cy("TI002")
        lines.append(_line("Donations & Grants Received", don_cy, 0, indent=1))
        oi_cy = self._cy("TI003") + self._cy("TI004")
        lines.append(_line("Other Receipts", oi_cy, 0, indent=1))
        tot_rec = cash_op_cy + don_cy + oi_cy
        lines.append(_grand("TOTAL RECEIPTS", tot_rec, 0))
        lines.append(_blank())
        lines.append(_sec("PAYMENTS"))
        prog_cy = self._cy("TE001"); adm_cy = self._cy("TE002") + self._cy("TE003")
        lines.append(_line("Programme Expenses Paid", prog_cy, 0, indent=1))
        lines.append(_line("Administrative Expenses Paid", adm_cy, 0, indent=1))
        cash_cl = self._cy("TR009") + self._cy("TR010")
        lines.append(_line("Closing Balance (Cash & Bank)", cash_cl, 0, indent=1))
        tot_pay = prog_cy + adm_cy + cash_cl
        lines.append(_grand("TOTAL PAYMENTS", tot_pay, 0))
        return lines

    # ─── SEC8 INCOME & EXPENDITURE (reads PL codes, I&E presentation) ────────

    def _sec8_ie(self) -> list[FSLine]:
        lines = [_hdr("INCOME AND EXPENDITURE ACCOUNT"), _blank()]
        lines.append(_sec("INCOME"))
        rev_cy = self._sum_cy(["PL001","PL002","PL003"]) - self._cy("PL004")
        rev_py = self._sum_py(["PL001","PL002","PL003"]) - self._py("PL004")
        lines.append(_line("I.   Income from Activities", rev_cy, rev_py, note=21, indent=1))
        oi_cy  = self._sum_cy(["PL005","PL006","PL007","PL008","PL009"])
        oi_py  = self._sum_py(["PL005","PL006","PL007","PL008","PL009"])
        lines.append(_line("II.  Other Income", oi_cy, oi_py, note=22, indent=1))
        tot_i_cy = rev_cy + oi_cy; tot_i_py = rev_py + oi_py
        lines.append(_grand("TOTAL INCOME (I)", tot_i_cy, tot_i_py))
        lines.append(_blank())
        lines.append(_sec("EXPENDITURE"))
        emp_cy = self._sum_cy(["PL017","PL018","PL019","PL020","PL021"])
        emp_py = self._sum_py(["PL017","PL018","PL019","PL020","PL021"])
        lines.append(_line("III. Programme / Staff Expenses", emp_cy, emp_py, note=26, indent=1))
        fin_cy = self._sum_cy(["PL022","PL023","PL024"])
        fin_py = self._sum_py(["PL022","PL023","PL024"])
        lines.append(_line("IV.  Finance Costs", fin_cy, fin_py, note=27, indent=1))
        dep_cy = self._cy("PL025") + self._cy("PL026")
        dep_py = self._py("PL025") + self._py("PL026")
        lines.append(_line("V.   Depreciation & Amortisation", dep_cy, dep_py, note=28, indent=1))
        oe_cy  = self._sum_cy([f"PL{i:03d}" for i in range(27, 40)])
        oe_py  = self._sum_py([f"PL{i:03d}" for i in range(27, 40)])
        lines.append(_line("VI.  Other Expenses", oe_cy, oe_py, note=29, indent=1))
        tot_e_cy = emp_cy + fin_cy + dep_cy + oe_cy
        tot_e_py = emp_py + fin_py + dep_py + oe_py
        lines.append(_grand("TOTAL EXPENDITURE (II)", tot_e_cy, tot_e_py))
        lines.append(_blank())
        sur_cy = tot_i_cy - tot_e_cy; sur_py = tot_i_py - tot_e_py
        lbl = "SURPLUS FOR THE YEAR (I–II)" if sur_cy >= 0 else "DEFICIT FOR THE YEAR (II–I)"
        lines.append(_grand(lbl, abs(sur_cy), abs(sur_py)))
        return lines

    # ─── LLP PROFIT & LOSS (LL018–LL027 codes) ────────────────────────────────

    def _llp_pl(self) -> list[FSLine]:
        lines = [_hdr("PROFIT AND LOSS ACCOUNT"), _blank()]
        rev_cy = self._cy("LL018"); rev_py = self._py("LL018")
        lines.append(_line("I.   Revenue from Operations", rev_cy, rev_py, note=14, indent=1))
        oi_cy  = self._cy("LL019"); oi_py  = self._py("LL019")
        lines.append(_line("II.  Other Income", oi_cy, oi_py, note=15, indent=1))
        tot_i_cy = rev_cy + oi_cy; tot_i_py = rev_py + oi_py
        lines.append(_tot("III. Total Income", tot_i_cy, tot_i_py))
        lines.append(_blank())
        lines.append(_sec("IV.  Expenses:"))
        cog_cy = self._cy("LL020") + self._cy("LL021")
        cog_py = self._py("LL020") + self._py("LL021")
        lines.append(_line("     Cost of Goods / Materials", cog_cy, cog_py, note=16, indent=2))
        emp_cy = self._cy("LL022"); emp_py = self._py("LL022")
        lines.append(_line("     Employee Expenses", emp_cy, emp_py, note=17, indent=2))
        rem_cy = self._cy("LL023"); rem_py = self._py("LL023")
        lines.append(_line("     Partners' Remuneration", rem_cy, rem_py, note=18, indent=2))
        fin_cy = self._cy("LL024"); fin_py = self._py("LL024")
        lines.append(_line("     Finance Costs", fin_cy, fin_py, note=19, indent=2))
        dep_cy = self._cy("LL025"); dep_py = self._py("LL025")
        lines.append(_line("     Depreciation & Amortisation", dep_cy, dep_py, note=20, indent=2))
        oe_cy  = self._cy("LL026"); oe_py  = self._py("LL026")
        lines.append(_line("     Administrative & Other Expenses", oe_cy, oe_py, note=21, indent=2))
        tax_cy = self._cy("LL027"); tax_py = self._py("LL027")
        lines.append(_line("     Provision for Tax", tax_cy, tax_py, indent=2))
        tot_e_cy = cog_cy + emp_cy + rem_cy + fin_cy + dep_cy + oe_cy + tax_cy
        tot_e_py = cog_py + emp_py + rem_py + fin_py + dep_py + oe_py + tax_py
        lines.append(_tot("     Total Expenses", tot_e_cy, tot_e_py))
        lines.append(_blank())
        net_cy = tot_i_cy - tot_e_cy; net_py = tot_i_py - tot_e_py
        lbl = "V.   Net Profit for the year" if net_cy >= 0 else "V.   Net Loss for the year"
        lines.append(_grand(lbl, net_cy, net_py))
        return lines

    # ─── CASH FLOW STATEMENT (Indirect Method — COMPANY / SEC8) ──────────────

    def _company_cf(self) -> list[FSLine]:
        lines = [_hdr("CASH FLOW STATEMENT"), _blank()]
        lines.append(_line("(Prepared using the Indirect Method as per AS 3)", 0, 0,
                           row_type="TEXT"))
        lines.append(_blank())

        # ── Recalculate PBT from P&L codes ──────────────────────────────────
        rev_cy = self._sum_cy(["PL001","PL002","PL003"]) - self._cy("PL004")
        rev_py = self._sum_py(["PL001","PL002","PL003"]) - self._py("PL004")
        oi_cy  = self._sum_cy(["PL005","PL006","PL007","PL008","PL009"])
        oi_py  = self._sum_py(["PL005","PL006","PL007","PL008","PL009"])
        tot_rev_cy = rev_cy + oi_cy
        tot_rev_py = rev_py + oi_py

        cmc_cy = self._cy("PL010") + self._cy("PL011")
        cmc_py = self._py("PL010") + self._py("PL011")
        pur_cy = self._cy("PL012"); pur_py = self._py("PL012")
        inv_ch_cy = self._sum_cy(["PL013","PL014"]) - self._sum_cy(["PL015","PL016"])
        inv_ch_py = self._sum_py(["PL013","PL014"]) - self._sum_py(["PL015","PL016"])
        emp_cy = self._sum_cy(["PL017","PL018","PL019","PL020","PL021"])
        emp_py = self._sum_py(["PL017","PL018","PL019","PL020","PL021"])
        fin_cy = self._sum_cy(["PL022","PL023","PL024"])
        fin_py = self._sum_py(["PL022","PL023","PL024"])
        dep_cy = self._cy("PL025") + self._cy("PL026")
        dep_py = self._py("PL025") + self._py("PL026")
        oe_cy  = self._sum_cy([f"PL{i:03d}" for i in range(27, 40)])
        oe_py  = self._sum_py([f"PL{i:03d}" for i in range(27, 40)])
        tot_exp_cy = cmc_cy + pur_cy + inv_ch_cy + emp_cy + fin_cy + dep_cy + oe_cy
        tot_exp_py = cmc_py + pur_py + inv_ch_py + emp_py + fin_py + dep_py + oe_py

        pbt_cy = tot_rev_cy - tot_exp_cy
        pbt_py = tot_rev_py - tot_exp_py

        # PL005 = Interest Income; reclassify from operating to investing
        int_inc_cy = self._cy("PL005"); int_inc_py = self._py("PL005")

        # ── A. OPERATING ACTIVITIES ──────────────────────────────────────────
        lines.append(_sec("A.  CASH FLOW FROM OPERATING ACTIVITIES"))
        lines.append(_line("Net Profit / (Loss) before Tax", pbt_cy, pbt_py, indent=1))
        lines.append(_blank())
        lines.append(_line("Adjustments for:", 0, 0, row_type="SECTION", indent=1))
        lines.append(_line("  Add: Depreciation & Amortisation", dep_cy, dep_py, indent=2))
        lines.append(_line("  Add: Finance Costs", fin_cy, fin_py, indent=2))
        lines.append(_line("  Less: Interest Income (moved to Investing)", -int_inc_cy, -int_inc_py, indent=2))

        adj_cy = dep_cy + fin_cy - int_inc_cy
        adj_py = dep_py + fin_py - int_inc_py
        lines.append(_tot("  Total Adjustments", adj_cy, adj_py))
        lines.append(_blank())

        # Working capital changes — asset increases = cash outflow (negative)
        tr_cy  = self._cy("AS020") + self._cy("AS021") - self._cy("AS022")
        tr_py  = self._py("AS020") + self._py("AS021") - self._py("AS022")
        inv_ca_cy = self._sum_cy(["AS015","AS016","AS017","AS018","AS019"])
        inv_ca_py = self._sum_py(["AS015","AS016","AS017","AS018","AS019"])
        stla_cy = self._sum_cy(["AS027","AS028","AS029","AS030"])
        stla_py = self._sum_py(["AS027","AS028","AS029","AS030"])
        oca_cy  = self._cy("AS031") + self._cy("AS032") + self._cy("AS033")
        oca_py  = self._py("AS031") + self._py("AS032") + self._py("AS033")

        tp_cy   = self._cy("EL025") + self._cy("EL026")
        tp_py   = self._py("EL025") + self._py("EL026")
        ocl_cy  = self._sum_cy(["EL027","EL028","EL029","EL030","EL031"])
        ocl_py  = self._sum_py(["EL027","EL028","EL029","EL030","EL031"])
        stp_cy  = self._sum_cy(["EL032","EL033","EL034"])
        stp_py  = self._sum_py(["EL032","EL033","EL034"])

        d_tr_cy  = -(tr_cy - tr_py);    d_tr_py  = -(tr_py - 0)
        d_inv_cy = -(inv_ca_cy - inv_ca_py); d_inv_py = -(inv_ca_py - 0)
        d_stla_cy= -(stla_cy - stla_py); d_stla_py= -(stla_py - 0)
        d_oca_cy = -(oca_cy - oca_py);  d_oca_py = -(oca_py - 0)
        d_tp_cy  = tp_cy - tp_py;       d_tp_py  = tp_py - 0
        d_ocl_cy = ocl_cy - ocl_py;     d_ocl_py = ocl_py - 0
        d_stp_cy = stp_cy - stp_py;     d_stp_py = stp_py - 0

        wc_cy = d_tr_cy + d_inv_cy + d_stla_cy + d_oca_cy + d_tp_cy + d_ocl_cy + d_stp_cy
        wc_py = d_tr_py + d_inv_py + d_stla_py + d_oca_py + d_tp_py + d_ocl_py + d_stp_py

        lines.append(_line("Changes in Working Capital:", 0, 0, row_type="SECTION", indent=1))
        lines.append(_line("  (Increase)/Decrease in Trade Receivables",    d_tr_cy,  d_tr_py,  indent=2))
        lines.append(_line("  (Increase)/Decrease in Inventories",          d_inv_cy, d_inv_py, indent=2))
        lines.append(_line("  (Increase)/Decrease in Loans & Advances",     d_stla_cy,d_stla_py,indent=2))
        lines.append(_line("  (Increase)/Decrease in Other Current Assets", d_oca_cy, d_oca_py, indent=2))
        lines.append(_line("  Increase/(Decrease) in Trade Payables",       d_tp_cy,  d_tp_py,  indent=2))
        lines.append(_line("  Increase/(Decrease) in Other Current Liab.",  d_ocl_cy, d_ocl_py, indent=2))
        lines.append(_line("  Increase/(Decrease) in Short-term Provisions",d_stp_cy, d_stp_py, indent=2))
        lines.append(_tot("  Net Working Capital Changes", wc_cy, wc_py))
        lines.append(_blank())

        tax_cy = self._cy("PL040"); tax_py = self._py("PL040")
        lines.append(_line("Less: Direct Taxes Paid (Net of Refunds)", -tax_cy, -tax_py, indent=1))
        cf_op_cy = round(pbt_cy + adj_cy + wc_cy - tax_cy, 2)
        cf_op_py = round(pbt_py + adj_py + wc_py - tax_py, 2)
        lines.append(_grand("Net Cash from/(used in) Operating Activities (A)", cf_op_cy, cf_op_py))
        lines.append(_blank())

        # ── B. INVESTING ACTIVITIES ──────────────────────────────────────────
        lines.append(_sec("B.  CASH FLOW FROM INVESTING ACTIVITIES"))

        # Capex: increase in gross fixed assets = outflow
        ppe_gross_cy = self._cy("AS001") + self._cy("AS004")
        ppe_gross_py = self._py("AS001") + self._py("AS004")
        capex_cy = -(ppe_gross_cy - ppe_gross_py)
        capex_py = -(ppe_gross_py - 0)

        nci_cy = self._sum_cy(["AS006","AS007","AS008"])
        nci_py = self._sum_py(["AS006","AS007","AS008"])
        d_invest_cy = -(nci_cy - nci_py)
        d_invest_py = -(nci_py - 0)

        lines.append(_line("Purchase of Fixed Assets (including CWIP)", capex_cy, capex_py, indent=1))
        lines.append(_line("Purchase/(Sale) of Investments (Net)",       d_invest_cy, d_invest_py, indent=1))
        lines.append(_line("Interest Received",                          int_inc_cy, int_inc_py, indent=1))

        cf_inv_cy = round(capex_cy + d_invest_cy + int_inc_cy, 2)
        cf_inv_py = round(capex_py + d_invest_py + int_inc_py, 2)
        lines.append(_grand("Net Cash from/(used in) Investing Activities (B)", cf_inv_cy, cf_inv_py))
        lines.append(_blank())

        # ── C. FINANCING ACTIVITIES ──────────────────────────────────────────
        lines.append(_sec("C.  CASH FLOW FROM FINANCING ACTIVITIES"))

        ltb_cy = self._sum_cy(["EL010","EL011","EL012","EL013","EL014","EL015"])
        ltb_py = self._sum_py(["EL010","EL011","EL012","EL013","EL014","EL015"])
        stb_cy = self._sum_cy(["EL020","EL021","EL022","EL023","EL024"])
        stb_py = self._sum_py(["EL020","EL021","EL022","EL023","EL024"])
        d_ltb_cy = ltb_cy - ltb_py
        d_stb_cy = stb_cy - stb_py
        div_cy  = self._cy("EL008"); div_py = self._py("EL008")

        lines.append(_line("Proceeds from/(Repayment of) Long-term Borrowings (Net)",   d_ltb_cy, 0, indent=1))
        lines.append(_line("Proceeds from/(Repayment of) Short-term Borrowings (Net)",  d_stb_cy, 0, indent=1))
        lines.append(_line("Finance Costs Paid",                                         -fin_cy,  -fin_py, indent=1))
        lines.append(_line("Dividends Paid",                                             -div_cy,  -div_py, indent=1))

        cf_fin_cy = round(d_ltb_cy + d_stb_cy - fin_cy - div_cy, 2)
        cf_fin_py = round(-fin_py - div_py, 2)
        lines.append(_grand("Net Cash from/(used in) Financing Activities (C)", cf_fin_cy, cf_fin_py))
        lines.append(_blank())

        # ── RECONCILIATION ───────────────────────────────────────────────────
        net_cf_cy = round(cf_op_cy + cf_inv_cy + cf_fin_cy, 2)
        net_cf_py = round(cf_op_py + cf_inv_py + cf_fin_py, 2)
        lines.append(_grand("Net Increase/(Decrease) in Cash (A+B+C)", net_cf_cy, net_cf_py))

        cash_cl_cy  = self._sum_cy(["AS023","AS024","AS025","AS026"])
        cash_op_val = self._sum_py(["AS023","AS024","AS025","AS026"])
        lines.append(_line("Add: Opening Cash & Cash Equivalents", cash_op_val, 0, indent=1))
        lines.append(_grand("Closing Cash & Cash Equivalents", cash_cl_cy, 0))

        diff = round(net_cf_cy - (cash_cl_cy - cash_op_val), 2)
        if abs(diff) > 0.5:
            lines.append(_line(
                f"⚠ CF reconciliation gap: {diff:,.2f} — check disposal proceeds & other adjustments",
                0, 0, row_type="TEXT"
            ))
        return lines
