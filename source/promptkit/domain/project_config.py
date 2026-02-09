"""Domain layer: ProjectConfig value object for promptkit.yaml structure."""

from dataclasses import dataclass, field
from typing import Any

DEFAULT_VERSION = 1

DEFAULT_PLATFORMS: dict[str, dict[str, str]] = {
    "cursor": {"output_dir": ".cursor"},
    "claude-code": {"output_dir": ".claude"},
}


@dataclass(frozen=True)
class ProjectConfig:
    """Configuration for a promptkit project (promptkit.yaml structure)."""

    version: int
    prompts: list[dict[str, Any]] = field(default_factory=list)
    platforms: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def default(cls, /) -> "ProjectConfig":
        """Return default configuration with example prompt structure."""
        return cls(
            version=DEFAULT_VERSION,
            prompts=[],
            platforms=dict(DEFAULT_PLATFORMS),
        )

    def to_dict(self, /) -> dict[str, Any]:
        """Return configuration as a plain dictionary."""
        return {
            "version": self.version,
            "prompts": self.prompts,
            "platforms": self.platforms,
        }
