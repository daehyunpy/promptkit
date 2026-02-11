"""Infrastructure layer: Shallow git clone management for marketplace registries."""

import shutil
import subprocess
from pathlib import Path

from promptkit.domain.errors import SyncError

GIT_CLONE_DEPTH = 1


class GitRegistryClone:
    """Manages a shallow git clone of a marketplace registry.

    Provides clone/pull/rev-parse operations for a single registry repo.
    Clones are stored at {registries_dir}/{registry_name}/.
    """

    def __init__(
        self,
        *,
        registry_name: str,
        registry_url: str,
        registries_dir: Path,
    ) -> None:
        self._registry_name = registry_name
        self._clone_url = self._to_clone_url(registry_url)
        self._clone_dir = registries_dir / registry_name
        self._check_git_available()

    @property
    def clone_dir(self) -> Path:
        return self._clone_dir

    def ensure_up_to_date(self) -> None:
        """Clone the repo if missing, or pull latest changes.

        If pull fails on an existing clone, deletes and re-clones.
        """
        if not self._is_valid_clone():
            self._fresh_clone()
            return

        try:
            self._run_git("pull", cwd=self._clone_dir)
        except SyncError:
            self._fresh_clone()

    def get_commit_sha(self) -> str:
        """Return the HEAD commit SHA of the local clone."""
        result = self._run_git("rev-parse", "HEAD", cwd=self._clone_dir)
        return result.stdout.strip()

    def _is_valid_clone(self) -> bool:
        """Check if the clone directory exists and has a .git subdirectory."""
        return (self._clone_dir / ".git").is_dir()

    def _fresh_clone(self) -> None:
        """Delete any existing directory and clone fresh."""
        if self._clone_dir.exists():
            shutil.rmtree(self._clone_dir)
        self._clone_dir.parent.mkdir(parents=True, exist_ok=True)
        self._run_git(
            "clone",
            "--depth",
            str(GIT_CLONE_DEPTH),
            self._clone_url,
            str(self._clone_dir),
        )

    def _run_git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        """Run a git command, raising SyncError on failure."""
        try:
            return subprocess.run(
                ["git", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise SyncError(
                f"Git command failed: git {' '.join(args)}\n{e.stderr.strip()}"
            ) from e

    def _check_git_available(self) -> None:
        """Verify git is on PATH."""
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as e:
            raise SyncError(
                "git is required but not found on PATH. "
                "Install git to use registry plugins."
            ) from e

    @staticmethod
    def _to_clone_url(registry_url: str) -> str:
        """Convert a GitHub URL to a git clone URL."""
        url = registry_url.rstrip("/")
        if not url.endswith(".git"):
            url = f"{url}.git"
        return url
