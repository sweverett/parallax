"""Smoke tests for the Parallax CLI."""

from typer.testing import CliRunner

from parallax.cli import app

runner = CliRunner()


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "parallax" in result.output.lower()


def test_init_not_implemented() -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output
