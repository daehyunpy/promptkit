# Technical Design: promptkit

## Architecture

promptkit is a Python-based CLI tool with a three-layer architecture:

```
┌─────────────────────────────────────────────────────┐
│                 CLI Commands                        │
│  (init, sync, lock, build, validate)                │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│              Application Layer                       │
│  (Use cases: LockPrompts, BuildArtifacts, etc.)     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│               Domain Layer                           │
│  (Prompt, PromptSpec, LockEntry, etc.)              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│           Infrastructure Layer                       │
│  (Fetchers, Builders, YAML parsers, File I/O)       │
└─────────────────────────────────────────────────────┘
```

### Layers

**Config Layer** - Declarative configuration and version locking
```
promptkit.yaml          # Declares which prompts to use and target platforms
promptkit.lock          # Locks exact versions/hashes for reproducibility
```

**Source Layer** - Prompt sources (synced + canonical)
```
.promptkit/cache/       # Cached upstream prompts (gitignored)
.agents/                # Canonical/custom prompts (committed to git)
```

**Output Layer** - Generated platform-specific artifacts
```
.cursor/                # Generated Cursor artifacts (agents, skills-cursor, rules, commands)
.claude/                # Generated Claude Code artifacts (skills, rules, subagents, commands)
```

### Command Model

promptkit follows the same pattern as modern package managers (uv, npm, cargo):

```
Manifest (promptkit.yaml)  →  Lockfile (promptkit.lock)  →  Artifacts (.cursor/, .claude/)
         human intent              resolved exact state           installed environment
```

| Command | Internal steps | Needs network | uv equivalent |
|---------|---------------|---------------|---------------|
| `promptkit init` | Scaffold project | No | `uv init` |
| `promptkit sync` | Fetch → lock → build | Yes | `uv sync` |
| `promptkit lock` | Fetch → update lockfile | Yes | `uv lock` |
| `promptkit build` | Cache → generate artifacts | No | N/A (implicit in sync) |
| `promptkit validate` | Check config well-formed | No | `uv lock --check` |

- **`sync`** is the primary command. It does everything: fetches prompts from sources, updates the lock file with content hashes, and generates platform artifacts. Like `uv sync`, it's the one command that takes you from config to working state.
- **`lock`** fetches and locks without generating artifacts. Useful for CI validation, code review (lock changes are a reviewable diff), and offline builds (lock on your machine with network, build later without).
- **`build`** generates artifacts from the existing lockfile and cache. No network needed. Useful after `lock`, after reverting a lockfile via git, or for rebuilding after changing platform config.

### Workflow

1. **Init** - `promptkit init` scaffolds a new project with config, directories, and gitignore.

2. **Configure** - User edits `promptkit.yaml` to declare which prompts to use and which platforms to target.

3. **Sync** - `promptkit sync` fetches prompts from sources, caches them in `.promptkit/cache/`, updates `promptkit.lock` with content hashes, and generates platform-specific artifacts in `.cursor/` and `.claude/`.

4. **Define** - Users write canonical/custom prompts in `.agents/` (committed to version control).

5. **Rebuild** - After config changes or git operations, `promptkit build` regenerates artifacts from cache without re-fetching.

### What Gets Committed to Git

- ✅ `promptkit.yaml` - config
- ✅ `promptkit.lock` - version locks
- ✅ `.agents/` - canonical prompts
- ❌ `.promptkit/cache/` - cached upstream prompts (reproducible via lock file)
- ⚠️  `.cursor/`, `.claude/` - generated artifacts (recommended to gitignore, but user's choice)

## Directory Layout

```
promptkit/
├── docs/
│   ├── product_requirements.md       # What and why
│   └── technical_design.md           # How (this file)
│
├── source/
│   └── promptkit/
│       ├── __init__.py
│       ├── cli.py                    # Typer CLI entry point
│       │
│       ├── domain/                   # Domain layer (pure business logic)
│       │   ├── __init__.py
│       │   ├── prompt.py             # Prompt aggregate root
│       │   ├── prompt_spec.py        # PromptSpec value object
│       │   ├── prompt_metadata.py    # PromptMetadata value object
│       │   ├── lock_entry.py         # LockEntry value object
│       │   ├── platform_target.py    # PlatformTarget enum
│       │   ├── errors.py             # Domain errors
│       │   └── protocols.py          # PromptFetcher, ArtifactBuilder protocols
│       │
│       ├── app/                      # Application layer (use cases)
│       │   ├── __init__.py
│       │   ├── init.py               # Init use case
│       │   ├── lock.py               # Lock use case (fetch + lock)
│       │   ├── build.py              # Build use case (cache → artifacts)
│       │   └── validate.py           # Validate use case
│       │
│       └── infra/                    # Infrastructure layer (adapters)
│           ├── __init__.py
│           ├── config/
│           │   ├── yaml_loader.py    # Load promptkit.yaml
│           │   └── lock_file.py      # Read/write promptkit.lock
│           ├── fetchers/
│           │   ├── claude_marketplace.py  # Fetch from Claude marketplace
│           │   └── local_file.py     # Read from .agents/
│           ├── builders/
│           │   ├── cursor_builder.py # Generate .cursor/ artifacts
│           │   └── claude_builder.py # Generate .claude/ artifacts
│           └── storage/
│               └── cache.py          # Manage .promptkit/cache/
│
├── tests/                            # Tests mirror source/ structure
│   ├── conftest.py
│   ├── domain/
│   │   ├── test_prompt.py
│   │   ├── test_prompt_spec.py
│   │   └── ...
│   ├── app/
│   │   ├── test_lock.py
│   │   └── test_build.py
│   └── infra/
│       ├── test_yaml_loader.py
│       └── test_cursor_builder.py
│
├── pyproject.toml                    # Python project config
├── uv.lock                           # Locked dependencies
│
├── promptkit.yaml                    # Example config (not committed in user projects)
├── .promptkit/cache/                 # Cached prompts (gitignored)
├── .agents/                          # Canonical prompts (committed)
├── .cursor/                          # Generated Cursor artifacts
└── .claude/                          # Generated Claude Code artifacts
```

## DDD Layers

### Domain Layer (`source/promptkit/domain/`)

Pure business logic. No dependencies on infrastructure.

**Entities:**
- `Prompt` - Aggregate root. Has identity, tracks state (synced, built, etc.)

**Value Objects:**
- `PromptSpec` - Immutable prompt specification (source, name, platforms, artifact_type)
- `LockEntry` - Immutable lock entry (hash, timestamp)
- `PromptMetadata` - Immutable metadata (author, description, version)
- `PlatformTarget` - Enum (CURSOR, CLAUDE_CODE)
- `ArtifactType` - Enum (SKILL, RULE, AGENT, COMMAND, SUBAGENT)

**Protocols:**
- `PromptFetcher` - Protocol for fetching prompts from sources
- `ArtifactBuilder` - Protocol for building platform-specific artifacts

**Domain Errors:**
- `PromptError` - Base domain error
- `SyncError` - Sync-related errors
- `BuildError` - Build-related errors
- `ValidationError` - Validation errors

### Application Layer (`source/promptkit/app/`)

Use cases that orchestrate domain objects and infrastructure.

**Use Cases:**
- `InitProject` - Scaffold new project structure
- `LockPrompts` - Fetch prompts and update lock file (used by both `lock` and `sync` commands)
- `BuildArtifacts` - Generate platform-specific outputs from cache (used by both `build` and `sync` commands)
- `ValidateConfig` - Validate promptkit.yaml

**`sync` = `LockPrompts` + `BuildArtifacts`** — the CLI `sync` command composes the two use cases sequentially.

### Infrastructure Layer (`source/promptkit/infra/`)

Adapters for external systems (file I/O, HTTP, YAML parsing).

**Config:**
- `YamlLoader` - Load and parse promptkit.yaml
- `LockFile` - Read/write promptkit.lock

**Fetchers (implement PromptFetcher):**
- `ClaudeMarketplaceFetcher` - Fetch from Claude plugin marketplace
- `LocalFileFetcher` - Read from .agents/

**Builders (implement ArtifactBuilder):**
- `CursorBuilder` - Generate .cursor/ artifacts
- `ClaudeBuilder` - Generate .claude/ artifacts

**Storage:**
- `PromptCache` - Manage .promptkit/cache/

## CLI Design

### Framework

Using **typer** for modern, type-safe CLI with minimal boilerplate.

### Commands

```python
# source/promptkit/cli.py
import typer

app = typer.Typer()

@app.command()
def init():
    """Initialize a new promptkit project"""
    pass

@app.command()
def sync():
    """Fetch prompts, update lock file, and generate artifacts"""
    pass

@app.command()
def lock():
    """Fetch prompts and update lock file without generating artifacts"""
    pass

@app.command()
def build():
    """Generate platform-specific artifacts from cached prompts"""
    pass

@app.command()
def validate():
    """Validate promptkit.yaml configuration"""
    pass
```

### Entry Point

Defined in `pyproject.toml`:
```toml
[project.scripts]
promptkit = "promptkit.cli:app"
```

## Configuration Schemas

### promptkit.yaml

```yaml
# Which prompts to use
prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer  # Fetch from Claude marketplace
    platforms:
      - cursor
      - claude-code

  - name: test-writer
    source: local/test-writer         # Read from .agents/
    platforms:
      - cursor

# Platform-specific settings (optional)
platforms:
  cursor:
    output_dir: .cursor
  claude-code:
    output_dir: .claude

# Metadata
version: 1
```

### promptkit.lock

```yaml
# Lock file format
version: 1

prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer
    hash: sha256:abc123...
    fetched_at: '2026-02-08T14:50:00+00:00'

  - name: test-writer
    source: local/test-writer
    hash: sha256:def456...
    fetched_at: '2026-02-08T14:50:00+00:00'
```

## Build System

### Build Process

Build is a deterministic, offline operation. It reads cached prompts and generates platform artifacts:

1. **Load Config** - Parse `promptkit.yaml` for prompt specs and platform output dirs
2. **Load Lock** - Parse `promptkit.lock` for content hashes (verification)
3. **Read Prompts** - Load prompt content from `.promptkit/cache/` and `.agents/`
4. **Route** - Map each prompt to the correct output directory based on `artifact_type` and `platform`
5. **Generate** - Write artifacts to `.cursor/` and `.claude/`

Build does **not** transform prompt content. It copies content to the correct platform directory. This keeps builds deterministic — same inputs always produce identical outputs.

### Platform Artifact Mapping

Each `artifact_type` maps to a specific subdirectory per platform:

| ArtifactType | Cursor output | Claude Code output |
|---|---|---|
| `skill` | `.cursor/skills-cursor/<name>.md` | `.claude/skills/<name>.md` |
| `rule` | `.cursor/rules/<name>.md` | `.claude/rules/<name>.md` |
| `agent` | `.cursor/agents/<name>.md` | `.claude/agents/<name>.md` |
| `command` | `.cursor/commands/<name>.md` | `.claude/commands/<name>.md` |
| `subagent` | `.cursor/subagents/<name>.md` | `.claude/subagents/<name>.md` |

### Determinism

- Sort all outputs alphabetically
- Use stable hashing (SHA256)
- No timestamps in generated files
- No AI transformation in the build pipeline — deterministic copy + route only
- Consistent formatting (YAML, Markdown)

### Future: AI-Assisted Transformation

Post-MVP, we may need AI to adapt prompts between platform formats (e.g., converting a Cursor-specific prompt to Claude Code conventions). If added, the approach would be:

- Transform once during `lock`, not during `build`
- Cache the transformed output alongside the original
- `build` always uses cached transforms — never calls an LLM
- Lock file records both original and transformed hashes

This preserves deterministic builds while allowing intelligent adaptation. Not needed for MVP where build is a simple copy + route operation.

## Lock Process

### Lock Algorithm

1. Parse `promptkit.yaml` to get list of prompt specs
2. Load existing `promptkit.lock` (if any) for comparison
3. For each prompt spec:
   - Fetch content from source (marketplace, local file, etc.)
   - Compute SHA256 hash of content
   - Compare with existing lock entry
   - If changed or new: update cache in `.promptkit/cache/` and create new lock entry
   - If unchanged: keep existing lock entry (preserves `fetched_at`)
4. Write updated `promptkit.lock`

### Lock Benefits

- **CI validation** — `promptkit validate` can check if lockfile is stale (config changed without re-locking)
- **Reproducibility** — lock captures exact content hashes; `build` uses cached content from lock
- **Code review** — lock changes show up as a reviewable diff separate from artifact changes
- **Offline builds** — `lock` once with network, then `build` anywhere without network

## Upstream Sync

### Claude Plugin Marketplace

**TBD:** Need to determine how to fetch prompts from Claude marketplace.

Options:
1. **Official API** - If Anthropic provides one (preferred)
2. **GitHub Repository** - If prompts are hosted on GitHub
3. **Web Scraping** - Last resort, fragile
4. **Manual Registry** - Curated list of known prompts

For MVP, we can start with a **manual registry** (hardcoded URLs or a local registry file).

## Testing Strategy

### Unit Tests

- **Domain layer** - Test in isolation, no mocks needed (pure logic)
- **Application layer** - Mock infrastructure protocols
- **Infrastructure layer** - Test against real dependencies or test doubles

### Integration Tests

- Test full workflows (init → sync → build)
- Use temporary directories for isolation
- Verify generated artifacts match expected structure

### Test Doubles

- `MockPromptFetcher` - Returns canned prompts
- `MockArtifactBuilder` - Captures build calls
- `InMemoryCache` - For testing without file I/O

## Build Order

### Phase 1: Project Scaffold ✅
- Set up Python package structure
- Configure pyproject.toml, uv
- Add basic CLI skeleton

### Phase 2: Init Command ✅
- Implement `promptkit init`
- Create directory structure
- Generate template `promptkit.yaml`

### Phase 3: Domain Model ✅
- Define `Prompt`, `PromptSpec`, `LockEntry`, `PromptMetadata`
- Define `PlatformTarget`, `ArtifactType` enums
- Define protocols (`PromptFetcher`, `ArtifactBuilder`)
- Define domain errors

### Phase 4: Config Loading ✅
- Implement YAML loader for `promptkit.yaml`
- Implement lock file reader/writer
- Add validation logic

### Phase 5: Lock Command
- Implement `LocalFileFetcher` for `.agents/`
- Implement `PromptCache` for `.promptkit/cache/`
- Implement `LockPrompts` use case
- Add `lock` CLI command

### Phase 6: Build Command
- Implement `CursorBuilder`
- Implement `ClaudeBuilder`
- Implement `BuildArtifacts` use case
- Add `build` CLI command

### Phase 7: Sync Command
- Compose `LockPrompts` + `BuildArtifacts` into `sync` CLI command
- This is the primary user-facing command

### Phase 8: Validate Command
- Implement validation use case
- Check config well-formed
- Verify prompts exist
- Check lockfile freshness

### Phase 9: Upstream Sync (Claude Marketplace)
- Implement `ClaudeMarketplaceFetcher`
- Add to lock/sync commands

### Phase 10: Polish
- Error messages
- CLI help text
- Progress indicators

## Implementation Decisions

### Resolved

1. **Prompt Fetching** - Fetch from GitHub repository (Anthropic hosts prompts there)
   - Will use GitHub API or raw.githubusercontent.com
   - Prompts stored in a known repository structure

2. **Prompt Format** - Markdown with YAML frontmatter
   ```markdown
   ---
   name: code-reviewer
   description: Reviews code for bugs and style issues
   author: Anthropic
   version: 1.0.0
   platforms:
     - cursor
     - claude-code
   ---

   # Code Reviewer Prompt

   You are an expert code reviewer...
   ```

3. **Platform Mapping** - Deterministic copy + route (no transformation)
   - Each prompt specifies which platform artifact type (skill, rule, agent, etc.)
   - Copy markdown content directly to appropriate directory based on artifact_type
   - No AI transformation in the build pipeline for MVP

4. **Hash Algorithm** - SHA256 of content only (excluding timestamps)
   - Standard, secure, widely supported
   - Hash only the content section, not metadata

5. **Progress Display** - Simple text output
   - Print status messages: "Syncing prompt 1/3..."
   - No fancy progress bars for MVP
   - Can add `rich` library later for better UX

6. **Git Integration** - Don't run git automatically
   - Promptkit doesn't execute git commands
   - User runs `git diff` themselves to see changes
   - Keeps tool simple, no git dependency

7. **Command Model** - Follow package manager conventions (uv, npm, cargo)
   - `sync` = fetch + lock + build (the one-stop command)
   - `lock` = fetch + update lockfile (resolve without installing)
   - `build` = generate artifacts from cache (install from lockfile)
   - Steps are cleanly separated internally; each is independently useful

### Open Questions

Need to resolve during implementation:

1. **GitHub Repository Structure** - What's the actual repo URL and structure for Claude prompts?
2. **Error Handling** - How to handle network failures, missing files, malformed YAML?
3. **Artifact Type Mapping** - How does prompt metadata specify if it's a skill vs rule vs agent?

## Dependencies

### Runtime
- `typer` - CLI framework
- `pyyaml` - YAML parsing
- `pydantic` - Data validation (for config schemas)
- `httpx` - HTTP client (if fetching from web)

### Development
- `pytest` - Testing framework
- `ruff` - Linter and formatter
- `pyright` - Type checker

## Cross-Platform Contracts

While promptkit is Python-only (no Swift), we still benefit from defining contracts:

### Prompt Schema

Prompts use **Markdown with YAML frontmatter** format:

```markdown
---
name: code-reviewer
description: Reviews code for bugs and style issues
author: Anthropic
version: 1.0.0
artifact_type: skill  # skill, rule, agent, command, subagent
platforms:
  - cursor
  - claude-code
---

# Code Reviewer Prompt

You are an expert code reviewer. Review the following code for:
- Bugs and logic errors
- Code style and best practices
- Performance issues

When you find issues, explain:
1. What the problem is
2. Why it's a problem
3. How to fix it

Be constructive and specific in your feedback.
```

**Key fields:**
- `name` - Unique identifier for the prompt
- `description` - Brief description (for display)
- `author` - Prompt author/maintainer
- `version` - Semantic version (for future version pinning)
- `artifact_type` - Where to place it (skill, rule, agent, command, subagent)
- `platforms` - Which platforms to generate for (cursor, claude-code)

The content after `---` is the actual prompt text in Markdown.

This ensures consistency and makes platform adapters simpler.
