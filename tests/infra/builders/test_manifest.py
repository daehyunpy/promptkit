"""Tests for manifest read/write/cleanup helpers."""

from pathlib import Path

import pytest

from promptkit.infra.builders.manifest import (
    MANAGED_DIR,
    MANIFEST_HEADER,
    cleanup_managed_files,
    read_manifest,
    write_manifest,
)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    return d


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


class TestReadManifest:
    def test_returns_empty_list_when_no_manifest(self, project_dir: Path) -> None:
        result = read_manifest(project_dir, "claude")

        assert result == []

    def test_reads_existing_manifest(self, project_dir: Path) -> None:
        manifest_path = project_dir / MANAGED_DIR / "claude.txt"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(f"{MANIFEST_HEADER}\nagents/a.md\nrules/b.md\n")

        result = read_manifest(project_dir, "claude")

        assert result == ["agents/a.md", "rules/b.md"]

    def test_skips_comment_lines(self, project_dir: Path) -> None:
        manifest_path = project_dir / MANAGED_DIR / "cursor.txt"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text("# comment\nrules/a.md\n# another\nrules/b.md\n")

        result = read_manifest(project_dir, "cursor")

        assert result == ["rules/a.md", "rules/b.md"]

    def test_skips_blank_lines(self, project_dir: Path) -> None:
        manifest_path = project_dir / MANAGED_DIR / "claude.txt"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text("a.md\n\nb.md\n\n")

        result = read_manifest(project_dir, "claude")

        assert result == ["a.md", "b.md"]


class TestWriteManifest:
    def test_writes_sorted_paths_with_header(self, project_dir: Path) -> None:
        write_manifest(project_dir, "claude", ["rules/b.md", "agents/a.md"])

        manifest_path = project_dir / MANAGED_DIR / "claude.txt"
        assert manifest_path.exists()
        lines = manifest_path.read_text().splitlines()
        assert lines[0] == MANIFEST_HEADER
        assert "agents/a.md" in lines
        assert "rules/b.md" in lines
        assert lines.index("agents/a.md") < lines.index("rules/b.md")

    def test_creates_managed_directory(self, project_dir: Path) -> None:
        write_manifest(project_dir, "cursor", ["a.md"])

        assert (project_dir / MANAGED_DIR / "cursor.txt").exists()

    def test_overwrites_existing_manifest(self, project_dir: Path) -> None:
        write_manifest(project_dir, "claude", ["old.md"])
        write_manifest(project_dir, "claude", ["new.md"])

        result = read_manifest(project_dir, "claude")
        assert result == ["new.md"]


class TestCleanupManagedFiles:
    def test_removes_listed_files(self, output_dir: Path) -> None:
        (output_dir / "a.md").write_text("a")
        (output_dir / "b.md").write_text("b")

        cleanup_managed_files(output_dir, ["a.md", "b.md"])

        assert not (output_dir / "a.md").exists()
        assert not (output_dir / "b.md").exists()

    def test_preserves_non_managed_files(self, output_dir: Path) -> None:
        (output_dir / "managed.md").write_text("managed")
        (output_dir / "settings.json").write_text("{}")

        cleanup_managed_files(output_dir, ["managed.md"])

        assert not (output_dir / "managed.md").exists()
        assert (output_dir / "settings.json").read_text() == "{}"

    def test_removes_empty_parent_directories(self, output_dir: Path) -> None:
        (output_dir / "agents").mkdir()
        (output_dir / "agents" / "a.md").write_text("a")

        cleanup_managed_files(output_dir, ["agents/a.md"])

        assert not (output_dir / "agents").exists()

    def test_preserves_non_empty_parent_directories(self, output_dir: Path) -> None:
        (output_dir / "rules").mkdir()
        (output_dir / "rules" / "managed.md").write_text("managed")
        (output_dir / "rules" / "custom.md").write_text("custom")

        cleanup_managed_files(output_dir, ["rules/managed.md"])

        assert not (output_dir / "rules" / "managed.md").exists()
        assert (output_dir / "rules" / "custom.md").read_text() == "custom"

    def test_ignores_missing_files(self, output_dir: Path) -> None:
        cleanup_managed_files(output_dir, ["nonexistent.md"])
        # No error raised

    def test_removes_nested_empty_directories(self, output_dir: Path) -> None:
        (output_dir / "skills" / "xlsx" / "scripts").mkdir(parents=True)
        (output_dir / "skills" / "xlsx" / "scripts" / "run.sh").write_text(
            "#!/bin/bash"
        )

        cleanup_managed_files(output_dir, ["skills/xlsx/scripts/run.sh"])

        assert not (output_dir / "skills").exists()

    def test_empty_manifest_does_nothing(self, output_dir: Path) -> None:
        (output_dir / "keep.md").write_text("keep")

        cleanup_managed_files(output_dir, [])

        assert (output_dir / "keep.md").exists()
