#!/usr/bin/env python3
"""Check documentation staleness against actual code/CLI state.

Checks:
1. CLI commands listed in README.md match `parallax --help` output
2. Every agent in _AGENT_NAMES is mentioned in README.md
3. ROADMAP.md Layer 1 checked items correspond to implemented features

Exit 1 on any staleness detected; 0 if all checks pass.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
ROADMAP = REPO_ROOT / "docs" / "ROADMAP.md"


def _get_cli_commands() -> set[str]:
    """Extract command names from `parallax --help`."""
    result = subprocess.run(
        ["parallax", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        print(f"ERROR: parallax --help failed: {result.stderr}")
        sys.exit(1)

    commands: set[str] = set()
    in_commands = False
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if "Commands" in stripped and "─" in stripped:
            in_commands = True
            continue
        if in_commands:
            if "─" in stripped and "╰" in stripped:
                break
            # Command lines look like: │ init    Description text │
            parts = stripped.strip("│").strip().split()
            if parts and parts[0].isalpha():
                commands.add(parts[0])
    return commands


def check_cli_commands_in_readme() -> list[str]:
    """Verify all CLI commands appear in README usage section."""
    errors: list[str] = []
    readme_text = README.read_text(encoding="utf-8")
    cli_commands = _get_cli_commands()

    for cmd in cli_commands:
        if f"parallax {cmd}" not in readme_text:
            errors.append(f"CLI command 'parallax {cmd}' missing from README.md")

    return errors


def check_agents_in_readme() -> list[str]:
    """Verify every agent in _AGENT_NAMES is mentioned in README.md."""
    from parallax.core.renderer import _AGENT_NAMES

    errors: list[str] = []
    readme_text = README.read_text(encoding="utf-8")

    for agent in _AGENT_NAMES:
        # Agent output names use hyphens
        hyphenated = agent.replace("_", "-")
        if hyphenated not in readme_text:
            errors.append(f"Agent '{hyphenated}' missing from README.md")

    return errors


def check_roadmap_checked_items() -> list[str]:
    """Verify ROADMAP.md Layer 1 checked items are reasonable.

    Light check: ensure [x] items under 'Layer 1 Remaining Work' exist.
    Doesn't validate semantics -- just that the section is present and
    checked items aren't empty.
    """
    errors: list[str] = []
    if not ROADMAP.exists():
        errors.append("docs/ROADMAP.md does not exist")
        return errors

    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    if "Layer 1 Remaining Work" not in roadmap_text:
        errors.append("ROADMAP.md missing 'Layer 1 Remaining Work' section")
        return errors

    # Count checked vs unchecked in Layer 1 section
    in_layer1 = False
    checked = 0
    for line in roadmap_text.splitlines():
        if "Layer 1 Remaining Work" in line:
            in_layer1 = True
            continue
        if in_layer1 and line.startswith("## "):
            break
        if in_layer1 and "- [x]" in line:
            checked += 1

    if checked == 0:
        errors.append("ROADMAP.md Layer 1 has no checked items")

    return errors


def main() -> None:
    """Run all staleness checks."""
    all_errors: list[str] = []

    print("Checking CLI commands in README...")
    all_errors.extend(check_cli_commands_in_readme())

    print("Checking agents in README...")
    all_errors.extend(check_agents_in_readme())

    print("Checking ROADMAP.md...")
    all_errors.extend(check_roadmap_checked_items())

    if all_errors:
        print(f"\n{len(all_errors)} staleness issue(s) found:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("All doc staleness checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
