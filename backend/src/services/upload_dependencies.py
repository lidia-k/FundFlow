"""FastAPI dependency injection for upload services."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database.connection import get_db
from .excel_service import ExcelService
from .file_handling_service import FileHandlingService
from .salt_rule_service import SaltRuleService
from .session_service import SessionService
from .tax_calculation_service import TaxCalculationService
from .upload_service_factory import UploadServiceDependencies


@lru_cache()
def get_excel_service() -> ExcelService:
    """Get Excel service singleton."""
    return ExcelService()


@lru_cache()
def get_file_handling_service() -> FileHandlingService:
    """Get file handling service singleton."""
    return FileHandlingService()


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """Get session service with database dependency."""
    return SessionService(db)


def get_salt_rule_service(db: Session = Depends(get_db)) -> SaltRuleService:
    """Get SALT rule service with database dependency."""
    return SaltRuleService(db)


def get_tax_calculation_service(
    salt_rule_service: SaltRuleService = Depends(get_salt_rule_service),
) -> TaxCalculationService:
    """Get tax calculation service with dependencies."""
    return TaxCalculationService(salt_rule_service)


def get_upload_services(
    excel_service: ExcelService = Depends(get_excel_service),
    file_handling_service: FileHandlingService = Depends(get_file_handling_service),
    session_service: SessionService = Depends(get_session_service),
    salt_rule_service: SaltRuleService = Depends(get_salt_rule_service),
    tax_calculation_service: TaxCalculationService = Depends(get_tax_calculation_service),
) -> UploadServiceDependencies:
    """Get all upload services with proper dependency injection."""
    return UploadServiceDependencies(
        excel_service=excel_service,
        file_handling_service=file_handling_service,
        session_service=session_service,
        salt_rule_service=salt_rule_service,
        tax_calculation_service=tax_calculation_service,
    )