"""Domain layer: PromptMetadata value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptMetadata:
    """Immutable metadata about a prompt (author, description, version)."""

    author: str | None = None
    description: str | None = None
    version: str | None = None
