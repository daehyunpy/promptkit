"""Infrastructure layer: Fetch prompts from local prompts/ directory."""

from pathlib import Path

from promptkit.domain.errors import SyncError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.prompt import Prompt
from promptkit.domain.prompt_spec import PromptSpec

LOCAL_SOURCE_PREFIX = "local/"
PROMPT_EXTENSION = ".md"


class LocalFileFetcher:
    """Fetches prompts from the local prompts/ directory.

    Implements the PromptFetcher protocol. Also provides discover()
    to scan for all local .md files.
    """

    def __init__(self, file_system: FileSystem, prompts_dir: Path, /) -> None:
        self._fs = file_system
        self._prompts_dir = prompts_dir

    def fetch(self, spec: PromptSpec, /) -> Prompt:
        """Fetch a local prompt by spec.

        The spec source must be in 'local/<relative-path>' format.
        """
        relative = spec.source.removeprefix(LOCAL_SOURCE_PREFIX)
        file_path = self._prompts_dir / f"{relative}{PROMPT_EXTENSION}"

        try:
            content = self._fs.read_file(file_path)
        except FileNotFoundError:
            raise SyncError(
                f"Local prompt not found: {relative}{PROMPT_EXTENSION}"
            ) from None

        return Prompt(spec=spec, content=content)

    def discover(self) -> list[PromptSpec]:
        """Discover all .md files in the prompts directory."""
        return sorted(
            self._scan_directory(self._prompts_dir),
            key=lambda s: s.source,
        )

    def _scan_directory(self, directory: Path, /) -> list[PromptSpec]:
        specs: list[PromptSpec] = []
        for entry in self._fs.list_directory(directory):
            if entry.is_dir():
                specs.extend(self._scan_directory(entry))
            elif entry.suffix == PROMPT_EXTENSION:
                relative = entry.relative_to(self._prompts_dir)
                name = str(relative).removesuffix(PROMPT_EXTENSION)
                specs.append(PromptSpec(source=f"{LOCAL_SOURCE_PREFIX}{name}"))
        return specs
