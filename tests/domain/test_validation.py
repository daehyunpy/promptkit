"""Tests for ValidationIssue and ValidationResult value objects."""

import pytest

from promptkit.domain.validation import (
    LEVEL_ERROR,
    LEVEL_WARNING,
    ValidationIssue,
    ValidationResult,
)


class TestValidationIssue:
    def test_create_error_issue(self) -> None:
        issue = ValidationIssue(level=LEVEL_ERROR, message="bad config")
        assert issue.level == LEVEL_ERROR
        assert issue.message == "bad config"

    def test_create_warning_issue(self) -> None:
        issue = ValidationIssue(level=LEVEL_WARNING, message="stale lock")
        assert issue.level == LEVEL_WARNING
        assert issue.message == "stale lock"

    def test_is_immutable(self) -> None:
        issue = ValidationIssue(level=LEVEL_ERROR, message="test")
        with pytest.raises(AttributeError):
            issue.level = "warning"  # type: ignore[misc]


class TestValidationResult:
    def test_is_valid_with_no_issues(self) -> None:
        result = ValidationResult()
        assert result.is_valid is True

    def test_is_valid_with_warnings_only(self) -> None:
        result = ValidationResult(
            issues=(ValidationIssue(level=LEVEL_WARNING, message="warn"),)
        )
        assert result.is_valid is True

    def test_is_not_valid_with_errors(self) -> None:
        result = ValidationResult(
            issues=(ValidationIssue(level=LEVEL_ERROR, message="err"),)
        )
        assert result.is_valid is False

    def test_is_not_valid_with_mixed_issues(self) -> None:
        result = ValidationResult(
            issues=(
                ValidationIssue(level=LEVEL_WARNING, message="warn"),
                ValidationIssue(level=LEVEL_ERROR, message="err"),
            )
        )
        assert result.is_valid is False

    def test_errors_property_filters_errors(self) -> None:
        result = ValidationResult(
            issues=(
                ValidationIssue(level=LEVEL_WARNING, message="warn"),
                ValidationIssue(level=LEVEL_ERROR, message="err"),
            )
        )
        assert len(result.errors) == 1
        assert result.errors[0].message == "err"

    def test_warnings_property_filters_warnings(self) -> None:
        result = ValidationResult(
            issues=(
                ValidationIssue(level=LEVEL_WARNING, message="warn"),
                ValidationIssue(level=LEVEL_ERROR, message="err"),
            )
        )
        assert len(result.warnings) == 1
        assert result.warnings[0].message == "warn"
