# Session: 2026-03-01 -- Merge mode for existing repos

## What Was Done
- Implemented merge mode: `parallax init` into repos with existing `.claude/` config writes `.parallax` suffixed versions instead of failing/overwriting
- Refactored `renderer.py`: extracted `_render_all_content()` (pure), added `MergeResult` dataclass, `_suffix_path()`, `classify_outputs()`, `_write_merge_guide()`
- Added `_MERGE_REFINEMENT_PROMPT` to `refiner.py` with `merge_mode` param on `run_refinement()`
- Repurposed `parallax refine`: now launches interactive session (was: print instructions). Auto-detects `.parallax/merge-guide.md` for merge-aware refinement
- Added `--target-dir` / `-t` to refine command
- Housekeeping: `.gitignore` scratch files, ROADMAP CI checkbox split
- Updated README.md for new refine behavior and merge mode
- Archived plan as `docs/plans/004_merge_mode.md`
- 31 new tests (199 total)

## Key Decisions
- `.parallax` inserted before extension (not appended) -- preserves file type associations, `.parallax.md` not discovered by Claude Code
- Merge mode is auto-detected (no flag needed) -- conflicts + no PARALLAX.md = merge mode
- `_render_all_content()` as pure function separate from I/O -- enables classify_outputs without writing to disk
- Force (`-f`) always overwrites, never enters merge mode -- conceptual boundary: merge is for coexistence, force is for replacement
- Removed `_print_refinement_instructions()` -- vestigial since init runs interactive refinement

## Current State
- What works: fresh init, merge mode init, force overwrite, refine interactive launch, refine merge detection, refine --done, all CLI flags
- What doesn't: merge refinement untested with real Claude (prompt written but no live test); `.parallax/` cleanup after merge is manual
- Test status: 199 passed, ruff clean, mypy strict clean

## Next Steps
1. Field-test merge mode on parallax repo itself (`parallax init --skip-refine -y` from repo root)
2. Test merge refinement with live Claude session
3. Layer 2 planning: SQLite hypothesis lifecycle, git worktrees

## Open Questions
- Should force-reinit clean up leftover `.parallax` files from previous merge?
- Self-init: commit merged result or keep as validation-only?

## Relevant Files
- `src/parallax/core/renderer.py` -- MergeResult, _render_all_content, _suffix_path, classify_outputs, _write_merge_guide, _render_merge
- `src/parallax/core/refiner.py` -- _MERGE_REFINEMENT_PROMPT, merge_mode param
- `src/parallax/cli/__init__.py` -- merge mode detection in _init_impl, _display_result, refine repurposed
- `tests/test_core/test_renderer.py` -- suffix, classify, merge mode tests
- `tests/test_cli/test_init.py` -- merge mode CLI tests
- `tests/test_cli/test_refine.py` -- interactive, target-dir, merge detection tests
- `tests/test_core/test_refiner.py` -- merge prompt selection tests
- `docs/plans/004_merge_mode.md` -- plan archive
