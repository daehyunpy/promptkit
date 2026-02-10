"""Domain layer: Prompt aggregate root."""

import hashlib
from dataclasses import dataclass, field

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_metadata import PromptMetadata
from promptkit.domain.prompt_spec import PromptSpec

HASH_PREFIX = "sha256:"
DEFAULT_CATEGORY = "rules"
LOCAL_SOURCE_PREFIX = "local/"


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
    def content_hash(self) -> str:
        """SHA256 hash of the prompt content, prefixed with 'sha256:'."""
        digest = hashlib.sha256(self.content.encode()).hexdigest()
        return f"{HASH_PREFIX}{digest}"

    @property
    def filename(self) -> str:
        """The prompt's filename (last segment of source path)."""
        return self.source.rsplit("/", 1)[-1]

    @property
    def category(self) -> str:
        """The prompt's category derived from its source path.

        For 'local/skills/my-skill' → 'skills'.
        For 'local/my-rule' (flat, no subdirectory) → 'rules' (default).
        For 'registry/prompt-name' (flat) → 'rules' (default).
        """
        # Strip the prefix (e.g., "local/" or "registry/")
        _, _, relative = self.source.partition("/")
        parts = relative.split("/")
        if len(parts) >= 2:
            return parts[0]
        return DEFAULT_CATEGORY

    def is_valid_for_platform(self, platform: PlatformTarget, /) -> bool:
        """Whether this prompt is valid for the given platform."""
        return self.spec.targets_platform(platform)
