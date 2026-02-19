# Parallax Vision

> Two perspectives (human + AI) to get a stronger result.

## Mission

Parallax is a scientific augmentation tool that encodes best practices for reproducible, hypothesis-driven science into agentic AI workflows. It accelerates excellent science — but no faster than that.

Personal science use case. Not enterprise/team tooling (yet).

## Core Principles

- AI supplements scientific work, never drives it
- Robust science over fast science
- Reproducibility is non-negotiable
- Loud errors over silent failures
- Negative results are scientifically valuable

See [CONSTITUTION.md](/CONSTITUTION.md) for the full set of values.

## Architecture: 3-Layer Model

### Layer 1: Convention System (MVP-alpha)

Maps to Claude Code native primitives (CLAUDE.md, skills, hooks, templates). The `parallax init` command runs a structured interview to generate project-specific config.

**Components:**
- `parallax init` — CLI interview generating CLAUDE.md, PARALLAX.md, experiment templates
- Claude Code skills — `/hypothesis`, `/handoff`, `/audit`, `/experiment`
- Claude Code hooks — test protection, auto-doc, lint/format, context reinforcement
- Template files — CLAUDE.md, PARALLAX.md, CONSTITUTION.md, experiment/hypothesis manifests
- CI/CD — ruff, mypy, pytest, semantic version validation, doc staleness checks

**Hard-coded baseline rules** (user interview can override):
- Concise interactions; loud errors; unit sanity checks on physical quantities
- Plans end with unresolved questions list
- Agentic workflow recommendation: Research (Opus) -> Plan (Opus, fresh context) -> Implement (Opus/Sonnet, fresh context) with structured handoffs between phases

### Layer 2: State + Workflow Engine (MVP-beta)

Adds persistent state, lifecycle tracking, and automation.

- Hypothesis lifecycle (proposed -> active -> tested -> concluded) in SQLite
- Parallel hypothesis exploration via git worktrees
- Agent handoff summaries with context rot mitigation
- Test result history + regression tracking
- Semantic versioning automation
- Environment reproducibility (pixi/conda-lock)
- Conversation/session logging with daily summaries
- Auto-documentation system (API docs, quickstart, README)
- Failure/negative result logging
- Basic token usage tracking, manual-trigger audits

### Layer 3: Full Orchestrator + Dashboard (v1+)

- Multi-agent coordination with token budget management
- Automated scheduled audits
- TUI/web dashboard
- Visual regression metric time series
- JupyterLab hub integration
- Literature/DOI integration
- Full provenance chains (result -> code -> data -> environment -> hypothesis)
- Data versioning (DVC/git-lfs)
- Multi-language support (Fortran, R, Julia, C++)
- Voice interface

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Interface | CLI-first (Typer) | Scriptable, testable, GUI/TUI later |
| Language | Python-only (MVP) | Scientific ecosystem, rapid iteration |
| State storage | Markdown/YAML + SQLite | Human-readable + structured queries |
| Package manager | pixi | conda+PyPI, lockfiles, scientific-aligned |
| Python version | 3.12+ | EOL Oct 2028, modern features |
| License | None yet | All rights reserved, decide later |

## JAX / Differentiable Code (Optional)

Configurable via `parallax init`:
- Prefer JAX-compatible ops; warn on non-differentiable ops
- Explicit flags when Rust/C extensions break differentiable chains
- Escalation hierarchy: JAX -> NumPy+Numba -> Rust/C (escalate only when needed, always ask)

## Auto-Documentation

**Layer 1:** Hooks warn (don't block) when docs may be stale relative to code changes.
**Layer 2:** Auto-generate API docs, keep quickstart/README in sync, clearly mark auto-generated sections.

## References

- [CONSTITUTION.md](/CONSTITUTION.md) — core values
- [ROADMAP.md](/docs/ROADMAP.md) — open questions, future features
- [Original idea](/docs/original_idea_v0.md) — unmodified vision document
