"""Application layer: BuildArtifacts use case."""

from collections.abc import Mapping
from pathlib import Path

from promptkit.domain.errors import BuildError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.lock_entry import LockEntry
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.domain.protocols import ArtifactBuilder
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import LoadedConfig, YamlLoader
from promptkit.infra.storage.plugin_cache import PluginCache

CONFIG_FILENAME = "promptkit.yaml"
LOCK_FILENAME = "promptkit.lock"
PROMPTS_DIR = "prompts"
LOCAL_SOURCE_PREFIX = "local/"


class BuildArtifacts:
    """Use case for generating platform-specific artifacts from locked plugins."""

    def __init__(
        self,
        *,
        file_system: FileSystem,
        yaml_loader: YamlLoader,
        lock_file: LockFile,
        plugin_cache: PluginCache,
        builders: Mapping[PlatformTarget, ArtifactBuilder],
    ) -> None:
        self._fs = file_system
        self._yaml_loader = yaml_loader
        self._lock_file = lock_file
        self._plugin_cache = plugin_cache
        self._builders = builders

    def execute(self, project_dir: Path, /) -> None:
        """Load config and lock, resolve plugins, delegate to builders."""
        config = self._load_config(project_dir)
        entries = self._load_lock(project_dir)
        specs_by_source = {s.source: s for s in config.prompt_specs}

        plugins = [
            self._resolve_plugin(entry, project_dir, specs_by_source)
            for entry in entries
        ]

        for platform_config in config.platform_configs:
            builder = self._builders.get(platform_config.platform_type)
            if builder is None:
                continue
            filtered = [
                p
                for p in plugins
                if p.spec.targets_platform(platform_config.platform_type)
            ]
            output_dir = project_dir / platform_config.output_dir
            builder.build(filtered, output_dir)

    def _resolve_plugin(
        self,
        entry: LockEntry,
        project_dir: Path,
        specs_by_source: dict[str, PromptSpec],
        /,
    ) -> Plugin:
        """Resolve a lock entry to a Plugin manifest."""
        spec = specs_by_source.get(
            entry.source,
            PromptSpec(source=entry.source, name=entry.name),
        )

        if entry.commit_sha is not None:
            source_dir, files = self._resolve_registry_plugin(entry)
        else:
            source_dir = project_dir / PROMPTS_DIR
            files = self._list_local_files(entry, project_dir)

        return Plugin(
            spec=spec,
            files=tuple(files),
            source_dir=source_dir,
            commit_sha=entry.commit_sha,
        )

    def _resolve_registry_plugin(self, entry: LockEntry, /) -> tuple[Path, list[str]]:
        """Resolve source directory and file list for a registry plugin."""
        assert entry.commit_sha is not None
        registry, plugin_name = entry.source.split("/", 1)
        cache_dir = self._plugin_cache.plugin_dir(
            registry, plugin_name, entry.commit_sha
        )
        if not cache_dir.is_dir():
            raise BuildError(
                f"Cached plugin missing for '{entry.name}' "
                f"(sha: {entry.commit_sha}). Run 'promptkit lock' to re-fetch."
            )
        files = self._plugin_cache.list_files(registry, plugin_name, entry.commit_sha)
        return cache_dir, files

    def _list_local_files(self, entry: LockEntry, project_dir: Path, /) -> list[str]:
        relative = entry.source.removeprefix(LOCAL_SOURCE_PREFIX)
        prompts_dir = project_dir / PROMPTS_DIR
        md_path = prompts_dir / f"{relative}.md"
        dir_path = prompts_dir / relative

        if md_path.is_file():
            return [f"{relative}.md"]
        if dir_path.is_dir():
            return sorted(
                str(f.relative_to(prompts_dir))
                for f in dir_path.rglob("*")
                if f.is_file()
            )
        raise BuildError(f"Local plugin not found for '{entry.name}': {relative}")

    def _load_config(self, project_dir: Path, /) -> LoadedConfig:
        config_path = project_dir / CONFIG_FILENAME
        yaml_content = self._fs.read_file(config_path)
        return self._yaml_loader.load(yaml_content)

    def _load_lock(self, project_dir: Path, /) -> list[LockEntry]:
        lock_path = project_dir / LOCK_FILENAME
        if not self._fs.file_exists(lock_path):
            raise BuildError("Lock file not found. Run 'promptkit lock' first.")
        lock_content = self._fs.read_file(lock_path)
        return self._lock_file.deserialize(lock_content)
