# AGENTS.md

Instructions for AI agents working on this codebase. `CLAUDE.md` is a symlink to this file — edit here, not there.

## Project

**promptkit** — a package manager for AI prompts. Syncs high-quality prompts from sources like Claude plugin marketplace, stores them in a declarative format, and generates platform-specific artifacts for Cursor and Claude Code.

## Key Docs

- `docs/product_requirements.md` — what to build and why
- `docs/technical_design.md` — how to build it (architecture, DDD layers, schemas, build process)

Read both before making changes.

## Current State

**MVP phases 1-8 complete (local-only). Phase 9 (registry fetcher) in progress.** 243 tests passing.

**Completed:**
- Phase 1-2: Project scaffold + `promptkit init` command
- Phase 3: Domain model (Prompt, PromptSpec, LockEntry, Registry, PlatformConfig, PlatformTarget, errors, protocols)
- Phase 4: Config loading (YamlLoader, LockFile reader/writer)
- Phase 5: Lock command (LocalFileFetcher, PromptCache, LockPrompts use case, `promptkit lock` CLI)
- Phase 6: Build command (CursorBuilder, ClaudeBuilder, BuildArtifacts use case)
- Phase 7: Sync command (compose lock + build)
- Phase 8: Validate command

**In Progress — Phase 9: Claude Marketplace Fetcher** (`openspec/changes/claude-marketplace-fetcher/`)
- Unified `Plugin` model replaces `Prompt` — both local and registry plugins are file trees on disk
- `PluginFetcher` protocol replaces `PromptFetcher` — single abstraction for local + registry
- `ClaudeMarketplaceFetcher` — downloads full plugin directories from GitHub via Contents API
- `PluginCache` — directory-based cache keyed by `{registry}/{plugin}/{commit_sha}/`
- `LocalPluginFetcher` — replaces `LocalFileFetcher`, supports multi-file directories + non-md files
- `LockEntry` gains `commit_sha` field for registry plugins
- Builders copy file trees (not string content) with directory mapping
- Removes: `Prompt`, `PromptFetcher`, `PromptCache`
- See `openspec/changes/claude-marketplace-fetcher/tasks.md` for full task list (14 groups, ~70 subtasks)

## Tech Stack

- **Language**: Python 3.13
- **Package Manager**: uv
- **CLI Framework**: typer (modern type-safe CLI)
- **Config Format**: YAML (promptkit.yaml)
- **Config Management**: pydantic-settings
- **Target Platforms**: Cursor (`.cursor/`), Claude Code (`.claude/`)

## Development Setup

```bash
# Prerequisites
# - Python 3.13+: https://www.python.org/downloads/
# - uv: https://docs.astral.sh/uv/
# - bun: https://bun.sh/
# - direnv: https://direnv.net/ (optional but recommended)

# 1. Install Python dependencies
uv sync                      # Install all dependencies including dev

# 2. Install OpenSpec CLI (spec-driven development tool)
bun install                  # Installs openspec CLI to node_modules/.bin

# 3. Setup environment (recommended)
cp .envrc.example .envrc     # Copy environment template
cp .env.example .env         # Copy config template (if needed)

# If direnv hook is set up in your shell (~/.bashrc or ~/.zshrc):
#   eval "$(direnv hook bash)"  # or zsh, fish, etc.
# Then direnv will auto-prompt, or run:
direnv allow                 # Explicitly allow .envrc to load

# If direnv hook is NOT set up, manually load for current shell:
eval "$(direnv export bash)" # Load .envrc (bash/zsh/fish)

# What .envrc does:
# - Activates Python virtual environment (.venv)
# - Adds node_modules/.bin to PATH (for openspec CLI)
# - Loads variables from .env file

# Alternative: Manual activation (if not using direnv at all)
source .venv/bin/activate
export PATH="$PWD/node_modules/.bin:$PATH"
```

## Common Commands

```bash
# Assumes .envrc is active (venv activated, PATH configured)
# If direnv isn't working, prefix commands with `uv run`

# Run tests (TDD workflow)
pytest -x                    # Run tests, stop on first failure
pytest -v                    # Verbose output
pytest tests/domain/         # Run specific test directory
pytest -k test_name          # Run tests matching name pattern

# Type checking
pyright                      # Type check all code

# Linting and formatting
ruff check .                 # Check for issues
ruff format .                # Auto-format code
ruff check --fix .           # Auto-fix issues
```

## Project Structure

```
promptkit/
├── docs/
│   ├── product_requirements.md       # Product requirements
│   ├── technical_design.md           # Architecture + schemas
│   └── references/                   # Upstream specs (tracked with commit SHAs)
│       ├── claude-marketplace-spec.md
│       ├── claude-code-directory-spec.md
│       └── cursor-directory-spec.md
├── source/
│   └── promptkit/
│       ├── __init__.py
│       ├── cli.py                    # CLI entry point
│       ├── domain/                   # Domain layer (pure business logic)
│       │   ├── plugin.py            # Plugin value object (unified model)
│       │   ├── prompt.py            # Prompt aggregate (being replaced by Plugin)
│       │   ├── prompt_spec.py       # PromptSpec value object
│       │   ├── lock_entry.py        # LockEntry value object (+commit_sha)
│       │   ├── platform_target.py   # PlatformTarget enum
│       │   ├── errors.py            # Domain errors
│       │   └── protocols.py         # PluginFetcher, ArtifactBuilder protocols
│       ├── app/                     # Application layer (use cases)
│       │   ├── init.py              # Init use case
│       │   ├── lock.py              # Lock use case (fetch + lock)
│       │   ├── build.py             # Build use case (cache → artifacts)
│       │   └── validate.py          # Validate use case
│       └── infra/                   # Infrastructure layer (adapters)
│           ├── config/              # Config loading
│           ├── fetchers/            # Plugin fetchers (local + marketplace)
│           ├── builders/            # Platform artifact builders
│           └── storage/             # Cache management (PluginCache)
├── tests/                           # Tests mirror source/ structure
├── openspec/                        # Spec-driven development artifacts
│   └── changes/                     # Active changes
├── pyproject.toml                   # Python project config
├── uv.lock                          # Locked dependencies
├── promptkit.yaml                   # Example/template config
├── .promptkit/
│   └── cache/
│       └── plugins/                 # Registry plugin cache ({reg}/{name}/{sha}/)
├── prompts/                         # Local plugins (committed, can be dirs)
├── .cursor/                         # Generated Cursor artifacts
└── .claude/                         # Generated Claude Code artifacts
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
4. **Define** - Write local prompts in `prompts/`
5. **Rebuild** - `promptkit build` regenerates artifacts without re-fetching

## Coding Disciplines

This project follows three disciplines: **DDD**, **TDD**, and **Clean Code**. These govern how every line of code is written, not just how folders are organized.

### DDD (Domain-Driven Design)

- **Ubiquitous language** — use domain terms consistently. A `Plugin` is a `Plugin`, not a `Template` or `Config`. A `PromptSpec` is a `PromptSpec`, not a `Definition` or `Manifest`. If the domain term changes, rename everywhere.
- **Entities vs Value Objects** — value objects are immutable data with no identity (`Plugin`, `PromptSpec`, `PlatformTarget`, `LockEntry`). Don't give value objects IDs.
- **Domain logic in domain objects** — not in CLI handlers or builder code. If you're writing an `if` about plugin state in a command handler, it belongs in the domain layer.

  **Example:**
  ```python
  # ✅ Good: Domain logic in domain object
  # In domain/plugin.py
  class Plugin:
      @property
      def is_registry(self) -> bool:
          return self.commit_sha is not None

  # ❌ Bad: Domain logic in CLI handler
  # In cli.py
  if plugin.commit_sha is not None:
      ...  # This logic should be in Plugin class
  ```

- **Domain layer has no outward dependencies** — domain code never imports infrastructure (file I/O, HTTP clients, YAML parsers). It depends only on protocols/interfaces.
- **Domain errors** — use `PromptError`, `SyncError`, `BuildError`, `ValidationError`. Let them propagate to the application layer.

### TDD (Test-Driven Development)

- **Red → Green → Refactor** — every feature and bug fix starts with a failing test.
- **Test naming** — describe behavior: `test_build_generates_cursor_artifacts`, not `test_build_method`.
- **Test structure** — Arrange-Act-Assert. One assertion per test where practical.
- **Unit tests** — domain logic in isolation, mock infrastructure. **Integration tests** — verify adapters work with real dependencies. **No tests for trivial code** — don't test getters, data classes, or framework glue.
- **Test location** — tests live in a separate `tests/` directory that mirrors the `source/` structure (e.g., `tests/domain/test_prompt.py` tests `source/promptkit/domain/prompt.py`).
- **Protocols enable testing** — every protocol (`PluginFetcher`, `ArtifactBuilder`, etc.) should have a test double.

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

1. Can sync a plugin from Claude marketplace (registry fetcher + cache + lock)
2. Can build artifacts for both Cursor and Claude Code (copy file trees with directory mapping)
3. Same config produces identical outputs (deterministic builds via commit SHA + lock file)
4. Lock file ensures reproducibility (commit SHA for registry, content hash for local)
5. Can use multiple plugins in a single project (local + registry)
6. Local plugins support multi-file directories (not just single .md)
7. Validation catches config errors before build
8. Init command scaffolds project structure

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
- **Fetch from Claude marketplace**: GitHub Contents API, `marketplace.json` manifest, full directory download
- **Lock file format**: YAML (`promptkit.lock`)
- **Prompt metadata**: YAML frontmatter (author, description) — optional, informational only
- **Platform-specific mapping**: directory-based routing (source category dir → platform output dir), no artifact_type needed
- **`.cursor/` and `.claude/` gitignored?**: Recommended to gitignore but user's choice
- **Frontmatter required?**: No — frontmatter is optional metadata (description, author)
- **Frontmatter in build output?**: Stripped for platforms that don't need it; each builder decides
- **Error handling**: Fail fast with clear messages, no retries for MVP
- **Local prompt source in lock file**: source = `local/<filename>`
- **Unified model**: `Plugin` replaces `Prompt` — both local and registry are file trees on disk
- **Local multi-file**: Local prompts can be directories with non-md files (scripts, configs, hooks)
- **Cache strategy**: Registry plugins cached by commit SHA (`{reg}/{plugin}/{sha}/`), local reads from `prompts/` directly
- **`content_hash` for registry plugins**: Empty string `""` — `commit_sha` is the discriminator
- **External git URL sources**: Skipped for MVP, `SyncError` raised
- **Build strategy**: Copy files from source to output, no hard links or symlinks
- **Build filtering**: Copy everything — no file exclusions. Platforms ignore unknown files
- **Builder protocol**: `build(list[Plugin], output_dir)` — builders receive Plugin objects directly
- **Local directory hashing**: Sort files by path, concatenate path + content, sha256 the result
- **Platform nesting**: Skills = 1 level (`skills/<name>/SKILL.md`), agents/commands = flat
- **`RegistryType` enum**: CLAUDE_MARKETPLACE
