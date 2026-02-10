"""Application layer: ValidateConfig use case."""

from pathlib import Path

from promptkit.domain.errors import ValidationError
from promptkit.domain.file_system import FileSystem
from promptkit.domain.prompt import LOCAL_SOURCE_PREFIX
from promptkit.domain.validation import (
    LEVEL_ERROR,
    LEVEL_WARNING,
    ValidationIssue,
    ValidationResult,
)
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import LoadedConfig, YamlLoader

CONFIG_FILENAME = "promptkit.yaml"
LOCK_FILENAME = "promptkit.lock"


class ValidateConfig:
    """Use case for validating promptkit configuration."""

    def __init__(
        self,
        *,
        file_system: FileSystem,
        yaml_loader: YamlLoader,
        lock_file: LockFile,
    ) -> None:
        self._fs = file_system
        self._yaml_loader = yaml_loader
        self._lock_file = lock_file

    def execute(self, project_dir: Path, /) -> ValidationResult:
        """Validate config and return collected issues."""
        issues: list[ValidationIssue] = []

        config = self._check_config_wellformed(project_dir, issues)
        if config is None:
            return ValidationResult(issues=tuple(issues))

        self._check_registry_references(config, issues)
        self._check_lock_freshness(project_dir, config, issues)

        return ValidationResult(issues=tuple(issues))

    def _check_config_wellformed(
        self, project_dir: Path, issues: list[ValidationIssue], /
    ) -> LoadedConfig | None:
        """Parse config; return LoadedConfig on success, None on failure."""
        config_path = project_dir / CONFIG_FILENAME
        try:
            yaml_content = self._fs.read_file(config_path)
            return self._yaml_loader.load(yaml_content)
        except (ValidationError, FileNotFoundError) as e:
            issues.append(ValidationIssue(level=LEVEL_ERROR, message=str(e)))
            return None

    def _check_registry_references(
        self, config: LoadedConfig, issues: list[ValidationIssue], /
    ) -> None:
        """Check that each prompt references a defined registry."""
        registry_names = {r.name for r in config.registries}
        for spec in config.prompt_specs:
            if spec.registry_name not in registry_names:
                issues.append(
                    ValidationIssue(
                        level=LEVEL_ERROR,
                        message=f"Prompt '{spec.source}' references undefined "
                        f"registry '{spec.registry_name}'",
                    )
                )

    def _check_lock_freshness(
        self,
        project_dir: Path,
        config: LoadedConfig,
        issues: list[ValidationIssue],
        /,
    ) -> None:
        """Check lock file exists and is consistent with config."""
        lock_path = project_dir / LOCK_FILENAME
        if not self._fs.file_exists(lock_path):
            issues.append(
                ValidationIssue(
                    level=LEVEL_WARNING,
                    message="No lock file found. Run 'promptkit lock' to create one.",
                )
            )
            return

        lock_content = self._fs.read_file(lock_path)
        entries = self._lock_file.deserialize(lock_content)
        locked_sources = {e.source for e in entries}
        config_sources = {s.source for s in config.prompt_specs}

        for source in config_sources - locked_sources:
            issues.append(
                ValidationIssue(
                    level=LEVEL_WARNING,
                    message=f"Prompt '{source}' is not locked. "
                    "Run 'promptkit lock' to update.",
                )
            )

        for entry in entries:
            if (
                not entry.source.startswith(LOCAL_SOURCE_PREFIX)
                and entry.source not in config_sources
            ):
                issues.append(
                    ValidationIssue(
                        level=LEVEL_WARNING,
                        message=f"Lock entry '{entry.name}' (source: {entry.source}) "
                        "is stale. Run 'promptkit lock' to update.",
                    )
                )
