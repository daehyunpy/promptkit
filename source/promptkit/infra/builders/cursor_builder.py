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

ALLOWED_CATEGORIES = {"commands", "agents", "skills", "rules"}

PLATFORM_NAME = "cursor"


class CursorBuilder:
    """Builds .cursor/ artifacts by copying plugin file trees.

    Implements the ArtifactBuilder protocol. Filters to allowed categories
    and uses manifest-based cleanup to preserve non-promptkit files.
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
        """Filter to allowed categories, passing paths through unchanged.

        Returns None if the file is not under an allowed category.
        """
        if "/" not in file_path:
            return None

        top_dir = file_path.split("/", 1)[0]

        if top_dir not in ALLOWED_CATEGORIES:
            return None

        return file_path
