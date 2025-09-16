"""Results API endpoint for retrieving session results."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..services.session_service import SessionService
from ..services.distribution_service import DistributionService
from ..services.validation_service import ValidationService

router = APIRouter()


@router.get("/results/{session_id}")
async def get_results(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # Get session summary
    session_summary = session_service.get_session_summary(session_id)

    # Get distributions
    distributions = distribution_service.get_distributions_by_session(session_id)

    # Format distribution data
    distribution_data = []
    for dist in distributions:
        distribution_data.append({
            "id": dist.id,
            "investor_id": dist.investor_id,
            "investor_name": dist.investor.investor_name,
            "investor_entity_type": dist.investor.investor_entity_type.value,
            "investor_tax_state": dist.investor.investor_tax_state,
            "fund_code": dist.fund_code,
            "period_quarter": dist.period_quarter,
            "period_year": dist.period_year,
            "jurisdiction": dist.jurisdiction.value,
            "amount": float(dist.amount),
            "composite_exemption": dist.composite_exemption,
            "withholding_exemption": dist.withholding_exemption,
            "created_at": dist.created_at.isoformat()
        })

    # Get validation errors
    validation_errors = validation_service.get_errors_by_session(session_id)
    error_data = []
    for error in validation_errors:
        error_data.append({
            "row_number": error.row_number,
            "column_name": error.column_name,
            "error_code": error.error_code,
            "error_message": error.error_message,
            "severity": error.severity.value,
            "field_value": error.field_value,
            "created_at": error.created_at.isoformat()
        })

    # Get error summary
    error_summary = validation_service.get_error_summary(session_id)

    # Calculate distribution totals if there are distributions
    distribution_summary = {}
    if distributions:
        # Get fund info from first distribution
        first_dist = distributions[0]
        distribution_summary = distribution_service.calculate_total_distributions(
            first_dist.fund_code,
            first_dist.period_quarter,
            first_dist.period_year
        )
        # Convert Decimal to float for JSON serialization
        distribution_summary = {k: float(v) for k, v in distribution_summary.items()}

        # Get exemption summary
        exemption_summary = distribution_service.get_exemption_summary(
            first_dist.fund_code,
            first_dist.period_quarter,
            first_dist.period_year
        )
        distribution_summary["exemption_summary"] = exemption_summary

    return {
        "session": session_summary,
        "distributions": {
            "data": distribution_data,
            "count": len(distribution_data),
            "summary": distribution_summary
        },
        "validation_errors": {
            "data": error_data,
            "summary": error_summary
        }
    }


@router.get("/results/{session_id}/preview")
async def get_results_preview(
    session_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # Get limited distributions
    distributions = distribution_service.get_distributions_by_session(session_id)
    limited_distributions = distributions[:limit]

    # Format for display
    preview_data = []
    for dist in limited_distributions:
        preview_data.append({
            "investor_name": dist.investor.investor_name,
            "entity_type": dist.investor.investor_entity_type.value,
            "tax_state": dist.investor.investor_tax_state,
            "jurisdiction": dist.jurisdiction.value,
            "amount": float(dist.amount),
            "composite_exemption": "Yes" if dist.composite_exemption else "No",
            "withholding_exemption": "Yes" if dist.withholding_exemption else "No",
            "fund_code": dist.fund_code,
            "period": f"{dist.period_quarter} {dist.period_year}"
        })

    return {
        "session_id": session_id,
        "status": session.status.value,
        "preview_data": preview_data,
        "total_records": len(distributions),
        "preview_limit": limit,
        "showing_count": len(preview_data)
    }