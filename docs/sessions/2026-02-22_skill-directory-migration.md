# Session: 2026-02-22 -- Skill directory migration

## What Was Done
- Migrated 5 dev skills from flat `.claude/skills/name.md` to `.claude/skills/name/SKILL.md` with YAML frontmatter
- Added YAML frontmatter (`name`, `description`, `disable-model-invocation`) to all 4 template skills in `src/parallax/templates/skills/`
- Updated `renderer.py`: `_SKILL_NAMES` uses stem names, `_load_skill_template` appends `.md`, output writes to `skill_name/SKILL.md` subdirs
- Updated all tests (test_renderer, test_generated_output, test_e2e, test_init) for new paths
- Updated CLAUDE.md and README.md directory structure descriptions
- Promoted skill format knowledge to MEMORY.md

## Key Decisions
- `disable-model-invocation: true` on session-start, handoff, audit (timing-sensitive / deliberate actions); left default (false) on hypothesis, experiment (core value prop, useful auto-invocation)
- Template files stay flat in `src/parallax/templates/skills/` -- no subdirectory restructuring needed for importlib.resources
- `_SKILL_NAMES` stores stems; `.md` appended only at template load time

## Current State
- What works: all 93 tests pass, lint clean, mypy --strict clean; skills discoverable by Claude Code (hypothesis, experiment confirmed during session)
- What doesn't: not yet verified that `parallax init` output produces discoverable skills in a real Claude Code session. Format is correct per spec but no end-to-end discovery test on generated project.
- Test status: `pixi run check` all green (93 passed, 0.46s)
- `test_skill_files_have_structure` glob changed from `*.md` to `*/SKILL.md` -- test intent shifted from "any .md in skills dir" to "SKILL.md inside subdirs"

## Next Steps
1. Commit this work (all changes uncommitted on main)
2. Manual verification: run `parallax init -t /tmp/test-proj`, open Claude Code in that dir, confirm `/hypothesis` etc. appear
3. Layer 2 planning: SQLite hypothesis lifecycle, git worktrees

## Open Questions
- No handoff was written for the previous planning session (plan created in separate conversation). The plan rationale (why flat files don't work, two valid discovery paths, Claude Code issue #9817) exists only in the plan file, not in session history.
- MEMORY.md now references `description` single-line gotcha (#9817) -- transcribed from plan but not independently verified. May be outdated.

## Relevant Files
- `.claude/skills/*/SKILL.md` -- 5 new dev skill files (replaced flat .md files)
- `src/parallax/templates/skills/*.md` -- 4 templates with added frontmatter
- `src/parallax/core/renderer.py` -- dir-based skill output paths
- `tests/test_cli/test_e2e.py` -- updated skill path assertions
- `tests/test_cli/test_init.py` -- updated skill path assertion
- `tests/test_core/test_renderer.py` -- updated skill names and paths
- `tests/test_integration/test_generated_output.py` -- updated expected paths and glob
- `CLAUDE.md`, `README.md` -- directory structure description updates
