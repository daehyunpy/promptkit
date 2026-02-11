"""Domain layer: Protocols for infrastructure adapters."""

from pathlib import Path
from typing import Protocol

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec


class PluginFetcher(Protocol):
    """Protocol for fetching plugins from a source.

    Implementations: LocalPluginFetcher, ClaudeMarketplaceFetcher.
    cache_dir and other configuration are injected at construction time.
    """

    def fetch(self, spec: PromptSpec, /) -> Plugin:
        """Fetch plugin files for the given spec.

        Returns a Plugin manifest pointing to files on disk.
        """
        ...


class ArtifactBuilder(Protocol):
    """Protocol for building platform-specific artifacts from plugins.

    Implementations: CursorBuilder, ClaudeBuilder
    """

    @property
    def platform(self) -> PlatformTarget:
        """The platform this builder targets."""
        ...

    def build(self, plugins: list[Plugin], output_dir: Path, /) -> list[Path]:
        """Build platform-specific artifacts from plugins.

        Copies file trees from each plugin's source_dir to the output directory.
        Returns list of paths to generated artifact files.
        """
        ...
