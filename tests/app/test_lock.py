"""Tests for LockPrompts use case."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from promptkit.app.lock import LockPrompts
from promptkit.domain.errors import SyncError
from promptkit.domain.lock_entry import LockEntry
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.fetchers.local_plugin_fetcher import LocalPluginFetcher
from promptkit.infra.file_system.local import FileSystem

CONFIG_WITH_ONE_REMOTE = """\
version: 1
registries:
  my-registry: https://example.com/registry
prompts:
  - my-registry/code-review
platforms:
  cursor:
"""

CONFIG_WITH_MULTIPLE_REMOTES = """\
version: 1
registries:
  reg-a: https://example.com/a
  reg-b: https://example.com/b
prompts:
  - reg-a/prompt-one
  - reg-b/prompt-two
platforms:
  cursor:
"""

CONFIG_WITH_NO_PROMPTS = """\
version: 1
prompts: []
platforms:
  cursor:
"""

FIXED_TIME = datetime(2026, 2, 9, 12, 0, 0, tzinfo=timezone.utc)


class FakePluginFetcher:
    """Test double for PluginFetcher (registry)."""

    def __init__(self, plugins: dict[str, tuple[tuple[str, ...], str]]) -> None:
        """plugins: {prompt_name: (files, commit_sha)}"""
        self._plugins = plugins

    def fetch(self, spec: PromptSpec, /) -> Plugin:
        key = spec.prompt_name
        if key not in self._plugins:
            raise SyncError(f"Plugin not found: {key}")
        files, sha = self._plugins[key]
        return Plugin(
            spec=spec,
            files=files,
            source_dir=Path("/fake/cache"),
            commit_sha=sha,
        )


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    return d


def _make_lock_prompts(
    project_dir: Path,
    fetchers: dict[str, FakePluginFetcher] | None = None,
) -> LockPrompts:
    fs = FileSystem()
    return LockPrompts(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
        local_fetcher=LocalPluginFetcher(fs, project_dir / "prompts"),
        fetchers=fetchers or {},
    )


def _read_lock_entries(project_dir: Path) -> list[LockEntry]:
    return LockFile.deserialize((project_dir / "promptkit.lock").read_text())


class TestLockRemotePlugins:
    def test_lock_single_registry_plugin(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakePluginFetcher(
            {"code-review": (("agents/reviewer.md",), "sha123")}
        )
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].name == "code-review"
        assert entries[0].source == "my-registry/code-review"
        assert entries[0].content_hash == ""
        assert entries[0].commit_sha == "sha123"

    def test_lock_multiple_registry_plugins(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_MULTIPLE_REMOTES)
        fetcher_a = FakePluginFetcher({"prompt-one": (("file.md",), "sha-a")})
        fetcher_b = FakePluginFetcher({"prompt-two": (("file.md",), "sha-b")})
        use_case = _make_lock_prompts(
            project_dir, {"reg-a": fetcher_a, "reg-b": fetcher_b}
        )

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 2
        names = sorted(e.name for e in entries)
        assert names == ["prompt-one", "prompt-two"]

    def test_lock_raises_for_missing_fetcher(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        use_case = _make_lock_prompts(project_dir, {})

        with pytest.raises(SyncError, match="my-registry"):
            use_case.execute(project_dir)


class TestLockLocalPlugins:
    def test_lock_local_single_file(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        (project_dir / "prompts" / "my-rule.md").write_text("# My Rule")
        use_case = _make_lock_prompts(project_dir)

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].name == "my-rule"
        assert entries[0].source == "local/my-rule"
        assert entries[0].content_hash.startswith("sha256:")
        assert entries[0].commit_sha is None

    def test_lock_local_directory_plugin(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        skill_dir = project_dir / "prompts" / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "check.sh").write_text("#!/bin/bash")
        use_case = _make_lock_prompts(project_dir)

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].name == "my-skill"
        assert entries[0].source == "local/my-skill"
        assert entries[0].content_hash.startswith("sha256:")
        assert entries[0].commit_sha is None

    def test_lock_no_local_plugins(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        use_case = _make_lock_prompts(project_dir)

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 0


class TestTimestampPreservation:
    def test_preserves_timestamp_for_local_when_unchanged(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        (project_dir / "prompts" / "my-rule.md").write_text("# My Rule")

        use_case = _make_lock_prompts(project_dir)

        old_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=old_time):
            use_case.execute(project_dir)

        new_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=new_time):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert entries[0].fetched_at == old_time

    def test_updates_timestamp_for_local_when_content_changes(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        (project_dir / "prompts" / "my-rule.md").write_text("# Version 1")

        use_case = _make_lock_prompts(project_dir)
        old_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=old_time):
            use_case.execute(project_dir)

        # Change content
        (project_dir / "prompts" / "my-rule.md").write_text("# Version 2")
        new_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=new_time):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert entries[0].fetched_at == new_time

    def test_preserves_timestamp_for_registry_when_sha_unchanged(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakePluginFetcher(
            {"code-review": (("agents/reviewer.md",), "sha123")}
        )

        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})
        old_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=old_time):
            use_case.execute(project_dir)

        new_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=new_time):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert entries[0].fetched_at == old_time

    def test_updates_timestamp_for_registry_when_sha_changes(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)

        fetcher_v1 = FakePluginFetcher(
            {"code-review": (("agents/reviewer.md",), "sha-v1")}
        )
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher_v1})
        old_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=old_time):
            use_case.execute(project_dir)

        fetcher_v2 = FakePluginFetcher(
            {"code-review": (("agents/reviewer.md",), "sha-v2")}
        )
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher_v2})
        new_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=new_time):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert entries[0].fetched_at == new_time


class TestStaleEntryRemoval:
    def test_removes_stale_entries(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakePluginFetcher({"code-review": (("file.md",), "sha123")})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})
        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        use_case = _make_lock_prompts(project_dir)
        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 0


class TestNoExistingLockFile:
    def test_works_without_existing_lock(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakePluginFetcher({"code-review": (("file.md",), "sha123")})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        assert (project_dir / "promptkit.lock").exists()
        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].fetched_at == FIXED_TIME
