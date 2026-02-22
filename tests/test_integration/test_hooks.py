"""Integration tests: simulate hook execution with subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Resolve hook template paths
_HOOKS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "parallax"
    / "templates"
    / "hooks"
)


def _run_hook(hook_name: str, stdin_json: str) -> subprocess.CompletedProcess[str]:
    """Run a hook script with the given stdin content."""
    hook_path = _HOOKS_DIR / hook_name
    return subprocess.run(
        [sys.executable, str(hook_path)],
        input=stdin_json,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _edit_payload(file_path: str, old_string: str, new_string: str) -> str:
    return json.dumps(
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": file_path,
                "old_string": old_string,
                "new_string": new_string,
            },
        }
    )


def _write_payload(file_path: str, content: str) -> str:
    return json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": file_path,
                "content": content,
            },
        }
    )


# ---------------------------------------------------------------------------
# test_guard.py tests
# ---------------------------------------------------------------------------


class TestTestGuard:
    def test_blocks_skip_marker(self) -> None:
        payload = _write_payload(
            "/project/tests/test_foo.py",
            "@pytest.mark.skip\ndef test_thing(): pass",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode != 0
        assert "skip" in result.stdout.lower()

    def test_blocks_xfail(self) -> None:
        payload = _write_payload(
            "/project/tests/test_foo.py",
            "@pytest.mark.xfail\ndef test_thing(): pass",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode != 0
        assert "xfail" in result.stdout.lower()

    def test_blocks_assert_true(self) -> None:
        payload = _write_payload(
            "/project/tests/test_foo.py",
            "def test_thing():\n    assert True",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode != 0
        assert "assert True" in result.stdout

    def test_blocks_noqa_in_test(self) -> None:
        payload = _write_payload(
            "/project/tests/test_foo.py",
            "x = bad_code  # noqa: F841",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode != 0
        assert "noqa" in result.stdout.lower()

    def test_blocks_type_ignore_in_test(self) -> None:
        payload = _write_payload(
            "/project/tests/test_foo.py",
            "x: int = 'bad'  # type: ignore",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode != 0
        assert "type: ignore" in result.stdout

    def test_blocks_assertion_removal(self) -> None:
        payload = _edit_payload(
            "/project/tests/test_foo.py",
            "assert result == 42\nassert result > 0",
            "pass",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode != 0
        assert "assertion count reduced" in result.stdout

    def test_allows_normal_test_edit(self) -> None:
        payload = _edit_payload(
            "/project/tests/test_foo.py",
            "x = 1",
            "x = 2",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode == 0

    def test_allows_non_test_file(self) -> None:
        payload = _write_payload(
            "/project/src/main.py",
            "@pytest.mark.skip\nassert True",
        )
        result = _run_hook("test_guard.py", payload)
        assert result.returncode == 0

    def test_handles_malformed_json(self) -> None:
        result = _run_hook("test_guard.py", "not json at all{{{")
        assert result.returncode == 0

    def test_handles_empty_stdin(self) -> None:
        result = _run_hook("test_guard.py", "")
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# lint_check.py tests
# ---------------------------------------------------------------------------


class TestLintCheck:
    def test_runs_without_crash(self) -> None:
        payload = _write_payload("/tmp/test_file.py", "x = 1\n")
        result = _run_hook("lint_check.py", payload)
        assert result.returncode == 0

    def test_ignores_non_python(self) -> None:
        payload = _write_payload("/tmp/readme.md", "# hello\n")
        result = _run_hook("lint_check.py", payload)
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# stop_check.py tests
# ---------------------------------------------------------------------------


class TestStopCheck:
    def test_runs_in_git_repo(self, tmp_path: Path) -> None:
        """Run stop_check in a temp git repo."""
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
        hook_path = _HOOKS_DIR / "stop_check.py"
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="",
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=10,
        )
        assert result.returncode == 0

    @pytest.mark.usefixtures("tmp_path")
    def test_runs_outside_git_repo(self, tmp_path: Path) -> None:
        """Run stop_check in a non-git temp dir."""
        hook_path = _HOOKS_DIR / "stop_check.py"
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="",
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=10,
        )
        assert result.returncode == 0
