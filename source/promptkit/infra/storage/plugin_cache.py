"""Infrastructure layer: Directory-based plugin cache for registry plugins."""

from pathlib import Path


class PluginCache:
    """Directory-based cache for registry plugin file trees.

    Cache structure: {cache_dir}/{registry}/{plugin}/{commit_sha}/
    Fetchers write directly to the directory returned by plugin_dir().
    This class provides path resolution and existence checks.
    """

    def __init__(self, cache_dir: Path, /) -> None:
        self._cache_dir = cache_dir

    def has(self, registry: str, plugin: str, sha: str, /) -> bool:
        """Check if a plugin version is cached."""
        return self.plugin_dir(registry, plugin, sha).is_dir()

    def plugin_dir(self, registry: str, plugin: str, sha: str, /) -> Path:
        """Return the cache path for a plugin version."""
        return self._cache_dir / registry / plugin / sha

    def list_files(self, registry: str, plugin: str, sha: str, /) -> list[str]:
        """List all files in a cached plugin directory as relative paths."""
        cache_dir = self.plugin_dir(registry, plugin, sha)
        if not cache_dir.is_dir():
            return []
        return sorted(
            str(f.relative_to(cache_dir)) for f in cache_dir.rglob("*") if f.is_file()
        )
