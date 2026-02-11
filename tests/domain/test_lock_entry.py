"""Tests for LockEntry value object."""

from datetime import datetime, timezone

from promptkit.domain.lock_entry import LockEntry


class TestLockEntry:
    def test_create_with_all_fields(self) -> None:
        fetched_at = datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc)
        entry = LockEntry(
            name="code-reviewer",
            source="anthropic/code-reviewer",
            content_hash="sha256:abc123",
            fetched_at=fetched_at,
        )
        assert entry.name == "code-reviewer"
        assert entry.source == "anthropic/code-reviewer"
        assert entry.content_hash == "sha256:abc123"
        assert entry.fetched_at == fetched_at

    def test_is_immutable(self) -> None:
        entry = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=datetime.now(tz=timezone.utc),
        )
        try:
            entry.name = "other"  # type: ignore[misc]
            assert False, "Expected FrozenInstanceError"
        except AttributeError:
            pass

    def test_equality_same_values(self) -> None:
        fetched_at = datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc)
        e1 = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=fetched_at,
        )
        e2 = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=fetched_at,
        )
        assert e1 == e2

    def test_equality_different_hash(self) -> None:
        fetched_at = datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc)
        e1 = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=fetched_at,
        )
        e2 = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:def",
            fetched_at=fetched_at,
        )
        assert e1 != e2

    def test_hash_changed_detects_difference(self) -> None:
        entry = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=datetime.now(tz=timezone.utc),
        )
        assert entry.has_content_changed("sha256:def") is True

    def test_hash_changed_detects_same(self) -> None:
        entry = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=datetime.now(tz=timezone.utc),
        )
        assert entry.has_content_changed("sha256:abc") is False


class TestLockEntryCommitSha:
    def test_commit_sha_defaults_to_none(self) -> None:
        entry = LockEntry(
            name="test",
            source="local/test",
            content_hash="sha256:abc",
            fetched_at=datetime.now(tz=timezone.utc),
        )
        assert entry.commit_sha is None

    def test_registry_plugin_with_commit_sha(self) -> None:
        entry = LockEntry(
            name="code-review",
            source="claude-plugins-official/code-review",
            content_hash="",
            fetched_at=datetime.now(tz=timezone.utc),
            commit_sha="abc123def",
        )
        assert entry.commit_sha == "abc123def"
        assert entry.content_hash == ""

    def test_has_commit_changed_detects_difference(self) -> None:
        entry = LockEntry(
            name="test",
            source="registry/test",
            content_hash="",
            fetched_at=datetime.now(tz=timezone.utc),
            commit_sha="abc123",
        )
        assert entry.has_commit_changed("def456") is True

    def test_has_commit_changed_detects_same(self) -> None:
        entry = LockEntry(
            name="test",
            source="registry/test",
            content_hash="",
            fetched_at=datetime.now(tz=timezone.utc),
            commit_sha="abc123",
        )
        assert entry.has_commit_changed("abc123") is False
