"""ProjectConfig: frozen dataclass holding all parallax init responses."""

from dataclasses import dataclass
from typing import Literal

PackageManager = Literal["pixi", "poetry", "pdm", "uv", "pip"]
TestFramework = Literal["pytest", "unittest", "nose2"]
TokenTier = Literal["pro", "5x", "20x", "api"]

VALID_PACKAGE_MANAGERS: frozenset[str] = frozenset(
    ["pixi", "poetry", "pdm", "uv", "pip"]
)
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
    package_manager: PackageManager
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

        # Defense-in-depth beyond Literal types
        if self.package_manager not in VALID_PACKAGE_MANAGERS:
            msg = (
                f"Invalid package_manager {self.package_manager!r}. "
                f"Must be one of: {sorted(VALID_PACKAGE_MANAGERS)}"
            )
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
