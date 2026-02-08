## Context

The promptkit project is in pre-implementation phase with no code yet. We need to establish a Python project foundation that aligns with:
- DDD, TDD, and Clean Code principles (per AGENTS.md)
- Python 3.13 and modern uv package management
- Stack alignment with interactive-books project (typer, pydantic-settings, same dev tools)
- Three-layer architecture: domain → app → infra

This design establishes the foundation before implementing any promptkit features (init, sync, build, validate).

## Goals / Non-Goals

**Goals:**
- Create a minimal, working Python project with proper tooling
- Establish DDD layer structure that future code will follow
- Set up TDD infrastructure (pytest configuration, test directory structure)
- Align with interactive-books project's Python stack and conventions
- Enable `uv sync` and `uv run pytest -x` to work immediately
- Configure linting (ruff), formatting (ruff), and type checking (pyright)

**Non-Goals:**
- Implementing any promptkit CLI commands (init, sync, build, validate) - those come in later phases
- Creating domain models or business logic - focus is purely on project structure
- Adding database or external service integrations - those come later
- Creating end-to-end tests - just verify the scaffold works with a smoke test

## Decisions

### 1. Package Layout: `source/promptkit/` Structure

**Decision:** Use `source/promptkit/` as the package root with DDD layers as subpackages.

**Rationale:**
- Matches the structure defined in `docs/technical_design.md`
- Clear separation: source code in `source/`, tests in `tests/`
- Aligns with modern Python packaging (PEP 517/518)
- Makes imports explicit: `from promptkit.domain import ...`

**Alternatives considered:**
- Flat `promptkit/` at root - rejected because mixing source and project files gets messy
- `src/` instead of `source/` - rejected for consistency with technical design doc

**Structure:**
```
source/
└── promptkit/
    ├── __init__.py
    ├── domain/
    │   └── __init__.py
    ├── app/
    │   └── __init__.py
    └── infra/
        └── __init__.py
```

### 2. Test Directory: Mirror `source/` Structure

**Decision:** Tests in `tests/` directory that mirrors `source/promptkit/` structure.

**Rationale:**
- Follows pytest conventions and AGENTS.md guidelines
- Easy to locate test for any source file: `source/promptkit/domain/prompt.py` → `tests/domain/test_prompt.py`
- Separates test code from source code (clean packaging)

**Structure:**
```
tests/
├── __init__.py
├── conftest.py  # Shared fixtures
├── domain/
│   └── __init__.py
├── app/
│   └── __init__.py
└── infra/
    └── __init__.py
```

### 3. Dependency Management: uv with dependency-groups

**Decision:** Use `uv` with `[dependency-groups]` for dev dependencies (not `[project.optional-dependencies]`).

**Rationale:**
- Aligns with interactive-books project's pyproject.toml structure
- Modern uv convention (as of 2024+)
- Cleaner separation: `dependencies` for runtime, `dev` group for development tools
- Works with `uv sync` command (auto-installs all groups)

**pyproject.toml structure:**
```toml
[project]
dependencies = ["typer", "pydantic-settings", "pyyaml", "httpx"]

[dependency-groups]
dev = ["pytest", "ruff", "pyright"]
```

### 4. Runtime Dependencies: Minimal for Phase 1

**Decision:** Include typer, pydantic-settings, pyyaml, httpx in initial dependencies even though not used yet.

**Rationale:**
- These are confirmed requirements per technical design and AGENTS.md
- Including them now prevents churn (no need to update pyproject.toml in next phase)
- Verifies they install correctly and are compatible with Python 3.13
- Small size - no performance or bloat concerns

**Alternatives considered:**
- Wait until actually needed - rejected because these are certain requirements, adding them later is busywork
- Add only when first used - rejected because it breaks the "scaffold everything first" approach

### 5. Tool Configuration: In pyproject.toml

**Decision:** Configure pytest, pyright in pyproject.toml. Rely on ruff defaults.

**Rationale:**
- Single source of truth (no separate pytest.ini, pyproject.toml, setup.cfg)
- Aligns with interactive-books project conventions
- pyright needs venv path configuration for proper type checking

**Configuration:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.pyright]
pythonVersion = "3.13"
venvPath = "."
venv = ".venv"
```

### 6. Environment Variables: Optional for Phase 1

**Decision:** Create `.env.example` and `.envrc.example` even though no env vars needed yet.

**Rationale:**
- Future-proofs for when we add API integrations (Claude marketplace, GitHub)
- Establishes the pattern: "use direnv for env vars"
- Minimal cost (2 small example files)
- Aligns with interactive-books project pattern

**Content:**
- `.env.example`: Empty or placeholder comments for future API keys
- `.envrc.example`: `dotenv` command for direnv

### 7. Initial Smoke Test

**Decision:** Create `tests/test_smoke.py` that verifies imports work.

**Rationale:**
- Confirms the package structure is valid
- Verifies pytest can discover and run tests
- Provides immediate feedback that `uv sync` and `uv run pytest -x` work
- TDD foundation: green test before any real code

**Test content:**
```python
def test_package_imports():
    """Verify the package structure is importable."""
    import promptkit
    import promptkit.domain
    import promptkit.app
    import promptkit.infra
    assert True
```

### 8. Entry Point Configuration

**Decision:** Add `[project.scripts]` entry point in pyproject.toml, but don't create the CLI module yet.

**Rationale:**
- Declares the intention: `promptkit` command will exist
- Documents the entry point for future implementation
- Doesn't require creating actual CLI code yet (deferred to next phase)
- Consistent with technical design: `promptkit.cli:app`

**Configuration:**
```toml
[project.scripts]
promptkit = "promptkit.cli:app"
```

**Note:** The `cli.py` module will be created in a later phase when implementing actual commands.

## Risks / Trade-offs

**[Risk: Package importability issues]**
- Mitigation: The smoke test catches this immediately. If imports fail, pytest will error.

**[Risk: Python 3.13 compatibility issues with dependencies]**
- Mitigation: All chosen dependencies (typer, pydantic-settings, pyyaml, httpx) have Python 3.13 support. `uv sync` will fail fast if there are issues.

**[Risk: Tool version skew between projects]**
- Mitigation: Using same tools as interactive-books. Lock file (`uv.lock`) ensures reproducibility.

**[Trade-off: Including unused dependencies]**
- We're adding typer, pydantic-settings, pyyaml, httpx even though they won't be imported until later phases
- Benefit: Prevents churn, verifies compatibility early
- Cost: Minimal (small libraries, no runtime overhead since nothing executes yet)

**[Trade-off: Empty env var files]**
- Creating `.env.example` with no actual env vars yet
- Benefit: Establishes pattern, one less thing to remember later
- Cost: Two nearly-empty files in the repo

## Migration Plan

**Deployment:**
1. Merge PR with project scaffold
2. All developers run: `uv sync` (creates venv, installs deps)
3. Verify: `uv run pytest -x` (should pass smoke test)
4. Verify: `uv run ruff check .` and `uv run pyright` (should pass with no errors)

**Rollback:**
- Not applicable (no production system yet)
- If scaffold is broken, revert commit and fix before re-merging

**Validation:**
- CI should run: `uv sync`, `uv run pytest -x`, `uv run ruff check .`, `uv run pyright`
- All checks must pass before merge

## Open Questions

None. All decisions are based on constraints from AGENTS.md, technical design, and alignment with interactive-books project.
