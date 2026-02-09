"""Application layer: InitProject use case."""

from pathlib import Path

from promptkit.domain.file_system import FileSystem
from promptkit.domain.project_config import ProjectConfig


class InitProjectError(Exception):
    """Error during project initialization."""

    pass


class InitProject:
    """Use case for initializing a new promptkit project."""

    def __init__(self, file_system: FileSystem, /):
        """Initialize with file system dependency."""
        self.file_system = file_system

    def execute(self, target_dir: Path, /) -> None:
        """Execute project initialization in target directory.

        Args:
            target_dir: Directory to initialize the project in

        Raises:
            InitProjectError: If promptkit.yaml already exists
        """
        # Check if already initialized
        config_path = target_dir / "promptkit.yaml"
        if self.file_system.file_exists(config_path):
            raise InitProjectError(
                "promptkit.yaml already exists. "
                "Remove it or run in a different directory."
            )

        # Create directories
        self.file_system.create_directory(target_dir / ".promptkit" / "cache")
        self.file_system.create_directory(target_dir / ".agents")
        self.file_system.create_directory(target_dir / ".cursor")
        self.file_system.create_directory(target_dir / ".claude")

        # Generate and write promptkit.yaml
        config = ProjectConfig.default()
        self.file_system.write_file(config_path, config.to_yaml_string())

        # Create empty promptkit.lock
        lock_path = target_dir / "promptkit.lock"
        lock_content = "# promptkit lock file\nversion: 1\nprompts: []\n"
        self.file_system.write_file(lock_path, lock_content)

        # Add/update .gitignore
        gitignore_path = target_dir / ".gitignore"
        gitignore_entry = "\n# promptkit\n.promptkit/cache/\n"

        if self.file_system.file_exists(gitignore_path):
            self.file_system.append_to_file(gitignore_path, gitignore_entry)
        else:
            self.file_system.write_file(gitignore_path, gitignore_entry)
