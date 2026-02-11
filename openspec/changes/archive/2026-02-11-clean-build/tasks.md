## 1. Domain & Use Case

- [x] 1.1 Create `CleanArtifacts` use case in `source/promptkit/app/clean.py` with `execute(project_dir, clean_cache)` method
- [x] 1.2 Implement manifest discovery: list `*.txt` files in `.promptkit/managed/` to find platforms
- [x] 1.3 Implement artifact removal: for each manifest, call `cleanup_managed_files()` then delete the manifest file
- [x] 1.4 Implement cache removal: when `clean_cache=True`, remove `.promptkit/cache/` directory tree
- [x] 1.5 Return a result indicating what was cleaned (artifacts removed, cache removed, or nothing to clean)

## 2. CLI Command

- [x] 2.1 Add `clean` command to `source/promptkit/cli.py` following existing command pattern
- [x] 2.2 Add `--cache` flag (default `False`) to the clean command
- [x] 2.3 Wire up `CleanArtifacts` use case with appropriate output messages ("Cleaned build artifacts", "Nothing to clean", "Cleaned build artifacts and cache")
- [x] 2.4 Handle errors with stderr output and exit code 1

## 3. Tests

- [x] 3.1 Test clean removes files listed in manifests and deletes manifest files
- [x] 3.2 Test clean is no-op when no manifests exist
- [x] 3.3 Test clean preserves non-managed files in output directories
- [x] 3.4 Test clean handles already-deleted managed files gracefully
- [x] 3.5 Test clean with `--cache` flag removes `.promptkit/cache/` directory
- [x] 3.6 Test clean without `--cache` flag preserves cache
- [x] 3.7 Test clean with `--cache` flag when cache directory doesn't exist
- [x] 3.8 Test CLI integration: `promptkit clean` succeeds and prints expected message
