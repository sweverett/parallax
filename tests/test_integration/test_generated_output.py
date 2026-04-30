"""Integration tests: validate parallax init generated output quality."""

from __future__ import annotations

import json

from parallax.core.renderer import render_project
from tests.conftest import make_config


class TestGeneratedOutput:
    def test_all_files_exist(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        result = render_project(make_config(), target)
        names = {p.relative_to(target).as_posix() for p in result.written}
        expected = {
            "CLAUDE.md",
            "PARALLAX.md",
            "CONSTITUTION.md",
            ".claude/settings.json",
            ".claude/hooks/test_guard.py",
            ".claude/hooks/lint_check.py",
            ".claude/hooks/stop_check.py",
            ".claude/skills/hypothesis/SKILL.md",
            ".claude/skills/handoff/SKILL.md",
            ".claude/skills/audit/SKILL.md",
            ".claude/skills/experiment/SKILL.md",
            ".claude/skills/session-start/SKILL.md",
            ".claude/skills/manuscript-review/SKILL.md",
            ".claude/skills/latex-guide/SKILL.md",
            ".claude/skills/grill-me/SKILL.md",
            ".claude/skills/test-integrity/SKILL.md",
            ".claude/skills/doc-sync/SKILL.md",
            ".claude/skills/diagnose/SKILL.md",
            ".claude/skills/zoom-out/SKILL.md",
            ".claude/skills/improve-architecture/SKILL.md",
            ".claude/skills/ubiquitous-language/SKILL.md",
            ".claude/agents/hypothesis-explorer.md",
            ".claude/agents/experiment-runner.md",
            ".claude/agents/literature-reviewer.md",
            ".claude/agents/result-validator.md",
            ".claude/agents/paper-writer.md",
            ".claude/agents/presentation-writer.md",
            ".claude/agents/manuscript-reviewer.md",
        }
        assert expected == names

    def test_no_unsubstituted_vars(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        for path in target.rglob("*"):
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                assert "${" not in content, f"Unsubstituted var in {path.name}"

    def test_settings_json_valid_json(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        settings_path = target / ".claude" / "settings.json"
        parsed = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" in parsed

    def test_settings_json_references_hooks(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        settings_path = target / ".claude" / "settings.json"
        parsed = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = parsed["hooks"]
        # Flatten all command strings from nested hooks structure
        commands: list[str] = []
        for hook_list in hooks.values():
            for entry in hook_list:
                for hook in entry["hooks"]:
                    commands.append(hook["command"])
        joined = " ".join(commands)
        assert ".claude/hooks/" in joined

    def test_hook_scripts_valid_python(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        hooks_dir = target / ".claude" / "hooks"
        for py_file in hooks_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            compile(source, py_file.name, "exec")

    def test_hook_scripts_have_main_guard(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        hooks_dir = target / ".claude" / "hooks"
        for py_file in hooks_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            assert "if __name__" in source, f"No __main__ guard in {py_file.name}"

    def test_skill_files_have_structure(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        skills_dir = target / ".claude" / "skills"
        for skill_file in skills_dir.glob("*/SKILL.md"):
            content = skill_file.read_text(encoding="utf-8")
            assert "When to Use" in content, (
                f"Missing 'When to Use' in {skill_file.name}"
            )
            assert "Rules" in content or "Protocol" in content, (
                f"Missing 'Rules'/'Protocol' in {skill_file.name}"
            )

    def test_core_docs_contain_project_name(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(project_name="myproject"), target)
        for name in ["CLAUDE.md", "PARALLAX.md", "CONSTITUTION.md"]:
            content = (target / name).read_text(encoding="utf-8")
            assert "myproject" in content, f"Project name missing from {name}"

    def test_agent_files_have_frontmatter(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        agents_dir = target / ".claude" / "agents"
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text(encoding="utf-8")
            assert content.startswith("---"), f"No frontmatter in {agent_file.name}"
            # Must have name, description, model fields
            assert "name:" in content, f"Missing name in {agent_file.name}"
            assert "description:" in content, (
                f"Missing description in {agent_file.name}"
            )
            assert "model:" in content, f"Missing model in {agent_file.name}"

    def test_manuscript_reviewer_frontmatter(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        content = (target / ".claude" / "agents" / "manuscript-reviewer.md").read_text()
        assert "skills: [manuscript-review]" in content
        assert "disallowedTools: [Edit, Write, NotebookEdit]" in content
        assert "tools: [Read, Glob, Grep, Bash]" in content

    def test_writer_agents_have_latex_guide(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        for name in ["paper-writer.md", "presentation-writer.md"]:
            content = (target / ".claude" / "agents" / name).read_text()
            assert "skills: [latex-guide]" in content, (
                f"Missing latex-guide skill in {name}"
            )

    def test_manuscript_review_skill_structure(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        content = (
            target / ".claude" / "skills" / "manuscript-review" / "SKILL.md"
        ).read_text()
        assert "disable-model-invocation: true" in content
        assert "memory:" not in content  # should NOT have memory
        assert "Paper Mode" in content
        assert "Presentation Mode" in content

    def test_latex_guide_skill_structure(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(), target)
        content = (
            target / ".claude" / "skills" / "latex-guide" / "SKILL.md"
        ).read_text()
        assert "disable-model-invocation" not in content  # auto-invocable
        assert "memory:" not in content
        assert "BibTeX" in content
        assert "Beamer" in content

    def test_agents_contain_project_name(self, tmp_path: object) -> None:
        from pathlib import Path

        target = Path(str(tmp_path))
        render_project(make_config(project_name="myproject", domain="genomics"), target)
        # literature-reviewer has domain substitution
        lit = (target / ".claude" / "agents" / "literature-reviewer.md").read_text()
        assert "genomics" in lit
