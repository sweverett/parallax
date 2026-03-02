"""Integration tests for parallax init command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from parallax.cli import _CACHE_REL, app
from parallax.core.config import ProjectConfig

runner = CliRunner()


def _dummy_config(**overrides: object) -> ProjectConfig:
    defaults: dict[str, object] = {
        "project_name": "test-project",
        "summary": "A test project",
        "domain": "astrophysics",
        "languages": "Python",
        "package_manager": "pixi",
        "test_framework": "pytest",
        "uses_units": False,
        "uses_jax": False,
        "branch_prefix": "",
        "generate_skills": True,
        "generate_hooks": True,
        "token_tier": "pro",
        "editor": "",
        "science_requirements": "",
        "preferred_patterns": "",
        "outlawed_patterns": "",
        "key_libraries": "",
        "custom_agent_description": "",
    }
    defaults.update(overrides)
    return ProjectConfig(**defaults)  # type: ignore[arg-type]


class TestInitCommand:
    def test_init_creates_files(self, tmp_path: Path) -> None:
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "PARALLAX.md").exists()
        assert (tmp_path / "CONSTITUTION.md").exists()
        assert (tmp_path / ".claude" / "settings.json").exists()
        assert (tmp_path / ".claude" / "skills" / "hypothesis" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "hooks" / "test_guard.py").exists()
        assert (tmp_path / ".claude" / "hooks" / "lint_check.py").exists()
        assert (tmp_path / ".claude" / "hooks" / "stop_check.py").exists()
        # Agent files
        assert (tmp_path / ".claude" / "agents" / "hypothesis-explorer.md").exists()
        assert (tmp_path / ".claude" / "agents" / "experiment-runner.md").exists()

    def test_init_summary_output(self, tmp_path: Path) -> None:
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert "Parallax initialized" in result.output
        assert "CLAUDE.md" in result.output

    def test_init_conflict_early_detection(self, tmp_path: Path) -> None:
        """Conflict detected BEFORE interview runs."""
        (tmp_path / "PARALLAX.md").write_text("existing")
        with patch("parallax.cli.run_interview") as mock_interview:
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 1
        assert "already Parallax-managed" in result.output
        mock_interview.assert_not_called()

    def test_init_force_overwrites(self, tmp_path: Path) -> None:
        (tmp_path / "PARALLAX.md").write_text("old")
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "-f", "--skip-refine"]
            )
        assert result.exit_code == 0
        assert "test-project" in (tmp_path / "PARALLAX.md").read_text()

    def test_init_no_skills(self, tmp_path: Path) -> None:
        cfg = _dummy_config(generate_skills=False)
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 0
        assert not (tmp_path / ".claude" / "skills").exists()
        assert not (tmp_path / ".claude" / "agents").exists()

    def test_init_no_hooks(self, tmp_path: Path) -> None:
        cfg = _dummy_config(generate_hooks=False)
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 0
        assert not (tmp_path / ".claude" / "settings.json").exists()
        assert not (tmp_path / ".claude" / "hooks").exists()


class TestCacheFlow:
    def test_cache_created_and_deleted(self, tmp_path: Path) -> None:
        """Cache saved after interview, deleted after all steps succeed."""
        cfg = _dummy_config()
        cache = tmp_path / _CACHE_REL
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 0
        assert not cache.exists()

    def test_cache_preserved_on_refinement_failure(self, tmp_path: Path) -> None:
        """Cache kept when refinement fails so user can retry."""
        cfg = _dummy_config()
        cache = tmp_path / _CACHE_REL
        with (
            patch("parallax.cli.run_interview", return_value=cfg),
            patch("parallax.cli.run_refinement", return_value=False),
        ):
            result = runner.invoke(app, ["init", "-t", str(tmp_path)])
        assert result.exit_code == 0
        assert cache.exists()

    def test_keep_cache_flag(self, tmp_path: Path) -> None:
        """--keep-cache preserves cache file after init."""
        cfg = _dummy_config()
        cache = tmp_path / _CACHE_REL
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "--keep-cache"]
            )
        assert result.exit_code == 0
        assert cache.exists()

    def test_resume_from_cache(self, tmp_path: Path) -> None:
        """If cache exists and user confirms, skip interview."""
        cfg = _dummy_config()
        cache = tmp_path / _CACHE_REL
        cfg.to_json(cache)
        with (
            patch("parallax.cli.run_interview") as mock_interview,
            patch("parallax.cli.typer.confirm", return_value=True),
        ):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-f"]
            )
        assert result.exit_code == 0
        mock_interview.assert_not_called()

    def test_decline_cache_runs_interview(self, tmp_path: Path) -> None:
        """If user declines cache, interview runs fresh."""
        cfg = _dummy_config()
        cache = tmp_path / _CACHE_REL
        cfg.to_json(cache)
        with (
            patch("parallax.cli.run_interview", return_value=cfg) as mock_interview,
            patch("parallax.cli.typer.confirm", return_value=False),
        ):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-f"]
            )
        assert result.exit_code == 0
        mock_interview.assert_called_once()
