"""Domain layer: ProjectConfig value object for promptkit.yaml structure."""

from dataclasses import dataclass, field

import yaml


@dataclass(frozen=True)
class ProjectConfig:
    """Configuration for a promptkit project (promptkit.yaml structure)."""

    version: int
    prompts: list[dict[str, any]] = field(default_factory=list)
    platforms: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def default(cls, /) -> "ProjectConfig":
        """Return default configuration with example prompt structure."""
        return cls(
            version=1,
            prompts=[],
            platforms={
                "cursor": {"output_dir": ".cursor"},
                "claude-code": {"output_dir": ".claude"},
            },
        )

    def to_yaml_string(self, /) -> str:
        """Serialize configuration to YAML string."""
        # Build config dict
        config_dict = {
            "version": self.version,
            "prompts": self.prompts if self.prompts else [],
            "platforms": self.platforms,
        }

        # Add commented example if prompts list is empty
        yaml_output = yaml.dump(config_dict, sort_keys=False, default_flow_style=False)

        if not self.prompts:
            # Insert commented example after prompts: []
            example = """  # Example prompt entry - uncomment and edit
  # - name: code-reviewer
  #   source: anthropic/code-reviewer
  #   platforms:
  #     - cursor
  #     - claude-code
"""
            yaml_output = yaml_output.replace("prompts: []\n", f"prompts:\n{example}\n")

        return yaml_output
