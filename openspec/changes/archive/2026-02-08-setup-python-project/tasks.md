## 1. Create pyproject.toml

- [x] 1.1 Create `pyproject.toml` with project metadata (name="promptkit", version="0.1.0")
- [x] 1.2 Add Python version requirement (requires-python = ">=3.13")
- [x] 1.3 Add runtime dependencies (typer, pydantic-settings, pyyaml, httpx)
- [x] 1.4 Add dev dependency group with pytest, ruff, and pyright
- [x] 1.5 Configure pytest in [tool.pytest.ini_options] with testpaths = ["tests"]
- [x] 1.6 Configure pyright in [tool.pyright] with pythonVersion, venvPath, and venv
- [x] 1.7 Add CLI entry point in [project.scripts]: promptkit = "promptkit.cli:app"
- [x] 1.8 Configure build system with hatchling backend
- [x] 1.9 Add [tool.hatch.build.targets.wheel] with packages = ["source/promptkit"]

## 2. Create source directory structure

- [x] 2.1 Create `source/promptkit/` directory
- [x] 2.2 Create `source/promptkit/__init__.py` (main package entry point)
- [x] 2.3 Create `source/promptkit/domain/` directory with `__init__.py`
- [x] 2.4 Create `source/promptkit/app/` directory with `__init__.py`
- [x] 2.5 Create `source/promptkit/infra/` directory with `__init__.py`

## 3. Create test directory structure

- [x] 3.1 Create `tests/` directory
- [x] 3.2 Create `tests/__init__.py` (test package marker)
- [x] 3.3 Create `tests/conftest.py` for shared pytest fixtures (can be empty initially)
- [x] 3.4 Create `tests/domain/` directory with `__init__.py`
- [x] 3.5 Create `tests/app/` directory with `__init__.py`
- [x] 3.6 Create `tests/infra/` directory with `__init__.py`

## 4. Create smoke test

- [x] 4.1 Create `tests/test_smoke.py` with test_package_imports function
- [x] 4.2 Add imports for promptkit, promptkit.domain, promptkit.app, promptkit.infra in the test
- [x] 4.3 Verify test structure follows pytest conventions

## 5. Create environment variable templates

- [x] 5.1 Create `.env.example` with placeholder comments for future API keys
- [x] 5.2 Create `.envrc.example` with dotenv command for direnv integration

## 6. Verify setup works

- [x] 6.1 Run `uv sync` to install dependencies and create virtual environment
- [x] 6.2 Run `uv run pytest -x` to verify smoke test passes
- [x] 6.3 Run `uv run ruff check .` to verify no linting errors
- [x] 6.4 Run `uv run pyright` to verify no type errors
- [x] 6.5 Verify all package imports work (promptkit, promptkit.domain, promptkit.app, promptkit.infra)

## 7. Update .gitignore if needed

- [x] 7.1 Check if `.gitignore` has comprehensive Python entries (already exists, verify it's complete)
- [x] 7.2 Ensure `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/` are gitignored
- [x] 7.3 Ensure `.env` (not .env.example) is gitignored
