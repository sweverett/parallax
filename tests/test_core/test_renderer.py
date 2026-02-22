"""Tests for the renderer module."""

from pathlib import Path

import pytest

from parallax.core.renderer import (
    check_conflicts,
    render_claude_md,
    render_constitution_md,
    render_parallax_md,
    render_project,
    render_settings_json,
    render_skill,
)
from tests.conftest import make_config

# ---------------------------------------------------------------------------
# CLAUDE.md rendering
# ---------------------------------------------------------------------------


class TestRenderClaudeMd:
    def test_basic_fields(self) -> None:
        out = render_claude_md(make_config())
        assert "test-project" in out
        assert "A test project" in out
        assert "astrophysics" in out
        assert "Python" in out
        assert "pixi" in out
        assert "pytest" in out

    def test_refinement_block_present(self) -> None:
        out = render_claude_md(make_config())
        assert "PARALLAX REFINEMENT" in out
        assert "parallax refine --done" in out

    def test_units_rule_absent_by_default(self) -> None:
        out = render_claude_md(make_config())
        assert "Dimensional analysis" not in out

    def test_units_rule_present(self) -> None:
        out = render_claude_md(make_config(uses_units=True))
        assert "Dimensional analysis is mandatory" in out

    def test_git_section_absent_without_prefix(self) -> None:
        out = render_claude_md(make_config())
        assert "Git Workflow" not in out

    def test_git_section_present_with_prefix(self) -> None:
        out = render_claude_md(make_config(branch_prefix="se/"))
        assert "Git Workflow" in out
        assert "se/" in out

    def test_optional_sections(self) -> None:
        out = render_claude_md(
            make_config(
                science_requirements="Measure galaxy redshifts",
                preferred_patterns="Functional style",
                outlawed_patterns="No global state",
                key_libraries="astropy: units and coordinates",
            )
        )
        assert "Science Requirements" in out
        assert "Measure galaxy redshifts" in out
        assert "Preferred Patterns" in out
        assert "Functional style" in out
        assert "Outlawed Patterns" in out
        assert "No global state" in out
        assert "Key Libraries" in out
        assert "astropy" in out

    def test_no_unsubstituted_vars(self) -> None:
        out = render_claude_md(make_config())
        # safe_substitute leaves unknown $vars; we should have none
        assert "${" not in out


# ---------------------------------------------------------------------------
# PARALLAX.md rendering
# ---------------------------------------------------------------------------


class TestRenderParallaxMd:
    def test_basic_fields(self) -> None:
        out = render_parallax_md(make_config())
        assert "test-project" in out
        assert "astrophysics" in out

    def test_jax_absent_by_default(self) -> None:
        out = render_parallax_md(make_config())
        assert "JAX" not in out

    def test_jax_present(self) -> None:
        out = render_parallax_md(make_config(uses_jax=True))
        assert "JAX" in out
        assert "pure functions" in out.lower() or "Pure functions" in out

    def test_no_unsubstituted_vars(self) -> None:
        out = render_parallax_md(make_config())
        assert "${" not in out


# ---------------------------------------------------------------------------
# CONSTITUTION.md rendering
# ---------------------------------------------------------------------------


class TestRenderConstitutionMd:
    def test_project_name(self) -> None:
        out = render_constitution_md(make_config())
        assert "test-project" in out

    def test_principles_present(self) -> None:
        out = render_constitution_md(make_config())
        assert "Robust science" in out
        assert "Reproducibility" in out


# ---------------------------------------------------------------------------
# settings.json rendering
# ---------------------------------------------------------------------------


class TestRenderSettingsJson:
    def test_valid_json(self) -> None:
        import json

        out = render_settings_json(make_config())
        parsed = json.loads(out)
        assert "hooks" in parsed

    def test_references_hook_scripts(self) -> None:
        out = render_settings_json(make_config())
        assert "test_guard.py" in out
        assert "lint_check.py" in out
        assert "stop_check.py" in out

    def test_no_echo_stubs(self) -> None:
        out = render_settings_json(make_config())
        assert "echo" not in out.lower()


# ---------------------------------------------------------------------------
# Skill rendering
# ---------------------------------------------------------------------------


class TestRenderSkill:
    def test_hypothesis(self) -> None:
        out = render_skill("hypothesis.md", make_config())
        assert "test-project" in out
        assert "/hypothesis" in out

    def test_all_skills_render(self) -> None:
        for name in ["hypothesis.md", "handoff.md", "audit.md", "experiment.md"]:
            out = render_skill(name, make_config())
            assert "test-project" in out
            assert "${" not in out


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------


class TestConflicts:
    def test_no_conflicts_empty_dir(self, tmp_path: Path) -> None:
        assert check_conflicts(make_config(), tmp_path, force=False) == []

    def test_conflict_detected(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("existing")
        conflicts = check_conflicts(make_config(), tmp_path, force=False)
        assert len(conflicts) == 1
        assert conflicts[0].name == "CLAUDE.md"

    def test_force_ignores_conflicts(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("existing")
        assert check_conflicts(make_config(), tmp_path, force=True) == []


# ---------------------------------------------------------------------------
# render_project orchestrator
# ---------------------------------------------------------------------------


class TestRenderProject:
    def test_creates_all_files(self, tmp_path: Path) -> None:
        written = render_project(make_config(), tmp_path)
        names = {p.relative_to(tmp_path).as_posix() for p in written}
        assert "CLAUDE.md" in names
        assert "PARALLAX.md" in names
        assert "CONSTITUTION.md" in names
        assert ".claude/settings.json" in names
        assert ".claude/hooks/test_guard.py" in names
        assert ".claude/hooks/lint_check.py" in names
        assert ".claude/hooks/stop_check.py" in names
        assert ".claude/skills/hypothesis.md" in names
        assert ".claude/skills/handoff.md" in names
        assert ".claude/skills/audit.md" in names
        assert ".claude/skills/experiment.md" in names

    def test_no_skills_when_disabled(self, tmp_path: Path) -> None:
        written = render_project(make_config(generate_skills=False), tmp_path)
        names = {p.name for p in written}
        assert "hypothesis.md" not in names

    def test_no_hooks_when_disabled(self, tmp_path: Path) -> None:
        written = render_project(make_config(generate_hooks=False), tmp_path)
        names = {p.relative_to(tmp_path).as_posix() for p in written}
        assert "settings.json" not in {p.name for p in written}
        assert not any(".claude/hooks/" in n for n in names)

    def test_already_initialized_error(self, tmp_path: Path) -> None:
        (tmp_path / "PARALLAX.md").write_text("existing")
        with pytest.raises(FileExistsError, match="already Parallax-managed"):
            render_project(make_config(), tmp_path)

    def test_force_overwrites(self, tmp_path: Path) -> None:
        (tmp_path / "PARALLAX.md").write_text("old")
        render_project(make_config(), tmp_path, force=True)
        assert "test-project" in (tmp_path / "PARALLAX.md").read_text()

    def test_generic_conflict_error(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("existing")
        with pytest.raises(FileExistsError, match="CLAUDE.md"):
            render_project(make_config(), tmp_path)

    def test_file_contents_valid(self, tmp_path: Path) -> None:
        render_project(make_config(), tmp_path)
        claude = (tmp_path / "CLAUDE.md").read_text()
        assert "test-project" in claude
        assert "${" not in claude
        parallax = (tmp_path / "PARALLAX.md").read_text()
        assert "Hypothesis Protocol" in parallax
        assert "${" not in parallax
