"""Shared enums for models."""

from enum import Enum
from typing import Dict


class InvestorEntityType(Enum):
    """Investor entity type enumeration with SALT coding support."""

    def __new__(cls, display_value: str, coding: str):
        """Create enum member with both display value and SALT coding."""
        obj = object.__new__(cls)
        obj._value_ = display_value
        obj.coding = coding
        return obj

    # Entity types with their corresponding SALT coding values
    CORPORATION = ("Corporation", "Corporation")
    LIMITED_PARTNERSHIP = ("Limited Partnership", "Partnership")
    EXEMPT_ORGANIZATION = ("Exempt Organization", "Exempt Org")
    LLC_TAXED_AS_PARTNERSHIP = ("LLC_Taxed as Partnership", "Partnership")
    INDIVIDUAL = ("Individual", "Individual")
    TRUST = ("Trust", "Trust")
    S_CORPORATION = ("S Corporation", "S Corporation")
    PARTNERSHIP = ("Partnership", "Partnership")
    JOINT_TENANCY_TENANCY_IN_COMMON = ("Joint Tenancy / Tenancy in Common", "Individual")
    GOVERNMENT_BENEFIT_PLAN = ("Government Benefit Plan", "Exempt Org")
    IRA_KEOGH = ("IRA/Keogh", "IRA")
    IRA = ("IRA", "IRA")
    EXEMPT_ORGANIZATION_BENEFIT = ("Exempt Organization_Benefit", "Exempt Org")
    LLP = ("LLP", "Partnership")
    BENEFIT_PLAN_INVESTOR_ERISA_TITLE_I = ("Benefit Plan Investor [ERISA Title I Plan]", "Exempt Org")
    GRANTOR_TRUST = ("Grantor Trust", "Individual")
    LLC_TAXED_AS_CORPORATION = ("LLC_Taxed as Corporation", "Corporation")
    LLC_TAXED_AS_PARTNERSHIP_ALT = ("LLC – Taxed as Partnership", "Partnership")
    ESTATE = ("Estate", "Estate")
    BENEFIT_PLAN_INVESTOR_PLAN_ASSETS = ("Benefit Plan Investor [Plan Assets Entity_ERISA 3(42)]", "Exempt Org")

    @classmethod
    def get_by_coding(cls, coding: str) -> "InvestorEntityType":
        """Get entity type by its SALT coding value."""
        for entity_type in cls:
            if entity_type.coding == coding:
                return entity_type
        raise ValueError(f"No entity type found for coding: {coding}")

    @classmethod
    def get_all_codings(cls) -> Dict[str, str]:
        """Get mapping of all entity types to their coding values."""
        return {entity_type.value: entity_type.coding for entity_type in cls}

    @classmethod
    def get_unique_codings(cls) -> set[str]:
        """Get set of all unique coding values."""
        return {entity_type.coding for entity_type in cls}


class USJurisdiction(Enum):
    """US states and DC jurisdiction enumeration."""
    AL = "AL"
    AK = "AK"
    AZ = "AZ"
    AR = "AR"
    CA = "CA"
    CO = "CO"
    CT = "CT"
    DE = "DE"
    FL = "FL"
    GA = "GA"
    HI = "HI"
    ID = "ID"
    IL = "IL"
    IN = "IN"
    IA = "IA"
    KS = "KS"
    KY = "KY"
    LA = "LA"
    ME = "ME"
    MD = "MD"
    MA = "MA"
    MI = "MI"
    MN = "MN"
    MS = "MS"
    MO = "MO"
    MT = "MT"
    NE = "NE"
    NV = "NV"
    NH = "NH"
    NJ = "NJ"
    NM = "NM"
    NY = "NY"
    NC = "NC"
    ND = "ND"
    OH = "OH"
    OK = "OK"
    OR = "OR"
    PA = "PA"
    RI = "RI"
    SC = "SC"
    SD = "SD"
    TN = "TN"
    TX = "TX"
    UT = "UT"
    VT = "VT"
    VA = "VA"
    WA = "WA"
    WV = "WV"
    WI = "WI"
    WY = "WY"
    DC = "DC"


class RuleSetStatus(Enum):
    """SALT rule set status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Quarter(Enum):
    """Quarter enumeration for SALT rule sets."""
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class IssueSeverity(Enum):
    """Validation issue severity enumeration."""
    ERROR = "error"
    WARNING = "warning"