"""Entity type definitions and FS format routing."""

from enum import Enum


class EntityType(str, Enum):
    COMPANY = "COMPANY"
    LLP     = "LLP"
    PROP    = "PROP"
    PART    = "PART"
    AOP     = "AOP"
    TRUST   = "TRUST"
    SEC8    = "SEC8"


ENTITY_LABELS = {
    EntityType.COMPANY: "Company under Companies Act 2013 Division I - Non IND AS",
    EntityType.LLP:     "Limited Liability Partnership",
    EntityType.PROP:    "Proprietorship",
    EntityType.PART:    "Partnership Firm",
    EntityType.AOP:     "AOP / RWA / Club / BOI",
    EntityType.TRUST:   "Public Charitable Trust / NPO",
    EntityType.SEC8:    "Section 8 Company",
}

AOP_SUBTYPES  = ["RWA", "Club", "AOP_General", "BOI"]
TRUST_SUBTYPES = ["Public_Charitable_Trust", "Private_Trust", "Section_8_equiv"]

# Which entity types use Income & Expenditure instead of P&L
IE_ENTITIES = {EntityType.AOP, EntityType.TRUST, EntityType.SEC8}

# Which entity types require Cash Flow Statement
CF_MANDATORY = {EntityType.COMPANY, EntityType.SEC8}

# Which entity types support small-company reduced disclosures
SMALL_CO_ELIGIBLE = {EntityType.COMPANY}

# Master DB tags applicable per entity
MASTER_TAGS: dict[EntityType, list[str]] = {
    EntityType.COMPANY: ["COMPANY", "ALL"],
    EntityType.LLP:     ["LLP", "NCE", "ALL"],
    EntityType.PROP:    ["PROP", "NCE", "ALL"],
    EntityType.PART:    ["PART", "NCE", "ALL"],
    EntityType.AOP:     ["AOP", "NCE", "ALL"],
    EntityType.TRUST:   ["TRUST", "NPO", "NCE", "ALL"],
    EntityType.SEC8:    ["SEC8", "COMPANY", "ALL"],
}


def fs_label(entity_type: EntityType) -> dict[str, str]:
    """Return display labels for FS statement tabs."""
    base = {
        EntityType.COMPANY: {"bs": "Balance Sheet", "pl": "Profit & Loss", "cf": "Cash Flow"},
        EntityType.LLP:     {"bs": "Balance Sheet", "pl": "Profit & Loss", "cap": "Partners' Capital"},
        EntityType.PROP:    {"bs": "Balance Sheet", "pl": "Profit & Loss"},
        EntityType.PART:    {"bs": "Balance Sheet", "pl": "Profit & Loss", "cap": "Partners' Capital"},
        EntityType.AOP:     {"bs": "Balance Sheet", "ie": "Income & Expenditure", "rp": "Receipt & Payment"},
        EntityType.TRUST:   {"bs": "Balance Sheet", "ie": "Income & Expenditure", "rp": "Receipt & Payment"},
        EntityType.SEC8:    {"bs": "Balance Sheet", "ie": "Income & Expenditure", "cf": "Cash Flow"},
    }
    return base.get(entity_type, {"bs": "Balance Sheet", "pl": "Profit & Loss"})
