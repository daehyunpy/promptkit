"""Tests for file system operations."""

from pathlib import Path

import pytest

from promptkit.infra.file_system.local import FileSystem


def test_create_directory_creates_nested_dirs(tmp_path: Path) -> None:
    """create_directory should create nested directories."""
    fs = FileSystem()
    target = tmp_path / "a" / "b" / "c"

    fs.create_directory(target)

    assert target.exists()
    assert target.is_dir()


def test_create_directory_is_idempotent(tmp_path: Path) -> None:
    """create_directory should not fail if directory already exists."""
    fs = FileSystem()
    target = tmp_path / "existing"

    fs.create_directory(target)
    fs.create_directory(target)  # Should not raise

    assert target.exists()


def test_write_file_creates_file_with_content(tmp_path: Path) -> None:
    """write_file should create file with given content."""
    fs = FileSystem()
    target = tmp_path / "test.txt"

    fs.write_file(target, "hello world")

    assert target.exists()
    assert target.read_text() == "hello world"


def test_write_file_creates_parent_directories(tmp_path: Path) -> None:
    """write_file should create parent directories if needed."""
    fs = FileSystem()
    target = tmp_path / "nested" / "dir" / "file.txt"

    fs.write_file(target, "content")

    assert target.exists()
    assert target.read_text() == "content"


def test_file_exists_returns_true_for_existing_file(tmp_path: Path) -> None:
    """file_exists should return True for existing files."""
    fs = FileSystem()
    target = tmp_path / "exists.txt"
    target.write_text("content")

    assert fs.file_exists(target) is True


def test_file_exists_returns_false_for_missing_file(tmp_path: Path) -> None:
    """file_exists should return False for missing files."""
    fs = FileSystem()
    target = tmp_path / "missing.txt"

    assert fs.file_exists(target) is False


def test_append_to_file_appends_content(tmp_path: Path) -> None:
    """append_to_file should append content to existing file."""
    fs = FileSystem()
    target = tmp_path / "append.txt"
    target.write_text("first\n")

    fs.append_to_file(target, "second\n")

    assert target.read_text() == "first\nsecond\n"


def test_read_file_returns_content(tmp_path: Path) -> None:
    """read_file should return file content as string."""
    fs = FileSystem()
    target = tmp_path / "read.txt"
    target.write_text("hello world")

    assert fs.read_file(target) == "hello world"


def test_read_file_raises_for_missing_file(tmp_path: Path) -> None:
    """read_file should raise FileNotFoundError for missing files."""
    fs = FileSystem()
    target = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        fs.read_file(target)


def test_list_directory_returns_children(tmp_path: Path) -> None:
    """list_directory should return immediate children of a directory."""
    fs = FileSystem()
    (tmp_path / "file1.txt").write_text("a")
    (tmp_path / "file2.txt").write_text("b")
    (tmp_path / "subdir").mkdir()

    result = fs.list_directory(tmp_path)

    names = sorted(p.name for p in result)
    assert names == ["file1.txt", "file2.txt", "subdir"]


def test_list_directory_returns_empty_for_missing_dir(tmp_path: Path) -> None:
    """list_directory should return empty list for nonexistent directory."""
    fs = FileSystem()
    target = tmp_path / "nonexistent"

    assert fs.list_directory(target) == []
