"""Auto-refinement: invoke Claude CLI to synthesize generated files."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from pathlib import Path

_REFINEMENT_PROMPT = """\
You are refining a freshly generated Parallax project. Read ALL generated files, then:

1. Read CLAUDE.md, PARALLAX.md, CONSTITUTION.md
2. Read all files in .claude/skills/*/SKILL.md
3. Read all files in .claude/agents/*.md
4. Read .claude/settings.json if it exists

Then synthesize for internal consistency:
- Cross-references between files should be accurate
- Terminology should be consistent (same terms for same concepts)
- Tone should be scientific, concise, no LLM-speak, no emojis
- Agent skill references should match actual skill names
- If .claude/agents/custom.md exists: infer a proper name, description, appropriate \
tools, and model from the user's description. Rename the file to match the agent name \
(hyphenated, e.g. data-validator.md). Update the frontmatter accordingly.

Strip all refinement comment blocks (<!-- PARALLAX REFINEMENT: ... -->) when done.

Report what was changed in a brief summary.
"""

_MERGE_REFINEMENT_PROMPT = """\
You are refining a Parallax project initialized into a repo with existing configuration.

Read .parallax/merge-guide.md for the full list of file pairs and merge instructions.
Then for each pair:
1. Read BOTH the original and the .parallax version
2. Synthesize a single merged version that:
   - Preserves existing project-specific content, structure, and tone
   - Integrates Parallax scientific rigor rules, workflow conventions, and references
   - For skills: merge capabilities, keeping the richer protocol
   - For settings.json: merge hook configs (union of hooks)
   - Resolves conflicts favoring the more specific/detailed version
3. Write merged result to the ORIGINAL filename
4. Delete the .parallax suffixed file after each successful merge
5. Review PARALLAX.md and CONSTITUTION.md for consistency with merged CLAUDE.md

Strip refinement comment blocks (<!-- PARALLAX REFINEMENT: ... -->) when done.
Report what was changed.
"""


_BACKGROUND_TIMEOUT = 300


def run_refinement(
    target: Path,
    *,
    background: bool = False,
    merge_mode: bool = False,
) -> bool:
    """Invoke Claude CLI for post-init synthesis. Returns True if successful.

    Default: interactive session (user sees and controls Claude).
    background=True: headless subprocess with 300s timeout.
    """
    if not shutil.which("claude"):
        typer.echo(
            "Warning: 'claude' CLI not found. Skipping auto-refinement.\n"
            "  Run refinement manually in a Claude Code session, or install:\n"
            "  npm install -g @anthropic-ai/claude-code"
        )
        return False

    prompt = _MERGE_REFINEMENT_PROMPT if merge_mode else _REFINEMENT_PROMPT

    if background:
        return _run_background(target, prompt)
    return _run_interactive(target, prompt)


def _run_interactive(target: Path, prompt: str) -> bool:
    """Launch interactive Claude session with refinement prompt."""
    typer.echo("Opening Claude Code session for refinement...")
    try:
        result = subprocess.run(
            ["claude", "--permission-mode", "plan", prompt],
            cwd=target,
        )
    except FileNotFoundError:
        typer.echo("Error: 'claude' binary not found.")
        return False
    if result.returncode != 0:
        typer.echo(
            f"Warning: Claude session exited with code {result.returncode}. "
            "Refinement blocks may be left intact. Run `parallax refine` manually."
        )
        return False
    typer.echo("Auto-refinement complete.")
    return True


def _run_background(target: Path, prompt: str) -> bool:
    """Run refinement as headless subprocess with timeout."""
    typer.echo("Running auto-refinement in background...")
    try:
        subprocess.run(
            ["claude", "-p", prompt],
            check=True,
            timeout=_BACKGROUND_TIMEOUT,
            cwd=target,
        )
    except subprocess.TimeoutExpired:
        typer.echo(
            f"Warning: refinement timed out after {_BACKGROUND_TIMEOUT}s. "
            "Files left as-is."
        )
        return False
    except subprocess.CalledProcessError as exc:
        typer.echo(
            f"Warning: refinement failed (exit {exc.returncode}). "
            "Refinement blocks left intact. Run `parallax refine` manually."
        )
        return False

    typer.echo("Auto-refinement complete.")
    return True
