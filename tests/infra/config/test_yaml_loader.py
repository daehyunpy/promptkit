"""Tests for YamlLoader - loads promptkit.yaml into domain objects."""

import pytest

from promptkit.domain.errors import ValidationError
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_spec import ArtifactType
from promptkit.infra.config.yaml_loader import YamlLoader


class TestYamlLoaderValidConfig:
    def test_loads_version(self) -> None:
        yaml_content = "version: 1\nprompts: []\n"
        config = YamlLoader.load(yaml_content)
        assert config.version == 1

    def test_loads_empty_prompts(self) -> None:
        yaml_content = "version: 1\nprompts: []\n"
        config = YamlLoader.load(yaml_content)
        assert config.prompt_specs == []

    def test_loads_single_prompt_spec(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer
    platforms:
      - cursor
      - claude-code
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.prompt_specs) == 1
        spec = config.prompt_specs[0]
        assert spec.name == "code-reviewer"
        assert spec.source == "anthropic/code-reviewer"
        assert PlatformTarget.CURSOR in spec.platforms
        assert PlatformTarget.CLAUDE_CODE in spec.platforms

    def test_loads_multiple_prompt_specs(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer
    platforms:
      - cursor
  - name: test-writer
    source: local/test-writer
    platforms:
      - claude-code
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.prompt_specs) == 2
        assert config.prompt_specs[0].name == "code-reviewer"
        assert config.prompt_specs[1].name == "test-writer"

    def test_loads_prompt_with_artifact_type(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer
    artifact_type: skill
    platforms:
      - cursor
"""
        config = YamlLoader.load(yaml_content)
        assert config.prompt_specs[0].artifact_type == ArtifactType.SKILL

    def test_loads_prompt_without_platforms(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer
"""
        config = YamlLoader.load(yaml_content)
        assert config.prompt_specs[0].platforms == ()

    def test_loads_platform_output_dirs(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: .cursor
  claude-code:
    output_dir: .claude
"""
        config = YamlLoader.load(yaml_content)
        assert config.platform_output_dirs[PlatformTarget.CURSOR] == ".cursor"
        assert config.platform_output_dirs[PlatformTarget.CLAUDE_CODE] == ".claude"

    def test_loads_default_output_dirs_when_missing(self) -> None:
        yaml_content = "version: 1\nprompts: []\n"
        config = YamlLoader.load(yaml_content)
        assert config.platform_output_dirs[PlatformTarget.CURSOR] == ".cursor"
        assert config.platform_output_dirs[PlatformTarget.CLAUDE_CODE] == ".claude"


class TestYamlLoaderInvalidConfig:
    def test_raises_on_invalid_yaml(self) -> None:
        with pytest.raises(ValidationError, match="Invalid YAML"):
            YamlLoader.load("{{invalid yaml:")

    def test_raises_on_missing_version(self) -> None:
        with pytest.raises(ValidationError, match="version"):
            YamlLoader.load("prompts: []\n")

    def test_raises_on_missing_prompts(self) -> None:
        with pytest.raises(ValidationError, match="prompts"):
            YamlLoader.load("version: 1\n")

    def test_raises_on_invalid_platform_in_prompt(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: test
    source: local/test
    platforms:
      - invalid-platform
"""
        with pytest.raises(ValidationError, match="Unknown platform"):
            YamlLoader.load(yaml_content)

    def test_raises_on_prompt_missing_name(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - source: local/test
"""
        with pytest.raises(ValidationError, match="name"):
            YamlLoader.load(yaml_content)

    def test_raises_on_prompt_missing_source(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: test
"""
        with pytest.raises(ValidationError, match="source"):
            YamlLoader.load(yaml_content)

    def test_raises_on_non_dict_yaml(self) -> None:
        with pytest.raises(ValidationError, match="mapping"):
            YamlLoader.load("- item1\n- item2\n")
