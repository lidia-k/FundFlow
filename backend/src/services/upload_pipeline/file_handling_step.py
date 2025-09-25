"""File handling step in upload pipeline."""

import os
import tempfile
from pathlib import Path

from ...exceptions.upload_exceptions import FileStorageException
from ...models.upload_context import UploadContext
from ...services.upload_dependencies import UploadServiceDependencies
from .base import UploadPipelineStep


class FileHandlingStep(UploadPipelineStep):
    """Pipeline step for handling file storage and temporary file creation."""

    def __init__(self, services: UploadServiceDependencies):
        self.services = services

    @property
    def step_name(self) -> str:
        return "file_handling"

    def execute(self, context: UploadContext) -> UploadContext:
        """Handle file storage operations."""
        try:
            # Read file content
            context.file_content = context.file.file.read()
            context.file.file.seek(0)  # Reset file pointer

            # Create temporary file
            file_extension = Path(context.file.filename).suffix
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension
            ) as temp_file:
                temp_file.write(context.file_content)
                context.temp_file_path = Path(temp_file.name)

            return context

        except Exception as e:
            raise FileStorageException(f"Failed to handle file storage: {str(e)}")

    @staticmethod
    def cleanup_temp_file(context: UploadContext) -> None:
        """Clean up temporary file."""
        if context.temp_file_path and context.temp_file_path.exists():
            try:
                os.unlink(context.temp_file_path)
            except Exception:
                pass  # Ignore cleanup errors

    def save_permanent_file(self, context: UploadContext) -> None:
        """Save file permanently after successful validation."""
        if not context.user or not context.file_content:
            raise FileStorageException("User or file content not available")

        try:
            # TODO: Configure S3 storage for production
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            context.saved_file_path = upload_dir / f"{context.user.id}_{context.file.filename}"

            # Save the raw file content permanently
            with open(context.saved_file_path, "wb") as saved_file:
                saved_file.write(context.file_content)

        except Exception as e:
            raise FileStorageException(f"Failed to save permanent file: {str(e)}")
