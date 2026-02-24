"""Parallax CLI — Typer-based command interface."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer

from parallax.core.config import VALID_TOKEN_TIERS
from parallax.core.interview import run_interview
from parallax.core.refiner import run_refinement
from parallax.core.renderer import _MODEL_MAP, model_for_agent, render_project

app = typer.Typer(
    name="parallax",
    help="Scientific augmentation tool for reproducible, hypothesis-driven science.",
    no_args_is_help=True,
)

config_app = typer.Typer(
    name="config",
    help="Post-init configuration changes.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@app.command()
def init(
    target_dir: Annotated[
        Path | None,
        typer.Option("--target-dir", "-t", help="Output directory."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing files."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Accept defaults, skip optional."),
    ] = False,
    token_tier: Annotated[
        str | None,
        typer.Option("--token-tier", help="Token usage tier (pro/5x/20x/api)."),
    ] = None,
    skip_refine: Annotated[
        bool,
        typer.Option("--skip-refine", help="Skip auto-refinement via Claude CLI."),
    ] = False,
) -> None:
    """Initialize a new Parallax-managed project via structured interview."""
    # Validate --token-tier if provided
    if token_tier is not None and token_tier not in VALID_TOKEN_TIERS:
        typer.echo(
            f"Error: invalid token tier {token_tier!r}. "
            f"Must be one of: {sorted(VALID_TOKEN_TIERS)}",
            err=True,
        )
        raise typer.Exit(code=1)

    target = target_dir or Path.cwd()
    target = target.resolve()

    config = run_interview(yes=yes, token_tier_override=token_tier)

    try:
        written = render_project(config, target, force=force)
    except FileExistsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"\nParallax initialized. {len(written)} files written:")
    for path in written:
        try:
            rel = path.relative_to(target)
        except ValueError:
            rel = path
        typer.echo(f"  {rel}")

    if not skip_refine:
        typer.echo("")
        run_refinement(target)
    else:
        typer.echo(
            "\nRefinement skipped. Run a Claude Code session and ask Claude to "
            "read CLAUDE.md, PARALLAX.md, and CONSTITUTION.md for refinement."
        )


@app.command()
def refine(
    done: Annotated[
        bool,
        typer.Option("--done", "-d", help="Strip refinement comment blocks."),
    ] = False,
) -> None:
    """Manage the post-init refinement process."""
    if done:
        try:
            _strip_refinement_blocks(Path.cwd())
        except ValueError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        _print_refinement_instructions()


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key to set.")],
    value: Annotated[str, typer.Argument(help="New value.")],
    target_dir: Annotated[
        Path | None,
        typer.Option("--target-dir", "-t", help="Project directory."),
    ] = None,
) -> None:
    """Update a Parallax config value in generated files."""
    target = target_dir or Path.cwd()
    target = target.resolve()

    if key == "token-tier":
        _set_token_tier(target, value)
    else:
        typer.echo(
            f"Error: unknown config key {key!r}. Valid keys: token-tier",
            err=True,
        )
        raise typer.Exit(code=1)


def _set_token_tier(target: Path, tier: str) -> None:
    """Update model fields in agent files for new token tier."""
    if tier not in VALID_TOKEN_TIERS:
        typer.echo(
            f"Error: invalid token tier {tier!r}. "
            f"Must be one of: {sorted(VALID_TOKEN_TIERS)}",
            err=True,
        )
        raise typer.Exit(code=1)

    agents_dir = target / ".claude" / "agents"
    if not agents_dir.exists():
        typer.echo(
            "Error: no .claude/agents/ directory found. Run `parallax init` first.",
            err=True,
        )
        raise typer.Exit(code=1)

    model_re = re.compile(r"^(model:\s*)\S+", re.MULTILINE)
    updated = 0
    for agent_file in sorted(agents_dir.glob("*.md")):
        # Map output filename back to template name
        stem = agent_file.stem.replace("-", "_")
        if stem not in _MODEL_MAP:
            continue
        new_model = model_for_agent(stem, tier)  # type: ignore[arg-type]
        text = agent_file.read_text(encoding="utf-8")
        new_text = model_re.sub(rf"\g<1>{new_model}", text, count=1)
        if new_text != text:
            agent_file.write_text(new_text, encoding="utf-8")
            updated += 1
            typer.echo(f"  {agent_file.name}: model -> {new_model}")

    if updated == 0:
        typer.echo("No agent files needed updating.")
    else:
        typer.echo(f"Updated {updated} agent file(s) to tier '{tier}'.")


_REFINEMENT_START = "<!-- PARALLAX REFINEMENT:"
_REFINEMENT_END = "-->"


def _strip_refinement_blocks(target: Path) -> None:
    """Remove refinement comment blocks from CLAUDE.md and PARALLAX.md."""
    count = 0
    for name in ("CLAUDE.md", "PARALLAX.md"):
        fpath = target / name
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")
        if _REFINEMENT_START not in text:
            continue
        lines = text.splitlines(keepends=True)
        filtered: list[str] = []
        inside_block = False
        for line in lines:
            if _REFINEMENT_START in line:
                inside_block = True
                continue
            if inside_block and _REFINEMENT_END in line:
                inside_block = False
                continue
            if not inside_block:
                filtered.append(line)
        if inside_block:
            msg = f"Unpaired refinement start marker in {name} (no closing -->)"
            raise ValueError(msg)
        # Strip leading blank lines after block removal
        result = "".join(filtered).lstrip("\n")
        fpath.write_text(result, encoding="utf-8")
        count += 1
        typer.echo(f"  Stripped refinement block from {name}")

    if count == 0:
        typer.echo("No refinement blocks found.")
    else:
        typer.echo(f"Done. Removed refinement blocks from {count} file(s).")


def _print_refinement_instructions() -> None:
    typer.echo(
        "Parallax refinement process:\n"
        "\n"
        "1. Start a Claude Code session in this project directory.\n"
        "2. Ask Claude to read CLAUDE.md, PARALLAX.md, and CONSTITUTION.md.\n"
        "3. Ask Claude to propose edits for project cohesion (plan mode).\n"
        "4. Iterate until satisfied.\n"
        "5. Run `parallax refine --done` to remove refinement comment blocks.\n"
    )
