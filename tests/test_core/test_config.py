"""Tests for ProjectConfig dataclass."""

from pathlib import Path

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
        "token_tier",
        "editor",
        "science_requirements",
        "preferred_patterns",
        "outlawed_patterns",
        "key_libraries",
        "custom_agent_description",
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

    def test_invalid_token_tier_raises(self) -> None:
        with pytest.raises(ValueError, match="token_tier"):
            make_config(token_tier="free")

    @pytest.mark.parametrize("tier", ["pro", "5x", "20x", "api"])
    def test_all_valid_token_tiers(self, tier: str) -> None:
        cfg = make_config(token_tier=tier)
        assert cfg.token_tier == tier

    def test_default_token_tier(self) -> None:
        cfg = make_config()
        assert cfg.token_tier == "pro"

    def test_custom_agent_description_field(self) -> None:
        cfg = make_config(custom_agent_description="my custom agent")
        assert cfg.custom_agent_description == "my custom agent"


# ---------------------------------------------------------------------------
# JSON serialization tests
# ---------------------------------------------------------------------------


class TestJsonRoundTrip:
    def test_round_trip_defaults(self, tmp_path: Path) -> None:
        cfg = make_config()
        path = tmp_path / "cache.json"
        cfg.to_json(path)
        loaded = type(cfg).from_json(path)
        assert loaded == cfg

    def test_round_trip_all_fields(self, tmp_path: Path) -> None:
        cfg = make_config(
            uses_units=True,
            uses_jax=True,
            branch_prefix="se/",
            token_tier="20x",
            science_requirements="Measure redshifts",
            preferred_patterns="Functional",
            outlawed_patterns="No bare except",
            key_libraries="astropy: units",
            custom_agent_description="pipeline checker",
        )
        path = tmp_path / "sub" / "cache.json"
        cfg.to_json(path)
        loaded = type(cfg).from_json(path)
        assert loaded == cfg

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        cfg = make_config()
        path = tmp_path / "deep" / "nested" / "cache.json"
        cfg.to_json(path)
        assert path.exists()

    def test_from_json_invalid_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{}", encoding="utf-8")
        with pytest.raises(TypeError):
            type(make_config()).from_json(path)
