<p align="center">
  <img src="parallax_logo.png" alt="Parallax" width="200">
</p>

# Parallax

Scientific augmentation tool encoding best practices for reproducible, hypothesis-driven science into agentic AI workflows.

*True depth requires two lines of sight.*

## Philosophy

Accelerate as fast as is safe, quantifiable, and verifiable — but no faster. Parallax encodes scientific best practices into agentic AI workflows so that speed gains never come at the cost of rigor, reproducibility, or correctness. AI supplements scientific work; it never drives it.

See [CONSTITUTION.md](CONSTITUTION.md) for core values.

## Architecture

3-layer model:

1. **Convention System** (MVP-alpha) — CLI interview (`parallax init`) generates project config (CLAUDE.md, PARALLAX.md, templates). Claude Code skills and hooks enforce scientific best practices. CI as hard enforcement layer.

2. **State + Workflow Engine** (MVP-beta) — SQLite-backed hypothesis lifecycle tracking, git worktree parallel exploration, auto-documentation, regression tracking, agent handoff summaries.

3. **Full Orchestrator** (v1+) — Dashboard, multi-agent coordination, provenance chains, literature integration, JupyterLab hub.

See [VISION.md](docs/VISION.md) for details.

## Repo Structure

```
src/parallax/           # Main package
  cli/                  # Typer CLI (init, refine)
  core/                 # Config, interview, renderer
  db/                   # SQLite models (Layer 2)
  templates/            # string.Template files for init output
tests/                  # pytest (mirrors src structure)
docs/                   # VISION.md, ROADMAP.md, plans/
.claude/                # Skills and hooks for development
```

## Installation

Requires [pixi](https://pixi.sh). Install via:

```bash
# macOS / Linux
curl -fsSL https://pixi.sh/install.sh | bash

# macOS (Homebrew)
brew install pixi

# Windows
powershell -c "irm https://pixi.sh/install.ps1 | iex"
```

Then:

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

## Usage

```bash
# Initialize a new Parallax-managed project
parallax init

# With options
parallax init -t /path/to/project   # target directory
parallax init -y                     # accept defaults, skip optional
parallax init -f                     # overwrite existing files

# Post-init refinement
parallax refine                      # print refinement instructions
parallax refine --done               # strip refinement comment blocks
```

`parallax init` runs a structured interview generating:
- **CLAUDE.md** -- project-specific AI agent guide
- **PARALLAX.md** -- scientific workflow rules
- **CONSTITUTION.md** -- core scientific principles
- **.claude/skills/** -- hypothesis, handoff, audit, experiment skills
- **.claude/hooks/** -- test guard, lint check, stop check enforcement scripts
- **.claude/settings.json** -- hook configuration referencing scripts above

## Current Status

Layer 1 (Convention System) functional. `parallax init`, `parallax refine`, hook enforcement, and skills all implemented.

What exists:
- `parallax init`: structured interview + template rendering
- `parallax refine`: post-init refinement workflow
- Hook enforcement: test guard (blocks test weakening), lint check (ruff feedback), stop check (uncommitted work reminder)
- Full skill definitions: /hypothesis, /handoff, /audit, /experiment
- CI pipeline (ruff, mypy --strict, pytest)
- Integration test suite validating generated output

What's next:
- Layer 2: SQLite hypothesis lifecycle, git worktrees
- Template versioning / migration
- CI enhancements (semantic version validation, doc staleness check)

See [ROADMAP.md](docs/ROADMAP.md) for the full backlog.

## Contributing

This is a personal project in early development. If you're interested, open an issue.

## License

All rights reserved. License to be determined.
