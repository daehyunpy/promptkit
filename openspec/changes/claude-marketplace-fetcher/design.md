## Context

`promptkit sync` and `promptkit lock` require a fetcher for each registry declared in `promptkit.yaml`. Currently only `LocalFileFetcher` exists. The CLI wires `fetchers={}`, so any remote prompt spec fails with `"No fetcher registered for registry: ..."`.

Both known registries (`anthropics/claude-plugins-official` and `anthropics/skills`) are GitHub repos with a `.claude-plugin/marketplace.json` manifest. Plugins contain entire directories of files — not just `.md` prompts but also hooks, MCP configs, LSP configs, scripts, and support files. A plugin is the unit of distribution.

The current domain model is built around `Prompt` (single markdown string in memory) and `PromptFetcher` (returns `Prompt`). This doesn't fit — both registry plugins AND local prompts can be multi-file directories with non-markdown content. The model needs to be unified around file trees on disk.

## Goals / Non-Goals

**Goals:**
- Unified model: both local and registry plugins are `Plugin` (file tree on disk)
- Fetch entire plugin directories from GitHub-hosted Claude marketplace registries
- Cache registry plugin directories keyed by commit SHA for reproducibility
- Support both repo structures (plugins repo with relative paths, skills repo with `skills` array)
- Handle all file types — `.md`, `.json`, scripts, configs — not just markdown
- Local prompts can be multi-file directories (not just single `.md` files)
- Single code path in `LockPrompts` and `BuildArtifacts` (no dual model)
- Wire fetchers automatically from config registries in the CLI

**Non-Goals:**
- Supporting non-GitHub registries (e.g., GitLab, self-hosted) — MVP only targets GitHub
- External git URL sources (e.g., `source: {source: "url", url: "..."}`) — MVP only handles relative-path plugins
- Caching `marketplace.json` across runs — fetch fresh each time for simplicity
- Authentication / private repos — public repos only for v1
- Rate limiting or retry logic — fail fast per project coding disciplines
- Transforming file content (rewriting `${CLAUDE_PLUGIN_ROOT}` paths, etc.) — builders just copy
- Hard links or symlinks for build output — just copy files

## Decisions

### 1. Unified `Plugin` domain value object replaces `Prompt`

**Rationale:** Both local and registry plugins are file trees on disk. A single `.md` file is just a degenerate case (a directory with one file). The `Prompt` model (content string in memory) doesn't fit multi-file plugins or non-markdown files. Unifying on `Plugin` eliminates the dual-model complexity.

```python
@dataclass(frozen=True)
class Plugin:
    spec: PromptSpec
    files: tuple[str, ...]        # relative paths within source dir
    source_dir: Path              # where files live on disk
    commit_sha: str | None = None # only for registry plugins
```

- `files`: relative paths like `("agents/reviewer.md", "hooks/hooks.json")`
- `source_dir`: for local → `prompts/{name}/` or `prompts/`. For registry → `.promptkit/cache/plugins/{reg}/{name}/{sha}/`
- `commit_sha`: set for registry plugins, `None` for local

### 2. `PluginFetcher` protocol replaces `PromptFetcher`

**Rationale:** `PromptFetcher.fetch(spec) → Prompt` is the wrong abstraction. The new protocol:

```python
class PluginFetcher(Protocol):
    def fetch(self, spec: PromptSpec, /) -> Plugin: ...
```

`cache_dir` is injected at construction time (configuration), not passed per-call. Each fetcher is constructed with the paths it needs:
- `ClaudeMarketplaceFetcher(registry_url, cache_dir, client=None)`
- `LocalPluginFetcher(file_system, prompts_dir)` — no cache_dir needed, reads from `prompts/` directly

Both implement the protocol. `PromptFetcher` is removed entirely.

### 3. `LocalFileFetcher` → `LocalPluginFetcher` with multi-file support

**Rationale:** Local prompts can be directories with mixed file types, not just single `.md` files. The updated fetcher:

- `discover()`: scans `prompts/` and returns one `PromptSpec` per top-level entry (file or directory)
  - `prompts/my-rule.md` → `PromptSpec(source="local/my-rule")` (single file)
  - `prompts/my-skill/` → `PromptSpec(source="local/my-skill")` (directory with SKILL.md, scripts, etc.)
- `fetch(spec)`: reads from `prompts/`, returns `Plugin(spec, files, source_dir)`
  - `source_dir` points to `prompts/` (local files stay in place, not copied to cache)
  - `files` lists all files for that plugin, relative to `source_dir`

### 4. `PluginCache` for registry plugins only

**Rationale:** Registry plugins need a download cache — they come from GitHub and must be stored locally. Local plugins don't need a cache — they already live in `prompts/`.

```
.promptkit/cache/
└── plugins/                           # Registry plugin cache only
    └── {registry}/{plugin}/{sha}/     # One dir per plugin version
        ├── agents/code-reviewer.md
        ├── commands/feature-dev.md
        ├── hooks/hooks.json
        └── scripts/deploy.sh
```

Cache key is `{registry_name}/{plugin_name}/{commit_sha}`. The commit SHA comes from the GitHub API. The lock file records this SHA for reproducibility — `promptkit lock` only re-downloads when the SHA changes.

`PluginCache` is a read-only lookup: `has()`, `plugin_dir()`, `list_files()`. Fetchers write to the cache directory directly — they call `plugin_dir()` to get the target path, then create directories and write files there. This is fine because both `PluginCache` and fetchers live in the infra layer.

The old content-addressable `PromptCache` (`sha256-*.md` flat files) is removed.

### 5. `LockEntry` gains optional `commit_sha` field; `content_hash` stays `str`

**Rationale:** Registry plugins are versioned by commit SHA, not content hash. The lock file needs to record this for reproducibility. Local plugins continue using `content_hash`.

For registry plugins, `content_hash` is set to `""` (empty string). This avoids a type change to `str | None` which would break all downstream consumers. The `commit_sha` field is the discriminator — if it's set, this is a registry plugin; if `None`, it's a local plugin.

```python
@dataclass(frozen=True)
class LockEntry:
    name: str
    source: str
    content_hash: str              # SHA256 for local, "" for registry plugins
    fetched_at: datetime
    commit_sha: str | None = None  # Only for registry plugins
```

### 6. `content_hash` for local directory plugins — hash of sorted file contents

**Rationale:** Local plugins need `content_hash` for change detection (preserve `fetched_at` when nothing changed). For single files: `sha256(content)` (unchanged). For directories: sort files by relative path, concatenate `path + "\n" + content` for each, hash the result. Deterministic and stable.

### 7. One lock entry per plugin (not per file)

**Rationale:** One lock entry per plugin (one per `PromptSpec` in config, one per discovered local plugin). The lock entry records the plugin name, source, commit SHA (if registry), content hash (if local), and timestamp. Individual files are tracked implicitly via the cached directory or the local `prompts/` structure.

### 8. Fetchers download all files — builders decide what to copy per platform

**Rationale:** Fetchers download the entire plugin file tree without filtering. At build time, each builder decides what to copy based on its platform. Claude Code copies everything. Cursor skips unsupported categories (agents, commands, hooks) and applies directory mapping (e.g., `skills/` → `skills-cursor/`). No files are excluded at the fetch/cache layer — only builders filter. Files are just copied — no hard links, no symlinks, no content transformation.

For local plugins: source is `prompts/`.
For registry plugins: source is `.promptkit/cache/plugins/{registry}/{plugin}/{sha}/`.

This is a single code path — builders don't need to know whether the source is local or remote.

### 9. Builder protocol receives `list[Plugin]`

**Rationale:** The `ArtifactBuilder.build()` method receives `list[Plugin]` and `output_dir`. Each `Plugin` has `source_dir` and `files`. The builder iterates plugins and copies from each `source_dir`. The builder already imports domain types (`PlatformTarget`), so depending on `Plugin` is fine.

### 10. GitHub Contents API + `download_url` for file fetching

**Rationale:** The Contents API (`api.github.com/repos/{owner}/{repo}/contents/{path}`) returns directory listings with `download_url` fields for each file. We use it to:
1. Fetch `marketplace.json` to find the plugin entry
2. Get the latest commit SHA for the default branch
3. List the plugin directory recursively
4. Download each file via its `download_url`

### 11. Skills repo `skills` array handling

**Rationale:** The skills repo uses `source: "./"` (repo root) with a `skills` array listing explicit skill paths. The fetcher detects the `skills` array in the marketplace entry and fetches each listed skill directory instead of walking the `source` path.

### 12. Skip external git URL sources for MVP

**Rationale:** Plugins like `atlassian`, `figma`, `vercel` use `source: {source: "url", url: "https://...git"}`. These point to entirely different repos. Handling them requires git clone or a different fetch strategy. Deferred to post-MVP. The fetcher raises a `SyncError` for these entries.

### 13. Injectable `httpx.Client` for testability

**Rationale:** The fetcher accepts an optional `httpx.Client` in the constructor. Production code uses the default (creates its own client). Tests inject a mock/fake client.

### 14. CLI wiring: `_make_fetchers()` helper reads config registries

**Rationale:** The CLI needs to load `promptkit.yaml` to discover registries before creating the `LockPrompts` use case. A `_make_fetchers(registries)` helper maps each `CLAUDE_MARKETPLACE` registry to a `ClaudeMarketplaceFetcher(registry.url)`. Local fetcher is always created.

## Data Flow

### Lock (fetch + lock)

```
promptkit.yaml → registries + prompt specs
    ↓
For each registry spec:
    fetcher.fetch(spec) → Plugin(spec, files, source_dir=cache_dir, commit_sha=sha)
      (internally: marketplace.json → resolve path → check SHA → download to cache)
    LockPrompts creates LockEntry(name, source, content_hash="", fetched_at, commit_sha=sha)

For each local spec (discovered from prompts/):
    fetcher.fetch(spec) → Plugin(spec, files, source_dir=prompts/, commit_sha=None)
    LockPrompts computes content_hash by reading files from plugin.source_dir
    LockPrompts creates LockEntry(name, source, content_hash=hash, fetched_at, commit_sha=None)

Write promptkit.lock (sorted by name)
```

**Note:** `content_hash` is computed in `LockPrompts` (app layer), not in `Plugin` (domain). Plugin is a pure manifest — no file I/O, no hashing. The app layer reads files via `FileSystem` protocol to compute the hash.

### Build (source → artifacts)

```
promptkit.lock → lock entries
promptkit.yaml → platform configs
    ↓
For each lock entry:
    Resolve source dir:
      If commit_sha → .promptkit/cache/plugins/{registry}/{plugin}/{sha}/
      If no commit_sha → prompts/ (local)
    For each platform:
      Copy entire file tree from source_dir to platform output_dir
      Apply directory mapping (skills/ → skills-cursor/ for Cursor)
      No file filtering — platforms ignore unknown files
```

## Risks / Trade-offs

**GitHub API rate limiting** → Unauthenticated: 60 requests/hour. Listing a plugin directory recursively may use 5-10 calls. Mitigated by commit SHA check — if SHA hasn't changed, skip entirely (0 API calls). Clear error on 403.

**marketplace.json format changes** → Fail with clear `SyncError` if expected fields are missing. We track the upstream spec in `docs/references/claude-marketplace-spec.md`.

**Large plugin directories** → Some plugins may have many files. The fetcher downloads all of them. Acceptable for MVP — plugins are typically small (< 50 files). Could add file-count limits later.

**Breaking change to existing tests** → Replacing `Prompt` with `Plugin` and `PromptFetcher` with `PluginFetcher` requires updating all existing tests. This is the right trade-off — simpler unified model is worth the migration cost.

**External plugins deferred** → Users who want `atlassian` or `figma` plugins get a clear error message. Post-MVP: add git clone support for external sources.
