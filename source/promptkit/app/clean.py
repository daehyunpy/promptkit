"""Application layer: CleanArtifacts use case."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from promptkit.infra.builders.manifest import (
    MANAGED_DIR,
    cleanup_managed_files,
    read_manifest,
)

CACHE_DIR = ".promptkit/cache"

PLATFORM_OUTPUT_DIRS: dict[str, str] = {
    "cursor": ".cursor",
    "claude": ".claude",
}


@dataclass(frozen=True)
class CleanResult:
    artifacts_removed: bool
    cache_removed: bool


class CleanArtifacts:
    """Remove promptkit-managed build artifacts and optionally the plugin cache."""

    def execute(self, project_dir: Path, /, *, clean_cache: bool = False) -> CleanResult:
        """Remove managed artifacts and optionally the plugin cache."""
        artifacts_removed = self._clean_artifacts(project_dir)
        cache_removed = self._clean_cache(project_dir) if clean_cache else False
        return CleanResult(
            artifacts_removed=artifacts_removed,
            cache_removed=cache_removed,
        )

    def _clean_artifacts(self, project_dir: Path, /) -> bool:
        """Remove all managed build artifacts and their manifests."""
        managed_dir = project_dir / MANAGED_DIR
        if not managed_dir.is_dir():
            return False

        manifests = sorted(managed_dir.glob("*.txt"))
        if not manifests:
            return False

        for manifest_path in manifests:
            platform_name = manifest_path.stem
            output_dir_name = PLATFORM_OUTPUT_DIRS.get(platform_name, f".{platform_name}")
            output_dir = project_dir / output_dir_name

            paths = read_manifest(project_dir, platform_name)
            cleanup_managed_files(output_dir, paths)
            manifest_path.unlink()

        return True

    def _clean_cache(self, project_dir: Path, /) -> bool:
        """Remove the plugin cache directory."""
        cache_dir = project_dir / CACHE_DIR
        if not cache_dir.is_dir():
            return False
        shutil.rmtree(cache_dir)
        return True
