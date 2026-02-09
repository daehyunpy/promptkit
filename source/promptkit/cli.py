"""CLI interface for promptkit."""

from pathlib import Path

import typer

from promptkit.app.init import InitProject, InitProjectError
from promptkit.infra.config_serializer import serialize_config_to_yaml
from promptkit.infra.file_system.local import FileSystem

app = typer.Typer(help="Package manager for AI prompts")

SUCCESS_MESSAGE = """\
✓ Initialized promptkit project

Created files and directories:
  - promptkit.yaml (project configuration)
  - promptkit.lock (dependency lock file)
  - .promptkit/cache/ (cached prompts)
  - .agents/ (canonical prompts)
  - .cursor/ (Cursor artifacts)
  - .claude/ (Claude Code artifacts)
  - .gitignore (updated with cache exclusions)

Next steps:
  1. Edit promptkit.yaml to configure prompts
  2. Run 'promptkit sync' to fetch prompts
  3. Run 'promptkit build' to generate artifacts\
"""


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


if __name__ == "__main__":
    app()
