"""Tests for ClaudeMarketplaceFetcher."""

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from promptkit.domain.errors import SyncError
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.fetchers.claude_marketplace import ClaudeMarketplaceFetcher
from promptkit.infra.storage.plugin_cache import PluginCache


def _make_response(json_data: object, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response for JSON API calls."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=response
        )
    return response


def _make_download_response(content: bytes, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response for file downloads."""
    response = MagicMock()
    response.status_code = status_code
    response.content = content
    return response


SAMPLE_MARKETPLACE_JSON = {
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

SAMPLE_COMMIT_RESPONSE = {
    "sha": "abc123def456789",
    "commit": {"message": "latest commit"},
}

SAMPLE_DIR_LISTING = [
    {
        "name": "agents",
        "type": "dir",
        "path": "plugins/code-simplifier/agents",
    },
    {
        "name": "hooks",
        "type": "dir",
        "path": "plugins/code-simplifier/hooks",
    },
]

SAMPLE_AGENTS_LISTING = [
    {
        "name": "simplifier.md",
        "type": "file",
        "path": "plugins/code-simplifier/agents/simplifier.md",
        "download_url": "https://raw.githubusercontent.com/org/repo/main/plugins/code-simplifier/agents/simplifier.md",
    },
]

SAMPLE_HOOKS_LISTING = [
    {
        "name": "hooks.json",
        "type": "file",
        "path": "plugins/code-simplifier/hooks/hooks.json",
        "download_url": "https://raw.githubusercontent.com/org/repo/main/plugins/code-simplifier/hooks/hooks.json",
    },
]


@pytest.fixture
def cache(tmp_path: Path) -> PluginCache:
    return PluginCache(tmp_path / "cache" / "plugins")


def _make_fetcher(
    cache: PluginCache,
    client: httpx.Client,
    url: str = "https://github.com/anthropics/claude-plugins-official",
) -> ClaudeMarketplaceFetcher:
    return ClaudeMarketplaceFetcher(
        registry_url=url,
        registry_name="claude-plugins-official",
        cache=cache,
        client=client,
    )


class TestGitHubUrlParsing:
    def test_parses_standard_github_url(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)
        fetcher = _make_fetcher(cache, client)
        assert fetcher._owner == "anthropics"
        assert fetcher._repo == "claude-plugins-official"

    def test_raises_for_invalid_url(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)
        with pytest.raises(SyncError, match="Invalid GitHub"):
            _make_fetcher(cache, client, url="https://gitlab.com/org/repo")


class TestFetchPlugin:
    def test_fetches_plugin_with_relative_path(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)

        # Call order: marketplace → commit → list root → list agents/ →
        # download simplifier.md → list hooks/ → download hooks.json
        client.get.side_effect = [
            _make_response(SAMPLE_MARKETPLACE_JSON),
            _make_response(SAMPLE_COMMIT_RESPONSE),
            _make_response(SAMPLE_DIR_LISTING),
            _make_response(SAMPLE_AGENTS_LISTING),
            _make_download_response(b"# Simplifier Agent"),
            _make_response(SAMPLE_HOOKS_LISTING),
            _make_download_response(b'{"hooks": []}'),
        ]

        fetcher = _make_fetcher(cache, client)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")
        plugin = fetcher.fetch(spec)

        assert plugin.spec is spec
        assert plugin.commit_sha == "abc123def456789"
        assert sorted(plugin.files) == ["agents/simplifier.md", "hooks/hooks.json"]

    def test_skips_download_when_cached(
        self, cache: PluginCache, tmp_path: Path
    ) -> None:
        client = MagicMock(spec=httpx.Client)
        # Pre-populate cache
        cache_dir = cache.plugin_dir(
            "claude-plugins-official", "code-simplifier", "abc123def456789"
        )
        cache_dir.mkdir(parents=True)
        (cache_dir / "agents").mkdir()
        (cache_dir / "agents" / "simplifier.md").write_text("cached")

        client.get.side_effect = [
            _make_response(SAMPLE_MARKETPLACE_JSON),
            _make_response(SAMPLE_COMMIT_RESPONSE),
        ]

        fetcher = _make_fetcher(cache, client)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")
        plugin = fetcher.fetch(spec)

        assert plugin.commit_sha == "abc123def456789"
        assert plugin.files == ("agents/simplifier.md",)
        # Only 2 API calls (marketplace + commit), not 7
        assert client.get.call_count == 2

    def test_plugin_not_found_raises(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.return_value = _make_response(SAMPLE_MARKETPLACE_JSON)

        fetcher = _make_fetcher(cache, client)
        spec = PromptSpec(source="claude-plugins-official/nonexistent")

        with pytest.raises(SyncError, match="not found"):
            fetcher.fetch(spec)

    def test_external_source_raises(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.return_value = _make_response(SAMPLE_MARKETPLACE_JSON)

        fetcher = _make_fetcher(cache, client)
        spec = PromptSpec(source="claude-plugins-official/external-plugin")

        with pytest.raises(SyncError, match="External"):
            fetcher.fetch(spec)

    def test_network_error_raises(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.side_effect = httpx.ConnectError("Connection refused")

        fetcher = _make_fetcher(cache, client)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")

        with pytest.raises(SyncError, match="Connection"):
            fetcher.fetch(spec)

    def test_http_error_raises(self, cache: PluginCache) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.return_value = _make_response({}, status_code=403)

        fetcher = _make_fetcher(cache, client)
        spec = PromptSpec(source="claude-plugins-official/code-simplifier")

        with pytest.raises(SyncError):
            fetcher.fetch(spec)


class TestSkillsRepoStructure:
    def test_fetches_skills_from_skills_array(self, cache: PluginCache) -> None:
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
        xlsx_listing = [
            {
                "name": "SKILL.md",
                "type": "file",
                "path": "skills/xlsx/SKILL.md",
                "download_url": "https://raw.githubusercontent.com/org/repo/main/skills/xlsx/SKILL.md",
            },
            {
                "name": "scripts",
                "type": "dir",
                "path": "skills/xlsx/scripts",
            },
        ]
        xlsx_scripts_listing = [
            {
                "name": "processor.py",
                "type": "file",
                "path": "skills/xlsx/scripts/processor.py",
                "download_url": "https://raw.githubusercontent.com/org/repo/main/skills/xlsx/scripts/processor.py",
            },
        ]
        docx_listing = [
            {
                "name": "SKILL.md",
                "type": "file",
                "path": "skills/docx/SKILL.md",
                "download_url": "https://raw.githubusercontent.com/org/repo/main/skills/docx/SKILL.md",
            },
        ]

        client = MagicMock(spec=httpx.Client)
        # Call order: marketplace → commit → list xlsx/ → download SKILL.md →
        # list xlsx/scripts/ → download processor.py → list docx/ → download SKILL.md
        client.get.side_effect = [
            _make_response(skills_marketplace),
            _make_response(SAMPLE_COMMIT_RESPONSE),
            _make_response(xlsx_listing),
            _make_download_response(b"# XLSX Skill"),
            _make_response(xlsx_scripts_listing),
            _make_download_response(b"import openpyxl"),
            _make_response(docx_listing),
            _make_download_response(b"# DOCX Skill"),
        ]

        fetcher = ClaudeMarketplaceFetcher(
            registry_url="https://github.com/anthropics/skills",
            registry_name="anthropic-skills",
            cache=cache,
            client=client,
        )
        spec = PromptSpec(source="anthropic-skills/document-skills")
        plugin = fetcher.fetch(spec)

        assert plugin.commit_sha == "abc123def456789"
        assert sorted(plugin.files) == [
            "skills/docx/SKILL.md",
            "skills/xlsx/SKILL.md",
            "skills/xlsx/scripts/processor.py",
        ]
