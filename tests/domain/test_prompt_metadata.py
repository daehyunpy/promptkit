"""Tests for PromptMetadata value object."""

from promptkit.domain.prompt_metadata import PromptMetadata


class TestPromptMetadata:
    def test_create_with_all_fields(self) -> None:
        metadata = PromptMetadata(
            author="Anthropic",
            description="Reviews code for bugs",
            version="1.0.0",
        )
        assert metadata.author == "Anthropic"
        assert metadata.description == "Reviews code for bugs"
        assert metadata.version == "1.0.0"

    def test_create_with_defaults(self) -> None:
        metadata = PromptMetadata()
        assert metadata.author is None
        assert metadata.description is None
        assert metadata.version is None

    def test_is_immutable(self) -> None:
        metadata = PromptMetadata(author="Anthropic")
        try:
            metadata.author = "Other"  # type: ignore[misc]
            assert False, "Expected FrozenInstanceError"
        except AttributeError:
            pass

    def test_equality_same_values(self) -> None:
        m1 = PromptMetadata(author="Anthropic", description="desc", version="1.0.0")
        m2 = PromptMetadata(author="Anthropic", description="desc", version="1.0.0")
        assert m1 == m2

    def test_equality_different_values(self) -> None:
        m1 = PromptMetadata(author="Anthropic")
        m2 = PromptMetadata(author="Other")
        assert m1 != m2
