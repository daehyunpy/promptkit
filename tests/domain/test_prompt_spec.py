"""Tests for PromptSpec value object."""

import pytest

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_spec import PromptSpec


class TestPromptSpec:
    def test_create_with_source_only(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        assert spec.source == "claude-plugins-official/code-review"
        assert spec.name == "code-review"
        assert spec.platforms == ()

    def test_name_derived_from_source(self) -> None:
        spec = PromptSpec(source="anthropic-agent-skills/feature-dev")
        assert spec.name == "feature-dev"

    def test_explicit_name_overrides_derived(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/code-review",
            name="my-reviewer",
        )
        assert spec.name == "my-reviewer"

    def test_create_with_platforms(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/code-review",
            platforms=(PlatformTarget.CURSOR,),
        )
        assert spec.platforms == (PlatformTarget.CURSOR,)

    def test_create_with_all_fields(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/code-review",
            name="my-reviewer",
            platforms=(PlatformTarget.CURSOR, PlatformTarget.CLAUDE_CODE),
        )
        assert spec.source == "claude-plugins-official/code-review"
        assert spec.name == "my-reviewer"
        assert len(spec.platforms) == 2

    def test_is_immutable(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        with pytest.raises(AttributeError):
            spec.name = "other"  # type: ignore[misc]

    def test_targets_platform_when_included(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/code-review",
            platforms=(PlatformTarget.CURSOR,),
        )
        assert spec.targets_platform(PlatformTarget.CURSOR) is True

    def test_does_not_target_platform_when_excluded(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/code-review",
            platforms=(PlatformTarget.CURSOR,),
        )
        assert spec.targets_platform(PlatformTarget.CLAUDE_CODE) is False

    def test_targets_all_platforms_when_empty(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        assert spec.targets_platform(PlatformTarget.CURSOR) is True
        assert spec.targets_platform(PlatformTarget.CLAUDE_CODE) is True

    def test_registry_name_extracted_from_source(self) -> None:
        spec = PromptSpec(source="anthropic-agent-skills/feature-dev")
        assert spec.registry_name == "anthropic-agent-skills"

    def test_prompt_name_extracted_from_source(self) -> None:
        spec = PromptSpec(source="anthropic-agent-skills/feature-dev")
        assert spec.prompt_name == "feature-dev"

    def test_equality_same_values(self) -> None:
        s1 = PromptSpec(source="claude-plugins-official/code-review")
        s2 = PromptSpec(source="claude-plugins-official/code-review")
        assert s1 == s2
