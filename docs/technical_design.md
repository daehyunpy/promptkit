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
promptkit.yaml          # Declares registries, prompts, and target platforms
promptkit.lock          # Locks exact versions/hashes for reproducibility
```

**Source Layer** - Prompt sources (synced + canonical)
```
.promptkit/cache/       # Cached remote prompts (gitignored)
prompts/                # Local/custom prompts (committed to git, auto-built)
```

**Output Layer** - Generated platform-specific artifacts
```
.cursor/                # Generated Cursor artifacts
.claude/                # Generated Claude Code artifacts
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

2. **Configure** - User edits `promptkit.yaml` to declare registries and which prompts to use.

3. **Sync** - `promptkit sync` fetches prompts from registries, caches them in `.promptkit/cache/`, updates `promptkit.lock` with content hashes, and generates platform-specific artifacts in `.cursor/` and `.claude/`.

4. **Define** - Users write local prompts in `prompts/` (committed to version control). These are automatically included in every build — no config entry needed.

5. **Rebuild** - After config changes or git operations, `promptkit build` regenerates artifacts from cache without re-fetching.

### What Gets Committed to Git

- ✅ `promptkit.yaml` - config
- ✅ `promptkit.lock` - version locks
- ✅ `prompts/` - local/custom prompts
- ❌ `.promptkit/cache/` - cached remote prompts (reproducible via lock file)
- ✅ `.cursor/`, `.claude/` - generated artifacts (commit for team collaboration; promptkit uses manifest-based cleanup to preserve non-promptkit files)

## Configuration Schema

### promptkit.yaml

```yaml
version: 1

# Registries define where to fetch remote prompts
# type defaults to "claude-marketplace" if omitted
registries:
  # Object form (full)
  anthropic-agent-skills:
    type: claude-marketplace
    url: https://github.com/anthropics/skills

  # Short form: key: <url> (type defaults to claude-marketplace)
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official

prompts:
  # Simple form: registry/name
  - claude-plugins-official/code-review
  - anthropic-agent-skills/feature-dev

  # Object form: with overrides
  - source: claude-plugins-official/code-review
    name: my-reviewer              # optional, defaults to "code-review"
    platforms:                      # optional, defaults to all
      - cursor

  # Version pinning (post-MVP, reserved syntax)
  # - claude-plugins-official/code-review@1.2.0

# Platforms define build targets
# type defaults to key name, output_dir has defaults per type
platforms:
  # Object form (full)
  cursor:
    type: cursor
    output_dir: .cursor

  # Short form: key: <output_dir>
  claude-code: .claude

  # Minimal form: key with no value (all defaults)
  # cursor:
```

**Key design points:**
- Prompts can be strings (`registry/name`) or objects (with overrides)
- `name` defaults to the part after `/` in the source
- `platforms` defaults to all platforms defined in the config
- `artifact_type` is NOT in the config — it comes from the prompt's frontmatter
- `prompts/` prompts are auto-included — no config entry needed
- `@version` syntax reserved for future version pinning (MVP always fetches latest)

**Short forms:**
- **Registries** support three forms:
  - Full: `key: {type: ..., url: ...}`
  - Short: `key: <url>` (string value = URL, type defaults to `claude-marketplace`)
- **Platforms** support three forms:
  - Full: `key: {type: ..., output_dir: ...}`
  - Short: `key: <output_dir>` (string value = output_dir, type defaults to key name)
  - Minimal: `key:` with no value (all defaults: type = key name, output_dir = default)

**Defaults:**
- Registry `type` defaults to `claude-marketplace` when omitted
- Platform `type` defaults to the key name when omitted (e.g., `cursor:` → type `cursor`)
- Platform `output_dir` defaults per type: `cursor` → `.cursor`, `claude-code` → `.claude`

### MVP Registries

| Registry Name | GitHub Repo | Description |
|---|---|---|
| `anthropic-agent-skills` | `anthropics/skills` | Anthropic's curated agent skills |
| `claude-plugins-official` | `anthropics/claude-plugins-official` | Official Claude plugins |

### Registry Types

| Type | Fetcher | Description |
|---|---|---|
| `claude-marketplace` | `ClaudeMarketplaceFetcher` | Prompts from Claude plugin marketplace (GitHub-hosted) |

MVP supports `claude-marketplace` only. The type determines which `PromptFetcher` implementation to use. If `type` is omitted in a registry definition, it defaults to `claude-marketplace`.

### Platform Types

| Type | Builder | Description |
|---|---|---|
| `cursor` | `CursorBuilder` | Generates `.cursor/` artifacts |
| `claude-code` | `ClaudeBuilder` | Generates `.claude/` artifacts |

The type determines which `ArtifactBuilder` implementation to use. If `type` is omitted in a platform definition, it defaults to the platform's key name (e.g., `cursor:` defaults to type `cursor`).

**Default output directories:**

| Platform Type | Default `output_dir` |
|---|---|
| `cursor` | `.cursor` |
| `claude-code` | `.claude` |

### promptkit.lock

```yaml
version: 1

prompts:
  - name: code-review
    source: claude-plugins-official/code-review
    hash: sha256:abc123...
    fetched_at: '2026-02-08T14:50:00+00:00'

  - name: feature-dev
    source: anthropic-agent-skills/feature-dev
    hash: sha256:def456...
    fetched_at: '2026-02-08T14:50:00+00:00'

local:
  - name: my-custom-rule
    hash: sha256:789xyz...
    fetched_at: '2026-02-08T15:00:00+00:00'
```

Lock file tracks both remote prompts (from registries) and local prompts (from `prompts/`).

## Prompt Format

Prompts are **Markdown files** (`.md`). They may optionally include YAML frontmatter for metadata (description, author), but it's not required.

```markdown
---
description: Reviews code for bugs and style issues
author: Anthropic
---

# Code Reviewer

You are an expert code reviewer. Review the following code for:
- Bugs and logic errors
- Code style and best practices
- Performance issues

Be constructive and specific in your feedback.
```

**Frontmatter fields (all optional):**
- `description` - Brief description (for display)
- `author` - Prompt author/maintainer

The `name` comes from the filename (e.g., `code-review.md` → name `code-review`), not frontmatter. This matches how `prompts/` files work — the filename IS the identity.

The entire file (including frontmatter) is the content that gets hashed and cached.

### Directory-Based Routing

The prompt's category (skills, commands, rules, agents) is determined by **directory structure**, not metadata:

**Remote prompts** — the source repo's directory structure tells us the category:
- `plugins/code-review/skills/review/SKILL.md` → it's a skill
- `plugins/code-review/commands/review.md` → it's a command
- `skills/pdf/SKILL.md` → it's a skill

**Local prompts** — users organize `prompts/` by subdirectory:
```
prompts/
  skills/my-skill.md
  commands/my-command.md
  rules/my-rule.md
```

This mirrors how the upstream repos work — no need for an `artifact_type` field.

## Build System

### Build Process

Build is a deterministic, offline operation. It reads cached/local prompts and generates platform artifacts:

1. **Load Config** - Parse `promptkit.yaml` for platform definitions
2. **Load Lock** - Parse `promptkit.lock` for content hashes (verification)
3. **Read Prompts** - Load prompt content from `.promptkit/cache/` (remote) and `prompts/` (local)
4. **Route** - Map each prompt's source category directory to the correct platform output directory
5. **Generate** - Write artifacts to platform output directories

Build does **not** transform prompt content. It copies content to the correct platform directory. This keeps builds deterministic — same inputs always produce identical outputs.

### Platform Artifact Mapping

Each source category maps to a platform-specific subdirectory:

| Source category | Cursor output | Claude Code output |
|---|---|---|
| `skills/` | `.cursor/skills/<name>.md` | `.claude/skills/<name>.md` |
| `rules/` | `.cursor/rules/<name>.md` | `.claude/rules/<name>.md` |
| `agents/` | `.cursor/agents/<name>.md` | `.claude/agents/<name>.md` |
| `commands/` | `.cursor/commands/<name>.md` | `.claude/commands/<name>.md` |
| `subagents/` | `.cursor/subagents/<name>.md` | `.claude/subagents/<name>.md` |

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

1. Parse `promptkit.yaml` to get registries and prompt specs
2. Load existing `promptkit.lock` (if any) for comparison
3. For each remote prompt spec:
   - Resolve registry from source prefix (e.g., `anthropic/` → `anthropic` registry)
   - Fetch content using registry's fetcher
   - Compute SHA256 hash of content
   - Compare with existing lock entry
   - If changed or new: update cache in `.promptkit/cache/` and create new lock entry
   - If unchanged: keep existing lock entry (preserves `fetched_at`)
4. For each local prompt (`prompts/*.md`):
   - Read file content
   - Compute SHA256 hash
   - Update lock entry if changed
5. Write updated `promptkit.lock`

### Lock Benefits

- **CI validation** — `promptkit validate` can check if lockfile is stale (config changed without re-locking)
- **Reproducibility** — lock captures exact content hashes; `build` uses cached content from lock
- **Code review** — lock changes show up as a reviewable diff separate from artifact changes
- **Offline builds** — `lock` once with network, then `build` anywhere without network

## Prompt Cache

### Content-Addressable Storage

The cache (`.promptkit/cache/`) uses content-addressable storage, similar to git objects. Files are named by their SHA256 content hash:

```
.promptkit/cache/
  sha256-abc123def456.md
  sha256-789xyz000111.md
```

The lockfile maps `name → hash`, the cache maps `hash → content`. This gives us:
- **No naming conflicts** — two prompts with the same name but different content get different cache entries
- **Deduplication** — identical content from different sources shares one cache file
- **Integrity verification** — cache filename = content hash, trivially verifiable

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
│       │   ├── registry.py           # Registry value object
│       │   ├── platform_config.py    # PlatformConfig value object
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
│           │   └── claude_marketplace.py  # Fetch from Claude marketplace
│           ├── builders/
│           │   ├── cursor_builder.py # Generate .cursor/ artifacts
│           │   └── claude_builder.py # Generate .claude/ artifacts
│           └── storage/
│               └── cache.py          # Manage .promptkit/cache/
│
├── tests/                            # Tests mirror source/ structure
│
├── pyproject.toml                    # Python project config
├── uv.lock                           # Locked dependencies
│
├── promptkit.yaml                    # Config
├── .promptkit/cache/                 # Cached remote prompts (gitignored)
├── prompts/                          # Local prompts (committed, auto-built)
├── .cursor/                          # Generated Cursor artifacts
└── .claude/                          # Generated Claude Code artifacts
```

## DDD Layers

### Domain Layer (`source/promptkit/domain/`)

Pure business logic. No dependencies on infrastructure.

**Entities:**
- `Prompt` - Aggregate root. Identity via name. Holds content and platform targeting.

**Value Objects:**
- `PromptSpec` - Immutable prompt specification from config (source, optional name, optional platforms)
- `LockEntry` - Immutable lock entry (name, source, hash, timestamp)
- `PromptMetadata` - Immutable metadata (description, author — from frontmatter)
- `Registry` - Immutable registry definition (name, type, url)
- `PlatformConfig` - Immutable platform definition (name, type, output_dir)
- `PlatformTarget` - Enum (CURSOR, CLAUDE_CODE)

**Protocols:**
- `PromptFetcher` - Protocol for fetching prompts from registries
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

**Fetchers (implement PromptFetcher, selected by registry type):**
- `ClaudeMarketplaceFetcher` - Fetch from Claude marketplace (type: `claude-marketplace`)

**Builders (implement ArtifactBuilder, selected by platform type):**
- `CursorBuilder` - Generate .cursor/ artifacts (type: `cursor`)
- `ClaudeBuilder` - Generate .claude/ artifacts (type: `claude-code`)

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

### Phase 3: Domain Model ✅ (being revised)
- Define `Prompt`, `PromptSpec`, `LockEntry`, `PromptMetadata`
- Define `Registry`, `PlatformConfig` value objects
- Define `PlatformTarget`, `ArtifactType` enums
- Define protocols (`PromptFetcher`, `ArtifactBuilder`)
- Define domain errors

### Phase 4: Config Loading ✅ (being revised)
- Implement YAML loader for `promptkit.yaml` (new schema with registries, typed platforms)
- Implement lock file reader/writer
- Add validation logic

### Phase 5: Lock Command
- Implement frontmatter parser (extract artifact_type)
- Implement `PromptCache` for `.promptkit/cache/`
- Implement `LockPrompts` use case (remote + local)
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

1. **Config follows plugin conventions** - Inspired by Claude Code's plugin system
   - Registries are typed and declared in config (type defaults to `claude-marketplace`)
   - Platforms are typed (type defaults to key name, e.g., `cursor:` → type `cursor`)
   - Types drive which fetcher/builder implementation to use
   - Prompts can be simple strings or objects with overrides
   - MVP registries: `anthropic-agent-skills` (anthropics/skills), `claude-plugins-official` (anthropics/claude-plugins-official)
   - Short forms supported: registries `key: <url>`, platforms `key: <output_dir>` or `key:` (minimal)

2. **Local prompts auto-included** - Everything in `prompts/` is built automatically
   - No config entry needed for local prompts
   - `prompts/` is scanned during both `lock` and `build`

3. **Directory-based routing, no `artifact_type`**
   - The prompt's category (skills, commands, rules, agents) is determined by its source directory structure
   - Remote: fetcher knows from the repo path (e.g., `plugins/code-review/commands/`)
   - Local: user organizes `prompts/` by subdirectory (e.g., `prompts/skills/`, `prompts/commands/`)
   - No frontmatter parsing needed for routing — simpler model, matches how upstream repos work

4. **Frontmatter is optional metadata only**
   - Frontmatter may contain `description`, `author` — purely informational
   - Entire file (including frontmatter) is hashed and cached as-is
   - Hash covers the full file content

5. **Version pinning uses `@` syntax** (post-MVP)
   - `anthropic/code-review@1.2.0` — reserved for future version pinning
   - MVP always fetches latest from registry

6. **Platform Mapping** - Deterministic copy + route (no transformation)
   - Each prompt's source category directory determines the output subdirectory
   - Builder copies source categories to platform output directories unchanged
   - No AI transformation in the build pipeline for MVP

7. **Hash Algorithm** - SHA256 of full file content (including frontmatter)
   - Standard, secure, widely supported

8. **Progress Display** - Simple text output
   - Print status messages: "Syncing prompt 1/3..."
   - No fancy progress bars for MVP

9. **Git Integration** - Don't run git automatically
   - Promptkit doesn't execute git commands
   - Keeps tool simple, no git dependency

10. **Command Model** - Follow package manager conventions (uv, npm, cargo)
    - `sync` = fetch + lock + build (the one-stop command)
    - `lock` = fetch + update lockfile (resolve without installing)
    - `build` = generate artifacts from cache (install from lockfile)

11. **Content-addressable cache** - `.promptkit/cache/` uses SHA256 hash as filename (like git objects)
    - Lockfile maps name → hash, cache maps hash → content
    - No naming conflicts, trivial deduplication

12. **Upstream sources stubbed for MVP** - `claude-marketplace` registry type returns clear error
    - `ClaudeMarketplaceFetcher` is on the roadmap but stubbed initially

13. **Error Handling** - Fail fast with clear messages, no retries for MVP
    - Network failures → `SyncError`
    - Malformed YAML → `ValidationError`
    - Missing files → `BuildError`

14. **Frontmatter is optional metadata** - Only contains `description` and `author`; no routing logic

15. **Frontmatter stripped in build output** - Each platform builder decides whether to strip frontmatter; platforms that don't understand it get clean content

16. **Local prompts use `local/` source in lock file** - e.g., `source: local/my-custom-rule`

### Future: AI-Assisted Transformation

Post-MVP, we may need AI to adapt prompts between platform formats. If added:

- Transform once during `lock`, not during `build`
- Cache the transformed output alongside the original
- `build` always uses cached transforms — never calls an LLM
- Lock file records both original and transformed hashes

## Dependencies

### Runtime
- `typer` - CLI framework
- `pyyaml` - YAML parsing
- `pydantic` - Data validation (for config schemas)
- `httpx` - HTTP client (for fetching from registries)

### Development
- `pytest` - Testing framework
- `ruff` - Linter and formatter
- `pyright` - Type checker

## Known Issues

1. **Build output collision: needs plugin name prefix** — When two plugins contain files with the same relative path (e.g., both have `skills/code-review/SKILL.md`), the second plugin silently overwrites the first in the build output directory. Builders should prefix output paths with the plugin name (e.g., `skills/my-plugin/code-review/SKILL.md`) to namespace them and prevent collisions.

2. **Skills can be zip files** — Skills in the Claude marketplace can be distributed as `.zip` files. Fetchers and builders need to handle extracting zip-packaged skills alongside the current directory-based format.

3. **Hooks, scripts, MCP, and LSP not yet supported in builders** — Builders currently allow only `commands`, `agents`, `skills`, and `rules` categories. Support for `hooks`, `scripts`, `mcp`, and `lsp` should be adapted in a future phase.
