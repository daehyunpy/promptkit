"""Tests for GitRegistryClone."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from promptkit.domain.errors import SyncError
from promptkit.infra.fetchers.git_registry_clone import GitRegistryClone


def _git_env(work_dir: Path) -> dict[str, str]:
    """Return a minimal git env for committing without user config."""
    return {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "t@t",
        "HOME": str(work_dir),
        "PATH": os.environ["PATH"],
    }


def _git(work_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in work_dir."""
    return subprocess.run(
        ["git", "-C", str(work_dir), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _commit_and_push(work_dir: Path, message: str) -> str:
    """Stage all, commit, push, and return the commit SHA."""
    _git(work_dir, "add", ".")
    subprocess.run(
        ["git", "-C", str(work_dir), "commit", "-m", message],
        check=True,
        capture_output=True,
        env=_git_env(work_dir),
    )
    _git(work_dir, "push")
    return _git(work_dir, "rev-parse", "HEAD").stdout.strip()


def _init_bare_repo(repo_dir: Path) -> str:
    """Create a bare git repo with one commit, return the commit SHA."""
    repo_dir.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--bare", str(repo_dir)],
        check=True,
        capture_output=True,
    )
    work_dir = repo_dir.parent / "work"
    subprocess.run(
        ["git", "clone", str(repo_dir), str(work_dir)],
        check=True,
        capture_output=True,
    )
    (work_dir / "README.md").write_text("# Test")
    return _commit_and_push(work_dir, "init")


def _make_clone(tmp_path: Path, repo_url: str, name: str = "test-registry") -> GitRegistryClone:
    """Create a GitRegistryClone pointing at a local bare repo."""
    return GitRegistryClone(
        registry_name=name,
        registry_url=repo_url,
        registries_dir=tmp_path / "registries",
    )


class TestGitAvailability:
    def test_construction_succeeds_when_git_is_available(self, tmp_path: Path) -> None:
        """Git is available on this machine, so construction should succeed."""
        _init_bare_repo(tmp_path / "repo.git")
        clone = _make_clone(tmp_path, str(tmp_path / "repo.git"))
        assert clone.clone_dir == tmp_path / "registries" / "test-registry"

    def test_construction_raises_when_git_not_found(self, tmp_path: Path) -> None:
        with patch("promptkit.infra.fetchers.git_registry_clone.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            with pytest.raises(SyncError, match="git is required but not found"):
                GitRegistryClone(
                    registry_name="test",
                    registry_url="https://github.com/org/repo",
                    registries_dir=tmp_path / "registries",
                )


class TestEnsureUpToDate:
    def test_clones_when_no_local_directory(self, tmp_path: Path) -> None:
        sha = _init_bare_repo(tmp_path / "repo.git")
        clone = _make_clone(tmp_path, str(tmp_path / "repo.git"))

        clone.ensure_up_to_date()

        assert (clone.clone_dir / ".git").is_dir()
        assert (clone.clone_dir / "README.md").read_text() == "# Test"
        assert clone.get_commit_sha() == sha

    def test_pulls_when_clone_exists(self, tmp_path: Path) -> None:
        sha = _init_bare_repo(tmp_path / "repo.git")
        clone = _make_clone(tmp_path, str(tmp_path / "repo.git"))
        clone.ensure_up_to_date()
        assert clone.get_commit_sha() == sha

        # Add a new commit to the bare repo via a fresh working copy
        work_dir = tmp_path / "work2"
        subprocess.run(
            ["git", "clone", str(tmp_path / "repo.git"), str(work_dir)],
            check=True,
            capture_output=True,
        )
        (work_dir / "new.txt").write_text("new file")
        new_sha = _commit_and_push(work_dir, "second")

        clone.ensure_up_to_date()

        assert clone.get_commit_sha() == new_sha
        assert (clone.clone_dir / "new.txt").read_text() == "new file"

    def test_recovers_from_corrupt_clone(self, tmp_path: Path) -> None:
        sha = _init_bare_repo(tmp_path / "repo.git")
        clone = _make_clone(tmp_path, str(tmp_path / "repo.git"))

        # Create a corrupt directory (exists but no .git)
        clone.clone_dir.mkdir(parents=True)
        (clone.clone_dir / "garbage.txt").write_text("corrupt")

        clone.ensure_up_to_date()

        assert (clone.clone_dir / ".git").is_dir()
        assert (clone.clone_dir / "README.md").read_text() == "# Test"
        assert not (clone.clone_dir / "garbage.txt").exists()
        assert clone.get_commit_sha() == sha


class TestGetCommitSha:
    def test_returns_correct_sha(self, tmp_path: Path) -> None:
        sha = _init_bare_repo(tmp_path / "repo.git")
        clone = _make_clone(tmp_path, str(tmp_path / "repo.git"))
        clone.ensure_up_to_date()

        assert clone.get_commit_sha() == sha
        assert len(sha) == 40


class TestErrorHandling:
    def test_git_error_wrapped_in_sync_error(self, tmp_path: Path) -> None:
        clone = _make_clone(tmp_path, str(tmp_path / "nonexistent-repo.git"))

        with pytest.raises(SyncError, match="Git command failed"):
            clone.ensure_up_to_date()
