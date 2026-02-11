"""End-to-end integration tests for the build command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from promptkit.cli import app

from .conftest import write_config, write_local_prompt

runner = CliRunner()

CURSOR_ONLY_CONFIG = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: .cursor
"""

CLAUDE_ONLY_CONFIG = """\
version: 1
prompts: []
platforms:
  claude-code:
    output_dir: .claude
"""

BOTH_PLATFORMS_CONFIG = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: .cursor
  claude-code:
    output_dir: .claude
"""


def _init_and_lock(project_dir: Path, config: str, prompts: dict[str, str]) -> None:
    """Write config and prompts, then run lock to create a real lock file."""
    write_config(project_dir, config)
    for name, content in prompts.items():
        write_local_prompt(project_dir, name, content)
    result = runner.invoke(app, ["lock"])
    assert result.exit_code == 0


@pytest.mark.integration
class TestBuildEndToEnd:
    """Integration tests that verify build generates real platform artifacts."""

    def test_build_generates_cursor_artifact_from_local_prompt(
        self, project_dir: Path
    ) -> None:
        _init_and_lock(
            project_dir,
            CURSOR_ONLY_CONFIG,
            {"my-rule": "# My Rule\nFollow this rule."},
        )

        result = runner.invoke(app, ["build"])

        assert result.exit_code == 0
        artifact = project_dir / ".cursor" / "rules" / "my-rule.md"
        assert artifact.exists()
        assert "Follow this rule." in artifact.read_text()

    def test_build_generates_claude_code_artifact_from_local_prompt(
        self, project_dir: Path
    ) -> None:
        _init_and_lock(
            project_dir,
            CLAUDE_ONLY_CONFIG,
            {"my-rule": "# My Rule\nFollow this rule."},
        )

        result = runner.invoke(app, ["build"])

        assert result.exit_code == 0
        artifact = project_dir / ".claude" / "rules" / "my-rule.md"
        assert artifact.exists()
        assert "Follow this rule." in artifact.read_text()

    def test_build_generates_artifacts_for_both_platforms(
        self, project_dir: Path
    ) -> None:
        _init_and_lock(
            project_dir,
            BOTH_PLATFORMS_CONFIG,
            {"my-rule": "# My Rule\nDual platform content."},
        )

        result = runner.invoke(app, ["build"])

        assert result.exit_code == 0
        assert (project_dir / ".cursor" / "rules" / "my-rule.md").exists()
        assert (project_dir / ".claude" / "rules" / "my-rule.md").exists()

    def test_build_fails_without_lock_file(self, project_dir: Path) -> None:
        write_config(project_dir, BOTH_PLATFORMS_CONFIG)

        result = runner.invoke(app, ["build"])

        assert result.exit_code == 1
        assert "Error" in result.output
