"""Domain layer: Registry value object and RegistryType enum."""

from dataclasses import dataclass, field
from enum import Enum


class RegistryType(Enum):
    """Type of prompt registry, determines which fetcher to use."""

    CLAUDE_MARKETPLACE = "claude-marketplace"

    @classmethod
    def from_string(cls, value: str, /) -> "RegistryType":
        """Create RegistryType from string value.

        Raises:
            ValueError: If value doesn't match any registry type.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown registry type: '{value}'. Valid types: {valid}")


@dataclass(frozen=True)
class Registry:
    """Immutable registry definition from promptkit.yaml.

    Declares where to fetch remote prompts. The type determines
    which PromptFetcher implementation to use.
    """

    name: str
    url: str
    registry_type: RegistryType = field(default=RegistryType.CLAUDE_MARKETPLACE)
