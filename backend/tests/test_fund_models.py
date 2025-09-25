"""Tests covering fund-related models and services."""

from decimal import Decimal

import pytest

from src.models.enums import InvestorEntityType, USJurisdiction
from src.models.investor import Investor
from src.services.distribution_service import DistributionService
from src.services.fund_service import FundService
from src.services.investor_service import InvestorService


@pytest.fixture()
def investor(db_session):
    investor = Investor(
        investor_name="Alpha Capital",
        investor_entity_type=InvestorEntityType.PARTNERSHIP,
        investor_tax_state=USJurisdiction.NY,
    )
    db_session.add(investor)
    db_session.commit()
    db_session.refresh(investor)
    return investor


def test_upsert_commitment_persists_and_exposes_funds(db_session, investor):
    fund_service = FundService(db_session)
    investor_service = InvestorService(db_session)

    fund = fund_service.get_or_create_fund("FUND001", "Q1", 2024)
    investor_service.upsert_commitment(investor, fund, Decimal("12.5"))
    db_session.commit()
    db_session.refresh(investor)

    assert len(investor.fund_commitments) == 1
    assert investor.fund_commitments[0].commitment_percentage == Decimal("12.5000")
    assert investor.funds[0].fund_code == "FUND001"
    assert investor.funds[0].period_quarter == "Q1"
    assert investor.funds[0].period_year == 2024


def test_upsert_commitment_out_of_range_raises(db_session, investor):
    fund_service = FundService(db_session)
    investor_service = InvestorService(db_session)

    fund = fund_service.get_or_create_fund("FUND002", "Q2", 2024)

    with pytest.raises(ValueError):
        investor_service.upsert_commitment(investor, fund, Decimal("150"))


def test_distribution_service_links_fund(db_session, investor):
    fund_service = FundService(db_session)
    investor_service = InvestorService(db_session)
    distribution_service = DistributionService(db_session)

    fund = fund_service.get_or_create_fund("FUND003", "Q3", 2025)
    investor_service.upsert_commitment(investor, fund, Decimal("10"))

    distributions = distribution_service.create_distributions_for_investor(
        investor=investor,
        session_id="session-xyz",
        fund=fund,
        parsed_row={
            "distributions": {USJurisdiction.TX.value: Decimal("100.00")},
            "withholding_exemptions": {},
            "composite_exemptions": {},
        },
    )
    db_session.commit()

    assert len(distributions) == 1
    distribution = distributions[0]
    assert distribution.fund is fund
    assert distribution.fund.period_quarter == "Q3"
    assert distribution.fund.period_year == 2025

    fetched = distribution_service.get_distributions_by_session("session-xyz")
    assert fetched[0].fund.fund_code == "FUND003"
    assert fetched[0].fund.period_year == 2025
