"""Application layer: InitProject use case."""

from collections.abc import Callable
from pathlib import Path

from promptkit.domain.file_system import FileSystem
from promptkit.domain.project_config import ProjectConfig

CONFIG_FILENAME = "promptkit.yaml"
LOCK_FILENAME = "promptkit.lock"
GITIGNORE_FILENAME = ".gitignore"

CACHE_DIR = ".promptkit/cache"
PROMPTS_DIR = "prompts"
CURSOR_DIR = ".cursor"
CLAUDE_DIR = ".claude"

SCAFFOLD_DIRS = (CACHE_DIR, PROMPTS_DIR, CURSOR_DIR, CLAUDE_DIR)

LOCK_FILE_CONTENT = "# promptkit lock file\nversion: 1\nprompts: []\n"
GITIGNORE_ENTRY = "\n# promptkit\n.promptkit/cache/\n.promptkit/registries/\n"


class InitProjectError(Exception):
    """Error during project initialization."""


class InitProject:
    """Use case for initializing a new promptkit project."""

    def __init__(
        self,
        file_system: FileSystem,
        config_serializer: Callable[[ProjectConfig], str],
        /,
    ):
        self._file_system = file_system
        self._config_serializer = config_serializer

    def execute(self, target_dir: Path, /) -> None:
        """Initialize a new promptkit project in target_dir.

        Raises:
            InitProjectError: If promptkit.yaml already exists.
        """
        config_path = target_dir / CONFIG_FILENAME
        if self._file_system.file_exists(config_path):
            raise InitProjectError(
                f"{CONFIG_FILENAME} already exists. "
                "Remove it or run in a different directory."
            )

        self._create_scaffold_dirs(target_dir)
        self._write_config(target_dir, config_path)
        self._write_lock_file(target_dir)
        self._update_gitignore(target_dir)

    def _create_scaffold_dirs(self, target_dir: Path, /) -> None:
        for directory in SCAFFOLD_DIRS:
            self._file_system.create_directory(target_dir / directory)

    def _write_config(self, target_dir: Path, config_path: Path, /) -> None:
        config = ProjectConfig.default()
        self._file_system.write_file(config_path, self._config_serializer(config))

    def _write_lock_file(self, target_dir: Path, /) -> None:
        self._file_system.write_file(target_dir / LOCK_FILENAME, LOCK_FILE_CONTENT)

    def _update_gitignore(self, target_dir: Path, /) -> None:
        gitignore_path = target_dir / GITIGNORE_FILENAME

        if self._file_system.file_exists(gitignore_path):
            self._file_system.append_to_file(gitignore_path, GITIGNORE_ENTRY)
        else:
            self._file_system.write_file(gitignore_path, GITIGNORE_ENTRY)
