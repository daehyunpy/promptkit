"""Application layer: LockPrompts use case."""

import hashlib
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from promptkit.domain.errors import SyncError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.lock_entry import LockEntry
from promptkit.domain.plugin import Plugin
from promptkit.domain.protocols import PluginFetcher
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import LoadedConfig, YamlLoader
from promptkit.infra.fetchers.local_plugin_fetcher import LocalPluginFetcher

CONFIG_FILENAME = "promptkit.yaml"
LOCK_FILENAME = "promptkit.lock"
HASH_PREFIX = "sha256:"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LockPrompts:
    """Use case for fetching plugins and updating the lock file.

    Single code path for both local and registry plugins:
    - Local: content_hash computed from files, commit_sha=None
    - Registry: content_hash="", commit_sha from fetcher
    """

    def __init__(
        self,
        *,
        file_system: FileSystem,
        yaml_loader: YamlLoader,
        lock_file: LockFile,
        local_fetcher: LocalPluginFetcher,
        fetchers: Mapping[str, PluginFetcher],
    ) -> None:
        self._fs = file_system
        self._yaml_loader = yaml_loader
        self._lock_file = lock_file
        self._local_fetcher = local_fetcher
        self._fetchers = fetchers

    def execute(self, project_dir: Path, /) -> int:
        """Fetch all plugins and write updated lock file.

        Returns:
            Number of plugins locked.
        """
        config = self._load_config(project_dir)
        existing_entries = self._load_existing_lock(project_dir)
        existing_by_source = {e.source: e for e in existing_entries}

        entries: list[LockEntry] = []

        for spec in config.prompt_specs:
            fetcher = self._resolve_fetcher(spec.registry_name)
            plugin = fetcher.fetch(spec)
            entries.append(self._lock_plugin(plugin, existing_by_source))

        for local_spec in self._local_fetcher.discover():
            plugin = self._local_fetcher.fetch(local_spec)
            entries.append(self._lock_plugin(plugin, existing_by_source))

        entries.sort(key=lambda e: e.name)
        lock_content = self._lock_file.serialize(entries)
        self._fs.write_file(project_dir / LOCK_FILENAME, lock_content)
        return len(entries)

    def _resolve_fetcher(self, registry_name: str, /) -> PluginFetcher:
        if registry_name not in self._fetchers:
            raise SyncError(f"No fetcher registered for registry: {registry_name}")
        return self._fetchers[registry_name]

    def _lock_plugin(
        self,
        plugin: Plugin,
        existing_by_source: dict[str, LockEntry],
    ) -> LockEntry:
        """Create a lock entry for a plugin."""
        existing = existing_by_source.get(plugin.source)

        if plugin.is_registry:
            return self._lock_registry_plugin(plugin, existing)
        return self._lock_local_plugin(plugin, existing)

    def _lock_registry_plugin(
        self, plugin: Plugin, existing: LockEntry | None, /
    ) -> LockEntry:
        assert plugin.commit_sha is not None
        fetched_at = (
            existing.fetched_at
            if existing and not existing.has_commit_changed(plugin.commit_sha)
            else _now()
        )
        return LockEntry(
            name=plugin.name,
            source=plugin.source,
            content_hash="",
            fetched_at=fetched_at,
            commit_sha=plugin.commit_sha,
        )

    def _lock_local_plugin(
        self, plugin: Plugin, existing: LockEntry | None, /
    ) -> LockEntry:
        content_hash = self._compute_content_hash(plugin)
        fetched_at = (
            existing.fetched_at
            if existing and not existing.has_content_changed(content_hash)
            else _now()
        )
        return LockEntry(
            name=plugin.name,
            source=plugin.source,
            content_hash=content_hash,
            fetched_at=fetched_at,
        )

    def _compute_content_hash(self, plugin: Plugin, /) -> str:
        """Compute content hash for a local plugin.

        For single files: sha256(content).
        For directories: sort files by path, concatenate path + content, sha256.
        """
        hasher = hashlib.sha256()
        for file_path in sorted(plugin.files):
            full_path = plugin.source_dir / file_path
            content = self._fs.read_file(full_path)
            hasher.update(f"{file_path}\n{content}".encode())
        return f"{HASH_PREFIX}{hasher.hexdigest()}"

    def _load_config(self, project_dir: Path, /) -> LoadedConfig:
        config_path = project_dir / CONFIG_FILENAME
        try:
            yaml_content = self._fs.read_file(config_path)
        except FileNotFoundError:
            raise SyncError(
                f"{CONFIG_FILENAME} not found. Run 'promptkit init' to create a new project."
            ) from None
        return self._yaml_loader.load(yaml_content)

    def _load_existing_lock(self, project_dir: Path, /) -> list[LockEntry]:
        lock_path = project_dir / LOCK_FILENAME
        if not self._fs.file_exists(lock_path):
            return []
        lock_content = self._fs.read_file(lock_path)
        return self._lock_file.deserialize(lock_content)
