## Why

The lock command (Phase 5) produces a lock file and populates the content-addressable cache, but there's no way to generate the platform-specific artifacts that Cursor and Claude Code actually consume. The `build` command is the offline, deterministic step that reads cached/local prompts and writes them into `.cursor/` and `.claude/` directories using directory-based routing. Without it, `sync` cannot be composed and prompts remain unusable by the target platforms.

## What Changes

- **New `CursorBuilder` adapter** — implements `ArtifactBuilder` protocol. Routes prompts from source categories (`skills/`, `rules/`, `agents/`, `commands/`, `subagents/`) to Cursor-specific output directories (e.g., `skills/` → `.cursor/skills-cursor/`).
- **New `ClaudeBuilder` adapter** — implements `ArtifactBuilder` protocol. Routes prompts to Claude Code output directories (category names are preserved as-is, e.g., `skills/` → `.claude/skills/`).
- **New `BuildArtifacts` use case** — orchestrates the build: load config, load lock file, read prompts from cache/local, filter by platform targeting, delegate to each platform's builder.
- **New `build` CLI command** — wires up `BuildArtifacts` with real infrastructure and exposes it as `promptkit build`.

## Capabilities

### New Capabilities
- `cursor-builder`: Generates `.cursor/` artifacts from prompts using directory-based routing with Cursor-specific path mappings
- `claude-builder`: Generates `.claude/` artifacts from prompts using directory-based routing with Claude Code path mappings
- `build-artifacts`: The `BuildArtifacts` use case that orchestrates reading cached prompts and delegating to platform builders
- `cli-build-command`: The `promptkit build` CLI command that wires up the use case

### Modified Capabilities

## Impact

- **Infrastructure layer** — two new builders (`CursorBuilder` in `infra/builders/`, `ClaudeBuilder` in `infra/builders/`)
- **Application layer** — new `BuildArtifacts` use case in `app/build.py`
- **CLI** — new `build` command in `cli.py`
- **Dependencies** — no new runtime dependencies
- **Output directories** — `.cursor/` and `.claude/` will be populated with generated artifacts
