# Session: 2026-03-04 -- Early conflict detection, interview cache, refiner fix

## What Was Done
- Moved already-initialized check (PARALLAX.md exists) to BEFORE interview -- users see error immediately, not after 10 min of Q&A
- Added `ProjectConfig.to_json(path)` / `ProjectConfig.from_json(path)` for interview cache serialization
- Interview cache flow: save to `<target>/.parallax/cache.json` after interview, prompt "Resume from previous interview?" on re-run, auto-delete after ALL steps succeed
- Added `--keep-cache` / `-k` flag: suppresses auto-delete entirely (permanent storage)
- Fixed refiner `--cwd` error: Claude CLI has no `--cwd` flag; replaced with `subprocess.run(..., cwd=target)` kwarg
- Cache deletion moved to after refinement completes (not after render) -- failed refinement preserves cache for retry
- Added README `-k` flag documentation

## Key Decisions
- Cache persists until entire init flow succeeds (including refinement). `-k` = never delete. Without `-k` = delete only on full success. Discovered during field-test: refinement failed post-render, cache would have been lost without `-k`.
- Early conflict check is defense-in-depth alongside renderer's existing FileExistsError -- CLI gives clear message, renderer is fallback.
- `_maybe_resume_cache()` extracted as standalone function -- keeps init() readable.

## Current State
- What works: early conflict detection, cache save/load/resume/delete, `--keep-cache`, refiner subprocess with `cwd=`, merge mode, interactive refinement, all CLI flags
- What doesn't: merge refinement untested with live Claude (prompt written but no live test)
- Test status: 162+ passed (exact count varies with later sessions), ruff clean, mypy strict clean
- Uncommitted: README.md `-k` flag addition

## Next Steps
1. Commit README `-k` flag addition
2. Field-test full flow with cache: init, fail refinement, resume from cache
3. Layer 2: SQLite hypothesis lifecycle (design doc at `docs/plans/005_layer2_design.md`)

## Open Questions
- None

## Relevant Files
- `src/parallax/core/config.py` -- `to_json()`, `from_json()` methods on ProjectConfig
- `src/parallax/cli/__init__.py` -- early conflict check, `_maybe_resume_cache()`, cache save/delete, `--keep-cache` flag, `_CACHE_REL`
- `src/parallax/core/refiner.py` -- `cwd=target` fix (was `--cwd` arg)
- `tests/test_core/test_config.py` -- JSON round-trip tests (4 new)
- `tests/test_cli/test_init.py` -- early detection test, cache flow tests (4 new)
- `tests/test_cli/test_e2e.py` -- early conflict e2e, cache resume e2e (2 new)
- `tests/test_core/test_refiner.py` -- updated: asserts `cwd=` kwarg, no `--cwd` in args
