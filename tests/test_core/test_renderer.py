"""Tests for the renderer module."""

from pathlib import Path

import pytest

from parallax.core.renderer import (
    _render_sync_content,
    _suffix_path,
    check_conflicts,
    classify_outputs,
    classify_sync,
    derive_config_from_target,
    model_for_agent,
    render_agent,
    render_claude_md,
    render_constitution_md,
    render_custom_agent,
    render_parallax_md,
    render_project,
    render_settings_json,
    render_skill,
    render_sync,
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
        assert "conda" in out
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

    def test_handoff_format_filename_storage(self) -> None:
        out = render_parallax_md(make_config())
        assert "Filename and storage" in out
        assert "YYYY-MM-DD_<topic>.md" in out
        assert "docs/sessions/" in out


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
            "manuscript_review",
            "latex_guide",
            "grill_me",
            "test_integrity",
            "doc_sync",
        ]:
            out = render_skill(name, make_config())
            assert "${" not in out

    def test_test_integrity_render(self) -> None:
        out = render_skill("test_integrity", make_config())
        assert "test-integrity" in out
        assert "disable-model-invocation: true" not in out
        assert "Weakening Patterns" in out
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
        assert "sort -r" in out

    def test_handoff_render_contains_writer_rule(self) -> None:
        out = render_skill("handoff", make_config())
        assert "docs/sessions/" in out
        assert "YYYY-MM-DD" in out

    def test_manuscript_review_render(self) -> None:
        out = render_skill("manuscript_review", make_config())
        assert "manuscript-review" in out
        assert "Paper Mode" in out
        assert "Presentation Mode" in out
        assert "disable-model-invocation: true" in out

    def test_latex_guide_render(self) -> None:
        out = render_skill("latex_guide", make_config())
        assert "latex-guide" in out
        assert "BibTeX" in out
        assert "disable-model-invocation" not in out

    def test_doc_sync_render(self) -> None:
        out = render_skill("doc_sync", make_config())
        assert "doc-sync" in out
        assert "disable-model-invocation: true" in out
        assert "Category A" in out
        assert "Category G" in out
        assert "${" not in out


# ---------------------------------------------------------------------------
# Agent rendering
# ---------------------------------------------------------------------------


class TestModelForAgent:
    def test_pro_tier_models(self) -> None:
        assert model_for_agent("hypothesis_explorer", "pro") == "haiku"
        assert model_for_agent("experiment_runner", "pro") == "sonnet"
        assert model_for_agent("literature_reviewer", "pro") == "haiku"
        assert model_for_agent("result_validator", "pro") == "sonnet"
        assert model_for_agent("paper_writer", "pro") == "sonnet"
        assert model_for_agent("presentation_writer", "pro") == "sonnet"
        assert model_for_agent("manuscript_reviewer", "pro") == "sonnet"

    def test_5x_tier_models(self) -> None:
        assert model_for_agent("hypothesis_explorer", "5x") == "opus"
        assert model_for_agent("experiment_runner", "5x") == "sonnet"
        assert model_for_agent("literature_reviewer", "5x") == "sonnet"
        assert model_for_agent("result_validator", "5x") == "opus"
        assert model_for_agent("paper_writer", "5x") == "opus"
        assert model_for_agent("presentation_writer", "5x") == "opus"
        assert model_for_agent("manuscript_reviewer", "5x") == "opus"

    def test_api_tier_all_opus(self) -> None:
        for agent in [
            "hypothesis_explorer",
            "experiment_runner",
            "literature_reviewer",
            "result_validator",
            "paper_writer",
            "presentation_writer",
            "manuscript_reviewer",
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

    def test_paper_writer_pro(self) -> None:
        out = render_agent("paper_writer", make_config())
        assert "model: sonnet" in out
        assert "paper-writer" in out
        assert "astrophysics" in out
        assert "${" not in out

    def test_paper_writer_5x(self) -> None:
        out = render_agent("paper_writer", make_config(token_tier="5x"))
        assert "model: opus" in out

    def test_presentation_writer_pro(self) -> None:
        out = render_agent("presentation_writer", make_config())
        assert "model: sonnet" in out
        assert "presentation-writer" in out
        assert "astrophysics" in out
        assert "${" not in out

    def test_presentation_writer_5x(self) -> None:
        out = render_agent("presentation_writer", make_config(token_tier="5x"))
        assert "model: opus" in out

    def test_manuscript_reviewer_pro(self) -> None:
        out = render_agent("manuscript_reviewer", make_config())
        assert "model: sonnet" in out
        assert "manuscript-reviewer" in out
        assert "disallowedTools:" in out
        assert "${" not in out

    def test_manuscript_reviewer_5x(self) -> None:
        out = render_agent("manuscript_reviewer", make_config(token_tier="5x"))
        assert "model: opus" in out

    def test_all_agents_no_unsubstituted_vars(self) -> None:
        for name in [
            "hypothesis_explorer",
            "experiment_runner",
            "literature_reviewer",
            "result_validator",
            "paper_writer",
            "presentation_writer",
            "manuscript_reviewer",
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
        result = render_project(make_config(), tmp_path)
        names = {p.relative_to(tmp_path).as_posix() for p in result.written}
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
        assert ".claude/agents/paper-writer.md" in names
        assert ".claude/agents/presentation-writer.md" in names
        assert ".claude/agents/manuscript-reviewer.md" in names
        assert ".claude/skills/manuscript-review/SKILL.md" in names
        assert ".claude/skills/latex-guide/SKILL.md" in names
        assert ".claude/skills/doc-sync/SKILL.md" in names

    def test_no_skills_when_disabled(self, tmp_path: Path) -> None:
        result = render_project(make_config(generate_skills=False), tmp_path)
        names = {p.relative_to(tmp_path).as_posix() for p in result.written}
        assert not any("skills/" in n for n in names)
        assert not any("agents/" in n for n in names)

    def test_no_hooks_when_disabled(self, tmp_path: Path) -> None:
        result = render_project(make_config(generate_hooks=False), tmp_path)
        names = {p.relative_to(tmp_path).as_posix() for p in result.written}
        assert "settings.json" not in {p.name for p in result.written}
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
        writer = (tmp_path / ".claude" / "agents" / "paper-writer.md").read_text()
        assert "model: sonnet" in writer
        presenter = (
            tmp_path / ".claude" / "agents" / "presentation-writer.md"
        ).read_text()
        assert "model: sonnet" in presenter

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

    def test_returns_merge_result(self, tmp_path: Path) -> None:
        result = render_project(make_config(), tmp_path)
        assert hasattr(result, "written")
        assert hasattr(result, "suffixed")
        assert hasattr(result, "skipped")
        assert len(result.written) > 0
        assert result.suffixed == []
        assert result.skipped == []


# ---------------------------------------------------------------------------
# Template edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_project_name_with_spaces(self) -> None:
        out = render_claude_md(make_config(project_name="My Cool Project"))
        assert "My Cool Project" in out
        assert "${" not in out

    def test_project_name_with_hyphens_and_numbers(self) -> None:
        out = render_claude_md(make_config(project_name="astro-v2"))
        assert "astro-v2" in out
        assert "${" not in out

    def test_very_long_summary(self) -> None:
        long_summary = "A" * 250
        out = render_claude_md(make_config(summary=long_summary))
        assert long_summary in out

    def test_domain_with_special_chars(self) -> None:
        out = render_claude_md(make_config(domain="high-energy particle physics"))
        assert "high-energy particle physics" in out
        assert "${" not in out


# ---------------------------------------------------------------------------
# Suffix infrastructure
# ---------------------------------------------------------------------------


class TestSuffixPath:
    def test_suffix_path_markdown(self) -> None:
        assert _suffix_path(Path("CLAUDE.md")) == Path("CLAUDE.parallax.md")

    def test_suffix_path_python(self) -> None:
        assert _suffix_path(Path("test_guard.py")) == Path("test_guard.parallax.py")

    def test_suffix_path_json(self) -> None:
        assert _suffix_path(Path("settings.json")) == Path("settings.parallax.json")

    def test_suffix_path_nested(self) -> None:
        p = Path(".claude/skills/hypothesis/SKILL.md")
        expected = Path(".claude/skills/hypothesis/SKILL.parallax.md")
        assert _suffix_path(p) == expected


# ---------------------------------------------------------------------------
# Classify outputs
# ---------------------------------------------------------------------------


class TestClassifyOutputs:
    def test_classify_all_new(self, tmp_path: Path) -> None:
        new, conflicting, identical = classify_outputs(make_config(), tmp_path)
        assert len(new) > 0
        assert len(conflicting) == 0
        assert len(identical) == 0

    def test_classify_one_conflict(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing project")
        new, conflicting, identical = classify_outputs(make_config(), tmp_path)
        assert "CLAUDE.md" in conflicting
        assert "CLAUDE.md" not in new

    def test_classify_identical_skip(self, tmp_path: Path) -> None:
        # Render once to get exact content
        cfg = make_config()
        content = render_claude_md(cfg)
        (tmp_path / "CLAUDE.md").write_text(content)
        new, conflicting, identical = classify_outputs(cfg, tmp_path)
        assert "CLAUDE.md" in identical
        assert "CLAUDE.md" not in new
        assert "CLAUDE.md" not in conflicting

    def test_classify_mixed(self, tmp_path: Path) -> None:
        cfg = make_config()
        # Write one file with different content (conflict)
        (tmp_path / "CLAUDE.md").write_text("# Different")
        # Write one file with identical content (skip)
        content = render_constitution_md(cfg)
        (tmp_path / "CONSTITUTION.md").write_text(content)
        new, conflicting, identical = classify_outputs(cfg, tmp_path)
        assert "CLAUDE.md" in conflicting
        assert "CONSTITUTION.md" in identical
        # PARALLAX.md should be new
        assert "PARALLAX.md" in new


# ---------------------------------------------------------------------------
# Merge mode rendering
# ---------------------------------------------------------------------------


class TestMergeMode:
    def test_merge_writes_new_normally(self, tmp_path: Path) -> None:
        # Put an existing CLAUDE.md so merge mode has something to suffix
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        result = render_project(make_config(), tmp_path, merge=True)
        # PARALLAX.md should be new (didn't exist)
        written_names = {p.name for p in result.written}
        assert "PARALLAX.md" in written_names
        assert (tmp_path / "PARALLAX.md").exists()

    def test_merge_suffixes_conflicts(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        result = render_project(make_config(), tmp_path, merge=True)
        suffixed_names = {p.name for p in result.suffixed}
        assert "CLAUDE.parallax.md" in suffixed_names
        assert (tmp_path / "CLAUDE.parallax.md").exists()

    def test_merge_skips_identical(self, tmp_path: Path) -> None:
        cfg = make_config()
        content = render_constitution_md(cfg)
        (tmp_path / "CONSTITUTION.md").write_text(content)
        result = render_project(cfg, tmp_path, merge=True)
        skipped_names = {p.name for p in result.skipped}
        assert "CONSTITUTION.md" in skipped_names
        # Should NOT have written a .parallax version
        assert not (tmp_path / "CONSTITUTION.parallax.md").exists()

    def test_merge_result_categories(self, tmp_path: Path) -> None:
        cfg = make_config()
        (tmp_path / "CLAUDE.md").write_text("# Different")
        content = render_constitution_md(cfg)
        (tmp_path / "CONSTITUTION.md").write_text(content)
        result = render_project(cfg, tmp_path, merge=True)
        assert len(result.written) > 0
        assert len(result.suffixed) > 0
        assert len(result.skipped) > 0

    def test_merge_never_touches_originals(self, tmp_path: Path) -> None:
        original_content = "# My existing CLAUDE.md\nDo not modify."
        (tmp_path / "CLAUDE.md").write_text(original_content)
        render_project(make_config(), tmp_path, merge=True)
        assert (tmp_path / "CLAUDE.md").read_text() == original_content

    def test_merge_guide_written(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        render_project(make_config(), tmp_path, merge=True)
        guide = tmp_path / ".parallax" / "merge-guide.md"
        assert guide.exists()

    def test_merge_guide_content(self, tmp_path: Path) -> None:
        (tmp_path / "CLAUDE.md").write_text("# Existing")
        cfg = make_config()
        content = render_constitution_md(cfg)
        (tmp_path / "CONSTITUTION.md").write_text(content)
        render_project(cfg, tmp_path, merge=True)
        guide = tmp_path / ".parallax" / "merge-guide.md"
        text = guide.read_text()
        assert "CLAUDE.parallax.md" in text
        assert "CONSTITUTION.md" in text  # listed as identical/skipped
        assert "parallax refine" in text

    def test_merge_no_guide_when_no_conflicts(self, tmp_path: Path) -> None:
        result = render_project(make_config(), tmp_path, merge=True)
        assert len(result.suffixed) == 0
        assert not (tmp_path / ".parallax" / "merge-guide.md").exists()


# ---------------------------------------------------------------------------
# New ported skills
# ---------------------------------------------------------------------------


class TestPortedSkills:
    @pytest.mark.parametrize(
        "name",
        ["diagnose", "zoom_out", "improve_architecture", "ubiquitous_language"],
    )
    def test_skill_renders(self, name: str) -> None:
        out = render_skill(name, make_config())
        assert "${" not in out  # no unsubstituted vars
        assert out.lstrip().startswith("<!-- Adapted")  # attribution preserved

    def test_diagnose_cross_references_hypothesis(self) -> None:
        out = render_skill("diagnose", make_config())
        assert "/hypothesis" in out
        assert "/test-integrity" in out

    def test_zoom_out_disabled_invocation(self) -> None:
        out = render_skill("zoom_out", make_config())
        assert "disable-model-invocation: true" in out

    def test_improve_architecture_disabled_invocation(self) -> None:
        out = render_skill("improve_architecture", make_config())
        assert "disable-model-invocation: true" in out
        # Science-code preamble warning is the load-bearing local adaptation
        assert "scientific code" in out

    def test_ubiquitous_language_disabled_invocation(self) -> None:
        out = render_skill("ubiquitous_language", make_config())
        assert "disable-model-invocation: true" in out
        # Output filename is the load-bearing decision
        assert "UBIQUITOUS_LANGUAGE.md" in out


# ---------------------------------------------------------------------------
# Sync content rendering
# ---------------------------------------------------------------------------


class TestRenderSyncContent:
    def test_excludes_claude_md(self) -> None:
        files = _render_sync_content(make_config())
        assert "CLAUDE.md" not in files

    def test_excludes_parallax_md(self) -> None:
        files = _render_sync_content(make_config())
        assert "PARALLAX.md" not in files

    def test_includes_constitution(self) -> None:
        files = _render_sync_content(make_config())
        assert "CONSTITUTION.md" in files

    def test_includes_skills(self) -> None:
        files = _render_sync_content(make_config())
        skill_keys = [k for k in files if k.startswith(".claude/skills/")]
        assert len(skill_keys) > 0

    def test_includes_agents(self) -> None:
        files = _render_sync_content(make_config())
        agent_keys = [k for k in files if k.startswith(".claude/agents/")]
        assert len(agent_keys) > 0

    def test_includes_hooks_and_settings(self) -> None:
        files = _render_sync_content(make_config())
        assert ".claude/settings.json" in files
        hook_keys = [k for k in files if k.startswith(".claude/hooks/")]
        assert len(hook_keys) > 0


class TestClassifySync:
    def test_all_new_in_empty_target(self, tmp_path: Path) -> None:
        new, conflicting, identical = classify_sync(make_config(), tmp_path)
        assert len(new) > 0
        assert "CLAUDE.md" not in new  # never in sync output
        assert "PARALLAX.md" not in new
        assert len(conflicting) == 0
        assert len(identical) == 0

    def test_conflict_on_edited_file(self, tmp_path: Path) -> None:
        cfg = make_config()
        # Pre-create CONSTITUTION.md with different content
        (tmp_path / "CONSTITUTION.md").write_text("# user-edited")
        new, conflicting, identical = classify_sync(cfg, tmp_path)
        assert "CONSTITUTION.md" in conflicting

    def test_identical_when_matches(self, tmp_path: Path) -> None:
        cfg = make_config()
        (tmp_path / "CONSTITUTION.md").write_text(render_constitution_md(cfg))
        new, conflicting, identical = classify_sync(cfg, tmp_path)
        assert "CONSTITUTION.md" in identical


class TestRenderSync:
    def test_writes_new_files(self, tmp_path: Path) -> None:
        result = render_sync(make_config(), tmp_path)
        # CONSTITUTION.md is in sync subset and should be written
        names = {p.name for p in result.written}
        assert "CONSTITUTION.md" in names
        assert (tmp_path / "CONSTITUTION.md").exists()

    def test_does_not_write_claude_md(self, tmp_path: Path) -> None:
        render_sync(make_config(), tmp_path)
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_does_not_write_parallax_md(self, tmp_path: Path) -> None:
        render_sync(make_config(), tmp_path)
        assert not (tmp_path / "PARALLAX.md").exists()

    def test_suffixes_conflicting_file(self, tmp_path: Path) -> None:
        (tmp_path / "CONSTITUTION.md").write_text("# user-edited")
        result = render_sync(make_config(), tmp_path)
        suffixed_names = {p.name for p in result.suffixed}
        assert "CONSTITUTION.parallax.md" in suffixed_names
        # Original is untouched
        assert (tmp_path / "CONSTITUTION.md").read_text() == "# user-edited"

    def test_skips_identical(self, tmp_path: Path) -> None:
        cfg = make_config()
        (tmp_path / "CONSTITUTION.md").write_text(render_constitution_md(cfg))
        result = render_sync(cfg, tmp_path)
        skipped_names = {p.name for p in result.skipped}
        assert "CONSTITUTION.md" in skipped_names
        assert not (tmp_path / "CONSTITUTION.parallax.md").exists()

    def test_writes_merge_guide_with_sync_intro(self, tmp_path: Path) -> None:
        (tmp_path / "CONSTITUTION.md").write_text("# user-edited")
        render_sync(make_config(), tmp_path)
        guide = tmp_path / ".parallax" / "merge-guide.md"
        assert guide.exists()
        text = guide.read_text()
        assert "parallax sync" in text  # sync-mode intro line

    def test_no_guide_when_no_conflicts(self, tmp_path: Path) -> None:
        result = render_sync(make_config(), tmp_path)
        assert len(result.suffixed) == 0
        assert not (tmp_path / ".parallax" / "merge-guide.md").exists()


# ---------------------------------------------------------------------------
# Config derivation (for legacy projects without .parallax/config.json)
# ---------------------------------------------------------------------------


class TestDeriveConfig:
    def test_derives_project_name_from_parallax_md(self, tmp_path: Path) -> None:
        cfg = make_config(project_name="my-project", domain="genomics")
        render_project(cfg, tmp_path)
        derived, _ = derive_config_from_target(tmp_path)
        assert derived.project_name == "my-project"

    def test_derives_domain_from_parallax_md(self, tmp_path: Path) -> None:
        cfg = make_config(project_name="x", domain="exoplanets")
        render_project(cfg, tmp_path)
        derived, _ = derive_config_from_target(tmp_path)
        assert derived.domain == "exoplanets"

    @pytest.mark.parametrize("tier", ["pro", "5x", "20x"])
    def test_derives_token_tier(self, tmp_path: Path, tier: str) -> None:
        cfg = make_config(token_tier=tier)
        render_project(cfg, tmp_path)
        derived, _ = derive_config_from_target(tmp_path)
        assert derived.token_tier == tier

    def test_api_tier_ambiguous_with_20x(self, tmp_path: Path) -> None:
        """20x and api use identical models; derivation chooses 20x with warning."""
        cfg = make_config(token_tier="api")
        render_project(cfg, tmp_path)
        derived, warnings = derive_config_from_target(tmp_path)
        assert derived.token_tier == "20x"
        assert any("ambiguous" in w for w in warnings)

    def test_derives_skills_and_hooks_flags(self, tmp_path: Path) -> None:
        cfg = make_config(generate_skills=True, generate_hooks=True)
        render_project(cfg, tmp_path)
        derived, _ = derive_config_from_target(tmp_path)
        assert derived.generate_skills is True
        assert derived.generate_hooks is True

    def test_skills_false_when_no_skills_dir(self, tmp_path: Path) -> None:
        cfg = make_config(generate_skills=True, generate_hooks=False)
        render_project(cfg, tmp_path)
        derived, _ = derive_config_from_target(tmp_path)
        assert derived.generate_hooks is False

    def test_round_trip_renders_identical_sync_subset(self, tmp_path: Path) -> None:
        """Sync content from derived config matches sync content from original."""
        cfg = make_config(
            project_name="round-trip", domain="cosmology", token_tier="5x"
        )
        render_project(cfg, tmp_path)
        derived, _ = derive_config_from_target(tmp_path)
        # If derivation is correct, classifying sync content against the target
        # should mark every file as identical.
        new, conflicting, identical = classify_sync(derived, tmp_path)
        assert len(new) == 0
        assert len(conflicting) == 0
        assert len(identical) > 0

    def test_falls_back_to_dir_name(self, tmp_path: Path) -> None:
        """If PARALLAX.md heading is unparseable, derive project_name from dir."""
        # Plain PARALLAX.md (no canonical "Scientific Workflow Rules" heading)
        (tmp_path / "PARALLAX.md").write_text("# Custom heading\n")
        derived, warnings = derive_config_from_target(tmp_path)
        assert derived.project_name == tmp_path.name
        assert any("project_name" in w for w in warnings)

    def test_falls_back_to_research_domain(self, tmp_path: Path) -> None:
        (tmp_path / "PARALLAX.md").write_text("# unknown\n")
        derived, warnings = derive_config_from_target(tmp_path)
        assert derived.domain == "research"
        assert any("domain" in w.lower() for w in warnings)

    def test_extracts_custom_agent_description(self, tmp_path: Path) -> None:
        custom_text = (
            "---\nname: custom\ndescription: ...\n---\nThis is the custom agent body.\n"
        )
        (tmp_path / "PARALLAX.md").write_text(
            "# proj -- Scientific Workflow Rules\nDomain: x\n"
        )
        agents = tmp_path / ".claude" / "agents"
        agents.mkdir(parents=True)
        (agents / "custom.md").write_text(custom_text)
        derived, _ = derive_config_from_target(tmp_path)
        assert "This is the custom agent body" in derived.custom_agent_description
