"""Tests for the interview module."""

from unittest.mock import patch

from parallax.core.interview import _ask_choice, run_interview


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
