"""Infrastructure layer: Claude Code platform artifact builder."""

import shutil
from pathlib import Path

from promptkit.domain.file_system import FileSystem
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin


class ClaudeBuilder:
    """Builds .claude/ artifacts by copying plugin file trees.

    Implements the ArtifactBuilder protocol. Copies all files from each
    plugin's source_dir to the output directory, preserving structure.
    """

    def __init__(self, file_system: FileSystem, /) -> None:
        self._fs = file_system

    @property
    def platform(self) -> PlatformTarget:
        return PlatformTarget.CLAUDE_CODE

    def build(self, plugins: list[Plugin], output_dir: Path, /) -> list[Path]:
        """Copy plugin file trees to the Claude Code output directory."""
        self._fs.remove_directory(output_dir)
        generated: list[Path] = []
        for plugin in plugins:
            for file_path in plugin.files:
                src = plugin.source_dir / file_path
                dst = output_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                generated.append(dst)
        return generated
