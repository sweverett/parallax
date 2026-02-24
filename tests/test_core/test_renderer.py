"""Tests for the renderer module."""

from pathlib import Path

import pytest

from parallax.core.renderer import (
    check_conflicts,
    model_for_agent,
    render_agent,
    render_claude_md,
    render_constitution_md,
    render_custom_agent,
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
        out = render_skill("hypothesis", make_config())
        assert "test-project" in out
        assert "/hypothesis" in out

    def test_all_skills_render(self) -> None:
        for name in [
            "hypothesis",
            "handoff",
            "audit",
            "experiment",
            "session_start",
        ]:
            out = render_skill(name, make_config())
            assert "test-project" in out
            assert "${" not in out

    def test_hypothesis_has_memory(self) -> None:
        out = render_skill("hypothesis", make_config())
        assert "memory: project" in out

    def test_experiment_has_memory(self) -> None:
        out = render_skill("experiment", make_config())
        assert "memory: project" in out

    def test_session_start_render(self) -> None:
        out = render_skill("session_start", make_config())
        assert "session-start" in out
        assert "handoffs" in out.lower()


# ---------------------------------------------------------------------------
# Agent rendering
# ---------------------------------------------------------------------------


class TestModelForAgent:
    def test_pro_tier_models(self) -> None:
        assert model_for_agent("hypothesis_explorer", "pro") == "haiku"
        assert model_for_agent("experiment_runner", "pro") == "sonnet"
        assert model_for_agent("literature_reviewer", "pro") == "haiku"
        assert model_for_agent("result_validator", "pro") == "sonnet"

    def test_5x_tier_models(self) -> None:
        assert model_for_agent("hypothesis_explorer", "5x") == "opus"
        assert model_for_agent("experiment_runner", "5x") == "sonnet"
        assert model_for_agent("literature_reviewer", "5x") == "sonnet"
        assert model_for_agent("result_validator", "5x") == "opus"

    def test_api_tier_all_opus(self) -> None:
        for agent in [
            "hypothesis_explorer",
            "experiment_runner",
            "literature_reviewer",
            "result_validator",
        ]:
            assert model_for_agent(agent, "api") == "opus"

    def test_unknown_agent_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown agent"):
            model_for_agent("nonexistent", "pro")

    def test_unknown_tier_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown token tier"):
            model_for_agent("hypothesis_explorer", "free")  # type: ignore[arg-type]


class TestRenderAgent:
    def test_hypothesis_explorer_pro(self) -> None:
        out = render_agent("hypothesis_explorer", make_config())
        assert "model: haiku" in out
        assert "hypothesis-explorer" in out
        assert "worktree" in out
        assert "${" not in out

    def test_experiment_runner_5x(self) -> None:
        out = render_agent("experiment_runner", make_config(token_tier="5x"))
        assert "model: sonnet" in out
        assert "experiment-runner" in out

    def test_literature_reviewer_has_domain(self) -> None:
        out = render_agent("literature_reviewer", make_config(domain="genomics"))
        assert "genomics" in out

    def test_result_validator_20x(self) -> None:
        out = render_agent("result_validator", make_config(token_tier="20x"))
        assert "model: opus" in out
        assert "result-validator" in out

    def test_all_agents_no_unsubstituted_vars(self) -> None:
        for name in [
            "hypothesis_explorer",
            "experiment_runner",
            "literature_reviewer",
            "result_validator",
        ]:
            out = render_agent(name, make_config())
            assert "${" not in out, f"Unsubstituted var in {name}"


class TestRenderCustomAgent:
    def test_basic_render(self) -> None:
        out = render_custom_agent(
            make_config(custom_agent_description="validates ETL pipeline outputs")
        )
        assert "validates ETL pipeline outputs" in out
        assert "name: custom" in out
        assert "test-project" in out
        assert "${" not in out

    def test_empty_description_still_renders(self) -> None:
        out = render_custom_agent(make_config(custom_agent_description=""))
        assert "name: custom" in out


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
        assert ".claude/skills/hypothesis/SKILL.md" in names
        assert ".claude/skills/handoff/SKILL.md" in names
        assert ".claude/skills/audit/SKILL.md" in names
        assert ".claude/skills/experiment/SKILL.md" in names
        assert ".claude/skills/session-start/SKILL.md" in names
        # Agent files
        assert ".claude/agents/hypothesis-explorer.md" in names
        assert ".claude/agents/experiment-runner.md" in names
        assert ".claude/agents/literature-reviewer.md" in names
        assert ".claude/agents/result-validator.md" in names

    def test_no_skills_when_disabled(self, tmp_path: Path) -> None:
        written = render_project(make_config(generate_skills=False), tmp_path)
        names = {p.relative_to(tmp_path).as_posix() for p in written}
        assert not any("skills/" in n for n in names)
        assert not any("agents/" in n for n in names)

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

    def test_agents_have_correct_models_pro(self, tmp_path: Path) -> None:
        render_project(make_config(token_tier="pro"), tmp_path)
        explorer = (
            tmp_path / ".claude" / "agents" / "hypothesis-explorer.md"
        ).read_text()
        assert "model: haiku" in explorer
        runner = (tmp_path / ".claude" / "agents" / "experiment-runner.md").read_text()
        assert "model: sonnet" in runner

    def test_agents_have_correct_models_api(self, tmp_path: Path) -> None:
        render_project(make_config(token_tier="api"), tmp_path)
        agents_dir = tmp_path / ".claude" / "agents"
        for f in agents_dir.glob("*.md"):
            assert "model: opus" in f.read_text(), (
                f"{f.name} should have opus for api tier"
            )

    def test_custom_agent_generated(self, tmp_path: Path) -> None:
        render_project(make_config(custom_agent_description="validates data"), tmp_path)
        custom = (tmp_path / ".claude" / "agents" / "custom.md").read_text()
        assert "validates data" in custom
        assert "${" not in custom

    def test_no_custom_agent_when_empty(self, tmp_path: Path) -> None:
        render_project(make_config(), tmp_path)
        assert not (tmp_path / ".claude" / "agents" / "custom.md").exists()
