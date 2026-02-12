"""Tests for CLI interface."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from promptkit.cli import app

runner = CliRunner()


@pytest.fixture
def working_dir(tmp_path: Path) -> Iterator[Path]:
    """Temporarily change the working directory to tmp_path."""
    original = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


def test_init_command_can_be_invoked() -> None:
    """init command should be invocable via CLI."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_app_help_shows_workflow_guidance() -> None:
    """App help should mention the init-to-sync workflow."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "promptkit init" in result.stdout
    assert "promptkit sync" in result.stdout


def test_init_command_shows_help_text() -> None:
    """init command should show helpful documentation."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Initialize a new promptkit project" in result.stdout


def test_init_command_creates_expected_files(working_dir: Path) -> None:
    """init command should create all required files and directories."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    assert (working_dir / ".promptkit" / "cache").exists()
    assert (working_dir / "prompts").exists()
    assert (working_dir / ".cursor").exists()
    assert (working_dir / ".claude").exists()
    assert (working_dir / "promptkit.yaml").exists()
    assert (working_dir / "promptkit.lock").exists()
    assert (working_dir / ".promptkit" / ".gitignore").exists()


def test_init_command_fails_when_config_exists(working_dir: Path) -> None:
    """init command should fail when promptkit.yaml already exists."""
    (working_dir / "promptkit.yaml").write_text("existing")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_success_message_is_displayed(working_dir: Path) -> None:
    """init command should display success message with next steps."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    assert "Initialized promptkit project" in result.stdout
    assert "Next steps:" in result.stdout
    assert "promptkit sync" in result.stdout


def test_exit_code_zero_on_success(working_dir: Path) -> None:
    """init command should exit with code 0 on success."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0


def test_exit_code_one_on_failure(working_dir: Path) -> None:
    """init command should exit with code 1 on failure."""
    (working_dir / "promptkit.yaml").write_text("existing")

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1


def test_generated_config_is_valid_yaml(working_dir: Path) -> None:
    """init command should generate valid YAML configuration."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    config = yaml.safe_load((working_dir / "promptkit.yaml").read_text())
    assert config["version"] == 1
    assert "prompts" in config
    assert "platforms" in config


# --- lock command ---


def _scaffold_project(working_dir: Path) -> None:
    """Set up a minimal promptkit project for lock tests."""
    runner.invoke(app, ["init"])


def test_lock_command_shows_in_help() -> None:
    """lock command should appear in CLI help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "lock" in result.stdout


def test_lock_succeeds_with_local_prompts(working_dir: Path) -> None:
    """lock command should lock local prompts and update lock file."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")

    result = runner.invoke(app, ["lock"])

    assert result.exit_code == 0
    assert "Locked 1 plugin" in result.stdout
    lock_content = yaml.safe_load((working_dir / "promptkit.lock").read_text())
    assert len(lock_content["prompts"]) == 1
    assert lock_content["prompts"][0]["source"] == "local/rules/my-rule"


def test_lock_fails_without_config(working_dir: Path) -> None:
    """lock command should show friendly error for missing config."""
    result = runner.invoke(app, ["lock"])

    assert result.exit_code == 1
    assert "promptkit.yaml not found" in result.output
    assert "promptkit init" in result.output


def test_lock_success_shows_plugin_count(working_dir: Path) -> None:
    """lock command should show how many plugins were locked."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "rule-a.md").write_text("# A")
    (working_dir / "prompts" / "rules" / "rule-b.md").write_text("# B")

    result = runner.invoke(app, ["lock"])

    assert result.exit_code == 0
    assert "Locked 2 plugins" in result.stdout


def test_lock_success_shows_singular_plugin(working_dir: Path) -> None:
    """lock command should use singular 'plugin' for count of 1."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# Rule")

    result = runner.invoke(app, ["lock"])

    assert result.exit_code == 0
    assert "Locked 1 plugin" in result.stdout


def test_lock_succeeds_with_no_prompts(working_dir: Path) -> None:
    """lock command should succeed when no prompts are configured."""
    _scaffold_project(working_dir)

    result = runner.invoke(app, ["lock"])

    assert result.exit_code == 0
    lock_content = yaml.safe_load((working_dir / "promptkit.lock").read_text())
    assert lock_content["prompts"] == []


# --- build command ---


def test_build_command_shows_in_help() -> None:
    """build command should appear in CLI help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "build" in result.stdout


def test_build_succeeds_with_local_prompts(working_dir: Path) -> None:
    """build command should generate artifacts from locked local prompts."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")
    # Lock first (lock-first workflow)
    runner.invoke(app, ["lock"])

    result = runner.invoke(app, ["build"])

    assert result.exit_code == 0
    assert "Built 1 plugin for 2 platforms" in result.stdout
    assert (working_dir / ".cursor" / "rules" / "my-rule.md").exists()
    assert (working_dir / ".claude" / "rules" / "my-rule.md").exists()


def test_build_fails_without_lock_file(working_dir: Path) -> None:
    """build command should show operation context in error."""
    _scaffold_project(working_dir)
    (working_dir / "promptkit.lock").unlink()

    result = runner.invoke(app, ["build"])

    assert result.exit_code == 1
    assert "Error building artifacts:" in result.output


def test_build_fails_without_config(working_dir: Path) -> None:
    """build command should show friendly error for missing config."""
    result = runner.invoke(app, ["build"])

    assert result.exit_code == 1
    assert "promptkit.yaml not found" in result.output
    assert "promptkit init" in result.output


# --- sync command ---


def test_sync_help_describes_all_in_one() -> None:
    """sync help should describe it as the all-in-one command."""
    result = runner.invoke(app, ["sync", "--help"])
    assert result.exit_code == 0
    assert "all-in-one" in result.stdout.lower()


def test_build_help_mentions_offline() -> None:
    """build help should note it works without network."""
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "no network" in result.stdout.lower() or "offline" in result.stdout.lower()


def test_sync_command_shows_in_help() -> None:
    """sync command should appear in CLI help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sync" in result.stdout


def test_sync_succeeds_with_local_prompts(working_dir: Path) -> None:
    """sync command should lock and build local prompts in one step."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")

    result = runner.invoke(app, ["sync"])

    assert result.exit_code == 0
    # Lock file should be updated
    lock_content = yaml.safe_load((working_dir / "promptkit.lock").read_text())
    assert len(lock_content["prompts"]) == 1
    assert lock_content["prompts"][0]["source"] == "local/rules/my-rule"
    # Artifacts should be generated
    assert (working_dir / ".cursor" / "rules" / "my-rule.md").exists()
    assert (working_dir / ".claude" / "rules" / "my-rule.md").exists()


def test_sync_fails_without_config(working_dir: Path) -> None:
    """sync command should show friendly error for missing config."""
    result = runner.invoke(app, ["sync"])

    assert result.exit_code == 1
    assert "promptkit.yaml not found" in result.output
    assert "promptkit init" in result.output


def test_sync_lock_failure_skips_build(working_dir: Path) -> None:
    """sync command should not attempt build when lock fails."""
    result = runner.invoke(app, ["sync"])

    assert result.exit_code == 1
    assert "Building" not in result.output


# --- validate command ---


def test_validate_command_shows_in_help() -> None:
    """validate command should appear in CLI help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.stdout


def test_validate_succeeds_with_valid_config(working_dir: Path) -> None:
    """validate command should exit 0 for a valid, locked config."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")
    runner.invoke(app, ["lock"])

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "valid" in result.stdout.lower()


def test_validate_fails_with_invalid_config(working_dir: Path) -> None:
    """validate command should exit 1 when config has errors."""
    _scaffold_project(working_dir)
    (working_dir / "promptkit.yaml").write_text("version: [[[invalid")

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()


def test_validate_fails_without_config(working_dir: Path) -> None:
    """validate command should exit 1 when no config file exists."""
    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()


# --- clean command ---


def test_clean_command_shows_in_help() -> None:
    """clean command should appear in CLI help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "clean" in result.stdout


def test_clean_succeeds_after_build(working_dir: Path) -> None:
    """clean command should remove managed artifacts after a build."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")
    runner.invoke(app, ["lock"])
    runner.invoke(app, ["build"])
    assert (working_dir / ".cursor" / "rules" / "my-rule.md").exists()

    result = runner.invoke(app, ["clean"])

    assert result.exit_code == 0
    assert "Cleaned build artifacts" in result.stdout
    assert not (working_dir / ".cursor" / "rules" / "my-rule.md").exists()


def test_clean_nothing_to_clean(working_dir: Path) -> None:
    """clean command should report nothing when no manifests exist."""
    result = runner.invoke(app, ["clean"])

    assert result.exit_code == 0
    assert "Nothing to clean" in result.stdout


def test_clean_with_cache_flag(working_dir: Path) -> None:
    """clean command with --cache should also remove cache directory."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")
    runner.invoke(app, ["lock"])
    runner.invoke(app, ["build"])
    (working_dir / ".promptkit" / "cache" / "plugins").mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["clean", "--cache"])

    assert result.exit_code == 0
    assert "Cleaned build artifacts and cache" in result.stdout
    assert not (working_dir / ".promptkit" / "cache").exists()


def test_validate_shows_warnings_with_exit_zero(working_dir: Path) -> None:
    """validate command should show warnings but exit 0 when no errors."""
    _scaffold_project(working_dir)
    (working_dir / "prompts" / "rules").mkdir(parents=True, exist_ok=True)
    (working_dir / "prompts" / "rules" / "my-rule.md").write_text("# My Rule")
    # Don't lock — so there will be a "no lock file" warning
    (working_dir / "promptkit.lock").unlink()

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "warning" in result.output.lower()
