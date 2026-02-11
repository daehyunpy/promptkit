"""Tests for CursorBuilder."""

from pathlib import Path

import pytest

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.builders.cursor_builder import CursorBuilder
from promptkit.infra.builders.manifest import MANAGED_DIR, read_manifest
from promptkit.infra.file_system.local import FileSystem


@pytest.fixture
def source_dir(tmp_path: Path) -> Path:
    d = tmp_path / "source"
    d.mkdir()
    return d


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".cursor"
    d.mkdir()
    return d


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def builder() -> CursorBuilder:
    return CursorBuilder(FileSystem())


def _make_plugin(
    source_dir: Path,
    files: dict[str, str],
    source: str = "local/test",
) -> Plugin:
    """Create a Plugin with actual files on disk."""
    for path, content in files.items():
        full = source_dir / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
    return Plugin(
        spec=PromptSpec(source=source),
        files=tuple(files.keys()),
        source_dir=source_dir,
    )


class TestDirectoryMapping:
    def test_maps_skills_to_skills_cursor(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "skills/my-skill/SKILL.md": "# Skill",
            },
        )

        builder.build([plugin], output_dir, project_dir)

        assert (
            output_dir / "skills-cursor" / "my-skill" / "SKILL.md"
        ).read_text() == "# Skill"

    def test_preserves_rules(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        plugin = _make_plugin(source_dir, {"rules/my-rule.md": "# Rule"})

        builder.build([plugin], output_dir, project_dir)

        assert (output_dir / "rules" / "my-rule.md").read_text() == "# Rule"

    def test_passes_through_scripts_without_mapping(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        plugin = _make_plugin(source_dir, {"scripts/check.sh": "#!/bin/bash"})

        builder.build([plugin], output_dir, project_dir)

        assert (output_dir / "scripts" / "check.sh").read_text() == "#!/bin/bash"


class TestCategoryFiltering:
    def test_only_copies_allowed_categories(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "skills/my-skill/SKILL.md": "# Skill",
                "rules/my-rule.md": "# Rule",
                "scripts/check.sh": "#!/bin/bash",
                "agents/reviewer.md": "# Agent",
                "commands/my-cmd.md": "# Command",
                "hooks/hooks.json": "{}",
                "README.md": "# Readme",
                ".claude-plugin/plugin.json": '{}',
            },
        )

        builder.build([plugin], output_dir, project_dir)

        assert (output_dir / "skills-cursor" / "my-skill" / "SKILL.md").exists()
        assert (output_dir / "rules" / "my-rule.md").exists()
        assert (output_dir / "scripts" / "check.sh").exists()
        assert (output_dir / "agents" / "reviewer.md").exists()
        assert (output_dir / "commands" / "my-cmd.md").exists()
        assert (output_dir / "hooks" / "hooks.json").exists()
        assert not (output_dir / "README.md").exists()
        assert not (output_dir / ".claude-plugin").exists()


class TestManifestCleanup:
    def test_removes_stale_managed_files(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        """Previously managed files are removed on rebuild."""
        stale = output_dir / "old" / "stale.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale")

        (project_dir / MANAGED_DIR).mkdir(parents=True)
        (project_dir / MANAGED_DIR / "cursor.txt").write_text("old/stale.md\n")

        plugin = _make_plugin(source_dir, {"rules/new.md": "# New"})
        builder.build([plugin], output_dir, project_dir)

        assert not stale.exists()
        assert (output_dir / "rules" / "new.md").exists()

    def test_preserves_non_managed_files(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        """Files not in the manifest survive a rebuild."""
        (output_dir / "settings.json").write_text("{}")

        plugin = _make_plugin(source_dir, {"rules/my-rule.md": "# Rule"})
        builder.build([plugin], output_dir, project_dir)

        assert (output_dir / "settings.json").read_text() == "{}"
        assert (output_dir / "rules" / "my-rule.md").exists()

    def test_first_build_without_manifest_is_additive(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        """First build creates manifest without removing anything."""
        (output_dir / "existing.md").write_text("existing")

        plugin = _make_plugin(source_dir, {"rules/new.md": "# New"})
        builder.build([plugin], output_dir, project_dir)

        assert (output_dir / "existing.md").read_text() == "existing"
        assert (output_dir / "rules" / "new.md").exists()
        assert read_manifest(project_dir, "cursor") == ["rules/new.md"]

    def test_skips_flat_files(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        """Files not under a category directory are skipped."""
        plugin = _make_plugin(
            source_dir, {"my-rule.md": "# Rule", "rules/real.md": "# Real"}
        )

        builder.build([plugin], output_dir, project_dir)

        assert not (output_dir / "my-rule.md").exists()
        assert (output_dir / "rules" / "real.md").exists()

    def test_manifest_records_mapped_paths(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        """Manifest should contain mapped paths (skills-cursor), not source paths."""
        plugin = _make_plugin(source_dir, {"skills/my-skill/SKILL.md": "# Skill"})
        builder.build([plugin], output_dir, project_dir)

        manifest = read_manifest(project_dir, "cursor")
        assert "skills-cursor/my-skill/SKILL.md" in manifest


class TestReturnPaths:
    def test_returns_only_copied_paths(
        self,
        builder: CursorBuilder,
        source_dir: Path,
        output_dir: Path,
        project_dir: Path,
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "rules/a.md": "A",
                "agents/b.md": "B",
                "skills/c/SKILL.md": "C",
                "README.md": "skip",  # skipped
            },
        )

        paths = builder.build([plugin], output_dir, project_dir)

        assert len(paths) == 3
        assert output_dir / "rules" / "a.md" in paths
        assert output_dir / "agents" / "b.md" in paths
        assert output_dir / "skills-cursor" / "c" / "SKILL.md" in paths




class TestPlatformProperty:
    def test_platform_returns_cursor(self, builder: CursorBuilder) -> None:
        assert builder.platform == PlatformTarget.CURSOR
