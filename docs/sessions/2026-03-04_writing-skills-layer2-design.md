# Session: 2026-03-04 -- Writing Skills + Layer 2 Design

## What Was Done
- Created `/manuscript-review` skill template — auto-detects paper vs Beamer, read-only peer review with severity-tagged issues, `disable-model-invocation: true`
- Created `/latex-guide` skill template — practical LaTeX/BibTeX troubleshooting, auto-invocable (no `disable-model-invocation`)
- Created `manuscript-reviewer` agent — read-only (disallows Edit/Write/NotebookEdit), Bash allowed for compilation checks, skills: [manuscript-review]
- Updated `paper-writer` and `presentation-writer` agents with `skills: [latex-guide]` frontmatter
- Updated `renderer.py`: added to `_SKILL_NAMES`, `_AGENT_NAMES`, `_MODEL_MAP`, `_AGENT_MODEL_VARS`
- Added unit tests (renderer) + integration tests (frontmatter validation) for all new templates
- Wrote Layer 2 design doc to `docs/plans/005_layer2_design.md` — full design, not summary
- Updated ROADMAP.md (checked off writing skills items, added Layer 2 doc reference)
- Updated README.md (new skills/agents in generated output lists)

## Key Decisions
- Single `/manuscript-review` skill (not separate `/paper-review` + `/presentation-review`) — auto-detects via `\begin{frame}`
- `/latex-guide` is auto-invocable (writing agents can trigger it on LaTeX errors) vs `/manuscript-review` is user-invoked only
- `manuscript-reviewer` model map: sonnet (pro), opus (5x/20x/api) — matches result-validator tier pattern
- Layer 2 design is research-only this session — 14 open questions (Q1-Q14) deferred for future iteration

## Current State
- What works: all 207 tests pass, `pixi run check` clean, CLI smoke test generates all 21 files correctly
- What doesn't: nothing known broken. Layer 2 is design-only, no code yet.
- Test status: lint OK, format OK, mypy strict OK, 207 tests passed

## Next Steps
1. Iterate on Layer 2 open questions (Q1-Q14 in `docs/plans/005_layer2_design.md`) — resolve before implementation
2. Semantic version validation in CI (remaining Layer 1 item)
3. Begin Layer 2 implementation once design questions are resolved (SQLite schema, Python API, CLI commands)

## Open Questions
- Layer 2 Q1-Q14 in `docs/plans/005_layer2_design.md` — all deferred, none blocking current work

## Relevant Files
- `src/parallax/templates/skills/manuscript_review.md` — new skill template
- `src/parallax/templates/skills/latex_guide.md` — new skill template
- `src/parallax/templates/agents/manuscript_reviewer.md` — new agent template
- `src/parallax/templates/agents/paper_writer.md` — added `skills: [latex-guide]`
- `src/parallax/templates/agents/presentation_writer.md` — added `skills: [latex-guide]`
- `src/parallax/core/renderer.py` — added to all name/model lists
- `tests/test_core/test_renderer.py` — new skill/agent rendering tests
- `tests/test_integration/test_generated_output.py` — new frontmatter validation tests
- `docs/plans/005_layer2_design.md` — full Layer 2 design (research doc)
- `docs/ROADMAP.md` — updated checkboxes
- `README.md` — updated generated output lists
