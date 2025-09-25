"""Download API endpoint for exporting results."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.distribution_service import DistributionService
from ..services.session_service import SessionService
from ..services.validation_service import ValidationService

router = APIRouter()


@router.get("/results/{session_id}/download")
async def download_results(
    session_id: str, format: str = "csv", db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download processed results as Excel or CSV file.

    Format options: 'csv' (default), 'excel'
    """
    # Initialize services
    session_service = SessionService(db)
    distribution_service = DistributionService(db)

    # Get session
    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get distributions
    distributions = distribution_service.get_distributions_by_session(session_id)

    if not distributions:
        raise HTTPException(
            status_code=404, detail="No distribution data found for this session"
        )

    # Prepare data for export
    export_data = []
    for dist in distributions:
        fund = dist.fund
        export_data.append(
            {
                "Investor Name": dist.investor.investor_name,
                "Entity Type": dist.investor.investor_entity_type.value,
                "Tax State": dist.investor.investor_tax_state,
                "Fund Code": dist.fund_code,
                "Period": f"{fund.period_quarter} {fund.period_year}" if fund else "",
                "Jurisdiction": dist.jurisdiction.value,
                "Distribution Amount": float(dist.amount),
                "Composite Exemption": "Yes" if dist.composite_exemption else "No",
                "Withholding Exemption": "Yes" if dist.withholding_exemption else "No",
                "Created Date": dist.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    if format.lower() == "csv":
        # Generate CSV
        output = io.StringIO()
        if export_data:
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)

        output.seek(0)

        # Create filename
        filename = f"fundflow_results_{session_id[:8]}.csv"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    else:
        raise HTTPException(
            status_code=400, detail="Invalid format. Supported formats: csv"
        )


@router.get("/results/{session_id}/download-errors")
async def download_errors(
    session_id: str, db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download validation errors as CSV file.
    """
    # Initialize services
    session_service = SessionService(db)
    validation_service = ValidationService(db)

    # Get session
    session = session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get validation errors
    error_data = validation_service.export_errors_to_csv_data(session_id)

    if not error_data:
        raise HTTPException(
            status_code=404, detail="No validation errors found for this session"
        )

    # Generate CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=error_data[0].keys())
    writer.writeheader()
    writer.writerows(error_data)

    output.seek(0)

    # Create filename
    filename = f"fundflow_errors_{session_id[:8]}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
