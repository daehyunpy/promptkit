"""Tests for CleanArtifacts use case."""

from pathlib import Path

from promptkit.app.clean import CleanArtifacts
from promptkit.infra.builders.manifest import MANAGED_DIR, write_manifest

CACHE_DIR = ".promptkit/cache"


def _write_artifact(project_dir: Path, output_dir: str, relative: str) -> Path:
    """Write a dummy artifact file and return its path."""
    path = project_dir / output_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("generated content")
    return path


def _setup_manifest(project_dir: Path, platform: str, paths: list[str]) -> None:
    """Write a manifest file for a platform."""
    write_manifest(project_dir, platform, paths)


class TestCleanRemovesArtifacts:
    """Task 3.1: Clean removes files listed in manifests and deletes manifest files."""

    def test_removes_managed_files_and_manifests(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, ".cursor", "skills/foo.md")
        _write_artifact(tmp_path, ".claude", "skills/bar.md")
        _setup_manifest(tmp_path, "cursor", ["skills/foo.md"])
        _setup_manifest(tmp_path, "claude", ["skills/bar.md"])

        result = CleanArtifacts().execute(tmp_path)

        assert not (tmp_path / ".cursor" / "skills" / "foo.md").exists()
        assert not (tmp_path / ".claude" / "skills" / "bar.md").exists()
        assert not (tmp_path / MANAGED_DIR / "cursor.txt").exists()
        assert not (tmp_path / MANAGED_DIR / "claude.txt").exists()
        assert result.artifacts_removed

    def test_prunes_empty_parent_directories(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, ".cursor", "skills/foo.md")
        _setup_manifest(tmp_path, "cursor", ["skills/foo.md"])

        CleanArtifacts().execute(tmp_path)

        assert not (tmp_path / ".cursor" / "skills").exists()


class TestCleanNoOp:
    """Task 3.2: Clean is no-op when no manifests exist."""

    def test_no_manifests_present(self, tmp_path: Path) -> None:
        result = CleanArtifacts().execute(tmp_path)

        assert not result.artifacts_removed
        assert not result.cache_removed

    def test_managed_dir_missing(self, tmp_path: Path) -> None:
        result = CleanArtifacts().execute(tmp_path)

        assert not result.artifacts_removed


class TestCleanPreservesNonManaged:
    """Task 3.3: Clean preserves non-managed files in output directories."""

    def test_preserves_non_managed_files(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, ".cursor", "skills/foo.md")
        non_managed = _write_artifact(tmp_path, ".cursor", "settings.json")
        _setup_manifest(tmp_path, "cursor", ["skills/foo.md"])

        CleanArtifacts().execute(tmp_path)

        assert non_managed.exists()
        assert non_managed.read_text() == "generated content"


class TestCleanHandlesDeletedFiles:
    """Task 3.4: Clean handles already-deleted managed files gracefully."""

    def test_already_deleted_file(self, tmp_path: Path) -> None:
        _setup_manifest(tmp_path, "cursor", ["skills/gone.md"])

        result = CleanArtifacts().execute(tmp_path)

        assert result.artifacts_removed


class TestCleanCacheFlag:
    """Tasks 3.5-3.7: Cache removal behavior."""

    def test_cache_flag_removes_cache(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / CACHE_DIR
        cache_dir.mkdir(parents=True)
        (cache_dir / "plugins" / "reg" / "plugin" / "abc123").mkdir(parents=True)

        result = CleanArtifacts().execute(tmp_path, clean_cache=True)

        assert not cache_dir.exists()
        assert result.cache_removed

    def test_no_cache_flag_preserves_cache(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / CACHE_DIR
        cache_dir.mkdir(parents=True)

        result = CleanArtifacts().execute(tmp_path, clean_cache=False)

        assert cache_dir.exists()
        assert not result.cache_removed

    def test_cache_flag_when_cache_missing(self, tmp_path: Path) -> None:
        result = CleanArtifacts().execute(tmp_path, clean_cache=True)

        assert not result.cache_removed
