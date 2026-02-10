"""Application layer: BuildArtifacts use case."""

from collections.abc import Mapping
from pathlib import Path

from promptkit.domain.errors import BuildError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.lock_entry import LockEntry
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt import Prompt
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.domain.protocols import ArtifactBuilder
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import LoadedConfig, YamlLoader
from promptkit.infra.storage.prompt_cache import PromptCache

CONFIG_FILENAME = "promptkit.yaml"
LOCK_FILENAME = "promptkit.lock"
PROMPTS_DIR = "prompts"
LOCAL_SOURCE_PREFIX = "local/"
PROMPT_EXTENSION = ".md"


class BuildArtifacts:
    """Use case for generating platform-specific artifacts from locked prompts."""

    def __init__(
        self,
        *,
        file_system: FileSystem,
        yaml_loader: YamlLoader,
        lock_file: LockFile,
        prompt_cache: PromptCache,
        builders: Mapping[PlatformTarget, ArtifactBuilder],
    ) -> None:
        self._fs = file_system
        self._yaml_loader = yaml_loader
        self._lock_file = lock_file
        self._cache = prompt_cache
        self._builders = builders

    def execute(self, project_dir: Path, /) -> None:
        """Load config and lock, read prompts, delegate to platform builders."""
        config = self._load_config(project_dir)
        entries = self._load_lock(project_dir)
        specs_by_source = {s.source: s for s in config.prompt_specs}
        prompts = [
            self._load_prompt(entry, project_dir, specs_by_source)
            for entry in entries
        ]

        for platform_config in config.platform_configs:
            builder = self._builders.get(platform_config.platform_type)
            if builder is None:
                continue
            filtered = [
                p
                for p in prompts
                if p.is_valid_for_platform(platform_config.platform_type)
            ]
            output_dir = project_dir / platform_config.output_dir
            builder.build(filtered, output_dir)

    def _load_config(self, project_dir: Path, /) -> LoadedConfig:
        config_path = project_dir / CONFIG_FILENAME
        yaml_content = self._fs.read_file(config_path)
        return self._yaml_loader.load(yaml_content)

    def _load_lock(self, project_dir: Path, /) -> list[LockEntry]:
        lock_path = project_dir / LOCK_FILENAME
        if not self._fs.file_exists(lock_path):
            raise BuildError(
                "Lock file not found. Run 'promptkit lock' first."
            )
        lock_content = self._fs.read_file(lock_path)
        return self._lock_file.deserialize(lock_content)

    def _load_prompt(
        self,
        entry: LockEntry,
        project_dir: Path,
        specs_by_source: dict[str, PromptSpec],
        /,
    ) -> Prompt:
        content = self._read_content(entry, project_dir)
        spec = specs_by_source.get(
            entry.source,
            PromptSpec(source=entry.source, name=entry.name),
        )
        return Prompt(spec=spec, content=content)

    def _read_content(
        self, entry: LockEntry, project_dir: Path, /
    ) -> str:
        if entry.source.startswith(LOCAL_SOURCE_PREFIX):
            return self._read_local_content(entry, project_dir)
        return self._read_cached_content(entry)

    def _read_local_content(
        self, entry: LockEntry, project_dir: Path, /
    ) -> str:
        relative = entry.source.removeprefix(LOCAL_SOURCE_PREFIX)
        file_path = project_dir / PROMPTS_DIR / f"{relative}{PROMPT_EXTENSION}"
        return self._fs.read_file(file_path)

    def _read_cached_content(self, entry: LockEntry, /) -> str:
        content = self._cache.retrieve(entry.content_hash)
        if content is None:
            raise BuildError(
                f"Cached content missing for '{entry.name}' "
                f"(hash: {entry.content_hash}). Run 'promptkit lock' to re-fetch."
            )
        return content
