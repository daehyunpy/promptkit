"""Tests for CursorBuilder."""

from pathlib import Path

import pytest

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.builders.cursor_builder import CursorBuilder
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
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "skills/my-skill/SKILL.md": "# Skill",
            },
        )

        builder.build([plugin], output_dir)

        assert (
            output_dir / "skills-cursor" / "my-skill" / "SKILL.md"
        ).read_text() == "# Skill"

    def test_preserves_rules(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(source_dir, {"rules/my-rule.md": "# Rule"})

        builder.build([plugin], output_dir)

        assert (output_dir / "rules" / "my-rule.md").read_text() == "# Rule"

    def test_passes_through_unknown_categories(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(source_dir, {"scripts/check.sh": "#!/bin/bash"})

        builder.build([plugin], output_dir)

        assert (output_dir / "scripts" / "check.sh").read_text() == "#!/bin/bash"


class TestCategoryFiltering:
    def test_skips_agents(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "agents/reviewer.md": "# Agent",
                "rules/my-rule.md": "# Rule",
            },
        )

        builder.build([plugin], output_dir)

        assert not (output_dir / "agents").exists()
        assert (output_dir / "rules" / "my-rule.md").exists()

    def test_skips_commands(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "commands/my-cmd.md": "# Command",
                "rules/my-rule.md": "# Rule",
            },
        )

        builder.build([plugin], output_dir)

        assert not (output_dir / "commands").exists()
        assert (output_dir / "rules" / "my-rule.md").exists()

    def test_skips_hooks(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "hooks/hooks.json": "{}",
                "rules/my-rule.md": "# Rule",
            },
        )

        builder.build([plugin], output_dir)

        assert not (output_dir / "hooks").exists()
        assert (output_dir / "rules" / "my-rule.md").exists()


class TestCleanBeforeWrite:
    def test_removes_stale_artifacts(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        stale = output_dir / "old" / "stale.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale")

        plugin = _make_plugin(source_dir, {"rules/new.md": "# New"})
        builder.build([plugin], output_dir)

        assert not stale.exists()
        assert (output_dir / "rules" / "new.md").exists()


class TestReturnPaths:
    def test_returns_only_copied_paths(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "rules/a.md": "A",
                "agents/b.md": "B",  # skipped
                "skills/c/SKILL.md": "C",
            },
        )

        paths = builder.build([plugin], output_dir)

        assert len(paths) == 2
        assert output_dir / "rules" / "a.md" in paths
        assert output_dir / "skills-cursor" / "c" / "SKILL.md" in paths


class TestFlatFiles:
    def test_copies_flat_files_directly(
        self, builder: CursorBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(source_dir, {"my-rule.md": "# Rule"})

        builder.build([plugin], output_dir)

        assert (output_dir / "my-rule.md").read_text() == "# Rule"


class TestPlatformProperty:
    def test_platform_returns_cursor(self, builder: CursorBuilder) -> None:
        assert builder.platform == PlatformTarget.CURSOR
