"""Tests for Plugin domain value object."""

from pathlib import Path

import pytest

from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec


class TestPluginConstruction:
    def test_creates_registry_plugin(self) -> None:
        spec = PromptSpec(source="my-registry/code-review")
        plugin = Plugin(
            spec=spec,
            files=("agents/reviewer.md", "hooks/hooks.json"),
            source_dir=Path("/cache/my-registry/code-review/abc123"),
            commit_sha="abc123",
        )
        assert plugin.spec is spec
        assert plugin.files == ("agents/reviewer.md", "hooks/hooks.json")
        assert plugin.source_dir == Path("/cache/my-registry/code-review/abc123")
        assert plugin.commit_sha == "abc123"

    def test_creates_local_plugin(self) -> None:
        spec = PromptSpec(source="local/my-rule")
        plugin = Plugin(
            spec=spec,
            files=("my-rule.md",),
            source_dir=Path("/project/prompts"),
        )
        assert plugin.commit_sha is None

    def test_creates_local_directory_plugin(self) -> None:
        spec = PromptSpec(source="local/my-skill")
        plugin = Plugin(
            spec=spec,
            files=("my-skill/SKILL.md", "my-skill/scripts/check.sh"),
            source_dir=Path("/project/prompts"),
        )
        assert plugin.files == ("my-skill/SKILL.md", "my-skill/scripts/check.sh")
        assert plugin.commit_sha is None


class TestPluginFrozen:
    def test_is_immutable(self) -> None:
        plugin = Plugin(
            spec=PromptSpec(source="local/test"),
            files=("test.md",),
            source_dir=Path("/tmp"),
        )
        with pytest.raises(AttributeError):
            plugin.commit_sha = "new-sha"  # type: ignore[misc]


class TestPluginProperties:
    def test_name_delegates_to_spec(self) -> None:
        plugin = Plugin(
            spec=PromptSpec(source="local/my-rule"),
            files=("my-rule.md",),
            source_dir=Path("/tmp"),
        )
        assert plugin.name == "my-rule"

    def test_source_delegates_to_spec(self) -> None:
        plugin = Plugin(
            spec=PromptSpec(source="local/my-rule"),
            files=("my-rule.md",),
            source_dir=Path("/tmp"),
        )
        assert plugin.source == "local/my-rule"

    def test_is_registry_true_for_registry_plugin(self) -> None:
        plugin = Plugin(
            spec=PromptSpec(source="my-registry/code-review"),
            files=("agents/reviewer.md",),
            source_dir=Path("/cache"),
            commit_sha="abc123",
        )
        assert plugin.is_registry is True

    def test_is_registry_false_for_local_plugin(self) -> None:
        plugin = Plugin(
            spec=PromptSpec(source="local/my-rule"),
            files=("my-rule.md",),
            source_dir=Path("/tmp"),
        )
        assert plugin.is_registry is False
