## 1. Extend FileSystem Protocol

- [x] 1.1 Add `read_file(path: Path) -> str` and `list_directory(path: Path) -> list[Path]` to the `FileSystem` protocol in `domain/file_system.py`
- [x] 1.2 Implement `read_file` and `list_directory` in `LocalFileSystem` (`infra/file_system/local.py`)
- [x] 1.3 Write tests for the new `LocalFileSystem` methods in `tests/infra/file_system/test_local.py`

## 2. PromptCache

- [x] 2.1 Write tests for `PromptCache` in `tests/infra/storage/test_prompt_cache.py` — store, retrieve, has, duplicate store
- [x] 2.2 Implement `PromptCache` in `infra/storage/prompt_cache.py` — content-addressable storage using `FileSystem` protocol
- [x] 2.3 Ensure cache filenames use format `sha256-<hex>.md` and methods accept/return `sha256:<hex>` hash strings

## 3. LocalFileFetcher

- [x] 3.1 Write tests for `LocalFileFetcher.fetch()` in `tests/infra/fetchers/test_local_file_fetcher.py` — fetch by spec, subdirectory support, missing file error
- [x] 3.2 Write tests for `LocalFileFetcher.discover()` — flat discovery, subdirectory discovery, empty dir, non-md files ignored
- [x] 3.3 Implement `LocalFileFetcher` in `infra/fetchers/local_file_fetcher.py` — implements `PromptFetcher` protocol plus `discover()` method

## 4. LockPrompts Use Case

- [x] 4.1 Write tests for `LockPrompts` in `tests/app/test_lock.py` — lock remote prompt, lock local prompt, timestamp preservation, stale entry removal, no existing lock file, missing fetcher error
- [x] 4.2 Implement `LockPrompts` use case in `app/lock.py` — orchestrate fetch → cache → lock for remote and local prompts
- [x] 4.3 Verify lock file output matches `LockFile.serialize` format with all entries sorted

## 5. CLI Lock Command

- [x] 5.1 Write tests for `promptkit lock` CLI command in `tests/test_cli.py` — success path, missing config error, fetch error
- [x] 5.2 Implement `lock` command in `cli.py` — wire up `LockPrompts` with real infrastructure
- [x] 5.3 Run full test suite (`uv run pytest -x`) and type checker (`uv run pyright`) to verify no regressions
