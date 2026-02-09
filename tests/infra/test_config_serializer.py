"""Tests for YAML config serialization."""

import yaml

from promptkit.domain.project_config import ProjectConfig
from promptkit.infra.config_serializer import serialize_config_to_yaml


def test_serialize_produces_valid_yaml() -> None:
    """serialize_config_to_yaml should produce parseable YAML."""
    config = ProjectConfig.default()

    result = yaml.safe_load(serialize_config_to_yaml(config))

    assert result is not None


def test_serialize_contains_required_fields() -> None:
    """Serialized YAML should contain version, prompts, and platforms."""
    config = ProjectConfig.default()

    result = yaml.safe_load(serialize_config_to_yaml(config))

    assert result["version"] == 1
    assert "prompts" in result
    assert "platforms" in result


def test_serialize_includes_example_when_prompts_empty() -> None:
    """Serialized YAML should include commented example when prompts list is empty."""
    config = ProjectConfig.default()

    yaml_str = serialize_config_to_yaml(config)

    assert "# Example prompt entry" in yaml_str
    assert "# - name: code-reviewer" in yaml_str
