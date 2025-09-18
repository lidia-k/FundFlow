"""Results API endpoint for retrieving session results."""

import os
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..services.session_service import SessionService
from ..services.distribution_service import DistributionService
from ..services.validation_service import ValidationService
from ..services.excel_service import ExcelService

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


@router.get("/results/{session_id}/file-preview")
async def get_file_preview(
    session_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get preview of the raw uploaded Excel file content.

    Shows the actual data from the uploaded file before processing.
    """
    # Initialize services
    session_service = SessionService(db)
    excel_service = ExcelService()

    # Get session
    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # Construct the file path where the uploaded file is stored
    upload_dir = Path("data/uploads")
    file_path = upload_dir / f"{session.user_id}_{session.original_filename}"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Uploaded file not found"
        )

    try:
        # Read the raw Excel file content
        parsing_result = excel_service.parse_excel_file(file_path, session.original_filename)

        # Limit the preview data
        limited_data = parsing_result.data[:limit]

        # Get all unique states from distributions for dynamic column headers
        all_distribution_states = set()
        all_exemption_states = set()
        for row in limited_data:
            distributions = row.get('distributions', {})
            withholding_exemptions = row.get('withholding_exemptions', {})
            composite_exemptions = row.get('composite_exemptions', {})

            all_distribution_states.update(distributions.keys())
            all_exemption_states.update(withholding_exemptions.keys())
            all_exemption_states.update(composite_exemptions.keys())

        # Sort states for consistent ordering
        sorted_distribution_states = sorted(all_distribution_states)
        sorted_exemption_states = sorted(all_exemption_states)

        # Format the raw data for display
        preview_data = []
        for row in limited_data:
            row_data = {
                "investor_name": row.get('investor_name', ''),
                "entity_type": row.get('investor_entity_type', ''),
                "tax_state": row.get('investor_tax_state', ''),
                "fund_code": parsing_result.fund_info.get('fund_code', ''),
                "period": f"{parsing_result.fund_info.get('period_quarter', '')} {parsing_result.fund_info.get('period_year', '')}"
            }

            # Add distribution amounts dynamically by state
            distributions = row.get('distributions', {})
            row_data["distributions"] = {}
            for state in sorted_distribution_states:
                row_data["distributions"][state] = float(distributions.get(state, 0))

            # Add exemption data dynamically by state
            withholding_exemptions = row.get('withholding_exemptions', {})
            composite_exemptions = row.get('composite_exemptions', {})

            row_data["withholding_exemptions"] = {}
            row_data["composite_exemptions"] = {}

            for state in sorted_exemption_states:
                row_data["withholding_exemptions"][state] = "Yes" if withholding_exemptions.get(state, False) else "No"
                row_data["composite_exemptions"][state] = "Yes" if composite_exemptions.get(state, False) else "No"

            preview_data.append(row_data)

        return {
            "session_id": session_id,
            "filename": session.original_filename,
            "status": session.status.value,
            "file_info": {
                "fund_code": parsing_result.fund_info.get('fund_code', ''),
                "period_quarter": parsing_result.fund_info.get('period_quarter', ''),
                "period_year": parsing_result.fund_info.get('period_year', ''),
                "file_format": parsing_result.fund_info.get('file_format', 'v1.3')
            },
            "preview_data": preview_data,
            "available_states": {
                "distributions": sorted_distribution_states,
                "exemptions": sorted_exemption_states
            },
            "total_rows": parsing_result.total_rows,
            "valid_rows": parsing_result.valid_rows,
            "preview_limit": limit,
            "showing_count": len(preview_data),
            "has_errors": len(parsing_result.errors) > 0,
            "error_count": len(parsing_result.errors)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )