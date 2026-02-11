"""End-to-end integration tests for the sync command."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from promptkit.cli import app

from .conftest import write_config, write_local_prompt

runner = CliRunner()

BOTH_PLATFORMS_CONFIG = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: .cursor
  claude-code:
    output_dir: .claude
"""


@pytest.mark.integration
class TestSyncEndToEnd:
    """Integration tests that verify sync performs lock + build end-to-end."""

    def test_sync_locks_and_builds_local_prompt(self, project_dir: Path) -> None:
        write_config(project_dir, BOTH_PLATFORMS_CONFIG)
        write_local_prompt(project_dir, "my-rule", "# My Rule\nContent here.")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0

        # Lock file created with entry
        lock_data = yaml.safe_load((project_dir / "promptkit.lock").read_text())
        assert len(lock_data["prompts"]) == 1
        assert lock_data["prompts"][0]["source"] == "local/rules/my-rule"

        # Artifacts generated for both platforms under rules/
        assert (project_dir / ".cursor" / "rules" / "my-rule.md").exists()
        assert (project_dir / ".claude" / "rules" / "my-rule.md").exists()

    def test_sync_with_multiple_local_prompts(self, project_dir: Path) -> None:
        write_config(project_dir, BOTH_PLATFORMS_CONFIG)
        write_local_prompt(project_dir, "rule-one", "# Rule One")
        write_local_prompt(project_dir, "rule-two", "# Rule Two")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0

        # Lock file has entries for both prompts
        lock_data = yaml.safe_load((project_dir / "promptkit.lock").read_text())
        sources = {p["source"] for p in lock_data["prompts"]}
        assert sources == {"local/rules/rule-one", "local/rules/rule-two"}

        # Artifacts exist for both prompts on both platforms
        for name in ("rule-one", "rule-two"):
            assert (project_dir / ".cursor" / "rules" / f"{name}.md").exists()
            assert (project_dir / ".claude" / "rules" / f"{name}.md").exists()
