"""Tests for the interview module."""

from unittest.mock import patch

from parallax.core.interview import (
    _ask_choice,
    _parse_phase_b,
    _strip_html_comments,
    run_interview,
)


class TestRunInterviewYesMode:
    """--yes mode: skips defaulted questions, prompts required."""

    def test_yes_mode_returns_defaults(self) -> None:
        """In --yes mode, non-required fields get defaults."""
        original_values = ["My project summary", "genomics"]
        call_idx = 0

        def fake_prompt(label: str, default: str = "") -> str:
            nonlocal call_idx
            val = original_values[call_idx]
            call_idx += 1
            return val

        with patch(
            "parallax.core.interview.typer.prompt",
            side_effect=fake_prompt,
        ):
            cfg = run_interview(yes=True)

        assert cfg.summary == "My project summary"
        assert cfg.domain == "genomics"
        assert cfg.languages == "Python"
        assert cfg.package_manager == "pixi"
        assert cfg.test_framework == "pytest"
        assert cfg.uses_units is False
        assert cfg.uses_jax is False
        assert cfg.branch_prefix == ""
        assert cfg.generate_skills is True
        assert cfg.generate_hooks is True
        assert cfg.token_tier == "pro"
        # Phase B skipped
        assert cfg.science_requirements == ""
        assert cfg.preferred_patterns == ""
        assert cfg.custom_agent_description == ""


class TestRunInterviewFull:
    """Full interactive mode."""

    def test_full_no_detailed(self) -> None:
        """Full interview, decline detailed context."""
        prompt_responses = iter(
            [
                "my-project",
                "A science tool",
                "climate",
                "Python",
                "pixi",
                "pytest",
                "",
                "pro",
            ]
        )
        confirm_responses = iter(
            [
                False,
                False,
                True,
                True,
                False,
            ]
        )

        def fake_prompt(label: str, default: str = "") -> str:
            return next(prompt_responses)

        def fake_confirm(label: str, default: bool = False) -> bool:
            return next(confirm_responses)

        with (
            patch(
                "parallax.core.interview.typer.prompt",
                side_effect=fake_prompt,
            ),
            patch(
                "parallax.core.interview.typer.confirm",
                side_effect=fake_confirm,
            ),
        ):
            cfg = run_interview(yes=False)

        assert cfg.project_name == "my-project"
        assert cfg.summary == "A science tool"
        assert cfg.domain == "climate"
        assert cfg.uses_units is False
        assert cfg.generate_skills is True
        assert cfg.science_requirements == ""

    def test_full_with_units_and_jax(self) -> None:
        prompt_responses = iter(
            [
                "jax-project",
                "Differentiable astrophysics",
                "astrophysics",
                "Python",
                "pixi",
                "pytest",
                "se/",
                "5x",
            ]
        )
        confirm_responses = iter(
            [
                True,
                True,
                True,
                True,
                False,
            ]
        )

        def fake_prompt(label: str, default: str = "") -> str:
            return next(prompt_responses)

        def fake_confirm(label: str, default: bool = False) -> bool:
            return next(confirm_responses)

        with (
            patch(
                "parallax.core.interview.typer.prompt",
                side_effect=fake_prompt,
            ),
            patch(
                "parallax.core.interview.typer.confirm",
                side_effect=fake_confirm,
            ),
        ):
            cfg = run_interview(yes=False)

        assert cfg.uses_units is True
        assert cfg.uses_jax is True
        assert cfg.branch_prefix == "se/"
        assert cfg.token_tier == "5x"

    def test_token_tier_override(self) -> None:
        """CLI --token-tier overrides interview answer."""
        original_values = ["My project", "genomics"]
        call_idx = 0

        def fake_prompt(label: str, default: str = "") -> str:
            nonlocal call_idx
            val = original_values[call_idx]
            call_idx += 1
            return val

        with patch(
            "parallax.core.interview.typer.prompt",
            side_effect=fake_prompt,
        ):
            cfg = run_interview(yes=True, token_tier_override="20x")

        assert cfg.token_tier == "20x"


class TestAskChoice:
    """Tests for _ask_choice validation and case-insensitive matching."""

    def test_rejects_invalid_then_accepts_valid(self) -> None:
        """Invalid input rejected, valid input accepted on retry."""
        responses = iter(["conda", "pixi"])

        with (
            patch(
                "parallax.core.interview.typer.prompt",
                side_effect=lambda *a, **kw: next(responses),
            ),
            patch("parallax.core.interview.typer.echo") as mock_echo,
        ):
            result = _ask_choice(
                "Package manager",
                "Pick one",
                ["pixi", "poetry"],
                default="pixi",
            )

        assert result == "pixi"
        # Verify error message was shown
        echo_calls = [str(c) for c in mock_echo.call_args_list]
        assert any("Invalid choice" in c for c in echo_calls)

    def test_case_insensitive_returns_canonical(self) -> None:
        """'Pixi' -> 'pixi' (canonical casing from choices list)."""
        with patch(
            "parallax.core.interview.typer.prompt",
            return_value="Pixi",
        ):
            result = _ask_choice(
                "Package manager",
                "Pick one",
                ["pixi", "poetry"],
                default="pixi",
            )

        assert result == "pixi"


class TestPhaseBParsing:
    """Tests for the single-editor Phase B parsing."""

    def test_parse_all_sections_filled(self) -> None:
        text = (
            "## Science Requirements\n"
            "Measure galaxy redshifts\n\n"
            "## Preferred Patterns\n"
            "Functional style\n\n"
            "## Outlawed Patterns\n"
            "No bare except\n\n"
            "## Key Libraries\n"
            "astropy: units\njax: autodiff\n\n"
            "## Custom Agent\n"
            "pipeline-validator -- checks ETL outputs\n"
        )
        result = _parse_phase_b(text)
        assert result["science_requirements"] == "Measure galaxy redshifts"
        assert result["preferred_patterns"] == "Functional style"
        assert result["outlawed_patterns"] == "No bare except"
        assert result["key_libraries"] == "astropy: units\njax: autodiff"
        assert (
            result["custom_agent_description"]
            == "pipeline-validator -- checks ETL outputs"
        )

    def test_parse_empty_sections(self) -> None:
        text = (
            "## Science Requirements\n\n"
            "## Preferred Patterns\n\n"
            "## Outlawed Patterns\n\n"
            "## Key Libraries\n\n"
            "## Custom Agent\n\n"
        )
        result = _parse_phase_b(text)
        for field in result.values():
            assert field == ""

    def test_parse_with_html_comments_stripped(self) -> None:
        text = (
            "## Science Requirements\n"
            "<!-- This is an instruction -->\n"
            "Actual content here\n\n"
            "## Preferred Patterns\n"
            "<!-- Multi-line\n"
            "instruction -->\n"
            "Real patterns\n"
        )
        result = _parse_phase_b(text)
        assert result["science_requirements"] == "Actual content here"
        assert result["preferred_patterns"] == "Real patterns"

    def test_parse_missing_sections_default_empty(self) -> None:
        text = "## Science Requirements\nSome content\n"
        result = _parse_phase_b(text)
        assert result["science_requirements"] == "Some content"
        assert result["preferred_patterns"] == ""
        assert result["custom_agent_description"] == ""

    def test_parse_preserves_multiline_content(self) -> None:
        text = (
            "## Key Libraries\n"
            "astropy: units and coordinates\n"
            "jax: autodiff framework\n"
            "galsim: galaxy image simulation\n"
        )
        result = _parse_phase_b(text)
        assert "astropy" in result["key_libraries"]
        assert "galsim" in result["key_libraries"]
        assert "\n" in result["key_libraries"]

    def test_strip_html_comments(self) -> None:
        assert _strip_html_comments("hello <!-- gone --> world") == "hello  world"
        assert _strip_html_comments("<!-- multi\nline -->keep") == "keep"
        assert _strip_html_comments("no comments") == "no comments"

    def test_parse_full_template(self) -> None:
        """Parse the actual template with user content added."""
        from parallax.core.interview import _PHASE_B_TEMPLATE

        # Simulate user filling in sections
        filled = _PHASE_B_TEMPLATE.replace(
            "## Science Requirements\n"
            "<!-- What is this project trying to achieve scientifically?\n"
            "     Describe objectives, key phenomena, methods. -->",
            "## Science Requirements\n"
            "<!-- What is this project trying to achieve scientifically?\n"
            "     Describe objectives, key phenomena, methods. -->\n"
            "Measure photometric redshifts for LSST",
        )
        result = _parse_phase_b(filled)
        expected = "Measure photometric redshifts for LSST"
        assert result["science_requirements"] == expected
