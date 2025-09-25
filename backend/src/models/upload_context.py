"""Upload context model for managing upload workflow state."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from fastapi import UploadFile

from ..models.fund import Fund
from ..models.user import User
from ..models.user_session import UserSession
from ..services.excel_service import ExcelParsingResult


@dataclass
class UploadContext:
    """Context object that carries state through the upload pipeline."""

    file: UploadFile
    db_session: Any  # SQLAlchemy session

    # File processing state
    temp_file_path: Optional[Path] = None
    saved_file_path: Optional[Path] = None
    file_content: Optional[bytes] = None

    # Domain objects
    user: Optional[User] = None
    session: Optional[UserSession] = None
    fund: Optional[Fund] = None

    # Parsing results
    parsing_result: Optional[ExcelParsingResult] = None

    # Processing results
    distributions_created: int = 0
    fund_source_data_created: int = 0

    # Error tracking
    validation_errors: List[str] = field(default_factory=list)
    blocking_errors: List[Any] = field(default_factory=list)

    def has_blocking_errors(self) -> bool:
        """Check if there are any blocking validation errors."""
        return len(self.blocking_errors) > 0

    def add_validation_error(self, error: str) -> None:
        """Add a validation error to the context."""
        self.validation_errors.append(error)


@dataclass
class UploadResult:
    """Result object returned from upload processing."""

    session_id: Optional[str] = None
    status: str = "processing"
    message: str = ""
    total_rows: int = 0
    valid_rows: int = 0
    distributions_created: int = 0
    fund_source_data_created: int = 0
    fund_info: dict = field(default_factory=dict)
    warning_count: int = 0
    fund_source_data_present: bool = False
    errors: List[str] = field(default_factory=list)
    error_count: int = 0

    def to_api_response(self) -> dict[str, Any]:
        """Convert result to API response format."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "message": self.message,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "distributions_created": self.distributions_created,
            "fund_source_data_created": self.fund_source_data_created,
            "fund_info": self.fund_info,
            "warning_count": self.warning_count,
            "fund_source_data_present": self.fund_source_data_present,
            "errors": self.errors,
            "error_count": self.error_count,
        }