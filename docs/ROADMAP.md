# Parallax Roadmap

Living document tracking decisions, open questions, and future work.

## Current Status

**Layer 1 (Convention System)** — functional. `parallax init` interview + template rendering implemented. `parallax refine` implemented. Hook enforcement scripts implemented. Skills fully specified.

## Known Gaps (Post-Bootstrap Design Work)

### ~~1. PARALLAX.md template content~~ (resolved)
Implemented in template with hypothesis protocol, experiment manifest, handoff format.

### ~~2. Structured interview questions~~ (resolved)
`parallax init` interview implemented: 2-phase (core + detailed), editor-based multi-line input, defaults, validation.

### 3. Template versioning/migration
When Parallax ships new templates, how do existing projects upgrade? Merge? Override? Side-by-side? Need a migration strategy before users depend on generated configs.

### 4. Data management
DVC/git-lfs/provenance unspecified for data-heavy science. Layer 3 mentions it but no concrete design. Critical for any project with non-trivial datasets.

### 5. Dogfooding plan
Test Parallax on a real scientific project ASAP. Identifies gaps theory can't. Candidate: use Parallax to manage its own development (meta-bootstrap).

### 6. Agent failure recovery
Partial state from midway failures. What happens when an agent dies mid-hypothesis? Recovery strategy, state rollback, idempotent operations.

### 7. PARALLAX.md + existing CLAUDE.md interaction
If a user already has CLAUDE.md, how does Parallax-generated content interact? Merge/append/@import/conflict resolution. Must not clobber user's existing rules.

### 8. Exploratory vs hypothesis-driven modes
Current design assumes hypothesis-driven work. Many scientific tasks are exploratory (data exploration, literature review, feasibility studies). Needs a "discovery mode" alongside hypothesis mode.

### 9. Claude Code API stability
Hooks/skills format could change upstream. No compatibility strategy. Should we pin Claude Code versions? Adapter layer? Accept breakage and fix forward?

## Layer 1 Remaining Work

- [x] `parallax init` interview design + implementation
- [x] Template files: PARALLAX.md, CLAUDE.md, CONSTITUTION.md, settings.json, skills
- [x] Claude Code skills: `/hypothesis`, `/handoff`, `/audit`, `/experiment`, `/session-start`
- [x] Hook scripts: test protection, lint check, stop check
- [x] Custom agent definitions: hypothesis-explorer, experiment-runner, literature-reviewer, result-validator
- [x] Token tier system: model selection per agent (pro/5x/20x/api)
- [x] Auto-refinement via Claude CLI (interactive plan-mode session; `-b` for headless background)
- [x] `parallax config set token-tier` for post-init changes
- [x] `memory: project` on hypothesis + experiment skills
- [x] Writing agents: paper-writer (LaTeX), presentation-writer (Beamer)
- [x] Writing skills: `/manuscript-review` (auto-detects paper/Beamer), `/latex-guide` (troubleshooting, auto-invocable)
- [x] `manuscript-reviewer` agent (read-only critique, Bash for compilation checks)
- [x] Layer 2 design doc ([005_layer2_design.md](plans/005_layer2_design.md))
- [x] Doc staleness check (`scripts/check_doc_staleness.py` + CI step)
- [ ] Semantic version validation in CI

## Layer 2 Features (MVP-beta)

- [ ] SQLite schema for hypothesis lifecycle + test results (skill `memory: project` as short-term proxy)
- [ ] Git worktree integration for parallel hypotheses (Claude Code handles plumbing natively; Parallax defines workflows)
- [ ] Agent handoff summary system
- [ ] Semantic versioning automation
- [ ] Conversation/session logging
- [ ] Auto-documentation generation
- [ ] Negative result logging
- [ ] Token usage tracking (basic)

## Layer 3 Features (v1+)

- [ ] Multi-agent orchestration with token budgets
- [ ] TUI/web dashboard
- [ ] Regression metric visualization
- [ ] JupyterLab hub
- [ ] Literature/DOI integration
- [ ] Full provenance chains
- [ ] Data versioning (DVC/git-lfs)
- [ ] Multi-language support
- [ ] Voice interface
- [ ] Fun scientist on startup
- [ ] cmux / terminal multiplexer integration ([plan](plans/002_cmux_integration.md))

## Deferred Decisions

- **License**: All rights reserved for now. Evaluate open-source options when project matures.
- **Team features**: Personal use only for MVP. Multi-user/org support is v2+.
- **Container strategy**: pixi for now. Evaluate Docker/Apptainer for HPC reproducibility in Layer 2/3.
- **Notebook format**: Jupytext (markdown-based, diffable). Evaluate when Layer 2 auto-docs land.
- **Terminal multiplexer docs**: Add tmux/cmux usage tutorial to docs/ when multiplexer integration lands.
- **Vision/roadmap as generated convention**: Parallax-dev uses VISION.md + ROADMAP.md for strategic context in `/session-start`, but these aren't part of the generated template yet. Scope/format TBD after dogfooding.
