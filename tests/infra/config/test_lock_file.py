"""Tests for LockFile reader/writer."""

from datetime import datetime, timezone

import pytest

from promptkit.domain.errors import ValidationError
from promptkit.domain.lock_entry import LockEntry
from promptkit.infra.config.lock_file import LockFile


SAMPLE_LOCK_ENTRIES = [
    LockEntry(
        name="code-reviewer",
        source="anthropic/code-reviewer",
        content_hash="sha256:abc123def456",
        fetched_at=datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc),
    ),
    LockEntry(
        name="test-writer",
        source="local/test-writer",
        content_hash="sha256:789xyz",
        fetched_at=datetime(2026, 2, 8, 15, 0, 0, tzinfo=timezone.utc),
    ),
]


class TestLockFileSerialize:
    def test_serialize_empty(self) -> None:
        result = LockFile.serialize([])
        assert "version: 1" in result
        assert "prompts: []" in result

    def test_serialize_single_entry(self) -> None:
        result = LockFile.serialize([SAMPLE_LOCK_ENTRIES[0]])
        assert "code-reviewer" in result
        assert "anthropic/code-reviewer" in result
        assert "sha256:abc123def456" in result

    def test_serialize_multiple_entries(self) -> None:
        result = LockFile.serialize(SAMPLE_LOCK_ENTRIES)
        assert "code-reviewer" in result
        assert "test-writer" in result

    def test_serialize_produces_valid_yaml(self) -> None:
        import yaml

        result = LockFile.serialize(SAMPLE_LOCK_ENTRIES)
        parsed = yaml.safe_load(result)
        assert parsed["version"] == 1
        assert len(parsed["prompts"]) == 2

    def test_serialize_includes_fetched_at_as_iso(self) -> None:
        result = LockFile.serialize([SAMPLE_LOCK_ENTRIES[0]])
        assert "2026-02-08" in result


class TestLockFileDeserialize:
    def test_roundtrip_empty(self) -> None:
        serialized = LockFile.serialize([])
        entries = LockFile.deserialize(serialized)
        assert entries == []

    def test_roundtrip_entries(self) -> None:
        serialized = LockFile.serialize(SAMPLE_LOCK_ENTRIES)
        entries = LockFile.deserialize(serialized)
        assert len(entries) == 2
        assert entries[0].name == "code-reviewer"
        assert entries[0].source == "anthropic/code-reviewer"
        assert entries[0].content_hash == "sha256:abc123def456"
        assert entries[1].name == "test-writer"

    def test_deserialize_preserves_hash(self) -> None:
        serialized = LockFile.serialize(SAMPLE_LOCK_ENTRIES)
        entries = LockFile.deserialize(serialized)
        assert entries[0].content_hash == SAMPLE_LOCK_ENTRIES[0].content_hash

    def test_deserialize_invalid_yaml_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid"):
            LockFile.deserialize("{{bad yaml:")

    def test_deserialize_missing_prompts_raises(self) -> None:
        with pytest.raises(ValidationError, match="prompts"):
            LockFile.deserialize("version: 1\n")

    def test_deserialize_entry_missing_name_raises(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - source: local/test
    hash: sha256:abc
    fetched_at: '2026-02-08T14:50:00+00:00'
"""
        with pytest.raises(ValidationError, match="name"):
            LockFile.deserialize(yaml_content)


class TestLockFileCommitSha:
    def test_serialize_entry_with_commit_sha(self) -> None:
        entry = LockEntry(
            name="code-review",
            source="claude-plugins-official/code-review",
            content_hash="",
            fetched_at=datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc),
            commit_sha="abc123def",
        )
        result = LockFile.serialize([entry])
        assert "commit_sha: abc123def" in result

    def test_serialize_entry_without_commit_sha_omits_field(self) -> None:
        entry = LockEntry(
            name="my-rule",
            source="local/my-rule",
            content_hash="sha256:abc",
            fetched_at=datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc),
        )
        result = LockFile.serialize([entry])
        assert "commit_sha" not in result

    def test_roundtrip_with_commit_sha(self) -> None:
        entry = LockEntry(
            name="code-review",
            source="claude-plugins-official/code-review",
            content_hash="",
            fetched_at=datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc),
            commit_sha="abc123def",
        )
        serialized = LockFile.serialize([entry])
        deserialized = LockFile.deserialize(serialized)
        assert deserialized[0].commit_sha == "abc123def"
        assert deserialized[0].content_hash == ""

    def test_roundtrip_without_commit_sha(self) -> None:
        entry = LockEntry(
            name="my-rule",
            source="local/my-rule",
            content_hash="sha256:abc",
            fetched_at=datetime(2026, 2, 8, 14, 50, 0, tzinfo=timezone.utc),
        )
        serialized = LockFile.serialize([entry])
        deserialized = LockFile.deserialize(serialized)
        assert deserialized[0].commit_sha is None

    def test_backward_compatible_lock_file_without_commit_sha(self) -> None:
        yaml_content = """\
version: 1
prompts:
  - name: old-prompt
    source: local/old-prompt
    hash: sha256:abc
    fetched_at: '2026-02-08T14:50:00+00:00'
"""
        entries = LockFile.deserialize(yaml_content)
        assert entries[0].commit_sha is None
