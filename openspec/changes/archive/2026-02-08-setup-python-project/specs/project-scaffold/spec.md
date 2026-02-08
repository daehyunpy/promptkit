## ADDED Requirements

### Requirement: Project structure follows DDD layers
The project SHALL use a three-layer architecture with domain, app, and infra layers under `source/promptkit/`.

#### Scenario: DDD layer directories exist
- **WHEN** the project is scaffolded
- **THEN** `source/promptkit/domain/`, `source/promptkit/app/`, and `source/promptkit/infra/` directories exist with `__init__.py` files

#### Scenario: Layers are importable
- **WHEN** importing from any layer
- **THEN** `import promptkit.domain`, `import promptkit.app`, and `import promptkit.infra` succeed without errors

### Requirement: Test structure mirrors source structure
The project SHALL have a `tests/` directory that mirrors the structure of `source/promptkit/`.

#### Scenario: Test directories match source layers
- **WHEN** the project is scaffolded
- **THEN** `tests/domain/`, `tests/app/`, and `tests/infra/` directories exist with `__init__.py` files

#### Scenario: Pytest can discover tests
- **WHEN** running `uv run pytest`
- **THEN** pytest discovers the tests directory and can run tests from it

### Requirement: Dependencies are declared in pyproject.toml
The project SHALL declare all runtime and development dependencies in `pyproject.toml` using modern uv conventions.

#### Scenario: Runtime dependencies are listed
- **WHEN** examining `pyproject.toml`
- **THEN** `[project.dependencies]` includes typer, pydantic-settings, pyyaml, and httpx

#### Scenario: Dev dependencies use dependency-groups
- **WHEN** examining `pyproject.toml`
- **THEN** `[dependency-groups]` section includes dev group with pytest, ruff, and pyright

#### Scenario: Dependencies install successfully
- **WHEN** running `uv sync`
- **THEN** all dependencies install without errors and a `.venv` directory is created

### Requirement: Python 3.13 is required
The project SHALL require Python 3.13 or higher.

#### Scenario: Python version is declared
- **WHEN** examining `pyproject.toml`
- **THEN** `requires-python = ">=3.13"` is specified

### Requirement: Tools are configured in pyproject.toml
The project SHALL configure pytest and pyright in `pyproject.toml`.

#### Scenario: Pytest knows where tests are
- **WHEN** examining `pyproject.toml`
- **THEN** `[tool.pytest.ini_options]` specifies `testpaths = ["tests"]`

#### Scenario: Pyright knows about venv
- **WHEN** examining `pyproject.toml`
- **THEN** `[tool.pyright]` specifies `pythonVersion = "3.13"`, `venvPath = "."`, and `venv = ".venv"`

### Requirement: CLI entry point is declared
The project SHALL declare a `promptkit` command entry point in `pyproject.toml`.

#### Scenario: Entry point is configured
- **WHEN** examining `pyproject.toml`
- **THEN** `[project.scripts]` includes `promptkit = "promptkit.cli:app"`

### Requirement: Environment variable support is established
The project SHALL provide example files for environment variable configuration.

#### Scenario: Env example file exists
- **WHEN** the project is scaffolded
- **THEN** `.env.example` file exists as a template for environment variables

#### Scenario: Direnv example file exists
- **WHEN** the project is scaffolded
- **THEN** `.envrc.example` file exists with direnv configuration

### Requirement: Package structure is verified with smoke test
The project SHALL include a smoke test that verifies the package structure is importable.

#### Scenario: Smoke test exists
- **WHEN** examining the test directory
- **THEN** `tests/test_smoke.py` exists

#### Scenario: Smoke test verifies imports
- **WHEN** running `uv run pytest tests/test_smoke.py`
- **THEN** the test imports `promptkit`, `promptkit.domain`, `promptkit.app`, and `promptkit.infra` successfully

#### Scenario: All tests pass on fresh setup
- **WHEN** running `uv sync` followed by `uv run pytest -x` on a fresh clone
- **THEN** all tests pass with no errors

### Requirement: Linting and type checking work out of the box
The project SHALL be configured so that linting and type checking tools work immediately after setup.

#### Scenario: Ruff linting succeeds
- **WHEN** running `uv run ruff check .`
- **THEN** the command completes with no linting errors

#### Scenario: Pyright type checking succeeds
- **WHEN** running `uv run pyright`
- **THEN** the command completes with no type errors

### Requirement: Project metadata is defined
The project SHALL have proper metadata in `pyproject.toml`.

#### Scenario: Project name and version are set
- **WHEN** examining `pyproject.toml`
- **THEN** `[project]` section includes `name = "promptkit"` and `version = "0.1.0"`

#### Scenario: Build system is configured
- **WHEN** examining `pyproject.toml`
- **THEN** `[build-system]` specifies hatchling as the build backend
