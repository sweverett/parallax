"""Structured interview for parallax init."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import cast

import typer

from parallax.core.config import (
    ProjectConfig,
    TestFramework,
    TokenTier,
)

# ---------------------------------------------------------------------------
# Sub-context strings shown during interview
# ---------------------------------------------------------------------------

_CTX_PROJECT_NAME = "Used in file headers and metadata for generated config files."
_CTX_SUMMARY = "One-line summary of your project. Becomes the tagline in CLAUDE.md."
_CTX_DOMAIN = (
    "Scientific domain (e.g., astrophysics, genomics, climate science). "
    "Frames CLAUDE.md and PARALLAX.md context."
)
_CTX_LANGUAGES = (
    "Primary programming language(s). Drives code conventions in CLAUDE.md."
)
_CTX_PACKAGE_MANAGER = "Shown in Tech Stack section of CLAUDE.md."
_CTX_TEST_FRAMEWORK = "Determines testing section in CLAUDE.md."
_CTX_USES_UNITS = (
    "If yes, CLAUDE.md will include a mandatory dimensional analysis rule -- "
    "Claude must verify unit consistency before finalizing any code "
    "involving physical quantities."
)
_CTX_USES_JAX = (
    "If yes, PARALLAX.md will include JAX-specific rules: "
    "pure functions, explicit RNG threading, pytree-compatible structures."
)
_CTX_BRANCH_PREFIX = (
    "Git branch prefix for your project (e.g., 'se/'). "
    "Added to CLAUDE.md git workflow section. Leave blank to skip."
)
_CTX_GENERATE_SKILLS = (
    "Creates .claude/skills/ with 4 prescriptive skills: "
    "/hypothesis, /handoff, /audit, /experiment."
)
_CTX_GENERATE_HOOKS = (
    "Creates .claude/settings.json with baseline hook structure "
    "(test protection, lint/format reminders)."
)
_CTX_TOKEN_TIER = (
    "Controls default model selection for generated agents.\n"
    "  pro  -- conservative: haiku exploration, sonnet validation\n"
    "  5x   -- balanced: sonnet exploration, opus validation\n"
    "  20x  -- generous: opus for most tasks\n"
    "  api  -- unconstrained: opus everywhere"
)
_CTX_DETAILED_GATE = (
    "Optional: provide detailed project context via your editor. "
    "Populates additional CLAUDE.md sections."
)
_CTX_EDITOR = "Editor to use for multi-line input. Defaults to $EDITOR or 'vim'."

# ---------------------------------------------------------------------------
# Editor-based input
# ---------------------------------------------------------------------------


_PHASE_B_TEMPLATE = """\
<!-- Parallax project context — fill in the sections below.
     Delete or leave empty any sections you want to skip.
     Lines inside <!-- --> comments are instructions and will be stripped. -->

## Science Requirements
<!-- What is this project trying to achieve scientifically?
     Describe objectives, key phenomena, methods. -->


## Preferred Patterns
<!-- What should Claude favor? Coding style, error handling,
     documentation level, testing philosophy. -->


## Outlawed Patterns
<!-- What must Claude avoid? Anti-patterns, forbidden libraries,
     unacceptable shortcuts. -->


## Key Libraries
<!-- Important packages, their roles, and gotchas.
     Include bespoke/internal libraries Claude might not know about. -->


## Custom Agent
<!-- Optional: define a project-specific agent beyond the core ones
     (hypothesis-explorer, experiment-runner, literature-reviewer,
      result-validator, paper-writer, presentation-writer).
     Describe its purpose and what it should do.
     Example: "data-pipeline-validator -- checks ETL outputs for
     schema drift and NaN propagation" -->

"""

# Section keys in template order, mapping heading -> config field name
_PHASE_B_SECTIONS: list[tuple[str, str]] = [
    ("Science Requirements", "science_requirements"),
    ("Preferred Patterns", "preferred_patterns"),
    ("Outlawed Patterns", "outlawed_patterns"),
    ("Key Libraries", "key_libraries"),
    ("Custom Agent", "custom_agent_description"),
]


def _strip_html_comments(text: str) -> str:
    """Remove <!-- ... --> blocks from text."""
    import re

    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _parse_phase_b(text: str) -> dict[str, str]:
    """Parse editor output into field dict keyed by config field name."""
    import re

    results: dict[str, str] = {}
    # Split on ## headings
    heading_re = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    heading_to_field = {h: f for h, f in _PHASE_B_SECTIONS}

    parts = heading_re.split(text)
    # parts = [preamble, heading1, body1, heading2, body2, ...]
    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        body = parts[i + 1]
        field = heading_to_field.get(heading)
        if field is not None:
            cleaned = _strip_html_comments(body).strip()
            results[field] = cleaned
        i += 2

    # Fill missing fields with empty string
    for _, field in _PHASE_B_SECTIONS:
        if field not in results:
            results[field] = ""
    return results


def _open_phase_b_editor(editor: str) -> dict[str, str]:
    """Open a single editor with all Phase B sections. Returns parsed fields."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix="parallax_project_context_",
        delete=False,
    ) as f:
        f.write(_PHASE_B_TEMPLATE)
        tmppath = f.name

    try:
        subprocess.run([editor, tmppath], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        typer.echo(
            f"  Warning: editor '{editor}' failed ({exc}). "
            "Falling back to single-line input."
        )
        os.unlink(tmppath)
        return _phase_b_fallback_prompts()

    try:
        text = Path(tmppath).read_text(encoding="utf-8")
    finally:
        os.unlink(tmppath)
    return _parse_phase_b(text)


def _phase_b_fallback_prompts() -> dict[str, str]:
    """Fallback: prompt each field on a single line if editor fails."""
    results: dict[str, str] = {}
    prompts = [
        ("science_requirements", "Science requirements (single line)"),
        ("preferred_patterns", "Preferred patterns (single line)"),
        ("outlawed_patterns", "Outlawed patterns (single line)"),
        ("key_libraries", "Key libraries (single line)"),
        ("custom_agent_description", "Custom agent description (single line)"),
    ]
    for field, label in prompts:
        val: str = typer.prompt(f"  {label}", default="")
        results[field] = val.strip()
    return results


# ---------------------------------------------------------------------------
# Individual question functions
# ---------------------------------------------------------------------------


def _ask_text(
    label: str,
    context: str,
    default: str = "",
    *,
    required: bool = False,
) -> str:
    typer.echo(f"\n  {context}")
    if required:
        while True:
            val: str = typer.prompt(f"  {label}", default=default or "")
            if val.strip():
                return val.strip()
            typer.echo("  (required)")
    else:
        val = typer.prompt(f"  {label}", default=default)
        return val.strip()


def _ask_bool(label: str, context: str, *, default: bool = False) -> bool:
    typer.echo(f"\n  {context}")
    return typer.confirm(f"  {label}", default=default)


def _ask_choice(
    label: str,
    context: str,
    choices: list[str],
    default: str,
) -> str:
    typer.echo(f"\n  {context}")
    choices_str = "/".join(choices)
    lower_to_canonical = {c.lower(): c for c in choices}
    while True:
        val: str = typer.prompt(
            f"  {label} [{choices_str}]",
            default=default,
        )
        canonical = lower_to_canonical.get(val.strip().lower())
        if canonical is not None:
            return canonical
        typer.echo(f"  Invalid choice. Must be one of: {', '.join(choices)}")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_interview(
    *,
    yes: bool = False,
    token_tier_override: str | None = None,
    target: Path | None = None,
) -> ProjectConfig:
    """Run the structured interview, returning a ProjectConfig.

    If yes=True, skip questions with defaults. Still prompt required fields.
    token_tier_override: if set from CLI flag, skip the token tier question.
    target: if set, use its name as default project name instead of cwd.
    """
    typer.echo("Parallax project initialization\n")

    # Detect dirname for default project name
    default_name = target.name if target is not None else Path.cwd().name

    # Phase A: core questions
    if yes:
        project_name = default_name
    else:
        project_name = _ask_text(
            "Project name", _CTX_PROJECT_NAME, default=default_name
        )

    summary = _ask_text("One-line summary", _CTX_SUMMARY, required=True)
    domain = _ask_text("Scientific domain", _CTX_DOMAIN, required=True)

    if yes:
        languages = "Python"
        package_manager = "conda"
        test_framework: TestFramework = "pytest"
        uses_units = False
        uses_jax = False
        branch_prefix = ""
        generate_skills = True
        generate_hooks = True
        token_tier: TokenTier = "pro"
    else:
        languages = _ask_text("Primary language(s)", _CTX_LANGUAGES, default="Python")
        package_manager = _ask_text(
            "Package manager", _CTX_PACKAGE_MANAGER, default="conda"
        )
        test_framework = cast(
            "TestFramework",
            _ask_choice(
                "Test framework",
                _CTX_TEST_FRAMEWORK,
                ["pytest", "unittest", "nose2"],
                default="pytest",
            ),
        )
        uses_units = _ask_bool("Uses physical units?", _CTX_USES_UNITS)
        uses_jax = _ask_bool("Uses JAX/differentiable computing?", _CTX_USES_JAX)
        branch_prefix = _ask_text("Git branch prefix", _CTX_BRANCH_PREFIX)
        generate_skills = _ask_bool(
            "Generate Claude Code skills?",
            _CTX_GENERATE_SKILLS,
            default=True,
        )
        generate_hooks = _ask_bool(
            "Generate Claude Code hooks?",
            _CTX_GENERATE_HOOKS,
            default=True,
        )
        token_tier = cast(
            "TokenTier",
            _ask_choice(
                "Token usage tier",
                _CTX_TOKEN_TIER,
                ["pro", "5x", "20x", "api"],
                default="pro",
            ),
        )

    # CLI flag override
    if token_tier_override is not None:
        token_tier = cast("TokenTier", token_tier_override)

    # Phase B gate
    editor = ""
    science_requirements = ""
    preferred_patterns = ""
    outlawed_patterns = ""
    key_libraries = ""
    custom_agent_description = ""

    if not yes:
        add_detailed = _ask_bool(
            "Add detailed project context?",
            _CTX_DETAILED_GATE,
        )
        if add_detailed:
            default_editor = os.environ.get("EDITOR", "vim")
            editor = _ask_text("Preferred editor", _CTX_EDITOR, default=default_editor)

            phase_b = _open_phase_b_editor(editor)
            science_requirements = phase_b["science_requirements"]
            preferred_patterns = phase_b["preferred_patterns"]
            outlawed_patterns = phase_b["outlawed_patterns"]
            key_libraries = phase_b["key_libraries"]
            custom_agent_description = phase_b["custom_agent_description"]

    return ProjectConfig(
        project_name=project_name,
        summary=summary,
        domain=domain,
        languages=languages,
        package_manager=package_manager,
        test_framework=test_framework,
        uses_units=uses_units,
        uses_jax=uses_jax,
        branch_prefix=branch_prefix,
        generate_skills=generate_skills,
        generate_hooks=generate_hooks,
        token_tier=token_tier,
        editor=editor,
        science_requirements=science_requirements,
        preferred_patterns=preferred_patterns,
        outlawed_patterns=outlawed_patterns,
        key_libraries=key_libraries,
        custom_agent_description=custom_agent_description,
    )
