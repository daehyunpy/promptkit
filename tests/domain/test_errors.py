"""Tests for domain errors."""

from promptkit.domain.errors import (
    BuildError,
    PromptError,
    SyncError,
    ValidationError,
)


class TestPromptError:
    def test_is_exception(self) -> None:
        assert issubclass(PromptError, Exception)

    def test_message_preserved(self) -> None:
        error = PromptError("something went wrong")
        assert str(error) == "something went wrong"


class TestSyncError:
    def test_inherits_from_prompt_error(self) -> None:
        assert issubclass(SyncError, PromptError)

    def test_message_preserved(self) -> None:
        error = SyncError("sync failed")
        assert str(error) == "sync failed"


class TestBuildError:
    def test_inherits_from_prompt_error(self) -> None:
        assert issubclass(BuildError, PromptError)

    def test_message_preserved(self) -> None:
        error = BuildError("build failed")
        assert str(error) == "build failed"


class TestValidationError:
    def test_inherits_from_prompt_error(self) -> None:
        assert issubclass(ValidationError, PromptError)

    def test_message_preserved(self) -> None:
        error = ValidationError("invalid config")
        assert str(error) == "invalid config"
