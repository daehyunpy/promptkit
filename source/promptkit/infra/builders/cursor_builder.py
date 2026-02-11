"""Infrastructure layer: Cursor platform artifact builder."""

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

CATEGORY_MAPPING: dict[str, str] = {
    "skills": "skills-cursor",
}

SKIPPED_CATEGORIES = {"agents", "commands", "hooks"}

PLATFORM_NAME = "cursor"


class CursorBuilder:
    """Builds .cursor/ artifacts by copying plugin file trees.

    Implements the ArtifactBuilder protocol. Applies directory mapping
    (skills → skills-cursor) and skips unsupported categories (agents,
    commands, hooks). Uses manifest-based cleanup to preserve non-promptkit files.
    """

    def __init__(self, file_system: FileSystem, /) -> None:
        self._fs = file_system

    @property
    def platform(self) -> PlatformTarget:
        return PlatformTarget.CURSOR

    def build(
        self, plugins: list[Plugin], output_dir: Path, project_dir: Path, /
    ) -> list[Path]:
        """Copy plugin file trees to the Cursor output directory."""
        previous = read_manifest(project_dir, PLATFORM_NAME)
        cleanup_managed_files(output_dir, previous)

        generated: list[Path] = []
        relative_paths: list[str] = []

        for plugin in plugins:
            for file_path in plugin.files:
                mapped = self._map_path(file_path)
                if mapped is None:
                    continue
                src = plugin.source_dir / file_path
                dst = output_dir / mapped
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                generated.append(dst)
                relative_paths.append(mapped)

        write_manifest(project_dir, PLATFORM_NAME, relative_paths)
        return generated

    @staticmethod
    def _map_path(file_path: str, /) -> str | None:
        """Map a file path for Cursor, applying directory renames and filtering.

        Returns None if the file should be skipped.
        """
        if "/" not in file_path:
            return file_path

        top_dir, rest = file_path.split("/", 1)

        if top_dir in SKIPPED_CATEGORIES:
            return None

        if top_dir in CATEGORY_MAPPING:
            return f"{CATEGORY_MAPPING[top_dir]}/{rest}"

        return file_path
