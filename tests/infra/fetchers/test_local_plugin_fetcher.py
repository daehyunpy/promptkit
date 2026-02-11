"""Tests for LocalPluginFetcher."""

from pathlib import Path

import pytest

from promptkit.domain.errors import SyncError
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.fetchers.local_plugin_fetcher import LocalPluginFetcher
from promptkit.infra.file_system.local import FileSystem


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir()
    return d


@pytest.fixture
def fetcher(prompts_dir: Path) -> LocalPluginFetcher:
    return LocalPluginFetcher(FileSystem(), prompts_dir)


class TestFetch:
    def test_fetch_single_md_file(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        (prompts_dir / "my-rule.md").write_text("# My Rule")
        spec = PromptSpec(source="local/my-rule")

        plugin = fetcher.fetch(spec)

        assert plugin.name == "my-rule"
        assert plugin.source == "local/my-rule"
        assert plugin.files == ("my-rule.md",)
        assert plugin.source_dir == prompts_dir
        assert plugin.commit_sha is None

    def test_fetch_directory_plugin(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        skill_dir = prompts_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "check.sh").write_text("#!/bin/bash")
        spec = PromptSpec(source="local/my-skill")

        plugin = fetcher.fetch(spec)

        assert plugin.files == ("my-skill/SKILL.md", "my-skill/scripts/check.sh")
        assert plugin.source_dir == prompts_dir
        assert plugin.commit_sha is None

    def test_fetch_from_category_subdirectory(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        skills_dir = prompts_dir / "skills"
        skills_dir.mkdir()
        (skills_dir / "my-skill.md").write_text("# Skill")
        spec = PromptSpec(source="local/skills/my-skill")

        plugin = fetcher.fetch(spec)

        assert plugin.files == ("skills/my-skill.md",)
        assert plugin.source_dir == prompts_dir

    def test_fetch_raises_for_missing_file(self, fetcher: LocalPluginFetcher) -> None:
        spec = PromptSpec(source="local/nonexistent")

        with pytest.raises(SyncError, match="nonexistent"):
            fetcher.fetch(spec)

    def test_fetch_directory_with_non_md_files(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        plugin_dir = prompts_dir / "my-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "agents").mkdir()
        (plugin_dir / "agents" / "reviewer.md").write_text("# Reviewer")
        (plugin_dir / "hooks").mkdir()
        (plugin_dir / "hooks" / "hooks.json").write_text('{"hooks": []}')
        spec = PromptSpec(source="local/my-plugin")

        plugin = fetcher.fetch(spec)

        assert sorted(plugin.files) == [
            "my-plugin/agents/reviewer.md",
            "my-plugin/hooks/hooks.json",
        ]


class TestDiscover:
    def test_discover_single_md_files(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        (prompts_dir / "rule-a.md").write_text("A")
        (prompts_dir / "rule-b.md").write_text("B")

        specs = fetcher.discover()

        sources = [s.source for s in specs]
        assert sources == ["local/rule-a", "local/rule-b"]

    def test_discover_directory_plugins(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        skill_dir = prompts_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("skill")

        specs = fetcher.discover()

        assert len(specs) == 1
        assert specs[0].source == "local/my-skill"

    def test_discover_mixed_files_and_directories(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        (prompts_dir / "my-rule.md").write_text("rule")
        skill_dir = prompts_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("skill")

        specs = fetcher.discover()

        sources = [s.source for s in specs]
        assert sources == ["local/my-rule", "local/my-skill"]

    def test_discover_category_subdirectories(
        self, fetcher: LocalPluginFetcher, prompts_dir: Path
    ) -> None:
        rules_dir = prompts_dir / "rules"
        rules_dir.mkdir()
        (rules_dir / "my-rule.md").write_text("rule")
        skills_dir = prompts_dir / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("skill")

        specs = fetcher.discover()

        sources = [s.source for s in specs]
        assert sources == ["local/rules/my-rule", "local/skills/my-skill"]

    def test_discover_empty_directory(self, fetcher: LocalPluginFetcher) -> None:
        specs = fetcher.discover()
        assert specs == []

    def test_discover_missing_directory(self, tmp_path: Path) -> None:
        fetcher = LocalPluginFetcher(FileSystem(), tmp_path / "nonexistent")

        specs = fetcher.discover()

        assert specs == []
