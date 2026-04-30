"""Integration tests for parallax sync command."""

from pathlib import Path

from typer.testing import CliRunner

from parallax.cli import _CONFIG_REL, app
from parallax.core.config import ProjectConfig
from parallax.core.renderer import (
    render_constitution_md,
    render_project,
)

runner = CliRunner()


def _dummy_config(**overrides: object) -> ProjectConfig:
    defaults: dict[str, object] = {
        "project_name": "sync-test",
        "summary": "A sync test project",
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


def _seed_initialized(
    tmp_path: Path, cfg: ProjectConfig | None = None
) -> ProjectConfig:
    """Render a full project tree and persist the config snapshot.

    Mirrors the post-init state that `parallax sync` expects to operate on.
    """
    cfg = cfg or _dummy_config()
    render_project(cfg, tmp_path)
    cfg.to_json(tmp_path / _CONFIG_REL)
    return cfg


class TestSyncPreflight:
    def test_requires_parallax_md(self, tmp_path: Path) -> None:
        # No PARALLAX.md: not a Parallax-managed project
        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 1
        assert "not a Parallax-managed project" in result.output

    def test_requires_config_json(self, tmp_path: Path) -> None:
        # PARALLAX.md exists but no config snapshot (legacy project)
        (tmp_path / "PARALLAX.md").write_text("# legacy")
        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 1
        assert "config.json" in result.output
        assert "parallax init -f" in result.output


class TestSyncBehavior:
    def test_clean_sync_is_noop(self, tmp_path: Path) -> None:
        """Newly-initialized project: every file matches template, sync skips all."""
        _seed_initialized(tmp_path)
        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 0
        assert "identical file(s) skipped" in result.output
        # No suffixed files anywhere
        assert not list(tmp_path.rglob("*.parallax.*"))

    def test_writes_new_skill_when_added(self, tmp_path: Path) -> None:
        """If a skill is missing in the target, sync writes it."""
        cfg = _seed_initialized(tmp_path)
        # Simulate "skill removed locally": user deleted it; sync should restore.
        skill_dir = tmp_path / ".claude" / "skills" / "diagnose"
        for f in skill_dir.glob("*"):
            f.unlink()
        skill_dir.rmdir()
        assert not skill_dir.exists()

        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 0
        assert (skill_dir / "SKILL.md").exists()
        assert "new file(s)" in result.output
        # Sanity: original config still intact
        loaded = ProjectConfig.from_json(tmp_path / _CONFIG_REL)
        assert loaded.project_name == cfg.project_name

    def test_suffixes_user_edited_skill(self, tmp_path: Path) -> None:
        _seed_initialized(tmp_path)
        skill = tmp_path / ".claude" / "skills" / "hypothesis" / "SKILL.md"
        original = skill.read_text()
        skill.write_text(original + "\n\n## My customizations\nlocal edits here\n")

        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 0
        # Original kept verbatim
        assert "local edits here" in skill.read_text()
        # Template version landed alongside with .parallax suffix
        assert (
            tmp_path / ".claude" / "skills" / "hypothesis" / "SKILL.parallax.md"
        ).exists()
        # Merge guide written
        assert (tmp_path / ".parallax" / "merge-guide.md").exists()
        assert "parallax refine" in result.output

    def test_does_not_touch_claude_md(self, tmp_path: Path) -> None:
        _seed_initialized(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        # Edit CLAUDE.md after init — sync must never touch it
        claude_md.write_text("# user-customized CLAUDE.md\n")

        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 0
        assert claude_md.read_text() == "# user-customized CLAUDE.md\n"
        # No CLAUDE.parallax.md should ever be created
        assert not (tmp_path / "CLAUDE.parallax.md").exists()

    def test_does_not_touch_parallax_md(self, tmp_path: Path) -> None:
        _seed_initialized(tmp_path)
        parallax_md = tmp_path / "PARALLAX.md"
        parallax_md.write_text("# user-customized PARALLAX.md\n")

        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 0
        assert parallax_md.read_text() == "# user-customized PARALLAX.md\n"
        assert not (tmp_path / "PARALLAX.parallax.md").exists()

    def test_constitution_md_is_synced(self, tmp_path: Path) -> None:
        """Edited CONSTITUTION.md should be suffixed (in sync subset)."""
        cfg = _seed_initialized(tmp_path)
        constitution = tmp_path / "CONSTITUTION.md"
        original_template = render_constitution_md(cfg)
        # Replace with an edit the user made
        constitution.write_text(original_template + "\n\n## My addition\n")

        result = runner.invoke(app, ["sync", "-t", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "CONSTITUTION.parallax.md").exists()
        # Original kept
        assert "My addition" in constitution.read_text()


class TestSyncDryRun:
    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        _seed_initialized(tmp_path)
        skill = tmp_path / ".claude" / "skills" / "hypothesis" / "SKILL.md"
        skill.write_text(skill.read_text() + "\n## edits\n")

        result = runner.invoke(app, ["sync", "-t", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "dry-run" in result.output
        # Nothing actually written
        assert not (
            tmp_path / ".claude" / "skills" / "hypothesis" / "SKILL.parallax.md"
        ).exists()
        assert not (tmp_path / ".parallax" / "merge-guide.md").exists()

    def test_dry_run_summary_counts(self, tmp_path: Path) -> None:
        _seed_initialized(tmp_path)
        # One conflict
        skill = tmp_path / ".claude" / "skills" / "hypothesis" / "SKILL.md"
        skill.write_text(skill.read_text() + "\n## edits\n")
        # One missing -> would be new
        improve_dir = tmp_path / ".claude" / "skills" / "improve-architecture"
        for f in improve_dir.glob("*"):
            f.unlink()
        improve_dir.rmdir()

        result = runner.invoke(app, ["sync", "-t", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "1 new" in result.output
        assert "1 updated" in result.output
