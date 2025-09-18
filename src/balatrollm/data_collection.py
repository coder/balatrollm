import json
import re
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from balatrollm.config import Config


@dataclass
class AggregatedStats:
    input_tokens: int | float
    output_tokens: int | float
    input_cost: float
    output_cost: float
    total_cost: float
    time_ms: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AggregatedStats":
        return cls(**data)


@dataclass
class CallStats:
    successful: int = 0  # tool call was executed successfully
    error: int = 0  # no a valid tool call
    failed: int = 0  # valid tool call but a BalatroError occurred
    total: int = 0  # total number of calls

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CallStats":
        return cls(**data)


@dataclass
class Stats:
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
        calls = CallStats.from_dict(data["calls"])
        total = AggregatedStats.from_dict(data["total"])
        average = AggregatedStats.from_dict(data["average"])
        std_dev = AggregatedStats.from_dict(data["std_dev"])

        return cls(
            won=data["won"],
            completed=data["completed"],
            ante_reached=data["ante_reached"],
            final_round=data["final_round"],
            providers=data["providers"],
            calls=calls,
            total=total,
            average=average,
            std_dev=std_dev,
        )


@dataclass
class ChatCompletionRequestInput:
    custom_id: str  # unique identifier for the request/response pair
    method: str = "POST"
    url: str = "/v1/chat/completions"
    body: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatCompletionResponse:
    request_id: str  # unix timestamp in ms for the request
    status_code: int
    body: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatCompletionResponse":
        return cls(**data)


@dataclass
class ChatCompletionError:
    code: str
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatCompletionError":
        return cls(**data)


@dataclass
class ChatCompletionRequestOutput:
    id: str  # unix timestamp in ms for the response
    custom_id: str  # unique identifier for the request/response pair
    response: ChatCompletionResponse | None = None
    error: ChatCompletionError | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatCompletionRequestOutput":
        response = None
        if data.get("response"):
            response = ChatCompletionResponse.from_dict(data["response"])

        error = None
        if data.get("error"):
            error = ChatCompletionError.from_dict(data["error"])

        return cls(
            id=data["id"],
            custom_id=data["custom_id"],
            response=response,
            error=error,
        )


class StatsCollector:
    def __init__(self, config: Config, base_dir: Path, run_dir: Path | None = None):
        self.config = config
        self.run_dir = run_dir or self._generate_run_dir(base_dir)
        self.call_stats = CallStats()
        self._request_count = 0

    def _generate_run_dir(self, base_dir: Path) -> Path:
        assert re.match(r"^[a-z0-9.-]+/[a-z0-9:.-]+$", self.config.model), (
            f"Invalid vendor/model format: {self.config.model}"
        )
        vendor, model = self.config.model.split("/", 1)
        dir_name = "_".join(
            [
                datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3],
                self.config.deck.replace(" ", ""),
                f"s{self.config.stake}",
                self.config.challenge.replace(" ", "") if self.config.challenge else "",
                self.config.seed,
            ]
        )
        return (
            base_dir
            / "runs"
            / f"v{self.config.version}"
            / self.config.strategy
            / vendor
            / model
            / dir_name
        )

    def write_stats(self) -> None:
        """Calculate and write final run statistics.

        Computes comprehensive statistics from logged data and saves
        to stats.json in the run directory.
        """
        stats = self.calculate_stats()
        with open(self.run_dir / "stats.json", "w") as f:
            json.dump(asdict(stats), f, indent=2)

    def write_request(self, body: dict[str, Any]) -> str:
        self._request_count += 1
        custom_id = f"request-{self._request_count:05}"
        req = ChatCompletionRequestInput(
            custom_id=custom_id,
            body=body,
        )
        with open(self.run_dir / "requests.jsonl", "a") as f:
            f.write(json.dumps(asdict(req)) + "\n")
        return custom_id

    def write_response(
        self,
        id: str,
        custom_id: str,
        response: ChatCompletionResponse | None = None,
        error: ChatCompletionError | None = None,
    ) -> None:
        res = ChatCompletionRequestOutput(
            id=id,
            custom_id=custom_id,
            response=response,
            error=error,
        )
        with open(self.run_dir / "responses.jsonl", "a") as f:
            f.write(json.dumps(asdict(res)) + "\n")

    def calculate_stats(self) -> Stats:
        with open(self.run_dir / "gamestates.jsonl", "r") as f:
            gamestates = [json.loads(line) for line in f]

        with open(self.run_dir / "responses.jsonl", "r") as f:
            responses = [
                ChatCompletionRequestOutput.from_dict(json.loads(line)) for line in f
            ]

        stats = dict(
            providers=[],
            input_tokens=[],
            output_tokens=[],
            input_cost=[],
            output_cost=[],
            total_cost=[],
            time_ms=[],
        )

        for res in responses:
            if res.response is not None and res.response.status_code == 200:
                stats["providers"].append(res.response.body["provider"])
                stats["input_tokens"].append(
                    res.response.body["usage"]["prompt_tokens"]
                )
                stats["output_tokens"].append(
                    res.response.body["usage"]["completion_tokens"]
                )
                stats["input_cost"].append(
                    res.response.body["usage"]["cost_details"][
                        "upstream_inference_prompt_cost"
                    ]
                )
                stats["output_cost"].append(
                    res.response.body["usage"]["cost_details"][
                        "upstream_inference_completions_cost"
                    ]
                )
                stats["total_cost"].append(res.response.body["usage"]["cost"])
                stats["time_ms"].append(int(res.id) - int(res.response.request_id))

        # Call Stats are tracked during the by the LLMBot class
        call_stats = self.call_stats

        # Total Stats
        total = AggregatedStats(
            input_tokens=sum(stats["input_tokens"]),
            output_tokens=sum(stats["output_tokens"]),
            input_cost=sum(stats["input_cost"]),
            output_cost=sum(stats["output_cost"]),
            total_cost=sum(stats["total_cost"]),
            time_ms=sum(stats["time_ms"]),
        )

        # Average Stats
        average = AggregatedStats(
            input_tokens=sum(stats["input_tokens"]) / len(stats["input_tokens"]),
            output_tokens=sum(stats["output_tokens"]) / len(stats["output_tokens"]),
            input_cost=sum(stats["input_cost"]) / len(stats["input_cost"]),
            output_cost=sum(stats["output_cost"]) / len(stats["output_cost"]),
            total_cost=sum(stats["total_cost"]) / len(stats["total_cost"]),
            time_ms=sum(stats["time_ms"]) / len(stats["time_ms"]),
        )

        # Std Dev Stats
        std_dev = AggregatedStats(
            input_tokens=statistics.stdev(stats["input_tokens"]),
            output_tokens=statistics.stdev(stats["output_tokens"]),
            input_cost=statistics.stdev(stats["input_cost"]),
            output_cost=statistics.stdev(stats["output_cost"]),
            total_cost=statistics.stdev(stats["total_cost"]),
            time_ms=statistics.stdev(stats["time_ms"]),
        )

        state = gamestates[-1]["game_state_after"]

        # Base Stats
        return Stats(
            won=state["game"]["won"],
            completed=state["state"] == 4,  # 4 is GAME_OVER gamestate
            ante_reached=state["game"]["round_resets"]["ante"],
            final_round=state["game"]["round"],
            providers=stats["providers"],
            calls=call_stats,
            total=total,
            average=average,
            std_dev=std_dev,
        )
