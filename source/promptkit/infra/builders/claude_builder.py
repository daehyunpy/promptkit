"""Infrastructure layer: Claude Code platform artifact builder."""

import shutil
from pathlib import Path

from promptkit.domain.file_system import FileSystem
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.infra.builders.manifest import (
    cleanup_managed_files,
    read_manifest,
    write_manifest,
)

PLATFORM_NAME = "claude"
ALLOWED_CATEGORIES = {"commands", "agents", "skills", "hooks", "scripts", "rules"}


class ClaudeBuilder:
    """Builds .claude/ artifacts by copying plugin file trees.

    Implements the ArtifactBuilder protocol. Copies all files from each
    plugin's source_dir to the output directory, preserving structure.
    Uses manifest-based cleanup to preserve non-promptkit files.
    """

    def __init__(self, file_system: FileSystem, /) -> None:
        self._fs = file_system

    @property
    def platform(self) -> PlatformTarget:
        return PlatformTarget.CLAUDE_CODE

    def build(
        self, plugins: list[Plugin], output_dir: Path, project_dir: Path, /
    ) -> list[Path]:
        """Copy plugin file trees to the Claude Code output directory."""
        previous = read_manifest(project_dir, PLATFORM_NAME)
        cleanup_managed_files(output_dir, previous)

        generated: list[Path] = []
        relative_paths: list[str] = []

        for plugin in plugins:
            for file_path in plugin.files:
                if not _is_allowed(file_path):
                    continue
                src = plugin.source_dir / file_path
                dst = output_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                generated.append(dst)
                relative_paths.append(file_path)

        write_manifest(project_dir, PLATFORM_NAME, relative_paths)
        return generated



def _is_allowed(file_path: str, /) -> bool:
    """Only copy files under allowed category directories."""
    if "/" not in file_path:
        return False
    top_dir = file_path.split("/", 1)[0]
    return top_dir in ALLOWED_CATEGORIES
