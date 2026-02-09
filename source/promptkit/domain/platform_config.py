"""Domain layer: PlatformConfig value object."""

from dataclasses import dataclass

from promptkit.domain.platform_target import PlatformTarget


@dataclass(frozen=True)
class PlatformConfig:
    """Immutable platform configuration from promptkit.yaml.

    Declares a build target. The platform_type determines which
    ArtifactBuilder implementation to use.
    """

    name: str
    platform_type: PlatformTarget
    output_dir: str
