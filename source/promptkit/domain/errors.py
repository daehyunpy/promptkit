"""Domain layer: Domain-specific errors."""


class PromptError(Exception):
    """Base error for all promptkit domain errors."""


class SyncError(PromptError):
    """Error during prompt sync operations."""


class BuildError(PromptError):
    """Error during artifact build operations."""


class ValidationError(PromptError):
    """Error during configuration or prompt validation."""
