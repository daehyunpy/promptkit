"""Domain layer: Protocols for infrastructure adapters."""

from pathlib import Path
from typing import Protocol

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt import Prompt
from promptkit.domain.prompt_spec import PromptSpec


class PromptFetcher(Protocol):
    """Protocol for fetching prompt content from a registry.

    Implementations: ClaudeMarketplaceFetcher (selected by registry type)
    """

    def fetch(self, spec: PromptSpec, /) -> list[Prompt]:
        """Fetch prompt content for the given spec.

        Returns a list of Prompts. Multi-file plugins produce multiple prompts
        from a single spec; single-file prompts return a one-element list.
        """
        ...


class ArtifactBuilder(Protocol):
    """Protocol for building platform-specific artifacts from prompts.

    Implementations: CursorBuilder, ClaudeBuilder
    """

    @property
    def platform(self) -> PlatformTarget:
        """The platform this builder targets."""
        ...

    def build(self, prompts: list[Prompt], output_dir: Path, /) -> list[Path]:
        """Build platform-specific artifacts from prompts.

        Returns list of paths to generated artifact files.
        """
        ...
