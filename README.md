# promptkit

A package manager for AI prompts. Sync high-quality prompts from sources like the Claude plugin marketplace, store them in version control, and generate platform-specific artifacts for tools like Cursor and Claude Code.

## Why promptkit?

- **Portable** — Same prompts work across multiple AI coding tools
- **Version-controlled** — Track changes and maintain reproducibility with lock files
- **No manual maintenance** — Eliminates copy/paste, format conversions, and cross-project drift
- **No tool lock-in** — Switch between AI coding tools without losing your prompt library

## Install

### Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/)

### Install

```bash
uv tool install git+https://github.com/anthropics/promptkit.git
```

This installs the `promptkit` CLI globally via uv.

## Quick Start

```bash
# 1. Initialize a new project
promptkit init

# 2. Edit promptkit.yaml to declare your prompts and platforms
#    Example config is generated with commented-out examples

# 3. Sync: fetch prompts, lock versions, build artifacts
promptkit sync

# 4. Done — check .cursor/ and .claude/ for generated artifacts
```

## Commands

| Command              | What it does                                      | Needs network |
|----------------------|---------------------------------------------------|---------------|
| `promptkit init`     | Scaffold new project with config and directories  | No            |
| `promptkit sync`     | Fetch + lock + build (the one-stop command)       | Yes           |
| `promptkit lock`     | Fetch + update lock file only                     | Yes           |
| `promptkit build`    | Generate artifacts from cached prompts            | No            |
| `promptkit validate` | Verify config is well-formed and prompts exist    | No            |

## How It Works

1. **Init** — `promptkit init` scaffolds your project with a `promptkit.yaml` config
2. **Configure** — Declare which prompts you want and which platforms to target
3. **Sync** — `promptkit sync` fetches prompts, locks versions, and builds platform artifacts
4. **Rebuild** — `promptkit build` regenerates artifacts without re-fetching (useful after config changes)

## Project Structure

After running `promptkit init`:

```
promptkit.yaml          # Declarative config — what prompts, which platforms
promptkit.lock          # Lock file — exact versions for reproducibility
.promptkit/cache/       # Cached upstream prompts (gitignored)
prompts/                # Your local/custom prompts (committed)
.cursor/                # Generated Cursor artifacts
.claude/                # Generated Claude Code artifacts
```

## Configuration

`promptkit.yaml` declares your prompts and target platforms:

```yaml
version: 1
registries:
  anthropic-agent-skills: https://github.com/anthropics/skills
  claude-plugins-official: https://github.com/anthropics/claude-plugins-official
prompts:
  - claude-plugins-official/code-review
  - anthropic-agent-skills/feature-dev
platforms:
  cursor:
    output_dir: .cursor
  claude-code:
    output_dir: .claude
```

## Documentation

- [Product Requirements](docs/product_requirements.md) — What and why
- [Agent Instructions](AGENTS.md) — For AI agents working on this codebase

## License

[MIT](LICENSE)
