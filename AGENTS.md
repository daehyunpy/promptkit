# AGENTS.md

Instructions for AI agents working on this codebase. `CLAUDE.md` is a symlink to this file — edit here, not there.

## Project

**promptkit** — a package manager for AI prompts. Syncs high-quality prompts from sources like Claude plugin marketplace, stores them in a declarative format, and generates platform-specific artifacts for Cursor and Claude Code.

## Key Docs

- `docs/product_requirements.md` — what to build and why

Read before making changes.

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

## Git Workflow

- **`main`** — production-ready code
- **`develop`** — integration branch (if needed)
- **Feature branches** — `feature/<name>` off main/develop
- **Commit style** — conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- **Keep commits focused** — one logical change per commit

## Coding Style

- Follow Python best practices (PEP 8)
- Use type hints where appropriate
- Write clear, descriptive function and variable names
- Keep functions focused and small
- Write tests for core functionality

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
