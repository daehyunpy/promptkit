"""Domain layer: PromptSpec value object and ArtifactType enum."""

from dataclasses import dataclass, field
from enum import Enum

from promptkit.domain.platform_target import PlatformTarget

LOCAL_SOURCE_PREFIX = "local/"


class ArtifactType(Enum):
    """Type of artifact a prompt produces in a platform."""

    SKILL = "skill"
    RULE = "rule"
    AGENT = "agent"
    COMMAND = "command"
    SUBAGENT = "subagent"

    @classmethod
    def from_string(cls, value: str, /) -> "ArtifactType":
        """Create ArtifactType from string value.

        Raises:
            ValueError: If value doesn't match any artifact type.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown artifact type: '{value}'. Valid types: {valid}")


@dataclass(frozen=True)
class PromptSpec:
    """Immutable specification for a prompt (source, name, platforms, artifact type).

    Defined in promptkit.yaml — declares what to sync and where to build.
    """

    name: str
    source: str
    artifact_type: ArtifactType
    platforms: tuple[PlatformTarget, ...] = field(default_factory=tuple)

    @property
    def is_local_source(self) -> bool:
        """Whether this prompt comes from the local .agents/ directory."""
        return self.source.startswith(LOCAL_SOURCE_PREFIX)

    def targets_platform(self, platform: PlatformTarget, /) -> bool:
        """Whether this prompt targets the given platform.

        An empty platforms tuple means the prompt targets all platforms.
        """
        if not self.platforms:
            return True
        return platform in self.platforms
