"""Excel parsing step in upload pipeline."""

from ...exceptions.upload_exceptions import ExcelProcessingException
from ...models.upload_context import UploadContext
from ...services.upload_dependencies import UploadServiceDependencies
from .base import UploadPipelineStep


class ExcelParsingStep(UploadPipelineStep):
    """Pipeline step for parsing and validating Excel files."""

    def __init__(self, services: UploadServiceDependencies):
        self.services = services

    @property
    def step_name(self) -> str:
        return "excel_parsing"

    def execute(self, context: UploadContext) -> UploadContext:
        """Parse and validate Excel file content."""
        if not context.temp_file_path:
            raise ExcelProcessingException("Temporary file not available for parsing")

        try:
            # Parse Excel file
            context.parsing_result = self.services.excel_service.parse_excel_file(
                context.temp_file_path, context.file.filename
            )

            # Validate parsing results
            self.services.excel_validator.validate_excel_content(context.parsing_result)

            return context

        except ExcelProcessingException:
            # Re-raise Excel processing exceptions as-is
            raise
        except Exception as e:
            raise ExcelProcessingException(f"Excel parsing failed: {str(e)}")
