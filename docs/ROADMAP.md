# Parallax Roadmap

Living document tracking decisions, open questions, and future work.

## Current Status

**Layer 1 (Convention System)** — in progress. Project skeleton, docs, CI bootstrapped.

## Known Gaps (Post-Bootstrap Design Work)

### 1. PARALLAX.md template content
Skeleton workflow steps, handoff format, experiment manifest structure need design. What fields are required vs optional? How prescriptive vs flexible?

### 2. Structured interview questions
`parallax init` is the centerpiece of Layer 1 but the question set is undefined. Needs its own design session: question ordering, defaults, validation, what gets generated from answers.

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

- [ ] `parallax init` interview design + implementation
- [ ] Claude Code skills: `/hypothesis`, `/handoff`, `/audit`, `/experiment`
- [ ] Hook scripts: test protection, auto-doc check, lint/format, context reinforcement
- [ ] Template files: PARALLAX.md, experiment manifest, hypothesis doc, agent summary
- [ ] CI enhancements: semantic version validation, doc staleness check

## Layer 2 Features (MVP-beta)

- [ ] SQLite schema for hypothesis lifecycle + test results
- [ ] Git worktree integration for parallel hypotheses
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

## Deferred Decisions

- **License**: All rights reserved for now. Evaluate open-source options when project matures.
- **Team features**: Personal use only for MVP. Multi-user/org support is v2+.
- **Container strategy**: pixi for now. Evaluate Docker/Apptainer for HPC reproducibility in Layer 2/3.
- **Notebook format**: Jupytext (markdown-based, diffable). Evaluate when Layer 2 auto-docs land.
