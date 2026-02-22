"""Structured interview for parallax init."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import cast

import typer

from parallax.core.config import PackageManager, ProjectConfig, TestFramework

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
_CTX_PACKAGE_MANAGER = (
    "Determines dev commands section in CLAUDE.md (e.g., pixi run test)."
)
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
_CTX_DETAILED_GATE = (
    "Optional: provide detailed project context via your editor. "
    "Populates additional CLAUDE.md sections."
)
_CTX_EDITOR = "Editor to use for multi-line input. Defaults to $EDITOR or 'vim'."
_CTX_SCIENCE_REQUIREMENTS = (
    "What is this project trying to achieve scientifically? "
    "Describe objectives, key phenomena, methods. "
    "Becomes a CLAUDE.md section. Leave blank to skip."
)
_CTX_PREFERRED_PATTERNS = (
    "What should Claude favor? Coding style, error handling, "
    "documentation level, testing philosophy. Leave blank to skip."
)
_CTX_OUTLAWED_PATTERNS = (
    "What must Claude avoid? Anti-patterns, forbidden libraries, "
    "unacceptable shortcuts. Leave blank to skip."
)
_CTX_KEY_LIBRARIES = (
    "List important packages, their roles, and gotchas. "
    "Include bespoke/internal libraries Claude might not know about. "
    "Leave blank to skip."
)

# ---------------------------------------------------------------------------
# Editor-based input
# ---------------------------------------------------------------------------


def _open_editor(editor: str, prompt_label: str) -> str:
    """Open editor for multi-line input. Falls back to single-line prompt."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix=f"parallax_{prompt_label}_",
        delete=False,
    ) as f:
        f.write(
            f"# {prompt_label}\n# Lines starting with # are kept.\n# "
            "Save and close editor when done. Empty file = skip.\n"
        )
        tmppath = f.name

    try:
        subprocess.run(
            [editor, tmppath],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        typer.echo(
            f"  Warning: editor '{editor}' failed ({exc}). "
            "Falling back to single-line input."
        )
        os.unlink(tmppath)
        result: str = typer.prompt(f"  {prompt_label} (single line)", default="")
        return result

    try:
        text = Path(tmppath).read_text(encoding="utf-8")
    finally:
        os.unlink(tmppath)
    return text.strip()


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


def run_interview(*, yes: bool = False) -> ProjectConfig:
    """Run the structured interview, returning a ProjectConfig.

    If yes=True, skip questions with defaults. Still prompt required fields.
    """
    typer.echo("Parallax project initialization\n")

    # Detect dirname for default project name
    default_name = Path.cwd().name

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
        package_manager: PackageManager = "pixi"
        test_framework: TestFramework = "pytest"
        uses_units = False
        uses_jax = False
        branch_prefix = ""
        generate_skills = True
        generate_hooks = True
    else:
        languages = _ask_text("Primary language(s)", _CTX_LANGUAGES, default="Python")
        package_manager = cast(
            "PackageManager",
            _ask_choice(
                "Package manager",
                _CTX_PACKAGE_MANAGER,
                ["pixi", "poetry", "pdm", "uv", "pip"],
                default="pixi",
            ),
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

    # Phase B gate
    editor = ""
    science_requirements = ""
    preferred_patterns = ""
    outlawed_patterns = ""
    key_libraries = ""

    if not yes:
        add_detailed = _ask_bool(
            "Add detailed project context?",
            _CTX_DETAILED_GATE,
        )
        if add_detailed:
            default_editor = os.environ.get("EDITOR", "vim")
            editor = _ask_text("Preferred editor", _CTX_EDITOR, default=default_editor)

            typer.echo(f"\n  {_CTX_SCIENCE_REQUIREMENTS}")
            science_requirements = _open_editor(editor, "science_requirements")

            typer.echo(f"\n  {_CTX_PREFERRED_PATTERNS}")
            preferred_patterns = _open_editor(editor, "preferred_patterns")

            typer.echo(f"\n  {_CTX_OUTLAWED_PATTERNS}")
            outlawed_patterns = _open_editor(editor, "outlawed_patterns")

            typer.echo(f"\n  {_CTX_KEY_LIBRARIES}")
            key_libraries = _open_editor(editor, "key_libraries")

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
        editor=editor,
        science_requirements=science_requirements,
        preferred_patterns=preferred_patterns,
        outlawed_patterns=outlawed_patterns,
        key_libraries=key_libraries,
    )
