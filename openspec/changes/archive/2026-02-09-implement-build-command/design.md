## Context

Phase 5 completed the lock command — prompts are fetched, cached in `.promptkit/cache/` by SHA256 hash, and recorded in `promptkit.lock`. The `ArtifactBuilder` protocol is already defined in `domain/protocols.py` with a `build(prompts, output_dir)` signature. The `PlatformConfig` value object carries the platform type and output directory. The build system needs to connect these pieces.

**Key constraint from technical design:** Build is a deterministic copy+route operation. No content transformation. Source category directories determine output subdirectories.

## Goals / Non-Goals

**Goals:**
- Implement `CursorBuilder` and `ClaudeBuilder` that route prompts to platform-specific directories
- Implement `BuildArtifacts` use case that loads config + lock, reads prompts, and delegates to builders
- Wire up `promptkit build` CLI command
- Clean output directories before each build (prevent stale artifacts)

**Non-Goals:**
- AI-assisted prompt transformation (post-MVP)
- Content modification or frontmatter stripping (MVP copies content as-is)
- Progress indicators (Phase 10)
- Building from config alone without a lock file (lock-first workflow)

## Decisions

### 1. Category is derived from the prompt source path

**Decision:** The prompt's category (skills, rules, commands, agents, subagents) is extracted from its source path. For local prompts with source `local/skills/my-skill`, the category is `skills`. For remote prompts with source `registry/prompt-name`, the category comes from the cached content's directory structure (deferred to Phase 9 when remote fetchers exist). For flat local prompts with source `local/my-rule` (no subdirectory), the category defaults to `rules`.

**Alternative considered:** Store category in LockEntry. Rejected — this adds a field to the lock schema that duplicates what's already in the source path.

### 2. Builders implement the existing ArtifactBuilder protocol

**Decision:** `CursorBuilder` and `ClaudeBuilder` implement the `ArtifactBuilder` protocol already defined in `domain/protocols.py`. Each builder receives a list of `Prompt` objects and an output directory, then writes files according to its platform's routing rules.

The protocol's `build()` method receives prompts already filtered for the platform — the use case handles filtering via `prompt.is_valid_for_platform()`.

### 3. Builders clean their output directory before writing

**Decision:** Each builder clears its platform output directory before writing new artifacts. This prevents stale artifacts from previous builds. The use case calls the builder once per platform with all prompts for that platform.

**Alternative considered:** Incremental builds that only update changed files. Rejected for MVP — full rebuild is simpler, deterministic, and fast enough for the expected prompt count.

### 4. BuildArtifacts use case requires a lock file

**Decision:** `BuildArtifacts` reads `promptkit.lock` to know which prompts to build. It loads each prompt's content from the cache (remote) or `prompts/` directory (local) using the lock entry's hash and source. If the lock file doesn't exist, it raises a `BuildError`.

This enforces the lock-first workflow: you must `lock` before you can `build`.

### 5. Category-to-directory routing is defined as data, not logic

**Decision:** Each builder defines a mapping from source category to output subdirectory as a simple dict. This makes the routing rules visible and testable without reading through branching logic.

```python
# CursorBuilder
CATEGORY_DIRS = {"skills": "skills-cursor", "rules": "rules", ...}

# ClaudeBuilder
CATEGORY_DIRS = {"skills": "skills", "rules": "rules", ...}
```

### 6. Frontmatter is NOT stripped in MVP

**Decision:** Build copies content as-is. Both Cursor and Claude Code can handle markdown with YAML frontmatter. Stripping frontmatter adds complexity without clear benefit for MVP.

## Risks / Trade-offs

- **No remote prompt category routing yet** — remote prompts (Phase 9) will need category info from the fetcher. The current design supports this: the source path will include category info from the registry structure.
- **Full rebuild on every `build`** — acceptable for MVP prompt counts (tens of prompts, not thousands). Incremental builds can be added later if needed.
- **Default category for flat local prompts** — prompts at `prompts/my-rule.md` (no subdirectory) default to `rules` category. This is a reasonable default but may surprise users who expect a different placement.
