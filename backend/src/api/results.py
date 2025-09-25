"""Results API endpoint for retrieving session results."""

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.distribution_service import DistributionService
from ..services.session_service import SessionService
from ..services.tax_calculation_service import TaxCalculationService
from ..services.validation_service import ValidationService

router = APIRouter()


@router.get("/results/{session_id}")
async def get_results(session_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Get processing results and status for a session.

    Returns session status, distribution data, and validation errors.
    """
    # Initialize services
    session_service = SessionService(db)
    distribution_service = DistributionService(db)
    validation_service = ValidationService(db)

    # Get session
    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get session summary
    session_summary = session_service.get_session_summary(session_id)

    # Get distributions
    distributions = distribution_service.get_distributions_by_session(session_id)

    # Format distribution data
    distribution_data = []
    for dist in distributions:
        fund = dist.fund
        distribution_data.append(
            {
                "id": dist.id,
                "investor_id": dist.investor_id,
                "investor_name": dist.investor.investor_name,
                "investor_entity_type": dist.investor.investor_entity_type.value,
                "investor_tax_state": dist.investor.investor_tax_state,
                "fund_code": dist.fund_code,
                "period_quarter": fund.period_quarter if fund else None,
                "period_year": fund.period_year if fund else None,
                "jurisdiction": dist.jurisdiction.value,
                "amount": float(dist.amount),
                "composite_exemption": dist.composite_exemption,
                "withholding_exemption": dist.withholding_exemption,
                "composite_tax_amount": (
                    float(dist.composite_tax_amount)
                    if dist.composite_tax_amount is not None
                    else None
                ),
                "withholding_tax_amount": (
                    float(dist.withholding_tax_amount)
                    if dist.withholding_tax_amount is not None
                    else None
                ),
                "created_at": dist.created_at.isoformat(),
            }
        )

    # Get validation errors
    validation_errors = validation_service.get_errors_by_session(session_id)
    error_data = []
    for error in validation_errors:
        error_data.append(
            {
                "row_number": error.row_number,
                "column_name": error.column_name,
                "error_code": error.error_code,
                "error_message": error.error_message,
                "severity": error.severity.value,
                "field_value": error.field_value,
                "created_at": error.created_at.isoformat(),
            }
        )

    # Get error summary
    error_summary = validation_service.get_error_summary(session_id)

    # Calculate distribution totals if there are distributions
    distribution_summary = {}
    if distributions:
        # Get fund info from first distribution
        first_dist = distributions[0]
        fund = first_dist.fund
        if not fund:
            raise HTTPException(
                status_code=500, detail="Fund metadata missing for distribution"
            )
        distribution_summary = distribution_service.calculate_total_distributions(
            first_dist.fund_code, fund.period_quarter, fund.period_year
        )
        # Convert Decimal to float for JSON serialization
        distribution_summary = {k: float(v) for k, v in distribution_summary.items()}

        # Get exemption summary
        exemption_summary = distribution_service.get_exemption_summary(
            first_dist.fund_code, fund.period_quarter, fund.period_year
        )
        distribution_summary["exemption_summary"] = exemption_summary

    return {
        "session": session_summary,
        "distributions": {
            "data": distribution_data,
            "count": len(distribution_data),
            "summary": distribution_summary,
        },
        "validation_errors": {"data": error_data, "summary": error_summary},
    }


@router.get("/results/{session_id}/preview")
async def get_results_preview(
    session_id: str,
    limit: int = 100,
    mode: str = Query("upload", pattern="^(upload|results)$"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get preview of first N distribution records for display.

    Optimized for frontend data grid display.
    """
    # Initialize services
    session_service = SessionService(db)
    distribution_service = DistributionService(db)

    # Get session
    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get limited distributions
    distributions = distribution_service.get_distributions_by_session(session_id)
    limited_distributions = distributions[:limit]

    # Format for display
    preview_data = []
    results_mode = mode == "results"
    for dist in limited_distributions:
        fund = dist.fund
        preview_entry = {
            "investor_name": dist.investor.investor_name,
            "entity_type": dist.investor.investor_entity_type.value,
            "tax_state": dist.investor.investor_tax_state,
            "jurisdiction": dist.jurisdiction.value,
            "amount": float(dist.amount),
            "fund_code": dist.fund_code,
            "period": f"{fund.period_quarter} {fund.period_year}" if fund else None,
        }

        if results_mode:
            preview_entry["composite_tax_amount"] = (
                float(dist.composite_tax_amount)
                if dist.composite_tax_amount is not None
                else None
            )
            preview_entry["withholding_tax_amount"] = (
                float(dist.withholding_tax_amount)
                if dist.withholding_tax_amount is not None
                else None
            )
        else:
            preview_entry["composite_exemption"] = (
                "Yes" if dist.composite_exemption else "No"
            )
            preview_entry["withholding_exemption"] = (
                "Yes" if dist.withholding_exemption else "No"
            )

        preview_data.append(preview_entry)

    return {
        "session_id": session_id,
        "status": session.status.value,
        "preview_data": preview_data,
        "total_records": len(distributions),
        "preview_limit": limit,
        "showing_count": len(preview_data),
    }


@router.get("/results/{session_id}/report")
async def download_results_report(session_id: str, db: Session = Depends(get_db)):
    """Download detailed tax calculation report for auditing."""
    session_service = SessionService(db)
    distribution_service = DistributionService(db)
    tax_service = TaxCalculationService(db)

    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    distributions = distribution_service.get_distributions_by_session(session_id)
    if not distributions:
        raise HTTPException(
            status_code=404, detail="No distributions found for session"
        )

    rule_context = tax_service.get_rule_context()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Investor Name",
            "Entity Type",
            "Investor Tax State",
            "Jurisdiction",
            "Distribution Amount",
            "Composite Exemption",
            "Withholding Exemption",
            "Composite Tax Amount",
            "Withholding Tax Amount",
            "Applied Tax",
            "Composite Rule ID",
            "Composite Rate",
            "Composite Income Threshold",
            "Composite Mandatory Filing",
            "Withholding Rule ID",
            "Withholding Rate",
            "Withholding Income Threshold",
            "Withholding Tax Threshold",
        ]
    )

    for dist in distributions:
        investor = dist.investor
        if investor is None:
            continue

        entity_type = investor.investor_entity_type
        entity_code = (
            entity_type.coding if hasattr(entity_type, "coding") else str(entity_type)
        )
        rule_key = (dist.jurisdiction.value, entity_code)

        composite_rule = None
        withholding_rule = None
        if rule_context:
            composite_rule = rule_context.composite_rules.get(rule_key)
            withholding_rule = rule_context.withholding_rules.get(rule_key)

        applied_tax = "None"
        if dist.composite_tax_amount:
            applied_tax = "Composite"
        elif dist.withholding_tax_amount:
            applied_tax = "Withholding"

        investor_state = (
            investor.investor_tax_state.value
            if hasattr(investor.investor_tax_state, "value")
            else str(investor.investor_tax_state)
        )

        writer.writerow(
            [
                investor.investor_name,
                investor.investor_entity_type.value,
                investor_state,
                dist.jurisdiction.value,
                f"{dist.amount:.2f}",
                "Yes" if dist.composite_exemption else "No",
                "Yes" if dist.withholding_exemption else "No",
                (
                    f"{dist.composite_tax_amount:.2f}"
                    if dist.composite_tax_amount is not None
                    else ""
                ),
                (
                    f"{dist.withholding_tax_amount:.2f}"
                    if dist.withholding_tax_amount is not None
                    else ""
                ),
                applied_tax,
                getattr(composite_rule, "id", ""),
                f"{composite_rule.tax_rate:.4f}" if composite_rule else "",
                f"{composite_rule.income_threshold:.2f}" if composite_rule else "",
                getattr(composite_rule, "mandatory_filing", ""),
                getattr(withholding_rule, "id", ""),
                f"{withholding_rule.tax_rate:.4f}" if withholding_rule else "",
                f"{withholding_rule.income_threshold:.2f}" if withholding_rule else "",
                f"{withholding_rule.tax_threshold:.2f}" if withholding_rule else "",
            ]
        )

    output.seek(0)
    filename = f"tax_calculation_report_{session_id}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
