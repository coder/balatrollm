"""Data collection and statistics for BalatroLLM runs."""

import json
import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from . import __version__
from .config import Task
from .strategy import StrategyManifest


def _generate_run_dir(task: Task, base_dir: Path) -> Path:
    """Generate unique run directory path."""
    assert re.match(r"^[a-z0-9.-]+/[a-z0-9:.-]+$", task.model), (
        f"Invalid vendor/model format: {task.model}"
    )
    vendor, model = task.model.split("/", 1)
    dir_name = "_".join(
        [
            datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3],
            task.deck,
            task.stake,
            task.seed,
        ]
    )
    return (
        base_dir
        / "runs"
        / f"v{__version__}"
        / task.strategy
        / vendor
        / model
        / dir_name
    )


@dataclass
class Stats:
    """Complete statistics for a game run (flat structure)."""

    # Outcome
    run_won: bool
    run_completed: bool
    final_ante: int
    final_round: int

    # Provider distribution
    providers: dict[str, int]

    # Call statistics
    calls_total: int
    calls_success: int
    calls_error: int
    calls_failed: int

    # Token statistics
    tokens_in_total: int
    tokens_out_total: int
    tokens_in_avg: float
    tokens_out_avg: float
    tokens_in_std: float
    tokens_out_std: float

    # Timing statistics
    time_total_ms: int
    time_avg_ms: float
    time_std_ms: float

    # Cost statistics
    cost_total: float
    cost_avg: float
    cost_std: float


@dataclass
class ChatCompletionRequestInput:
    """OpenAI Batch API request format."""

    custom_id: str  # f"request-{Collector._request_count:05}"
    method: str = "POST"
    url: str = "/v1/chat/completions"
    body: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatCompletionResponse:
    """OpenAI Batch API response format."""

    request_id: str  # str(time.time_ns() // 1_000_000) at request time
    status_code: int
    body: dict[str, Any]


@dataclass
class ChatCompletionError:
    """Error information for failed requests."""

    code: str
    message: str


@dataclass
class ChatCompletionRequestOutput:
    """OpenAI Batch API response output format."""

    id: str  # str(time.time_ns() // 1_000_000) at response time
    custom_id: str  # f"request-{Collector._request_count:05}"
    response: ChatCompletionResponse | None = None
    error: ChatCompletionError | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatCompletionRequestOutput":
        response = None
        if data.get("response"):
            response = ChatCompletionResponse(**data["response"])

        error = None
        if data.get("error"):
            error = ChatCompletionError(**data["error"])

        return cls(
            id=data["id"],
            custom_id=data["custom_id"],
            response=response,
            error=error,
        )


class Collector:
    """Manages run data collection."""

    def __init__(self, task: Task, base_dir: Path) -> None:
        # Create save directories
        self.run_dir = _generate_run_dir(task, base_dir)
        self.screenshot_dir = self.run_dir / "screenshots"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.task = task
        self._request_count = 0

        # Call tracking
        self._calls_success = 0
        self._calls_error = 0
        self._calls_failed = 0
        self._calls_total = 0

        # Write task with structured model for benchmark analysis
        vendor, model_name = task.model.split("/", 1)
        task_data = {
            "model": {"vendor": vendor, "name": model_name},
            "seed": task.seed,
            "deck": task.deck,
            "stake": task.stake,
            "strategy": task.strategy,
        }
        manifest = StrategyManifest.from_file(task.strategy)
        with (self.run_dir / "task.json").open("w") as f:
            json.dump(task_data, f, indent=2)
        with (self.run_dir / "strategy.json").open("w") as f:
            json.dump(asdict(manifest), f, indent=2)

    def record_call(self, outcome: Literal["successful", "error", "failed"]) -> None:
        """Record a call outcome."""
        match outcome:
            case "successful":
                self._calls_success += 1
            case "error":
                self._calls_error += 1
            case "failed":
                self._calls_failed += 1
            case _:
                raise ValueError(f"Invalid call outcome: {outcome}")
        self._calls_total += 1

    def write_request(self, body: dict[str, Any]) -> str:
        """Write request to requests.jsonl. Returns custom_id."""
        self._request_count += 1
        custom_id = f"request-{self._request_count:05}"
        req = ChatCompletionRequestInput(custom_id=custom_id, body=body)
        with (self.run_dir / "requests.jsonl").open("a") as f:
            f.write(json.dumps(asdict(req)) + "\n")
        return custom_id

    def write_response(
        self,
        id: str,
        custom_id: str,
        response: ChatCompletionResponse | None = None,
        error: ChatCompletionError | None = None,
    ) -> None:
        """Write response to responses.jsonl."""
        res = ChatCompletionRequestOutput(
            id=id,
            custom_id=custom_id,
            response=response,
            error=error,
        )
        with (self.run_dir / "responses.jsonl").open("a") as f:
            f.write(json.dumps(asdict(res)) + "\n")

    def write_gamestate(self, gamestate: dict[str, Any]) -> None:
        """Write gamestate to gamestates.jsonl."""
        with (self.run_dir / "gamestates.jsonl").open("a") as f:
            f.write(json.dumps(gamestate) + "\n")

    def write_stats(self) -> None:
        """Calculate and write final statistics to stats.json."""
        stats = self._calculate_stats()
        with (self.run_dir / "stats.json").open("w") as f:
            json.dump(asdict(stats), f, indent=2)

    def _calculate_stats(self) -> Stats:
        """Calculate statistics from collected data."""

        ################################################################################
        # Load gamestates and responses
        ################################################################################

        gamestates_path = self.run_dir / "gamestates.jsonl"
        with gamestates_path.open() as f:
            gamestates = [json.loads(line) for line in f]
        assert len(gamestates) >= 1, "Expected at least one gamestate"
        responses_path = self.run_dir / "responses.jsonl"
        with responses_path.open() as f:
            responses = [
                ChatCompletionRequestOutput.from_dict(json.loads(line)) for line in f
            ]
        assert len(responses) >= 2, "Expected at least two responses"

        ################################################################################
        # Populate lists for each stat type and count providers
        ################################################################################

        provider_counts: Counter[str] = Counter()
        input_tokens: list[int] = []
        output_tokens: list[int] = []
        total_costs: list[float] = []
        time_ms_list: list[int] = []

        for res in responses:
            if res.response is not None and res.response.status_code == 200:
                body = res.response.body
                if "provider" in body:
                    provider_counts[body["provider"]] += 1

                usage = body.get("usage", {})
                input_tokens.append(usage.get("prompt_tokens", 0))
                output_tokens.append(usage.get("completion_tokens", 0))
                total_costs.append(usage.get("cost", 0))
                time_ms_list.append(int(res.id) - int(res.response.request_id))

        ################################################################################
        # Compute aggregated stats
        ################################################################################

        n = len(input_tokens)
        gamestate = gamestates[-1]

        return Stats(
            # Outcome
            run_won=gamestate["won"],
            run_completed=gamestate["state"] == "GAME_OVER" or gamestate["won"],
            final_ante=gamestate["ante_num"],
            final_round=gamestate["round_num"],
            # Provider distribution
            providers=dict(provider_counts),
            # Call statistics
            calls_total=self._calls_total,
            calls_success=self._calls_success,
            calls_error=self._calls_error,
            calls_failed=self._calls_failed,
            # Token statistics
            tokens_in_total=sum(input_tokens),
            tokens_out_total=sum(output_tokens),
            tokens_in_avg=sum(input_tokens) / n,
            tokens_out_avg=sum(output_tokens) / n,
            tokens_in_std=statistics.stdev(input_tokens),
            tokens_out_std=statistics.stdev(output_tokens),
            # Timing statistics
            time_total_ms=sum(time_ms_list),
            time_avg_ms=sum(time_ms_list) / n,
            time_std_ms=statistics.stdev(time_ms_list),
            # Cost statistics
            cost_total=sum(total_costs),
            cost_avg=sum(total_costs) / n,
            cost_std=statistics.stdev(total_costs),
        )
