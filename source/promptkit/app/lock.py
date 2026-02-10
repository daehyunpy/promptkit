"""Application layer: LockPrompts use case."""

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from promptkit.domain.errors import SyncError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.lock_entry import LockEntry
from promptkit.domain.prompt import Prompt
from promptkit.domain.protocols import PromptFetcher
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import LoadedConfig, YamlLoader
from promptkit.infra.fetchers.local_file_fetcher import LocalFileFetcher
from promptkit.infra.storage.prompt_cache import PromptCache

CONFIG_FILENAME = "promptkit.yaml"
LOCK_FILENAME = "promptkit.lock"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LockPrompts:
    """Use case for fetching prompts and updating the lock file."""

    def __init__(
        self,
        *,
        file_system: FileSystem,
        yaml_loader: YamlLoader,
        lock_file: LockFile,
        prompt_cache: PromptCache,
        local_fetcher: LocalFileFetcher,
        fetchers: Mapping[str, PromptFetcher],
    ) -> None:
        self._fs = file_system
        self._yaml_loader = yaml_loader
        self._lock_file = lock_file
        self._cache = prompt_cache
        self._local_fetcher = local_fetcher
        self._fetchers = fetchers

    def execute(self, project_dir: Path, /) -> None:
        """Fetch all prompts and write updated lock file."""
        config = self._load_config(project_dir)
        existing_entries = self._load_existing_lock(project_dir)
        existing_by_source = {e.source: e for e in existing_entries}

        entries: list[LockEntry] = []

        for spec in config.prompt_specs:
            fetcher = self._resolve_fetcher(spec.registry_name)
            prompt = fetcher.fetch(spec)
            entries.append(self._lock_prompt(prompt, existing_by_source))

        for local_spec in self._local_fetcher.discover():
            prompt = self._local_fetcher.fetch(local_spec)
            entries.append(self._lock_prompt(prompt, existing_by_source))

        entries.sort(key=lambda e: e.name)
        lock_content = self._lock_file.serialize(entries)
        self._fs.write_file(project_dir / LOCK_FILENAME, lock_content)

    def _resolve_fetcher(self, registry_name: str, /) -> PromptFetcher:
        if registry_name not in self._fetchers:
            raise SyncError(
                f"No fetcher registered for registry: {registry_name}"
            )
        return self._fetchers[registry_name]

    def _lock_prompt(
        self,
        prompt: Prompt,
        existing_by_source: dict[str, LockEntry],
    ) -> LockEntry:
        """Cache a prompt and create its lock entry."""
        self._cache.store(prompt.content)
        existing = existing_by_source.get(prompt.source)
        fetched_at = (
            existing.fetched_at
            if existing and not existing.has_content_changed(prompt.content_hash)
            else _now()
        )
        return LockEntry(
            name=prompt.name,
            source=prompt.source,
            content_hash=prompt.content_hash,
            fetched_at=fetched_at,
        )

    def _load_config(self, project_dir: Path, /) -> LoadedConfig:
        config_path = project_dir / CONFIG_FILENAME
        yaml_content = self._fs.read_file(config_path)
        return self._yaml_loader.load(yaml_content)

    def _load_existing_lock(self, project_dir: Path, /) -> list[LockEntry]:
        lock_path = project_dir / LOCK_FILENAME
        if not self._fs.file_exists(lock_path):
            return []
        lock_content = self._fs.read_file(lock_path)
        return self._lock_file.deserialize(lock_content)
