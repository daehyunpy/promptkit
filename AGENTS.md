# AGENTS.md

Instructions for AI agents working on this codebase. `CLAUDE.md` is a symlink to this file — edit here, not there.

## Project

**promptkit** — a package manager for AI prompts. Syncs high-quality prompts from sources like Claude plugin marketplace, stores them in a declarative format, and generates platform-specific artifacts for Cursor and Claude Code.

## Key Docs

- `docs/product_requirements.md` — what to build and why
- `docs/technical_design.md` — how to build it (architecture, DDD layers, schemas, build process)

Read both before making changes.

## Current State

**Pre-implementation.** No code written yet. Currently in planning phase.

## Tech Stack

- **Language**: Python
- **Package Manager**: uv
- **CLI Framework**: TBD (typer, click, or argparse)
- **Config Format**: YAML (promptkit.yaml)
- **Target Platforms**: Cursor (`.cursor/`), Claude Code (`.claude/`)

## Project Structure

```
promptkit/
├── docs/
│   └── product_requirements.md    # Product requirements
├── source/
│   └── promptkit/
│       ├── __init__.py
│       ├── cli.py                  # CLI entry point
│       ├── sync.py                 # Sync command
│       ├── build.py                # Build command
│       ├── validate.py             # Validate command
│       └── init.py                 # Init command
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

| Command | What it does |
|---------|--------------|
| `promptkit init` | Scaffold new project structure |
| `promptkit sync` | Fetch prompts from upstream sources → `.promptkit/cache/`, update lock file |
| `promptkit build` | Generate `.cursor/` and `.claude/` artifacts from cache + `.agents/` |
| `promptkit validate` | Verify `promptkit.yaml` is well-formed and prompts exist |

## Core Workflow

1. **Sync** - Fetch upstream prompts and cache them
2. **Define** - Write canonical prompts in `.agents/`
3. **Build** - Generate platform-specific artifacts in `.cursor/` and `.claude/`

## What NOT to Do

- Don't add a web UI or GUI — CLI only
- Don't add analytics, telemetry, or usage tracking
- Don't add A/B testing or prompt optimization features
- Don't add SaaS hosting or cloud service
- Don't add version pinning in v1 — always sync latest
- Don't add composition layers in v1 — that's post-MVP
- Don't support platforms beyond Cursor and Claude Code in v1

## Coding Disciplines

This project follows three disciplines: **DDD**, **TDD**, and **Clean Code**. These govern how every line of code is written, not just how folders are organized.

### DDD (Domain-Driven Design)

- **Ubiquitous language** — use domain terms consistently. A `Prompt` is a `Prompt`, not a `Template` or `Config`. A `PromptSpec` is a `PromptSpec`, not a `Definition` or `Manifest`. If the domain term changes, rename everywhere.
- **Entities vs Value Objects** — entities have identity (`Prompt` has an ID, persists, tracks state). Value objects are immutable data with no identity (`PromptMetadata`, `PlatformTarget`, `LockEntry`). Don't give value objects IDs.
- **Aggregates** — `Prompt` is an aggregate root. Access its metadata and content through `Prompt`, not independently. Don't let outside code reach into aggregate internals.
- **Domain logic in domain objects** — not in CLI handlers or builder code. If you're writing an `if` about prompt state in a command handler, it belongs in the domain layer.
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

- Don't add a web UI or GUI — CLI only
- Don't add analytics, telemetry, or usage tracking
- Don't add A/B testing or prompt optimization features
- Don't add SaaS hosting or cloud service
- Don't write code without a failing test first
- Don't put domain logic in CLI handlers or builder code
- Don't let domain code import infrastructure modules
- Don't leave dead code, commented-out code, or unused imports
- Don't use magic numbers or strings — name them
- Don't add version pinning in v1 — that's post-MVP
- Don't add composition layers in v1 — that's post-MVP
- Don't support platforms beyond Cursor and Claude Code in v1

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

## Open Questions

These need to be resolved during implementation:

- Which Python CLI framework? (typer recommended for modern type-safe CLI)
- How to fetch from Claude plugin marketplace? (API? web scraping? manual registry?)
- Lock file format? (JSON? YAML? custom format?)
- How to handle prompt metadata (author, version, description)?
- How to map generic prompts to platform-specific formats?
- Should `.cursor/` and `.claude/` be gitignored by default?
