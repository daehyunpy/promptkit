"""Integration test for LockPrompts with real GitHub registry.

This test fetches actual plugins from the claude-plugins-official repository
using the production ClaudeMarketplaceFetcher to verify the full lock workflow.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from promptkit.app.lock import LockPrompts
from promptkit.domain.errors import SyncError
from promptkit.domain.lock_entry import LockEntry
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.fetchers.claude_marketplace import ClaudeMarketplaceFetcher
from promptkit.infra.fetchers.local_plugin_fetcher import LocalPluginFetcher
from promptkit.infra.file_system.local import FileSystem
from promptkit.infra.storage.plugin_cache import PluginCache

FIXED_TIME = datetime(2026, 2, 9, 12, 0, 0, tzinfo=timezone.utc)

REGISTRY_NAME = "claude-plugins-official"
REGISTRY_URL = "https://github.com/anthropics/claude-plugins-official"


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    (d / ".promptkit" / "cache" / "plugins").mkdir(parents=True)
    return d


@pytest.fixture
def plugin_cache(project_dir: Path) -> PluginCache:
    return PluginCache(project_dir / ".promptkit" / "cache" / "plugins")


@pytest.fixture
def marketplace_fetcher(plugin_cache: PluginCache) -> ClaudeMarketplaceFetcher:
    """Create a real ClaudeMarketplaceFetcher for claude-plugins-official."""
    return ClaudeMarketplaceFetcher(
        registry_url=REGISTRY_URL,
        registry_name=REGISTRY_NAME,
        cache=plugin_cache,
    )


def _make_lock_prompts(
    project_dir: Path,
    fetchers: dict[str, ClaudeMarketplaceFetcher],
) -> LockPrompts:
    """Create a LockPrompts use case instance."""
    fs = FileSystem()
    return LockPrompts(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
        local_fetcher=LocalPluginFetcher(fs, project_dir / "prompts"),
        fetchers=fetchers,
    )


def _read_lock_entries(project_dir: Path) -> list[LockEntry]:
    """Read and deserialize lock entries from promptkit.lock."""
    return LockFile.deserialize((project_dir / "promptkit.lock").read_text())


@pytest.mark.integration
@pytest.mark.network
class TestLockWithRealRegistry:
    """Integration tests that fetch from real GitHub registry."""

    def test_lock_code_simplifier_from_claude_plugins_official(
        self, project_dir: Path, marketplace_fetcher: ClaudeMarketplaceFetcher
    ) -> None:
        """Test locking the code-simplifier plugin from claude-plugins-official.

        This verifies:
        1. Real GitHub fetch via ClaudeMarketplaceFetcher works
        2. Files are cached in plugin cache
        3. Lock file is created with proper entries
        4. commit_sha is recorded (full 40-char SHA)
        """
        config_yaml = """\
version: 1
registries:
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts:
  - claude-plugins-official/code-simplifier
platforms:
  cursor:
"""
        (project_dir / "promptkit.yaml").write_text(config_yaml)

        use_case = _make_lock_prompts(
            project_dir,
            {REGISTRY_NAME: marketplace_fetcher},
        )

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        # Verify lock file was created
        assert (project_dir / "promptkit.lock").exists()

        # Verify lock entry
        entries = _read_lock_entries(project_dir)
        assert len(entries) == 1

        entry = entries[0]
        assert entry.name == "code-simplifier"
        assert entry.source == "claude-plugins-official/code-simplifier"
        assert entry.commit_sha is not None
        assert len(entry.commit_sha) == 40
        assert entry.fetched_at == FIXED_TIME

        # Verify files are cached on disk
        cache_dir = (
            project_dir
            / ".promptkit"
            / "cache"
            / "plugins"
            / REGISTRY_NAME
            / "code-simplifier"
            / entry.commit_sha
        )
        assert cache_dir.is_dir()
        cached_files = list(cache_dir.rglob("*"))
        assert any(f.is_file() for f in cached_files)

    def test_lock_preserves_timestamp_on_re_lock(
        self, project_dir: Path, marketplace_fetcher: ClaudeMarketplaceFetcher
    ) -> None:
        """Test that re-locking preserves timestamp when commit unchanged."""
        config_yaml = """\
version: 1
registries:
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts:
  - claude-plugins-official/code-simplifier
platforms:
  cursor:
"""
        (project_dir / "promptkit.yaml").write_text(config_yaml)

        use_case = _make_lock_prompts(
            project_dir,
            {REGISTRY_NAME: marketplace_fetcher},
        )

        # First lock
        first_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=first_time):
            use_case.execute(project_dir)

        first_entries = _read_lock_entries(project_dir)
        assert first_entries[0].fetched_at == first_time

        # Second lock (commit SHA should be identical)
        second_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=second_time):
            use_case.execute(project_dir)

        second_entries = _read_lock_entries(project_dir)
        # Timestamp preserved since commit_sha hasn't changed
        assert second_entries[0].fetched_at == first_time

    def test_lock_with_nonexistent_plugin_raises_error(
        self, project_dir: Path, marketplace_fetcher: ClaudeMarketplaceFetcher
    ) -> None:
        """Test that fetching a non-existent plugin raises SyncError."""
        config_yaml = """\
version: 1
registries:
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts:
  - claude-plugins-official/this-plugin-does-not-exist-xyz123
platforms:
  cursor:
"""
        (project_dir / "promptkit.yaml").write_text(config_yaml)

        use_case = _make_lock_prompts(
            project_dir,
            {REGISTRY_NAME: marketplace_fetcher},
        )

        with pytest.raises(SyncError):
            use_case.execute(project_dir)
