"""E2E test: full parallax init pipeline with dummy answers."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from parallax.cli import _CACHE_REL, app
from parallax.core.config import ProjectConfig

runner = CliRunner()


def _full_config() -> ProjectConfig:
    return ProjectConfig(
        project_name="astro-pipeline",
        summary="Galaxy redshift measurement pipeline",
        domain="astrophysics",
        languages="Python",
        package_manager="pixi",
        test_framework="pytest",
        uses_units=True,
        uses_jax=True,
        branch_prefix="se/",
        generate_skills=True,
        generate_hooks=True,
        token_tier="pro",
        editor="vim",
        science_requirements="Measure photometric redshifts for LSST galaxies",
        preferred_patterns="Functional style, immutable data, explicit errors",
        outlawed_patterns="No global mutable state, no bare except",
        key_libraries="astropy: units and coordinates\njax: autodiff",
        custom_agent_description="",
    )


class TestE2E:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Full init with all options enabled, verify all output."""
        cfg = _full_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])

        assert result.exit_code == 0, result.output
        assert "Parallax initialized" in result.output

        # --- All files exist ---
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "PARALLAX.md").exists()
        assert (tmp_path / "CONSTITUTION.md").exists()
        assert (tmp_path / ".claude" / "settings.json").exists()
        for skill in [
            "hypothesis",
            "handoff",
            "audit",
            "experiment",
            "session-start",
        ]:
            assert (tmp_path / ".claude" / "skills" / skill / "SKILL.md").exists()
        # Agent files
        for agent in [
            "hypothesis-explorer",
            "experiment-runner",
            "literature-reviewer",
            "result-validator",
            "paper-writer",
            "presentation-writer",
        ]:
            assert (tmp_path / ".claude" / "agents" / f"{agent}.md").exists()

        # --- CLAUDE.md content ---
        claude = (tmp_path / "CLAUDE.md").read_text()
        assert "astro-pipeline" in claude
        assert "Galaxy redshift measurement pipeline" in claude
        assert "astrophysics" in claude
        assert "Python" in claude
        assert "pixi" in claude
        assert "pytest" in claude
        # Conditional sections
        assert "Dimensional analysis is mandatory" in claude
        assert "Git Workflow" in claude
        assert "se/" in claude
        assert "Science Requirements" in claude
        assert "photometric redshifts" in claude
        assert "Preferred Patterns" in claude
        assert "Functional style" in claude
        assert "Outlawed Patterns" in claude
        assert "No global mutable state" in claude
        assert "Key Libraries" in claude
        assert "astropy" in claude
        # Refinement block
        assert "PARALLAX REFINEMENT" in claude
        # No unsubstituted vars
        assert "${" not in claude

        # --- PARALLAX.md content ---
        parallax = (tmp_path / "PARALLAX.md").read_text()
        assert "astro-pipeline" in parallax
        assert "Hypothesis Protocol" in parallax
        assert "JAX" in parallax
        assert "Pure functions" in parallax
        assert "PARALLAX REFINEMENT" in parallax
        assert "${" not in parallax

        # --- CONSTITUTION.md content ---
        constitution = (tmp_path / "CONSTITUTION.md").read_text()
        assert "astro-pipeline" in constitution
        assert "Robust science" in constitution
        assert "${" not in constitution

        # --- Hook scripts exist ---
        for hook in ["test_guard.py", "lint_check.py", "stop_check.py"]:
            assert (tmp_path / ".claude" / "hooks" / hook).exists()

        # --- settings.json content ---
        settings = (tmp_path / ".claude" / "settings.json").read_text()
        assert "test_guard.py" in settings
        assert "lint_check.py" in settings
        assert "stop_check.py" in settings
        assert "${" not in settings

        # --- Skills content ---
        for skill in [
            "hypothesis",
            "handoff",
            "audit",
            "experiment",
            "session-start",
        ]:
            text = (tmp_path / ".claude" / "skills" / skill / "SKILL.md").read_text()
            assert "astro-pipeline" in text
            assert "${" not in text

        # --- Agent content ---
        explorer = (
            tmp_path / ".claude" / "agents" / "hypothesis-explorer.md"
        ).read_text()
        assert "model: haiku" in explorer
        assert "hypothesis-explorer" in explorer
        assert "${" not in explorer

    def test_minimal_pipeline(self, tmp_path: Path) -> None:
        """Minimal config: no units, no jax, no skills, no hooks."""
        cfg = ProjectConfig(
            project_name="minimal",
            summary="Minimal test",
            domain="testing",
            languages="Python",
            package_manager="pip",
            test_framework="pytest",
            uses_units=False,
            uses_jax=False,
            branch_prefix="",
            generate_skills=False,
            generate_hooks=False,
            token_tier="pro",
            editor="",
            science_requirements="",
            preferred_patterns="",
            outlawed_patterns="",
            key_libraries="",
            custom_agent_description="",
        )
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])

        assert result.exit_code == 0
        # Only 3 core files
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "PARALLAX.md").exists()
        assert (tmp_path / "CONSTITUTION.md").exists()
        assert not (tmp_path / ".claude").exists()

        claude = (tmp_path / "CLAUDE.md").read_text()
        assert "minimal" in claude
        # Conditional sections absent
        assert "Dimensional analysis" not in claude
        assert "JAX" not in claude
        assert "Git Workflow" not in claude
        assert "Science Requirements" not in claude

    def test_refine_done_after_init(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Init then refine --done: blocks are stripped, content preserved."""
        cfg = _full_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["refine", "--done"])
        assert result.exit_code == 0

        claude = (tmp_path / "CLAUDE.md").read_text()
        assert "PARALLAX REFINEMENT" not in claude
        assert "astro-pipeline" in claude

        parallax = (tmp_path / "PARALLAX.md").read_text()
        assert "PARALLAX REFINEMENT" not in parallax
        assert "Hypothesis Protocol" in parallax

    def test_token_tier_flag(self, tmp_path: Path) -> None:
        """--token-tier flag overrides default."""
        cfg = _full_config()
        with patch("parallax.cli.run_interview", return_value=cfg) as mock:
            runner.invoke(
                app,
                [
                    "init",
                    "-t",
                    str(tmp_path),
                    "--token-tier",
                    "5x",
                    "--skip-refine",
                ],
            )
            mock.assert_called_once_with(
                yes=False, token_tier_override="5x", target=tmp_path.resolve()
            )

    def test_invalid_token_tier_flag(self) -> None:
        result = runner.invoke(app, ["init", "--token-tier", "free", "--skip-refine"])
        assert result.exit_code == 1
        assert "invalid token tier" in result.output.lower()

    def test_early_conflict_skips_interview(self, tmp_path: Path) -> None:
        """Already-initialized dir fails before interview runs."""
        (tmp_path / "PARALLAX.md").write_text("existing")
        with patch("parallax.cli.run_interview") as mock:
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 1
        assert "already Parallax-managed" in result.output
        mock.assert_not_called()

    def test_cache_resume_e2e(self, tmp_path: Path) -> None:
        """Cache from first run resumes on second run, full output verified."""
        cfg = _full_config()
        cache = tmp_path / _CACHE_REL
        cfg.to_json(cache)
        with (
            patch("parallax.cli.run_interview") as mock,
            patch("parallax.cli.typer.confirm", return_value=True),
        ):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 0
        mock.assert_not_called()
        assert (tmp_path / "CLAUDE.md").exists()
        assert "astro-pipeline" in (tmp_path / "CLAUDE.md").read_text()
        # Cache auto-deleted
        assert not cache.exists()

    def test_custom_agent_pipeline(self, tmp_path: Path) -> None:
        """Config with custom agent generates custom.md."""
        cfg = ProjectConfig(
            project_name="custom-proj",
            summary="Custom agent test",
            domain="testing",
            languages="Python",
            package_manager="pixi",
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
            custom_agent_description="validates ETL pipeline outputs",
        )
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])

        assert result.exit_code == 0
        custom = (tmp_path / ".claude" / "agents" / "custom.md").read_text()
        assert "validates ETL pipeline outputs" in custom
