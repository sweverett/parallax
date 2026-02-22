"""Parallax CLI — Typer-based command interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from parallax.core.interview import run_interview
from parallax.core.renderer import render_project

app = typer.Typer(
    name="parallax",
    help="Scientific augmentation tool for reproducible, hypothesis-driven science.",
    no_args_is_help=True,
)


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
) -> None:
    """Initialize a new Parallax-managed project via structured interview."""
    target = target_dir or Path.cwd()
    target = target.resolve()

    config = run_interview(yes=yes)

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
    typer.echo(
        "\nNext: start a Claude Code session and ask Claude to read "
        "CLAUDE.md, PARALLAX.md, and CONSTITUTION.md for refinement."
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
