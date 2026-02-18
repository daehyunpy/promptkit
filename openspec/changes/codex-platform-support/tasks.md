## 1. Domain Layer

- [ ] 1.1 Add `CODEX = "codex"` member to `PlatformTarget` enum in `source/promptkit/domain/platform_target.py`
- [ ] 1.2 Update `tests/domain/test_platform_target.py` — add tests for `CODEX` value, `from_string("codex")`, and updated member count

## 2. CodexBuilder Implementation

- [ ] 2.1 Create `source/promptkit/infra/builders/codex_builder.py` with `CodexBuilder` class implementing `ArtifactBuilder` protocol — `PLATFORM_NAME = "codex"`, `ALLOWED_CATEGORIES = {"skills"}`, `platform` returns `PlatformTarget.CODEX`
- [ ] 2.2 Create `tests/infra/builders/test_codex_builder.py` — test skills-only filtering, skip non-skills categories, skip flat files, content preservation, manifest cleanup, platform property, returned paths, FileSystem dependency

## 3. Config & Wiring

- [ ] 3.1 Add `PlatformTarget.CODEX: ".codex"` to `DEFAULT_OUTPUT_DIRS` in `source/promptkit/infra/config/yaml_loader.py`
- [ ] 3.2 Update YAML loader tests — verify `codex` is accepted as a platform key, defaults to `.codex` output dir, is NOT included in default platform configs
- [ ] 3.3 Register `PlatformTarget.CODEX: CodexBuilder(fs)` in `_make_build_use_case()` in `source/promptkit/cli.py`

## 4. Clean Use Case

- [ ] 4.1 Add `"codex": ".codex"` to `PLATFORM_OUTPUT_DIRS` in `source/promptkit/app/clean.py`
- [ ] 4.2 Update clean tests to verify Codex manifest (`codex.txt`) is discovered and `.codex/` files are cleaned

## 5. Verification

- [ ] 5.1 Run full test suite (`pytest -x`) and confirm all tests pass
- [ ] 5.2 Run type checker (`pyright`) and confirm no errors
- [ ] 5.3 Run linter (`ruff check .`) and confirm no issues
