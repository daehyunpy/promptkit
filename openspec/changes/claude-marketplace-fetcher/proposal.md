## Why

`promptkit sync` fails with `"No fetcher registered for registry: claude-plugins-official"` because `cli.py` passes `fetchers={}` to the lock use case. No remote fetcher exists — only `LocalFileFetcher`. Both Claude marketplace registries (`anthropics/claude-plugins-official` and `anthropics/skills`) use the same `marketplace.json` manifest pattern and need a single fetcher implementation.

## What Changes

- **`PromptFetcher.fetch()` returns `list[Prompt]`** instead of `Prompt`. Plugins like `feature-dev` contain multiple `.md` files across subdirectories (`agents/`, `commands/`), so a single `fetch(spec)` call must return all prompts in the plugin. **BREAKING** — all fetcher implementations and their callers must update.
- **New `ClaudeMarketplaceFetcher`** that reads `marketplace.json` from `.claude-plugin/marketplace.json` via the GitHub Contents API, resolves the plugin's `source` path, discovers `.md` files in category subdirectories (`agents/`, `commands/`, `skills/`), and fetches their raw content.
- **`LockPrompts` use case** iterates `list[Prompt]` from `fetch()` instead of a single prompt.
- **CLI wiring** in `_make_lock_use_case` reads registries from config and maps `CLAUDE_MARKETPLACE` type to `ClaudeMarketplaceFetcher(registry.url)`.

## Marketplace Structure (both registries)

Both `anthropics/claude-plugins-official` and `anthropics/skills` follow the same pattern:

```
repo/
├── .claude-plugin/
│   └── marketplace.json      # Registry manifest listing all plugins
├── plugins/                   # (claude-plugins-official uses "plugins/")
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json    # Plugin metadata (name, description, author)
│       ├── agents/            # Category subdirectory with .md files
│       │   ├── agent-a.md
│       │   └── agent-b.md
│       └── commands/          # Another category subdirectory
│           └── command-a.md
└── skills/                    # (skills repo uses "skills/")
    └── <skill-name>/
        ├── SKILL.md           # Skill content (the prompt)
        └── scripts/           # Non-prompt files (ignored)
```

**marketplace.json** schema (shared by both repos):

```json
{
  "name": "registry-name",
  "plugins": [
    {
      "name": "plugin-name",
      "description": "...",
      "source": "./plugins/plugin-name",   // relative path to plugin root
      "skills": ["./skills/xlsx", ...]      // (skills repo: explicit skill paths)
    }
  ]
}
```

**Key differences to handle:**
- **Plugins repo**: `source` points to `./plugins/<name>`, content is `.md` files in category subdirs (`agents/`, `commands/`)
- **Skills repo**: `source` is `"./"` (root), content listed via `skills` array pointing to `./skills/<name>/SKILL.md`

The fetcher reads `marketplace.json` to find the plugin entry, then discovers `.md` files from the resolved source path.

## Capabilities

### New Capabilities
- `claude-marketplace-fetcher`: Remote fetcher that reads plugin/skill content from GitHub-hosted Claude marketplace registries via the Contents API and `marketplace.json` manifest

### Modified Capabilities
- `lock-prompts`: `PromptFetcher.fetch()` signature changes from returning `Prompt` to `list[Prompt]` to support multi-file plugins

## Impact

- **Domain layer**: `PromptFetcher` protocol signature changes (breaking for all implementations)
- **Infrastructure layer**: `LocalFileFetcher.fetch()` wraps return in a list; new `ClaudeMarketplaceFetcher` added
- **Application layer**: `LockPrompts.execute()` loops over list from `fetch()`
- **CLI layer**: `_make_lock_use_case()` loads config to wire fetchers from registries
- **Dependencies**: `httpx` already in `pyproject.toml`
- **Tests**: `FakeFetcher` in `test_lock.py`, assertions in `test_local_file_fetcher.py`, and integration tests all need updating
