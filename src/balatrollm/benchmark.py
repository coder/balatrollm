import json
import re
import statistics
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from balatrollm.config import Config
from balatrollm.data_collection import Stats


@dataclass
class ModelCallStats:
    successful: int = 0
    error: int = 0
    failed: int = 0
    total: int = 0


@dataclass
class ModelAggregatedStats:
    input_tokens: int | float
    output_tokens: int | float
    input_cost: float
    output_cost: float
    total_cost: float
    time_ms: float


@dataclass
class ModelStats:
    runs: int
    wins: int
    completed: int

    avg_final_round: float
    std_dev_final_round: float
    providers: dict[str, int]  # provider -> number of calls

    calls: ModelCallStats  # sum of successful/error/failed calls
    total: ModelAggregatedStats
    average: ModelAggregatedStats  # avg over tool calls
    std_dev: ModelAggregatedStats  # std dev over tool calls
    config: Config


@dataclass
class ModelStatsFull(ModelStats):
    stats: list[Stats]


@dataclass
class ModelsLeaderboard:
    generated_at: int
    entries: list[ModelStats]


class BenchmarkAnalyzer:
    def __init__(
        self,
        runs_dir: Path = Path("runs"),
        benchmark_dir: Path = Path("benchmarks"),
    ):
        self.runs_dir = runs_dir
        self.benchmak_dir = benchmark_dir

    def analyze_all_runs(self) -> None:
        for version_dir in self.runs_dir.iterdir():
            if version_dir.is_dir():
                if re.match(r"^v[0-9]+\.[0-9]+\.[0-9]+$", version_dir.name):
                    for strategy_dir in version_dir.iterdir():
                        if strategy_dir.is_dir():
                            self.analyze_strategy_runs(strategy_dir)

    def analyze_strategy_runs(self, strategy_dir: Path) -> None:
        models_stats = []
        output_dir = self.benchmak_dir / strategy_dir.relative_to(self.runs_dir)
        for vendor_dir in strategy_dir.iterdir():
            for model_dir in vendor_dir.iterdir():
                model_stats = self.compute_model_stats(model_dir)
                models_stats.append(model_stats)
                model_stats_path = (
                    output_dir / vendor_dir.name / f"{model_dir.name}.json"
                )
                model_stats_path.parent.mkdir(exist_ok=True, parents=True)
                with open(model_stats_path, "w") as f:
                    json.dump(asdict(model_stats), f, indent=2)

        leaderboard = self.compute_models_leaderboard(models_stats)
        leaderboard_path = output_dir / "leaderboard.json"
        with open(leaderboard_path, "w") as f:
            json.dump(asdict(leaderboard), f, indent=2)

    def compute_model_stats(self, model_dir: Path) -> ModelStatsFull:
        stats: list[Stats] = []
        configs: list[Config] = []
        for run_dir in model_dir.iterdir():
            with open(run_dir / "stats.json", "r") as f:
                stats.append(Stats.from_dict(json.load(f)))
            with open(run_dir / "config.json", "r") as f:
                configs.append(Config(**json.load(f)))

        config = configs[0]
        for c in configs[1:]:
            assert c == config, f"Configs in {model_dir} are not the same"

        avg_final_round = sum(stat.final_round for stat in stats) / len(stats)
        std_final_round = statistics.stdev(stat.final_round for stat in stats)

        providers_list = []
        for stat in stats:
            providers_list.extend(stat.providers)
        providers = dict(Counter(providers_list))

        calls = ModelCallStats(
            sum(stat.calls.successful for stat in stats),
            sum(stat.calls.error for stat in stats),
            sum(stat.calls.failed for stat in stats),
            sum(stat.calls.total for stat in stats),
        )

        total = ModelAggregatedStats(
            sum(stat.total.input_tokens for stat in stats),
            sum(stat.total.output_tokens for stat in stats),
            sum(stat.total.input_cost for stat in stats),
            sum(stat.total.output_cost for stat in stats),
            sum(stat.total.total_cost for stat in stats),
            sum(stat.total.time_ms for stat in stats),
        )

        average = ModelAggregatedStats(
            total.input_tokens / calls.total,
            total.output_tokens / calls.total,
            total.input_cost / calls.total,
            total.output_cost / calls.total,
            total.total_cost / calls.total,
            total.time_ms / calls.total,
        )

        def tot_std_dev(attr: str) -> float:
            var = 0
            mean = getattr(average, attr)
            for stat in stats:
                std_i = getattr(stat.std_dev, attr)
                mean_i = getattr(stat.average, attr)
                n_i = stat.calls.total
                var += (n_i * (std_i**2 + (mean_i - mean) ** 2)) / (calls.total - 1)
            return (1 / calls.total) * var**0.5

        std_dev = ModelAggregatedStats(
            tot_std_dev("input_tokens"),
            tot_std_dev("output_tokens"),
            tot_std_dev("input_cost"),
            tot_std_dev("output_cost"),
            tot_std_dev("total_cost"),
            tot_std_dev("time_ms"),
        )

        return ModelStatsFull(
            runs=len(stats),
            wins=len([s for s in stats if s.won]),
            completed=len([s for s in stats if s.completed]),
            avg_final_round=avg_final_round,
            std_dev_final_round=std_final_round,
            providers=providers,
            calls=calls,
            total=total,
            average=average,
            std_dev=std_dev,
            stats=stats,
            config=config,
        )

    def compute_models_leaderboard(
        self, models_stats: list[ModelStatsFull | ModelStats]
    ) -> ModelsLeaderboard:
        models_stats = sorted(
            models_stats, key=lambda x: x.avg_final_round, reverse=True
        )
        entries = []
        for stats in models_stats:
            stats_dict = asdict(stats)
            stats_dict.pop("stats", None)
            entries.append(ModelStats(**stats_dict))
        return ModelsLeaderboard(generated_at=int(time.time()), entries=entries)
