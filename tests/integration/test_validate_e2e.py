"""End-to-end integration tests for the validate command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from promptkit.cli import app
from promptkit.domain.lock_entry import LockEntry
from promptkit.infra.config.lock_file import LockFile

from .conftest import write_config, write_local_prompt

runner = CliRunner()

VALID_CONFIG = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: .cursor
"""


def _write_lock_file(project_dir: Path, entries: list[LockEntry]) -> None:
    """Write a lock file with the given entries."""
    content = LockFile.serialize(entries)
    (project_dir / "promptkit.lock").write_text(content)


@pytest.mark.integration
class TestValidateEndToEnd:
    """Integration tests that verify validate checks real config and lock files."""

    def test_validate_passes_on_valid_config_with_fresh_lock(
        self, project_dir: Path
    ) -> None:
        write_config(project_dir, VALID_CONFIG)
        write_local_prompt(project_dir, "my-rule", "# My Rule")
        runner.invoke(app, ["lock"])

        result = runner.invoke(app, ["validate"])

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_validate_warns_on_missing_lock_file(self, project_dir: Path) -> None:
        write_config(project_dir, VALID_CONFIG)

        result = runner.invoke(app, ["validate"])

        assert result.exit_code == 0
        assert "lock" in result.output.lower()

    def test_validate_errors_on_undefined_registry(self, project_dir: Path) -> None:
        config_with_bad_registry = """\
version: 1
registries:
  my-registry: https://example.com/registry
prompts:
  - nonexistent-registry/some-prompt
platforms:
  cursor:
    output_dir: .cursor
"""
        write_config(project_dir, config_with_bad_registry)

        result = runner.invoke(app, ["validate"])

        assert result.exit_code == 1
        assert "undefined" in result.output.lower()

    def test_validate_warns_on_stale_lock_entries(self, project_dir: Path) -> None:
        from datetime import datetime, timezone

        # Config with no remote prompts
        write_config(project_dir, VALID_CONFIG)

        # Manually write a lock file with a non-local stale entry
        stale_entry = LockEntry(
            name="old-prompt",
            source="some-registry/old-prompt",
            content_hash="sha256:" + "a" * 64,
            fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        _write_lock_file(project_dir, [stale_entry])

        result = runner.invoke(app, ["validate"])

        assert result.exit_code == 0
        assert "stale" in result.output.lower()
