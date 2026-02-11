## Why

The `ClaudeMarketplaceFetcher` uses the GitHub Contents API to download plugins file-by-file. Each plugin fetch requires N+2 HTTP requests (marketplace.json, commit SHA, then 1 per directory listing + 1 per file download). The unauthenticated GitHub API rate limit is 60 requests/hour — locking 3-4 plugins exhausts it and produces a `403 rate limit exceeded` error. This makes promptkit unusable without a GitHub token.

Claude Code itself solves this by using `git clone --depth 1` instead of REST API calls. The git protocol has no per-request rate limit, and a single shallow clone fetches the entire marketplace in one atomic operation regardless of how many plugins are needed.

## What Changes

- **BREAKING**: Replace GitHub Contents API fetching with shallow git clone in `ClaudeMarketplaceFetcher`
- Add persistent marketplace clone at `.promptkit/registries/{registry_name}/` (shallow git repo)
- On first lock: `git clone --depth 1` the marketplace repo
- On subsequent locks: `git pull` to update the existing clone (delta transfer only)
- Read `marketplace.json` from local clone instead of REST API
- Get commit SHA from local `git rev-parse HEAD` instead of REST API
- Copy plugin files from local clone to `.promptkit/cache/plugins/{registry}/{plugin}/{sha}/` (existing cache structure preserved)
- Add `.promptkit/registries/` to `.gitignore` (clones are ephemeral, re-cloneable)
- Remove `httpx` dependency from `ClaudeMarketplaceFetcher` (no more REST API calls)
- Zero GitHub API calls for any lock operation

## Capabilities

### New Capabilities
- `git-registry-clone`: Shallow git clone management for marketplace registries — clone, pull, read files from local clone at `.promptkit/registries/`

### Modified Capabilities
- `claude-marketplace-fetcher`: Replace HTTP-based fetching with local filesystem reads from the git clone. Same `PluginFetcher` protocol contract, different transport mechanism.

## Impact

- **Infrastructure layer only**: `ClaudeMarketplaceFetcher` internals change completely, but the `PluginFetcher` protocol contract is unchanged. No domain or application layer changes.
- **Dependencies**: Removes runtime dependency on `httpx` for marketplace fetching. Adds requirement for `git` CLI on user's machine (standard for developer tooling).
- **Disk**: Adds ~5MB per marketplace clone in `.promptkit/registries/`. Offset by eliminating redundant per-file downloads.
- **Network**: Reduces from O(files) HTTP requests to O(1) git operations per lock. Subsequent locks use `git pull` (delta only).
- **Tests**: Marketplace fetcher tests need rework — mock `subprocess` calls instead of `httpx` responses. Test doubles for git operations.
- **Gitignore**: `.promptkit/registries/` added to `.gitignore` template (both project and `init` command output).
- **Existing cache**: `.promptkit/cache/plugins/` structure unchanged. Plugins still cached by `{registry}/{plugin}/{sha}/`.
