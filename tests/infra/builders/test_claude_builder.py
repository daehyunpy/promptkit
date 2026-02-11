"""Tests for ClaudeBuilder."""

from pathlib import Path

import pytest

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.builders.claude_builder import ClaudeBuilder
from promptkit.infra.file_system.local import FileSystem


@pytest.fixture
def source_dir(tmp_path: Path) -> Path:
    d = tmp_path / "source"
    d.mkdir()
    return d


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".claude"
    d.mkdir()
    return d


@pytest.fixture
def builder() -> ClaudeBuilder:
    return ClaudeBuilder(FileSystem())


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


class TestFileCopying:
    def test_copies_single_md_file(
        self, builder: ClaudeBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(source_dir, {"my-rule.md": "# Rule"})

        builder.build([plugin], output_dir)

        assert (output_dir / "my-rule.md").read_text() == "# Rule"

    def test_copies_multi_file_plugin(
        self, builder: ClaudeBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "agents/reviewer.md": "# Reviewer",
                "hooks/hooks.json": '{"hooks": []}',
                "scripts/check.sh": "#!/bin/bash",
            },
        )

        builder.build([plugin], output_dir)

        assert (output_dir / "agents" / "reviewer.md").read_text() == "# Reviewer"
        assert (output_dir / "hooks" / "hooks.json").read_text() == '{"hooks": []}'
        assert (output_dir / "scripts" / "check.sh").read_text() == "#!/bin/bash"

    def test_preserves_directory_structure(
        self, builder: ClaudeBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "skills/xlsx/SKILL.md": "# XLSX",
                "skills/xlsx/scripts/processor.py": "import xlsx",
            },
        )

        builder.build([plugin], output_dir)

        assert (output_dir / "skills" / "xlsx" / "SKILL.md").read_text() == "# XLSX"
        assert (
            output_dir / "skills" / "xlsx" / "scripts" / "processor.py"
        ).read_text() == "import xlsx"


class TestCleanBeforeWrite:
    def test_removes_stale_artifacts(
        self, builder: ClaudeBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        stale = output_dir / "old" / "stale.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale")

        plugin = _make_plugin(source_dir, {"new.md": "# New"})
        builder.build([plugin], output_dir)

        assert not stale.exists()
        assert (output_dir / "new.md").exists()


class TestReturnPaths:
    def test_returns_generated_paths(
        self, builder: ClaudeBuilder, source_dir: Path, output_dir: Path
    ) -> None:
        plugin = _make_plugin(
            source_dir,
            {
                "agents/a.md": "A",
                "skills/b/SKILL.md": "B",
            },
        )

        paths = builder.build([plugin], output_dir)

        assert len(paths) == 2
        assert output_dir / "agents" / "a.md" in paths
        assert output_dir / "skills" / "b" / "SKILL.md" in paths


class TestPlatformProperty:
    def test_platform_returns_claude_code(self, builder: ClaudeBuilder) -> None:
        assert builder.platform == PlatformTarget.CLAUDE_CODE
