## Why

The Python project foundation is now in place. Users need a way to scaffold a new promptkit project with the correct directory structure and configuration files. The `promptkit init` command is the entry point for users to start using promptkit - without it, they must manually create the structure.

## What Changes

- Implement `promptkit init` CLI command using typer
- Create application layer use case: `InitProject`
- Scaffold directory structure: `.promptkit/cache/`, `.agents/`, `.cursor/`, `.claude/`
- Generate `promptkit.yaml` template with example configuration
- Generate `promptkit.lock` (empty initially, populated by sync)
- Add `.gitignore` entries for promptkit-specific paths
- Display success message with next steps
- Exit with appropriate status codes (0 for success, 1 for errors)

## Capabilities

### New Capabilities
- `cli-init-command`: CLI command that scaffolds a new promptkit project with directory structure, config files, and gitignore entries

### Modified Capabilities
<!-- No existing capabilities to modify -->

## Impact

**New files:**
- `source/promptkit/cli.py` - CLI entry point with typer app and init command
- `source/promptkit/app/init.py` - InitProject use case (orchestrates initialization)
- `source/promptkit/domain/project_config.py` - ProjectConfig value object for promptkit.yaml structure
- `source/promptkit/infra/file_system.py` - File system operations (create dirs, write files)
- `tests/test_cli.py` - CLI command tests
- `tests/app/test_init.py` - InitProject use case tests
- `tests/domain/test_project_config.py` - ProjectConfig tests

**Modified files:**
- None (pure addition)

**Dependencies:**
- Uses existing: typer (CLI framework)
- Uses existing: pyyaml (for generating promptkit.yaml)
- No new dependencies required

**Systems affected:**
- User workflow: Provides entry point for new promptkit projects
- File system: Creates directories and files in current working directory
- Git: Adds/updates .gitignore with promptkit-specific entries
