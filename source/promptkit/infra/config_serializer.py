"""Infrastructure layer: YAML serialization for ProjectConfig."""

import yaml

from promptkit.domain.project_config import ProjectConfig

PROMPT_EXAMPLE_COMMENT = """\
  # Example prompt entry - uncomment and edit
  # - claude-plugins-official/code-review
  # - anthropic-agent-skills/document-skills
"""


def serialize_config_to_yaml(config: ProjectConfig, /) -> str:
    """Serialize a ProjectConfig to a YAML string.

    When the prompts list is empty, includes a commented-out example
    to guide users.
    """
    yaml_output = yaml.dump(config.to_dict(), sort_keys=False, default_flow_style=False)

    if not config.prompts:
        yaml_output = yaml_output.replace(
            "prompts: []\n", f"prompts:\n{PROMPT_EXAMPLE_COMMENT}\n"
        )

    return yaml_output
