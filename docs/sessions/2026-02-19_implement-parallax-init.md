# Session: 2026-02-19 — Implement `parallax init`

## What was done

- Implemented full `parallax init` structured interview + template renderer (Layer 1 centerpiece)
- Implemented `parallax refine` command (prints instructions / strips refinement blocks)
- Created `ProjectConfig` frozen dataclass (16 fields, Phase A + Phase B)
- Built interview module: 11 core questions, Phase B editor-based detail gate, `--yes` mode
- Built renderer: per-file renderers, conditional sections, atomic writes via tempdir, conflict detection
- Created 8 template files in `src/parallax/templates/` (CLAUDE.md, PARALLAX.md, CONSTITUTION.md, settings.json, 4 skills)
- Wrote 52 tests (unit, integration, E2E) — all passing
- Fixed pixi.toml deprecation: `[project]` -> `[workspace]`
- Updated CLAUDE.md directory structure and README.md current status + usage section
- Removed repo-root `templates/` (moved inside package)

## Key decisions

- Templates inside package (`src/parallax/templates/`) using `importlib.resources` — not repo-root
- `string.Template` (stdlib) for rendering — no Jinja2 dependency
- Atomic file writes via `tempfile.TemporaryDirectory()` — no half-initialized projects
- Already-initialized detection via PARALLAX.md existence — distinct error from generic file conflicts
- Generated files include refinement comment block — Claude proposes cohesion edits on first read
- `--yes` skips defaulted Qs + Phase B, still prompts required fields (summary, domain)
- Editor fallback: if editor launch fails, graceful single-line prompt fallback

## Current state

What works:
- `parallax init` full pipeline (interview -> config -> render -> write)
- `parallax init -t PATH -f -y` all flags functional
- `parallax refine` prints instructions
- `parallax refine --done` strips refinement blocks from CLAUDE.md + PARALLAX.md
- `pixi run check` fully green (lint, mypy --strict, 52 tests)

What doesn't / incomplete:
- Hook scripts in generated `settings.json` are structure-only (echo reminders, not real enforcement)
- No merge/append for existing CLAUDE.md (deferred per ROADMAP #7)
- No `--config file.yaml` non-interactive mode
- Skills are prescriptive templates but not wired as executable Claude Code skills
- `parallax init` not manually tested end-to-end in a real project yet (only CliRunner tests)

## Next steps

1. Manual test: run `parallax init` in a temp dir, review generated files for quality
2. Hook script implementations (real enforcement, not echo reminders)
3. Wire skills as actual Claude Code invocable skills (requires `.claude/settings.json` command integration)
4. Consider `parallax init --config` for non-interactive/CI use
5. Layer 2 planning: SQLite schema for hypothesis lifecycle, git worktree integration
6. Template versioning / migration strategy (ROADMAP #3)

## Relevant files

- `src/parallax/cli/__init__.py` — CLI commands (init, refine)
- `src/parallax/core/config.py` — ProjectConfig dataclass
- `src/parallax/core/interview.py` — structured interview
- `src/parallax/core/renderer.py` — template rendering + atomic writes
- `src/parallax/templates/` — all .tpl and skill templates
- `tests/test_cli/test_e2e.py` — primary confidence test
- `docs/plans/001_project_bootstrap.md` — original bootstrap plan (archived)
