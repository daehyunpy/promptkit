"""Infrastructure layer: local file system implementation."""

import shutil
from pathlib import Path


class FileSystem:
    """File system backed by the local OS.

    Implements the FileSystem protocol defined in the domain layer.
    """

    def create_directory(self, path: Path, /) -> None:
        """Create directory, including parent directories if needed."""
        path.mkdir(parents=True, exist_ok=True)

    def write_file(self, path: Path, content: str, /) -> None:
        """Write content to file, creating parent directories if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def file_exists(self, path: Path, /) -> bool:
        """Check if file exists."""
        return path.exists()

    def append_to_file(self, path: Path, content: str, /) -> None:
        """Append content to existing file."""
        with path.open("a") as f:
            f.write(content)

    def read_file(self, path: Path, /) -> str:
        """Read file content as string."""
        return path.read_text()

    def list_directory(self, path: Path, /) -> list[Path]:
        """List immediate children of a directory."""
        if not path.is_dir():
            return []
        return list(path.iterdir())

    def remove_directory(self, path: Path, /) -> None:
        """Remove a directory and all its contents."""
        if path.is_dir():
            shutil.rmtree(path)
