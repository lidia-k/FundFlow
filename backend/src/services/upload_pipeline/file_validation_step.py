"""File validation step in upload pipeline."""

from ...exceptions.upload_exceptions import FileValidationException
from ...models.upload_context import UploadContext
from ...services.upload_dependencies import UploadServiceDependencies
from .base import UploadPipelineStep


class FileValidationStep(UploadPipelineStep):
    """Pipeline step for validating uploaded files."""

    def __init__(self, services: UploadServiceDependencies):
        self.services = services

    @property
    def step_name(self) -> str:
        return "file_validation"

    def execute(self, context: UploadContext) -> UploadContext:
        """Validate the uploaded file for type and size constraints."""
        try:
            self.services.file_validator.validate_upload_file(context.file)
            return context
        except FileValidationException:
            # Re-raise file validation exceptions as-is
            raise
