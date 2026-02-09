# AGENTS.md

Instructions for AI agents working on this codebase. `CLAUDE.md` is a symlink to this file — edit here, not there.

## Project

**promptkit** — a package manager for AI prompts. Syncs high-quality prompts from sources like Claude plugin marketplace, stores them in a declarative format, and generates platform-specific artifacts for Cursor and Claude Code.

## Key Docs

- `docs/product_requirements.md` — what to build and why
- `docs/technical_design.md` — how to build it (architecture, DDD layers, schemas, build process)

Read both before making changes.

## Current State

**Phases 1-4 complete.** Domain model and config loading implemented. 111 tests passing.

**Completed:**
- Phase 1-2: Project scaffold + `promptkit init` command
- Phase 3: Domain model (Prompt, PromptSpec, LockEntry, PlatformTarget, ArtifactType, errors, protocols)
- Phase 4: Config loading (YamlLoader, LockFile reader/writer)

**Next Steps:**
- Phase 5: Lock command (LocalFileFetcher, PromptCache, LockPrompts use case)
- Phase 6: Build command (CursorBuilder, ClaudeBuilder, BuildArtifacts use case)
- Phase 7: Sync command (compose lock + build)
- Phase 8: Validate command

## Tech Stack

- **Language**: Python 3.13
- **Package Manager**: uv
- **CLI Framework**: typer (modern type-safe CLI)
- **Config Format**: YAML (promptkit.yaml)
- **Config Management**: pydantic-settings
- **Target Platforms**: Cursor (`.cursor/`), Claude Code (`.claude/`)

## Development Setup

```bash
# Requires Python 3.13+ and uv package manager
# Install uv: https://docs.astral.sh/uv/

# Create virtual environment and install dependencies (when pyproject.toml exists)
uv sync                      # Install all dependencies including dev

# (Optional) Environment variables - if needed
cp .env.example .env         # Create .env file
direnv allow                 # Load environment variables (requires direnv)
```

## Common Commands

```bash
# Run tests (TDD workflow)
uv run pytest -x             # Run tests, stop on first failure
uv run pytest -v             # Verbose output
uv run pytest tests/domain/  # Run specific test directory
uv run pytest -k test_name   # Run tests matching name pattern

# Type checking
uv run pyright               # Type check all code

# Linting and formatting
uv run ruff check .          # Check for issues
uv run ruff format .         # Auto-format code
uv run ruff check --fix .    # Auto-fix issues
```

## Project Structure

```
promptkit/
├── docs/
│   └── product_requirements.md    # Product requirements
├── source/
│   └── promptkit/
│       ├── __init__.py
│       ├── cli.py                  # CLI entry point
│       ├── domain/                 # Domain layer (pure business logic)
│       │   ├── prompt.py           # Prompt aggregate root
│       │   ├── prompt_spec.py      # PromptSpec value object + ArtifactType enum
│       │   ├── prompt_metadata.py  # PromptMetadata value object
│       │   ├── lock_entry.py       # LockEntry value object
│       │   ├── platform_target.py  # PlatformTarget enum
│       │   ├── errors.py           # Domain errors
│       │   └── protocols.py        # PromptFetcher, ArtifactBuilder protocols
│       ├── app/                    # Application layer (use cases)
│       │   ├── init.py             # Init use case
│       │   ├── lock.py             # Lock use case (fetch + lock)
│       │   ├── build.py            # Build use case (cache → artifacts)
│       │   └── validate.py         # Validate use case
│       └── infra/                  # Infrastructure layer (adapters)
│           ├── config/             # Config loading
│           ├── fetchers/           # Prompt fetchers
│           ├── builders/           # Platform artifact builders
│           └── storage/            # Cache management
├── tests/                          # Tests mirror source/ structure
├── pyproject.toml                  # Python project config
├── uv.lock                         # Locked dependencies
├── promptkit.yaml                  # Example/template config
├── .promptkit/
│   └── cache/                      # Cached upstream prompts (gitignored)
├── .agents/                        # Canonical prompts (committed)
├── .cursor/                        # Generated Cursor artifacts
└── .claude/                        # Generated Claude Code artifacts
```

## MVP Commands

| Command | What it does | Needs network |
|---------|--------------|---------------|
| `promptkit init` | Scaffold new project structure | No |
| `promptkit sync` | Fetch + lock + build (the one-stop command) | Yes |
| `promptkit lock` | Fetch + update lockfile only | Yes |
| `promptkit build` | Generate artifacts from cached prompts | No |
| `promptkit validate` | Verify config is well-formed and prompts exist | No |

## Core Workflow

1. **Init** - `promptkit init` scaffolds project with config and directories
2. **Configure** - Edit `promptkit.yaml` to declare prompts and platforms
3. **Sync** - `promptkit sync` fetches, locks, and builds everything
4. **Define** - Write canonical prompts in `.agents/`
5. **Rebuild** - `promptkit build` regenerates artifacts without re-fetching

## Coding Disciplines

This project follows three disciplines: **DDD**, **TDD**, and **Clean Code**. These govern how every line of code is written, not just how folders are organized.

### DDD (Domain-Driven Design)

- **Ubiquitous language** — use domain terms consistently. A `Prompt` is a `Prompt`, not a `Template` or `Config`. A `PromptSpec` is a `PromptSpec`, not a `Definition` or `Manifest`. If the domain term changes, rename everywhere.
- **Entities vs Value Objects** — entities have identity (`Prompt` has an ID, persists, tracks state). Value objects are immutable data with no identity (`PromptMetadata`, `PlatformTarget`, `LockEntry`). Don't give value objects IDs.
- **Aggregates** — `Prompt` is an aggregate root. Access its metadata and content through `Prompt`, not independently. Don't let outside code reach into aggregate internals.
- **Domain logic in domain objects** — not in CLI handlers or builder code. If you're writing an `if` about prompt state in a command handler, it belongs in the domain layer.

  **Example:**
  ```python
  # ✅ Good: Domain logic in domain object
  # In domain/prompt.py
  class Prompt:
      def is_valid_for_platform(self, platform: PlatformTarget) -> bool:
          return platform in self.spec.platforms

  # ❌ Bad: Domain logic in CLI handler
  # In cli.py
  if prompt.spec.platforms and platform in prompt.spec.platforms:
      ...  # This logic should be in Prompt class
  ```

- **Domain layer has no outward dependencies** — domain code never imports infrastructure (file I/O, HTTP clients, YAML parsers). It depends only on protocols/interfaces.
- **Domain errors** — use `PromptError`, `SyncError`, `BuildError`, `ValidationError`. Let them propagate to the application layer.

### TDD (Test-Driven Development)

- **Red → Green → Refactor** — every feature and bug fix starts with a failing test.
- **Test naming** — describe behavior: `test_build_generates_cursor_artifacts`, not `test_build_method`.
- **Test structure** — Arrange-Act-Assert. One assertion per test where practical.
- **Unit tests** — domain logic in isolation, mock infrastructure. **Integration tests** — verify adapters work with real dependencies. **No tests for trivial code** — don't test getters, data classes, or framework glue.
- **Test location** — tests live in a separate `tests/` directory that mirrors the `source/` structure (e.g., `tests/domain/test_prompt.py` tests `source/promptkit/domain/prompt.py`).
- **Protocols enable testing** — every protocol (`PromptFetcher`, `ArtifactBuilder`, etc.) should have a test double.

### Clean Code

- **Naming** — names reveal intent. `fetch_prompt_from_source(source)` not `get(s)`. Booleans read as assertions: `is_valid`, `has_lock_file`.
- **Functions** — do one thing. If it has "and" in its description, split it. Aim for < 20 lines.
- **No dead code** — no commented-out code, no unused imports. Delete it; git remembers.
- **No magic values** — `DEFAULT_CACHE_DIR = ".promptkit/cache"`, not bare `".promptkit/cache"`.
- **Dependency direction** — CLI → App → Domain ← Infra. Never reverse.
- **Single level of abstraction** — high-level functions call named functions; don't mix orchestration with details.
- **Early return** — guard clauses over nested `if/else`.
- **Immutability by default** — avoid mutation where practical (Python).

## What NOT to Do

**Product Scope:**
- Don't add a web UI or GUI — CLI only
- Don't add analytics, telemetry, or usage tracking
- Don't add A/B testing or prompt optimization features
- Don't add SaaS hosting or cloud service
- Don't add version pinning in v1 — always sync latest
- Don't add composition layers in v1 — that's post-MVP
- Don't support platforms beyond Cursor and Claude Code in v1

**Code Quality:**
- Don't write code without a failing test first
- Don't put domain logic in CLI handlers or builder code
- Don't let domain code import infrastructure modules
- Don't leave dead code, commented-out code, or unused imports
- Don't use magic numbers or strings — name them

## Git Workflow

- **`main`** — production-ready code
- **`develop`** — integration branch (if needed)
- **Feature branches** — `feature/<name>` off main/develop
- **Commit style** — conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- **Keep commits focused** — one logical change per commit
- **No direct pushes** to `main` or `develop`

## Success Criteria

The MVP is complete when:

1. Can sync a prompt from Claude plugin marketplace
2. Can build artifacts for both Cursor and Claude Code
3. Same config produces identical outputs (deterministic builds)
4. Lock file ensures reproducibility
5. Can use multiple prompts in a single project
6. Validation catches config errors before build
7. Init command scaffolds project structure

## OpenSpec

This project uses OpenSpec for spec-driven development. All non-trivial changes go through this workflow. Trivial fixes (typos, single-line bugs) can skip it.

| Step | Command | What it does |
|------|---------|--------------|
| 1 | `/opsx:new <name>` | Create a new change with a kebab-case name (e.g., `/opsx:new add-sync-command`) |
| 2 | `/opsx:ff` | Generate all spec artifacts (requirements, design, tasks) in one pass |
| 3 | `/opsx:apply` | Implement the tasks from the generated spec |
| 4 | `/opsx:verify` | Verify implementation matches the spec artifacts |
| 5 | `/opsx:archive` | Archive the completed change |

Artifacts are stored in `openspec/changes/` during development and moved to `openspec/changes/archive/` when done.

## Resolved Questions

- **CLI framework**: typer (modern type-safe CLI)
- **Fetch from Claude marketplace**: GitHub-hosted registries, stub fetcher for initial phases (needs research)
- **Lock file format**: YAML (`promptkit.lock`)
- **Prompt metadata**: YAML frontmatter (author, description, artifact_type)
- **Platform-specific mapping**: artifact_type from frontmatter routes to platform subdirectories (deterministic copy, no transformation)
- **`.cursor/` and `.claude/` gitignored?**: Recommended to gitignore but user's choice
- **Frontmatter required?**: artifact_type is optional — prompts without it default to `skill`
- **Frontmatter in build output?**: Stripped for platforms that don't need it; each builder decides
- **Error handling**: Fail fast with clear messages, no retries for MVP
- **Local prompt source in lock file**: source = `local/<filename>`
