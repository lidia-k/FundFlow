"""Data processing step in upload pipeline."""

from ...exceptions.upload_exceptions import DataProcessingException, FundSourceDataException
from ...models.upload_context import UploadContext
from ...services.upload_dependencies import UploadServiceDependencies
from .base import UploadPipelineStep


class DataProcessingStep(UploadPipelineStep):
    """Pipeline step for processing parsed data into database entities."""

    def __init__(self, services: UploadServiceDependencies):
        self.services = services

    @property
    def step_name(self) -> str:
        return "data_processing"

    def execute(self, context: UploadContext) -> UploadContext:
        """Process parsed data and create database entities."""
        if not context.parsing_result:
            raise DataProcessingException("Parsing result not available")

        try:
            # Get or create default user
            context.user = self.services.user_service.get_or_create_default_user()

            # Create session
            context.session = self.services.session_service.create_session(
                user_id=context.user.id,
                upload_filename=str(context.temp_file_path.name) if context.temp_file_path else "",
                original_filename=context.file.filename,
                file_size=context.file.size or 0,
            )

            # Create or get fund
            context.fund = self._create_fund(context)

            # Process fund source data if present
            self._process_fund_source_data(context)

            # Process distribution data
            self._process_distribution_data(context)

            return context

        except (FundSourceDataException, ValueError) as e:
            raise DataProcessingException(f"Data processing failed: {str(e)}", "data_processing")
        except Exception as e:
            raise DataProcessingException(f"Unexpected error during data processing: {str(e)}")

    def _create_fund(self, context: UploadContext):
        """Create or retrieve fund entity."""
        try:
            return self.services.fund_service.get_or_create_fund(
                context.parsing_result.fund_info["fund_code"],
                context.parsing_result.fund_info["period_quarter"],
                int(context.parsing_result.fund_info["period_year"]),
            )
        except ValueError as e:
            raise DataProcessingException(f"Fund creation failed: {str(e)}", "fund_creation")

    def _process_fund_source_data(self, context: UploadContext):
        """Process fund source data if present."""
        if not context.parsing_result.fund_source_data:
            return

        try:
            # Validate fund source data constraints
            validation_errors = (
                self.services.fund_source_data_service.validate_fund_source_data_constraints(
                    context.fund.fund_code,
                    context.parsing_result.fund_source_data,
                    context.session.session_id,
                )
            )

            if validation_errors:
                raise FundSourceDataException(
                    f"Fund source data validation failed: {'; '.join(validation_errors)}",
                    validation_errors
                )

            # Create fund source data records
            fund_source_records = (
                self.services.fund_source_data_service.create_fund_source_data(
                    context.fund, context.session.session_id, context.parsing_result.fund_source_data
                )
            )
            context.fund_source_data_created = len(fund_source_records)

        except FundSourceDataException:
            # Re-raise fund source data exceptions as-is
            raise
        except Exception as e:
            raise DataProcessingException(f"Fund source data processing failed: {str(e)}", "fund_source_data")

    def _process_distribution_data(self, context: UploadContext):
        """Process distribution data for all investors."""
        try:
            context.distributions_created = 0

            for row_data in context.parsing_result.data:
                # Find or create investor
                investor = self.services.investor_service.find_or_create_investor(
                    row_data["investor_name"],
                    row_data["investor_entity_type"],
                    row_data["investor_tax_state"],
                )

                # Handle commitment percentage if present
                commitment_percentage = row_data.get("commitment_percentage")
                if commitment_percentage is not None:
                    self.services.investor_service.upsert_commitment(
                        investor=investor,
                        fund=context.fund,
                        commitment_percentage=commitment_percentage,
                    )

                # Create distributions
                distributions = self.services.distribution_service.create_distributions_for_investor(
                    investor=investor,
                    session_id=context.session.session_id,
                    fund=context.fund,
                    parsed_row=row_data,
                )
                context.distributions_created += len(distributions)

        except Exception as e:
            raise DataProcessingException(f"Distribution processing failed: {str(e)}", "distribution_processing")
