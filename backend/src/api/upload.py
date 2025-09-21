"""Upload API endpoint for file processing."""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..services.user_service import UserService
from ..services.session_service import SessionService
from ..services.excel_service import ExcelService
from ..services.investor_service import InvestorService
from ..services.distribution_service import DistributionService
from ..services.tax_calculation_service import TaxCalculationService
from ..models.user_session import UploadStatus

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload and process Excel file (v1.3 format).

    Returns session information and processing status.
    """
    # Validate file type (Excel only)
    if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Only .xlsx and .xls files are allowed."
        )

    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 10MB."
        )

    try:
        # Initialize services
        user_service = UserService(db)
        session_service = SessionService(db)
        excel_service = ExcelService()
        investor_service = InvestorService(db)
        distribution_service = DistributionService(db)
        tax_calculation_service = TaxCalculationService(db)

        # Save uploaded file temporarily for validation
        file_extension = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        try:
            # Parse and validate Excel file BEFORE creating any database entries
            parsing_result = excel_service.parse_excel_file(
                temp_file_path, file.filename
            )

            # Check for blocking validation errors
            blocking_errors = [error for error in parsing_result.errors
                             if error.severity.value == "ERROR"]

            if blocking_errors:
                # Clean up temp file
                if temp_file_path.exists():
                    os.unlink(temp_file_path)

                # Return detailed error response without saving anything
                error_details = []
                for error in blocking_errors:
                    error_detail = f"Row {error.row_number}, {error.column_name}: {error.error_message}"
                    if error.field_value:
                        error_detail += f" (Value: '{error.field_value}')"
                    error_details.append(error_detail)

                return {
                    "status": "validation_failed",
                    "message": "File validation failed. Please fix the following errors and try again:",
                    "errors": error_details,
                    "error_count": len(blocking_errors),
                    "total_rows": parsing_result.total_rows
                }

            # File is valid - now proceed with saving and processing
            # Get or create default user
            user = user_service.get_or_create_default_user()


            # TODO: Configure S3 storage for production
            # Save raw uploaded file permanently (local storage for now)
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            saved_file_path = upload_dir / f"{user.id}_{file.filename}"

            # Save the raw file content permanently
            with open(saved_file_path, 'wb') as saved_file:
                saved_file.write(content)

            # Create session in database
            session = session_service.create_session(
                user_id=user.id,
                upload_filename=temp_file_path.name,
                original_filename=file.filename,
                file_size=file.size or 0
            )

            # Process valid data
            distributions_created = 0
            for row_data in parsing_result.data:
                # Find or create investor
                investor = investor_service.find_or_create_investor(
                    row_data['investor_name'],
                    row_data['investor_entity_type'],
                    row_data['investor_tax_state']
                )

                # Create distributions
                distributions = distribution_service.create_distributions_for_investor(
                    investor=investor,
                    session_id=session.session_id,
                    fund_code=parsing_result.fund_info['fund_code'],
                    period_quarter=parsing_result.fund_info['period_quarter'],
                    period_year=int(parsing_result.fund_info['period_year']),
                    parsed_row=row_data
                )
                distributions_created += len(distributions)

            # Apply SALT tax calculations before finalizing
            db.flush()
            tax_calculation_service.apply_for_session(session.session_id)

            # Commit all changes
            db.commit()

            # Update session counts and mark as completed
            session_service.update_session_counts(
                session.session_id,
                parsing_result.total_rows,
                parsing_result.valid_rows
            )
            session_service.update_session_status(
                session.session_id, UploadStatus.COMPLETED, 100
            )
            db.commit()

            return {
                "session_id": session.session_id,
                "status": UploadStatus.COMPLETED.value,
                "message": "File processed successfully",
                "total_rows": parsing_result.total_rows,
                "valid_rows": parsing_result.valid_rows,
                "distributions_created": distributions_created,
                "fund_info": parsing_result.fund_info,
                "warning_count": len([e for e in parsing_result.errors if e.severity.value == "WARNING"])
            }

        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                os.unlink(temp_file_path)

    except Exception as e:
        db.rollback()
        # Try to update session status if session was created
        try:
            if 'session' in locals():
                session_service.update_session_status(
                    session.session_id,
                    UploadStatus.FAILED_SAVING,
                    error_message=str(e)
                )
                db.commit()
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
