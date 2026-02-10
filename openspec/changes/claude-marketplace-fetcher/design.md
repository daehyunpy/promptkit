## Context

`promptkit sync` and `promptkit lock` require a fetcher for each registry declared in `promptkit.yaml`. Currently only `LocalFileFetcher` exists. The CLI wires `fetchers={}`, so any remote prompt spec fails with `"No fetcher registered for registry: ..."`.

Both known registries (`anthropics/claude-plugins-official` and `anthropics/skills`) are GitHub repos with a `.claude-plugin/marketplace.json` manifest. Plugins contain entire directories of files — not just `.md` prompts but also hooks, MCP configs, LSP configs, scripts, and support files. A plugin is the unit of distribution.

The current domain model is built around `Prompt` (single markdown string) and `PromptFetcher` (returns `Prompt`). This doesn't fit the plugin model — we need a new domain concept for fetched plugin directories.

## Goals / Non-Goals

**Goals:**
- Fetch entire plugin directories from GitHub-hosted Claude marketplace registries
- Cache complete plugin directories keyed by commit SHA for reproducibility
- Support both repo structures (plugins repo with relative paths, skills repo with `skills` array)
- Handle all file types — `.md`, `.json`, scripts, configs — not just markdown
- Wire fetchers automatically from config registries in the CLI
- Lock file records commit SHA per plugin for deterministic re-builds

**Non-Goals:**
- Supporting non-GitHub registries (e.g., GitLab, self-hosted) — MVP only targets GitHub
- External git URL sources (e.g., `source: {source: "url", url: "..."}`) — MVP only handles relative-path plugins
- Caching `marketplace.json` across runs — fetch fresh each time for simplicity
- Authentication / private repos — public repos only for v1
- Rate limiting or retry logic — fail fast per project coding disciplines
- Transforming file content (rewriting `${CLAUDE_PLUGIN_ROOT}` paths, etc.) — builders just copy

## Decisions

### 1. New `Plugin` domain value object (manifest, not content)

**Rationale:** A plugin is a directory of files, not a single markdown string. The `Prompt` model doesn't fit. But we don't need to load all file contents into memory — the fetcher downloads files to a cache directory on disk, and the `Plugin` object is just a manifest: spec + commit SHA + list of relative file paths.

```python
@dataclass(frozen=True)
class Plugin:
    spec: PromptSpec
    commit_sha: str
    files: tuple[str, ...]  # relative paths within plugin dir
```

`Prompt` stays for local prompts (which genuinely are single `.md` files with content in memory).

### 2. New `PluginFetcher` protocol separate from `PromptFetcher`

**Rationale:** `PromptFetcher.fetch(spec) → Prompt` is the wrong abstraction for plugins. Instead of stretching it, introduce `PluginFetcher.fetch(spec, cache_dir) → Plugin`. The fetcher downloads files to `cache_dir` and returns a manifest.

The previous design changed `PromptFetcher.fetch()` to return `list[Prompt]` — this is reverted. `PromptFetcher` remains for local prompts. `PluginFetcher` is the new protocol for remote registries.

**Alternative considered:** Keep single `PromptFetcher` with `list[Prompt]` return — rejected because it forces loading all file content into memory and doesn't model non-markdown files.

### 3. Directory-based `PluginCache` keyed by commit SHA

**Rationale:** The current `PromptCache` is content-addressable (SHA256 of content string, flat file storage). This doesn't work for multi-file plugin directories. Instead:

```
.promptkit/cache/
├── plugins/                           # Remote plugin cache
│   └── {registry}/{plugin}/{sha}/     # One dir per plugin version
│       ├── agents/code-reviewer.md
│       ├── commands/feature-dev.md
│       ├── hooks/hooks.json
│       └── scripts/deploy.sh
└── sha256-*.md                        # Legacy content-addressable (local prompts)
```

Cache key is `{registry_name}/{plugin_name}/{commit_sha}`. The commit SHA comes from the GitHub API (latest commit on default branch). The lock file records this SHA for reproducibility — `promptkit lock` only re-downloads when the SHA changes.

### 4. `LockEntry` gains optional `commit_sha` field

**Rationale:** Remote plugins are versioned by commit SHA, not content hash. The lock file needs to record this for reproducibility. Local prompts continue using `content_hash`.

```python
@dataclass(frozen=True)
class LockEntry:
    name: str
    source: str
    content_hash: str
    fetched_at: datetime
    commit_sha: str | None = None  # Only for remote plugins
```

This is backward-compatible — existing lock files without `commit_sha` still parse correctly.

### 5. One lock entry per plugin (not per file)

**Rationale:** The previous design created one lock entry per `.md` file in a plugin (e.g., `feature-dev` → 4 entries). With the new model, one lock entry per `PromptSpec` in config. The lock entry records the plugin name, source, commit SHA, and timestamp. Individual files are tracked implicitly via the cached directory.

### 6. Builders copy from plugin cache directory

**Rationale:** At build time, builders read files from the plugin cache directory (not from `Prompt` objects in memory). The builder walks the cached plugin directory and copies files to the platform output directory, applying directory structure mapping (e.g., `skills/` → `skills-cursor/` for Cursor).

For local prompts, the existing `Prompt`-based build path is unchanged.

### 7. GitHub Contents API + `download_url` for file fetching

**Rationale:** The Contents API (`api.github.com/repos/{owner}/{repo}/contents/{path}`) returns directory listings with `download_url` fields for each file. We use it to:
1. Fetch `marketplace.json` to find the plugin entry
2. Get the latest commit SHA for the default branch
3. List the plugin directory recursively
4. Download each file via its `download_url`

### 8. Skills repo `skills` array handling

**Rationale:** The skills repo uses `source: "./"` (repo root) with a `skills` array listing explicit skill paths. The fetcher detects the `skills` array in the marketplace entry and fetches each listed skill directory instead of walking the `source` path.

### 9. Skip external git URL sources for MVP

**Rationale:** Plugins like `atlassian`, `figma`, `vercel` use `source: {source: "url", url: "https://...git"}`. These point to entirely different repos. Handling them requires git clone or a different fetch strategy. Deferred to post-MVP. The fetcher logs a warning and skips these entries.

### 10. Injectable `httpx.Client` for testability

**Rationale:** The fetcher accepts an optional `httpx.Client` in the constructor. Production code uses the default (creates its own client). Tests inject a mock/fake client.

### 11. CLI wiring: `_make_fetchers()` helper reads config registries

**Rationale:** The CLI needs to load `promptkit.yaml` to discover registries before creating the `LockPrompts` use case. A `_make_fetchers(registries)` helper maps each `CLAUDE_MARKETPLACE` registry to a `ClaudeMarketplaceFetcher(registry.url)`.

## Data Flow

### Lock (fetch + lock)

```
promptkit.yaml → registries + prompt specs
    ↓
For each remote spec:
    marketplace.json → find plugin entry → resolve source path
    GitHub API → get latest commit SHA for default branch
    If SHA matches lock → skip (already cached)
    Otherwise → list plugin dir → download all files → write to cache
    Return Plugin(spec, commit_sha, files)
    Write LockEntry(name, source, content_hash="", commit_sha=sha, fetched_at)
For each local spec:
    LocalFileFetcher → Prompt → cache content → LockEntry (unchanged)
Write promptkit.lock
```

### Build (cache → artifacts)

```
promptkit.lock → lock entries
promptkit.yaml → platform configs
    ↓
For each lock entry:
    If local → read from prompts/ → Prompt → builder.build()
    If remote → resolve cache dir from commit_sha → copy files to output
        Apply directory mapping (skills/ → skills-cursor/ for Cursor)
        Copy all non-md files as-is
```

## Risks / Trade-offs

**GitHub API rate limiting** → Unauthenticated: 60 requests/hour. Listing a plugin directory recursively may use 5-10 calls. Mitigated by commit SHA check — if SHA hasn't changed, skip entirely (0 API calls). Clear error on 403.

**marketplace.json format changes** → Fail with clear `SyncError` if expected fields are missing. We track the upstream spec in `docs/references/claude-marketplace-spec.md`.

**Large plugin directories** → Some plugins may have many files. The fetcher downloads all of them. Acceptable for MVP — plugins are typically small (< 50 files). Could add file-count limits later.

**Dual model complexity** → Local prompts use `Prompt` (content in memory), remote plugins use `Plugin` (files on disk). This creates two code paths in `LockPrompts` and `BuildArtifacts`. Acceptable trade-off — the models genuinely differ.

**External plugins deferred** → Users who want `atlassian` or `figma` plugins get a clear error message. Post-MVP: add git clone support for external sources.
