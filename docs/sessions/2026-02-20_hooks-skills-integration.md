# Session: 2026-02-20 -- Hook enforcement, skills, integration tests

## What Was Done
- Fixed TC006 lint in `interview.py` (quoted type args in `cast()`)
- Fixed exception context in `renderer.py` (`from exc` instead of `from None`)
- Created hook script templates: `test_guard.py`, `lint_check.py`, `stop_check.py`
- Updated `settings.json.tpl` -- replaced echo stubs with hook script references
- Updated `renderer.py` -- removed `_lint_command()`, added hook loading/writing to `render_project`
- Created parallax's own hooks at `.claude/hooks/` (identical to templates)
- Updated `.claude/settings.json` with real hook references
- Replaced all 4 skill stubs with full content (hypothesis, handoff, audit, experiment)
- Created new `/session-start` skill for session onboarding
- Updated existing tests to assert hook script generation
- Created integration test suite: `test_generated_output.py` (8 tests) + `test_hooks.py` (14 tests)
- Updated ROADMAP.md, README.md, CLAUDE.md

## Key Decisions
- Hook scripts are stdlib-only (sys, json, re, subprocess) -- no external dependencies
- `test_guard.py` is the only blocking hook (exit 1); lint_check and stop_check are informational (exit 0)
- `render_settings_json()` no longer substitutes variables -- template is static JSON
- Hook templates and parallax's own hooks start identical; divergence expected over time
- `/session-start` skill is parallax-dev-only, not a template for generated projects

## Current State
- What works: `parallax init` generates 11 files (3 core docs + settings.json + 3 hooks + 4 skills). All hooks enforce. 93 tests passing. lint/typecheck/test all green.
- What doesn't: nothing broken
- Test status: `pixi run check` fully green (93 tests, 0 lint errors, mypy strict passes)

## Next Steps
1. Layer 2 design: SQLite schema for hypothesis lifecycle
2. Template versioning/migration strategy
3. CI enhancements (semantic version validation, doc staleness check)
4. Dogfood parallax on a real scientific project

## Open Questions
- None from this session

## Relevant Files
- `src/parallax/core/renderer.py` -- hook loading + render_project changes
- `src/parallax/templates/hooks/` -- test_guard.py, lint_check.py, stop_check.py
- `src/parallax/templates/settings.json.tpl` -- now static JSON
- `.claude/hooks/` -- parallax's own enforcement scripts
- `.claude/skills/` -- all 5 skills (4 replaced + session-start new)
- `tests/test_integration/` -- test_generated_output.py, test_hooks.py
- `docs/ROADMAP.md` -- updated status and checklists
