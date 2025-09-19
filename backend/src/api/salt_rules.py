"""SALT Rules API endpoints for upload, validation, preview, and publishing."""

import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime, date
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database.connection import get_db
from ..services.excel_processor import ExcelProcessor
from ..services.validation_service import ValidationService
from ..services.file_service import FileService
from ..services.comparison_service import ComparisonService
from ..services.rule_set_service import RuleSetService
from ..models.salt_rule_set import SaltRuleSet, RuleSetStatus
from ..models.source_file import SourceFile
from ..models.enums import Quarter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salt-rules", tags=["SALT Rules"])


# Request/Response Models
class PublishRequest(BaseModel):
    """Request model for publishing rule set."""
    effective_date: Optional[date] = None
    confirm_archive: bool = False


class UploadResponse(BaseModel):
    """Response model for upload endpoint."""
    rule_set_id: str = Field(alias="ruleSetId")
    status: str  # "valid", "validation_failed"
    uploaded_file: Dict[str, Any] = Field(alias="uploadedFile")
    validation_started: bool = Field(alias="validationStarted")
    message: str
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, alias="validationErrors")
    rule_counts: Optional[Dict[str, int]] = Field(None, alias="ruleCounts")

    class Config:
        populate_by_name = True


class ValidationResponse(BaseModel):
    """Response model for validation endpoint."""
    rule_set_id: str
    status: str
    summary: Dict[str, Any]
    issues: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None




@router.post("/upload", response_model=UploadResponse, response_model_by_alias=True, status_code=201)
async def upload_salt_rules(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UploadResponse:
    """
    Upload and validate SALT rule workbook.

    Validates the file first, then saves to database only if validation passes.
    Returns validation errors immediately if file is invalid.
    """
    # Auto-detect current year and quarter
    current_date = datetime.now()
    year = current_date.year

    # Determine quarter based on current month
    month = current_date.month
    if month <= 3:
        quarter_enum = Quarter.Q1
    elif month <= 6:
        quarter_enum = Quarter.Q2
    elif month <= 9:
        quarter_enum = Quarter.Q3
    else:
        quarter_enum = Quarter.Q4

    # Basic input validation
    if description and len(description) > 500:
        raise HTTPException(
            status_code=400,
            detail="Description must be 500 characters or less"
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File is required"
        )

    if not file.filename.lower().endswith(('.xlsx', '.xlsm')):
        raise HTTPException(
            status_code=400,
            detail="File must be Excel format (.xlsx or .xlsm)"
        )

    # Check file size (10MB limit for prototype)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10MB limit"
        )

    try:
        # Save uploaded file temporarily for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        try:
            # STEP 1: Validate file first (before saving anything)
            excel_processor = ExcelProcessor()
            validation_result = excel_processor.validate_file(temp_file_path)

            # If validation fails, return errors immediately without saving anything
            if not validation_result.is_valid:
                return UploadResponse(
                    rule_set_id="",
                    status="validation_failed",
                    uploaded_file={
                        "filename": file.filename,
                        "fileSize": file.size or 0,
                        "uploadTimestamp": datetime.now().isoformat() + "Z"
                    },
                    validation_started=False,
                    message="File validation failed",
                    validation_errors=validation_result.errors
                )

            # STEP 2: File is valid - archive any existing active rule set
            # Archive any existing ACTIVE rule set for this year/quarter
            existing_active_rule_set = db.query(SaltRuleSet).filter(
                SaltRuleSet.year == year,
                SaltRuleSet.quarter == quarter_enum,
                SaltRuleSet.status == RuleSetStatus.ACTIVE
            ).first()

            if existing_active_rule_set:
                logger.info(f"Found existing active rule set: {existing_active_rule_set.id}, archiving it")
                existing_active_rule_set.status = RuleSetStatus.ARCHIVED
                existing_active_rule_set.archived_at = datetime.now()
                db.commit()
                logger.info("Successfully archived existing active rule set")

            # Store file (simple override if exists)
            file_service = FileService(db)
            storage_result = file_service.store_uploaded_file(
                temp_file_path, file.filename, file.content_type or
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "admin@fundflow.com",  # TODO: Get from auth
                year, quarter_enum.value
            )

            if storage_result.error_message:
                raise HTTPException(status_code=400, detail=storage_result.error_message)

            # Create new rule set with ACTIVE status
            rule_set_id = str(uuid4())
            rule_set = SaltRuleSet(
                id=rule_set_id,
                year=year,
                quarter=quarter_enum,
                version="1.0.0",
                status=RuleSetStatus.ACTIVE,
                effective_date=date.today(),
                created_at=datetime.now(),
                created_by="admin@fundflow.com",  # TODO: Get from auth
                description=description,
                source_file_id=storage_result.source_file.id,
                published_at=datetime.now()
            )

            db.add(rule_set)
            db.commit()
            db.refresh(rule_set)

            # Process Excel file and extract rules
            processing_result = excel_processor.process_file(
                Path(storage_result.source_file.filepath), rule_set_id
            )

            # Save processed rules
            for rule in processing_result.withholding_rules:
                db.add(rule)
            for rule in processing_result.composite_rules:
                db.add(rule)
            for issue in processing_result.validation_issues:
                db.add(issue)

            # Update rule counts
            rule_set.rule_count_withholding = len(processing_result.withholding_rules)
            rule_set.rule_count_composite = len(processing_result.composite_rules)

            db.commit()

            response = UploadResponse(
                rule_set_id=rule_set_id,
                status="valid",
                uploaded_file={
                    "filename": storage_result.source_file.filename,
                    "fileSize": storage_result.source_file.file_size,
                    "uploadTimestamp": storage_result.source_file.upload_timestamp.isoformat() + "Z"
                },
                validation_started=True,
                message="File uploaded and validated successfully",
                rule_counts={
                    "withholding": len(processing_result.withholding_rules),
                    "composite": len(processing_result.composite_rules)
                }
            )
            return response

        finally:
            # Clean up temp file
            temp_file_path.unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )




@router.get("/{rule_set_id}/preview")
async def get_rule_set_preview(
    rule_set_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get preview of rule set changes compared to current active rules."""
    try:
        # Validate rule set exists
        rule_set = db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise HTTPException(
                status_code=404,
                detail="Rule set not found"
            )

        comparison_service = ComparisonService(db)
        preview_result = comparison_service.get_rule_set_preview(rule_set_id)

        return preview_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule set preview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{rule_set_id}/publish")
async def publish_rule_set(
    rule_set_id: str,
    publish_request: PublishRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Publish draft rule set to active status."""
    try:
        # Validate rule set exists
        rule_set = db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise HTTPException(
                status_code=404,
                detail="Rule set not found"
            )

        if rule_set.status != RuleSetStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="Only active rule sets can be republished"
            )

        # Use RuleSetService to handle publication
        rule_set_service = RuleSetService(db)
        result = rule_set_service.publish_rule_set(
            rule_set_id,
            publish_request.effective_date,
            publish_request.confirm_archive
        )

        return {
            "ruleSetId": result["ruleSetId"],
            "status": result["status"],
            "publishedAt": result["publishedAt"],
            "effectiveDate": result["effectiveDate"],
            "resolvedRulesGenerated": result["resolvedRulesGenerated"],
            "archivedPrevious": result["archivedPrevious"],
            "message": "Rule set published successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing rule set: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("")
async def list_rule_sets(
    year: Optional[int] = Query(None),
    quarter: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List SALT rule sets with optional filtering."""
    try:
        query = db.query(SaltRuleSet)

        # Apply filters
        if year:
            if year < 2020 or year > 2030:
                raise HTTPException(
                    status_code=400,
                    detail="Year must be between 2020 and 2030"
                )
            query = query.filter(SaltRuleSet.year == year)

        if quarter:
            try:
                quarter_enum = Quarter(quarter)
                query = query.filter(SaltRuleSet.quarter == quarter_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Quarter must be one of: Q1, Q2, Q3, Q4"
                )

        if status:
            try:
                status_enum = RuleSetStatus(status)
                query = query.filter(SaltRuleSet.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Status must be one of: active, archived"
                )

        # Get total count
        total_count = query.count()

        # Apply pagination and ordering
        rule_sets = (
            query.order_by(SaltRuleSet.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Format response
        items = []
        for rule_set in rule_sets:
            items.append({
                "id": str(rule_set.id),
                "year": rule_set.year,
                "quarter": rule_set.quarter.value,
                "version": rule_set.version,
                "status": rule_set.status.value,
                "effectiveDate": rule_set.effective_date.isoformat(),
                "ruleCountWithholding": rule_set.rule_count_withholding,
                "ruleCountComposite": rule_set.rule_count_composite,
                "createdAt": rule_set.created_at.isoformat() + "Z",
                "publishedAt": rule_set.published_at.isoformat() + "Z" if rule_set.published_at else None,
                "description": rule_set.description
            })

        return {
            "items": items,
            "totalCount": total_count,
            "limit": limit,
            "offset": offset,
            "hasMore": offset + limit < total_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing rule sets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{rule_set_id}")
async def get_rule_set_detail(
    rule_set_id: str,
    include_rules: bool = Query(False, description="Include actual rule data in response"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about a specific rule set."""
    try:
        # Use RuleSetService to get detailed information
        rule_set_service = RuleSetService(db)
        result = rule_set_service.get_rule_set_detail(rule_set_id, include_rules)

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting rule set detail: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{rule_set_id}")
async def delete_rule_set(
    rule_set_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a rule set and all associated data."""
    try:
        # Validate rule set exists
        rule_set = db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise HTTPException(
                status_code=404,
                detail="Rule set not found"
            )

        # Check if rule set can be deleted (only archived rule sets)
        if rule_set.status == RuleSetStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete active rule set. Archive it first."
            )

        # Use RuleSetService to handle deletion
        rule_set_service = RuleSetService(db)
        rule_set_service.delete_rule_set(rule_set_id)

        return {
            "message": "Rule set deleted successfully",
            "deletedAt": datetime.now().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rule set: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )