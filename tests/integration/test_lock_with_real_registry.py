"""Integration test for LockPrompts with real GitHub registry.

This test fetches actual prompts from the claude-plugins-official repository
to verify the full lock workflow with real data.
"""

import urllib.request
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

FIXED_TIME = datetime(2026, 2, 9, 12, 0, 0, tzinfo=timezone.utc)

# GitHub raw content base URL for claude-plugins-official
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/anthropics/claude-plugins-official/main"


class GitHubRegistryFetcher:
    """Fetcher that retrieves prompts from GitHub-hosted registries.

    This is a minimal implementation for integration testing. The production
    ClaudeMarketplaceFetcher (Phase 9) will be more sophisticated.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def fetch(self, spec: PromptSpec, /) -> Prompt:
        """Fetch prompt content from GitHub.

        For claude-plugins-official registry, prompts are structured as:
        plugins/<plugin-name>/agents/<agent-name>.md
        """
        prompt_name = spec.prompt_name

        # Try common paths in order of likelihood
        paths_to_try = [
            f"plugins/{prompt_name}/agents/{prompt_name}.md",
            f"plugins/{prompt_name}/skills/{prompt_name}.md",
            f"plugins/{prompt_name}/commands/{prompt_name}.md",
            f"{prompt_name}.md",
        ]

        last_error = None
        for path in paths_to_try:
            url = f"{self._base_url}/{path}"
            try:
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode("utf-8")
                    return Prompt(spec=spec, content=content)
            except Exception as e:
                last_error = e
                continue

        raise SyncError(
            f"Failed to fetch {spec.source} from GitHub. "
            f"Tried paths: {paths_to_try}. Last error: {last_error}"
        )


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    (d / ".promptkit" / "cache").mkdir(parents=True)
    return d


@pytest.fixture
def github_fetcher() -> GitHubRegistryFetcher:
    """Create a GitHub registry fetcher for claude-plugins-official."""
    return GitHubRegistryFetcher(GITHUB_RAW_BASE)


def _make_lock_prompts(
    project_dir: Path,
    fetchers: dict[str, GitHubRegistryFetcher],
) -> LockPrompts:
    """Create a LockPrompts use case instance."""
    fs = FileSystem()
    return LockPrompts(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
        prompt_cache=PromptCache(fs, project_dir / ".promptkit" / "cache"),
        local_fetcher=LocalFileFetcher(fs, project_dir / "prompts"),
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
        self, project_dir: Path, github_fetcher: GitHubRegistryFetcher
    ) -> None:
        """Test locking the code-simplifier agent from claude-plugins-official.

        This verifies:
        1. Real GitHub fetch works
        2. Content is cached correctly
        3. Lock file is created with proper entries
        4. Content hash is computed from real content
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
            {"claude-plugins-official": github_fetcher},
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
        assert entry.content_hash.startswith("sha256:")
        assert entry.fetched_at == FIXED_TIME

        # Verify content was cached
        cache_dir = project_dir / ".promptkit" / "cache"
        cache_files = list(cache_dir.glob("sha256-*.md"))
        assert len(cache_files) == 1

        # Verify cached content matches what we expect
        cached_content = cache_files[0].read_text()
        assert "code-simplifier" in cached_content.lower()
        assert "---" in cached_content  # Has frontmatter
        assert "name: code-simplifier" in cached_content

        # Verify content is substantial (the real agent prompt is ~500+ lines)
        assert len(cached_content) > 1000

    def test_lock_multiple_prompts_from_real_registry(
        self, project_dir: Path, github_fetcher: GitHubRegistryFetcher
    ) -> None:
        """Test locking multiple prompts from the real registry.

        This tests that the fetcher can handle multiple prompts in sequence.
        Note: Only using code-simplifier for now since we know it exists.
        Add more prompts here as they become available in the registry.
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
            {"claude-plugins-official": github_fetcher},
        )

        with patch("promptkit.app.lock._now", return_value=FIXED_TIME):
            use_case.execute(project_dir)

        entries = _read_lock_entries(project_dir)
        assert len(entries) >= 1

        # Verify all entries have valid hashes
        for entry in entries:
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64  # SHA256 hex

    def test_lock_preserves_timestamp_on_re_fetch(
        self, project_dir: Path, github_fetcher: GitHubRegistryFetcher
    ) -> None:
        """Test that re-locking preserves timestamp when content unchanged.

        This verifies the timestamp preservation logic works with real data.
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
            {"claude-plugins-official": github_fetcher},
        )

        # First lock
        first_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=first_time):
            use_case.execute(project_dir)

        first_entries = _read_lock_entries(project_dir)
        assert first_entries[0].fetched_at == first_time

        # Second lock (content should be identical)
        second_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        with patch("promptkit.app.lock._now", return_value=second_time):
            use_case.execute(project_dir)

        second_entries = _read_lock_entries(project_dir)
        # Timestamp should be preserved since content hasn't changed
        assert second_entries[0].fetched_at == first_time

    def test_lock_with_nonexistent_prompt_raises_error(
        self, project_dir: Path, github_fetcher: GitHubRegistryFetcher
    ) -> None:
        """Test that fetching a non-existent prompt raises SyncError."""
        config_yaml = """\
version: 1
registries:
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts:
  - claude-plugins-official/this-prompt-does-not-exist-xyz123
platforms:
  cursor:
"""
        (project_dir / "promptkit.yaml").write_text(config_yaml)

        use_case = _make_lock_prompts(
            project_dir,
            {"claude-plugins-official": github_fetcher},
        )

        with pytest.raises(SyncError, match="Failed to fetch"):
            use_case.execute(project_dir)
