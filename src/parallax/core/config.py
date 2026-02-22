"""ProjectConfig: frozen dataclass holding all parallax init responses."""

from dataclasses import dataclass
from typing import Literal

PackageManager = Literal["pixi", "poetry", "pdm", "uv", "pip"]
TestFramework = Literal["pytest", "unittest", "nose2"]

VALID_PACKAGE_MANAGERS: frozenset[str] = frozenset(
    ["pixi", "poetry", "pdm", "uv", "pip"]
)
VALID_TEST_FRAMEWORKS: frozenset[str] = frozenset(["pytest", "unittest", "nose2"])


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

    # Phase B: detailed context (all may be empty)
    editor: str
    science_requirements: str
    preferred_patterns: str
    outlawed_patterns: str
    key_libraries: str

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
