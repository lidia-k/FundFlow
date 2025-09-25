"""File upload orchestrator for coordinating the upload workflow."""

import logging
from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..exceptions.upload_exceptions import (
    ExcelProcessingException,
    FileValidationException,
    UploadException,
)
from ..models.upload_context import UploadContext, UploadResult
from ..models.user_session import UploadStatus
from .upload_pipeline import (
    DataProcessingStep,
    ExcelParsingStep,
    FileHandlingStep,
    FileValidationStep,
    TaxCalculationStep,
    UploadPipelineStep,
)
from .upload_service_factory import UploadServiceDependencies

logger = logging.getLogger(__name__)


class FileUploadOrchestrator:
    """Orchestrates the entire file upload and processing workflow."""

    def __init__(self, services: UploadServiceDependencies, db: Session):
        self.services = services
        self.db = db
        self.pipeline_steps = self._create_pipeline()

    def _create_pipeline(self) -> List[UploadPipelineStep]:
        """Create the upload processing pipeline."""
        return [
            FileValidationStep(self.services),
            FileHandlingStep(self.services),
            ExcelParsingStep(self.services),
            DataProcessingStep(self.services),
            TaxCalculationStep(self.services),
        ]

    async def process_upload(self, file: UploadFile) -> UploadResult:
        """
        Process file upload through the complete pipeline.

        Args:
            file: The uploaded file

        Returns:
            UploadResult: Results of the upload processing

        Raises:
            UploadException: If processing fails
        """
        context = UploadContext(file=file, db_session=self.db)

        try:
            # Execute pipeline steps
            for step in self.pipeline_steps:
                logger.info(f"Executing pipeline step: {step.step_name}")
                context = step.execute(context)

            # Save permanent file after successful processing
            file_handling_step = self.pipeline_steps[1]  # FileHandlingStep
            file_handling_step.save_permanent_file(context)

            # Commit all changes
            self.db.commit()

            # Update session status
            self.services.session_service.update_session_counts(
                context.session.session_id,
                context.parsing_result.total_rows,
                context.parsing_result.valid_rows,
            )
            self.services.session_service.update_session_status(
                context.session.session_id, UploadStatus.COMPLETED, 100
            )
            self.db.commit()

            return self._create_success_result(context)

        except FileValidationException as e:
            # File validation errors - return structured error response
            return UploadResult(
                status="validation_failed",
                message="File validation failed",
                errors=e.errors,
                error_count=len(e.errors),
            )

        except ExcelProcessingException as e:
            # Excel parsing/validation errors - return structured error response
            if context.parsing_result:
                return self._create_excel_validation_error_result(context)
            else:
                return UploadResult(
                    status="parsing_failed",
                    message="Excel parsing failed",
                    errors=[str(e)],
                    error_count=1,
                )

        except UploadException as e:
            # Other upload-related errors
            self._handle_upload_failure(context, str(e))
            return UploadResult(
                status="processing_failed",
                message=str(e),
                errors=[str(e)],
                error_count=1,
            )

        except Exception as e:
            # Unexpected errors
            logger.exception("Unexpected error during upload processing")
            self._handle_upload_failure(context, f"Internal server error: {str(e)}")
            raise UploadException(f"Upload processing failed: {str(e)}")

        finally:
            # Clean up temporary file
            if hasattr(self.pipeline_steps[1], "cleanup_temp_file"):
                self.pipeline_steps[1].cleanup_temp_file(context)

    def _create_success_result(self, context: UploadContext) -> UploadResult:
        """Create success result from context."""
        return UploadResult(
            session_id=context.session.session_id,
            status=UploadStatus.COMPLETED.value,
            message="File processed successfully",
            total_rows=context.parsing_result.total_rows,
            valid_rows=context.parsing_result.valid_rows,
            distributions_created=context.distributions_created,
            fund_source_data_created=context.fund_source_data_created,
            fund_info=context.parsing_result.fund_info,
            warning_count=len([
                e for e in context.parsing_result.errors
                if e.severity.value == "WARNING"
            ]),
            fund_source_data_present=len(context.parsing_result.fund_source_data) > 0,
        )

    def _create_excel_validation_error_result(self, context: UploadContext) -> UploadResult:
        """Create error result for Excel validation failures."""
        blocking_errors = [
            error for error in context.parsing_result.errors
            if error.severity.value == "ERROR"
        ]

        error_details = []
        for error in blocking_errors:
            error_detail = f"Row {error.row_number}, {error.column_name}: {error.error_message}"
            if error.field_value:
                error_detail += f" (Value: '{error.field_value}')"
            error_details.append(error_detail)

        return UploadResult(
            status="validation_failed",
            message="File validation failed. Please fix the following errors and try again:",
            errors=error_details,
            error_count=len(blocking_errors),
            total_rows=context.parsing_result.total_rows,
            fund_source_data_present=len(context.parsing_result.fund_source_data) > 0,
        )

    def _handle_upload_failure(self, context: UploadContext, error_message: str) -> None:
        """Handle upload failure by updating session status and rolling back."""
        try:
            self.db.rollback()

            # Update session status if session was created
            if context.session:
                self.services.session_service.update_session_status(
                    context.session.session_id,
                    UploadStatus.FAILED_SAVING,
                    error_message=error_message,
                )
                self.db.commit()
        except Exception:
            # Ignore errors during cleanup
            pass