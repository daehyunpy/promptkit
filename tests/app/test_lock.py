"""Tests for LockPrompts use case."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from promptkit.app.lock import LockPrompts
from promptkit.domain.errors import SyncError
from promptkit.domain.lock_entry import LockEntry
from promptkit.domain.prompt import Prompt
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.fetchers.local_file_fetcher import LocalFileFetcher
from promptkit.infra.file_system.local import FileSystem
from promptkit.infra.storage.prompt_cache import PromptCache

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


class FakeFetcher:
    """Test double for PromptFetcher."""

    def __init__(self, content_by_name: dict[str, str]) -> None:
        self._content = content_by_name

    def fetch(self, spec: PromptSpec, /) -> Prompt:
        key = spec.prompt_name
        if key not in self._content:
            raise SyncError(f"Prompt not found: {key}")
        return Prompt(spec=spec, content=self._content[key])


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    (d / ".promptkit" / "cache").mkdir(parents=True)
    return d


def _make_lock_prompts(
    project_dir: Path,
    fetchers: dict[str, FakeFetcher] | None = None,
) -> LockPrompts:
    fs = FileSystem()
    return LockPrompts(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
        prompt_cache=PromptCache(fs, project_dir / ".promptkit" / "cache"),
        local_fetcher=LocalFileFetcher(fs, project_dir / "prompts"),
        fetchers=fetchers or {},
    )


def _read_lock_entries(project_dir: Path) -> list[LockEntry]:
    """Read and deserialize lock entries from project_dir/promptkit.lock."""
    return LockFile.deserialize((project_dir / "promptkit.lock").read_text())


class TestLockRemotePrompts:
    def test_lock_single_remote_prompt(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakeFetcher({"code-review": "# Code Review\nReview code"})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        assert (project_dir / "promptkit.lock").exists()
        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].name == "code-review"
        assert entries[0].source == "my-registry/code-review"
        assert entries[0].content_hash.startswith("sha256:")

    def test_lock_multiple_remote_prompts(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_MULTIPLE_REMOTES)
        fetcher_a = FakeFetcher({"prompt-one": "# One"})
        fetcher_b = FakeFetcher({"prompt-two": "# Two"})
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


class TestLockLocalPrompts:
    def test_lock_local_prompt(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        (project_dir / "prompts" / "my-rule.md").write_text("# My Rule")
        use_case = _make_lock_prompts(project_dir)

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].name == "my-rule"
        assert entries[0].source == "local/my-rule"

    def test_lock_no_local_prompts(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        use_case = _make_lock_prompts(project_dir)

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 0


class TestTimestampPreservation:
    def test_preserves_timestamp_when_unchanged(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakeFetcher({"code-review": "# Code Review"})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})

        # First lock
        old_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=old_time):
            use_case.execute(project_dir)

        # Second lock with same content
        new_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=new_time):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert entries[0].fetched_at == old_time

    def test_updates_timestamp_when_content_changes(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)

        # First lock
        fetcher_v1 = FakeFetcher({"code-review": "# Version 1"})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher_v1})
        old_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=old_time):
            use_case.execute(project_dir)

        # Second lock with changed content
        fetcher_v2 = FakeFetcher({"code-review": "# Version 2"})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher_v2})
        new_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=new_time):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert entries[0].fetched_at == new_time


class TestStaleEntryRemoval:
    def test_removes_stale_entries(self, project_dir: Path) -> None:
        # First lock with a prompt
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakeFetcher({"code-review": "# Review"})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})
        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        # Second lock without that prompt
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_NO_PROMPTS)
        use_case = _make_lock_prompts(project_dir)
        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) == 0


class TestNoExistingLockFile:
    def test_works_without_existing_lock(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_WITH_ONE_REMOTE)
        fetcher = FakeFetcher({"code-review": "# Review"})
        use_case = _make_lock_prompts(project_dir, {"my-registry": fetcher})

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        assert (project_dir / "promptkit.lock").exists()
        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1
        assert entries[0].fetched_at == FIXED_TIME
