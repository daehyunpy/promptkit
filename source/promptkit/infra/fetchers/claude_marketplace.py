"""Infrastructure layer: Fetch plugins from Claude Code marketplace (GitHub)."""

import re
from pathlib import Path
from typing import Any

import httpx

from promptkit.domain.errors import SyncError
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.storage.plugin_cache import PluginCache

GITHUB_API_BASE = "https://api.github.com"
MARKETPLACE_PATH = ".claude-plugin/marketplace.json"
GITHUB_URL_PATTERN = re.compile(r"https://github\.com/([^/]+)/([^/]+)")


class ClaudeMarketplaceFetcher:
    """Fetches plugins from a GitHub-hosted Claude marketplace registry.

    Implements the PluginFetcher protocol. Downloads full plugin directories
    from GitHub via Contents API and caches them by commit SHA.
    """

    def __init__(
        self,
        *,
        registry_url: str,
        registry_name: str,
        cache: PluginCache,
        client: httpx.Client | None = None,
    ) -> None:
        self._registry_name = registry_name
        self._cache = cache
        self._client = client or httpx.Client()
        self._owner, self._repo = self._parse_github_url(registry_url)

    def fetch(self, spec: PromptSpec, /) -> Plugin:
        """Fetch a plugin from the marketplace.

        Looks up the plugin in marketplace.json, gets the latest commit SHA,
        downloads all files to the cache directory, and returns a Plugin manifest.
        """
        try:
            return self._do_fetch(spec)
        except httpx.HTTPError as e:
            raise SyncError(f"Failed to fetch plugin '{spec.prompt_name}': {e}") from e

    def _do_fetch(self, spec: PromptSpec, /) -> Plugin:
        marketplace = self._fetch_marketplace_json()
        entry = self._find_plugin_entry(marketplace, spec.prompt_name)
        self._validate_source(entry)
        sha = self._get_latest_commit_sha()
        cache_dir = self._cache.plugin_dir(self._registry_name, spec.prompt_name, sha)

        if not self._cache.has(self._registry_name, spec.prompt_name, sha):
            self._download_plugin(entry, marketplace, cache_dir)

        files = self._cache.list_files(self._registry_name, spec.prompt_name, sha)
        return Plugin(
            spec=spec,
            files=tuple(files),
            source_dir=cache_dir,
            commit_sha=sha,
        )

    @staticmethod
    def _validate_source(entry: dict[str, Any], /) -> None:
        """Validate that the plugin source is a relative path, not external."""
        source = entry.get("source", "")
        if isinstance(source, dict):
            raise SyncError(
                f"External source not supported for plugin '{entry.get('name')}'. "
                "Only relative-path plugins are supported in this version."
            )

    def _download_plugin(
        self,
        entry: dict[str, Any],
        marketplace: dict[str, Any],
        cache_dir: Path,
        /,
    ) -> None:
        """Download all plugin files to the cache directory."""
        skills = entry.get("skills")
        if skills:
            self._handle_skills_array(skills, cache_dir)
        else:
            source_path = self._resolve_source_path(entry, marketplace)
            self._list_and_download_directory(
                source_path, cache_dir, base_prefix=source_path
            )

    def _fetch_marketplace_json(self) -> dict[str, Any]:
        url = f"{GITHUB_API_BASE}/repos/{self._owner}/{self._repo}/contents/{MARKETPLACE_PATH}"
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def _find_plugin_entry(
        self, marketplace: dict[str, Any], plugin_name: str, /
    ) -> dict[str, Any]:
        plugins = marketplace.get("plugins", [])
        for entry in plugins:
            if entry.get("name") == plugin_name:
                return entry
        raise SyncError(
            f"Plugin '{plugin_name}' not found in marketplace.json "
            f"for {self._owner}/{self._repo}"
        )

    @staticmethod
    def _resolve_source_path(
        entry: dict[str, Any], marketplace: dict[str, Any], /
    ) -> str:
        """Resolve the source path, combining with pluginRoot if present."""
        path = str(entry.get("source", "")).lstrip("./")
        plugin_root = marketplace.get("metadata", {}).get("pluginRoot", "").lstrip("./")
        if not plugin_root:
            return path
        if not path:
            return plugin_root
        return f"{plugin_root}/{path}"

    def _get_latest_commit_sha(self) -> str:
        url = f"{GITHUB_API_BASE}/repos/{self._owner}/{self._repo}/commits/HEAD"
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()["sha"]

    def _list_and_download_directory(
        self,
        dir_path: str,
        cache_dir: Path,
        /,
        *,
        base_prefix: str,
    ) -> list[str]:
        """Recursively list and download all files in a directory."""
        url = f"{GITHUB_API_BASE}/repos/{self._owner}/{self._repo}/contents/{dir_path}"
        response = self._client.get(url)
        response.raise_for_status()
        entries = response.json()

        files: list[str] = []
        for item in entries:
            if item["type"] == "dir":
                files.extend(
                    self._list_and_download_directory(
                        item["path"], cache_dir, base_prefix=base_prefix
                    )
                )
            elif item["type"] == "file":
                relative = self._strip_prefix(item["path"], base_prefix)
                self._download_file(item["download_url"], cache_dir / relative)
                files.append(relative)
        return files

    def _handle_skills_array(self, skills: list[str], cache_dir: Path, /) -> None:
        """Download files from each skill directory listed in the skills array."""
        for skill_path in skills:
            clean_path = skill_path.lstrip("./")
            self._list_and_download_directory(clean_path, cache_dir, base_prefix="")

    def _download_file(self, download_url: str, target_path: Path, /) -> None:
        response = self._client.get(download_url)
        response.raise_for_status()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(response.content)

    @staticmethod
    def _strip_prefix(path: str, prefix: str, /) -> str:
        """Strip the repository prefix from a path to get the relative path."""
        if prefix and path.startswith(prefix):
            stripped = path[len(prefix) :]
            return stripped.lstrip("/")
        return path

    @staticmethod
    def _parse_github_url(url: str, /) -> tuple[str, str]:
        match = GITHUB_URL_PATTERN.match(url)
        if not match:
            raise SyncError(
                f"Invalid GitHub URL: '{url}'. "
                "Expected format: https://github.com/owner/repo"
            )
        return match.group(1), match.group(2)
