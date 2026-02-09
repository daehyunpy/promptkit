"""Infrastructure layer: Load promptkit.yaml into domain objects."""

from dataclasses import dataclass, field
from typing import Any

import yaml

from promptkit.domain.errors import ValidationError
from promptkit.domain.platform_config import PlatformConfig
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.domain.registry import Registry, RegistryType

DEFAULT_OUTPUT_DIRS: dict[PlatformTarget, str] = {
    PlatformTarget.CURSOR: ".cursor",
    PlatformTarget.CLAUDE_CODE: ".claude",
}

DEFAULT_PLATFORM_CONFIGS: list[PlatformConfig] = [
    PlatformConfig(
        name="cursor",
        platform_type=PlatformTarget.CURSOR,
        output_dir=".cursor",
    ),
    PlatformConfig(
        name="claude-code",
        platform_type=PlatformTarget.CLAUDE_CODE,
        output_dir=".claude",
    ),
]


@dataclass(frozen=True)
class LoadedConfig:
    """Result of loading and parsing a promptkit.yaml file."""

    version: int
    registries: list[Registry] = field(default_factory=list)
    prompt_specs: list[PromptSpec] = field(default_factory=list)
    platform_configs: list[PlatformConfig] = field(default_factory=list)


class YamlLoader:
    """Loads promptkit.yaml content into domain objects."""

    @staticmethod
    def load(yaml_content: str, /) -> LoadedConfig:
        """Parse YAML content into a LoadedConfig.

        Raises:
            ValidationError: If YAML is invalid or missing required fields.
        """
        raw = _parse_yaml(yaml_content)
        version = _extract_version(raw)
        registries = _extract_registries(raw)
        prompt_specs = _extract_prompt_specs(raw)
        platform_configs = _extract_platform_configs(raw)

        return LoadedConfig(
            version=version,
            registries=registries,
            prompt_specs=prompt_specs,
            platform_configs=platform_configs,
        )


def _parse_yaml(yaml_content: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise ValidationError("Config must be a YAML mapping, not a list or scalar")
    return data


def _extract_version(raw: dict[str, Any]) -> int:
    if "version" not in raw:
        raise ValidationError("Missing required field: 'version'")
    return int(raw["version"])


def _extract_registries(raw: dict[str, Any]) -> list[Registry]:
    registries_raw = raw.get("registries", {})
    if not registries_raw:
        return []

    registries: list[Registry] = []
    for name, value in registries_raw.items():
        registries.append(_parse_registry_entry(name, value))
    return registries


def _parse_registry_entry(name: str, value: Any) -> Registry:
    # Short form: key: <url>
    if isinstance(value, str):
        return Registry(
            name=name,
            url=value,
            registry_type=RegistryType.CLAUDE_MARKETPLACE,
        )

    # Object form: key: {type: ..., url: ...}
    if isinstance(value, dict):
        url = value.get("url", "")
        type_str = value.get("type")
        if type_str:
            try:
                registry_type = RegistryType.from_string(type_str)
            except ValueError as e:
                raise ValidationError(str(e)) from e
        else:
            registry_type = RegistryType.CLAUDE_MARKETPLACE

        return Registry(name=name, url=url, registry_type=registry_type)

    raise ValidationError(f"Invalid registry entry for '{name}'")


def _extract_prompt_specs(raw: dict[str, Any]) -> list[PromptSpec]:
    if "prompts" not in raw:
        raise ValidationError("Missing required field: 'prompts'")

    prompts_raw = raw["prompts"]
    if not prompts_raw:
        return []

    specs: list[PromptSpec] = []
    for entry in prompts_raw:
        specs.append(_parse_prompt_entry(entry))
    return specs


def _parse_prompt_entry(entry: Any) -> PromptSpec:
    # String form: "registry/name"
    if isinstance(entry, str):
        return PromptSpec(source=entry)

    # Object form: {source: ..., name: ..., platforms: ...}
    if isinstance(entry, dict):
        if "source" not in entry:
            raise ValidationError("Prompt entry missing required field: 'source'")

        platforms = _parse_platforms(entry.get("platforms", []))
        name = entry.get("name", "")

        return PromptSpec(
            source=entry["source"],
            name=name,
            platforms=tuple(platforms),
        )

    raise ValidationError(f"Invalid prompt entry: {entry}")


def _parse_platforms(platforms_raw: list[str] | None) -> list[PlatformTarget]:
    if not platforms_raw:
        return []
    platforms: list[PlatformTarget] = []
    for p in platforms_raw:
        try:
            platforms.append(PlatformTarget.from_string(p))
        except ValueError as e:
            raise ValidationError(str(e)) from e
    return platforms


def _extract_platform_configs(raw: dict[str, Any]) -> list[PlatformConfig]:
    platforms_raw = raw.get("platforms")
    if not platforms_raw:
        return list(DEFAULT_PLATFORM_CONFIGS)

    configs: list[PlatformConfig] = []
    for key, value in platforms_raw.items():
        configs.append(_parse_platform_entry(key, value))
    return configs


def _parse_platform_entry(key: str, value: Any) -> PlatformConfig:
    # Resolve platform type from key name
    try:
        platform_type = PlatformTarget.from_string(key)
    except ValueError as e:
        raise ValidationError(str(e)) from e

    default_output_dir = DEFAULT_OUTPUT_DIRS.get(platform_type, f".{key}")

    # Minimal form: key with no value (None)
    if value is None:
        return PlatformConfig(
            name=key,
            platform_type=platform_type,
            output_dir=default_output_dir,
        )

    # Short form: key: <output_dir>
    if isinstance(value, str):
        return PlatformConfig(
            name=key,
            platform_type=platform_type,
            output_dir=value,
        )

    # Object form: key: {type: ..., output_dir: ...}
    if isinstance(value, dict):
        type_str = value.get("type", key)
        try:
            resolved_type = PlatformTarget.from_string(type_str)
        except ValueError as e:
            raise ValidationError(str(e)) from e

        output_dir = value.get("output_dir", default_output_dir)
        return PlatformConfig(
            name=key,
            platform_type=resolved_type,
            output_dir=output_dir,
        )

    raise ValidationError(f"Invalid platform entry for '{key}'")
