"""Tests for InitProject use case."""

from pathlib import Path

import pytest
import yaml

from promptkit.app.init import InitProject, InitProjectError
from promptkit.infra.config_serializer import serialize_config_to_yaml
from promptkit.infra.file_system.local import FileSystem


def _make_use_case() -> InitProject:
    return InitProject(FileSystem(), serialize_config_to_yaml)


def test_execute_creates_all_required_directories(tmp_path: Path) -> None:
    """execute should create .promptkit/cache/, prompts/, .cursor/, .claude/."""
    _make_use_case().execute(tmp_path)

    assert (tmp_path / ".promptkit" / "cache").exists()
    assert (tmp_path / "prompts").exists()
    assert (tmp_path / ".cursor").exists()
    assert (tmp_path / ".claude").exists()


def test_execute_generates_valid_promptkit_yaml(tmp_path: Path) -> None:
    """execute should generate valid promptkit.yaml."""
    _make_use_case().execute(tmp_path)

    config_path = tmp_path / "promptkit.yaml"
    assert config_path.exists()

    config = yaml.safe_load(config_path.read_text())
    assert config["version"] == 1
    assert "prompts" in config
    assert "platforms" in config


def test_execute_creates_promptkit_lock(tmp_path: Path) -> None:
    """execute should create promptkit.lock."""
    _make_use_case().execute(tmp_path)

    lock_path = tmp_path / "promptkit.lock"
    assert lock_path.exists()

    lock = yaml.safe_load(lock_path.read_text())
    assert lock["version"] == 1


def test_execute_fails_when_promptkit_yaml_exists(tmp_path: Path) -> None:
    """execute should raise InitProjectError if promptkit.yaml exists."""
    (tmp_path / "promptkit.yaml").write_text("existing")

    with pytest.raises(InitProjectError, match="already exists"):
        _make_use_case().execute(tmp_path)


def test_creates_promptkit_gitignore(tmp_path: Path) -> None:
    """execute should create .promptkit/.gitignore that ignores all contents."""
    _make_use_case().execute(tmp_path)

    gitignore = tmp_path / ".promptkit" / ".gitignore"
    assert gitignore.exists()
    assert "*" in gitignore.read_text()


def test_does_not_create_root_gitignore(tmp_path: Path) -> None:
    """execute should not create a root .gitignore."""
    _make_use_case().execute(tmp_path)

    assert not (tmp_path / ".gitignore").exists()


def test_execute_does_not_modify_files_when_config_exists(tmp_path: Path) -> None:
    """execute should not create directories when config exists."""
    (tmp_path / "promptkit.yaml").write_text("existing")

    with pytest.raises(InitProjectError):
        _make_use_case().execute(tmp_path)

    assert not (tmp_path / "prompts").exists()
    assert not (tmp_path / ".cursor").exists()
