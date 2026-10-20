"""Unit tests for the pricing module."""

from typing import Any

import pytest

from balatrollm.pricing import PRICING, add_cost, get_pricing


class TestGetPricing:
    """Tests for model pricing lookup."""

    def test_exact_match(self) -> None:
        """Model ids match exactly."""
        assert get_pricing("claude-haiku-5-5") is PRICING["claude-haiku-5-5"]

    def test_vendor_prefix_ignored(self) -> None:
        """A vendor prefix is ignored."""
        assert get_pricing("openai/gpt-6.1-sol") is PRICING["gpt-6.1-sol"]

    def test_dated_snapshot_matches_base_model(self) -> None:
        """Dated snapshots match the longest base model id."""
        assert get_pricing("gpt-6-sol-2026-09-01") is PRICING["gpt-6-sol"]
        assert get_pricing("claude-opus-5-5-20261001") is PRICING["claude-opus-5-5"]

    def test_unknown_model(self) -> None:
        """Unknown models have no pricing."""
        assert get_pricing("some-local-model") is None


class TestAddCost:
    """Tests for cost estimation."""

    def test_cost_breakdown(self) -> None:
        """Cost splits uncached, cache read, cache write and output tokens."""
        usage: dict[str, Any] = {
            "prompt_tokens": 1_000_000,
            "completion_tokens": 1_000_000,
            "prompt_tokens_details": {
                "cached_tokens": 500_000,
                "cache_write_tokens": 250_000,
            },
        }
        add_cost(usage, "claude-opus-5-5")
        # 250K uncached * $4 + 500K read * $0.20 + 250K write * $5 = $2.35
        details = usage["cost_details"]
        assert details["upstream_inference_prompt_cost"] == pytest.approx(2.35)
        assert details["upstream_inference_completions_cost"] == pytest.approx(20.0)
        assert usage["cost"] == pytest.approx(22.35)

    def test_long_context_prices(self) -> None:
        """Prompts over the threshold use long-context prices for the request."""
        usage = {"prompt_tokens": 100_001, "completion_tokens": 0}
        add_cost(usage, "claude-haiku-5-5")
        assert usage["cost"] == pytest.approx(100_001 * 0.50 / 1_000_000)

    def test_threshold_counts_cached_tokens(self) -> None:
        """The long-context threshold counts cache reads too."""
        usage = {
            "prompt_tokens": 300_000,
            "completion_tokens": 0,
            "prompt_tokens_details": {"cached_tokens": 290_000},
        }
        add_cost(usage, "gpt-6.1-sol")
        expected = (10_000 * 4.00 + 290_000 * 0.20) / 1_000_000
        assert usage["cost"] == pytest.approx(expected)

    def test_existing_cost_kept(self) -> None:
        """A provider-reported cost is not overwritten."""
        usage = {"prompt_tokens": 10, "completion_tokens": 10, "cost": 1.5}
        add_cost(usage, "gpt-6.1-sol")
        assert usage["cost"] == 1.5

    def test_unknown_model_no_cost(self) -> None:
        """Models without pricing get no cost."""
        usage = {"prompt_tokens": 10, "completion_tokens": 10}
        add_cost(usage, "some-local-model")
        assert "cost" not in usage
