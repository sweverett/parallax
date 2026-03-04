"""Render ProjectConfig into output files via string.Template."""

from __future__ import annotations

import importlib.resources
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parallax.core.config import ProjectConfig, TokenTier


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MergeResult:
    """Outcome of render_project: categorises written files."""

    written: list[Path] = field(default_factory=list)
    suffixed: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------

_TEMPLATES = importlib.resources.files("parallax.templates")
_SKILL_TEMPLATES = importlib.resources.files("parallax.templates.skills")
_HOOK_TEMPLATES = importlib.resources.files("parallax.templates.hooks")
_AGENT_TEMPLATES = importlib.resources.files("parallax.templates.agents")


def _load_template(name: str) -> Template:
    ref = _TEMPLATES.joinpath(name)
    return Template(ref.read_text(encoding="utf-8"))


def _load_skill_template(name: str) -> str:
    ref = _SKILL_TEMPLATES.joinpath(f"{name}.md")
    return ref.read_text(encoding="utf-8")


def _load_hook_script(name: str) -> str:
    ref = _HOOK_TEMPLATES.joinpath(name)
    return ref.read_text(encoding="utf-8")


def _load_agent_template(name: str) -> str:
    ref = _AGENT_TEMPLATES.joinpath(f"{name}.md")
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
# Agent rendering
# ---------------------------------------------------------------------------

# Model selection per (agent, token_tier).
# Rows: agent template names. Columns: pro, 5x, 20x, api.
_MODEL_MAP: dict[str, dict[str, str]] = {
    "hypothesis_explorer": {
        "pro": "haiku",
        "5x": "opus",
        "20x": "opus",
        "api": "opus",
    },
    "experiment_runner": {
        "pro": "sonnet",
        "5x": "sonnet",
        "20x": "opus",
        "api": "opus",
    },
    "literature_reviewer": {
        "pro": "haiku",
        "5x": "sonnet",
        "20x": "opus",
        "api": "opus",
    },
    "result_validator": {
        "pro": "sonnet",
        "5x": "opus",
        "20x": "opus",
        "api": "opus",
    },
    "paper_writer": {
        "pro": "sonnet",
        "5x": "opus",
        "20x": "opus",
        "api": "opus",
    },
    "presentation_writer": {
        "pro": "sonnet",
        "5x": "opus",
        "20x": "opus",
        "api": "opus",
    },
    "manuscript_reviewer": {
        "pro": "sonnet",
        "5x": "opus",
        "20x": "opus",
        "api": "opus",
    },
}

# Template var name -> agent template name mapping
_AGENT_MODEL_VARS: dict[str, str] = {
    "hypothesis_explorer": "explorer_model",
    "experiment_runner": "runner_model",
    "literature_reviewer": "reviewer_model",
    "result_validator": "validator_model",
    "paper_writer": "writer_model",
    "presentation_writer": "presenter_model",
    "manuscript_reviewer": "reviewer_writing_model",
}

_AGENT_NAMES = [
    "hypothesis_explorer",
    "experiment_runner",
    "literature_reviewer",
    "result_validator",
    "paper_writer",
    "presentation_writer",
    "manuscript_reviewer",
]


def _agent_output_name(template_name: str) -> str:
    """Convert template name (underscores) to output name (hyphens)."""
    return template_name.replace("_", "-") + ".md"


def model_for_agent(agent_name: str, tier: TokenTier) -> str:
    """Look up the model string for a given agent and token tier."""
    agent_models = _MODEL_MAP.get(agent_name)
    if agent_models is None:
        msg = f"Unknown agent {agent_name!r}"
        raise ValueError(msg)
    model = agent_models.get(tier)
    if model is None:
        msg = f"Unknown token tier {tier!r}"
        raise ValueError(msg)
    return model


def render_agent(name: str, config: ProjectConfig) -> str:
    """Render an agent template with model and project substitutions."""
    raw = _load_agent_template(name)
    model_var = _AGENT_MODEL_VARS[name]
    model = model_for_agent(name, config.token_tier)
    return Template(raw).safe_substitute(
        **{model_var: model},
        project_name=config.project_name,
        domain=config.domain,
    )


_CUSTOM_AGENT_TEMPLATE = """\
---
name: custom
description: Custom project-specific agent for ${project_name}.
model: sonnet
tools: [Read, Glob, Grep, Edit, Write, Bash]
---
${custom_agent_description}
"""


def _has_custom_agent(config: ProjectConfig) -> bool:
    """True if custom_agent_description has content beyond # comment lines."""
    return any(
        line.strip() and not line.strip().startswith("#")
        for line in config.custom_agent_description.strip().splitlines()
    )


def render_custom_agent(config: ProjectConfig) -> str:
    """Render a custom agent from user description."""
    return Template(_CUSTOM_AGENT_TEMPLATE).safe_substitute(
        project_name=config.project_name,
        custom_agent_description=config.custom_agent_description.strip(),
    )


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

_SKILL_NAMES = [
    "hypothesis",
    "handoff",
    "audit",
    "experiment",
    "session_start",
    "manuscript_review",
    "latex_guide",
]
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
            # session_start uses hyphen in output dir name
            out_name = s.replace("_", "-") if "_" in s else s
            paths.append(target / ".claude" / "skills" / out_name / "SKILL.md")
        # Agents are generated alongside skills
        for a in _AGENT_NAMES:
            paths.append(target / ".claude" / "agents" / _agent_output_name(a))
        if _has_custom_agent(config):
            paths.append(target / ".claude" / "agents" / "custom.md")
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
# Content rendering (pure — no I/O)
# ---------------------------------------------------------------------------


def _render_all_content(config: ProjectConfig) -> dict[str, str]:
    """Render all output content keyed by relative path string. Pure function."""
    files: dict[str, str] = {
        "CLAUDE.md": render_claude_md(config),
        "PARALLAX.md": render_parallax_md(config),
        "CONSTITUTION.md": render_constitution_md(config),
    }

    if config.generate_hooks:
        files[".claude/settings.json"] = render_settings_json(config)
        for hook_name in _HOOK_NAMES:
            files[f".claude/hooks/{hook_name}"] = _load_hook_script(hook_name)

    if config.generate_skills:
        for skill_name in _SKILL_NAMES:
            out_name = skill_name.replace("_", "-") if "_" in skill_name else skill_name
            files[f".claude/skills/{out_name}/SKILL.md"] = render_skill(
                skill_name, config
            )
        for agent_name in _AGENT_NAMES:
            out_file = f".claude/agents/{_agent_output_name(agent_name)}"
            files[out_file] = render_agent(agent_name, config)
        if _has_custom_agent(config):
            files[".claude/agents/custom.md"] = render_custom_agent(config)

    return files


# ---------------------------------------------------------------------------
# Suffix / classify infrastructure (merge mode)
# ---------------------------------------------------------------------------


def _suffix_path(path: Path) -> Path:
    """Insert `.parallax` before the file extension.

    CLAUDE.md -> CLAUDE.parallax.md
    test_guard.py -> test_guard.parallax.py
    settings.json -> settings.parallax.json
    """
    return path.with_suffix(f".parallax{path.suffix}")


def classify_outputs(
    config: ProjectConfig,
    target: Path,
) -> tuple[dict[str, str], dict[str, str], list[str]]:
    """Render all content and classify against existing target files.

    Returns (new, conflicting, identical):
      - new: {rel_path: content} — files that don't exist in target
      - conflicting: {rel_path: content} — files that exist and differ
      - identical: [rel_path, ...] — files that exist and match
    """
    all_content = _render_all_content(config)
    new: dict[str, str] = {}
    conflicting: dict[str, str] = {}
    identical: list[str] = []

    for rel_path, content in all_content.items():
        existing = target / rel_path
        if not existing.exists():
            new[rel_path] = content
        elif existing.read_text(encoding="utf-8") == content:
            identical.append(rel_path)
        else:
            conflicting[rel_path] = content

    return new, conflicting, identical


# ---------------------------------------------------------------------------
# Merge guide
# ---------------------------------------------------------------------------


def _write_merge_guide(
    target: Path,
    result: MergeResult,
    *,
    new_paths: list[str] | None = None,
    identical_paths: list[str] | None = None,
) -> Path:
    """Write .parallax/merge-guide.md describing the merge state."""
    guide_dir = target / ".parallax"
    guide_dir.mkdir(parents=True, exist_ok=True)
    guide_path = guide_dir / "merge-guide.md"

    lines = [
        "# Parallax Merge Guide\n",
        "\n",
        "Parallax was initialized into a repo with existing configuration.\n",
        "Your existing files were **not modified**. Parallax versions were written\n",
        "with a `.parallax` suffix alongside originals that differ.\n",
        "\n",
    ]

    if result.suffixed:
        lines.append("## Files to merge\n\n")
        lines.append(
            "Each `.parallax` file is Parallax's generated version. "
            "Merge its content into the original, then delete it.\n\n"
        )
        for sf in sorted(result.suffixed):
            rel = sf.relative_to(target)
            # Derive original path by stripping .parallax from stem
            orig = rel.parent / rel.name.replace(".parallax", "")
            lines.append(f"- `{orig}` <-- `{rel}`\n")
        lines.append("\n")

    if new_paths:
        lines.append("## New files (no merge needed)\n\n")
        for np in sorted(new_paths):
            lines.append(f"- `{np}`\n")
        lines.append("\n")

    if identical_paths:
        lines.append("## Identical files (skipped)\n\n")
        for ip in sorted(identical_paths):
            lines.append(f"- `{ip}`\n")
        lines.append("\n")

    lines.append("## How to complete the merge\n\n")
    lines.append("Option A: Run `parallax refine` to launch a Claude session ")
    lines.append("that reads this guide and assists with merging.\n\n")
    lines.append("Option B: Manually merge each pair listed above, then delete ")
    lines.append("the `.parallax` files.\n\n")
    lines.append("When done, delete the `.parallax/` directory.\n")

    guide_path.write_text("".join(lines), encoding="utf-8")
    return guide_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def render_project(
    config: ProjectConfig,
    target: Path,
    *,
    force: bool = False,
    merge: bool = False,
) -> MergeResult:
    """Render all output files atomically. Returns MergeResult.

    merge=False (default): standard fresh-init. Raises FileExistsError on conflicts.
    merge=True: writes new files normally, conflicting files with .parallax suffix,
                skips identical files. Writes .parallax/merge-guide.md.
    """
    if merge:
        return _render_merge(config, target)

    # --- Standard (non-merge) path ---

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

    all_content = _render_all_content(config)

    # Render to temp dir, then move atomically
    written: list[Path] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Write all to temp
        for rel_path, content in all_content.items():
            tmp_file = tmp / rel_path
            tmp_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file.write_text(content, encoding="utf-8")

        # Move to target
        for rel_path in all_content:
            tmp_file = tmp / rel_path
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(tmp_file), str(dest))
            except OSError as exc:
                succeeded = [str(p.relative_to(target)) for p in written]
                msg = f"Failed to write {rel_path}. Files already written: {succeeded}"
                raise OSError(msg) from exc
            written.append(dest)

    return MergeResult(written=written)


def _render_merge(config: ProjectConfig, target: Path) -> MergeResult:
    """Merge-mode rendering: suffix conflicts, skip identical."""
    new_content, conflicting_content, identical = classify_outputs(config, target)

    written: list[Path] = []
    suffixed: list[Path] = []
    skipped = [target / ip for ip in identical]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Stage new files
        for rel_path, content in new_content.items():
            tmp_file = tmp / rel_path
            tmp_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file.write_text(content, encoding="utf-8")

        # Stage conflicting files with suffix
        for rel_path, content in conflicting_content.items():
            suf = _suffix_path(Path(rel_path))
            tmp_file = tmp / str(suf)
            tmp_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file.write_text(content, encoding="utf-8")

        # Move new files to target
        for rel_path in new_content:
            tmp_file = tmp / rel_path
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp_file), str(dest))
            written.append(dest)

        # Move suffixed files to target
        for rel_path in conflicting_content:
            suf = _suffix_path(Path(rel_path))
            tmp_file = tmp / str(suf)
            dest = target / str(suf)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp_file), str(dest))
            suffixed.append(dest)

    result = MergeResult(written=written, suffixed=suffixed, skipped=skipped)

    # Write merge guide if there are suffixed files
    if suffixed:
        _write_merge_guide(
            target,
            result,
            new_paths=[str(p.relative_to(target)) for p in written],
            identical_paths=identical,
        )

    return result
