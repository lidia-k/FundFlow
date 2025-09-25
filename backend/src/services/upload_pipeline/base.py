"""Base class for upload pipeline steps."""

from abc import ABC, abstractmethod

from ...models.upload_context import UploadContext


class UploadPipelineStep(ABC):
    """Abstract base class for upload pipeline steps."""

    @abstractmethod
    def execute(self, context: UploadContext) -> UploadContext:
        """
        Execute this pipeline step.

        Args:
            context: Upload context with current state

        Returns:
            UploadContext: Updated context after step execution

        Raises:
            UploadException: If step execution fails
        """
        pass

    @property
    @abstractmethod
    def step_name(self) -> str:
        """Name of this pipeline step for logging/debugging."""
        pass