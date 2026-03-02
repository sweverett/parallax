# Session: 2026-03-01 -- Field-test fixes

## What Was Done
- Fixed `--cwd` error in refiner subprocess (claude CLI doesn't support `--cwd`; use `subprocess.run(cwd=target)`)
- Moved cache deletion to after ALL init steps complete (was after render, before refinement)
- Gated cache deletion on refinement success (`refine_ok`) -- failed refinement preserves cache for retry
- Replaced headless `claude -p` refinement with interactive Claude session as default
- Added `--refine-background` / `-b` flag for headless mode (300s timeout, was 120s)
- Interactive refinement opens in plan mode (`--permission-mode plan`)
- Fixed Ctrl+C not killing process during interview (`signal.SIG_DFL` in `init()`)
- Extracted `init()` body into `_init_impl()` for signal handler setup
- Added `_has_custom_agent()` gate in renderer -- skips `custom.md` when description is only `#`-comment boilerplate
- Field-tested `parallax init -f -t ~/repos/prism` -- refinement completed interactively, jax-auditor agent created from custom placeholder
- Updated README (new `-b` flag), ROADMAP (refinement mode), MEMORY.md

## Key Decisions
- Interactive refinement is default because headless was fragile (timeouts, no user visibility)
- `signal.SIG_DFL` over Python-level `KeyboardInterrupt` handling -- readline/Click swallow SIGINT, OS-level handler is only reliable fix
- Custom agent gate checks for non-`#`-comment content rather than stripping `#` lines from parser (avoids breaking markdown headings in other Phase B fields)

## Current State
- What works: full init flow with interactive refinement, cache resume, Ctrl+C exit, custom agent filtering
- What doesn't: nothing known broken
- Test status: 167 tests passing, lint clean, mypy --strict clean

## Next Steps
1. Commit this session's changes
2. Layer 2: SQLite hypothesis lifecycle, git worktrees
3. Continue prism development using the scaffolded config

## Open Questions
- Should `parallax refine` (standalone command) also launch interactive Claude session instead of just printing instructions?

## Relevant Files
- `src/parallax/core/refiner.py` -- interactive/background split, plan mode, 300s timeout
- `src/parallax/cli/__init__.py` -- `_init_impl` extraction, SIG_DFL, `--refine-background`, `refine_ok` gate
- `src/parallax/core/renderer.py` -- `_has_custom_agent()` gate
- `tests/test_core/test_refiner.py` -- 8 tests (interactive + background modes)
- `tests/test_cli/test_init.py` -- cache-preserved-on-refinement-failure test
- `README.md` -- `-b` flag documented
- `docs/ROADMAP.md` -- refinement mode updated
