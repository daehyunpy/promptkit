"""Infrastructure layer: Read/write promptkit.lock files."""

from datetime import datetime, timezone
from typing import Any

import yaml

from promptkit.domain.errors import ValidationError
from promptkit.domain.lock_entry import LockEntry

LOCK_VERSION = 1


class LockFile:
    """Serializes and deserializes promptkit.lock content."""

    @staticmethod
    def serialize(entries: list[LockEntry], /) -> str:
        """Serialize lock entries to YAML string."""
        prompts_data: list[dict[str, Any]] = []
        for entry in entries:
            entry_data: dict[str, Any] = {
                "name": entry.name,
                "source": entry.source,
                "hash": entry.content_hash,
                "fetched_at": entry.fetched_at.isoformat(),
            }
            if entry.commit_sha is not None:
                entry_data["commit_sha"] = entry.commit_sha
            prompts_data.append(entry_data)

        data: dict[str, Any] = {
            "version": LOCK_VERSION,
            "prompts": prompts_data,
        }
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    @staticmethod
    def deserialize(yaml_content: str, /) -> list[LockEntry]:
        """Deserialize YAML string into lock entries.

        Raises:
            ValidationError: If YAML is invalid or missing required fields.
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid lock file YAML: {e}") from e

        if not isinstance(data, dict):
            raise ValidationError("Lock file must be a YAML mapping")

        if "prompts" not in data:
            raise ValidationError("Lock file missing required field: 'prompts'")

        prompts_raw = data["prompts"]
        if not prompts_raw:
            return []

        return [_parse_lock_entry(entry_raw) for entry_raw in prompts_raw]


_REQUIRED_LOCK_FIELDS = ("name", "source", "hash", "fetched_at")


def _parse_lock_entry(entry: dict[str, Any]) -> LockEntry:
    for field in _REQUIRED_LOCK_FIELDS:
        if field not in entry:
            raise ValidationError(f"Lock entry missing required field: '{field}'")

    fetched_at = _parse_datetime(entry["fetched_at"])

    return LockEntry(
        name=entry["name"],
        source=entry["source"],
        content_hash=entry["hash"],
        fetched_at=fetched_at,
        commit_sha=entry.get("commit_sha"),
    )


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid datetime: '{value}'") from e

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
