"""Shared fixtures for integration tests."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def project_dir(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary project directory with basic structure and chdir into it.

    Creates:
    - prompts/ (local prompt directory)
    - .promptkit/cache/ (cached prompt content)

    Changes the working directory to the project dir for the test,
    then restores the original working directory on teardown.
    """
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    (d / ".promptkit" / "cache" / "plugins").mkdir(parents=True)

    original = os.getcwd()
    os.chdir(d)
    yield d
    os.chdir(original)


def write_config(project_dir: Path, config_yaml: str) -> None:
    """Write a promptkit.yaml config file to the project directory."""
    (project_dir / "promptkit.yaml").write_text(config_yaml)


def write_local_prompt(project_dir: Path, name: str, content: str) -> None:
    """Write a local prompt file to the prompts/ directory."""
    (project_dir / "prompts" / f"{name}.md").write_text(content)
