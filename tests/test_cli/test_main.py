"""Smoke tests for the Parallax CLI."""

from typer.testing import CliRunner

from parallax.cli import app

runner = CliRunner()


def test_no_args_shows_usage() -> None:
    result = runner.invoke(app, [])
    # Typer multi-command app returns 2 with usage info
    assert result.exit_code == 2
    assert "Usage" in result.output


def test_init_shows_in_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert "init" in result.output


def test_refine_shows_in_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert "refine" in result.output


def test_config_shows_in_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert "config" in result.output
