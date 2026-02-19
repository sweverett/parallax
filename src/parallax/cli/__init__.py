"""Parallax CLI — Typer-based command interface."""

import typer

app = typer.Typer(
    name="parallax",
    help="Scientific augmentation tool for reproducible, hypothesis-driven science.",
    no_args_is_help=True,
)


@app.command()
def init() -> None:
    """Initialize a new Parallax-managed project via structured interview."""
    typer.echo("parallax init: not yet implemented")
    raise typer.Exit(code=1)
