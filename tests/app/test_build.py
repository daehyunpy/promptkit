"""Tests for BuildArtifacts use case."""

import hashlib
from pathlib import Path

import pytest

from promptkit.app.build import BuildArtifacts
from promptkit.domain.errors import BuildError
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt import Prompt
from promptkit.domain.protocols import ArtifactBuilder
from promptkit.infra.builders.claude_builder import ClaudeBuilder
from promptkit.infra.builders.cursor_builder import CursorBuilder
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.file_system.local import FileSystem
from promptkit.infra.storage.prompt_cache import PromptCache

CONFIG_BOTH_PLATFORMS = """\
version: 1
prompts: []
platforms:
  cursor:
  claude-code:
"""

CONFIG_CURSOR_ONLY = """\
version: 1
prompts: []
platforms:
  cursor:
"""


class FakeBuilder:
    """Test double for ArtifactBuilder that records calls."""

    def __init__(self, platform: PlatformTarget) -> None:
        self._platform = platform
        self.built_prompts: list[Prompt] = []
        self.built_output_dir: Path | None = None

    @property
    def platform(self) -> PlatformTarget:
        return self._platform

    def build(self, prompts: list[Prompt], output_dir: Path, /) -> list[Path]:
        self.built_prompts = list(prompts)
        self.built_output_dir = output_dir
        return []


def _sha256(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode()).hexdigest()


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    (d / ".promptkit" / "cache").mkdir(parents=True)
    return d


def _make_build(
    project_dir: Path,
    builders: dict[PlatformTarget, ArtifactBuilder] | None = None,
) -> BuildArtifacts:
    fs = FileSystem()
    if builders is None:
        builders = {
            PlatformTarget.CURSOR: CursorBuilder(fs),
            PlatformTarget.CLAUDE_CODE: ClaudeBuilder(fs),
        }
    return BuildArtifacts(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
        prompt_cache=PromptCache(fs, project_dir / ".promptkit" / "cache"),
        builders=builders,
    )


def _write_lock(project_dir: Path, entries: list[dict[str, str]]) -> None:
    """Write a lock file with the given entries."""
    lines = ["version: 1\nprompts:\n"]
    for entry in entries:
        lines.append(f"  - name: {entry['name']}\n")
        lines.append(f"    source: {entry['source']}\n")
        lines.append(f"    hash: {entry['hash']}\n")
        lines.append("    fetched_at: '2026-02-09T12:00:00+00:00'\n")
    (project_dir / "promptkit.lock").write_text("".join(lines))


class TestLockFileRequired:
    def test_raises_build_error_when_lock_missing(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        use_case = _make_build(project_dir)

        with pytest.raises(BuildError, match="Lock file not found"):
            use_case.execute(project_dir)


class TestLoadLocalContent:
    def test_loads_local_prompt_from_prompts_dir(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        skills_dir = project_dir / "prompts" / "skills"
        skills_dir.mkdir()
        (skills_dir / "my-skill.md").write_text("# My Skill")
        _write_lock(project_dir, [
            {"name": "skills/my-skill", "source": "local/skills/my-skill",
             "hash": _sha256("# My Skill")},
        ])
        use_case = _make_build(project_dir)

        use_case.execute(project_dir)

        # Verify the artifact was built (in .cursor output)
        assert (project_dir / ".cursor" / "skills-cursor" / "my-skill.md").read_text() == "# My Skill"


class TestLoadCachedContent:
    def test_loads_remote_prompt_from_cache(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        content = "# Remote Prompt"
        content_hash = _sha256(content)
        # Store in cache
        cache = PromptCache(FileSystem(), project_dir / ".promptkit" / "cache")
        cache.store(content)
        _write_lock(project_dir, [
            {"name": "code-review", "source": "my-registry/code-review",
             "hash": content_hash},
        ])
        use_case = _make_build(project_dir)

        use_case.execute(project_dir)

        assert (project_dir / ".cursor" / "rules" / "code-review.md").read_text() == content

    def test_raises_build_error_when_cache_missing(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        _write_lock(project_dir, [
            {"name": "missing", "source": "registry/missing",
             "hash": "sha256:deadbeef"},
        ])
        use_case = _make_build(project_dir)

        with pytest.raises(BuildError, match="Cached content missing"):
            use_case.execute(project_dir)


class TestPlatformFiltering:
    def test_filters_prompts_by_platform(
        self, project_dir: Path
    ) -> None:
        # Config with both platforms, but prompt targets only cursor
        config = """\
version: 1
prompts:
  - source: my-registry/cursor-only
    platforms:
      - cursor
platforms:
  cursor:
  claude-code:
"""
        (project_dir / "promptkit.yaml").write_text(config)
        content = "# Cursor Only"
        cache = PromptCache(FileSystem(), project_dir / ".promptkit" / "cache")
        cache.store(content)
        _write_lock(project_dir, [
            {"name": "cursor-only", "source": "my-registry/cursor-only",
             "hash": _sha256(content)},
        ])

        cursor_builder = FakeBuilder(PlatformTarget.CURSOR)
        claude_builder = FakeBuilder(PlatformTarget.CLAUDE_CODE)
        use_case = _make_build(project_dir, {
            PlatformTarget.CURSOR: cursor_builder,
            PlatformTarget.CLAUDE_CODE: claude_builder,
        })

        use_case.execute(project_dir)

        assert len(cursor_builder.built_prompts) == 1
        assert len(claude_builder.built_prompts) == 0


class TestBuilderDelegation:
    def test_delegates_to_each_platform_builder(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        (project_dir / "prompts" / "my-rule.md").write_text("# Rule")
        _write_lock(project_dir, [
            {"name": "my-rule", "source": "local/my-rule",
             "hash": _sha256("# Rule")},
        ])

        cursor_builder = FakeBuilder(PlatformTarget.CURSOR)
        claude_builder = FakeBuilder(PlatformTarget.CLAUDE_CODE)
        use_case = _make_build(project_dir, {
            PlatformTarget.CURSOR: cursor_builder,
            PlatformTarget.CLAUDE_CODE: claude_builder,
        })

        use_case.execute(project_dir)

        assert len(cursor_builder.built_prompts) == 1
        assert len(claude_builder.built_prompts) == 1
        assert cursor_builder.built_output_dir == project_dir / ".cursor"
        assert claude_builder.built_output_dir == project_dir / ".claude"

    def test_builds_for_single_platform(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_CURSOR_ONLY)
        (project_dir / "prompts" / "my-rule.md").write_text("# Rule")
        _write_lock(project_dir, [
            {"name": "my-rule", "source": "local/my-rule",
             "hash": _sha256("# Rule")},
        ])

        cursor_builder = FakeBuilder(PlatformTarget.CURSOR)
        claude_builder = FakeBuilder(PlatformTarget.CLAUDE_CODE)
        use_case = _make_build(project_dir, {
            PlatformTarget.CURSOR: cursor_builder,
            PlatformTarget.CLAUDE_CODE: claude_builder,
        })

        use_case.execute(project_dir)

        assert len(cursor_builder.built_prompts) == 1
        assert len(claude_builder.built_prompts) == 0
