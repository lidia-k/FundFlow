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
from ..services.validation_service import ValidationService
from ..models.user_session import UploadStatus

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload and process Excel file.

    Returns session information and processing status.
    """
    # Validate file type
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
        validation_service = ValidationService(db)

        # Get or create default user
        user = user_service.get_or_create_default_user()

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        try:
            # Calculate file hash for idempotency
            file_hash = excel_service.calculate_file_hash(temp_file_path)

            # Check for duplicate files
            existing_session = session_service.check_file_duplicate(file_hash, user.id)
            if existing_session:
                return {
                    "session_id": existing_session.session_id,
                    "status": existing_session.status.value,
                    "message": "File already processed",
                    "duplicate": True
                }

            # Create session
            session = session_service.create_session(
                user_id=user.id,
                upload_filename=temp_file_path.name,
                original_filename=file.filename,
                file_hash=file_hash,
                file_size=file.size or 0
            )

            # Update status to uploading
            session_service.update_session_status(
                session.session_id, UploadStatus.UPLOADING, 5
            )

            # Parse Excel file
            session_service.update_session_status(
                session.session_id, UploadStatus.PARSING, 40
            )

            parsing_result = excel_service.parse_excel_file(
                temp_file_path, file.filename
            )

            # Update status to validating
            session_service.update_session_status(
                session.session_id, UploadStatus.VALIDATING, 70
            )

            # Save validation errors
            if parsing_result.errors:
                validation_service.save_validation_errors(
                    session.session_id, parsing_result.errors
                )

            # Check if there are blocking errors
            has_errors = validation_service.has_blocking_errors(session.session_id)
            if has_errors:
                session_service.update_session_status(
                    session.session_id,
                    UploadStatus.FAILED_VALIDATION,
                    70,
                    "File contains validation errors that prevent processing"
                )
                session_service.update_session_counts(
                    session.session_id,
                    parsing_result.total_rows,
                    0
                )
                return {
                    "session_id": session.session_id,
                    "status": UploadStatus.FAILED_VALIDATION.value,
                    "message": "File contains validation errors",
                    "total_rows": parsing_result.total_rows,
                    "valid_rows": 0,
                    "error_count": len(parsing_result.errors)
                }

            # Update status to saving
            session_service.update_session_status(
                session.session_id, UploadStatus.SAVING, 90
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