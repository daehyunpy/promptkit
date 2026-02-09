"""Domain layer: PromptSpec value object and ArtifactType enum."""

from dataclasses import dataclass, field
from enum import Enum

from promptkit.domain.platform_target import PlatformTarget


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
    """Immutable specification for a prompt from promptkit.yaml.

    Declares which prompt to fetch and where to build it.
    The source format is 'registry/name' (e.g., 'claude-plugins-official/code-review').
    Name defaults to the part after '/' in the source if not explicitly set.
    """

    source: str
    name: str = ""
    platforms: tuple[PlatformTarget, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, "name", self.prompt_name)

    @property
    def registry_name(self) -> str:
        """The registry part of the source (before '/')."""
        return self.source.split("/", 1)[0]

    @property
    def prompt_name(self) -> str:
        """The prompt name part of the source (after '/')."""
        return self.source.split("/", 1)[1]

    def targets_platform(self, platform: PlatformTarget, /) -> bool:
        """Whether this prompt targets the given platform.

        An empty platforms tuple means the prompt targets all platforms.
        """
        if not self.platforms:
            return True
        return platform in self.platforms
