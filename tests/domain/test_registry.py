"""Tests for Registry value object and RegistryType enum."""

import pytest

from promptkit.domain.registry import Registry, RegistryType

DEFAULT_REGISTRY_TYPE = RegistryType.CLAUDE_MARKETPLACE


class TestRegistryType:
    def test_claude_marketplace_value(self) -> None:
        assert RegistryType.CLAUDE_MARKETPLACE.value == "claude-marketplace"

    def test_from_string(self) -> None:
        assert (
            RegistryType.from_string("claude-marketplace")
            == RegistryType.CLAUDE_MARKETPLACE
        )

    def test_from_string_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown registry type"):
            RegistryType.from_string("invalid")


class TestRegistry:
    def test_create_with_all_fields(self) -> None:
        registry = Registry(
            name="anthropic-agent-skills",
            registry_type=RegistryType.CLAUDE_MARKETPLACE,
            url="https://github.com/anthropics/skills",
        )
        assert registry.name == "anthropic-agent-skills"
        assert registry.registry_type == RegistryType.CLAUDE_MARKETPLACE
        assert registry.url == "https://github.com/anthropics/skills"

    def test_is_immutable(self) -> None:
        registry = Registry(
            name="test",
            registry_type=RegistryType.CLAUDE_MARKETPLACE,
            url="https://example.com",
        )
        with pytest.raises(AttributeError):
            registry.name = "other"  # type: ignore[misc]

    def test_equality_same_values(self) -> None:
        r1 = Registry(
            name="test",
            registry_type=RegistryType.CLAUDE_MARKETPLACE,
            url="https://example.com",
        )
        r2 = Registry(
            name="test",
            registry_type=RegistryType.CLAUDE_MARKETPLACE,
            url="https://example.com",
        )
        assert r1 == r2

    def test_default_type_is_claude_marketplace(self) -> None:
        """Registry type should default to claude-marketplace."""
        registry = Registry(
            name="test",
            url="https://example.com",
        )
        assert registry.registry_type == DEFAULT_REGISTRY_TYPE
