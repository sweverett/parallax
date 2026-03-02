# Plan: Cleanup + Merge Mode for Existing Repos

## Context

Layer 1 is complete. Before starting Layer 2, three items needed resolution:
1. Housekeeping: untracked scratch files, stale ROADMAP checkbox
2. Existing-repo init: `parallax init` fails (or clobbers with `-f`) on existing config. Need merge strategy.
3. Self-init viability: whether parallax should init itself (depends on #2)

## Implementation Summary

### Part 1: Housekeeping
- Added scratch files to `.gitignore`
- Split ROADMAP CI checkbox (doc staleness = done, semantic version = pending)

### Part 2: `parallax refine` repurposed
- `parallax refine` (no flags) now launches interactive refinement session
- Auto-detects `.parallax/merge-guide.md` for merge-mode refinement
- Added `--target-dir` / `-t` option
- Removed vestigial `_print_refinement_instructions()`
- `--done` unchanged

### Part 3: Merge mode
When `parallax init` targets a repo with existing files but no PARALLAX.md:
- Files that don't exist: written normally
- Files that exist and differ: written with `.parallax` suffix (e.g. `CLAUDE.parallax.md`)
- Files that exist and are identical: skipped
- `.parallax/merge-guide.md` written with context + instructions
- User offered optional Claude session for merge assistance

Key implementation:
- `MergeResult` dataclass: `written`, `suffixed`, `skipped` lists
- `_render_all_content()`: pure function extracting content generation
- `_suffix_path()`: inserts `.parallax` before extension
- `classify_outputs()`: renders + classifies against existing files
- `_write_merge_guide()`: generates merge instructions
- `_MERGE_REFINEMENT_PROMPT`: merge-specific Claude prompt
- `run_refinement(merge_mode=True)` selects appropriate prompt

### Part 4: Self-init
Deferred. Merge mode implemented; self-init viable but should be field-tested first.

## Verification
All automated checks pass:
- `pixi run check` (lint + typecheck + 198 tests)
- `pixi run test -k "suffix_path or classify_outputs or merge"` (24 targeted tests)
