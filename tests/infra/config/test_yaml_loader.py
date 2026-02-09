"""Tests for YamlLoader - loads promptkit.yaml into domain objects."""

import pytest

from promptkit.domain.errors import ValidationError
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.registry import RegistryType
from promptkit.infra.config.yaml_loader import YamlLoader


MINIMAL_CONFIG = """\
version: 1
prompts: []
"""


class TestYamlLoaderVersion:
    def test_loads_version(self) -> None:
        config = YamlLoader.load(MINIMAL_CONFIG)
        assert config.version == 1


class TestYamlLoaderRegistries:
    def test_loads_registry_object_form(self) -> None:
        yaml_content = """\
version: 1
registries:
  anthropic-agent-skills:
    type: claude-marketplace
    url: https://github.com/anthropics/skills
prompts: []
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.registries) == 1
        reg = config.registries[0]
        assert reg.name == "anthropic-agent-skills"
        assert reg.registry_type == RegistryType.CLAUDE_MARKETPLACE
        assert reg.url == "https://github.com/anthropics/skills"

    def test_loads_registry_short_form(self) -> None:
        yaml_content = """\
version: 1
registries:
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts: []
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.registries) == 1
        reg = config.registries[0]
        assert reg.name == "claude-plugins-official"
        assert reg.registry_type == RegistryType.CLAUDE_MARKETPLACE
        assert reg.url == "https://github.com/anthropics/claude-plugins-official"

    def test_registry_type_defaults_to_claude_marketplace(self) -> None:
        yaml_content = """\
version: 1
registries:
  anthropic-agent-skills:
    url: https://github.com/anthropics/skills
prompts: []
"""
        config = YamlLoader.load(yaml_content)
        assert config.registries[0].registry_type == RegistryType.CLAUDE_MARKETPLACE

    def test_loads_multiple_registries(self) -> None:
        yaml_content = """\
version: 1
registries:
  anthropic-agent-skills:
    url: https://github.com/anthropics/skills
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts: []
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.registries) == 2
        names = {r.name for r in config.registries}
        assert names == {"anthropic-agent-skills", "claude-plugins-official"}

    def test_empty_registries_when_missing(self) -> None:
        config = YamlLoader.load(MINIMAL_CONFIG)
        assert config.registries == []


class TestYamlLoaderPrompts:
    def test_loads_string_form_prompt(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - claude-plugins-official/code-review
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.prompt_specs) == 1
        spec = config.prompt_specs[0]
        assert spec.source == "claude-plugins-official/code-review"
        assert spec.name == "code-review"
        assert spec.platforms == ()

    def test_loads_object_form_prompt(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - source: claude-plugins-official/code-review
    name: my-reviewer
    platforms:
      - cursor
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.prompt_specs) == 1
        spec = config.prompt_specs[0]
        assert spec.source == "claude-plugins-official/code-review"
        assert spec.name == "my-reviewer"
        assert PlatformTarget.CURSOR in spec.platforms

    def test_object_form_name_defaults_to_source_name(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - source: claude-plugins-official/code-review
"""
        config = YamlLoader.load(yaml_content)
        assert config.prompt_specs[0].name == "code-review"

    def test_loads_prompt_without_platforms(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - source: claude-plugins-official/code-review
"""
        config = YamlLoader.load(yaml_content)
        assert config.prompt_specs[0].platforms == ()

    def test_loads_multiple_prompts_mixed_forms(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - claude-plugins-official/code-review
  - source: anthropic-agent-skills/feature-dev
    name: my-feature
    platforms:
      - claude-code
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.prompt_specs) == 2
        assert config.prompt_specs[0].name == "code-review"
        assert config.prompt_specs[1].name == "my-feature"
        assert PlatformTarget.CLAUDE_CODE in config.prompt_specs[1].platforms

    def test_loads_empty_prompts(self) -> None:
        config = YamlLoader.load(MINIMAL_CONFIG)
        assert config.prompt_specs == []


class TestYamlLoaderPlatforms:
    def test_loads_platform_object_form(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  cursor:
    type: cursor
    output_dir: .cursor
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.platform_configs) == 1
        pc = config.platform_configs[0]
        assert pc.name == "cursor"
        assert pc.platform_type == PlatformTarget.CURSOR
        assert pc.output_dir == ".cursor"

    def test_loads_platform_short_form(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  claude-code: .claude
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.platform_configs) == 1
        pc = config.platform_configs[0]
        assert pc.name == "claude-code"
        assert pc.platform_type == PlatformTarget.CLAUDE_CODE
        assert pc.output_dir == ".claude"

    def test_loads_platform_minimal_form(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  cursor:
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.platform_configs) == 1
        pc = config.platform_configs[0]
        assert pc.name == "cursor"
        assert pc.platform_type == PlatformTarget.CURSOR
        assert pc.output_dir == ".cursor"

    def test_platform_type_defaults_to_key_name(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: /custom/cursor
"""
        config = YamlLoader.load(yaml_content)
        assert config.platform_configs[0].platform_type == PlatformTarget.CURSOR

    def test_platform_output_dir_defaults_per_type(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  cursor:
  claude-code:
"""
        config = YamlLoader.load(yaml_content)
        dirs = {pc.name: pc.output_dir for pc in config.platform_configs}
        assert dirs["cursor"] == ".cursor"
        assert dirs["claude-code"] == ".claude"

    def test_loads_default_platforms_when_missing(self) -> None:
        config = YamlLoader.load(MINIMAL_CONFIG)
        assert len(config.platform_configs) == 2
        names = {pc.name for pc in config.platform_configs}
        assert names == {"cursor", "claude-code"}

    def test_loads_multiple_platforms(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  cursor:
    output_dir: .cursor
  claude-code: .claude
"""
        config = YamlLoader.load(yaml_content)
        assert len(config.platform_configs) == 2


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
  - source: claude-plugins-official/test
    platforms:
      - invalid-platform
"""
        with pytest.raises(ValidationError, match="Unknown platform"):
            YamlLoader.load(yaml_content)

    def test_raises_on_prompt_missing_source_in_object_form(self) -> None:
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

    def test_raises_on_invalid_platform_key(self) -> None:
        yaml_content = """\
version: 1
prompts: []
platforms:
  invalid-platform:
    output_dir: .invalid
"""
        with pytest.raises(ValidationError, match="Unknown platform"):
            YamlLoader.load(yaml_content)
