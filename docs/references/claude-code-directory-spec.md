# Claude Code Directory Structure Reference

> **Reference snapshot** — upstream `.claude/` directory spec for promptkit builder design.
> This is NOT a promptkit doc. It tracks upstream platform constraints.

| Field | Value |
|-------|-------|
| Source | https://code.claude.com/docs/en/plugins-reference, https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/sub-agents |
| Captured | 2026-02-10 |
| anthropics/claude-code commit | `19bb071fe024` (2026-02-10) |

---

## Directory Structure

```
.claude/
├── settings.json              # Project settings + enabled plugins
├── settings.local.json        # Local settings (gitignored)
├── CLAUDE.md                  # Project memory / context
├── agents/                    # Subagent markdown files (FLAT)
│   └── *.md
├── skills/                    # Skills (ONE LEVEL nesting only)
│   └── <name>/
│       ├── SKILL.md           # Required entrypoint
│       ├── scripts/           # Optional support files
│       ├── reference.md       # Optional reference docs
│       └── examples/          # Optional examples
├── commands/                  # Slash commands / legacy skills (FLAT)
│   └── *.md                   # Merged into skills system; still works
├── hooks/                     # Hook configurations
│   └── hooks.json
├── .mcp.json                  # MCP server definitions
├── .lsp.json                  # LSP server configurations
├── agent-memory/              # Persistent subagent memory (project scope)
│   └── <agent-name>/
│       └── MEMORY.md
└── agent-memory-local/        # Persistent subagent memory (gitignored)
    └── <agent-name>/
        └── MEMORY.md
```

Personal (user-level) equivalents live at `~/.claude/` with the same structure.

---

## Nesting Constraints

| Component | Structure | Max Depth | Notes |
|-----------|-----------|-----------|-------|
| **Skills** | `skills/<name>/SKILL.md` | 1 level | Subdirs inside skill dir OK (scripts/, references, examples/) |
| **Agents** | `agents/*.md` | Flat | No subdirectories |
| **Commands** | `commands/*.md` | Flat | Legacy; use skills for new work |
| **Hooks** | `hooks/hooks.json` | Single file | Additional hook files can be referenced from plugin.json |
| **MCP** | `.mcp.json` | Single file | At project or plugin root |
| **LSP** | `.lsp.json` | Single file | At project or plugin root |

[Issue #16438](https://github.com/anthropics/claude-code/issues/16438): Feature request for nested skill directories (`skills/<category>/<name>/SKILL.md`) — **not yet supported** as of 2026-02-10.

---

## SKILL.md Format

```yaml
---
name: skill-name                    # kebab-case, max 64 chars (optional, defaults to dir name)
description: What this skill does   # recommended — Claude uses for auto-invocation
disable-model-invocation: true      # optional — prevent Claude auto-loading (default: false)
user-invocable: false               # optional — hide from / menu (default: true)
allowed-tools: Read, Grep, Glob     # optional — tool restrictions when skill is active
model: sonnet                       # optional — model override (sonnet/opus/haiku)
context: fork                       # optional — run in isolated subagent
agent: Explore                      # optional — subagent type when context: fork
argument-hint: "[issue-number]"     # optional — hint shown during autocomplete
hooks:                              # optional — lifecycle hooks scoped to this skill
  PostToolUse: [...]
---

Skill instructions in markdown...

Supports $ARGUMENTS, $ARGUMENTS[N], $N for argument substitution.
Supports !`command` for dynamic context injection (shell preprocessing).
```

### Supporting files

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files:

```
my-skill/
├── SKILL.md           # Main instructions (required)
├── reference.md       # Detailed API docs (loaded when needed)
├── examples.md        # Usage examples (loaded when needed)
└── scripts/
    └── helper.py      # Utility script (executed, not loaded)
```

Reference supporting files from `SKILL.md` so Claude knows when to load them.

---

## Agent .md Format

```yaml
---
name: agent-name                    # required, kebab-case
description: When to use this agent # required
tools: Read, Grep, Glob, Bash      # optional — inherits all if omitted
disallowedTools: Write, Edit        # optional — denylist
model: sonnet                       # optional — sonnet/opus/haiku/inherit (default: inherit)
permissionMode: default             # optional — default/acceptEdits/dontAsk/delegate/bypassPermissions/plan
maxTurns: 10                        # optional — max agentic turns
skills:                             # optional — skills preloaded into context
  - skill-name
mcpServers:                         # optional — MCP servers available to this agent
  - server-name
hooks:                              # optional — lifecycle hooks
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
memory: user                        # optional — persistent memory scope (user/project/local)
---

System prompt in markdown...
```

Built-in agents: `Explore` (read-only, haiku), `Plan` (read-only, inherits), `general-purpose` (all tools, inherits), `Bash` (terminal).

---

## Hook Events

| Event | Matcher Input | When |
|-------|--------------|------|
| `PreToolUse` | Tool name | Before tool call (can block with exit 2) |
| `PostToolUse` | Tool name | After successful tool call |
| `PostToolUseFailure` | Tool name | After failed tool call |
| `PermissionRequest` | — | When permission dialog shown |
| `UserPromptSubmit` | — | When user submits prompt |
| `Notification` | — | When notification sent |
| `Stop` | — | When Claude attempts to stop |
| `SubagentStart` | Agent type | When subagent starts |
| `SubagentStop` | Agent type | When subagent completes |
| `SessionStart` | — | At session start |
| `SessionEnd` | — | At session end |
| `TeammateIdle` | — | When team teammate goes idle |
| `TaskCompleted` | — | When task marked complete |
| `PreCompact` | — | Before conversation compaction |

Hook types: `command` (shell), `prompt` (LLM eval), `agent` (agentic verifier).

---

## Plugin Directory Structure (for reference)

When a plugin is installed, Claude Code copies its directory to cache. The canonical structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Manifest (optional — name is only required field)
├── agents/*.md               # Subagents
├── commands/*.md              # Commands
├── skills/<name>/SKILL.md    # Skills
├── hooks/hooks.json          # Hook configs
├── .mcp.json                 # MCP servers
├── .lsp.json                 # LSP servers
├── scripts/                  # Hook/utility scripts
└── README.md
```

Components MUST be at plugin root, NOT inside `.claude-plugin/`.
Custom paths in `plugin.json` supplement defaults — they don't replace them.
`${CLAUDE_PLUGIN_ROOT}` resolves to plugin's installed location.

---

## promptkit Builder Implications

**Claude Code builder** copies to `.claude/`:
- `skills/<name>/` → `.claude/skills/<name>/` (preserves structure)
- `agents/*.md` → `.claude/agents/*.md` (flat)
- `commands/*.md` → `.claude/commands/*.md` (flat)
- `hooks/hooks.json` → `.claude/hooks/hooks.json`
- `.mcp.json` → `.claude/.mcp.json`
- `.lsp.json` → `.claude/.lsp.json`

**Known limitation**: `${CLAUDE_PLUGIN_ROOT}` in hook commands will not resolve correctly when files are copied outside the plugin cache.
