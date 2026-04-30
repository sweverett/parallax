"""Tests for parallax config command."""

from pathlib import Path

from typer.testing import CliRunner

from parallax.cli import _CONFIG_REL, app
from parallax.core.config import ProjectConfig
from parallax.core.renderer import render_project

runner = CliRunner()


def _make_project(tmp_path: Path) -> None:
    cfg = ProjectConfig(
        project_name="test-proj",
        summary="A test",
        domain="testing",
        languages="Python",
        package_manager="conda",
        test_framework="pytest",
        uses_units=False,
        uses_jax=False,
        branch_prefix="",
        generate_skills=True,
        generate_hooks=False,
        token_tier="pro",
        editor="",
        science_requirements="",
        preferred_patterns="",
        outlawed_patterns="",
        key_libraries="",
        custom_agent_description="",
    )
    render_project(cfg, tmp_path)


class TestConfigSetTokenTier:
    def test_updates_agent_models(self, tmp_path: Path, monkeypatch: object) -> None:
        _make_project(tmp_path)
        # Verify initial pro tier
        explorer = (
            tmp_path / ".claude" / "agents" / "hypothesis-explorer.md"
        ).read_text()
        assert "model: haiku" in explorer

        result = runner.invoke(
            app, ["config", "set", "token-tier", "api", "-t", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Updated" in result.output

        # Verify updated to opus
        explorer = (
            tmp_path / ".claude" / "agents" / "hypothesis-explorer.md"
        ).read_text()
        assert "model: opus" in explorer

    def test_invalid_tier_errors(self, tmp_path: Path) -> None:
        _make_project(tmp_path)
        result = runner.invoke(
            app,
            ["config", "set", "token-tier", "free", "-t", str(tmp_path)],
        )
        assert result.exit_code == 1
        assert "invalid token tier" in result.output.lower()

    def test_missing_agents_dir_errors(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["config", "set", "token-tier", "5x", "-t", str(tmp_path)],
        )
        assert result.exit_code == 1
        assert "no .claude/agents/" in result.output.lower()

    def test_unknown_key_errors(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["config", "set", "foo", "bar", "-t", str(tmp_path)],
        )
        assert result.exit_code == 1
        assert "unknown config key" in result.output.lower()

    def test_updates_config_snapshot(self, tmp_path: Path) -> None:
        """When .parallax/config.json exists, token-tier change is mirrored."""
        _make_project(tmp_path)
        cfg = ProjectConfig(
            project_name="test-proj",
            summary="A test",
            domain="testing",
            languages="Python",
            package_manager="conda",
            test_framework="pytest",
            uses_units=False,
            uses_jax=False,
            branch_prefix="",
            generate_skills=True,
            generate_hooks=False,
            token_tier="pro",
            editor="",
            science_requirements="",
            preferred_patterns="",
            outlawed_patterns="",
            key_libraries="",
            custom_agent_description="",
        )
        config_path = tmp_path / _CONFIG_REL
        cfg.to_json(config_path)

        result = runner.invoke(
            app, ["config", "set", "token-tier", "20x", "-t", str(tmp_path)]
        )
        assert result.exit_code == 0
        loaded = ProjectConfig.from_json(config_path)
        assert loaded.token_tier == "20x"

    def test_no_snapshot_prints_notice(self, tmp_path: Path) -> None:
        """Legacy projects (no config.json) get a warning, not a failure."""
        _make_project(tmp_path)
        # Note: _make_project does NOT create config.json
        result = runner.invoke(
            app, ["config", "set", "token-tier", "5x", "-t", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "config.json" in result.output
        assert "parallax init -f" in result.output
