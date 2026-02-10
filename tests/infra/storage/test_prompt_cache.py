"""Tests for PromptCache content-addressable storage."""

import hashlib
from pathlib import Path

import pytest

from promptkit.infra.file_system.local import FileSystem
from promptkit.infra.storage.prompt_cache import PromptCache


@pytest.fixture
def cache(tmp_path: Path) -> PromptCache:
    cache_dir = tmp_path / ".promptkit" / "cache"
    return PromptCache(FileSystem(), cache_dir)


def _hash_of(content: str) -> str:
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


class TestStore:
    def test_store_returns_content_hash(self, cache: PromptCache) -> None:
        content = "# My Prompt\nContent here"
        result = cache.store(content)
        assert result == _hash_of(content)

    def test_store_creates_cache_file(
        self, cache: PromptCache, tmp_path: Path
    ) -> None:
        content = "# My Prompt"
        content_hash = cache.store(content)
        hex_digest = content_hash.removeprefix("sha256:")
        cache_file = tmp_path / ".promptkit" / "cache" / f"sha256-{hex_digest}.md"
        assert cache_file.exists()
        assert cache_file.read_text() == content

    def test_store_duplicate_is_idempotent(self, cache: PromptCache) -> None:
        content = "# Same content"
        hash1 = cache.store(content)
        hash2 = cache.store(content)
        assert hash1 == hash2


class TestRetrieve:
    def test_retrieve_returns_stored_content(self, cache: PromptCache) -> None:
        content = "# Stored prompt"
        content_hash = cache.store(content)
        assert cache.retrieve(content_hash) == content

    def test_retrieve_returns_none_for_missing(self, cache: PromptCache) -> None:
        assert cache.retrieve("sha256:0000000000000000") is None


class TestHas:
    def test_has_returns_true_for_stored(self, cache: PromptCache) -> None:
        content_hash = cache.store("# Exists")
        assert cache.has(content_hash) is True

    def test_has_returns_false_for_missing(self, cache: PromptCache) -> None:
        assert cache.has("sha256:0000000000000000") is False
