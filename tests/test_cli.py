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


def test_init_command_shows_help_text() -> None:
    """init command should show helpful documentation."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Initialize a new promptkit project" in result.stdout


def test_init_command_creates_expected_files(working_dir: Path) -> None:
    """init command should create all required files and directories."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0

    assert (working_dir / ".promptkit" / "cache").exists()
    assert (working_dir / ".agents").exists()
    assert (working_dir / ".cursor").exists()
    assert (working_dir / ".claude").exists()
    assert (working_dir / "promptkit.yaml").exists()
    assert (working_dir / "promptkit.lock").exists()
    assert (working_dir / ".gitignore").exists()


def test_init_command_fails_when_config_exists(working_dir: Path) -> None:
    """init command should fail when promptkit.yaml already exists."""
    (working_dir / "promptkit.yaml").write_text("existing")

    result = runner.invoke(app, [])

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_success_message_is_displayed(working_dir: Path) -> None:
    """init command should display success message with next steps."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0

    assert "Initialized promptkit project" in result.stdout
    assert "Created files and directories:" in result.stdout
    assert "promptkit.yaml" in result.stdout
    assert "Next steps:" in result.stdout
    assert "promptkit sync" in result.stdout
    assert "promptkit build" in result.stdout


def test_exit_code_zero_on_success(working_dir: Path) -> None:
    """init command should exit with code 0 on success."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0


def test_exit_code_one_on_failure(working_dir: Path) -> None:
    """init command should exit with code 1 on failure."""
    (working_dir / "promptkit.yaml").write_text("existing")

    result = runner.invoke(app, [])
    assert result.exit_code == 1


def test_generated_config_is_valid_yaml(working_dir: Path) -> None:
    """init command should generate valid YAML configuration."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0

    config = yaml.safe_load((working_dir / "promptkit.yaml").read_text())
    assert config["version"] == 1
    assert "prompts" in config
    assert "platforms" in config
