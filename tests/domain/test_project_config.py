"""Tests for ProjectConfig value object."""

from promptkit.domain.project_config import (
    DEFAULT_VERSION,
    ProjectConfig,
)


def test_default_config_has_required_fields() -> None:
    """Default config should have version, registries, prompts, and platforms."""
    config = ProjectConfig.default()

    assert config.version == DEFAULT_VERSION
    assert config.prompts == []
    assert "cursor" in config.platforms
    assert "claude-code" in config.platforms
    assert len(config.registries) > 0


def test_default_config_has_platform_output_dirs() -> None:
    """Default config should specify output directories for platforms."""
    config = ProjectConfig.default()

    assert config.platforms["cursor"]["output_dir"] == ".cursor"
    assert config.platforms["claude-code"]["output_dir"] == ".claude"


def test_default_config_has_mvp_registries() -> None:
    """Default config should include the MVP registries."""
    config = ProjectConfig.default()

    assert "anthropic-agent-skills" in config.registries
    assert "claude-plugins-official" in config.registries


def test_to_dict_contains_all_fields() -> None:
    """to_dict() should return all config fields."""
    config = ProjectConfig.default()
    result = config.to_dict()

    assert result["version"] == DEFAULT_VERSION
    assert result["prompts"] == []
    assert "cursor" in result["platforms"]
    assert "claude-code" in result["platforms"]
    assert "registries" in result


def test_to_dict_returns_plain_dict() -> None:
    """to_dict() should return a plain dictionary, not a dataclass."""
    config = ProjectConfig.default()
    result = config.to_dict()

    assert isinstance(result, dict)
    assert set(result.keys()) == {"version", "registries", "prompts", "platforms"}
