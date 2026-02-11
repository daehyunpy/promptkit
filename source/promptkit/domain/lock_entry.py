"""Domain layer: LockEntry value object for promptkit.lock entries."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LockEntry:
    """Immutable lock entry recording the exact state of a synced plugin.

    Stored in promptkit.lock to ensure reproducible builds.
    For registry plugins: commit_sha is set, content_hash is "".
    For local plugins: commit_sha is None, content_hash is sha256 hash.
    """

    name: str
    source: str
    content_hash: str
    fetched_at: datetime
    commit_sha: str | None = None

    def has_content_changed(self, new_hash: str, /) -> bool:
        """Whether the content has changed compared to a new hash."""
        return self.content_hash != new_hash

    def has_commit_changed(self, new_sha: str, /) -> bool:
        """Whether the commit SHA has changed (for registry plugins)."""
        return self.commit_sha != new_sha
