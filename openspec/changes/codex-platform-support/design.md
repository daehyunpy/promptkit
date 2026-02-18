## Context

promptkit builds platform-specific artifacts by dispatching to builder implementations keyed by `PlatformTarget` enum members. Currently two builders exist: `CursorBuilder` and `ClaudeBuilder`. Both follow the same pattern — filter plugin files by allowed category directories, copy them to the platform output dir, and manage a manifest for cleanup.

OpenAI Codex CLI uses a different directory convention than Cursor and Claude Code. Codex reads project-level skills from `.codex/skills/<name>/SKILL.md` and also scans `.agents/skills/` (the open Agent Skills standard location). Instructions live in `AGENTS.md` at the project root. Codex has no file-based equivalent of `commands/`, `agents/`, or `rules/` directories — only `skills/` is a recognized structured directory.

See `docs/references/codex-directory-spec.md` for the full upstream spec.

## Goals / Non-Goals

**Goals:**
- Add Codex as an opt-in platform target that users can declare in `promptkit.yaml`
- Build a `CodexBuilder` that copies skill files to `.codex/skills/`, matching Codex conventions
- Follow existing builder patterns (protocol, manifest cleanup, FileSystem dependency)
- Keep Codex opt-in — not added to default platform configs

**Non-Goals:**
- No AGENTS.md generation or manipulation (that's user-controlled)
- No support for Codex `config.toml` or MCP server configuration
- No `agents/openai.yaml` generation for skill metadata
- No platform-specific frontmatter transformation (post-MVP item)
- No Codex marketplace/registry fetcher (this change is builder-only)
- No output to `.agents/skills/` — use `.codex/` for consistency with `.cursor/` and `.claude/`

## Decisions

### 1. Output directory: `.codex` (consistent with other platforms)

Codex has two skill locations: `.codex/skills/` (project-level, checked into repo) and `.agents/skills/` (open standard, scanned per-directory). We use `.codex/` because:
- It matches the `.cursor/` and `.claude/` naming convention (dot-prefixed platform name)
- `.codex/skills/` is the project-level location intended for team-shared skills
- `.agents/` is a cross-platform shared convention — promptkit shouldn't own it
- Codex reads from both locations, so either works functionally

**Alternative considered**: `.agents/` — rejected because it's a shared cross-platform convention not specific to Codex, and doesn't match the `.cursor/`/`.claude/` naming pattern.

### 2. Allowed categories: `skills` only

Codex's structured directory convention only recognizes `skills/`. Files under `commands/`, `agents/`, `rules/`, etc. have no Codex equivalent. The `CodexBuilder` will filter to `skills/` category only.

**Alternative considered**: Copy all categories and let users figure it out — rejected because outputting files Codex can't discover provides no value and creates confusion.

### 3. Opt-in only (not a default platform)

Cursor and Claude Code are included in `DEFAULT_PLATFORM_CONFIGS` so new projects build for both by default. Codex should not be a default because: (a) it's a newer addition, (b) not all users have Codex, (c) adding a third default output directory without user intent is surprising. Users add `codex:` to their `platforms:` section to opt in.

### 4. Builder follows existing pattern exactly

`CodexBuilder` will mirror `ClaudeBuilder`'s structure: constructor takes `FileSystem`, `platform` property returns `PlatformTarget.CODEX`, `build()` filters files by allowed categories, copies via `shutil.copy2`, uses manifest for cleanup. The manifest platform name will be `"codex"` (stored at `.promptkit/managed/codex.txt`).

### 5. No init scaffold change

The init command will not create `.codex/` by default (since Codex is opt-in). No change to `init.py` scaffold dirs. The builder creates the output dir on first build (via `mkdir(parents=True, exist_ok=True)`), which is the existing behavior.

## Risks / Trade-offs

- **Skills-only limitation** — If Codex later adds file-based `commands/` or `rules/` support, the builder will need updating. → Mitigation: Adding categories is a one-line change to `ALLOWED_CATEGORIES`.
- **Path mapping** — Codex skills live at `.codex/skills/<name>/SKILL.md` while source plugins use `skills/<name>/SKILL.md`. The relative paths within `skills/` are preserved as-is, so no path rewriting is needed. The output dir (`.codex`) plus the file path (`skills/<name>/SKILL.md`) produces the correct absolute path.
- **Codex also scans `.agents/skills/`** — Users who want skills in `.agents/` instead can use a custom `output_dir` in config: `codex: .agents`.
