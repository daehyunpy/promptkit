"""Domain layer: Validation result value objects."""

from dataclasses import dataclass, field
from typing import Literal

LEVEL_ERROR: Literal["error"] = "error"
LEVEL_WARNING: Literal["warning"] = "warning"

ValidationLevel = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue found during config validation."""

    level: ValidationLevel
    message: str


@dataclass(frozen=True)
class ValidationResult:
    """Collected validation issues from a config validation run."""

    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """True if no error-level issues exist (warnings are acceptable)."""
        return not any(issue.level == LEVEL_ERROR for issue in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        """All error-level issues."""
        return [i for i in self.issues if i.level == LEVEL_ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """All warning-level issues."""
        return [i for i in self.issues if i.level == LEVEL_WARNING]
