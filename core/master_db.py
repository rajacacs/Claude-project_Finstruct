"""Schedule III + ICAI NCE mapping master — static reference data.

Ported from MasterDB.gs (Companies Act / Schedule III) and
NCE config files (PROP, PART, AOP, NPO entity types).
"""

from __future__ import annotations
from collections.abc import Iterable
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal


from core.entity_types import EntityType

FsTag = Literal["BS", "PL", "IE", "RP"]
SignConvention = Literal["DR_POSITIVE", "CR_POSITIVE"]

VALID_ENTITY_TYPES = frozenset(et.value for et in EntityType)
VALID_ENTITY_TAGS = VALID_ENTITY_TYPES | {"ALL", "NCE", "NPO"}
VALID_FS_TAGS = frozenset({"BS", "PL", "IE", "RP"})
VALID_SIGNS = frozenset({"DR_POSITIVE", "CR_POSITIVE"})


@dataclass(frozen=True, slots=True)
class MappingEntry:
    code: str
    entity_types: tuple[str, ...]   # ("COMPANY","SEC8") or ("ALL",) or ("NCE",...)
    group: str
    heading: str
    sub_heading: str
    fs_tag: FsTag             # BS | PL | IE | RP
    sign: SignConvention      # DR_POSITIVE | CR_POSITIVE
    note_number: int | None
    small_co_exempt: bool
    parent_code: str | None = None  # Added for hierarchy
    lookup_name: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "code", self.code.strip().upper())
        object.__setattr__(self, "entity_types", tuple(dict.fromkeys(self.entity_types)))
        object.__setattr__(self, "group", self.group.strip())
        object.__setattr__(self, "heading", self.heading.strip())
        object.__setattr__(self, "sub_heading", self.sub_heading.strip())
        object.__setattr__(self, "fs_tag", self.fs_tag.strip().upper())
        object.__setattr__(self, "sign", self.sign.strip().upper())
        object.__setattr__(
            self,
            "lookup_name",
            f"{self.group} > {self.heading} > {self.sub_heading}",
        )


def _e(
    code: str,
    types: Iterable[str],
    grp: str,
    hdg: str,
    sub: str,
    tag: FsTag,
    sign: SignConvention = "DR_POSITIVE",
    note: int | None = None,
    sc_exempt: bool = False,
    parent: str | None = None,
) -> MappingEntry:
    return MappingEntry(code, tuple(types), grp, hdg, sub, tag, sign, note, sc_exempt, parent)


CO  = [EntityType.COMPANY.value, EntityType.SEC8.value]
NCE = [EntityType.LLP.value, EntityType.PROP.value, EntityType.PART.value]
AOP = [EntityType.AOP.value]
NPO = [EntityType.TRUST.value]
ALL = [et.value for et in EntityType]


MASTER: list[MappingEntry] = [

    # ─── SCHEDULE III — EQUITY & LIABILITIES ──────────────────────────────

    # Shareholders' Funds
    _e("EL001", CO,  "Shareholders Funds", "Share Capital", "Equity Share Capital",          "BS", "CR_POSITIVE", 3),
    _e("EL002", CO,  "Shareholders Funds", "Share Capital", "Preference Share Capital",       "BS", "CR_POSITIVE", 3),
    _e("EL003", CO,  "Shareholders Funds", "Reserves & Surplus", "Capital Reserve",           "BS", "CR_POSITIVE", 4),
    _e("EL004", CO,  "Shareholders Funds", "Reserves & Surplus", "Capital Redemption Reserve","BS", "CR_POSITIVE", 4),
    _e("EL005", CO,  "Shareholders Funds", "Reserves & Surplus", "Securities Premium Reserve","BS", "CR_POSITIVE", 4),
    _e("EL006", CO,  "Shareholders Funds", "Reserves & Surplus", "General Reserve",           "BS", "CR_POSITIVE", 4),
    _e("EL007", CO,  "Shareholders Funds", "Reserves & Surplus", "Retained Earnings / Surplus in P&L", "BS", "CR_POSITIVE", 4),
    _e("EL008", CO,  "Shareholders Funds", "Reserves & Surplus", "Other Reserves",            "BS", "CR_POSITIVE", 4),
    _e("EL009", CO,  "Shareholders Funds", "Share App Money Pending Allotment", "Share Application Money", "BS", "CR_POSITIVE"),

    # Non-Current Liabilities
    _e("EL010", CO,  "Non-Current Liabilities", "Long Term Borrowings", "Term Loans from Banks",                "BS", "CR_POSITIVE", 5),
    _e("EL011", CO,  "Non-Current Liabilities", "Long Term Borrowings", "Term Loans from Financial Institutions","BS", "CR_POSITIVE", 5),
    _e("EL012", CO,  "Non-Current Liabilities", "Long Term Borrowings", "Bonds / Debentures",                   "BS", "CR_POSITIVE", 5),
    _e("EL013", CO,  "Non-Current Liabilities", "Long Term Borrowings", "Deposits",                             "BS", "CR_POSITIVE", 5),
    _e("EL014", CO,  "Non-Current Liabilities", "Long Term Borrowings", "Loans from Related Parties",           "BS", "CR_POSITIVE", 5),
    _e("EL015", CO,  "Non-Current Liabilities", "Long Term Borrowings", "Other Long Term Borrowings",           "BS", "CR_POSITIVE", 5),
    _e("EL016", CO,  "Non-Current Liabilities", "Deferred Tax Liability", "Deferred Tax Liability (Net)",       "BS", "CR_POSITIVE"),
    _e("EL017", CO,  "Non-Current Liabilities", "Other Long Term Liabilities", "Other Long Term Liabilities",   "BS", "CR_POSITIVE", 6),
    _e("EL018", CO,  "Non-Current Liabilities", "Long Term Provisions", "Provision for Employee Benefits",      "BS", "CR_POSITIVE", 7),
    _e("EL019", CO,  "Non-Current Liabilities", "Long Term Provisions", "Other Long Term Provisions",           "BS", "CR_POSITIVE", 7),

    # Current Liabilities
    _e("EL020", CO,  "Current Liabilities", "Short Term Borrowings", "Cash Credit / OD from Banks",             "BS", "CR_POSITIVE", 8),
    _e("EL021", CO,  "Current Liabilities", "Short Term Borrowings", "Short Term Loans from Banks",             "BS", "CR_POSITIVE", 8),
    _e("EL022", CO,  "Current Liabilities", "Short Term Borrowings", "Current Maturities of LT Debt",           "BS", "CR_POSITIVE", 8),
    _e("EL023", CO,  "Current Liabilities", "Short Term Borrowings", "Loans from Directors / Related Parties",  "BS", "CR_POSITIVE", 8),
    _e("EL024", CO,  "Current Liabilities", "Short Term Borrowings", "Other Short Term Borrowings",             "BS", "CR_POSITIVE", 8),
    _e("EL025", CO,  "Current Liabilities", "Trade Payables", "Trade Payables – MSME",                          "BS", "CR_POSITIVE", 9),
    _e("EL026", CO,  "Current Liabilities", "Trade Payables", "Trade Payables – Others",                        "BS", "CR_POSITIVE", 9),
    _e("EL027", CO,  "Current Liabilities", "Other Current Liabilities", "Advance from Customers",              "BS", "CR_POSITIVE", 10),
    _e("EL028", CO,  "Current Liabilities", "Other Current Liabilities", "Statutory Dues Payable",              "BS", "CR_POSITIVE", 10),
    _e("EL029", CO,  "Current Liabilities", "Other Current Liabilities", "Employee Related Payables",           "BS", "CR_POSITIVE", 10),
    _e("EL030", CO,  "Current Liabilities", "Other Current Liabilities", "Interest Accrued & Due",              "BS", "CR_POSITIVE", 10),
    _e("EL031", CO,  "Current Liabilities", "Other Current Liabilities", "Other Payables",                      "BS", "CR_POSITIVE", 10),
    _e("EL032", CO,  "Current Liabilities", "Short Term Provisions", "Provision for Tax (Current Year)",        "BS", "CR_POSITIVE", 11),
    _e("EL033", CO,  "Current Liabilities", "Short Term Provisions", "Provision for Dividend",                  "BS", "CR_POSITIVE", 11),
    _e("EL034", CO,  "Current Liabilities", "Short Term Provisions", "Other Short Term Provisions",             "BS", "CR_POSITIVE", 11),

    # ─── SCHEDULE III — ASSETS ───────────────────────────────────────────

    # Non-Current Assets
    _e("AS001", CO,  "Non-Current Assets", "Property Plant & Equipment", "Tangible Assets – Gross Block",       "BS", "DR_POSITIVE", 12),
    _e("AS002", CO,  "Non-Current Assets", "Property Plant & Equipment", "Less: Accumulated Depreciation",      "BS", "CR_POSITIVE", 12),
    _e("AS003", CO,  "Non-Current Assets", "Property Plant & Equipment", "Capital Work-in-Progress",             "BS", "DR_POSITIVE", 12),
    _e("AS004", CO,  "Non-Current Assets", "Intangible Assets", "Intangible Assets – Gross Block",              "BS", "DR_POSITIVE", 12),
    _e("AS005", CO,  "Non-Current Assets", "Intangible Assets", "Less: Accumulated Amortisation",               "BS", "CR_POSITIVE", 12),
    _e("AS006", CO,  "Non-Current Assets", "Non-Current Investments", "Investment in Subsidiaries",             "BS", "DR_POSITIVE", 13),
    _e("AS007", CO,  "Non-Current Assets", "Non-Current Investments", "Investment in Associates",               "BS", "DR_POSITIVE", 13),
    _e("AS008", CO,  "Non-Current Assets", "Non-Current Investments", "Other Long Term Investments",            "BS", "DR_POSITIVE", 13),
    _e("AS009", CO,  "Non-Current Assets", "Deferred Tax Asset", "Deferred Tax Asset (Net)",                   "BS", "DR_POSITIVE"),
    _e("AS010", CO,  "Non-Current Assets", "Long Term Loans & Advances", "Security Deposits",                   "BS", "DR_POSITIVE", 14),
    _e("AS011", CO,  "Non-Current Assets", "Long Term Loans & Advances", "Loans to Subsidiaries/Related Parties","BS","DR_POSITIVE",14),
    _e("AS012", CO,  "Non-Current Assets", "Long Term Loans & Advances", "Other Long Term Loans & Advances",    "BS", "DR_POSITIVE", 14),
    _e("AS013", CO,  "Non-Current Assets", "Other Non-Current Assets", "Long Term Trade Receivables",           "BS", "DR_POSITIVE", 15),
    _e("AS014", CO,  "Non-Current Assets", "Other Non-Current Assets", "Other Non-Current Assets",             "BS", "DR_POSITIVE", 15),

    # Current Assets
    _e("AS015", CO,  "Current Assets", "Inventories", "Raw Materials",                                          "BS", "DR_POSITIVE", 16),
    _e("AS016", CO,  "Current Assets", "Inventories", "Work-in-Progress",                                       "BS", "DR_POSITIVE", 16),
    _e("AS017", CO,  "Current Assets", "Inventories", "Finished Goods",                                         "BS", "DR_POSITIVE", 16),
    _e("AS018", CO,  "Current Assets", "Inventories", "Stock-in-Trade",                                         "BS", "DR_POSITIVE", 16),
    _e("AS019", CO,  "Current Assets", "Inventories", "Stores & Spares",                                        "BS", "DR_POSITIVE", 16),
    _e("AS020", CO,  "Current Assets", "Trade Receivables", "Trade Receivables – Outstanding > 6 months",       "BS", "DR_POSITIVE", 17),
    _e("AS021", CO,  "Current Assets", "Trade Receivables", "Trade Receivables – Outstanding ≤ 6 months",       "BS", "DR_POSITIVE", 17),
    _e("AS022", CO,  "Current Assets", "Trade Receivables", "Less: Provision for Doubtful Debts",               "BS", "CR_POSITIVE", 17),
    _e("AS023", CO,  "Current Assets", "Cash & Cash Equivalents", "Cash in Hand",                               "BS", "DR_POSITIVE", 18),
    _e("AS024", CO,  "Current Assets", "Cash & Cash Equivalents", "Balances with Banks – Current A/c",          "BS", "DR_POSITIVE", 18),
    _e("AS025", CO,  "Current Assets", "Cash & Cash Equivalents", "Balances with Banks – Savings A/c",          "BS", "DR_POSITIVE", 18),
    _e("AS026", CO,  "Current Assets", "Cash & Cash Equivalents", "Fixed Deposits (< 3 months)",                "BS", "DR_POSITIVE", 18),
    _e("AS027", CO,  "Current Assets", "Short Term Loans & Advances", "Advance to Suppliers",                   "BS", "DR_POSITIVE", 19),
    _e("AS028", CO,  "Current Assets", "Short Term Loans & Advances", "Prepaid Expenses",                       "BS", "DR_POSITIVE", 19),
    _e("AS029", CO,  "Current Assets", "Short Term Loans & Advances", "Advance Tax / TDS Receivable",           "BS", "DR_POSITIVE", 19),
    _e("AS030", CO,  "Current Assets", "Short Term Loans & Advances", "Other Short Term Loans & Advances",      "BS", "DR_POSITIVE", 19),
    _e("AS031", CO,  "Current Assets", "Other Current Assets", "Interest Accrued on FDs",                       "BS", "DR_POSITIVE", 20),
    _e("AS032", CO,  "Current Assets", "Other Current Assets", "GST Receivable / Input Tax Credit",             "BS", "DR_POSITIVE", 20),
    _e("AS033", CO,  "Current Assets", "Other Current Assets", "Other Current Assets",                          "BS", "DR_POSITIVE", 20),

    # ─── SCHEDULE III — PROFIT & LOSS ────────────────────────────────────

    _e("PL001", CO,  "Revenue", "Revenue from Operations", "Sale of Products",                                  "PL", "CR_POSITIVE", 21),
    _e("PL002", CO,  "Revenue", "Revenue from Operations", "Sale of Services",                                  "PL", "CR_POSITIVE", 21),
    _e("PL003", CO,  "Revenue", "Revenue from Operations", "Other Operating Revenue",                           "PL", "CR_POSITIVE", 21),
    _e("PL004", CO,  "Revenue", "Revenue from Operations", "Less: Excise Duty / GST (if applicable)",           "PL", "DR_POSITIVE", 21),
    _e("PL005", CO,  "Revenue", "Other Income", "Interest Income",                                              "PL", "CR_POSITIVE", 22),
    _e("PL006", CO,  "Revenue", "Other Income", "Dividend Income",                                              "PL", "CR_POSITIVE", 22),
    _e("PL007", CO,  "Revenue", "Other Income", "Profit on Sale of Assets",                                     "PL", "CR_POSITIVE", 22),
    _e("PL008", CO,  "Revenue", "Other Income", "Rental Income",                                                "PL", "CR_POSITIVE", 22),
    _e("PL009", CO,  "Revenue", "Other Income", "Miscellaneous Income",                                         "PL", "CR_POSITIVE", 22),
    _e("PL010", CO,  "Expenses", "Cost of Materials Consumed", "Raw Material Consumed",                         "PL", "DR_POSITIVE", 23),
    _e("PL011", CO,  "Expenses", "Cost of Materials Consumed", "Packing Material Consumed",                     "PL", "DR_POSITIVE", 23),
    _e("PL012", CO,  "Expenses", "Purchases of Stock-in-Trade", "Purchases – Trading Goods",                    "PL", "DR_POSITIVE", 24),
    _e("PL013", CO,  "Expenses", "Changes in Inventories", "Opening Stock – Finished Goods",                    "PL", "DR_POSITIVE", 25),
    _e("PL014", CO,  "Expenses", "Changes in Inventories", "Opening Stock – WIP",                               "PL", "DR_POSITIVE", 25),
    _e("PL015", CO,  "Expenses", "Changes in Inventories", "Less: Closing Stock – Finished Goods",              "PL", "CR_POSITIVE", 25),
    _e("PL016", CO,  "Expenses", "Changes in Inventories", "Less: Closing Stock – WIP",                         "PL", "CR_POSITIVE", 25),
    _e("PL017", CO,  "Expenses", "Employee Benefit Expenses", "Salaries & Wages",                               "PL", "DR_POSITIVE", 26),
    _e("PL018", CO,  "Expenses", "Employee Benefit Expenses", "Bonus",                                          "PL", "DR_POSITIVE", 26),
    _e("PL019", CO,  "Expenses", "Employee Benefit Expenses", "PF / ESI Contribution",                          "PL", "DR_POSITIVE", 26),
    _e("PL020", CO,  "Expenses", "Employee Benefit Expenses", "Gratuity Expense",                               "PL", "DR_POSITIVE", 26),
    _e("PL021", CO,  "Expenses", "Employee Benefit Expenses", "Staff Welfare",                                   "PL", "DR_POSITIVE", 26),
    _e("PL022", CO,  "Expenses", "Finance Costs", "Interest on Term Loans",                                     "PL", "DR_POSITIVE", 27),
    _e("PL023", CO,  "Expenses", "Finance Costs", "Interest on CC / OD",                                        "PL", "DR_POSITIVE", 27),
    _e("PL024", CO,  "Expenses", "Finance Costs", "Bank Charges",                                               "PL", "DR_POSITIVE", 27),
    _e("PL025", CO,  "Expenses", "Depreciation & Amortisation", "Depreciation – Tangible Assets",              "PL", "DR_POSITIVE", 28),
    _e("PL026", CO,  "Expenses", "Depreciation & Amortisation", "Amortisation – Intangible Assets",            "PL", "DR_POSITIVE", 28),
    _e("PL027", CO,  "Expenses", "Other Expenses", "Power & Fuel",                                              "PL", "DR_POSITIVE", 29),
    _e("PL028", CO,  "Expenses", "Other Expenses", "Rent",                                                      "PL", "DR_POSITIVE", 29),
    _e("PL029", CO,  "Expenses", "Other Expenses", "Repairs & Maintenance",                                     "PL", "DR_POSITIVE", 29),
    _e("PL030", CO,  "Expenses", "Other Expenses", "Insurance",                                                 "PL", "DR_POSITIVE", 29),
    _e("PL031", CO,  "Expenses", "Other Expenses", "Printing & Stationery",                                     "PL", "DR_POSITIVE", 29),
    _e("PL032", CO,  "Expenses", "Other Expenses", "Travelling & Conveyance",                                   "PL", "DR_POSITIVE", 29),
    _e("PL033", CO,  "Expenses", "Other Expenses", "Communication Expenses",                                    "PL", "DR_POSITIVE", 29),
    _e("PL034", CO,  "Expenses", "Other Expenses", "Professional & Legal Fees",                                 "PL", "DR_POSITIVE", 29),
    _e("PL035", CO,  "Expenses", "Other Expenses", "Audit Fees",                                                "PL", "DR_POSITIVE", 29),
    _e("PL036", CO,  "Expenses", "Other Expenses", "Advertisement & Sales Promotion",                           "PL", "DR_POSITIVE", 29),
    _e("PL037", CO,  "Expenses", "Other Expenses", "GST / Taxes & Duties",                                      "PL", "DR_POSITIVE", 29),
    _e("PL038", CO,  "Expenses", "Other Expenses", "Bad Debts Written Off",                                     "PL", "DR_POSITIVE", 29),
    _e("PL039", CO,  "Expenses", "Other Expenses", "Miscellaneous Expenses",                                    "PL", "DR_POSITIVE", 29),
    _e("PL021A", CO, "Expenses", "Employee Benefit Expenses", "Commission to Employees",                        "PL", "DR_POSITIVE", 26),
    _e("PL021B", CO, "Expenses", "Employee Benefit Expenses", "Leave Encashment Expense",                       "PL", "DR_POSITIVE", 26),
    _e("PL040", CO,  "Tax", "Current Tax", "Current Income Tax",                                                "PL", "DR_POSITIVE"),
    _e("PL041", CO,  "Tax", "Deferred Tax", "Deferred Tax (Charge) / Credit",                                  "PL", "DR_POSITIVE"),

    # ─── LLP FORMAT ───────────────────────────────────────────────────────

    _e("LL001", ["LLP"], "Partners' Capital", "Partners' Capital Account", "Capital Contribution",              "BS", "CR_POSITIVE", 1),
    _e("LL002", ["LLP"], "Partners' Capital", "Partners' Capital Account", "Accumulated Profit / (Loss)",       "BS", "CR_POSITIVE", 1),
    _e("LL003", ["LLP"], "Reserves & Surplus", "Reserves & Surplus", "General Reserve",                        "BS", "CR_POSITIVE", 2),
    _e("LL004", ["LLP"], "Loans", "Secured Loans", "Loans from Banks (Secured)",                                "BS", "CR_POSITIVE", 3),
    _e("LL005", ["LLP"], "Loans", "Unsecured Loans", "Loans from Partners",                                     "BS", "CR_POSITIVE", 4),
    _e("LL006", ["LLP"], "Loans", "Unsecured Loans", "Other Unsecured Loans",                                   "BS", "CR_POSITIVE", 4),
    _e("LL007", ["LLP"], "Current Liabilities", "Trade Payables", "Creditors for Goods",                        "BS", "CR_POSITIVE", 5),
    _e("LL008", ["LLP"], "Current Liabilities", "Other Current Liabilities", "Other Payables",                  "BS", "CR_POSITIVE", 6),
    _e("LL009", ["LLP"], "Current Liabilities", "Provisions", "Provision for Tax",                              "BS", "CR_POSITIVE", 7),
    _e("LL010", ["LLP"], "Fixed Assets", "Fixed Assets", "Tangible Assets (Net Block)",                         "BS", "DR_POSITIVE", 8),
    _e("LL011", ["LLP"], "Fixed Assets", "Fixed Assets", "Intangible Assets (Net Block)",                       "BS", "DR_POSITIVE", 8),
    _e("LL012", ["LLP"], "Investments", "Long-Term Investments", "Investments",                                  "BS", "DR_POSITIVE", 9),
    _e("LL013", ["LLP"], "Current Assets", "Cash & Bank", "Cash in Hand",                                       "BS", "DR_POSITIVE", 10),
    _e("LL014", ["LLP"], "Current Assets", "Cash & Bank", "Bank Balances",                                      "BS", "DR_POSITIVE", 10),
    _e("LL015", ["LLP"], "Current Assets", "Debtors", "Trade Receivables",                                      "BS", "DR_POSITIVE", 11),
    _e("LL016", ["LLP"], "Current Assets", "Loans & Advances", "Loans & Advances",                              "BS", "DR_POSITIVE", 12),
    _e("LL017", ["LLP"], "Current Assets", "Other Current Assets", "Other Current Assets",                      "BS", "DR_POSITIVE", 13),

    # LLP P&L (ICAI Guidance Note — LLP Financial Statements)
    _e("LL018", ["LLP"], "Revenue", "Revenue from Operations", "Sale of Products / Services",                   "PL", "CR_POSITIVE", 14),
    _e("LL019", ["LLP"], "Revenue", "Other Income", "Interest & Other Income",                                  "PL", "CR_POSITIVE", 15),
    _e("LL020", ["LLP"], "Expenses", "Cost of Materials / Purchases", "Cost of Goods Sold / Purchases",         "PL", "DR_POSITIVE", 16),
    _e("LL021", ["LLP"], "Expenses", "Changes in Inventories", "Inventory Change (Opening – Closing)",          "PL", "DR_POSITIVE", 16),
    _e("LL022", ["LLP"], "Expenses", "Employee Benefit Expenses", "Salaries, Wages & Staff Costs",              "PL", "DR_POSITIVE", 17),
    _e("LL023", ["LLP"], "Expenses", "Partners' Remuneration", "Remuneration to Designated Partners",           "PL", "DR_POSITIVE", 18),
    _e("LL024", ["LLP"], "Expenses", "Finance Costs", "Interest & Finance Charges",                             "PL", "DR_POSITIVE", 19),
    _e("LL025", ["LLP"], "Expenses", "Depreciation & Amortisation", "Depreciation & Amortisation",             "PL", "DR_POSITIVE", 20),
    _e("LL026", ["LLP"], "Expenses", "Other Expenses", "Administrative & Other Expenses",                       "PL", "DR_POSITIVE", 21),
    _e("LL027", ["LLP"], "Tax",      "Provision for Tax", "Income Tax Provision",                               "PL", "DR_POSITIVE"),

    # ─── NCE PROP / PART FORMAT ───────────────────────────────────────────

    _e("NC001", NCE,  "Capital", "Capital Account", "Capital as at Beginning",                                   "BS", "CR_POSITIVE", 1),
    _e("NC002", NCE,  "Capital", "Capital Account", "Add: Net Profit for the Year",                              "BS", "CR_POSITIVE", 1),
    _e("NC003", NCE,  "Capital", "Capital Account", "Less: Drawings",                                            "BS", "DR_POSITIVE", 1),
    _e("NC004", NCE,  "Reserves & Surplus", "Reserves & Surplus", "General Reserve",                            "BS", "CR_POSITIVE", 2),
    _e("NC005", NCE,  "Loans", "Secured Loans", "Secured Loans",                                                 "BS", "CR_POSITIVE", 3),
    _e("NC006", NCE,  "Loans", "Unsecured Loans", "Unsecured Loans",                                             "BS", "CR_POSITIVE", 4),
    _e("NC007", NCE,  "Current Liabilities", "Trade Payables", "Creditors for Goods & Services",                 "BS", "CR_POSITIVE", 5),
    _e("NC008", NCE,  "Current Liabilities", "Other Current Liabilities", "Outstanding Expenses",                "BS", "CR_POSITIVE", 6),
    _e("NC009", NCE,  "Current Liabilities", "Other Current Liabilities", "Advance from Customers",              "BS", "CR_POSITIVE", 6),
    _e("NC010", NCE,  "Current Liabilities", "Other Current Liabilities", "Statutory Dues",                      "BS", "CR_POSITIVE", 6),
    _e("NC011", NCE,  "Current Liabilities", "Provisions", "Provision for Tax",                                  "BS", "CR_POSITIVE", 7),
    _e("NC012", NCE,  "Fixed Assets", "Fixed Assets", "Tangible Fixed Assets (Net Block)",                       "BS", "DR_POSITIVE", 8),
    _e("NC013", NCE,  "Fixed Assets", "Fixed Assets", "Intangible Assets (Net Block)",                           "BS", "DR_POSITIVE", 8),
    _e("NC014", NCE,  "Investments", "Long-Term Investments", "Long-Term Investments",                            "BS", "DR_POSITIVE", 9),
    _e("NC015", NCE,  "Current Assets", "Cash & Bank", "Cash in Hand",                                           "BS", "DR_POSITIVE", 10),
    _e("NC016", NCE,  "Current Assets", "Cash & Bank", "Bank Balances",                                          "BS", "DR_POSITIVE", 10),
    _e("NC017", NCE,  "Current Assets", "Inventories", "Stock-in-Trade",                                         "BS", "DR_POSITIVE", 11),
    _e("NC018", NCE,  "Current Assets", "Trade Receivables", "Trade Receivables (Debtors)",                      "BS", "DR_POSITIVE", 12),
    _e("NC019", NCE,  "Current Assets", "Loans & Advances", "Loans & Advances",                                  "BS", "DR_POSITIVE", 13),
    _e("NC020", NCE,  "Current Assets", "Other Current Assets", "Other Current Assets",                          "BS", "DR_POSITIVE", 14),

    # NCE P&L
    _e("NP001", NCE,  "Revenue", "Gross Revenue", "Sales / Turnover",                                            "PL", "CR_POSITIVE", 15),
    _e("NP002", NCE,  "Revenue", "Other Income", "Other Income",                                                 "PL", "CR_POSITIVE", 16),
    _e("NP003", NCE,  "Expenses", "Cost of Goods", "Opening Stock",                                              "PL", "DR_POSITIVE", 17),
    _e("NP004", NCE,  "Expenses", "Cost of Goods", "Purchases",                                                  "PL", "DR_POSITIVE", 17),
    _e("NP005", NCE,  "Expenses", "Cost of Goods", "Less: Closing Stock",                                        "PL", "CR_POSITIVE", 17),
    _e("NP006", NCE,  "Expenses", "Employee Expenses", "Salaries & Wages",                                       "PL", "DR_POSITIVE", 18),
    _e("NP007", NCE,  "Expenses", "Finance Costs", "Interest & Finance Charges",                                 "PL", "DR_POSITIVE", 19),
    _e("NP008", NCE,  "Expenses", "Depreciation", "Depreciation",                                                "PL", "DR_POSITIVE", 20),
    _e("NP009", NCE,  "Expenses", "Other Expenses", "Administrative & Other Expenses",                           "PL", "DR_POSITIVE", 21),

    # PROP-specific expanded BS — Capital Work-in-Progress and Intangibles as separate entries
    _e("PR001", ["PROP"], "Fixed Assets", "Capital Work-in-Progress", "Capital Work-in-Progress",               "BS", "DR_POSITIVE", 10),
    _e("PR002", ["PROP"], "Fixed Assets", "Intangible Assets", "Intangible Assets (Net Block)",                  "BS", "DR_POSITIVE", 10),
    _e("PR003", ["PROP"], "Non-Current Assets", "Long-Term Loans & Advances", "Security Deposits & Advances",   "BS", "DR_POSITIVE", 13),
    _e("PR004", ["PROP"], "Non-Current Assets", "Other Non-Current Assets", "Other Non-Current Assets",         "BS", "DR_POSITIVE", 14),
    _e("PR005", ["PROP"], "Current Liabilities", "Long-Term Borrowings", "Long-Term Borrowings (secured)",      "BS", "CR_POSITIVE", 4),
    _e("PR006", ["PROP"], "Current Liabilities", "Long-Term Provisions", "Long-Term Provisions",                "BS", "CR_POSITIVE", 5),

    # PART-specific capital accounts (separate from generic NC001 capital)
    _e("PT001", ["PART"], "Partners' Capital", "Partners' Fixed Capital", "Fixed Capital Accounts",             "BS", "CR_POSITIVE", 2),
    _e("PT002", ["PART"], "Partners' Capital", "Partners' Current Account", "Current Accounts (Fluctuating)",   "BS", "CR_POSITIVE", 3),
    _e("PT003", ["PART"], "Partners' Capital", "Partners' Capital Accounts", "Capital Accounts (Fluctuating)",  "BS", "CR_POSITIVE", 2),
    _e("PT004", ["PART"], "Appropriation", "Partners' Remuneration", "Remuneration to Partners (Sec 40b)",      "PL", "DR_POSITIVE", 25),
    _e("PT005", ["PART"], "Appropriation", "Interest on Capital", "Interest on Partners' Capital",              "PL", "DR_POSITIVE", 29),
    _e("PT006", ["PART"], "Appropriation", "Profit Appropriation", "Share of Profit per Partner",               "PL", "DR_POSITIVE", 29),
    _e("PT007", ["PART"], "Tax", "Provision for Income Tax", "Current Tax (@ 30% + surcharge)",                 "PL", "DR_POSITIVE", 10),

    # ─── AOP / RWA FORMAT ──────────────────────────────────────────────────

    _e("AO001", AOP, "Capital / Members Fund", "Capital Fund", "Members' Capital Fund (Opening)",                "BS", "CR_POSITIVE", 1),
    _e("AO002", AOP, "Earmarked Funds", "Earmarked Funds", "Sinking Fund",                                       "BS", "CR_POSITIVE", 2),
    _e("AO003", AOP, "Earmarked Funds", "Earmarked Funds", "Development Fund",                                   "BS", "CR_POSITIVE", 2),
    _e("AO004", AOP, "Reserves & Surplus", "Reserves & Surplus", "General Reserve",                              "BS", "CR_POSITIVE", 3),
    _e("AO005", AOP, "Loans", "Secured Loans", "Secured Loans",                                                  "BS", "CR_POSITIVE", 4),
    _e("AO006", AOP, "Loans", "Unsecured Loans", "Member Deposits (Refundable)",                                 "BS", "CR_POSITIVE", 5),
    _e("AO007", AOP, "Current Liabilities", "Other Current Liabilities", "Outstanding Expenses",                 "BS", "CR_POSITIVE", 6),
    _e("AO008", AOP, "Current Liabilities", "Other Current Liabilities", "Advance from Members",                 "BS", "CR_POSITIVE", 6),
    _e("AO009", AOP, "Fixed Assets", "Fixed Assets", "Fixed Assets (Net Block)",                                 "BS", "DR_POSITIVE", 7),
    _e("AO010", AOP, "Investments", "Long-Term Investments", "Investments – FDs / Bonds",                        "BS", "DR_POSITIVE", 8),
    _e("AO011", AOP, "Current Assets", "Cash & Bank", "Cash in Hand",                                            "BS", "DR_POSITIVE", 9),
    _e("AO012", AOP, "Current Assets", "Cash & Bank", "Bank Balances",                                           "BS", "DR_POSITIVE", 9),
    _e("AO013", AOP, "Current Assets", "Debtors", "Maintenance Dues Receivable",                                 "BS", "DR_POSITIVE", 10),
    _e("AO014", AOP, "Current Assets", "Loans & Advances", "Loans & Advances",                                   "BS", "DR_POSITIVE", 11),
    _e("AO015", AOP, "Current Assets", "Other Current Assets", "Other Current Assets",                           "BS", "DR_POSITIVE", 12),

    # AOP I&E
    _e("AI001", AOP, "Income", "Maintenance Income", "Maintenance Charges Collected",                            "IE", "CR_POSITIVE", 13),
    _e("AI002", AOP, "Income", "Other Income", "Interest on FDs",                                               "IE", "CR_POSITIVE", 14),
    _e("AI003", AOP, "Income", "Other Income", "Other Receipts",                                                 "IE", "CR_POSITIVE", 14),
    _e("AE001", AOP, "Expenditure", "Establishment Expenses", "Salaries & Staff Expenses",                       "IE", "DR_POSITIVE", 15),
    _e("AE002", AOP, "Expenditure", "Maintenance Expenses", "Common Area Maintenance",                           "IE", "DR_POSITIVE", 16),
    _e("AE003", AOP, "Expenditure", "Administrative Expenses", "Administrative & Other Expenses",                "IE", "DR_POSITIVE", 17),
    _e("AE004", AOP, "Expenditure", "Depreciation", "Depreciation",                                             "IE", "DR_POSITIVE", 18),

    # AOP expanded I&E sub-lines
    _e("AI010", AOP, "Income", "Maintenance Income", "Car Parking / Other Charges",                             "IE", "CR_POSITIVE", 15),
    _e("AI011", AOP, "Income", "Maintenance Income", "Sub-letting / Hall Rental Income",                        "IE", "CR_POSITIVE", 15),
    _e("AE010", AOP, "Expenditure", "Establishment Expenses", "Security & Housekeeping",                        "IE", "DR_POSITIVE", 17),
    _e("AE011", AOP, "Expenditure", "Establishment Expenses", "Electricity – Common Areas",                     "IE", "DR_POSITIVE", 17),
    _e("AE012", AOP, "Expenditure", "Maintenance Expenses", "Lift / Pump Maintenance",                          "IE", "DR_POSITIVE", 18),
    _e("AE013", AOP, "Expenditure", "Maintenance Expenses", "Civil Repairs & Upkeep",                           "IE", "DR_POSITIVE", 18),
    _e("AE014", AOP, "Expenditure", "Administrative Expenses", "Printing, Postage & Stationery",                "IE", "DR_POSITIVE", 19),
    _e("AE015", AOP, "Expenditure", "Administrative Expenses", "Audit Fees",                                    "IE", "DR_POSITIVE", 19),

    # ─── TRUST / NPO FORMAT ───────────────────────────────────────────────

    _e("TR001", NPO, "Corpus Fund", "Corpus Fund", "Corpus Contributions",                                       "BS", "CR_POSITIVE", 1),
    _e("TR002", NPO, "Corpus Fund", "Corpus Fund", "Accumulated Surplus",                                        "BS", "CR_POSITIVE", 1),
    _e("TR003", NPO, "Earmarked Funds", "Specific Funds", "Building Fund",                                       "BS", "CR_POSITIVE", 2),
    _e("TR004", NPO, "Earmarked Funds", "Specific Funds", "Education Fund",                                      "BS", "CR_POSITIVE", 2),
    _e("TR005", NPO, "Loans", "Unsecured Loans", "Loans from Donors/Trustees",                                   "BS", "CR_POSITIVE", 3),
    _e("TR006", NPO, "Current Liabilities", "Current Liabilities", "Outstanding Expenses",                       "BS", "CR_POSITIVE", 4),
    _e("TR007", NPO, "Fixed Assets", "Fixed Assets", "Fixed Assets (Net Block)",                                 "BS", "DR_POSITIVE", 5),
    _e("TR008", NPO, "Investments", "Investments", "Corpus Investments (FDs/Bonds)",                             "BS", "DR_POSITIVE", 6),
    _e("TR009", NPO, "Current Assets", "Cash & Bank", "Cash in Hand",                                            "BS", "DR_POSITIVE", 7),
    _e("TR010", NPO, "Current Assets", "Cash & Bank", "Bank Balances",                                           "BS", "DR_POSITIVE", 7),
    _e("TR011", NPO, "Current Assets", "Other Current Assets", "Receivables & Other Assets",                    "BS", "DR_POSITIVE", 8),

    # Trust I&E
    _e("TI001", NPO, "Income", "Donations & Grants", "Corpus Donations",                                         "IE", "CR_POSITIVE", 9),
    _e("TI002", NPO, "Income", "Donations & Grants", "General Donations",                                        "IE", "CR_POSITIVE", 9),
    _e("TI003", NPO, "Income", "Income from Activities", "Fees / Course Charges",                                "IE", "CR_POSITIVE", 10),
    _e("TI004", NPO, "Income", "Other Income", "Interest & Investment Income",                                   "IE", "CR_POSITIVE", 11),
    _e("TE001", NPO, "Expenditure", "Programme Expenses", "Programme & Project Expenses",                        "IE", "DR_POSITIVE", 12),
    _e("TE002", NPO, "Expenditure", "Administrative Expenses", "Staff Costs",                                    "IE", "DR_POSITIVE", 13),
    _e("TE003", NPO, "Expenditure", "Administrative Expenses", "Administrative & Office Expenses",               "IE", "DR_POSITIVE", 13),
    _e("TE004", NPO, "Expenditure", "Depreciation", "Depreciation",                                             "IE", "DR_POSITIVE", 14),

    # NPO/Trust expanded BS codes
    _e("TR020", NPO, "Capital Grants", "Capital Grants Received", "Capital Grants – Deferred (Govt / CSR)",     "BS", "CR_POSITIVE", 5),
    _e("TR021", NPO, "Investments", "Corpus Investments", "Corpus Investments – FDs / Bonds / Equity",          "BS", "DR_POSITIVE", 10),
    _e("TR022", NPO, "Investments", "Other Investments", "Other Investments (non-corpus)",                       "BS", "DR_POSITIVE", 11),
    _e("TR023", NPO, "Current Assets", "Cash & Bank", "FCRA Bank Account (separate)",                           "BS", "DR_POSITIVE", 12),
    _e("TR024", NPO, "Current Assets", "Debtors", "Grants Receivable",                                          "BS", "DR_POSITIVE", 13),
    _e("TR025", NPO, "Current Assets", "Loans & Advances", "Loans & Advances – Programme",                      "BS", "DR_POSITIVE", 14),
    _e("TR026", NPO, "Loans", "Secured Loans", "Secured Loans – Banks",                                         "BS", "CR_POSITIVE", 6),

    # NPO/Trust expanded I&E codes
    _e("TI010", NPO, "Income", "Revenue Grants", "Government / State Grants",                                   "IE", "CR_POSITIVE", 16),
    _e("TI011", NPO, "Income", "Revenue Grants", "CSR Funding from Corporates",                                  "IE", "CR_POSITIVE", 16),
    _e("TI012", NPO, "Income", "Revenue Grants", "Foreign Grants (FCRA)",                                       "IE", "CR_POSITIVE", 16),
    _e("TI013", NPO, "Income", "Donations", "Corpus Donations",                                                  "IE", "CR_POSITIVE", 17),
    _e("TI014", NPO, "Income", "Donations", "General Donations",                                                 "IE", "CR_POSITIVE", 17),
    _e("TI015", NPO, "Income", "Programme Income", "Fees / Training / Course Charges",                          "IE", "CR_POSITIVE", 18),
    _e("TI016", NPO, "Income", "Programme Income", "Subscriptions & Membership Fees",                           "IE", "CR_POSITIVE", 18),
    _e("TE010", NPO, "Expenditure", "Programme Expenses", "Programme / Project Direct Expenses",                 "IE", "DR_POSITIVE", 21),
    _e("TE011", NPO, "Expenditure", "Programme Expenses", "Field Activities & Beneficiary Costs",                "IE", "DR_POSITIVE", 21),
    _e("TE012", NPO, "Expenditure", "Establishment Expenses", "Staff Salaries & Allowances",                    "IE", "DR_POSITIVE", 20),
    _e("TE013", NPO, "Expenditure", "Establishment Expenses", "PF / ESI / Gratuity",                            "IE", "DR_POSITIVE", 20),
    _e("TE014", NPO, "Expenditure", "Administrative Expenses", "Rent, Electricity & Utilities",                  "IE", "DR_POSITIVE", 22),
    _e("TE015", NPO, "Expenditure", "Administrative Expenses", "Audit Fees & Professional Charges",             "IE", "DR_POSITIVE", 22),
]


def validate_master(entries: Iterable[MappingEntry] = MASTER) -> list[str]:
    """Return schema/data-quality errors for a taxonomy collection."""
    errors: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        prefix = f"{entry.code}: "
        if not entry.code:
            errors.append("blank mapping code")
        elif entry.code in seen:
            errors.append(f"duplicate mapping code {entry.code}")
        seen.add(entry.code)

        if not entry.entity_types:
            errors.append(prefix + "missing entity_types")
        else:
            invalid_tags = sorted(set(entry.entity_types) - VALID_ENTITY_TAGS)
            if invalid_tags:
                errors.append(prefix + f"invalid entity type tags {invalid_tags}")

        if entry.fs_tag not in VALID_FS_TAGS:
            errors.append(prefix + f"invalid fs_tag {entry.fs_tag!r}")
        if entry.sign not in VALID_SIGNS:
            errors.append(prefix + f"invalid sign convention {entry.sign!r}")
        if entry.note_number is not None and entry.note_number <= 0:
            errors.append(prefix + f"invalid note_number {entry.note_number!r}")
        if not all((entry.group, entry.heading, entry.sub_heading)):
            errors.append(prefix + "group, heading and sub_heading are required")

    return errors


_MASTER_ERRORS = validate_master(MASTER)
if _MASTER_ERRORS:
    raise ValueError("Invalid mapping master:\n- " + "\n- ".join(_MASTER_ERRORS))

_LOOKUP_MAP = MappingProxyType({m.code: m for m in MASTER})


def get_master(entity_types_filter: list[str] | None = None) -> list[MappingEntry]:
    """Return master entries filtered by entity type tags."""
    if not entity_types_filter:
        return MASTER
    s = set(entity_types_filter)
    return [m for m in MASTER if s.intersection(m.entity_types) or "ALL" in m.entity_types]


def get_lookup_map() -> dict[str, MappingEntry]:
    """code → MappingEntry for fast lookup."""
    return dict(_LOOKUP_MAP)


def get_entry(code: str) -> MappingEntry | None:
    """Return a single mapping entry by code."""
    return _LOOKUP_MAP.get(code.strip().upper())


def get_group_tree(entity_types_filter: list[str] | None = None) -> dict[str, dict[str, list[str]]]:
    """Build hierarchical {group: {heading: [sub_headings]}} dict."""
    tree: dict[str, dict[str, list[str]]] = {}
    for m in get_master(entity_types_filter):
        tree.setdefault(m.group, {}).setdefault(m.heading, [])
        if m.sub_heading not in tree[m.group][m.heading]:
            tree[m.group][m.heading].append(m.sub_heading)
    return tree
