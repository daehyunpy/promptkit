## Why

The project is currently in planning phase with no code written. Before implementing promptkit's core features (sync, build, validate), we need a proper Python project foundation that follows DDD, TDD, and Clean Code principles. This establishes the structure, tooling, and development workflow that all future features will build upon.

## What Changes

- Create `pyproject.toml` with Python 3.13, uv dependency management, and dev tools (pytest, ruff, pyright)
- Scaffold `source/promptkit/` directory with DDD layer structure (domain, app, infra)
- Create `tests/` directory mirroring `source/` structure with pytest configuration
- Add `.env.example` for environment variables (if needed for future API integrations)
- Set up `.envrc.example` for direnv integration
- Configure tooling: pytest test discovery, pyright type checking, ruff linting
- Create initial `__init__.py` files to make packages importable
- Add a smoke test to verify the setup works (`uv sync`, `uv run pytest -x`)

## Capabilities

### New Capabilities
- `project-scaffold`: Python project structure with pyproject.toml, dependency management, directory layout following DDD layers, and basic tooling configuration

### Modified Capabilities
<!-- No existing capabilities to modify -->

## Impact

**New files:**
- `pyproject.toml` - Python project configuration
- `source/promptkit/__init__.py` - Main package entry point
- `source/promptkit/domain/__init__.py` - Domain layer package
- `source/promptkit/app/__init__.py` - Application layer package
- `source/promptkit/infra/__init__.py` - Infrastructure layer package
- `tests/conftest.py` - Pytest configuration
- `tests/__init__.py` - Test package marker
- `.env.example` - Environment variable template (if needed)
- `.envrc.example` - direnv configuration template

**Modified files:**
- `.gitignore` - May need updates for Python artifacts if not already comprehensive

**Dependencies:**
- Python 3.13+
- uv package manager
- Runtime: typer, pydantic-settings, pyyaml, httpx (for future features)
- Dev: pytest, ruff, pyright

**Systems affected:**
- Development workflow - establishes `uv sync` and `uv run pytest` patterns
- Project structure - sets DDD layer conventions for all future code
