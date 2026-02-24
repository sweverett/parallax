"""Tests for the refiner module."""

from pathlib import Path
from unittest.mock import patch

from parallax.core.refiner import run_refinement


class TestRunRefinement:
    def test_missing_claude_cli(self, tmp_path: Path) -> None:
        with patch("parallax.core.refiner.shutil.which", return_value=None):
            result = run_refinement(tmp_path)
        assert result is False

    def test_successful_refinement(self, tmp_path: Path) -> None:
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch("parallax.core.refiner.subprocess.run") as mock_run,
        ):
            result = run_refinement(tmp_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "claude"
        assert "-p" in args
        assert "--cwd" in args
        assert str(tmp_path) in args

    def test_failed_refinement(self, tmp_path: Path) -> None:
        import subprocess

        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "claude"),
            ),
        ):
            result = run_refinement(tmp_path)

        assert result is False

    def test_timeout(self, tmp_path: Path) -> None:
        import subprocess

        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run",
                side_effect=subprocess.TimeoutExpired("claude", 120),
            ),
        ):
            result = run_refinement(tmp_path)

        assert result is False
