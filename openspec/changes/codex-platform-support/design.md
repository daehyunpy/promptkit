## Context

promptkit builds platform-specific artifacts by dispatching to builder implementations keyed by `PlatformTarget` enum members. Currently two builders exist: `CursorBuilder` and `ClaudeBuilder`. Both follow the same pattern — filter plugin files by allowed category directories, copy them to the platform output dir, and manage a manifest for cleanup.

OpenAI Codex CLI uses a different directory convention than Cursor and Claude Code. Codex reads skills from `.agents/skills/<name>/SKILL.md` and instructions from `AGENTS.md` at the project root. It does not have `commands/`, `agents/`, or `rules/` directories — only `skills/` is a recognized structured directory.

## Goals / Non-Goals

**Goals:**
- Add Codex as an opt-in platform target that users can declare in `promptkit.yaml`
- Build a `CodexBuilder` that copies skill files to `.agents/skills/`, matching Codex conventions
- Follow existing builder patterns (protocol, manifest cleanup, FileSystem dependency)
- Keep Codex opt-in — not added to default platform configs

**Non-Goals:**
- No AGENTS.md generation or manipulation (that's user-controlled)
- No support for Codex `config.toml` or MCP server configuration
- No `agents/openai.yaml` generation for skill metadata
- No platform-specific frontmatter transformation (post-MVP item)
- No Codex marketplace/registry fetcher (this change is builder-only)

## Decisions

### 1. Output directory: `.agents` (not `.codex`)

Codex reads skills from `.agents/skills/` in the project directory. Unlike Cursor (`.cursor/`) and Claude Code (`.claude/`) which use dot-prefixed platform-named dirs, Codex uses `.agents/` as its standard directory. The default output dir for Codex will be `.agents`.

**Alternative considered**: `.codex/` — rejected because Codex does not read from `.codex/`; it scans `.agents/skills/`.

### 2. Allowed categories: `skills` only

Codex's structured directory convention only recognizes `skills/`. Files under `commands/`, `agents/`, `rules/`, etc. have no Codex equivalent. The `CodexBuilder` will filter to `skills/` category only.

**Alternative considered**: Copy all categories and let users figure it out — rejected because outputting files Codex can't discover provides no value and creates confusion.

### 3. Opt-in only (not a default platform)

Cursor and Claude Code are included in `DEFAULT_PLATFORM_CONFIGS` so new projects build for both by default. Codex should not be a default because: (a) it's a newer addition, (b) not all users have Codex, (c) the `.agents/` directory is a shared convention not owned by promptkit. Users add `codex:` to their `platforms:` section to opt in.

### 4. Builder follows existing pattern exactly

`CodexBuilder` will mirror `ClaudeBuilder`'s structure: constructor takes `FileSystem`, `platform` property returns `PlatformTarget.CODEX`, `build()` filters files by allowed categories, copies via `shutil.copy2`, uses manifest for cleanup. The manifest platform name will be `"codex"` (stored at `.promptkit/managed/codex.txt`).

### 5. Init scaffold conditionally creates `.agents/`

The init command will not create `.agents/` by default (since Codex is opt-in). The `.agents/` directory is only created when `codex` appears in the project's platform config. This is a change from the current behavior where all platform dirs are created unconditionally — but since Codex is not a default platform, this is consistent: scaffold creates dirs only for default platforms.

**Decision**: No change to `init.py` scaffold dirs. The builder creates the output dir on first build (via `mkdir(parents=True, exist_ok=True)`), which is the existing behavior.

## Risks / Trade-offs

- **`.agents/` directory ownership** — `.agents/` is a shared convention (Codex, potentially other tools). promptkit's manifest-based cleanup protects non-managed files, so this is safe. → Mitigation: manifest ensures only promptkit-written files are cleaned.
- **Skills-only limitation** — If Codex later adds `commands/` or `rules/` support, the builder will need updating. → Mitigation: Adding categories is a one-line change to `ALLOWED_CATEGORIES`.
- **Path mapping divergence** — Codex skills live at `.agents/skills/<name>/SKILL.md` while source plugins use `skills/<name>/SKILL.md`. The relative paths within `skills/` are preserved as-is, so no path rewriting is needed. The output dir (`.agents`) plus the file path (`skills/<name>/SKILL.md`) produces the correct absolute path.
