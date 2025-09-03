"""Benchmark analysis and leaderboard generation for BalatroLLM runs."""

import json
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .config import Config
from .data_collection import RunStats


@dataclass
class AveragedStats:
    """Simple container for averaged stats.

    Stores averaged performance metrics calculated across multiple runs
    with the same configuration.

    Attributes:
        avg_final_round: Average final round reached across runs.
        avg_ante_reached: Average ante level reached across runs.
        avg_jokers_bought: Average number of jokers bought per run.
        avg_jokers_sold: Average number of jokers sold per run.
        avg_consumables_used: Average number of consumables used per run.
        avg_rerolls: Average number of shop rerolls per run.
        avg_money_spent: Average money spent per run.
        avg_successful_calls: Average successful LLM calls per run.
        avg_error_calls: Average number of error calls per run.
        avg_failed_calls: Average number of failed calls per run.
        avg_total_input_tokens: Average total input tokens per run.
        avg_total_output_tokens: Average total output tokens per run.
        avg_total_reasoning_tokens: Average total reasoning tokens per run.
        avg_total_tokens: Average total tokens per run.
        avg_total_response_time_ms: Average total response time per run.
    """

    avg_final_round: float
    avg_ante_reached: float

    avg_jokers_bought: float
    avg_jokers_sold: float
    avg_consumables_used: float
    avg_rerolls: float
    avg_money_spent: float

    avg_successful_calls: float
    avg_error_calls: float
    avg_failed_calls: float

    avg_total_input_tokens: float
    avg_total_output_tokens: float
    avg_total_reasoning_tokens: float
    avg_total_tokens: float
    avg_total_response_time_ms: float


@dataclass
class RunsData:
    """Aggregated data for multiple runs with identical configuration.

    Combines statistics from multiple runs sharing the same model,
    strategy, and version for comparative analysis.

    Attributes:
        config: Shared configuration across all runs.
        total_runs: Total number of runs in this group.
        completed_runs: Number of runs that completed (won or game over).
        won_runs: Number of runs that were won.
        averaged_stats: Averaged statistics across all runs.
        stats: List of individual run statistics.
    """

    config: Config

    # Run statistics
    total_runs: int
    completed_runs: int
    won_runs: int

    # Averaged stats
    averaged_stats: AveragedStats

    # Raw stats
    stats: list[RunStats]


class BenchmarkAnalyzer:
    """Analyzes BalatroLLM runs and generates leaderboards.

    Processes structured run data to generate comprehensive performance
    analysis and rankings organized by version and strategy.

    Attributes:
        runs_dir: Directory containing run data to analyze.
        aggregated_data: Dictionary mapping config keys to aggregated run data.
    """

    def __init__(self, runs_dir: Path = Path("runs")):
        """Initialize the benchmark analyzer.

        Args:
            runs_dir: Directory containing run data to analyze (default: 'runs').
        """
        self.runs_dir = runs_dir
        self.aggregated_data: dict[str, RunsData] = {}

    def analyze_all_runs(self) -> None:
        """Analyze all runs in the runs directory.

        Processes all run data in the directory structure and aggregates
        statistics by configuration.

        Raises:
            FileNotFoundError: If the runs directory doesn't exist.
        """
        print("Analyzing all runs...")

        if not self.runs_dir.exists():
            raise FileNotFoundError(f"Runs directory not found: {self.runs_dir}")

        all_run_stats: list[tuple[RunStats, Config]] = []

        for version_dir in self.runs_dir.iterdir():
            if not version_dir.is_dir() or not version_dir.name.startswith("v"):
                continue

            version = version_dir.name[1:]  # Remove 'v' prefix
            run_stats = self._analyze_runs(version_dir, version)
            all_run_stats.extend(run_stats)

        print(f"Analyzed {len(all_run_stats)} runs")
        self._aggregate_data(all_run_stats)

    def _analyze_runs(
        self, version_dir: Path, version: str
    ) -> list[tuple[RunStats, Config]]:
        """Analyze runs using the directory structure: version/strategy/provider/model/run.

        Args:
            version_dir: Directory containing runs for a specific version.
            version: Version string for this directory.

        Returns:
            List of tuples containing (RunStats, Config) for each valid run.
        """
        run_stats = []

        for strategy_dir in version_dir.iterdir():
            if not strategy_dir.is_dir():
                continue

            for provider_dir in strategy_dir.iterdir():
                if not provider_dir.is_dir():
                    continue

                for model_dir in provider_dir.iterdir():
                    if not model_dir.is_dir():
                        continue

                    for run_dir in model_dir.iterdir():
                        if not run_dir.is_dir():
                            continue

                        result = self._load_run_data(run_dir)
                        if result:
                            run_stats.append(result)

        return run_stats

    def _load_run_data(self, run_dir: Path) -> tuple[RunStats, Config] | None:
        """Load data from a single run directory.

        Args:
            run_dir: Directory containing a single run's data files.

        Returns:
            Tuple of (RunStats, Config) if loading succeeds, None if it fails.
        """
        config_file = run_dir / "config.json"
        stats_file = run_dir / "stats.json"

        if not config_file.exists() or not stats_file.exists():
            return None

        try:
            with open(config_file) as f:
                config_dict = json.load(f)
            with open(stats_file) as f:
                stats_dict = json.load(f)

            config = Config(**config_dict)

            stats = RunStats(**stats_dict)
            return stats, config

        except Exception as e:
            print(f"Warning: Error loading {run_dir.name}: {e}")
            return None

    def _aggregate_data(self, all_run_stats: list[tuple[RunStats, Config]]) -> None:
        """Aggregate data by identical config.

        Groups runs by identical configuration and calculates averaged statistics
        for each unique configuration.

        Args:
            all_run_stats: List of (RunStats, Config) tuples from all runs.
        """
        print("Aggregating data...")

        # Group runs by identical config content (excluding run-specific fields)
        grouped_runs = defaultdict(list)
        for stats, config in all_run_stats:
            # Create a config dict without run-specific fields for grouping
            config_dict = {
                "model": config.model,
                "strategy": config.strategy,
                "version": config.version,
            }
            config_key = json.dumps(config_dict, sort_keys=True)
            grouped_runs[config_key].append((stats, config))

        for config_key, run_pairs in grouped_runs.items():
            if not run_pairs:
                continue

            # Get shared config from first run
            _, first_config = run_pairs[0]
            stats_list = [stats for stats, _ in run_pairs]

            # Count runs by completion status
            total_runs = len(run_pairs)
            completed_runs = sum(1 for stats in stats_list if stats.completed)
            won_runs = sum(1 for stats in stats_list if stats.run_won)

            # Calculate averaged stats using the AveragedStats dataclass
            averaged_stats = self._calculate_averaged_stats(stats_list)

            self.aggregated_data[config_key] = RunsData(
                config=first_config,
                total_runs=total_runs,
                completed_runs=completed_runs,
                won_runs=won_runs,
                averaged_stats=averaged_stats,
                stats=stats_list,
            )

        print(f"Aggregated {len(self.aggregated_data)} unique configurations")

    def _calculate_averaged_stats(self, stats_list: list[RunStats]) -> AveragedStats:
        """Calculate averaged stats using the AveragedStats dataclass.

        Args:
            stats_list: List of RunStats to average.

        Returns:
            AveragedStats containing averaged values across all runs.

        Raises:
            ValueError: If stats_list is empty.
        """
        if not stats_list:
            raise ValueError("Cannot calculate averages for empty stats list")

        def avg(field_name: str) -> float:
            """Calculate average for a field across all stats."""
            values = [getattr(s, field_name) for s in stats_list]
            return statistics.mean(values) if values else 0.0

        def avg_len(field_name: str) -> float:
            """Calculate average length of list fields."""
            values = []
            for s in stats_list:
                field_value = getattr(s, field_name)
                if isinstance(field_value, list):
                    values.append(len(field_value))
                elif isinstance(field_value, int):
                    values.append(field_value)  # For numeric counts
                else:
                    values.append(0)
            return statistics.mean(values) if values else 0.0

        return AveragedStats(
            avg_final_round=avg("final_round"),
            avg_ante_reached=avg("ante_reached"),
            avg_jokers_bought=avg_len("jokers_bought"),
            avg_jokers_sold=avg_len("jokers_sold"),
            avg_consumables_used=avg_len("consumables_used"),
            avg_rerolls=avg("rerolls"),
            avg_money_spent=avg("money_spent"),
            avg_successful_calls=avg("successful_calls"),
            avg_error_calls=avg_len("invalid_responses"),
            avg_failed_calls=avg_len("failed_calls"),
            avg_total_input_tokens=avg("total_input_tokens"),
            avg_total_output_tokens=avg("total_output_tokens"),
            avg_total_reasoning_tokens=avg("total_reasoning_tokens"),
            avg_total_tokens=avg("total_tokens"),
            avg_total_response_time_ms=avg("total_response_time_ms"),
        )

    def generate_leaderboard(self, output_dir: Path = Path("benchmarks")) -> None:
        """Generate leaderboard and detailed analysis files organized by version/strategy.

        Creates hierarchical benchmark results with strategy-specific leaderboards
        and individual model performance files.

        Args:
            output_dir: Directory to write benchmark results (default: 'benchmarks').
        """
        print("Generating leaderboard...")

        # Check if output directory exists and ask for confirmation
        if output_dir.exists() and any(output_dir.iterdir()):
            print(f"Output directory '{output_dir}' already exists and contains files.")
            # Check if we're running in a non-interactive environment
            import sys

            if sys.stdin.isatty():
                response = (
                    input("Do you want to overwrite the existing content? (y/N): ")
                    .strip()
                    .lower()
                )
                if response not in ("y", "yes"):
                    print("Benchmark analysis cancelled.")
                    return
            else:
                print("Non-interactive mode: Proceeding with overwrite...")
            print("Proceeding with overwrite...")

        output_dir.mkdir(exist_ok=True)

        # Group data by version and strategy from configs
        version_strategy_groups = defaultdict(lambda: defaultdict(list))
        for runs_data in self.aggregated_data.values():
            config = runs_data.config
            version = config.version
            strategy = config.strategy
            version_strategy_groups[version][strategy].append(runs_data)

        # Process each version
        for version, strategy_groups in version_strategy_groups.items():
            version_dir = output_dir / f"v{version}"
            version_dir.mkdir(exist_ok=True)

            # Process each strategy within the version
            for strategy, data_list in strategy_groups.items():
                strategy_dir = version_dir / strategy
                strategy_dir.mkdir(exist_ok=True)

                # Sort by avg_final_round descending (larger values first)
                sorted_data = sorted(
                    data_list,
                    key=lambda x: x.averaged_stats.avg_final_round,
                    reverse=True,
                )

                # Generate leaderboard entries
                leaderboard_entries = []
                for rank, data in enumerate(sorted_data, 1):
                    # Convert config dataclass to dict for JSON serialization
                    averaged_stats_dict = asdict(data.averaged_stats)
                    # Round all float values in averaged_stats
                    for key, value in averaged_stats_dict.items():
                        if isinstance(value, float):
                            averaged_stats_dict[key] = round(value, 2)

                    entry = {
                        "rank": rank,
                        "config": asdict(data.config),
                        "total_runs": data.total_runs,
                        "completed_runs": data.completed_runs,
                        "won_runs": data.won_runs,
                        "averaged_stats": averaged_stats_dict,
                    }
                    leaderboard_entries.append(entry)

                # Write strategy-specific leaderboard.json
                leaderboard_data = {
                    "generated_at": datetime.now().isoformat(),
                    "version": version,
                    "strategy": strategy,
                    "total_entries": len(leaderboard_entries),
                    "total_runs_analyzed": sum(d.total_runs for d in data_list),
                    "entries": leaderboard_entries,
                }

                leaderboard_file = strategy_dir / "leaderboard.json"
                with open(leaderboard_file, "w") as f:
                    json.dump(leaderboard_data, f, indent=2)

                # Write individual model files using hierarchical structure
                for data in sorted_data:
                    model = data.config.model

                    # Parse provider/model from full model name
                    if "/" in model:
                        provider, model_name = model.split("/", 1)
                        # Make model name filesystem-safe by replacing / with --
                        model_name = model_name.replace("/", "--")
                    else:
                        provider = "unknown"
                        model_name = model

                    # Create provider/model directory structure
                    provider_dir = strategy_dir / provider
                    provider_dir.mkdir(exist_ok=True)

                    model_file = provider_dir / f"{model_name}.json"

                    # Create simplified model data structure using RunsData
                    model_data = asdict(data)

                    # Round all float values in averaged_stats
                    for key, value in model_data["averaged_stats"].items():
                        if isinstance(value, float):
                            model_data["averaged_stats"][key] = round(value, 2)

                    with open(model_file, "w") as f:
                        json.dump(model_data, f, indent=2)

                print(f"Generated strategy leaderboard: {leaderboard_file}")

        # Generate summary statistics
        total_entries = len(self.aggregated_data)
        total_runs = sum(data.total_runs for data in self.aggregated_data.values())

        print(f"Generated benchmark results with {total_entries} unique configurations")
        print(f"Total runs analyzed: {total_runs}")
        print(f"Results organized by version/strategy in: {output_dir}/")

        # Print top performers across all strategies
        all_sorted_data = sorted(
            self.aggregated_data.values(),
            key=lambda x: x.averaged_stats.avg_final_round,
            reverse=True,
        )

        print("\nTop 5 Performers Overall:")
        for i, data in enumerate(all_sorted_data[:5]):
            config = data.config
            model = config.model
            strategy = config.strategy
            version = config.version
            avg_final_round = data.averaged_stats.avg_final_round
            print(
                f"{i + 1}. {model} ({strategy}, v{version}) - "
                f"Avg Final Round: {avg_final_round:.1f}, "
                f"Won Runs: {data.won_runs}/{data.total_runs}"
            )


def run_benchmark_analysis(
    runs_dir: Path = Path("runs"), output_dir: Path = Path("benchmarks")
) -> None:
    """Analyze BalatroLLM runs and generate comprehensive leaderboards.

    Main entry point for benchmark analysis that creates analyzer and
    processes all run data.

    Args:
        runs_dir: Directory containing run data to analyze (default: 'runs').
        output_dir: Directory to write benchmark results (default: 'benchmarks').
    """
    print("BalatroLLM Benchmark Analyzer")
    print(f"Analyzing runs in: {runs_dir}")
    print(f"Output directory: {output_dir}")

    analyzer = BenchmarkAnalyzer(runs_dir)
    analyzer.analyze_all_runs()
    analyzer.generate_leaderboard(output_dir)

    print("\nBenchmark analysis complete!")
