"""Domain layer: PlatformTarget enum for supported output platforms."""

from enum import Enum


class PlatformTarget(Enum):
    """Supported platform targets for artifact generation."""

    CURSOR = "cursor"
    CLAUDE_CODE = "claude-code"

    @classmethod
    def from_string(cls, value: str, /) -> "PlatformTarget":
        """Create PlatformTarget from string value.

        Raises:
            ValueError: If value doesn't match any platform target.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(m.value for m in cls)
        raise ValueError(f"Unknown platform target: '{value}'. Valid targets: {valid}")
