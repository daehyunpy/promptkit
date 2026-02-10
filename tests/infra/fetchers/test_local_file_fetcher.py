"""Tests for LocalFileFetcher."""

from pathlib import Path

import pytest

from promptkit.domain.errors import SyncError
from promptkit.domain.prompt_spec import PromptSpec
from promptkit.infra.fetchers.local_file_fetcher import LocalFileFetcher
from promptkit.infra.file_system.local import FileSystem


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir()
    return d


@pytest.fixture
def fetcher(prompts_dir: Path) -> LocalFileFetcher:
    return LocalFileFetcher(FileSystem(), prompts_dir)


class TestFetch:
    def test_fetch_reads_local_prompt(
        self, fetcher: LocalFileFetcher, prompts_dir: Path
    ) -> None:
        (prompts_dir / "my-rule.md").write_text("# My Rule\nContent")
        spec = PromptSpec(source="local/my-rule")

        prompt = fetcher.fetch(spec)

        assert prompt.name == "my-rule"
        assert prompt.content == "# My Rule\nContent"
        assert prompt.source == "local/my-rule"

    def test_fetch_reads_from_subdirectory(
        self, fetcher: LocalFileFetcher, prompts_dir: Path
    ) -> None:
        skills_dir = prompts_dir / "skills"
        skills_dir.mkdir()
        (skills_dir / "my-skill.md").write_text("# Skill")
        spec = PromptSpec(source="local/skills/my-skill")

        prompt = fetcher.fetch(spec)

        assert prompt.name == "skills/my-skill"
        assert prompt.content == "# Skill"

    def test_fetch_raises_for_missing_file(
        self, fetcher: LocalFileFetcher
    ) -> None:
        spec = PromptSpec(source="local/nonexistent")

        with pytest.raises(SyncError, match="nonexistent"):
            fetcher.fetch(spec)


class TestDiscover:
    def test_discover_flat_directory(
        self, fetcher: LocalFileFetcher, prompts_dir: Path
    ) -> None:
        (prompts_dir / "rule-a.md").write_text("A")
        (prompts_dir / "rule-b.md").write_text("B")

        specs = fetcher.discover()

        sources = sorted(s.source for s in specs)
        assert sources == ["local/rule-a", "local/rule-b"]

    def test_discover_subdirectories(
        self, fetcher: LocalFileFetcher, prompts_dir: Path
    ) -> None:
        skills_dir = prompts_dir / "skills"
        skills_dir.mkdir()
        (skills_dir / "code-review.md").write_text("Review")

        specs = fetcher.discover()

        assert len(specs) == 1
        assert specs[0].source == "local/skills/code-review"

    def test_discover_empty_directory(self, fetcher: LocalFileFetcher) -> None:
        specs = fetcher.discover()
        assert specs == []

    def test_discover_ignores_non_markdown(
        self, fetcher: LocalFileFetcher, prompts_dir: Path
    ) -> None:
        (prompts_dir / "notes.txt").write_text("text")
        (prompts_dir / "config.yaml").write_text("yaml: true")
        (prompts_dir / "valid.md").write_text("# Valid")

        specs = fetcher.discover()

        assert len(specs) == 1
        assert specs[0].source == "local/valid"

    def test_discover_missing_directory(self, tmp_path: Path) -> None:
        fetcher = LocalFileFetcher(FileSystem(), tmp_path / "nonexistent")

        specs = fetcher.discover()

        assert specs == []
