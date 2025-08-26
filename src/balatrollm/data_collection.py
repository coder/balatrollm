"""Data collection and run directory management for BalatroLLM."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from openai.types.chat import ChatCompletion


def generate_run_directory(
    deck: str,
    stake: int,
    seed: str,
    model: str,
    strategy: str,
    project_version: str,
    challenge: str | None = None,
    base_dir: Path | None = None,
) -> Path:
    """Generate structured directory path for the run."""
    base_dir = base_dir or Path.cwd() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clean names for filesystem safety
    deck_clean = _clean_name(deck)
    provider_model = _parse_provider_model(model)
    challenge_clean = _clean_name(challenge) if challenge else None

    # Build run directory name
    parts = [timestamp, deck_clean, f"s{stake}"]
    if challenge_clean:
        parts.append(challenge_clean)
    parts.append(seed)

    run_dir_name = "_".join(parts)
    return base_dir / f"v{project_version}" / provider_model / strategy / run_dir_name


def _parse_provider_model(model: str) -> str:
    """Parse provider/model format and sanitize for filesystem safety."""
    # Handle provider/model format (e.g., groq/qwen/qwen3-32b -> groq/qwen--qwen3-32b)
    if "/" in model:
        provider, model_name = model.split("/", 1)  # Split on first / only
        # Sanitize model name: replace / with -- for filesystem safety
        sanitized_model = model_name.replace("/", "--")
        # Clean other problematic characters
        provider_clean = _clean_name(provider, ": ", "-")
        model_clean = _clean_name(sanitized_model, ": ", "-")
        return f"{provider_clean}/{model_clean}"

    # Fallback: treat as single model name without provider
    return _clean_name(model, "/: ", "-")


def _clean_name(name: str, chars_to_replace: str = " -", replacement: str = "") -> str:
    """Clean a name for filesystem safety."""
    for char in chars_to_replace:
        name = name.replace(char, replacement)
    return name


@dataclass
class RunDataCollector:
    """Collects run data in structured directory format."""

    run_dir: Path
    run_config: dict[str, Any] = field(default_factory=dict)
    initial_stats: dict[str, Any] = field(default_factory=dict)
    request_count: int = 0

    def __post_init__(self):
        """Create directory structure and write config and initial stats."""
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Write config immediately if available
        if self.run_config:
            self._write_config()

        # Write initial stats if available
        if self.initial_stats:
            self._write_stats()

    def _write_config(self) -> None:
        """Write the run configuration to config.json."""
        config_path = self.run_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(self.run_config, f, indent=2)

    def _write_stats(self) -> None:
        """Write the run statistics to stats.json."""
        stats_path = self.run_dir / "stats.json"
        with open(stats_path, "w") as f:
            json.dump(self.initial_stats, f, indent=2)

    def update_config(self, config: dict[str, Any]) -> None:
        """Update and write the run configuration."""
        self.run_config.update(config)
        self._write_config()

    def update_stats(self, stats: dict[str, Any]) -> None:
        """Update and write the run statistics."""
        self.initial_stats.update(stats)
        self._write_stats()

    def write_gamestate(self, entry: dict[str, Any]) -> None:
        """Write a game state entry to gamestates.jsonl."""
        self._write_jsonl("gamestates.jsonl", entry)

    def write_request(self, request_data: dict[str, Any]) -> str:
        """Write an LLM request to requests.jsonl in OpenAI batch format."""
        self.request_count += 1
        request_id = f"req_{self.request_count:03d}"

        batch_entry = {
            "custom_id": request_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": request_data,
        }

        self._write_jsonl("requests.jsonl", batch_entry)
        return request_id

    def write_response(
        self,
        request_id: str,
        response: ChatCompletion | None = None,
        error: Exception | None = None,
        status_code: int = 200,
    ) -> None:
        """Write an LLM response to responses.jsonl in OpenAI batch format."""
        if response:
            batch_response = self._create_success_response(request_id, response)
        elif error:
            batch_response = self._create_error_response(request_id, error, status_code)
        else:
            raise ValueError("Either response or error must be provided")

        self._write_jsonl("responses.jsonl", batch_response)

    def _create_success_response(
        self, request_id: str, response: ChatCompletion
    ) -> dict:
        """Create success response entry."""
        return {
            "id": request_id,
            "custom_id": request_id,
            "response": {
                "status_code": 200,
                "request_id": response.id,
                "body": response.model_dump(),
            },
            "error": None,
        }

    def _create_error_response(
        self, request_id: str, error: Exception, status_code: int
    ) -> dict:
        """Create error response entry."""
        return {
            "id": request_id,
            "custom_id": request_id,
            "response": {
                "status_code": status_code,
                "request_id": request_id,
                "body": {},
            },
            "error": {"code": type(error).__name__, "message": str(error)},
        }

    def _write_jsonl(self, filename: str, data: dict) -> None:
        """Write data to a JSONL file."""
        file_path = self.run_dir / filename
        with open(file_path, "a") as f:
            f.write(json.dumps(data) + "\n")

    def calculate_comprehensive_stats(self) -> dict[str, Any]:
        """Calculate comprehensive statistics from game data."""
        gamestates_path = self.run_dir / "gamestates.jsonl"
        if not gamestates_path.exists():
            return {}

        # Load game states
        game_states = self._load_game_states(gamestates_path)
        if not game_states:
            return {}

        # Extract final state data
        final_state = game_states[-1].get("game_state_after", {})
        game_data = final_state.get("game", {})

        # Calculate metrics in logical groups
        core_metrics = self._calculate_core_performance_metrics(
            game_states, final_state, game_data
        )
        efficiency_metrics = self._calculate_efficiency_metrics(
            game_states, final_state, game_data
        )
        strategic_metrics = self._calculate_strategic_metrics(game_states, game_data)
        advanced_metrics = self._calculate_advanced_analytics(game_states)
        llm_metrics = self._calculate_llm_performance_metrics(game_states)

        # Combine all metrics
        return {
            **core_metrics,
            **efficiency_metrics,
            **strategic_metrics,
            **advanced_metrics,
            **llm_metrics,
        }

    def _load_game_states(self, gamestates_path: Path) -> list[dict[str, Any]]:
        """Load and parse game states from JSONL file."""
        game_states = []
        with open(gamestates_path, "r") as f:
            for line in f:
                game_states.append(json.loads(line))
        return game_states

    def _calculate_core_performance_metrics(
        self, game_states: list[dict], final_state: dict, game_data: dict
    ) -> dict[str, Any]:
        """Calculate core game performance metrics."""
        return {
            "run_won": game_data.get("won", False),
            "final_score": final_state.get("chips", 0),
            "final_money": game_data.get("dollars", 0),
            "ante_reached": self._calculate_ante_reached(game_states),
            "final_round": game_data.get("round", 0),
            "blinds_defeated": self._count_blinds_defeated(game_states),
            "boss_blinds_defeated": self._count_boss_blinds_defeated(game_states),
        }

    def _calculate_efficiency_metrics(
        self, game_states: list[dict], final_state: dict, game_data: dict
    ) -> dict[str, Any]:
        """Calculate efficiency and speed metrics."""
        total_decisions = len(game_states)
        return {
            "total_decisions": total_decisions,
            "decisions_per_minute": self._calculate_decisions_per_minute(game_states),
            "score_per_decision": self._safe_divide(
                final_state.get("chips", 0), total_decisions
            ),
            "money_per_decision": self._safe_divide(
                game_data.get("dollars", 0), total_decisions
            ),
            "average_response_time_ms": self._calculate_average_response_time(
                game_states
            ),
        }

    def _calculate_strategic_metrics(
        self, game_states: list[dict], game_data: dict
    ) -> dict[str, Any]:
        """Calculate strategic depth metrics."""
        return {
            "jokers_acquired": self._count_jokers_acquired(game_states),
            "consumables_used": self._count_consumables_used(game_states),
            "shop_visits": self._count_shop_visits(game_states),
            "rerolls_used": self._count_rerolls_used(game_states),
            "total_money_spent": self._calculate_money_spent(game_states),
            "peak_money_reached": self._calculate_peak_money(game_states),
            "hands_played_total": game_data.get("hands_played", 0),
            "discards_used_total": self._calculate_total_discards_used(game_states),
        }

    def _calculate_advanced_analytics(self, game_states: list[dict]) -> dict[str, Any]:
        """Calculate advanced analytics metrics."""
        return {
            "money_efficiency_ratio": self._calculate_money_efficiency(game_states),
            "resource_management_score": self._calculate_resource_management_score(
                game_states
            ),
            "hand_type_distribution": self._analyze_hand_types(game_states),
            "decision_consistency_score": self._calculate_decision_consistency(
                game_states
            ),
            "risk_assessment_score": self._calculate_risk_score(game_states),
            "joker_synergy_score": self._calculate_joker_synergy(game_states),
        }

    def _calculate_llm_performance_metrics(
        self, game_states: list[dict]
    ) -> dict[str, Any]:
        """Calculate LLM-specific performance metrics."""
        return {
            "failed_requests": self._count_failed_requests(),
            "total_reasoning_length": self._calculate_total_reasoning_length(
                game_states
            ),
            "average_reasoning_complexity": self._calculate_reasoning_complexity(
                game_states
            ),
        }

    def _calculate_ante_reached(self, game_states: list[dict]) -> int:
        """Calculate the highest ante reached."""
        max_ante = 0
        for state in game_states:
            game_data = state.get("game_state_after", {}).get("game", {})
            # Ante is typically round // 3 + 1 in Balatro
            round_num = game_data.get("round", 0)
            ante = min(round_num // 3 + 1, 8) if round_num > 0 else 1
            max_ante = max(max_ante, ante)
        return max_ante

    def _count_blinds_defeated(self, game_states: list[dict]) -> int:
        """Count total blinds defeated."""
        blinds_defeated = 0
        for state in game_states:
            if state.get("function", {}).get("name") == "cash_out":
                blinds_defeated += 1
        return blinds_defeated

    def _count_boss_blinds_defeated(self, game_states: list[dict]) -> int:
        """Count boss blinds defeated."""
        boss_blinds = 0
        for state in game_states:
            game_after = state.get("game_state_after", {}).get("game", {})
            last_blind = game_after.get("last_blind", {})
            if (
                last_blind.get("boss", False)
                and state.get("function", {}).get("name") == "cash_out"
            ):
                boss_blinds += 1
        return boss_blinds

    def _calculate_decisions_per_minute(self, game_states: list[dict]) -> float:
        """Calculate decisions per minute."""
        if not game_states or len(game_states) < 2:
            return 0.0

        first_timestamp = game_states[0].get("timestamp_ms_before", 0)
        last_timestamp = game_states[-1].get("timestamp_ms_after", 0)

        duration_minutes = (last_timestamp - first_timestamp) / (1000 * 60)
        return len(game_states) / duration_minutes if duration_minutes > 0 else 0.0

    def _calculate_average_response_time(self, game_states: list[dict]) -> float:
        """Calculate average response time in milliseconds."""
        response_times = []
        for state in game_states:
            before = state.get("timestamp_ms_before", 0)
            after = state.get("timestamp_ms_after", 0)
            if after > before:
                response_times.append(after - before)

        return sum(response_times) / len(response_times) if response_times else 0.0

    def _count_jokers_acquired(self, game_states: list[dict]) -> int:
        """Count total jokers acquired during the run."""
        max_jokers = 0
        for state in game_states:
            jokers = state.get("game_state_after", {}).get("jokers", {})
            joker_count = jokers.get("config", {}).get("card_count", 0)
            max_jokers = max(max_jokers, joker_count)
        return max_jokers

    def _count_consumables_used(self, game_states: list[dict]) -> int:
        """Count consumables (Planet/Tarot cards) used."""
        consumables_used = 0
        for state in game_states:
            if state.get("function", {}).get("name") == "use_consumable":
                consumables_used += 1
        return consumables_used

    def _count_shop_visits(self, game_states: list[dict]) -> int:
        """Count number of shop visits."""
        shop_visits = 0
        for state in game_states:
            if "shop_jokers" in state.get("game_state_after", {}):
                shop_visits += 1
        return shop_visits

    def _count_rerolls_used(self, game_states: list[dict]) -> int:
        """Count shop rerolls used."""
        rerolls = 0
        for state in game_states:
            if (
                state.get("function", {}).get("name") == "shop"
                and state.get("function", {}).get("arguments", {}).get("action")
                == "reroll"
            ):
                rerolls += 1
        return rerolls

    def _calculate_money_spent(self, game_states: list[dict]) -> int:
        """Calculate total money spent during the run."""
        money_spent = 0
        prev_money = None

        for state in game_states:
            current_money = (
                state.get("game_state_after", {}).get("game", {}).get("dollars", 0)
            )
            if prev_money is not None and current_money < prev_money:
                money_spent += prev_money - current_money
            prev_money = current_money

        return money_spent

    def _calculate_peak_money(self, game_states: list[dict]) -> int:
        """Calculate peak money reached."""
        peak_money = 0
        for state in game_states:
            money = state.get("game_state_after", {}).get("game", {}).get("dollars", 0)
            peak_money = max(peak_money, money)
        return peak_money

    def _calculate_total_discards_used(self, game_states: list[dict]) -> int:
        """Calculate total discards used."""
        total_discards = 0
        for state in game_states:
            game_data = state.get("game_state_after", {}).get("game", {})
            current_round = game_data.get("current_round", {})
            discards_used = current_round.get("discards_used", 0)
            total_discards = max(total_discards, discards_used)
        return total_discards

    def _calculate_money_efficiency(self, game_states: list[dict]) -> float:
        """Calculate money efficiency ratio."""
        if not game_states:
            return 0.0

        final_money = (
            game_states[-1]
            .get("game_state_after", {})
            .get("game", {})
            .get("dollars", 0)
        )
        peak_money = self._calculate_peak_money(game_states)

        return final_money / peak_money if peak_money > 0 else 0.0

    def _calculate_resource_management_score(self, game_states: list[dict]) -> float:
        """Calculate composite resource management score."""
        if not game_states:
            return 0.0

        final_state = game_states[-1].get("game_state_after", {})
        final_money = final_state.get("game", {}).get("dollars", 0)
        final_score = final_state.get("chips", 0)

        # Composite score: (money + score/100) / decisions
        composite = (final_money + final_score / 100) / len(game_states)
        return round(composite, 2)

    def _analyze_hand_types(self, game_states: list[dict]) -> dict[str, int]:
        """Analyze distribution of hand types played."""
        # This would require parsing the actual hands played
        # For now, return empty dict - can be enhanced later
        return {}

    def _calculate_decision_consistency(self, game_states: list[dict]) -> float:
        """Calculate decision consistency score based on reasoning patterns."""
        reasoning_lengths = []
        for state in game_states:
            reasoning = (
                state.get("function", {}).get("arguments", {}).get("reasoning", "")
            )
            reasoning_lengths.append(len(reasoning))

        if not reasoning_lengths:
            return 0.0

        # Calculate coefficient of variation (lower = more consistent)
        mean_length = sum(reasoning_lengths) / len(reasoning_lengths)
        variance = sum((x - mean_length) ** 2 for x in reasoning_lengths) / len(
            reasoning_lengths
        )
        std_dev = variance**0.5

        cv = std_dev / mean_length if mean_length > 0 else 0
        # Convert to consistency score (higher = more consistent)
        return max(0, 1 - cv)

    def _calculate_risk_score(self, game_states: list[dict]) -> float:
        """Calculate risk assessment based on money variance."""
        money_values = []
        for state in game_states:
            money = state.get("game_state_after", {}).get("game", {}).get("dollars", 0)
            money_values.append(money)

        if len(money_values) < 2:
            return 0.0

        mean_money = sum(money_values) / len(money_values)
        variance = sum((x - mean_money) ** 2 for x in money_values) / len(money_values)
        std_dev = variance**0.5

        # Normalize by mean to get coefficient of variation
        return std_dev / mean_money if mean_money > 0 else 0.0

    def _calculate_joker_synergy(self, game_states: list[dict]) -> float:
        """Calculate joker synergy effectiveness score."""
        # This would require complex analysis of joker combinations
        # For now, return simple metric based on joker count vs performance
        if not game_states:
            return 0.0

        max_jokers = self._count_jokers_acquired(game_states)
        final_score = game_states[-1].get("game_state_after", {}).get("chips", 0)

        # Simple synergy metric: score per joker
        return final_score / max_jokers if max_jokers > 0 else 0.0

    def _count_failed_requests(self) -> int:
        """Count failed LLM requests from responses.jsonl."""
        responses_path = self.run_dir / "responses.jsonl"
        if not responses_path.exists():
            return 0

        failed_count = 0
        with open(responses_path, "r") as f:
            for line in f:
                response = json.loads(line)
                if response.get("error") is not None:
                    failed_count += 1
        return failed_count

    def _calculate_total_reasoning_length(self, game_states: list[dict]) -> int:
        """Calculate total length of reasoning text."""
        total_length = 0
        for state in game_states:
            reasoning = (
                state.get("function", {}).get("arguments", {}).get("reasoning", "")
            )
            total_length += len(reasoning)
        return total_length

    def _calculate_reasoning_complexity(self, game_states: list[dict]) -> float:
        """Calculate average reasoning complexity."""
        reasoning_lengths = []
        for state in game_states:
            reasoning = (
                state.get("function", {}).get("arguments", {}).get("reasoning", "")
            )
            reasoning_lengths.append(len(reasoning))

        return (
            sum(reasoning_lengths) / len(reasoning_lengths)
            if reasoning_lengths
            else 0.0
        )

    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """Safely divide two numbers, returning 0 if denominator is 0."""
        return numerator / denominator if denominator != 0 else 0.0
