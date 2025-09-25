"""Tax calculation step in upload pipeline."""

from ...exceptions.upload_exceptions import TaxCalculationException
from ...models.upload_context import UploadContext
from ...services.upload_dependencies import UploadServiceDependencies
from .base import UploadPipelineStep


class TaxCalculationStep(UploadPipelineStep):
    """Pipeline step for applying SALT tax calculations."""

    def __init__(self, services: UploadServiceDependencies):
        self.services = services

    @property
    def step_name(self) -> str:
        return "tax_calculation"

    def execute(self, context: UploadContext) -> UploadContext:
        """Apply SALT tax calculations to the session."""
        if not context.session:
            raise TaxCalculationException("Session not available for tax calculation")

        try:
            # Flush to ensure all data is committed before tax calculations
            context.db_session.flush()

            # Apply tax calculations
            self.services.tax_calculation_service.apply_for_session(context.session.session_id)

            return context

        except Exception as e:
            raise TaxCalculationException(f"Tax calculation failed: {str(e)}")
