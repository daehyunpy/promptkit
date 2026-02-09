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
