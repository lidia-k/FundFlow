"""Factory for creating upload-related services."""

from dataclasses import dataclass
from sqlalchemy.orm import Session

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

    # Core services
    user_service: UserService
    session_service: SessionService
    excel_service: ExcelService
    investor_service: InvestorService
    fund_service: FundService
    fund_source_data_service: FundSourceDataService
    distribution_service: DistributionService
    tax_calculation_service: TaxCalculationService

    # Validators
    file_validator: FileValidator
    excel_validator: ExcelValidator


class UploadServiceFactory:
    """Factory for creating upload service dependencies."""

    @staticmethod
    def create(db: Session) -> UploadServiceDependencies:
        """
        Create all upload service dependencies.

        Args:
            db: Database session

        Returns:
            UploadServiceDependencies: Container with all services
        """
        return UploadServiceDependencies(
            # Core services
            user_service=UserService(db),
            session_service=SessionService(db),
            excel_service=ExcelService(),
            investor_service=InvestorService(db),
            fund_service=FundService(db),
            fund_source_data_service=FundSourceDataService(db),
            distribution_service=DistributionService(db),
            tax_calculation_service=TaxCalculationService(db),
            # Validators
            file_validator=FileValidator(),
            excel_validator=ExcelValidator(),
        )