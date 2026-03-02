"""Tests for the refiner module."""

import subprocess as _subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from parallax.core.refiner import _BACKGROUND_TIMEOUT, run_refinement


class TestRunRefinement:
    def test_missing_claude_cli(self, tmp_path: Path) -> None:
        with patch("parallax.core.refiner.shutil.which", return_value=None):
            result = run_refinement(tmp_path)
        assert result is False

    def test_missing_claude_cli_background(self, tmp_path: Path) -> None:
        with patch("parallax.core.refiner.shutil.which", return_value=None):
            result = run_refinement(tmp_path, background=True)
        assert result is False


class TestInteractiveMode:
    def test_successful(self, tmp_path: Path) -> None:
        mock_result = MagicMock(returncode=0)
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run", return_value=mock_result
            ) as mock_run,
        ):
            result = run_refinement(tmp_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "claude"
        assert "-p" not in args
        assert mock_run.call_args[1]["cwd"] == tmp_path
        # No timeout in interactive mode
        assert "timeout" not in mock_run.call_args[1]

    def test_nonzero_exit(self, tmp_path: Path) -> None:
        mock_result = MagicMock(returncode=1)
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run", return_value=mock_result
            ),
        ):
            result = run_refinement(tmp_path)

        assert result is False

    def test_file_not_found(self, tmp_path: Path) -> None:
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run",
                side_effect=FileNotFoundError,
            ),
        ):
            result = run_refinement(tmp_path)

        assert result is False


class TestBackgroundMode:
    def test_successful(self, tmp_path: Path) -> None:
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch("parallax.core.refiner.subprocess.run") as mock_run,
        ):
            result = run_refinement(tmp_path, background=True)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "claude"
        assert "-p" in args
        assert mock_run.call_args[1]["cwd"] == tmp_path
        assert mock_run.call_args[1]["timeout"] == _BACKGROUND_TIMEOUT

    def test_failed(self, tmp_path: Path) -> None:
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run",
                side_effect=_subprocess.CalledProcessError(1, "claude"),
            ),
        ):
            result = run_refinement(tmp_path, background=True)

        assert result is False

    def test_timeout(self, tmp_path: Path) -> None:
        with (
            patch(
                "parallax.core.refiner.shutil.which",
                return_value="/usr/bin/claude",
            ),
            patch(
                "parallax.core.refiner.subprocess.run",
                side_effect=_subprocess.TimeoutExpired("claude", _BACKGROUND_TIMEOUT),
            ),
        ):
            result = run_refinement(tmp_path, background=True)

        assert result is False
