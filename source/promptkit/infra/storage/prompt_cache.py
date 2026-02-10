"""Infrastructure layer: Content-addressable prompt cache."""

import hashlib
from pathlib import Path

from promptkit.domain.file_system import FileSystem

HASH_PREFIX = "sha256:"
CACHE_FILE_PREFIX = "sha256-"
CACHE_FILE_SUFFIX = ".md"


class PromptCache:
    """Content-addressable storage for fetched prompt files.

    Files are stored as sha256-<hex>.md in the cache directory.
    Methods accept/return hash strings in sha256:<hex> format.
    """

    def __init__(self, file_system: FileSystem, cache_dir: Path, /) -> None:
        self._fs = file_system
        self._cache_dir = cache_dir

    def store(self, content: str, /) -> str:
        """Store content in cache. Returns the content hash (sha256:<hex>)."""
        content_hash = self._compute_hash(content)
        cache_path = self._hash_to_path(content_hash)
        if not self._fs.file_exists(cache_path):
            self._fs.write_file(cache_path, content)
        return content_hash

    def retrieve(self, content_hash: str, /) -> str | None:
        """Retrieve content by hash. Returns None if not cached."""
        cache_path = self._hash_to_path(content_hash)
        if not self._fs.file_exists(cache_path):
            return None
        return self._fs.read_file(cache_path)

    def has(self, content_hash: str, /) -> bool:
        """Check if content with the given hash exists in cache."""
        return self._fs.file_exists(self._hash_to_path(content_hash))

    def _hash_to_path(self, content_hash: str, /) -> Path:
        hex_digest = content_hash.removeprefix(HASH_PREFIX)
        return self._cache_dir / f"{CACHE_FILE_PREFIX}{hex_digest}{CACHE_FILE_SUFFIX}"

    @staticmethod
    def _compute_hash(content: str, /) -> str:
        digest = hashlib.sha256(content.encode()).hexdigest()
        return f"{HASH_PREFIX}{digest}"
