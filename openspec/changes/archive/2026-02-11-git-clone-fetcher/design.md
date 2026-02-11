## Context

The `ClaudeMarketplaceFetcher` currently uses the GitHub Contents API (`api.github.com/repos/{owner}/{repo}/contents/...`) to fetch marketplace plugins. Each plugin requires multiple HTTP requests: marketplace manifest, commit SHA, directory listings (recursive), and individual file downloads. The unauthenticated GitHub API rate limit of 60 requests/hour makes this approach unviable for normal usage.

Claude Code's own plugin system uses `git clone --depth 1` to fetch entire marketplace repos in a single operation, avoiding REST API rate limits entirely. We adopt the same pattern.

Current fetcher architecture:
- `ClaudeMarketplaceFetcher` implements `PluginFetcher` protocol (`fetch(spec) -> Plugin`)
- Uses `httpx.Client` for all GitHub API calls
- Writes files to `PluginCache` at `.promptkit/cache/plugins/{registry}/{plugin}/{sha}/`
- Cache check skips re-download if SHA matches

## Goals / Non-Goals

**Goals:**
- Eliminate GitHub REST API rate limit issues by using git protocol
- Maintain the existing `PluginFetcher` protocol contract (no domain/app layer changes)
- Preserve the existing `PluginCache` structure (`{registry}/{plugin}/{sha}/`)
- Support first-run clone and incremental updates (git pull)
- Keep marketplace clones out of version control (`.gitignore`)

**Non-Goals:**
- Supporting non-GitHub registries (SSH-only, GitLab, etc.) — MVP stays GitHub HTTPS
- Sparse checkout or partial clone — shallow clone of full repo is simple and sufficient (~5MB)
- Authentication for private repos — public marketplace repos only for MVP
- Parallel cloning of multiple registries — sequential is fast enough for MVP

## Decisions

### 1. Use `subprocess` to run git CLI instead of a Python git library

**Decision**: Shell out to `git` via `subprocess.run()`.

**Alternatives considered**:
- `GitPython` (pygit2): Adds a heavy dependency with C bindings. Overkill for 3 git commands.
- `dulwich` (pure Python git): Lighter but still a new dependency. Our needs are trivial.

**Rationale**: We need exactly 3 git operations: `clone --depth 1`, `pull`, and `rev-parse HEAD`. `subprocess` is zero-dependency, well-tested, and matches how Claude Code does it. The git CLI is a safe assumption for promptkit's target audience (developers).

### 2. Persistent clone at `.promptkit/registries/{registry_name}/`

**Decision**: Keep the shallow clone between runs. Use `git pull` for updates.

**Alternatives considered**:
- Ephemeral clone (clone to temp dir, copy files, delete): Simpler but re-downloads ~5MB every `promptkit lock`. Wastes bandwidth on repeated runs.
- Clone inside `.promptkit/cache/`: Conflates cache (immutable, SHA-keyed) with mutable clone state.

**Rationale**: `.promptkit/registries/` is a distinct directory for mutable clone state, separate from the immutable cache. First run: `git clone --depth 1`. Subsequent runs: `git pull` (transfers only deltas). The ~5MB cost is negligible for modern systems.

### 3. Extract `GitRegistryClone` as a separate infrastructure class

**Decision**: Create a new `GitRegistryClone` class that encapsulates git operations. `ClaudeMarketplaceFetcher` delegates to it.

**Alternatives considered**:
- Inline git calls directly in `ClaudeMarketplaceFetcher`: Mixes fetch logic with git plumbing. Harder to test (must mock subprocess in fetcher tests).
- Use a protocol/interface: Over-engineering — we only have one git backend.

**Rationale**: Separation of concerns. `GitRegistryClone` handles clone/pull/rev-parse. `ClaudeMarketplaceFetcher` handles marketplace.json parsing, plugin resolution, and file copying. Each class is independently testable. `GitRegistryClone` can be tested with a real temp git repo; the fetcher can be tested with a mock clone.

### 4. Copy files from clone to cache (not symlink or hard link)

**Decision**: `shutil.copytree` / `shutil.copy2` from clone dir to cache dir.

**Alternatives considered**:
- Symlinks: Cache entries would break if the clone updates (git pull changes files in-place).
- Hard links: Same problem — git pull replaces files, breaking hard links on some filesystems.
- Read directly from clone (skip cache): Breaks the cache invariant — cached plugins must be immutable snapshots keyed by SHA.

**Rationale**: The cache must hold an immutable snapshot at a specific commit SHA. The clone is mutable (git pull updates it). Copying preserves the existing cache contract. The copy is fast (local filesystem, small files).

### 5. Read marketplace.json from the local clone filesystem

**Decision**: `json.loads(Path(...).read_text())` instead of HTTP GET + base64 decode.

**Rationale**: The clone already has the file. Direct filesystem read is simpler, faster, and has no rate limit. The base64 decoding layer was a GitHub API artifact, not a domain concern.

### 6. Git error handling strategy

**Decision**: Wrap git subprocess failures in `SyncError` with the stderr output.

**Rationale**: Consistent with existing error handling. `SyncError` is the established domain error for fetch failures. Git stderr messages are developer-readable and actionable (e.g., "repository not found", "could not resolve host").

## Risks / Trade-offs

- **[Risk] git not installed** → Check for git availability at fetcher construction time. Raise a clear `SyncError("git is required but not found on PATH")` before attempting any operations.
- **[Risk] Clone corruption** → If `.promptkit/registries/{name}/` exists but is corrupted, `git pull` will fail. Mitigation: catch git errors, delete the corrupt clone, and re-clone from scratch.
- **[Risk] Disk space for full repo clone** → The `claude-plugins-official` repo is ~5MB. Acceptable. If future registries are larger, we can revisit with sparse checkout.
- **[Trade-off] Requires git CLI** → All promptkit users are developers. Git is ubiquitous. This is the same requirement Claude Code imposes.
- **[Trade-off] First lock is slower** → `git clone --depth 1` transfers the entire repo (~5MB) vs only the needed files. But subsequent locks are faster (delta pull), and there are no rate limit failures. Net positive.

## Resolved Questions

### Multiple registries: sequential or parallel?
**Sequential.** Each `GitRegistryClone` is independent (one per registry). A shallow clone takes 2-3 seconds; `git pull` is sub-second. Even with 3 registries, sequential is under 10 seconds. The architecture doesn't prevent parallelism later — each clone is an independent object. Not worth the complexity for MVP.

### Clone URL: HTTPS or SSH?
**Always HTTPS.** Marketplace repos are public — HTTPS works without authentication. SSH requires key setup, adding friction for a tool that should "just work." Claude Code itself uses HTTPS for marketplace clones. If a user needs SSH for a private registry, that's post-MVP scope.

### httpx removal scope?
**Remove `httpx` from `pyproject.toml` entirely.** The only runtime import of `httpx` is in `claude_marketplace.py`, which this change rewrites. No other source file imports it. Tests that mock httpx responses are rewritten too. Keeping an unused dependency is dead code — the project policy is "no dead code." Re-adding it is one line if needed later.
