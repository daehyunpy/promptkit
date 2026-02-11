"""Tests for ValidateConfig use case."""

from pathlib import Path

import pytest

from promptkit.app.validate import ValidateConfig
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.file_system.local import FileSystem

VALID_CONFIG = """\
version: 1
registries:
  my-registry: https://example.com/registry
prompts:
  - my-registry/code-review
platforms:
  cursor:
"""

CONFIG_WITH_UNKNOWN_REGISTRY = """\
version: 1
registries:
  my-registry: https://example.com/registry
prompts:
  - unknown-registry/code-review
platforms:
  cursor:
"""

CONFIG_WITH_NO_PROMPTS = """\
version: 1
prompts: []
platforms:
  cursor:
"""

INVALID_YAML = "version: [[[invalid"

MATCHING_LOCK = """\
version: 1
prompts:
  - name: code-review
    source: my-registry/code-review
    hash: sha256:abc123
    fetched_at: '2026-02-09T12:00:00+00:00'
"""

STALE_LOCK = """\
version: 1
prompts:
  - name: old-prompt
    source: removed-registry/old-prompt
    hash: sha256:abc123
    fetched_at: '2026-02-09T12:00:00+00:00'
"""

LOCK_MISSING_PROMPT = """\
version: 1
prompts: []
"""


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    return d


def _make_validate() -> ValidateConfig:
    return ValidateConfig(
        file_system=FileSystem(),
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
    )


class TestConfigWellFormed:
    def test_valid_config_returns_no_errors(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(VALID_CONFIG)
        (project_dir / "promptkit.lock").write_text(MATCHING_LOCK)
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_yaml_returns_error(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(INVALID_YAML)
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert not result.is_valid
        assert len(result.errors) >= 1
        assert any("YAML" in e.message or "yaml" in e.message for e in result.errors)


class TestRegistryReferences:
    def test_unknown_registry_returns_error(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_UNKNOWN_REGISTRY)
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert not result.is_valid
        assert any("unknown-registry" in e.message for e in result.errors)


class TestLockFreshness:
    def test_missing_lock_returns_warning(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(VALID_CONFIG)
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert result.is_valid  # warnings don't make it invalid
        assert any("lock" in w.message.lower() for w in result.warnings)

    def test_stale_entry_returns_warning(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(VALID_CONFIG)
        (project_dir / "promptkit.lock").write_text(STALE_LOCK)
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert any(
            "stale" in w.message.lower() or "old-prompt" in w.message
            for w in result.warnings
        )

    def test_unlocked_prompt_returns_warning(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(VALID_CONFIG)
        (project_dir / "promptkit.lock").write_text(LOCK_MISSING_PROMPT)
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert any(
            "not locked" in w.message.lower() or "code-review" in w.message
            for w in result.warnings
        )


class TestMultipleIssues:
    def test_collects_multiple_issues(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_UNKNOWN_REGISTRY)
        # No lock file → warning + unknown registry → error
        use_case = _make_validate()

        result = use_case.execute(project_dir)

        assert len(result.issues) >= 2
        assert len(result.errors) >= 1
        assert len(result.warnings) >= 1
