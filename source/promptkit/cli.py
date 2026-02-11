"""CLI interface for promptkit."""

from pathlib import Path

import typer

from promptkit.app.build import BuildArtifacts
from promptkit.app.init import InitProject, InitProjectError
from promptkit.app.lock import LockPrompts
from promptkit.app.validate import ValidateConfig
from promptkit.domain.errors import PromptError
from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.protocols import PluginFetcher
from promptkit.domain.registry import Registry, RegistryType
from promptkit.domain.validation import LEVEL_ERROR, ValidationIssue
from promptkit.infra.builders.claude_builder import ClaudeBuilder
from promptkit.infra.builders.cursor_builder import CursorBuilder
from promptkit.infra.config.lock_file import LockFile
from promptkit.infra.config.yaml_loader import YamlLoader
from promptkit.infra.config_serializer import serialize_config_to_yaml
from promptkit.infra.fetchers.claude_marketplace import ClaudeMarketplaceFetcher
from promptkit.infra.fetchers.git_registry_clone import GitRegistryClone
from promptkit.infra.fetchers.local_plugin_fetcher import LocalPluginFetcher
from promptkit.infra.file_system.local import FileSystem
from promptkit.infra.storage.plugin_cache import PluginCache

app = typer.Typer(help="Package manager for AI prompts")

PLUGIN_CACHE_DIR = ".promptkit/cache/plugins"
REGISTRIES_DIR = ".promptkit/registries"
PROMPTS_DIR = "prompts"

SUCCESS_MESSAGE = """\
✓ Initialized promptkit project

  promptkit.yaml    configuration
  promptkit.lock    dependency lock
  prompts/          local prompts
  .promptkit/       cache, registries, and build manifests (gitignored)

Next steps:
  1. Edit promptkit.yaml to configure prompts
  2. Run 'promptkit sync' to fetch and build\
"""


def _make_plugin_fetchers(
    registries: list[Registry], cache: PluginCache, registries_dir: Path
) -> dict[str, PluginFetcher]:
    """Map config registries to PluginFetcher instances."""
    fetchers: dict[str, PluginFetcher] = {}
    for registry in registries:
        if registry.registry_type == RegistryType.CLAUDE_MARKETPLACE:
            clone = GitRegistryClone(
                registry_name=registry.name,
                registry_url=registry.url,
                registries_dir=registries_dir,
            )
            fetchers[registry.name] = ClaudeMarketplaceFetcher(
                registry_url=registry.url,
                registry_name=registry.name,
                cache=cache,
                clone=clone,
            )
    return fetchers


def _make_lock_use_case(cwd: Path, fs: FileSystem) -> LockPrompts:
    """Create a LockPrompts use case with standard wiring."""
    yaml_loader = YamlLoader()
    config_path = cwd / "promptkit.yaml"
    cache = PluginCache(cwd / PLUGIN_CACHE_DIR)

    registries: list[Registry] = []
    if config_path.exists():
        yaml_content = fs.read_file(config_path)
        config = yaml_loader.load(yaml_content)
        registries = config.registries

    return LockPrompts(
        file_system=fs,
        yaml_loader=yaml_loader,
        lock_file=LockFile(),
        local_fetcher=LocalPluginFetcher(fs, cwd / PROMPTS_DIR),
        fetchers=_make_plugin_fetchers(registries, cache, cwd / REGISTRIES_DIR),
    )


def _make_build_use_case(cwd: Path, fs: FileSystem) -> BuildArtifacts:
    """Create a BuildArtifacts use case with standard wiring."""
    return BuildArtifacts(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
        plugin_cache=PluginCache(cwd / PLUGIN_CACHE_DIR),
        builders={
            PlatformTarget.CURSOR: CursorBuilder(fs),
            PlatformTarget.CLAUDE_CODE: ClaudeBuilder(fs),
        },
    )


def _make_validate_use_case(fs: FileSystem) -> ValidateConfig:
    """Create a ValidateConfig use case with standard wiring."""
    return ValidateConfig(
        file_system=fs,
        yaml_loader=YamlLoader(),
        lock_file=LockFile(),
    )


@app.command()
def init() -> None:
    """Initialize a new promptkit project."""
    try:
        use_case = InitProject(FileSystem(), serialize_config_to_yaml)
        use_case.execute(Path.cwd())
        typer.echo(SUCCESS_MESSAGE)
    except InitProjectError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def lock() -> None:
    """Fetch prompts and update lock file without generating artifacts."""
    try:
        cwd = Path.cwd()
        fs = FileSystem()
        _make_lock_use_case(cwd, fs).execute(cwd)
        typer.echo("Locked promptkit.lock")
    except (PromptError, FileNotFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def build() -> None:
    """Generate platform-specific artifacts from cached prompts."""
    try:
        cwd = Path.cwd()
        fs = FileSystem()
        _make_build_use_case(cwd, fs).execute(cwd)
        typer.echo("Built platform artifacts")
    except (PromptError, FileNotFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def sync() -> None:
    """Fetch prompts, update lock file, and generate artifacts."""
    try:
        cwd = Path.cwd()
        fs = FileSystem()
        typer.echo("Locking prompts...")
        _make_lock_use_case(cwd, fs).execute(cwd)
        typer.echo("Building artifacts...")
        _make_build_use_case(cwd, fs).execute(cwd)
        typer.echo("Synced prompts and built artifacts")
    except (PromptError, FileNotFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def validate() -> None:
    """Verify config is well-formed and prompts exist."""
    cwd = Path.cwd()
    fs = FileSystem()
    result = _make_validate_use_case(fs).execute(cwd)

    for issue in result.issues:
        _echo_issue(issue)

    if result.is_valid:
        typer.echo("Config is valid")
    else:
        raise typer.Exit(code=1)


def _echo_issue(issue: ValidationIssue) -> None:
    """Print a validation issue with appropriate prefix and stream."""
    is_error = issue.level == LEVEL_ERROR
    prefix = "Error" if is_error else "Warning"
    typer.echo(f"{prefix}: {issue.message}", err=is_error)


if __name__ == "__main__":
    app()
