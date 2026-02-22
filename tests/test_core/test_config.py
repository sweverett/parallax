"""Tests for ProjectConfig dataclass."""

import pytest

from tests.conftest import make_config


def test_basic_construction() -> None:
    cfg = make_config()
    assert cfg.project_name == "test-project"
    assert cfg.summary == "A test project"
    assert cfg.domain == "astrophysics"


def test_frozen() -> None:
    cfg = make_config()
    with pytest.raises(AttributeError):
        cfg.project_name = "nope"  # type: ignore[misc]


def test_all_fields_present() -> None:
    cfg = make_config()
    expected_fields = {
        "project_name",
        "summary",
        "domain",
        "languages",
        "package_manager",
        "test_framework",
        "uses_units",
        "uses_jax",
        "branch_prefix",
        "generate_skills",
        "generate_hooks",
        "editor",
        "science_requirements",
        "preferred_patterns",
        "outlawed_patterns",
        "key_libraries",
    }
    assert set(cfg.__dataclass_fields__) == expected_fields


def test_phase_b_defaults_empty() -> None:
    cfg = make_config()
    assert cfg.science_requirements == ""
    assert cfg.preferred_patterns == ""
    assert cfg.outlawed_patterns == ""
    assert cfg.key_libraries == ""


def test_bool_fields() -> None:
    cfg = make_config(uses_units=True, uses_jax=True)
    assert cfg.uses_units is True
    assert cfg.uses_jax is True


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_empty_project_name_raises(self) -> None:
        with pytest.raises(ValueError, match="project_name"):
            make_config(project_name="")

    def test_whitespace_project_name_raises(self) -> None:
        with pytest.raises(ValueError, match="project_name"):
            make_config(project_name="   ")

    def test_empty_summary_raises(self) -> None:
        with pytest.raises(ValueError, match="summary"):
            make_config(summary="")

    def test_empty_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="domain"):
            make_config(domain="")

    def test_whitespace_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="domain"):
            make_config(domain="  \t ")

    def test_invalid_package_manager_raises(self) -> None:
        with pytest.raises(ValueError, match="package_manager"):
            make_config(package_manager="conda")

    def test_invalid_test_framework_raises(self) -> None:
        with pytest.raises(ValueError, match="test_framework"):
            make_config(test_framework="tox")

    @pytest.mark.parametrize("pm", ["pixi", "poetry", "pdm", "uv", "pip"])
    def test_all_valid_package_managers(self, pm: str) -> None:
        cfg = make_config(package_manager=pm)
        assert cfg.package_manager == pm

    @pytest.mark.parametrize("tf", ["pytest", "unittest", "nose2"])
    def test_all_valid_test_frameworks(self, tf: str) -> None:
        cfg = make_config(test_framework=tf)
        assert cfg.test_framework == tf
