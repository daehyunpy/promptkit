"""Tests for BuildArtifacts use case."""

from pathlib import Path

import pytest

from promptkit.app.build import BuildArtifacts
from promptkit.domain.errors import BuildError
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.plugin import Plugin
from promptkit.domain.protocols import ArtifactBuilder
from promptkit.infra.builders.claude_builder import ClaudeBuilder
from promptkit.infra.builders.cursor_builder import CursorBuilder
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.file_system.local import FileSystem
from promptkit.infra.storage.plugin_cache import PluginCache

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
        self.built_plugins: list[Plugin] = []
        self.built_output_dir: Path | None = None

    @property
    def platform(self) -> PlatformTarget:
        return self._platform

    def build(
        self, plugins: list[Plugin], output_dir: Path, project_dir: Path, /
    ) -> list[Path]:
        self.built_plugins = list(plugins)
        self.built_output_dir = output_dir
        return []


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    (d / "prompts").mkdir()
    (d / ".promptkit" / "cache" / "plugins").mkdir(parents=True)
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
        plugin_cache=PluginCache(project_dir / ".promptkit" / "cache" / "plugins"),
        builders=builders,
    )


def _write_lock(project_dir: Path, entries: list[dict[str, str]]) -> None:
    """Write a lock file with the given entries."""
    lines = ["version: 1\nprompts:\n"]
    for entry in entries:
        lines.append(f"  - name: {entry['name']}\n")
        lines.append(f"    source: {entry['source']}\n")
        lines.append(f"    hash: '{entry['hash']}'\n")
        lines.append("    fetched_at: '2026-02-09T12:00:00+00:00'\n")
        if "commit_sha" in entry:
            lines.append(f"    commit_sha: {entry['commit_sha']}\n")
    (project_dir / "promptkit.lock").write_text("".join(lines))


class TestLockFileRequired:
    def test_raises_build_error_when_lock_missing(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        use_case = _make_build(project_dir)

        with pytest.raises(BuildError, match="Lock file not found"):
            use_case.execute(project_dir)


class TestBuildLocalPlugin:
    def test_builds_local_single_file(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        (project_dir / "prompts" / "my-rule.md").write_text("# My Rule")
        _write_lock(
            project_dir,
            [
                {"name": "my-rule", "source": "local/my-rule", "hash": "sha256:abc"},
            ],
        )
        use_case = _make_build(project_dir)

        use_case.execute(project_dir)

        assert (project_dir / ".claude" / "my-rule.md").read_text() == "# My Rule"

    def test_builds_local_directory_plugin(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        skill_dir = project_dir / "prompts" / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "check.sh").write_text("#!/bin/bash")
        _write_lock(
            project_dir,
            [
                {"name": "my-skill", "source": "local/my-skill", "hash": "sha256:abc"},
            ],
        )
        use_case = _make_build(project_dir)

        use_case.execute(project_dir)

        assert (
            project_dir / ".claude" / "my-skill" / "SKILL.md"
        ).read_text() == "# Skill"
        assert (
            project_dir / ".claude" / "my-skill" / "scripts" / "check.sh"
        ).read_text() == "#!/bin/bash"


class TestBuildRegistryPlugin:
    def test_builds_from_cache(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        # Set up cached registry plugin
        cache_dir = (
            project_dir
            / ".promptkit"
            / "cache"
            / "plugins"
            / "my-registry"
            / "code-review"
            / "sha123"
        )
        cache_dir.mkdir(parents=True)
        (cache_dir / "agents").mkdir()
        (cache_dir / "agents" / "reviewer.md").write_text("# Reviewer")
        _write_lock(
            project_dir,
            [
                {
                    "name": "code-review",
                    "source": "my-registry/code-review",
                    "hash": "",
                    "commit_sha": "sha123",
                },
            ],
        )
        use_case = _make_build(project_dir)

        use_case.execute(project_dir)

        assert (
            project_dir / ".claude" / "agents" / "reviewer.md"
        ).read_text() == "# Reviewer"

    def test_raises_when_cache_missing(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        _write_lock(
            project_dir,
            [
                {
                    "name": "missing",
                    "source": "registry/missing",
                    "hash": "",
                    "commit_sha": "deadbeef",
                },
            ],
        )
        use_case = _make_build(project_dir)

        with pytest.raises(BuildError, match="Cached plugin missing"):
            use_case.execute(project_dir)


class TestPlatformFiltering:
    def test_filters_plugins_by_platform(self, project_dir: Path) -> None:
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
        # Set up cached plugin
        cache_dir = (
            project_dir
            / ".promptkit"
            / "cache"
            / "plugins"
            / "my-registry"
            / "cursor-only"
            / "sha1"
        )
        cache_dir.mkdir(parents=True)
        (cache_dir / "rules").mkdir()
        (cache_dir / "rules" / "rule.md").write_text("# Rule")
        _write_lock(
            project_dir,
            [
                {
                    "name": "cursor-only",
                    "source": "my-registry/cursor-only",
                    "hash": "",
                    "commit_sha": "sha1",
                },
            ],
        )

        cursor_builder = FakeBuilder(PlatformTarget.CURSOR)
        claude_builder = FakeBuilder(PlatformTarget.CLAUDE_CODE)
        use_case = _make_build(
            project_dir,
            {
                PlatformTarget.CURSOR: cursor_builder,
                PlatformTarget.CLAUDE_CODE: claude_builder,
            },
        )

        use_case.execute(project_dir)

        assert len(cursor_builder.built_plugins) == 1
        assert len(claude_builder.built_plugins) == 0


class TestBuilderDelegation:
    def test_delegates_to_each_platform_builder(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_BOTH_PLATFORMS)
        (project_dir / "prompts" / "my-rule.md").write_text("# Rule")
        _write_lock(
            project_dir,
            [
                {"name": "my-rule", "source": "local/my-rule", "hash": "sha256:abc"},
            ],
        )

        cursor_builder = FakeBuilder(PlatformTarget.CURSOR)
        claude_builder = FakeBuilder(PlatformTarget.CLAUDE_CODE)
        use_case = _make_build(
            project_dir,
            {
                PlatformTarget.CURSOR: cursor_builder,
                PlatformTarget.CLAUDE_CODE: claude_builder,
            },
        )

        use_case.execute(project_dir)

        assert len(cursor_builder.built_plugins) == 1
        assert len(claude_builder.built_plugins) == 1
        assert cursor_builder.built_output_dir == project_dir / ".cursor"
        assert claude_builder.built_output_dir == project_dir / ".claude"

    def test_builds_for_single_platform(self, project_dir: Path) -> None:
        (project_dir / "promptkit.yaml").write_text(CONFIG_CURSOR_ONLY)
        (project_dir / "prompts" / "my-rule.md").write_text("# Rule")
        _write_lock(
            project_dir,
            [
                {"name": "my-rule", "source": "local/my-rule", "hash": "sha256:abc"},
            ],
        )

        cursor_builder = FakeBuilder(PlatformTarget.CURSOR)
        claude_builder = FakeBuilder(PlatformTarget.CLAUDE_CODE)
        use_case = _make_build(
            project_dir,
            {
                PlatformTarget.CURSOR: cursor_builder,
                PlatformTarget.CLAUDE_CODE: claude_builder,
            },
        )

        use_case.execute(project_dir)

        assert len(cursor_builder.built_plugins) == 1
        assert len(claude_builder.built_plugins) == 0
