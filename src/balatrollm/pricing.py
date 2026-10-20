"""Per-model token pricing for providers that don't report cost.

OpenRouter reports the cost of each request in `usage.cost`. The OpenAI and
Anthropic APIs don't, so for direct calls the cost is estimated from the
published per-token prices below and written to the same `usage` fields
(`cost`, `cost_details.upstream_inference_*_cost`) that BalatroBench reads.

Prices are standard-tier USD per million tokens. Update them when providers
change their prices; models not listed here get no cost.

Sources (checked 2026-10-20):
- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing
- OpenAI: https://developers.openai.com/api/docs/pricing
"""

from dataclasses import dataclass
from typing import Any

PRICING_AS_OF = "2026-10-20"


@dataclass(frozen=True)
class Price:
    """Token prices in USD per million tokens."""

    input: float
    cache_read: float
    cache_write: float  # Anthropic: 5-minute cache writes
    output: float


@dataclass(frozen=True)
class ModelPricing:
    """Pricing for one model, with optional long-context prices.

    `long_context` applies to the whole request when its prompt (all input
    tokens, including cache reads and writes) exceeds `long_context_threshold`.
    """

    base: Price
    long_context: Price | None = None
    long_context_threshold: int | None = None


# fmt: off
PRICING: dict[str, ModelPricing] = {
    # Anthropic
    "claude-fable-5-1":  ModelPricing(Price(10.00, 0.25, 12.50, 50.00)),
    "claude-fable-5":    ModelPricing(Price(10.00, 1.00, 12.50, 50.00)),
    "claude-opus-5-5":   ModelPricing(Price(4.00, 0.20, 5.00, 20.00)),
    "claude-opus-5":     ModelPricing(Price(5.00, 0.50, 6.25, 25.00)),
    "claude-opus-4-8":   ModelPricing(Price(5.00, 0.50, 6.25, 25.00)),
    "claude-opus-4-7":   ModelPricing(Price(5.00, 0.50, 6.25, 25.00)),
    "claude-opus-4-6":   ModelPricing(Price(5.00, 0.50, 6.25, 25.00)),
    "claude-sonnet-5-5": ModelPricing(Price(2.00, 0.10, 2.50, 10.00)),
    "claude-sonnet-5":   ModelPricing(Price(2.00, 0.20, 2.50, 10.00)),
    "claude-sonnet-4-6": ModelPricing(Price(3.00, 0.30, 3.75, 15.00)),
    "claude-haiku-5-5":  ModelPricing(
        Price(0.10, 0.01, 0.125, 0.50),
        long_context=Price(0.50, 0.05, 0.625, 2.50),
        long_context_threshold=100_000,
    ),
    "claude-haiku-4-5":  ModelPricing(Price(1.00, 0.10, 1.25, 5.00)),
    # OpenAI
    "gpt-6.1-sol": ModelPricing(
        Price(2.00, 0.10, 2.50, 10.00),
        long_context=Price(4.00, 0.20, 5.00, 15.00),
        long_context_threshold=272_000,
    ),
    "gpt-6-astra": ModelPricing(
        Price(10.00, 1.00, 12.50, 50.00),
        long_context=Price(20.00, 2.00, 25.00, 75.00),
        long_context_threshold=272_000,
    ),
    "gpt-6-sol": ModelPricing(
        Price(2.00, 0.20, 2.50, 10.00),
        long_context=Price(4.00, 0.40, 5.00, 15.00),
        long_context_threshold=272_000,
    ),
    "gpt-6-luna": ModelPricing(
        Price(0.10, 0.01, 0.125, 0.50),
        long_context=Price(0.20, 0.02, 0.25, 0.75),
        long_context_threshold=272_000,
    ),
    "gpt-5.6-sol": ModelPricing(
        Price(4.00, 0.40, 5.00, 20.00),
        long_context=Price(8.00, 0.80, 10.00, 30.00),
        long_context_threshold=272_000,
    ),
}
# fmt: on


def get_pricing(model: str) -> ModelPricing | None:
    """Look up pricing by model id, also matching dated snapshots.

    "gpt-6.1-sol-2026-10-01" matches "gpt-6.1-sol". A vendor prefix
    ("openai/", "anthropic/") is ignored.
    """
    model = model.rsplit("/", 1)[-1]
    if model in PRICING:
        return PRICING[model]
    matches = sorted((key for key in PRICING if model.startswith(f"{key}-")), key=len)
    return PRICING[matches[-1]] if matches else None


def add_cost(usage: dict[str, Any], model: str) -> None:
    """Add estimated cost to a Chat Completions-style usage dict in place.

    Expects `prompt_tokens` to count all input tokens, with cache reads in
    `prompt_tokens_details.cached_tokens` and cache writes in
    `prompt_tokens_details.cache_write_tokens`. Does nothing if the usage
    already has a cost or the model has no pricing.
    """
    pricing = get_pricing(model)
    if pricing is None or usage.get("cost") is not None:
        return

    details = usage.get("prompt_tokens_details") or {}
    prompt_tokens = usage.get("prompt_tokens") or 0
    cache_read = details.get("cached_tokens") or 0
    cache_write = details.get("cache_write_tokens") or 0
    uncached = max(prompt_tokens - cache_read - cache_write, 0)
    completion_tokens = usage.get("completion_tokens") or 0

    price = pricing.base
    if (
        pricing.long_context is not None
        and pricing.long_context_threshold is not None
        and prompt_tokens > pricing.long_context_threshold
    ):
        price = pricing.long_context

    prompt_cost = (
        uncached * price.input
        + cache_read * price.cache_read
        + cache_write * price.cache_write
    ) / 1_000_000
    completion_cost = completion_tokens * price.output / 1_000_000

    usage["cost"] = prompt_cost + completion_cost
    usage["cost_details"] = {
        "upstream_inference_prompt_cost": prompt_cost,
        "upstream_inference_completions_cost": completion_cost,
        "estimated": True,
        "pricing_as_of": PRICING_AS_OF,
    }
