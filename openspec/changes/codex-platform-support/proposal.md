## Why

promptkit currently supports Cursor and Claude Code as build targets. OpenAI Codex CLI is a widely-adopted coding agent with its own directory conventions (`.agents/skills/` for skills, `AGENTS.md` for instructions). Users who work with Codex alongside Cursor or Claude Code cannot use promptkit to manage their Codex prompts. Adding Codex as a platform target lets promptkit users sync prompts to all three platforms from a single config.

## What Changes

- Add `CODEX` variant to the `PlatformTarget` enum with value `"codex"`
- Create `CodexBuilder` implementing the `ArtifactBuilder` protocol
- Codex uses `.agents/skills/<name>/SKILL.md` for skills — the builder maps `skills/` category files to this path structure
- Codex has no equivalent of `commands/`, `agents/`, `rules/` directories — only `skills/` files are copied
- Register Codex in the YAML config loader with default output dir `.agents`
- Wire `CodexBuilder` into CLI composition root
- Add Codex to project scaffold (`init`) and clean use case
- Codex is **not** added to `DEFAULT_PLATFORM_CONFIGS` — users must opt in explicitly (unlike Cursor/Claude which are defaults)

## Capabilities

### New Capabilities
- `codex-builder`: CodexBuilder that copies skill files to `.agents/skills/`, filtering to the `skills` category only. Implements manifest-based cleanup like existing builders.

### Modified Capabilities
- `build-artifacts`: Add Codex to the set of known platforms the build use case can dispatch to
- `project-scaffold`: Add Codex output dir to scaffold when platform is configured
- `clean-artifacts`: Add Codex manifest cleanup support

## Impact

- **Domain**: `PlatformTarget` enum gains `CODEX` member; `from_string("codex")` must resolve it
- **Infra/builders**: New `codex_builder.py` module
- **Infra/config**: `DEFAULT_OUTPUT_DIRS` gains Codex entry; `DEFAULT_PLATFORM_CONFIGS` unchanged (opt-in only)
- **App**: `init.py` and `clean.py` gain Codex entries
- **CLI**: `_make_build_use_case` registers `CodexBuilder`
- **Config schema**: `promptkit.yaml` accepts `codex:` under `platforms:`
- **Tests**: New builder tests, updated enum tests, updated config loader tests
