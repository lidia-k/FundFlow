"""FastAPI dependency injection for upload services."""

from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database.connection import get_db
from .distribution_service import DistributionService
from .excel_service import ExcelService
from .fund_service import FundService
from .fund_source_data_service import FundSourceDataService
from .investor_service import InvestorService
from .session_service import SessionService
from .tax_calculation_service import TaxCalculationService
from .user_service import UserService
from .validators import ExcelValidator, FileValidator


@dataclass
class UploadServiceDependencies:
    """Container for all upload-related service dependencies."""

    user_service: UserService
    session_service: SessionService
    excel_service: ExcelService
    investor_service: InvestorService
    fund_service: FundService
    fund_source_data_service: FundSourceDataService
    distribution_service: DistributionService
    tax_calculation_service: TaxCalculationService
    file_validator: FileValidator
    excel_validator: ExcelValidator


@lru_cache()
def get_excel_service() -> ExcelService:
    """Get Excel service singleton."""
    return ExcelService()


@lru_cache()
def get_file_validator() -> FileValidator:
    """Get file validator singleton."""
    return FileValidator()


@lru_cache()
def get_excel_validator() -> ExcelValidator:
    """Get Excel validator singleton."""
    return ExcelValidator()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get user service with database dependency."""
    return UserService(db)


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """Get session service with database dependency."""
    return SessionService(db)


def get_investor_service(db: Session = Depends(get_db)) -> InvestorService:
    """Get investor service with database dependency."""
    return InvestorService(db)


def get_fund_service(db: Session = Depends(get_db)) -> FundService:
    """Get fund service with database dependency."""
    return FundService(db)


def get_fund_source_data_service(db: Session = Depends(get_db)) -> FundSourceDataService:
    """Get fund source data service with database dependency."""
    return FundSourceDataService(db)


def get_distribution_service(db: Session = Depends(get_db)) -> DistributionService:
    """Get distribution service with database dependency."""
    return DistributionService(db)


def get_tax_calculation_service(db: Session = Depends(get_db)) -> TaxCalculationService:
    """Get tax calculation service with database dependency."""
    return TaxCalculationService(db)


def get_upload_services(
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
    excel_service: ExcelService = Depends(get_excel_service),
    investor_service: InvestorService = Depends(get_investor_service),
    fund_service: FundService = Depends(get_fund_service),
    fund_source_data_service: FundSourceDataService = Depends(get_fund_source_data_service),
    distribution_service: DistributionService = Depends(get_distribution_service),
    tax_calculation_service: TaxCalculationService = Depends(get_tax_calculation_service),
    file_validator: FileValidator = Depends(get_file_validator),
    excel_validator: ExcelValidator = Depends(get_excel_validator),
) -> UploadServiceDependencies:
    """Get all upload services with proper dependency injection."""
    return UploadServiceDependencies(
        user_service=user_service,
        session_service=session_service,
        excel_service=excel_service,
        investor_service=investor_service,
        fund_service=fund_service,
        fund_source_data_service=fund_source_data_service,
        distribution_service=distribution_service,
        tax_calculation_service=tax_calculation_service,
        file_validator=file_validator,
        excel_validator=excel_validator,
    )
