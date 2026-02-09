"""Domain layer: ProjectConfig value object for promptkit.yaml structure."""

from dataclasses import dataclass, field
from typing import Any

DEFAULT_VERSION = 1

DEFAULT_REGISTRIES: dict[str, str] = {
    "anthropic-agent-skills": "https://github.com/anthropics/skills",
    "claude-plugins-official": "https://github.com/anthropics/claude-plugins-official",
}

DEFAULT_PLATFORMS: dict[str, dict[str, str]] = {
    "cursor": {"output_dir": ".cursor"},
    "claude-code": {"output_dir": ".claude"},
}


@dataclass(frozen=True)
class ProjectConfig:
    """Configuration for a promptkit project (promptkit.yaml structure)."""

    version: int
    registries: dict[str, str] = field(default_factory=dict)
    prompts: list[dict[str, Any]] = field(default_factory=list)
    platforms: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def default(cls, /) -> "ProjectConfig":
        """Return default configuration with MVP registries and platforms."""
        return cls(
            version=DEFAULT_VERSION,
            registries=dict(DEFAULT_REGISTRIES),
            prompts=[],
            platforms=dict(DEFAULT_PLATFORMS),
        )

    def to_dict(self, /) -> dict[str, Any]:
        """Return configuration as a plain dictionary."""
        return {
            "version": self.version,
            "registries": self.registries,
            "prompts": self.prompts,
            "platforms": self.platforms,
        }
