"""Tests for ClaudeMarketplaceFetcher."""

import json
from pathlib import Path

import pytest

from promptkit.domain.errors import SyncError
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.fetchers.claude_marketplace import ClaudeMarketplaceFetcher
from promptkit.infra.storage.plugin_cache import PluginCache

FAKE_SHA = "abc123def4567890000000000000000000000000"


class FakeGitRegistryClone:
    """Test double for GitRegistryClone using a temp directory with pre-populated files."""

    def __init__(self, clone_dir: Path, sha: str = FAKE_SHA) -> None:
        self._clone_dir = clone_dir
        self._sha = sha
        self.ensure_up_to_date_called = False

    @property
    def clone_dir(self) -> Path:
        return self._clone_dir

    def ensure_up_to_date(self) -> None:
        self.ensure_up_to_date_called = True

    def get_commit_sha(self) -> str:
        return self._sha


def _write_marketplace_json(clone_dir: Path, marketplace: dict) -> None:
    manifest_dir = clone_dir / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "marketplace.json").write_text(json.dumps(marketplace))


def _write_plugin_file(clone_dir: Path, path: str, content: str = "") -> None:
    full_path = clone_dir / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)


SAMPLE_MARKETPLACE = {
    "name": "claude-plugins-official",
    "owner": {"name": "Anthropic"},
    "plugins": [
        {
            "name": "code-simplifier",
            "source": "./plugins/code-simplifier",
            "description": "Simplifies code",
        },
        {
            "name": "external-plugin",
            "source": {"source": "url", "url": "https://github.com/org/repo.git"},
        },
    ],
}


@pytest.fixture
def cache(tmp_path: Path) -> PluginCache:
    return PluginCache(tmp_path / "cache" / "plugins")


@pytest.fixture
def clone_dir(tmp_path: Path) -> Path:
    d = tmp_path / "clone"
    d.mkdir()
    return d


def _make_fetcher(
    cache: PluginCache,
    clone: FakeGitRegistryClone,
    url: str = "https://github.com/anthropics/claude-plugins-official",
) -> ClaudeMarketplaceFetcher:
    return ClaudeMarketplaceFetcher(
        registry_url=url,
        registry_name="claude-plugins-official",
        cache=cache,
        clone=clone,
    )


class TestGitHubUrlParsing:
    def test_parses_standard_github_url(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        assert fetcher._owner == "anthropics"
        assert fetcher._repo == "claude-plugins-official"

    def test_raises_for_invalid_url(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        clone = FakeGitRegistryClone(clone_dir)
        with pytest.raises(SyncError, match="Invalid GitHub"):
            _make_fetcher(cache, clone, url="https://gitlab.com/org/repo")


class TestFetchPlugin:
    def test_fetches_plugin_with_relative_source(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        _write_marketplace_json(clone_dir, SAMPLE_MARKETPLACE)
        _write_plugin_file(
            clone_dir, "plugins/code-simplifier/agents/simplifier.md", "# Agent"
        )
        _write_plugin_file(
            clone_dir, "plugins/code-simplifier/hooks/hooks.json", '{"hooks": []}'
        )

        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")
        plugin = fetcher.fetch(spec)

        assert plugin.spec is spec
        assert plugin.commit_sha == FAKE_SHA
        assert sorted(plugin.files) == ["agents/simplifier.md", "hooks/hooks.json"]
        assert (plugin.source_dir / "agents" / "simplifier.md").read_text() == "# Agent"
        assert clone.ensure_up_to_date_called

    def test_fetches_plugin_with_mixed_files(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        _write_marketplace_json(clone_dir, SAMPLE_MARKETPLACE)
        _write_plugin_file(
            clone_dir, "plugins/code-simplifier/agents/reviewer.md", "# Reviewer"
        )
        _write_plugin_file(
            clone_dir,
            "plugins/code-simplifier/.claude-plugin/plugin.json",
            '{"name": "test"}',
        )
        _write_plugin_file(
            clone_dir, "plugins/code-simplifier/hooks/hooks.json", "{}"
        )
        _write_plugin_file(
            clone_dir, "plugins/code-simplifier/scripts/check.sh", "#!/bin/bash"
        )

        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")
        plugin = fetcher.fetch(spec)

        assert sorted(plugin.files) == [
            ".claude-plugin/plugin.json",
            "agents/reviewer.md",
            "hooks/hooks.json",
            "scripts/check.sh",
        ]

    def test_skips_copy_when_cached(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        _write_marketplace_json(clone_dir, SAMPLE_MARKETPLACE)
        _write_plugin_file(
            clone_dir, "plugins/code-simplifier/agents/simplifier.md", "# Agent"
        )

        # Pre-populate cache
        cache_dir = cache.plugin_dir(
            "claude-plugins-official", "code-simplifier", FAKE_SHA
        )
        cache_dir.mkdir(parents=True)
        (cache_dir / "agents").mkdir()
        (cache_dir / "agents" / "simplifier.md").write_text("cached version")

        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")
        plugin = fetcher.fetch(spec)

        assert plugin.commit_sha == FAKE_SHA
        assert plugin.files == ("agents/simplifier.md",)
        # Cached version should be preserved (no overwrite)
        assert (plugin.source_dir / "agents" / "simplifier.md").read_text() == "cached version"

    def test_plugin_not_found_raises(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        _write_marketplace_json(clone_dir, SAMPLE_MARKETPLACE)
        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/nonexistent")

        with pytest.raises(SyncError, match="not found"):
            fetcher.fetch(spec)

    def test_external_source_raises(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        _write_marketplace_json(clone_dir, SAMPLE_MARKETPLACE)
        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/external-plugin")

        with pytest.raises(SyncError, match="External"):
            fetcher.fetch(spec)

    def test_missing_marketplace_json_raises(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        # No marketplace.json written
        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")

        with pytest.raises(SyncError, match="marketplace.json not found"):
            fetcher.fetch(spec)

    def test_missing_plugin_directory_raises(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        _write_marketplace_json(clone_dir, SAMPLE_MARKETPLACE)
        # Don't create the plugin directory
        clone = FakeGitRegistryClone(clone_dir)
        fetcher = _make_fetcher(cache, clone)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")

        with pytest.raises(SyncError, match="Plugin directory not found"):
            fetcher.fetch(spec)


class TestSkillsRepoStructure:
    def test_fetches_skills_from_skills_array(
        self, cache: PluginCache, clone_dir: Path
    ) -> None:
        skills_marketplace = {
            "name": "anthropic-agent-skills",
            "owner": {"name": "Anthropic"},
            "plugins": [
                {
                    "name": "document-skills",
                    "source": "./",
                    "strict": False,
                    "skills": ["./skills/xlsx", "./skills/docx"],
                },
            ],
        }
        _write_marketplace_json(clone_dir, skills_marketplace)
        _write_plugin_file(clone_dir, "skills/xlsx/SKILL.md", "# XLSX Skill")
        _write_plugin_file(
            clone_dir, "skills/xlsx/scripts/processor.py", "import openpyxl"
        )
        _write_plugin_file(clone_dir, "skills/docx/SKILL.md", "# DOCX Skill")

        clone = FakeGitRegistryClone(clone_dir)
        fetcher = ClaudeMarketplaceFetcher(
            registry_url="https://github.com/anthropics/skills",
            registry_name="anthropic-skills",
            cache=cache,
            clone=clone,
        )
        spec = PromptSpec(source="anthropic-skills/document-skills")
        plugin = fetcher.fetch(spec)

        assert plugin.commit_sha == FAKE_SHA
        assert sorted(plugin.files) == [
            "skills/docx/SKILL.md",
            "skills/xlsx/SKILL.md",
            "skills/xlsx/scripts/processor.py",
        ]
