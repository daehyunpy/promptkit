"""Domain layer: File system abstraction (protocol)."""

from pathlib import Path
from typing import Protocol


class FileSystem(Protocol):
    """Protocol for file system operations.

    This is a domain concept - the domain defines what file operations it needs.
    Infrastructure layer provides concrete implementations.
    """

    def create_directory(self, path: Path, /) -> None:
        """Create directory, including parent directories if needed."""
        ...

    def write_file(self, path: Path, content: str, /) -> None:
        """Write content to file, creating parent directories if needed."""
        ...

    def file_exists(self, path: Path, /) -> bool:
        """Check if file exists."""
        ...

    def append_to_file(self, path: Path, content: str, /) -> None:
        """Append content to existing file."""
        ...
