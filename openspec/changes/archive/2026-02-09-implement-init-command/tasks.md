## 1. Create domain layer: ProjectConfig value object

- [x] 1.1 Create `source/promptkit/domain/project_config.py`
- [x] 1.2 Define ProjectConfig dataclass with version, prompts, platforms fields
- [x] 1.3 Implement `ProjectConfig.default()` class method returning default configuration
- [x] 1.4 Implement `to_yaml_string()` method for YAML serialization
- [x] 1.5 Create `tests/domain/test_project_config.py` with tests for default config
- [x] 1.6 Add test for YAML serialization (verify output contains required fields)

## 2. Create infrastructure layer: File system operations

- [x] 2.1 Create `source/promptkit/infra/file_system.py`
- [x] 2.2 Define FileSystemProtocol with create_directory, write_file, file_exists, append_to_file methods
- [x] 2.3 Implement LocalFileSystem class implementing FileSystemProtocol
- [x] 2.4 Create `tests/infra/test_file_system.py` with tests for LocalFileSystem
- [x] 2.5 Test create_directory creates nested directories (parents=True, exist_ok=True)
- [x] 2.6 Test write_file creates file with content
- [x] 2.7 Test file_exists returns True/False correctly
- [x] 2.8 Test append_to_file appends content to existing file

## 3. Create application layer: InitProject use case

- [x] 3.1 Create `source/promptkit/app/init.py`
- [x] 3.2 Define InitProject class with __init__(file_system: FileSystemProtocol)
- [x] 3.3 Implement execute(target_dir: Path) method
- [x] 3.4 Add logic to check if promptkit.yaml exists (raise error if yes)
- [x] 3.5 Add logic to create directories (.promptkit/cache/, .agents/, .cursor/, .claude/)
- [x] 3.6 Add logic to generate and write promptkit.yaml using ProjectConfig
- [x] 3.7 Add logic to create empty promptkit.lock file
- [x] 3.8 Add logic to add/update .gitignore with .promptkit/cache/ entry
- [x] 3.9 Create `tests/app/test_init.py` with tests for InitProject use case
- [x] 3.10 Test execute creates all required directories
- [x] 3.11 Test execute generates valid promptkit.yaml
- [x] 3.12 Test execute creates promptkit.lock
- [x] 3.13 Test execute fails when promptkit.yaml already exists
- [x] 3.14 Test .gitignore is created/updated correctly

## 4. Create CLI layer: promptkit init command

- [x] 4.1 Create `source/promptkit/cli.py`
- [x] 4.2 Import typer and create app = typer.Typer()
- [x] 4.3 Define init() command function with @app.command() decorator
- [x] 4.4 Add docstring: "Initialize a new promptkit project."
- [x] 4.5 Implement init() to instantiate InitProject with LocalFileSystem
- [x] 4.6 Call execute(Path.cwd()) to init in current directory
- [x] 4.7 Handle exceptions and print error messages
- [x] 4.8 Print success message with next steps and created files list
- [x] 4.9 Exit with appropriate status code (0 success, 1 error)
- [x] 4.10 Create `tests/test_cli.py` with CLI tests
- [x] 4.11 Test init command can be invoked (use typer.testing.CliRunner)
- [x] 4.12 Test init command shows help text
- [x] 4.13 Test init command creates expected files and directories
- [x] 4.14 Test init command fails when promptkit.yaml exists
- [x] 4.15 Test success message is displayed
- [x] 4.16 Test exit code is 0 on success, 1 on failure

## 5. Verify integration

- [x] 5.1 Run `uv run pytest -x` to verify all tests pass
- [x] 5.2 Run `uv run ruff check .` to verify no linting errors
- [x] 5.3 Run `uv run pyright` to verify no type errors
- [x] 5.4 Manually test: `uv run promptkit init` in temp directory
- [x] 5.5 Verify all directories and files are created
- [x] 5.6 Verify promptkit.yaml is valid YAML with correct structure
- [x] 5.7 Verify running `uv run promptkit init` twice fails appropriately
- [x] 5.8 Verify success message is helpful and accurate
