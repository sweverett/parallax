"""ProjectConfig: frozen dataclass holding all parallax init responses."""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 — used at runtime in to_json/from_json
from typing import Literal

TestFramework = Literal["pytest", "unittest", "nose2"]
TokenTier = Literal["pro", "5x", "20x", "api"]

VALID_TEST_FRAMEWORKS: frozenset[str] = frozenset(["pytest", "unittest", "nose2"])
VALID_TOKEN_TIERS: frozenset[str] = frozenset(["pro", "5x", "20x", "api"])


@dataclass(frozen=True)
class ProjectConfig:
    """All answers from the parallax init interview."""

    # Phase A: core (always asked)
    project_name: str
    summary: str
    domain: str
    languages: str
    package_manager: str
    test_framework: TestFramework
    uses_units: bool
    uses_jax: bool
    branch_prefix: str
    generate_skills: bool
    generate_hooks: bool
    token_tier: TokenTier

    # Phase B: detailed context (all may be empty)
    editor: str
    science_requirements: str
    preferred_patterns: str
    outlawed_patterns: str
    key_libraries: str
    custom_agent_description: str

    def __post_init__(self) -> None:
        # Required non-empty strings
        for field in ("project_name", "summary", "domain"):
            val = getattr(self, field)
            if not isinstance(val, str) or not val.strip():
                msg = f"{field} must be a non-empty string, got {val!r}"
                raise ValueError(msg)

        if self.test_framework not in VALID_TEST_FRAMEWORKS:
            msg = (
                f"Invalid test_framework {self.test_framework!r}. "
                f"Must be one of: {sorted(VALID_TEST_FRAMEWORKS)}"
            )
            raise ValueError(msg)

        if self.token_tier not in VALID_TOKEN_TIERS:
            msg = (
                f"Invalid token_tier {self.token_tier!r}. "
                f"Must be one of: {sorted(VALID_TOKEN_TIERS)}"
            )
            raise ValueError(msg)

    def to_json(self, path: Path) -> None:
        """Serialize config to JSON file. Creates parent dirs if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dataclasses.asdict(self), indent=2) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def from_json(cls, path: Path) -> ProjectConfig:
        """Deserialize config from JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)
