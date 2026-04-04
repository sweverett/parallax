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
        "package_manager": "conda",
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


class TestMergeMode:
    def test_merge_mode_detected(self, tmp_path: Path) -> None:
        """Existing CLAUDE.md (no PARALLAX.md) triggers merge mode."""
        (tmp_path / "CLAUDE.md").write_text("# Existing project")
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-y"]
            )
        assert result.exit_code == 0
        assert "merge" in result.output.lower()
        # Existing file untouched
        assert (tmp_path / "CLAUDE.md").read_text() == "# Existing project"
        # Suffixed file created
        assert (tmp_path / "CLAUDE.parallax.md").exists()

    def test_merge_mode_shows_conflicts(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = _dummy_config()
        with (
            patch("parallax.cli.run_interview", return_value=cfg),
            patch("parallax.cli.typer.confirm", return_value=True),
        ):
            result = runner.invoke(app, ["init", "-t", str(tmp_path), "--skip-refine"])
        assert result.exit_code == 0
        assert "CLAUDE.md" in result.output
        assert "conflict" in result.output.lower()

    def test_merge_mode_yes_skips_confirm(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = _dummy_config()
        with (
            patch("parallax.cli.run_interview", return_value=cfg),
            # No confirm mock needed -- -y should skip it
        ):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-y"]
            )
        assert result.exit_code == 0

    def test_merge_mode_force_skips_merge(self, tmp_path: Path) -> None:
        """Force overwrites normally, no suffixes."""
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "-f", "--skip-refine"]
            )
        assert result.exit_code == 0
        # Force overwrites, so no .parallax suffix
        assert not (tmp_path / "CLAUDE.parallax.md").exists()
        assert "test-project" in (tmp_path / "CLAUDE.md").read_text()

    def test_merge_mode_offers_claude_session(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = _dummy_config()
        with (
            patch("parallax.cli.run_interview", return_value=cfg),
            patch("parallax.cli.typer.confirm", return_value=False),
            patch("parallax.cli.run_refinement", return_value=True) as mock_refine,
        ):
            result = runner.invoke(app, ["init", "-t", str(tmp_path)])
        assert result.exit_code == 0
        # Should not have launched refinement since user declined
        mock_refine.assert_not_called()

    def test_merge_mode_skip_refine_no_session(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-y"]
            )
        assert result.exit_code == 0
        assert "merge-guide.md" in result.output

    def test_merge_guide_path_printed(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = _dummy_config()
        with patch("parallax.cli.run_interview", return_value=cfg):
            result = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-y"]
            )
        assert result.exit_code == 0
        assert "merge-guide.md" in result.output

    def test_force_after_merge_overwrites_but_leaves_suffixed(
        self, tmp_path: Path
    ) -> None:
        """Merge then force: force overwrites originals, .parallax files survive."""
        cfg = _dummy_config()
        # Step 1: merge mode -- creates .parallax suffixed files
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        with patch("parallax.cli.run_interview", return_value=cfg):
            r1 = runner.invoke(
                app, ["init", "-t", str(tmp_path), "--skip-refine", "-y"]
            )
        assert r1.exit_code == 0
        assert (tmp_path / "CLAUDE.parallax.md").exists()
        assert (tmp_path / "CLAUDE.md").read_text() == "# Existing"

        # Step 2: force reinit -- overwrites everything, no merge
        with patch("parallax.cli.run_interview", return_value=cfg):
            r2 = runner.invoke(
                app, ["init", "-t", str(tmp_path), "-f", "--skip-refine"]
            )
        assert r2.exit_code == 0
        # CLAUDE.md now has generated content
        assert "test-project" in (tmp_path / "CLAUDE.md").read_text()
        # .parallax file from previous merge still on disk (force doesn't clean up)
        assert (tmp_path / "CLAUDE.parallax.md").exists()
