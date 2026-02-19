# Parallax

Scientific augmentation tool encoding best practices for reproducible, hypothesis-driven science into agentic AI workflows.

Two perspectives (human + AI) to get a stronger result.

## Philosophy

Accelerate excellent science — but no faster than that. AI supplements scientific work, never drives it. See [CONSTITUTION.md](CONSTITUTION.md) for core values.

## Architecture

3-layer model:

1. **Convention System** (MVP-alpha) — CLI interview (`parallax init`) generates project config (CLAUDE.md, PARALLAX.md, templates). Claude Code skills and hooks enforce scientific best practices. CI as hard enforcement layer.

2. **State + Workflow Engine** (MVP-beta) — SQLite-backed hypothesis lifecycle tracking, git worktree parallel exploration, auto-documentation, regression tracking, agent handoff summaries.

3. **Full Orchestrator** (v1+) — Dashboard, multi-agent coordination, provenance chains, literature integration, JupyterLab hub.

See [VISION.md](docs/VISION.md) for details.

## Repo Structure

```
src/parallax/           # Main package (cli/, core/, db/)
templates/              # Templates generated for user projects
tests/                  # pytest
docs/                   # VISION.md, ROADMAP.md, plans/
.claude/                # Skills and hooks for development
```

## Installation

Requires [pixi](https://pixi.sh).

```bash
pixi install
```

## Development

```bash
pixi run test        # pytest
pixi run lint        # ruff check
pixi run format      # ruff format
pixi run typecheck   # mypy --strict
pixi run check       # all of the above
```

## Current Status

Project bootstrap complete. Layer 1 (Convention System) in active development.

What exists:
- Project skeleton with CLI entry point
- CI pipeline (ruff, mypy, pytest)
- Foundation docs (VISION, ROADMAP, CONSTITUTION)

What's next:
- `parallax init` structured interview
- Claude Code skills (`/hypothesis`, `/handoff`, `/audit`, `/experiment`)
- Hook scripts for test protection, auto-doc, lint/format
- Template files for user projects

See [ROADMAP.md](docs/ROADMAP.md) for the full backlog.

## Contributing

This is a personal project in early development. If you're interested, open an issue.

## License

All rights reserved. License to be determined.
