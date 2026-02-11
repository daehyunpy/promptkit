"""Domain layer: Plugin value object representing a fetched plugin manifest."""

from dataclasses import dataclass
from pathlib import Path

from promptkit.domain.prompt_spec import PromptSpec


@dataclass(frozen=True)
class Plugin:
    """Immutable manifest for a fetched plugin (local or registry).

    A Plugin points to files on disk — it does not hold file content in memory.
    Both local and registry plugins are file trees; a single .md file is just
    a degenerate case (a directory with one file).
    """

    spec: PromptSpec
    files: tuple[str, ...]
    source_dir: Path
    commit_sha: str | None = None

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def source(self) -> str:
        return self.spec.source

    @property
    def is_registry(self) -> bool:
        return self.commit_sha is not None
