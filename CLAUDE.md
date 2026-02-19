# Parallax — Developer Guide

Instructions for AI agents and humans building Parallax itself.

## Project Overview

Parallax is a scientific augmentation tool encoding best practices for reproducible, hypothesis-driven science into agentic AI workflows. CLI-first (Typer), Python-only for MVP.

**3-layer architecture:**
1. **Convention System** (current) — CLAUDE.md, skills, hooks, templates, `parallax init`
2. **State + Workflow Engine** — SQLite lifecycle tracking, git worktrees, auto-docs
3. **Full Orchestrator** — dashboard, multi-agent coordination, provenance chains

See [VISION.md](docs/VISION.md) for full architecture. See [ROADMAP.md](docs/ROADMAP.md) for open questions.

**Current design context:** [docs/plans/001_project_bootstrap.md](docs/plans/001_project_bootstrap.md) — remove this reference once codebase is more settled.

## Tech Stack

- Python 3.12+
- Typer (CLI)
- SQLite (structured state, Layer 2)
- pixi (package/environment management)
- pytest, mypy (strict), ruff (lint + format)

## Directory Structure

```
src/parallax/           # Main package
  cli/                  # Typer CLI commands
  core/                 # Hypothesis, state, templates, workflow logic
  db/                   # SQLite models + queries
templates/              # Templates Parallax generates for user projects
tests/                  # pytest
docs/                   # VISION.md, ROADMAP.md, plans/
.claude/skills/         # Claude Code skills for Parallax development
.claude/settings.json   # Claude Code hooks
```

## Writing Style

All docs, markdown, READMEs, commit messages, and code comments:
- Concise, scientific tone
- No LLM-speak ("I'd be happy to...", "Great question!", "Certainly!")
- No emojis
- Sacrifice grammar for concision except when clarifying code design or accuracy

## Code Conventions

- **Loud errors.** Surface problems immediately. Never swallow, hide, or downplay errors. Prefer exceptions over silent defaults.
- **Type hints everywhere.** All function signatures fully typed. `mypy --strict` must pass.
- **Ruff** for formatting and linting. No exceptions.
- **Docstrings on public API only.** Internal functions: type hints are the docs. Don't add docstrings to private helpers unless the logic is genuinely non-obvious.
- **No over-engineering.** Minimum complexity for current requirements. No premature abstractions, feature flags, or backward-compat shims.
- **Sanity checks on physical quantities.** Any code involving units must include dimensional analysis verification before finalizing.

## Scientific Rigor (Practiced While Building)

We build Parallax *using* the principles it encodes:
- Hypotheses before implementation — know what you expect before writing code
- Test every feature; never weaken tests to pass
- Document negative results (things we tried that didn't work)
- Reproducible environments (pixi lockfiles)

See [CONSTITUTION.md](CONSTITUTION.md) for the full set of scientific values.

## Git Workflow

- Branch prefix: `se/` (e.g., `se/add-hypothesis-cli`)
- Concise commit messages; sacrifice grammar for brevity
- Semantic versioning (once releases begin)
- Never force-push to main

## Testing

- pytest for all tests
- All features need tests — no exceptions
- Test files mirror source structure: `tests/test_cli/`, `tests/test_core/`, etc.
- Regression tests are first-class citizens

## Development Commands

```bash
pixi run test        # pytest
pixi run lint        # ruff check
pixi run format      # ruff format
pixi run typecheck   # mypy --strict
pixi run check       # all of the above
```

## Never Do

- Never reduce test tolerances/scope to make tests pass without explicit human approval
- Never swallow exceptions or hide error details
- Never commit `.env`, credentials, or secrets
- Never add emojis to code, docs, or commits
- Never use notebook-first workflows (library code > notebooks)
- Never skip type hints on function signatures
- Never add backward-compat shims — just change the code
- Never create docs/READMEs unless explicitly requested

## References

- @CONSTITUTION.md — core scientific values (import into agent context)
- [VISION.md](docs/VISION.md) — architecture, design decisions, feature roadmap
- [ROADMAP.md](docs/ROADMAP.md) — open questions, future work, known gaps
