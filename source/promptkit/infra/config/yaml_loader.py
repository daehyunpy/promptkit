"""Infrastructure layer: Load promptkit.yaml into domain objects."""

from dataclasses import dataclass, field
from typing import Any

import yaml

from promptkit.domain.errors import ValidationError
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt_spec import ArtifactType, PromptSpec

DEFAULT_OUTPUT_DIRS: dict[PlatformTarget, str] = {
    PlatformTarget.CURSOR: ".cursor",
    PlatformTarget.CLAUDE_CODE: ".claude",
}


@dataclass(frozen=True)
class LoadedConfig:
    """Result of loading and parsing a promptkit.yaml file."""

    version: int
    prompt_specs: list[PromptSpec] = field(default_factory=list)
    platform_output_dirs: dict[PlatformTarget, str] = field(default_factory=dict)


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
        prompt_specs = _extract_prompt_specs(raw)
        platform_output_dirs = _extract_platform_output_dirs(raw)

        return LoadedConfig(
            version=version,
            prompt_specs=prompt_specs,
            platform_output_dirs=platform_output_dirs,
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


def _parse_prompt_entry(entry: dict[str, Any]) -> PromptSpec:
    if "name" not in entry:
        raise ValidationError("Prompt entry missing required field: 'name'")
    if "source" not in entry:
        raise ValidationError("Prompt entry missing required field: 'source'")
    if "artifact_type" not in entry:
        raise ValidationError("Prompt entry missing required field: 'artifact_type'")

    platforms = _parse_platforms(entry.get("platforms", []))
    artifact_type = _parse_artifact_type(entry["artifact_type"])

    return PromptSpec(
        name=entry["name"],
        source=entry["source"],
        artifact_type=artifact_type,
        platforms=tuple(platforms),
    )


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


def _parse_artifact_type(value: str) -> ArtifactType:
    try:
        return ArtifactType.from_string(value)
    except ValueError as e:
        raise ValidationError(str(e)) from e


def _extract_platform_output_dirs(
    raw: dict[str, Any],
) -> dict[PlatformTarget, str]:
    result = dict(DEFAULT_OUTPUT_DIRS)

    platforms_raw = raw.get("platforms", {})
    if not platforms_raw:
        return result

    for key, config in platforms_raw.items():
        try:
            platform = PlatformTarget.from_string(key)
        except ValueError:
            continue
        if isinstance(config, dict) and "output_dir" in config:
            result[platform] = config["output_dir"]

    return result
