# Platform Directory Structure Reference

> **Reference snapshot** — platform directory specs for promptkit builder design.
> This is NOT a promptkit doc. It tracks upstream platform constraints.

| Field | Value |
|-------|-------|
| Sources | code.claude.com/docs, cursor.directory, github.com/anthropics/claude-code#16438 |
| Captured | 2026-02-10 |

---

## Claude Code `.claude/`

Full spec at [Plugins Reference](https://code.claude.com/docs/en/plugins-reference).

```
.claude/
├── settings.json              # Project settings + enabled plugins
├── settings.local.json        # Local settings (gitignored)
├── CLAUDE.md                  # Project memory / context
├── agents/                    # Subagent markdown files (FLAT)
│   └── *.md                   #   frontmatter: name, description, tools, model, hooks, skills
├── skills/                    # Skills (ONE LEVEL nesting only)
│   └── <name>/                #   one dir per skill
│       ├── SKILL.md           #   frontmatter: name, description, disable-model-invocation
│       ├── scripts/           #   optional support files
│       └── reference.md       #   optional references
├── commands/                  # Slash commands / legacy skills (FLAT)
│   └── *.md                   #   frontmatter same as skills
├── hooks/                     # Hook configurations
│   └── hooks.json             #   JSON: event → matcher → command/prompt/agent
├── .mcp.json                  # MCP server definitions
├── .lsp.json                  # LSP server configurations
├── agent-memory/              # Persistent subagent memory (project scope)
│   └── <agent-name>/
│       └── MEMORY.md
└── agent-memory-local/        # Persistent subagent memory (gitignored)
```

### Nesting Constraints

| Component | Structure | Max Depth | Notes |
|-----------|-----------|-----------|-------|
| **Skills** | `skills/<name>/SKILL.md` | 1 level | Subdirs inside skill dir OK (scripts/, references) |
| **Agents** | `agents/*.md` | Flat | No subdirectories |
| **Commands** | `commands/*.md` | Flat | Merged into skills system; legacy but still works |
| **Hooks** | `hooks/hooks.json` | Single file | Additional hook files referenced from plugin.json |
| **MCP** | `.mcp.json` | Single file | At project or plugin root |
| **LSP** | `.lsp.json` | Single file | At project or plugin root |

[Issue #16438](https://github.com/anthropics/claude-code/issues/16438): Feature request for nested skill directories (`skills/<category>/<name>/SKILL.md`) — not yet supported.

### SKILL.md Format

```yaml
---
name: skill-name                    # kebab-case, max 64 chars (optional, defaults to dir name)
description: What this skill does   # recommended — Claude uses for auto-invocation
disable-model-invocation: true      # optional — prevent Claude auto-loading
user-invocable: false               # optional — hide from /menu
allowed-tools: Read, Grep, Glob     # optional — tool restrictions
model: sonnet                       # optional — model override
context: fork                       # optional — run in subagent
agent: Explore                      # optional — subagent type when context: fork
---

Skill instructions in markdown...
```

### Agent .md Format

```yaml
---
name: agent-name                    # required, kebab-case
description: When to use this agent # required
tools: Read, Grep, Glob, Bash      # optional — inherits all if omitted
disallowedTools: Write, Edit        # optional — denylist
model: sonnet                       # optional — sonnet/opus/haiku/inherit
permissionMode: default             # optional — default/acceptEdits/dontAsk/bypassPermissions/plan
maxTurns: 10                        # optional
skills:                             # optional — preloaded skills
  - skill-name
hooks:                              # optional — lifecycle hooks
  PreToolUse: [...]
memory: user                        # optional — user/project/local
---

System prompt in markdown...
```

---

## Cursor `.cursor/`

No single published spec. Gathered from [Cursor docs](https://cursor.directory/) and community sources.

```
.cursor/
├── rules/                     # Project rules (FLAT)
│   └── *.mdc                  #   frontmatter: description, globs, alwaysApply
├── skills/                    # Skills (ONE LEVEL — same as Claude Code)
│   └── <name>/
│       ├── SKILL.md
│       └── scripts/           # optional
└── skill-packs/               # Optional skill pack configs
    └── *.json
```

### Nesting Constraints

| Component | Structure | Max Depth | Notes |
|-----------|-----------|-----------|-------|
| **Skills** | `skills/<name>/SKILL.md` | 1 level | Same Agent Skills standard as Claude Code |
| **Rules** | `rules/*.mdc` | Flat | `.mdc` format (markdown + YAML frontmatter) |

### What Cursor DOESN'T have (file-based)

- No `agents/` directory (agent mode is IDE-integrated)
- No `commands/` directory (uses IDE command palette)
- No `hooks/` (no hook system)
- No `.mcp.json` (MCP configured through IDE settings)
- No `.lsp.json` (LSP is built-in to the IDE)

### .mdc Rule Format

```yaml
---
description: Short description of the rule's purpose
globs: optional/path/pattern/**/*
alwaysApply: false
---

Rule content in markdown...
```

---

## Cross-Platform Compatibility Matrix

| Component | Claude Code `.claude/` | Cursor `.cursor/` | Shared Format? |
|-----------|----------------------|-------------------|----------------|
| **Skills** | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | Yes — Agent Skills standard |
| **Agents** | `agents/*.md` | N/A | No |
| **Commands** | `commands/*.md` | N/A | No |
| **Rules** | CLAUDE.md | `rules/*.mdc` | No |
| **Hooks** | `hooks/hooks.json` | N/A | No |
| **MCP** | `.mcp.json` | IDE settings | No |
| **LSP** | `.lsp.json` | Built-in | No |

---

## Implications for promptkit Builder

### What to copy per platform

**Claude Code builder** copies to `.claude/`:
- `skills/<name>/` → `.claude/skills/<name>/` (preserves structure)
- `agents/*.md` → `.claude/agents/*.md` (flat)
- `commands/*.md` → `.claude/commands/*.md` (flat)
- `hooks/hooks.json` → `.claude/hooks/hooks.json`
- `.mcp.json` → `.claude/.mcp.json`
- `.lsp.json` → `.claude/.lsp.json`
- `scripts/` → not copied (referenced via hooks, must stay in plugin)

**Cursor builder** copies to `.cursor/`:
- `skills/<name>/` → `.cursor/skills/<name>/` (preserves structure)
- Everything else (agents, commands, hooks, MCP, LSP) → skipped (no Cursor equivalent)

### Name collision handling

When multiple plugins provide skills/agents/commands with the same name, the builder should:
- Warn about conflicts
- Last-write-wins or fail — TBD per user preference

### Scripts and `${CLAUDE_PLUGIN_ROOT}`

Plugins reference scripts via `${CLAUDE_PLUGIN_ROOT}` which resolves to the plugin's installed location. When promptkit copies files, hook commands referencing this variable will break because the files are no longer in a plugin cache. This is a known limitation — hooks that depend on `${CLAUDE_PLUGIN_ROOT}` won't work when copied by promptkit.
