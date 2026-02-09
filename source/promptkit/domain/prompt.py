"""Domain layer: Prompt aggregate root."""

import hashlib
from dataclasses import dataclass, field

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_metadata import PromptMetadata
from promptkit.domain.prompt_spec import ArtifactType, PromptSpec

HASH_PREFIX = "sha256:"


@dataclass
class Prompt:
    """Aggregate root representing a synced prompt.

    A Prompt has identity (via its spec name), holds content fetched from a source,
    and knows which platforms it targets. All access to prompt data goes through
    this aggregate.
    """

    spec: PromptSpec
    content: str
    metadata: PromptMetadata | None = field(default=None)

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def source(self) -> str:
        return self.spec.source

    @property
    def artifact_type(self) -> ArtifactType:
        return self.spec.artifact_type

    @property
    def content_hash(self) -> str:
        """SHA256 hash of the prompt content, prefixed with 'sha256:'."""
        digest = hashlib.sha256(self.content.encode()).hexdigest()
        return f"{HASH_PREFIX}{digest}"

    def is_valid_for_platform(self, platform: PlatformTarget, /) -> bool:
        """Whether this prompt is valid for the given platform."""
        return self.spec.targets_platform(platform)
