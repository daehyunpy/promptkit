# Technical Design: promptkit

## Architecture

promptkit is a Python-based CLI tool with a three-layer architecture:

```
┌─────────────────────────────────────────────────────┐
│                 CLI Commands                        │
│  (init, sync, build, validate)                      │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│              Application Layer                       │
│  (Use cases: SyncPrompts, BuildArtifacts, etc.)     │
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

### Workflow

1. **Sync** - `promptkit sync` fetches upstream prompts from sources (Claude plugin marketplace) and stores them in `.promptkit/cache/`. Updates `promptkit.lock` with versions/hashes.

2. **Define** - Users write canonical/custom prompts in `.agents/` (committed to version control).

3. **Build** - `promptkit build` reads from both `.promptkit/cache/` (upstream) and `.agents/` (canonical), merges them according to `promptkit.yaml`, and generates platform-specific outputs in `.cursor/` and `.claude/`.

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
│       │   ├── lock_entry.py         # LockEntry value object
│       │   ├── platform_target.py    # PlatformTarget enum
│       │   ├── errors.py             # Domain errors
│       │   └── protocols.py          # PromptFetcher, ArtifactBuilder protocols
│       │
│       ├── app/                      # Application layer (use cases)
│       │   ├── __init__.py
│       │   ├── init.py               # Init use case
│       │   ├── sync.py               # Sync use case
│       │   ├── build.py              # Build use case
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
│   │   └── test_prompt_spec.py
│   ├── app/
│   │   ├── test_sync.py
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
- `PromptSpec` - Immutable prompt specification (source, name, platforms)
- `LockEntry` - Immutable lock entry (version, hash, timestamp)
- `PromptMetadata` - Immutable metadata (author, description, version)
- `PlatformTarget` - Enum (CURSOR, CLAUDE_CODE)

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
- `SyncPrompts` - Fetch prompts and update lock file
- `BuildArtifacts` - Generate platform-specific outputs
- `ValidateConfig` - Validate promptkit.yaml

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
    """Sync prompts from upstream sources"""
    pass

@app.command()
def build():
    """Build platform-specific artifacts"""
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
generated_at: 2026-02-08T14:50:00Z

prompts:
  - name: code-reviewer
    source: anthropic/code-reviewer
    version: latest  # For MVP (no version pinning yet)
    hash: sha256:abc123...
    fetched_at: 2026-02-08T14:50:00Z

  - name: test-writer
    source: local/test-writer
    version: null  # Local prompts have no version
    hash: sha256:def456...
    fetched_at: 2026-02-08T14:50:00Z
```

## Build System

### Build Process

1. **Load Config** - Parse `promptkit.yaml` and `promptkit.lock`
2. **Read Prompts** - Load prompts from `.promptkit/cache/` and `.agents/`
3. **Validate** - Check that all referenced prompts exist
4. **Transform** - Convert prompts to platform-specific formats
5. **Generate** - Write artifacts to `.cursor/` and `.claude/`

### Platform Adapters

Each platform has a builder that implements `ArtifactBuilder`:

**CursorBuilder:**
- Generates `.cursor/agents/`
- Generates `.cursor/skills-cursor/`
- Generates `.cursor/rules/`
- Generates `.cursor/commands/`

**ClaudeBuilder:**
- Generates `.claude/skills/`
- Generates `.claude/rules/`
- Generates `.claude/subagents/`
- Generates `.claude/commands/`

### Determinism

- Sort all outputs alphabetically
- Use stable hashing (SHA256)
- No timestamps in generated files
- Consistent formatting (YAML, Markdown)

## Upstream Sync

### Claude Plugin Marketplace

**TBD:** Need to determine how to fetch prompts from Claude marketplace.

Options:
1. **Official API** - If Anthropic provides one (preferred)
2. **GitHub Repository** - If prompts are hosted on GitHub
3. **Web Scraping** - Last resort, fragile
4. **Manual Registry** - Curated list of known prompts

For MVP, we can start with a **manual registry** (hardcoded URLs or a local registry file).

### Sync Algorithm

1. Parse `promptkit.yaml` to get list of prompts
2. For each prompt:
   - Fetch from source (marketplace or local)
   - Compute hash (SHA256)
   - Compare with `promptkit.lock`
   - If different, update cache and lock file
3. Write updated `promptkit.lock`
4. Show git diff to user

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

### Phase 1: Project Scaffold
- Set up Python package structure
- Configure pyproject.toml, uv
- Add basic CLI skeleton

### Phase 2: Init Command
- Implement `promptkit init`
- Create directory structure
- Generate template `promptkit.yaml`

### Phase 3: Domain Model
- Define `Prompt`, `PromptSpec`, `LockEntry`
- Define protocols (`PromptFetcher`, `ArtifactBuilder`)
- Define domain errors

### Phase 4: Config Loading
- Implement YAML loader for `promptkit.yaml`
- Implement lock file reader/writer
- Add validation logic

### Phase 5: Sync Command (Local)
- Implement `LocalFileFetcher` for `.agents/`
- Implement sync use case
- Update lock file with hashes

### Phase 6: Build Command
- Implement `CursorBuilder`
- Implement `ClaudeBuilder`
- Generate artifacts from prompts

### Phase 7: Validate Command
- Implement validation use case
- Check config well-formed
- Verify prompts exist

### Phase 8: Upstream Sync (Claude Marketplace)
- Implement `ClaudeMarketplaceFetcher`
- Add to sync command

### Phase 9: Polish
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

3. **Platform Mapping** - Direct copy (simple approach)
   - Each prompt specifies which platform artifact type (skill, rule, agent, etc.)
   - Copy markdown content directly to appropriate directory
   - Platform-specific formatting added later if needed

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
