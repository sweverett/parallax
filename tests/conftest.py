"""Shared test fixtures and helpers."""

from parallax.core.config import ProjectConfig


def make_config(**overrides: object) -> ProjectConfig:
    """Build a ProjectConfig with sensible defaults, overriding as needed."""
    defaults: dict[str, object] = {
        "project_name": "test-project",
        "summary": "A test project",
        "domain": "astrophysics",
        "languages": "Python",
        "package_manager": "pixi",
        "test_framework": "pytest",
        "uses_units": False,
        "uses_jax": False,
        "branch_prefix": "",
        "generate_skills": True,
        "generate_hooks": True,
        "token_tier": "pro",
        "editor": "vim",
        "science_requirements": "",
        "preferred_patterns": "",
        "outlawed_patterns": "",
        "key_libraries": "",
        "custom_agent_description": "",
    }
    defaults.update(overrides)
    return ProjectConfig(**defaults)  # type: ignore[arg-type]
