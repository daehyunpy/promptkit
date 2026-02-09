"""Tests for PromptSpec value object."""

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_spec import ArtifactType, PromptSpec


class TestArtifactType:
    def test_skill_value(self) -> None:
        assert ArtifactType.SKILL.value == "skill"

    def test_rule_value(self) -> None:
        assert ArtifactType.RULE.value == "rule"

    def test_agent_value(self) -> None:
        assert ArtifactType.AGENT.value == "agent"

    def test_command_value(self) -> None:
        assert ArtifactType.COMMAND.value == "command"

    def test_subagent_value(self) -> None:
        assert ArtifactType.SUBAGENT.value == "subagent"

    def test_from_string(self) -> None:
        assert ArtifactType.from_string("skill") == ArtifactType.SKILL

    def test_from_string_invalid_raises(self) -> None:
        try:
            ArtifactType.from_string("invalid")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "invalid" in str(e)


class TestPromptSpec:
    def test_create_with_required_fields(self) -> None:
        spec = PromptSpec(
            name="code-reviewer",
            source="anthropic/code-reviewer",
        )
        assert spec.name == "code-reviewer"
        assert spec.source == "anthropic/code-reviewer"
        assert spec.platforms == ()
        assert spec.artifact_type is None

    def test_create_with_all_fields(self) -> None:
        spec = PromptSpec(
            name="code-reviewer",
            source="anthropic/code-reviewer",
            platforms=(PlatformTarget.CURSOR, PlatformTarget.CLAUDE_CODE),
            artifact_type=ArtifactType.SKILL,
        )
        assert spec.name == "code-reviewer"
        assert spec.source == "anthropic/code-reviewer"
        assert len(spec.platforms) == 2
        assert spec.artifact_type == ArtifactType.SKILL

    def test_is_immutable(self) -> None:
        spec = PromptSpec(name="test", source="local/test")
        try:
            spec.name = "other"  # type: ignore[misc]
            assert False, "Expected FrozenInstanceError"
        except AttributeError:
            pass

    def test_is_local_source(self) -> None:
        spec = PromptSpec(name="test", source="local/test")
        assert spec.is_local_source is True

    def test_is_not_local_source(self) -> None:
        spec = PromptSpec(name="test", source="anthropic/code-reviewer")
        assert spec.is_local_source is False

    def test_targets_platform_when_included(self) -> None:
        spec = PromptSpec(
            name="test",
            source="local/test",
            platforms=(PlatformTarget.CURSOR,),
        )
        assert spec.targets_platform(PlatformTarget.CURSOR) is True

    def test_does_not_target_platform_when_excluded(self) -> None:
        spec = PromptSpec(
            name="test",
            source="local/test",
            platforms=(PlatformTarget.CURSOR,),
        )
        assert spec.targets_platform(PlatformTarget.CLAUDE_CODE) is False

    def test_targets_all_platforms_when_empty(self) -> None:
        spec = PromptSpec(name="test", source="local/test", platforms=())
        assert spec.targets_platform(PlatformTarget.CURSOR) is True
        assert spec.targets_platform(PlatformTarget.CLAUDE_CODE) is True

    def test_equality_same_values(self) -> None:
        s1 = PromptSpec(name="test", source="local/test")
        s2 = PromptSpec(name="test", source="local/test")
        assert s1 == s2
