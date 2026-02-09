"""Tests for InitProject use case."""

from pathlib import Path

import pytest
import yaml

from promptkit.app.init import InitProject, InitProjectError
from promptkit.infra.file_system.local import FileSystem


def test_execute_creates_all_required_directories(tmp_path: Path) -> None:
    """execute should create .promptkit/cache/, .agents/, .cursor/, .claude/."""
    fs = FileSystem()
    use_case = InitProject(fs)

    use_case.execute(tmp_path)

    assert (tmp_path / ".promptkit" / "cache").exists()
    assert (tmp_path / ".agents").exists()
    assert (tmp_path / ".cursor").exists()
    assert (tmp_path / ".claude").exists()


def test_execute_generates_valid_promptkit_yaml(tmp_path: Path) -> None:
    """execute should generate valid promptkit.yaml."""
    fs = FileSystem()
    use_case = InitProject(fs)

    use_case.execute(tmp_path)

    config_path = tmp_path / "promptkit.yaml"
    assert config_path.exists()

    # Should be valid YAML
    config = yaml.safe_load(config_path.read_text())
    assert config["version"] == 1
    assert "prompts" in config
    assert "platforms" in config


def test_execute_creates_promptkit_lock(tmp_path: Path) -> None:
    """execute should create promptkit.lock."""
    fs = FileSystem()
    use_case = InitProject(fs)

    use_case.execute(tmp_path)

    lock_path = tmp_path / "promptkit.lock"
    assert lock_path.exists()

    # Should be valid YAML
    lock = yaml.safe_load(lock_path.read_text())
    assert lock["version"] == 1


def test_execute_fails_when_promptkit_yaml_exists(tmp_path: Path) -> None:
    """execute should raise InitProjectError if promptkit.yaml exists."""
    fs = FileSystem()
    use_case = InitProject(fs)

    # Create existing config
    (tmp_path / "promptkit.yaml").write_text("existing")

    with pytest.raises(InitProjectError) as exc_info:
        use_case.execute(tmp_path)

    assert "already exists" in str(exc_info.value)


def test_gitignore_is_created_with_cache_entry(tmp_path: Path) -> None:
    """execute should create .gitignore with .promptkit/cache/ entry."""
    fs = FileSystem()
    use_case = InitProject(fs)

    use_case.execute(tmp_path)

    gitignore_path = tmp_path / ".gitignore"
    assert gitignore_path.exists()

    content = gitignore_path.read_text()
    assert ".promptkit/cache/" in content


def test_gitignore_is_updated_if_exists(tmp_path: Path) -> None:
    """execute should append to existing .gitignore."""
    fs = FileSystem()
    use_case = InitProject(fs)

    # Create existing .gitignore
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("# Existing content\n*.pyc\n")

    use_case.execute(tmp_path)

    content = gitignore_path.read_text()
    assert "*.pyc" in content  # Existing content preserved
    assert ".promptkit/cache/" in content  # New entry added


def test_execute_does_not_modify_files_when_config_exists(tmp_path: Path) -> None:
    """execute should not create directories when config exists."""
    fs = FileSystem()
    use_case = InitProject(fs)

    # Create existing config
    (tmp_path / "promptkit.yaml").write_text("existing")

    with pytest.raises(InitProjectError):
        use_case.execute(tmp_path)

    # Directories should not be created
    assert not (tmp_path / ".agents").exists()
    assert not (tmp_path / ".cursor").exists()
