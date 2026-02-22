"""Render ProjectConfig into output files via string.Template."""

from __future__ import annotations

import importlib.resources
import shutil
import tempfile
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parallax.core.config import ProjectConfig

# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------

_TEMPLATES = importlib.resources.files("parallax.templates")
_SKILL_TEMPLATES = importlib.resources.files("parallax.templates.skills")
_HOOK_TEMPLATES = importlib.resources.files("parallax.templates.hooks")


def _load_template(name: str) -> Template:
    ref = _TEMPLATES.joinpath(name)
    return Template(ref.read_text(encoding="utf-8"))


def _load_skill_template(name: str) -> str:
    ref = _SKILL_TEMPLATES.joinpath(name)
    return ref.read_text(encoding="utf-8")


def _load_hook_script(name: str) -> str:
    ref = _HOOK_TEMPLATES.joinpath(name)
    return ref.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Section builders (conditional sections assembled before substitution)
# ---------------------------------------------------------------------------


def _science_requirements_section(config: ProjectConfig) -> str:
    if not config.science_requirements:
        return ""
    return (
        "\n## Science Requirements & Goals\n\n"
        + config.science_requirements.strip()
        + "\n\n"
    )


def _preferred_patterns_section(config: ProjectConfig) -> str:
    if not config.preferred_patterns:
        return ""
    return (
        "\n## Preferred Patterns & Behaviors\n\n"
        + config.preferred_patterns.strip()
        + "\n\n"
    )


def _outlawed_patterns_section(config: ProjectConfig) -> str:
    if not config.outlawed_patterns:
        return ""
    return (
        "\n## Outlawed Patterns & Behaviors\n\n"
        + config.outlawed_patterns.strip()
        + "\n\n"
    )


def _key_libraries_section(config: ProjectConfig) -> str:
    if not config.key_libraries:
        return ""
    return "\n## Key Libraries & Tools\n\n" + config.key_libraries.strip() + "\n\n"


def _units_rule(config: ProjectConfig) -> str:
    if not config.uses_units:
        return ""
    return (
        "- **Dimensional analysis is mandatory.** "
        "Verify unit consistency before finalizing any code "
        "involving physical quantities.\n"
    )


def _git_section(config: ProjectConfig) -> str:
    if not config.branch_prefix:
        return ""
    return (
        "\n## Git Workflow\n\n"
        f"- Branch prefix: `{config.branch_prefix}` "
        f"(e.g., `{config.branch_prefix}add-feature`)\n"
        "- Concise commit messages\n\n"
    )


def _jax_section(config: ProjectConfig) -> str:
    if not config.uses_jax:
        return ""
    return (
        "\n## JAX / Differentiable Computing Rules\n\n"
        "- Pure functions: no side effects inside jitted code\n"
        "- Explicit RNG key threading (never use global state)\n"
        "- Use pytree-compatible data structures\n"
        "- Avoid Python control flow over traced values "
        "(use jax.lax.cond, jax.lax.scan, etc.)\n"
        "- Shape/dtype annotations on all array-producing functions\n"
    )


# ---------------------------------------------------------------------------
# Per-file renderers
# ---------------------------------------------------------------------------


def render_claude_md(config: ProjectConfig) -> str:
    """Render CLAUDE.md content from config."""
    tpl = _load_template("claude_md.tpl")
    return tpl.safe_substitute(
        project_name=config.project_name,
        summary=config.summary,
        domain=config.domain,
        languages=config.languages,
        package_manager=config.package_manager,
        test_framework=config.test_framework,
        science_requirements_section=_science_requirements_section(config),
        preferred_patterns_section=_preferred_patterns_section(config),
        outlawed_patterns_section=_outlawed_patterns_section(config),
        key_libraries_section=_key_libraries_section(config),
        units_rule=_units_rule(config),
        git_section=_git_section(config),
    )


def render_parallax_md(config: ProjectConfig) -> str:
    """Render PARALLAX.md content from config."""
    tpl = _load_template("parallax_md.tpl")
    return tpl.safe_substitute(
        project_name=config.project_name,
        domain=config.domain,
        jax_section=_jax_section(config),
    )


def render_constitution_md(config: ProjectConfig) -> str:
    """Render CONSTITUTION.md content from config."""
    tpl = _load_template("constitution_md.tpl")
    return tpl.safe_substitute(project_name=config.project_name)


def render_settings_json(config: ProjectConfig) -> str:
    """Render .claude/settings.json content from config."""
    ref = _TEMPLATES.joinpath("settings.json.tpl")
    return ref.read_text(encoding="utf-8")


def render_skill(name: str, config: ProjectConfig) -> str:
    """Render a skill template, substituting project_name."""
    raw = _load_skill_template(name)
    return Template(raw).safe_substitute(project_name=config.project_name)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

_SKILL_NAMES = ["hypothesis.md", "handoff.md", "audit.md", "experiment.md"]
_HOOK_NAMES = ["test_guard.py", "lint_check.py", "stop_check.py"]


def _output_paths(
    config: ProjectConfig,
    target: Path,
) -> list[Path]:
    """All files that render_project would create."""
    paths = [
        target / "CLAUDE.md",
        target / "PARALLAX.md",
        target / "CONSTITUTION.md",
    ]
    if config.generate_hooks:
        paths.append(target / ".claude" / "settings.json")
        for h in _HOOK_NAMES:
            paths.append(target / ".claude" / "hooks" / h)
    if config.generate_skills:
        for s in _SKILL_NAMES:
            paths.append(target / ".claude" / "skills" / s)
    return paths


def check_conflicts(
    config: ProjectConfig,
    target: Path,
    *,
    force: bool,
) -> list[Path]:
    """Return list of conflicting paths. Empty if none or force=True."""
    if force:
        return []
    return [p for p in _output_paths(config, target) if p.exists()]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def render_project(
    config: ProjectConfig,
    target: Path,
    *,
    force: bool = False,
) -> list[Path]:
    """Render all output files atomically. Returns list of written paths.

    Raises FileExistsError if conflicts detected and force=False.
    """
    # Check for already-initialized project
    parallax_md = target / "PARALLAX.md"
    if parallax_md.exists() and not force:
        msg = "This project is already Parallax-managed. Use `-f` to reinitialize."
        raise FileExistsError(msg)

    # Check generic conflicts
    conflicts = check_conflicts(config, target, force=force)
    if conflicts:
        names = ", ".join(str(c.relative_to(target)) for c in conflicts)
        msg = f"Files already exist: {names}. Use `-f` to overwrite."
        raise FileExistsError(msg)

    # Render to temp dir, then move atomically
    written: list[Path] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Core files
        files: dict[Path, str] = {
            tmp / "CLAUDE.md": render_claude_md(config),
            tmp / "PARALLAX.md": render_parallax_md(config),
            tmp / "CONSTITUTION.md": render_constitution_md(config),
        }

        # Hooks
        if config.generate_hooks:
            claude_dir = tmp / ".claude"
            claude_dir.mkdir(parents=True, exist_ok=True)
            files[claude_dir / "settings.json"] = render_settings_json(config)
            hooks_dir = claude_dir / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            for hook_name in _HOOK_NAMES:
                files[hooks_dir / hook_name] = _load_hook_script(hook_name)

        # Skills
        if config.generate_skills:
            skills_dir = tmp / ".claude" / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            for skill_name in _SKILL_NAMES:
                files[skills_dir / skill_name] = render_skill(skill_name, config)

        # Write all to temp
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        # Move to target
        for tmp_path in files:
            rel = tmp_path.relative_to(tmp)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(tmp_path), str(dest))
            except OSError as exc:
                succeeded = [str(p.relative_to(target)) for p in written]
                msg = f"Failed to write {rel}. Files already written: {succeeded}"
                raise OSError(msg) from exc
            written.append(dest)

    return written
