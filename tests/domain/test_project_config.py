"""Tests for ProjectConfig value object."""

import yaml

from promptkit.domain.project_config import ProjectConfig


def test_default_config_has_required_fields():
    """Default config should have version, prompts, and platforms."""
    config = ProjectConfig.default()

    assert config.version == 1
    assert config.prompts == []
    assert "cursor" in config.platforms
    assert "claude-code" in config.platforms


def test_default_config_has_platform_output_dirs():
    """Default config should specify output directories for platforms."""
    config = ProjectConfig.default()

    assert config.platforms["cursor"]["output_dir"] == ".cursor"
    assert config.platforms["claude-code"]["output_dir"] == ".claude"


def test_to_yaml_string_produces_valid_yaml():
    """to_yaml_string() should produce parseable YAML."""
    config = ProjectConfig.default()
    yaml_str = config.to_yaml_string()

    # Should be parseable
    parsed = yaml.safe_load(yaml_str)
    assert parsed is not None


def test_to_yaml_string_contains_required_fields():
    """YAML output should contain version, prompts, and platforms."""
    config = ProjectConfig.default()
    yaml_str = config.to_yaml_string()
    parsed = yaml.safe_load(yaml_str)

    assert "version" in parsed
    assert "prompts" in parsed
    assert "platforms" in parsed
    assert parsed["version"] == 1


def test_to_yaml_string_includes_example_when_empty():
    """YAML output should include commented example when prompts list is empty."""
    config = ProjectConfig.default()
    yaml_str = config.to_yaml_string()

    assert "# Example prompt entry" in yaml_str
    assert "# - name: code-reviewer" in yaml_str
