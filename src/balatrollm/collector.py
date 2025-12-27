"""Data collection and statistics for BalatroLLM runs."""

import json
import re
import statistics
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
class AggregatedStats:
    """Aggregated statistics for token usage, costs, and timing."""

    input_tokens: int | float
    output_tokens: int | float
    input_cost: float
    output_cost: float
    total_cost: float
    time_ms: float


@dataclass
class CallStats:
    """Statistics for tool call outcomes."""

    successful: int = 0
    error: int = 0
    failed: int = 0
    total: int = 0


@dataclass
class Stats:
    """Complete statistics for a game run."""

    won: bool
    completed: bool
    ante_reached: int
    final_round: int
    providers: list[str]
    calls: CallStats
    total: AggregatedStats
    average: AggregatedStats
    std_dev: AggregatedStats

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stats":
        return cls(
            won=data["won"],
            completed=data["completed"],
            ante_reached=data["ante_reached"],
            final_round=data["final_round"],
            providers=data["providers"],
            calls=CallStats(**data["calls"]),
            total=AggregatedStats(**data["total"]),
            average=AggregatedStats(**data["average"]),
            std_dev=AggregatedStats(**data["std_dev"]),
        )


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

    request_id: str
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

    id: str  # str(time.time_ns() // 1_000_000),
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
        self.call_stats = CallStats()

        # Write task and strategy for benchmark analysis
        manifest = StrategyManifest.from_file(task.strategy)
        with (self.run_dir / "task.json").open("w") as f:
            json.dump(asdict(self.task), f, indent=2)
        with (self.run_dir / "strategy.json").open("w") as f:
            json.dump(asdict(manifest), f, indent=2)

    def record_call(self, outcome: Literal["successful", "error", "failed"]) -> None:
        """Record a call outcome."""
        match outcome:
            case "successful":
                self.call_stats.successful += 1
            case "error":
                self.call_stats.error += 1
            case "failed":
                self.call_stats.failed += 1
            case _:
                raise ValueError(f"Invalid call outcome: {outcome}")
        self.call_stats.total += 1

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
        # Populate list for each stat type
        ################################################################################

        stats: dict[str, list] = {
            "providers": [],
            "input_tokens": [],
            "output_tokens": [],
            "input_cost": [],
            "output_cost": [],
            "total_cost": [],
            "time_ms": [],
        }
        for res in responses:
            if res.response is not None and res.response.status_code == 200:
                body = res.response.body
                if "provider" in body:
                    stats["providers"].append(body["provider"])

                usage = body.get("usage", {})
                stats["input_tokens"].append(usage.get("prompt_tokens", 0))
                stats["output_tokens"].append(usage.get("completion_tokens", 0))

                cost_details = usage.get("cost_details", {})
                stats["input_cost"].append(
                    cost_details.get("upstream_inference_prompt_cost", 0)
                )
                stats["output_cost"].append(
                    cost_details.get("upstream_inference_completions_cost", 0)
                )
                stats["total_cost"].append(usage.get("cost", 0))
                stats["time_ms"].append(int(res.id) - int(res.response.request_id))

        ################################################################################
        # Compute aggregated stats
        ################################################################################

        n = len(stats["input_tokens"])

        total = AggregatedStats(
            input_tokens=sum(stats["input_tokens"]),
            output_tokens=sum(stats["output_tokens"]),
            input_cost=sum(stats["input_cost"]),
            output_cost=sum(stats["output_cost"]),
            total_cost=sum(stats["total_cost"]),
            time_ms=sum(stats["time_ms"]),
        )

        average = AggregatedStats(
            input_tokens=total.input_tokens / n,
            output_tokens=total.output_tokens / n,
            input_cost=total.input_cost / n,
            output_cost=total.output_cost / n,
            total_cost=total.total_cost / n,
            time_ms=total.time_ms / n,
        )

        std_dev = AggregatedStats(
            input_tokens=statistics.stdev(stats["input_tokens"]),
            output_tokens=statistics.stdev(stats["output_tokens"]),
            input_cost=statistics.stdev(stats["input_cost"]),
            output_cost=statistics.stdev(stats["output_cost"]),
            total_cost=statistics.stdev(stats["total_cost"]),
            time_ms=statistics.stdev(stats["time_ms"]),
        )

        ################################################################################
        # Compute Stats from the final gamestate
        ################################################################################

        gamestate = gamestates[-1]

        return Stats(
            won=gamestate["won"],
            completed=gamestate["state"] == "GAME_OVER" or gamestate["won"],
            ante_reached=gamestate["ante_num"],
            final_round=gamestate["round_num"],
            providers=stats["providers"],
            calls=self.call_stats,
            total=total,
            average=average,
            std_dev=std_dev,
        )
