## Context

`promptkit sync` and `promptkit lock` require a `PromptFetcher` for each registry declared in `promptkit.yaml`. Currently only `LocalFileFetcher` exists. The CLI wires `fetchers={}`, so any remote prompt spec fails with `"No fetcher registered for registry: ..."`.

Both known registries (`anthropics/claude-plugins-official` and `anthropics/skills`) are GitHub repos with a `.claude-plugin/marketplace.json` manifest. Plugins can be single-file (e.g., `code-simplifier` with one agent `.md`) or multi-file (e.g., `feature-dev` with 3 agents + 1 command across subdirectories).

The current `PromptFetcher` protocol returns a single `Prompt`, which cannot represent multi-file plugins.

## Goals / Non-Goals

**Goals:**
- Fetch remote prompts from GitHub-hosted Claude marketplace registries
- Support both single-file and multi-file plugins in a single `fetch()` call
- Use `marketplace.json` as the source of truth for discovering plugin content paths
- Handle both repo structures (plugins repo with category subdirs, skills repo with `SKILL.md` files)
- Wire fetchers automatically from config registries in the CLI

**Non-Goals:**
- Supporting non-GitHub registries (e.g., GitLab, self-hosted) — MVP only targets GitHub
- Caching `marketplace.json` across runs — fetch fresh each time for simplicity
- Authentication / private repos — public repos only for v1
- Rate limiting or retry logic — fail fast per project coding disciplines

## Decisions

### 1. `PromptFetcher.fetch()` returns `list[Prompt]` instead of `Prompt`

**Rationale:** A plugin like `feature-dev` has 4 `.md` files (3 agents + 1 command). These all belong to a single `PromptSpec` (source: `claude-plugins-official/feature-dev`), but produce multiple lock entries and cached files. Returning a list is the minimal change that models this correctly.

**Alternative considered:** Keep `fetch() → Prompt` and have the fetcher call it multiple times internally — rejected because the caller has one `PromptSpec` and doesn't know how many files exist in the plugin. The fetcher discovers them.

**Alternative considered:** A new `PluginFetcher` protocol separate from `PromptFetcher` — rejected as unnecessary complexity. One protocol with a list return handles both single and multi-file cases.

### 2. Use GitHub Contents API for directory discovery, `download_url` for file content

**Rationale:** The Contents API (`api.github.com/repos/{owner}/{repo}/contents/{path}`) returns directory listings with `download_url` fields for each file. This avoids cloning repos or parsing HTML. Two API calls per plugin: one to list the plugin directory, one per subdirectory to find `.md` files.

**Alternative considered:** Raw GitHub URLs (`raw.githubusercontent.com`) — rejected because raw URLs require knowing exact file paths upfront. We need directory listing to discover `.md` files.

**Alternative considered:** Git tree API (`/git/trees/{sha}?recursive=1`) — a single call to get the full tree. Rejected for now as it requires knowing the tree SHA and returns the entire repo tree. Contents API is simpler for targeted directory reads.

### 3. Read `marketplace.json` to find plugin source path

**Rationale:** The `marketplace.json` manifest at `.claude-plugin/marketplace.json` maps plugin names to their `source` paths (e.g., `"./plugins/feature-dev"`). This is authoritative — we don't guess paths.

**Flow:**
1. Fetch `marketplace.json` from the registry repo
2. Find the plugin entry by `name` matching `spec.prompt_name`
3. Resolve the `source` path relative to repo root (strip `./` prefix)
4. For plugins with category subdirs: list the source dir, recurse into subdirs, collect `.md` files
5. For skills with a `skills` array: follow each skill path, fetch `SKILL.md` from that directory

### 4. Source path format for lock entries: `{registry}/{category}/{filename}`

**Rationale:** The `Prompt.category` property derives the category from the source path (splits on `/`, takes the middle segment). For a prompt with source `claude-plugins-official/agents/code-reviewer`, category resolves to `agents`. This routes the prompt to the correct platform output directory during build.

For the skills repo, a skill's source would be `anthropic-agent-skills/skills/{skill-name}`, giving category `skills`.

### 5. Injectable `httpx.Client` for testability

**Rationale:** The fetcher accepts an optional `httpx.Client` in the constructor. Production code uses the default (creates its own client). Tests inject a mock/fake client. This follows the project's protocol-based testing pattern.

### 6. CLI wiring: `_make_fetchers()` helper reads config registries

**Rationale:** The CLI needs to load `promptkit.yaml` to discover registries before creating the `LockPrompts` use case. A `_make_fetchers(registries)` helper maps each `CLAUDE_MARKETPLACE` registry to a `ClaudeMarketplaceFetcher`. This keeps CLI code minimal.

The `_make_lock_use_case` function already has access to `cwd` and `fs`. It will load the config via `YamlLoader` to get the registry list, then build fetchers. This means the config is loaded twice (once in CLI, once in `LockPrompts.execute()`), but this is acceptable for simplicity — the config file is small and local.

## Risks / Trade-offs

**GitHub API rate limiting** → The unauthenticated GitHub API allows 60 requests/hour. A plugin with 5 subdirectories costs ~7 API calls (1 marketplace.json + 1 plugin dir + 5 subdirs). For typical usage (1-5 plugins), this is well within limits. Mitigation: clear error message when rate-limited (HTTP 403).

**marketplace.json format changes** → If Anthropic changes the manifest schema, the fetcher breaks. Mitigation: fail with a clear `SyncError` if expected fields are missing. The schema is unlikely to change without notice.

**Multi-file plugins expand `promptkit.lock` entries** → A user adding `claude-plugins-official/feature-dev` gets 4 lock entries instead of 1. This is correct behavior — each `.md` file is independently cacheable and buildable — but may surprise users. Mitigation: document this in sync output.

**Double config load in CLI** → Loading `promptkit.yaml` both in CLI (to get registries) and in `LockPrompts.execute()` is redundant but simple. Mitigation: acceptable for now; could be refactored later to pass registries from outside.
