# Product Requirements: promptkit

## Overview

**promptkit** is a package manager for AI prompts. It syncs high-quality prompts from sources like the Claude plugin marketplace, stores them in a declarative, version-controlled format (`promptkit.yaml` + lock file), and generates platform-specific artifacts for tools like Cursor and Claude Code.

This brings package management principles to prompt engineering: declare your prompt dependencies, lock versions for reproducibility, and build outputs for multiple platforms automatically.

**Key benefits:**
- **Portable** - prompts work consistently across tools and projects
- **Version-controlled** - track changes and maintain reproducibility with lock files
- **No manual maintenance** - eliminates copy/paste, format conversions, and cross-project drift
- **No tool lock-in** - switch between AI coding tools without losing your prompt library

## Problem

High-quality prompts exist in the Claude plugin marketplace and official documentation, but using them in practice is painful:

1. **Manual copy/paste workflow** - Using official prompts requires copying from web sources and manually pasting into tool configs. No programmatic way to import and maintain them.

2. **No standard for prompt management** - Each AI coding tool (Cursor, Claude Code, etc.) has its own approach. There's no unified system for managing prompts across tools.

3. **Format conversion is tedious** - Different tools use different formats (`.cursor/rules` vs `.claude/skills`). Converting prompts between formats means manually asking agents to adapt them, which is error-prone.

4. **Cross-project drift** - Sharing prompts between projects requires copy/paste. Fix a bug or improve a prompt in one project, and you have to remember to update all others manually.

5. **Maintaining multiple formats doubles the work** - If you use both Cursor and Claude Code, you maintain two separate copies of the same prompt logic. Changes must be replicated manually.

6. **Tool lock-in** - Investing time in tool-specific prompts makes switching tools painful. Your prompt library is tied to a specific platform's format.

7. **Stale prompts** - Manual sync means you miss upstream improvements and bug fixes. No way to know when official prompts have been updated or improved by the community.

## Target User

**promptkit** is designed for:

- **Solo developers** using AI coding tools daily (Cursor, Claude Code, etc.) who are frustrated with manual prompt copy/paste and want a better workflow

- **AI tool power users** who customize prompts heavily and need proper version control, reproducibility, and the ability to track changes over time

- **Development teams** that want to standardize prompts across team members and projects, ensuring everyone uses the same high-quality prompt configurations

- **Prompt engineers** who create and maintain prompt libraries, whether for personal use, team distribution, or sharing with the broader community

## Core Features

### Must Have (MVP)

1. **Sync (Primary Command)**
   - `promptkit sync` is the one-stop command: fetches prompts, updates lock file, and generates artifacts
   - Equivalent to `uv sync` — takes you from config to working state in one step
   - Stores prompts in `.promptkit/cache/` directory
   - Re-syncing updates existing prompts

2. **Declarative Configuration**
   - `promptkit.yaml` specifies which prompts to use and for which platforms
   - Includes source, prompt name, and target platforms (Cursor, Claude Code)
   - Human-readable and version-controllable

3. **Lock File for Reproducibility**
   - `promptkit lock` fetches prompts and records exact hashes in `promptkit.lock`
   - Ensures consistent builds across machines and over time
   - Useful for CI validation, code review, and offline builds
   - Equivalent to `uv lock` — resolves without generating artifacts

4. **Multi-Platform Build**
   - `promptkit build` generates platform-specific artifacts from cached prompts (no network needed)
   - **Cursor**: Generates `.cursor/` artifacts (agents, skills-cursor, rules, commands)
   - **Claude Code**: Generates `.claude/` artifacts (skills, rules, subagents, commands)
   - Deterministic builds — same input always produces identical output (no AI transformation)
   - Useful after `lock`, after reverting a lockfile via git, or for rebuilding after config changes

5. **Multi-Prompt Support**
   - Single project can use multiple prompts (e.g., code reviewer + test writer + documentation generator)
   - Each prompt can target different platforms
   - Prompts are composed independently in the build output

6. **Validation**
   - `promptkit validate` checks that `promptkit.yaml` is well-formed
   - Verifies all referenced prompts exist in `.promptkit/cache/` or `.agents/`
   - Catches configuration errors before build

7. **Project Scaffolding**
   - `promptkit init` creates new project with standard structure:
     ```
     promptkit.yaml          # declarative config
     promptkit.lock          # lock file
     .promptkit/cache/       # cached upstream prompts
     .agents/                # canonical/custom prompts
     .cursor/                # generated Cursor artifacts
     .claude/                # generated Claude Code artifacts
     ```

### Nice to Have (Post-MVP)

8. **Version Pinning**
   - Pin prompts to specific versions instead of always using latest
   - Support syntax like `promptkit sync anthropic/code-reviewer@v1.2.0`
   - Allow different versions of same prompt for different contexts

9. **Composition Layers**
   - Wrap imported prompts with custom rules or policies
   - Example: Add project-specific coding standards on top of official prompts
   - Layer system allows non-destructive customization

10. **Additional Platform Support**
    - Extend beyond Cursor and Claude Code
    - Support for: Codex, OpenCode, Antigravity, Aider, Continue, etc.
    - Plugin system for adding new platform targets

## Use Cases

### 1. Import Official Claude Prompt

A developer discovers a high-quality prompt in the Claude plugin marketplace. They add it to `promptkit.yaml`, run `promptkit sync`, and the prompt is fetched, locked, and built into both Cursor and Claude Code artifacts automatically.

### 2. Share Prompts Across Personal Projects

A developer has 5 projects that all need the same code review prompt. Using promptkit, they maintain one source of truth. When they improve the prompt, a rebuild propagates changes to all projects instantly.

### 3. Team Standardization

A team lead adds `promptkit.yaml` to the company repository specifying approved prompts. All developers run `promptkit sync`, and everyone gets an identical prompt setup. No more "it works on my machine" due to different prompt configurations.

### 4. Update Upstream Prompts

An official prompt receives a bug fix or improvement. The developer runs `promptkit sync`, sees a git diff showing exactly what changed, reviews the update, and commits it. All projects using that prompt can now be rebuilt with the fix.

### 5. Switch from Cursor to Claude Code

A developer moves from Cursor to Claude Code. They update the target platforms in `promptkit.yaml`, run `promptkit build` (no re-fetch needed), and their entire prompt library now works in the new tool—no manual migration needed.

### 6. Start New Project with Best Practices

A developer starts a new project and runs `promptkit init` to scaffold the structure. They copy proven prompts from previous projects into `promptkit.yaml`, run `promptkit sync`, and immediately have a professional prompt setup.

### 7. Multi-Prompt Composition

A developer wants to use multiple prompts together: code-reviewer, test-writer, and docs-generator. They declare all three in `promptkit.yaml`, and promptkit builds them into the appropriate platform-specific locations, handling the composition automatically.

### 8. Rollback Problematic Update

A new prompt version introduces unexpected behavior. The developer uses git to revert `promptkit.lock` to the previous working state, runs `promptkit build`, and is back to the stable version—no manual hunting for old prompt files.

## Architecture Overview

promptkit is a Python-based CLI tool with a three-layer architecture (config, source, output). It follows Domain-Driven Design principles with clear separation between domain logic, application use cases, and infrastructure adapters.

For detailed architecture, directory layout, DDD layers, schemas, and build process, see [`technical_design.md`](technical_design.md).

## Non-Goals (v1)

### Permanently Out of Scope

These features will not be added in any version:

- **Web UI or GUI** - promptkit is a CLI tool only
- **Prompt analytics or usage tracking** - no telemetry or usage metrics
- **A/B testing framework** - no built-in testing or comparison features
- **Real-time runtime prompt injection** - prompts are built at development time, not runtime
- **SaaS hosting or cloud service** - fully local tool, no hosted version
- **Automatic prompt optimization** - no AI-powered prompt improvement suggestions

### Out of Scope for v1

These features may be considered for future versions but are not included in the initial release:

- **Version pinning** - v1 always syncs latest; pinning specific versions is post-MVP
- **Composition layers** - wrapping prompts with custom rules/policies is post-MVP
- **Additional platforms** - v1 supports Cursor and Claude Code only; other tools (Codex, OpenCode, Antigravity, etc.) may be added later
- **Prompt marketplace or distribution system** - no public registry or sharing platform
- **Prompt testing framework** - beyond basic config validation, no automated prompt testing
- **Prompt regression detection** - no system to detect when prompts produce different outputs
- **Prompt linting** - no quality scoring or style checking for prompts
- **Multi-user collaboration features** - no conflict resolution, permissions, or team workflows beyond standard git
- **Custom template system** - v1 uses built-in platform mappings only; extensible templates may be added later

## Success Criteria

promptkit is successful when:

1. **No tool lock-in** - Same prompt works in both Cursor and Claude Code without manual duplication. Can switch platforms by changing config and rebuilding.

2. **Single source of truth** - Canonical prompts live in `.agents/`, clearly separated from generated artifacts (`.cursor/`, `.claude/`).

3. **Deterministic and reproducible** - Same `promptkit.yaml` + `promptkit.lock` produces identical outputs across machines and over time.

4. **Prompt updates tracked via git** - Can see exactly what changed when syncing upstream prompts through git diff.

5. **Fast upstream sync** - Import prompts from Claude plugin marketplace and use them in both tools in under 5 minutes.

6. **Reusable prompt library** - Can use multiple prompts together in a single project, and share configurations across projects with consistent results.

7. **Version control friendly** - All meaningful changes are trackable in git (yaml, lock, .agents). No binary files or opaque artifacts in version control.
