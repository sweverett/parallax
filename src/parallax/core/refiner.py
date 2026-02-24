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


def run_refinement(target: Path) -> bool:
    """Invoke Claude CLI for post-init synthesis. Returns True if successful."""
    if not shutil.which("claude"):
        typer.echo(
            "Warning: 'claude' CLI not found. Skipping auto-refinement.\n"
            "  Run refinement manually in a Claude Code session, or install:\n"
            "  npm install -g @anthropic-ai/claude-code"
        )
        return False

    typer.echo("Running auto-refinement via Claude CLI...")
    try:
        subprocess.run(
            ["claude", "-p", _REFINEMENT_PROMPT, "--cwd", str(target)],
            check=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        typer.echo("Warning: refinement timed out after 120s. Files left as-is.")
        return False
    except subprocess.CalledProcessError as exc:
        typer.echo(
            f"Warning: refinement failed (exit {exc.returncode}). "
            "Refinement blocks left intact. Run `parallax refine` manually."
        )
        return False

    typer.echo("Auto-refinement complete.")
    return True
