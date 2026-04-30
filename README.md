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
  cli/                  # Typer CLI (init, refine, config)
  core/                 # Config, interview, renderer, refiner
  db/                   # SQLite models (Layer 2)
  templates/            # string.Template files for init output
    agents/             # Agent definition templates
    skills/             # Skill templates
    hooks/              # Hook script templates
tests/                  # pytest (mirrors src structure)
docs/                   # VISION.md, ROADMAP.md, plans/
.claude/                # Skills (skill-name/SKILL.md) and hooks for development
```

## Prerequisites

- [pixi](https://pixi.sh) -- package/environment management
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) -- required for auto-refinement during `parallax init`

## Installation

Install pixi:

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
parallax init --token-tier 5x        # set model tier for agents
parallax init --skip-refine          # skip auto-refinement
parallax init -b                     # run refinement in background (headless)
parallax init -k                     # keep interview cache after init

# Post-init refinement
parallax refine                      # launch interactive refinement session
parallax refine -t /path/to/project  # target directory
parallax refine --done               # strip refinement comment blocks

# Post-init config changes
parallax config set token-tier 5x    # update agent model selection

# Sync template updates into an existing project
parallax sync                        # pull latest CONSTITUTION/skills/agents/hooks
parallax sync -t /path/to/project    # target directory
parallax sync --dry-run              # show what would change without writing
```

`parallax sync` updates Parallax-managed template files (CONSTITUTION.md, all skills, agents, hooks, settings.json) without touching your CLAUDE.md or PARALLAX.md. User-modified files are written with a `.parallax` suffix; run `parallax refine` afterward to merge.

For projects initialized before the `.parallax/config.json` snapshot existed, `parallax sync` auto-derives the snapshot from rendered files (project_name from PARALLAX.md heading, domain from PARALLAX.md, token_tier reverse-derived from agent model fields, skills/hooks from directory presence). The derived values are printed and persisted; review `.parallax/config.json` and edit if anything is wrong.

`parallax init` runs a structured interview generating:
- **CLAUDE.md** -- project-specific AI agent guide
- **PARALLAX.md** -- scientific workflow rules
- **CONSTITUTION.md** -- core scientific principles
- **.claude/skills/** -- hypothesis, handoff, audit, experiment, session-start, manuscript-review, latex-guide, doc-sync, diagnose, zoom-out, improve-architecture, ubiquitous-language skills
- **.claude/agents/** -- hypothesis-explorer, experiment-runner, literature-reviewer, result-validator, paper-writer, presentation-writer, manuscript-reviewer agents
- **.claude/hooks/** -- test guard, lint check, stop check enforcement scripts
- **.claude/settings.json** -- hook configuration referencing scripts above

See [docs/toolkit.md](docs/toolkit.md) for descriptions of each skill, agent, and hook.

Token tiers control agent model selection:
- **pro** (default) -- conservative: haiku exploration, sonnet validation
- **5x** -- balanced: opus exploration, sonnet runner
- **20x** -- generous: opus for most tasks
- **api** -- unconstrained: opus everywhere

## Current Status

Layer 1 (Convention System) functional. `parallax init`, `parallax refine`, hook enforcement, and skills all implemented.

What exists:
- `parallax init`: structured interview + template rendering + auto-refinement
- Merge mode: `parallax init` into repos with existing `.claude/` files -- suffixes conflicts, never overwrites, writes merge guide
- `parallax refine`: interactive refinement session (auto-detects merge guide for merge assistance)
- `parallax refine --done`: strip refinement comment blocks
- `parallax config`: post-init configuration changes (token tier)
- `parallax sync`: pull latest CONSTITUTION/skills/agents/hooks into an existing project; suffix user-edited files for merge via `parallax refine`
- Hook enforcement: test guard (blocks test weakening), lint check (ruff feedback), stop check (uncommitted work reminder)
- Full skill definitions: /hypothesis, /handoff, /audit, /experiment, /session-start, /manuscript-review, /latex-guide, /doc-sync, /diagnose, /zoom-out, /improve-architecture, /ubiquitous-language
- Agent definitions: hypothesis-explorer, experiment-runner, literature-reviewer, result-validator, paper-writer, presentation-writer, manuscript-reviewer
- Token tier system: model selection per agent based on usage tier (pro/5x/20x/api)
- CI pipeline (ruff, mypy --strict, pytest)
- Integration test suite validating generated output

What's next:
- Layer 2: SQLite hypothesis lifecycle, git worktrees
- Template versioning / migration (basic flow shipped via `parallax sync`)
- Semantic version validation in CI

See [ROADMAP.md](docs/ROADMAP.md) for the full backlog.

## Contributing

This is a personal project in early development. If you're interested, open an issue.

## License

All rights reserved. License to be determined.
