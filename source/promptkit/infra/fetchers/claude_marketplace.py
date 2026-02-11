"""Infrastructure layer: Fetch plugins from Claude Code marketplace (GitHub)."""

import json
import re
import shutil
from pathlib import Path
from typing import Any, Protocol

from promptkit.domain.errors import SyncError
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.fetchers.git_registry_clone import GitRegistryClone
from promptkit.infra.storage.plugin_cache import PluginCache


class RegistryClone(Protocol):
    """Structural protocol for registry clone objects (enables test doubles)."""

    @property
    def clone_dir(self) -> Path: ...
    def ensure_up_to_date(self) -> None: ...
    def get_commit_sha(self) -> str: ...


MARKETPLACE_PATH = ".claude-plugin/marketplace.json"
GITHUB_URL_PATTERN = re.compile(r"https://github\.com/([^/]+)/([^/]+)")


class ClaudeMarketplaceFetcher:
    """Fetches plugins from a GitHub-hosted Claude marketplace registry.

    Implements the PluginFetcher protocol. Reads plugin files from a local
    shallow git clone and copies them to the cache by commit SHA.
    """

    def __init__(
        self,
        *,
        registry_url: str,
        registry_name: str,
        cache: PluginCache,
        registries_dir: Path | None = None,
        clone: RegistryClone | None = None,
    ) -> None:
        self._registry_name = registry_name
        self._cache = cache
        self._owner, self._repo = self._parse_github_url(registry_url)
        default_registries_dir = cache.cache_dir.parent.parent / "registries"
        self._clone = clone or GitRegistryClone(
            registry_name=registry_name,
            registry_url=registry_url,
            registries_dir=registries_dir or default_registries_dir,
        )

    def fetch(self, spec: PromptSpec, /) -> Plugin:
        """Fetch a plugin from the marketplace.

        Ensures the local clone is up to date, looks up the plugin in
        marketplace.json, copies files to cache, and returns a Plugin manifest.
        """
        try:
            return self._fetch_and_cache(spec)
        except SyncError:
            raise
        except Exception as e:
            raise SyncError(f"Failed to fetch plugin '{spec.prompt_name}': {e}") from e

    def _fetch_and_cache(self, spec: PromptSpec, /) -> Plugin:
        self._clone.ensure_up_to_date()
        marketplace = self._read_marketplace_json()
        entry = self._find_plugin_entry(marketplace, spec.prompt_name)
        self._reject_external_source(entry)
        sha = self._clone.get_commit_sha()
        cache_dir = self._cache.plugin_dir(self._registry_name, spec.prompt_name, sha)

        if not self._cache.has(self._registry_name, spec.prompt_name, sha):
            self._copy_plugin(entry, marketplace, cache_dir)

        files = self._cache.list_files(self._registry_name, spec.prompt_name, sha)
        return Plugin(
            spec=spec,
            files=tuple(files),
            source_dir=cache_dir,
            commit_sha=sha,
        )

    @staticmethod
    def _reject_external_source(entry: dict[str, Any], /) -> None:
        """Raise if the plugin source is an external URL dict, not a relative path."""
        source = entry.get("source", "")
        if isinstance(source, dict):
            raise SyncError(
                f"External source not supported for plugin '{entry.get('name')}'. "
                "Only relative-path plugins are supported in this version."
            )

    def _read_marketplace_json(self) -> dict[str, Any]:
        """Read marketplace.json from the local clone."""
        manifest_path = self._clone.clone_dir / MARKETPLACE_PATH
        if not manifest_path.is_file():
            raise SyncError(
                f"marketplace.json not found in clone at {manifest_path}. "
                f"Registry {self._owner}/{self._repo} may not be a valid marketplace."
            )
        return json.loads(manifest_path.read_text())

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

    def _copy_plugin(
        self,
        entry: dict[str, Any],
        marketplace: dict[str, Any],
        cache_dir: Path,
        /,
    ) -> None:
        """Copy plugin files from the local clone to the cache directory."""
        skills = entry.get("skills")
        if skills:
            self._copy_skills(skills, cache_dir)
        else:
            source_path = self._resolve_source_path(entry, marketplace)
            source_dir = self._clone.clone_dir / source_path
            if not source_dir.is_dir():
                raise SyncError(
                    f"Plugin directory not found in clone: {source_path}"
                )
            self._copy_directory(source_dir, cache_dir)

    def _copy_skills(self, skills: list[str], cache_dir: Path, /) -> None:
        """Copy skill directories from the clone to the cache."""
        for skill_path in skills:
            clean_path = skill_path.lstrip("./")
            source_dir = self._clone.clone_dir / clean_path
            target_dir = cache_dir / clean_path
            if source_dir.is_dir():
                self._copy_directory(source_dir, target_dir)

    @staticmethod
    def _copy_directory(source_dir: Path, target_dir: Path, /) -> None:
        """Copy all files from source to target, preserving structure."""
        for source_file in source_dir.rglob("*"):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source_dir)
            target_file = target_dir / relative
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)

    @staticmethod
    def _parse_github_url(url: str, /) -> tuple[str, str]:
        match = GITHUB_URL_PATTERN.match(url)
        if not match:
            raise SyncError(
                f"Invalid GitHub URL: '{url}'. "
                "Expected format: https://github.com/owner/repo"
            )
        return match.group(1), match.group(2)
