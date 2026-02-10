"""Tests for ClaudeBuilder."""

from pathlib import Path

import pytest

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt import Prompt
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.builders.claude_builder import ClaudeBuilder
from promptkit.infra.file_system.local import FileSystem


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".claude"
    d.mkdir()
    return d


@pytest.fixture
def builder() -> ClaudeBuilder:
    return ClaudeBuilder(FileSystem())


class TestCategoryRouting:
    def test_routes_skills_to_skills(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompt = Prompt(
            spec=PromptSpec(source="local/skills/my-skill"), content="# Skill"
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "skills" / "my-skill.md").read_text() == "# Skill"

    def test_routes_rules_to_rules(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompt = Prompt(
            spec=PromptSpec(source="local/rules/my-rule"), content="# Rule"
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "rules" / "my-rule.md").read_text() == "# Rule"

    def test_routes_agents_to_agents(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompt = Prompt(
            spec=PromptSpec(source="local/agents/my-agent"), content="# Agent"
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "agents" / "my-agent.md").read_text() == "# Agent"

    def test_routes_commands_to_commands(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompt = Prompt(
            spec=PromptSpec(source="local/commands/my-cmd"), content="# Command"
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "commands" / "my-cmd.md").read_text() == "# Command"

    def test_routes_subagents_to_subagents(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompt = Prompt(
            spec=PromptSpec(source="local/subagents/my-sub"), content="# Subagent"
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "subagents" / "my-sub.md").read_text() == "# Subagent"


class TestFlatSourceDefault:
    def test_flat_source_defaults_to_rules(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompt = Prompt(
            spec=PromptSpec(source="local/my-rule"), content="# Rule"
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "rules" / "my-rule.md").read_text() == "# Rule"


class TestContentPreservation:
    def test_copies_content_without_transformation(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        content = "---\nauthor: Test\n---\n\n# Prompt\n\nContent with frontmatter."
        prompt = Prompt(
            spec=PromptSpec(source="local/rules/my-rule"), content=content
        )

        builder.build([prompt], output_dir)

        assert (output_dir / "rules" / "my-rule.md").read_text() == content


class TestCleanBeforeWrite:
    def test_removes_stale_artifacts(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        stale_dir = output_dir / "rules"
        stale_dir.mkdir()
        (stale_dir / "old-rule.md").write_text("stale")

        new_prompt = Prompt(
            spec=PromptSpec(source="local/skills/new-skill"), content="# New"
        )

        builder.build([new_prompt], output_dir)

        assert not (output_dir / "rules" / "old-rule.md").exists()
        assert (output_dir / "skills" / "new-skill.md").exists()


class TestReturnPaths:
    def test_returns_generated_paths(
        self, builder: ClaudeBuilder, output_dir: Path
    ) -> None:
        prompts = [
            Prompt(spec=PromptSpec(source="local/rules/a"), content="A"),
            Prompt(spec=PromptSpec(source="local/rules/b"), content="B"),
            Prompt(spec=PromptSpec(source="local/skills/c"), content="C"),
        ]

        paths = builder.build(prompts, output_dir)

        assert len(paths) == 3
        assert output_dir / "rules" / "a.md" in paths
        assert output_dir / "rules" / "b.md" in paths
        assert output_dir / "skills" / "c.md" in paths


class TestPlatformProperty:
    def test_platform_returns_claude_code(self, builder: ClaudeBuilder) -> None:
        assert builder.platform == PlatformTarget.CLAUDE_CODE
