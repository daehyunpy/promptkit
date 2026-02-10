"""Infrastructure layer: Cursor platform artifact builder."""

from pathlib import Path

from promptkit.domain.file_system import FileSystem
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt import Prompt

PROMPT_EXTENSION = ".md"

CATEGORY_DIRS: dict[str, str] = {
    "skills": "skills-cursor",
    "rules": "rules",
    "agents": "agents",
    "commands": "commands",
    "subagents": "subagents",
}


class CursorBuilder:
    """Builds .cursor/ artifacts from prompts using directory-based routing.

    Implements the ArtifactBuilder protocol. Maps prompt categories to
    Cursor-specific output directories (e.g., skills → skills-cursor).
    """

    def __init__(self, file_system: FileSystem, /) -> None:
        self._fs = file_system

    @property
    def platform(self) -> PlatformTarget:
        return PlatformTarget.CURSOR

    def build(self, prompts: list[Prompt], output_dir: Path, /) -> list[Path]:
        """Build Cursor artifacts from prompts.

        Cleans the output directory before writing. Returns list of
        paths to generated artifact files.
        """
        self._fs.remove_directory(output_dir)
        generated: list[Path] = []
        for prompt in prompts:
            path = self._route(prompt, output_dir)
            self._fs.write_file(path, prompt.content)
            generated.append(path)
        return generated

    def _route(self, prompt: Prompt, output_dir: Path, /) -> Path:
        category_dir = CATEGORY_DIRS.get(prompt.category, prompt.category)
        return output_dir / category_dir / f"{prompt.filename}{PROMPT_EXTENSION}"
