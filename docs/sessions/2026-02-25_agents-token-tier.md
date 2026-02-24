# Session: 2026-02-25 -- Custom agents, token tier, auto-refinement

## What Was Done
- Added `TokenTier` type (`pro/5x/20x/api`) and `token_tier` field to `ProjectConfig`
- Added `custom_agent_description` field to `ProjectConfig`
- Added token tier interview question (Phase A, after generate_hooks)
- Added custom agent editor-based question (Phase B, after key_libraries)
- Created 4 agent templates: hypothesis-explorer, experiment-runner, literature-reviewer, result-validator
- Implemented model selection matrix (`_MODEL_MAP`) mapping `(agent, tier) -> model`
- Added agent rendering to `renderer.py` (render_agent, render_custom_agent)
- Created `/session-start` skill template for generated projects
- Added `memory: project` to hypothesis + experiment skill frontmatter
- Created `refiner.py` -- auto-invokes `claude -p` after init for synthesis/refinement
- Added CLI flags: `--token-tier`, `--skip-refine`
- Added `parallax config set token-tier <tier>` command (rewrites agent model lines)
- Added "Plan Completion & Verification" rule to CLAUDE.md (includes plan archival + verification reporting)
- Archived plan to `docs/plans/003_agents_token_tier.md`
- Updated previous session file (2026-02-22) with CI fix and handoff self-review items that were never committed
- Updated README, CLAUDE.md directory structure, ROADMAP
- Updated MEMORY.md with agent/skill patterns
- 134 tests (was 126), all pass

## Key Decisions
- **Agents gated by `generate_skills=True`** -- agents require skills (hypothesis-explorer preloads /hypothesis), so no separate `generate_agents` flag
- **Underscore templates, hyphen output** -- template filenames use underscores (Python import compat via importlib.resources), output filenames use hyphens (Claude Code convention)
- **Custom agent = generic wrapper** -- user description wrapped in minimal frontmatter; refinement pass infers proper name/tools/model
- **`_MODEL_MAP` shared between renderer and CLI** -- `parallax config set token-tier` reuses same mapping to update agent files post-init
- **Auto-refinement gracefully degrades** -- if `claude` CLI not found or fails, warns and leaves refinement blocks intact
- **Plan archival as CLAUDE.md rule** -- implementation sessions copy plan from `.claude/plans/` to `docs/plans/NNN_name.md` as first step; no user action needed since plan path is in system message

## Current State
- What works: all Layer 1 features including agents, token tier, auto-refinement, config command, session-start skill
- What doesn't: auto-refinement untested against live Claude CLI (subprocess mocked in tests). Agent discoverability by Claude Code not manually verified.
- Test status: 134 passed, lint clean, mypy --strict clean, format clean
- Git: committed `04287d6`, pushed to main

## Next Steps
1. Manually verify agent discoverability in Claude Code (open a generated project, confirm agents appear)
2. Test auto-refinement end-to-end with live `claude` CLI
3. Iterate on refinement prompt content -- current prompt is reasonable but will need tuning based on actual output quality
4. Consider: should `parallax init -y` (minimal mode) still generate agents? Currently yes. May want a `--no-agents` flag if users find them noisy.
5. Layer 2 planning: SQLite hypothesis tracking, now that `memory: project` provides a short-term proxy

## Open Questions
- Refinement prompt quality -- needs real-world iteration. Current prompt is domain-aware but untested against actual Claude output.
- Agent discovery verification -- step 5 from the plan ("open Claude Code in generated project dir, confirm agents discoverable") was not performed

## Relevant Files

### New files
- `docs/plans/003_agents_token_tier.md` -- archived plan
- `src/parallax/core/refiner.py` -- Claude CLI auto-refinement
- `src/parallax/templates/agents/__init__.py` -- package init
- `src/parallax/templates/agents/hypothesis_explorer.md` -- explorer agent template
- `src/parallax/templates/agents/experiment_runner.md` -- runner agent template
- `src/parallax/templates/agents/literature_reviewer.md` -- reviewer agent template
- `src/parallax/templates/agents/result_validator.md` -- validator agent template
- `src/parallax/templates/skills/session_start.md` -- session bootstrap skill
- `tests/test_core/test_refiner.py` -- refiner tests
- `tests/test_cli/test_config.py` -- config command tests

### Modified files
- `src/parallax/core/config.py` -- TokenTier, token_tier, custom_agent_description
- `src/parallax/core/interview.py` -- token tier + custom agent questions
- `src/parallax/core/renderer.py` -- agent rendering, model mapping, output paths
- `src/parallax/cli/__init__.py` -- --token-tier, --skip-refine, config set command
- `src/parallax/templates/skills/hypothesis.md` -- memory: project
- `src/parallax/templates/skills/experiment.md` -- memory: project
- `tests/conftest.py` -- new defaults
- `tests/test_core/test_config.py` -- token tier + custom agent tests
- `tests/test_core/test_interview.py` -- updated for new questions
- `tests/test_core/test_renderer.py` -- agent rendering tests
- `tests/test_cli/test_e2e.py` -- full pipeline with agents
- `tests/test_cli/test_init.py` -- updated for new output
- `tests/test_cli/test_main.py` -- config command in help
- `tests/test_integration/test_generated_output.py` -- agent frontmatter validation
- `CLAUDE.md` -- directory structure, plan archival + verification rules
- `docs/sessions/2026-02-22_skill-directory-migration.md` -- appended CI fix + handoff self-review items
- `README.md` -- agents, token tier, prerequisites, config command
- `docs/ROADMAP.md` -- Layer 1 completion items
