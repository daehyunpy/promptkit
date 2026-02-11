"""Infrastructure layer: Fetch plugins from local prompts/ directory."""

from pathlib import Path

from promptkit.domain.errors import SyncError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec

LOCAL_SOURCE_PREFIX = "local/"
PROMPT_EXTENSION = ".md"
CATEGORY_DIRS = {"rules", "skills", "agents", "commands", "subagents", "hooks"}


class LocalPluginFetcher:
    """Fetches plugins from the local prompts/ directory.

    Implements the PluginFetcher protocol. Supports both single .md files
    and multi-file directories. Files stay in prompts/ — no cache needed.
    """

    def __init__(self, file_system: FileSystem, prompts_dir: Path, /) -> None:
        self._fs = file_system
        self._prompts_dir = prompts_dir

    def fetch(self, spec: PromptSpec, /) -> Plugin:
        """Fetch a local plugin by spec.

        For single files: prompts/my-rule.md → Plugin(files=("my-rule.md",))
        For directories: prompts/my-skill/ → Plugin(files=("my-skill/SKILL.md", ...))
        """
        relative = spec.source.removeprefix(LOCAL_SOURCE_PREFIX)
        md_path = self._prompts_dir / f"{relative}{PROMPT_EXTENSION}"
        dir_path = self._prompts_dir / relative

        if self._fs.file_exists(md_path):
            return Plugin(
                spec=spec,
                files=(f"{relative}{PROMPT_EXTENSION}",),
                source_dir=self._prompts_dir,
            )

        if dir_path.is_dir():
            files = self._list_files_recursive(dir_path)
            return Plugin(
                spec=spec,
                files=tuple(sorted(files)),
                source_dir=self._prompts_dir,
            )

        raise SyncError(f"Local plugin not found: {relative}")

    def discover(self) -> list[PromptSpec]:
        """Discover all plugins in the prompts directory."""
        if not self._prompts_dir.is_dir():
            return []
        return sorted(
            self._scan_directory(self._prompts_dir),
            key=lambda s: s.source,
        )

    def _scan_directory(self, directory: Path, /) -> list[PromptSpec]:
        specs: list[PromptSpec] = []
        for entry in self._fs.list_directory(directory):
            if entry.is_dir():
                if entry.name in CATEGORY_DIRS:
                    specs.extend(self._scan_directory(entry))
                else:
                    relative = str(entry.relative_to(self._prompts_dir))
                    specs.append(PromptSpec(source=f"{LOCAL_SOURCE_PREFIX}{relative}"))
            elif entry.suffix == PROMPT_EXTENSION:
                relative = entry.relative_to(self._prompts_dir)
                name = str(relative).removesuffix(PROMPT_EXTENSION)
                specs.append(PromptSpec(source=f"{LOCAL_SOURCE_PREFIX}{name}"))
        return specs

    def _list_files_recursive(self, directory: Path, /) -> list[str]:
        """List all files in a directory recursively, as paths relative to prompts_dir."""
        return [
            str(child.relative_to(self._prompts_dir))
            for child in sorted(directory.rglob("*"))
            if child.is_file()
        ]
