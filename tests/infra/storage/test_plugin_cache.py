"""Tests for PluginCache directory-based storage."""

from pathlib import Path

from promptkit.infra.storage.plugin_cache import PluginCache


class TestPluginCacheHas:
    def test_returns_false_when_not_cached(self, tmp_path: Path) -> None:
        cache = PluginCache(tmp_path)
        assert cache.has("my-registry", "my-plugin", "abc123") is False

    def test_returns_true_when_cached(self, tmp_path: Path) -> None:
        cache = PluginCache(tmp_path)
        # Manually create the cache directory
        cache_dir = tmp_path / "my-registry" / "my-plugin" / "abc123"
        cache_dir.mkdir(parents=True)
        (cache_dir / "agents" / "reviewer.md").parent.mkdir(parents=True)
        (cache_dir / "agents" / "reviewer.md").write_text("content")
        assert cache.has("my-registry", "my-plugin", "abc123") is True


class TestPluginCachePluginDir:
    def test_returns_correct_path(self, tmp_path: Path) -> None:
        cache = PluginCache(tmp_path)
        result = cache.plugin_dir("my-registry", "my-plugin", "abc123")
        assert result == tmp_path / "my-registry" / "my-plugin" / "abc123"


class TestPluginCacheListFiles:
    def test_lists_all_files_recursively(self, tmp_path: Path) -> None:
        cache = PluginCache(tmp_path)
        cache_dir = tmp_path / "my-registry" / "my-plugin" / "abc123"
        cache_dir.mkdir(parents=True)
        (cache_dir / "agents").mkdir()
        (cache_dir / "agents" / "reviewer.md").write_text("content")
        (cache_dir / "hooks").mkdir()
        (cache_dir / "hooks" / "hooks.json").write_text("{}")

        files = cache.list_files("my-registry", "my-plugin", "abc123")
        assert sorted(files) == ["agents/reviewer.md", "hooks/hooks.json"]

    def test_returns_empty_list_when_not_cached(self, tmp_path: Path) -> None:
        cache = PluginCache(tmp_path)
        files = cache.list_files("no-registry", "no-plugin", "no-sha")
        assert files == []

    def test_handles_nested_directories(self, tmp_path: Path) -> None:
        cache = PluginCache(tmp_path)
        cache_dir = tmp_path / "reg" / "plugin" / "sha"
        cache_dir.mkdir(parents=True)
        (cache_dir / "skills" / "xlsx" / "scripts").mkdir(parents=True)
        (cache_dir / "skills" / "xlsx" / "SKILL.md").write_text("skill")
        (cache_dir / "skills" / "xlsx" / "scripts" / "processor.py").write_text("py")

        files = cache.list_files("reg", "plugin", "sha")
        assert sorted(files) == [
            "skills/xlsx/SKILL.md",
            "skills/xlsx/scripts/processor.py",
        ]
