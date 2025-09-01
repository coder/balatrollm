"""Data collection and run directory management for BalatroLLM."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from openai.types.chat import ChatCompletion

from balatrollm.config import Config


def generate_run_directory(config: Config, base_dir: Path) -> Path:
    """Generate structured directory path for the run.

    Creates a hierarchical directory structure organized by version,
    strategy, provider, model, and run timestamp.

    Args:
        config: Bot configuration containing model, strategy, and run parameters.
        base_dir: Base directory for organizing run data.

    Returns:
        Path to the generated run directory.
    """
    base_dir = base_dir / "runs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    provider, model_name = config.model.split(sep="/", maxsplit=1)
    model_name = model_name.replace("/", "--")

    # Clean names for filesystem safety
    deck_clean = config.deck.replace(" ", "").replace("-", "")
    challenge_clean = (
        config.challenge.replace(" ", "").replace("-", "") if config.challenge else ""
    )

    # Build run directory name
    parts = [timestamp, deck_clean, f"s{config.stake}"]
    if challenge_clean:
        parts.append(challenge_clean)
    parts.append(config.seed)
    run_dir_name = "_".join(parts)

    return (
        base_dir
        / f"v{config.version}"
        / config.strategy
        / provider
        / model_name
        / run_dir_name
    )


@dataclass
class RunStats:
    """Statistics collected from a single game run.

    Tracks game performance, strategy metrics, and LLM performance
    for comprehensive run analysis.

    Attributes:
        run_won: Whether the game run was won.
        completed: Whether the run completed (won or game over).
        ante_reached: Highest ante level reached.
        final_round: Final round number achieved.
        jokers_bought: List of joker names purchased during the run.
        jokers_sold: List of joker names sold during the run.
        consumables_used: List of consumable names used during the run.
        rerolls: Number of shop rerolls performed.
        money_spent: Total money spent during the run.
        hands_played: Dictionary mapping hand types to play counts.
        successful_calls: Number of successful LLM API calls.
        error_calls: List of error messages from failed LLM calls.
        failed_calls: List of failure messages from LLM calls.
        avg_input_tokens: Average input tokens per LLM call.
        avg_output_tokens: Average output tokens per LLM call.
        avg_reasoning_tokens: Average reasoning tokens per LLM call.
        avg_total_tokens: Average total tokens per LLM call.
        avg_response_time_ms: Average response time in milliseconds.
        total_input_tokens: Total input tokens across all calls.
        total_output_tokens: Total output tokens across all calls.
        total_reasoning_tokens: Total reasoning tokens across all calls.
        total_tokens: Total tokens across all calls.
        total_response_time_ms: Total response time in milliseconds.
    """

    # Game Performance
    run_won: bool = False
    completed: bool = False
    ante_reached: int = 0
    final_round: int = 0

    # Strategy Metrics
    jokers_bought: list[str] = field(default_factory=list)
    jokers_sold: list[str] = field(default_factory=list)
    consumables_used: list[str] = field(default_factory=list)
    rerolls: int = 0
    money_spent: int = 0
    hands_played: dict[str, int] = field(default_factory=dict)

    # LLM Performance
    successful_calls: int = 0
    error_calls: list[str] = field(default_factory=list)
    failed_calls: list[str] = field(default_factory=list)
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
    avg_reasoning_tokens: float = 0.0
    avg_total_tokens: float = 0.0
    avg_response_time_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_reasoning_tokens: int = 0
    total_tokens: int = 0
    total_response_time_ms: float = 0.0


@dataclass
class RunStatsCollector:
    """Collects run data in structured directory format.

    Manages structured logging of game execution data, LLM requests/responses,
    and final statistics calculation.

    Attributes:
        run_dir: Directory path for storing this run's data.
        config: Bot configuration for this run.
        request_count: Counter for LLM request numbering.
    """

    run_dir: Path
    config: Config
    request_count: int = 0

    def __post_init__(self):
        """Create directory structure and write config."""
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def write_config(self) -> None:
        """Write the run configuration.

        Saves the bot configuration to config.json in the run directory.
        """
        with open(self.run_dir / "config.json", "w") as f:
            json.dump(asdict(self.config), f, indent=2)

    def write_stats(self) -> None:
        """Calculate and write final run statistics.

        Computes comprehensive statistics from logged data and saves
        to stats.json in the run directory.
        """
        stats = self.calculate_stats()
        with open(self.run_dir / "stats.json", "w") as f:
            json.dump(asdict(stats), f, indent=2)

    def write_request(self, request_data: dict[str, Any]) -> str:
        """Write an LLM request to requests.jsonl in OpenAI batch format.

        Args:
            request_data: Dictionary containing the LLM request parameters.

        Returns:
            Unique request ID for matching with responses.
        """
        self.request_count += 1
        request_id = f"req_{self.request_count:03d}"

        batch_entry = {
            "custom_id": request_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": request_data,
        }

        with open(self.run_dir / "requests.jsonl", "a") as f:
            f.write(json.dumps(batch_entry) + "\n")
        return request_id

    def write_response(
        self,
        request_id: str,
        response: ChatCompletion | None = None,
        error: Exception | None = None,
        status_code: int = 200,
    ) -> None:
        """Write an LLM response to responses.jsonl in OpenAI batch format.

        Args:
            request_id: Unique ID matching the original request.
            response: Successful ChatCompletion response (mutually exclusive with error).
            error: Exception that occurred during request (mutually exclusive with response).
            status_code: HTTP status code for error responses (default: 200).

        Raises:
            ValueError: If neither response nor error is provided.
        """
        if response:
            batch_response = {
                "id": request_id,
                "custom_id": request_id,
                "response": {
                    "status_code": 200,
                    "request_id": response.id,
                    "body": response.model_dump(),
                },
                "error": None,
            }
        elif error:
            batch_response = {
                "id": request_id,
                "custom_id": request_id,
                "response": {
                    "status_code": status_code,
                    "request_id": request_id,
                    "body": {},
                },
                "error": {"code": type(error).__name__, "message": str(error)},
            }
        else:
            raise ValueError("Either response or error must be provided")

        with open(self.run_dir / "responses.jsonl", "a") as f:
            f.write(json.dumps(batch_response) + "\n")

    def calculate_stats(self) -> RunStats:
        """Calculate comprehensive run statistics from logged data.

        Analyzes gamestates.jsonl and responses.jsonl to compute game performance,
        strategy metrics, and LLM performance statistics.

        Returns:
            RunStats instance containing all calculated statistics.
        """
        stats = RunStats()

        # Load game states
        gamestates_path = self.run_dir / "gamestates.jsonl"
        if not gamestates_path.exists():
            return stats

        game_states = []
        with open(gamestates_path, "r") as f:
            for line in f:
                game_states.append(json.loads(line))

        if not game_states:
            return stats

        # Extract final state data
        final_state = game_states[-1].get("game_state_after", {})

        # Game Performance
        stats.run_won = final_state["game"].get(
            "won", False
        )  # TODO: check if "won" is the right key
        stats.completed = stats.run_won or final_state["state"] == "GAME_OVER"
        stats.final_round = final_state["game"]["round"]
        stats.ante_reached = (
            max(1, (stats.final_round // 3) + 1) if stats.final_round > 0 else 1
        )

        # Strategy Metrics
        for state in game_states:
            function_name = state.get("function", {}).get("name")
            args = state.get("function", {}).get("arguments", {})

            if function_name == "shop" and args.get("action") == "buy_joker":
                shop_jokers = state.get("game_state_before", {}).get("shop_jokers", {})
                joker_index = args.get("joker_index", 0)
                if "cards" in shop_jokers and joker_index < len(shop_jokers["cards"]):
                    joker_name = shop_jokers["cards"][joker_index].get(
                        "label", "Unknown"
                    )
                    stats.jokers_bought.append(joker_name)

            elif function_name == "sell_joker":
                jokers_before = state.get("game_state_before", {}).get("jokers", {})
                joker_index = args.get("joker_index", 0)
                if "cards" in jokers_before and joker_index < len(
                    jokers_before["cards"]
                ):
                    joker_name = jokers_before["cards"][joker_index].get(
                        "label", "Unknown"
                    )
                    stats.jokers_sold.append(joker_name)

            elif function_name == "use_consumable":
                consumables_before = state.get("game_state_before", {}).get(
                    "consumables", {}
                )
                consumable_index = args.get("consumable_index", 0)
                if "cards" in consumables_before and consumable_index < len(
                    consumables_before["cards"]
                ):
                    consumable_name = consumables_before["cards"][consumable_index].get(
                        "label", "Unknown"
                    )
                    stats.consumables_used.append(consumable_name)

            elif function_name == "shop" and args.get("action") == "reroll":
                stats.rerolls += 1

            elif (
                function_name == "play_hand_or_discard"
                and args.get("action") == "play_hand"
            ):
                reasoning = args.get("reasoning", "")
                hand_types = [
                    "Pair",
                    "Two Pair",
                    "Three of a Kind",
                    "Straight",
                    "Flush",
                    "Full House",
                    "Four of a Kind",
                    "Straight Flush",
                    "Royal Flush",
                ]
                for hand_type in hand_types:
                    if hand_type.lower() in reasoning.lower():
                        stats.hands_played[hand_type] = (
                            stats.hands_played.get(hand_type, 0) + 1
                        )
                        break
                else:
                    stats.hands_played["High Card"] = (
                        stats.hands_played.get("High Card", 0) + 1
                    )

        # Calculate money spent
        prev_money = None
        for state in game_states:
            current_money = (
                state.get("game_state_after", {}).get("game", {}).get("dollars", 0)
            )
            if prev_money is not None and current_money < prev_money:
                stats.money_spent += prev_money - current_money
            prev_money = current_money

        # Calculate response times
        response_times = []
        for state in game_states:
            before = state.get("timestamp_ms_before", 0)
            after = state.get("timestamp_ms_after", 0)
            if after > before:
                response_times.append(after - before)
        stats.total_response_time_ms = sum(response_times)
        stats.avg_response_time_ms = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )

        # LLM Performance
        responses_path = self.run_dir / "responses.jsonl"
        if responses_path.exists():
            input_tokens = []
            output_tokens = []
            reasoning_tokens = []
            total_tokens = []

            with open(responses_path, "r") as f:
                for line in f:
                    response = json.loads(line)
                    if (
                        response.get("error") is None
                        and response.get("response", {}).get("status_code") == 200
                    ):
                        stats.successful_calls += 1
                        body = response.get("response", {}).get("body", {})
                        usage = body.get("usage", {})

                        if "prompt_tokens" in usage:
                            input_tokens.append(usage["prompt_tokens"])
                        if "completion_tokens" in usage:
                            output_tokens.append(usage["completion_tokens"])
                        if "reasoning_tokens" in usage:
                            reasoning_tokens.append(usage["reasoning_tokens"])
                        if "total_tokens" in usage:
                            total_tokens.append(usage["total_tokens"])

                    elif response.get("error") is not None:
                        error = response.get("error", {})
                        error_msg = f"{error.get('code', 'UnknownError')}: {error.get('message', '')}"
                        stats.error_calls.append(error_msg)

                    elif response.get("response", {}).get("status_code", 200) != 200:
                        status_code = response.get("response", {}).get("status_code")
                        body = response.get("response", {}).get("body", {})
                        error_msg = body.get("error", f"HTTP {status_code}")
                        stats.failed_calls.append(f"Status {status_code}: {error_msg}")

            # Calculate totals
            stats.total_input_tokens = sum(input_tokens)
            stats.total_output_tokens = sum(output_tokens)
            stats.total_reasoning_tokens = sum(reasoning_tokens)
            stats.total_tokens = sum(total_tokens)

            # Calculate averages
            stats.avg_input_tokens = (
                sum(input_tokens) / len(input_tokens) if input_tokens else 0.0
            )
            stats.avg_output_tokens = (
                sum(output_tokens) / len(output_tokens) if output_tokens else 0.0
            )
            stats.avg_reasoning_tokens = (
                sum(reasoning_tokens) / len(reasoning_tokens)
                if reasoning_tokens
                else 0.0
            )
            stats.avg_total_tokens = (
                sum(total_tokens) / len(total_tokens) if total_tokens else 0.0
            )

        return stats
