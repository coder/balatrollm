"""Benchmark analysis and leaderboard generation for BalatroLLM runs (v0.3.0+)."""

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class RunMetrics:
    """Metrics extracted from a single run."""

    # Run identification
    version: str
    model: str
    strategy: str
    deck: str
    stake: int
    seed: str
    challenge: str | None

    # Timing and completion
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    completed: bool

    # Game outcome
    won: bool
    final_ante: int
    final_round: int
    final_money: int
    peak_money: int

    # LLM performance
    total_requests: int
    total_responses: int
    success_rate: float
    avg_response_time: float
    total_tokens: int
    avg_tokens_per_request: float

    # Decision metrics
    hands_played: int
    total_chips_scored: int
    avg_chips_per_hand: float
    parsing_errors: int
    timeout_errors: int

    # Strategy-specific metrics
    shop_purchases: int
    jokers_acquired: int
    consumables_used: int
    blinds_skipped: int

    # Raw data for detailed analysis
    raw_config: dict[str, Any] = field(default_factory=dict)
    raw_stats: dict[str, Any] = field(default_factory=dict)
    raw_responses: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a version/model/strategy combination."""

    # Identification
    version: str
    model: str
    strategy: str

    # Run statistics
    total_runs: int
    completed_runs: int
    completion_rate: float

    # Performance aggregates
    avg_duration_seconds: float
    avg_final_ante: float
    avg_final_round: float
    avg_final_money: float
    avg_peak_money: float
    win_rate: float

    # LLM performance aggregates
    avg_success_rate: float
    avg_response_time: float
    avg_total_tokens: float
    avg_tokens_per_request: float

    # Consistency metrics
    std_final_ante: float
    std_final_money: float
    std_duration: float

    # Efficiency metrics
    tokens_per_ante: float
    seconds_per_ante: float
    money_efficiency: float  # peak_money / total_tokens

    # Error rates
    avg_parsing_error_rate: float
    avg_timeout_error_rate: float

    # Strategy metrics
    avg_shop_purchases: float
    avg_jokers_acquired: float
    avg_consumables_used: float
    avg_blinds_skipped: float

    # Performance score (composite metric)
    performance_score: float

    # All individual runs for detailed analysis
    runs: list[RunMetrics] = field(default_factory=list)


@dataclass
class LeaderboardEntry:
    """Single entry in the leaderboard."""

    rank: int
    version: str
    model: str
    strategy: str
    performance_score: float
    win_rate: float
    avg_final_ante: float
    avg_duration_seconds: float
    total_runs: int
    completion_rate: float
    efficiency_rating: str  # S, A, B, C, D based on composite metrics


class BenchmarkAnalyzer:
    """Analyzes BalatroLLM runs and generates leaderboards."""

    def __init__(self, runs_dir: Path = Path("runs")):
        self.runs_dir = runs_dir
        self.run_metrics: list[RunMetrics] = []
        self.aggregated_metrics: dict[tuple[str, str, str], AggregatedMetrics] = {}

    def analyze_all_runs(self) -> None:
        """Analyze all runs in the runs directory."""
        print("Analyzing all runs...")

        if not self.runs_dir.exists():
            raise FileNotFoundError(f"Runs directory not found: {self.runs_dir}")

        run_count = 0
        for version_dir in self.runs_dir.iterdir():
            if not version_dir.is_dir() or not version_dir.name.startswith("v"):
                continue

            version = version_dir.name[1:]  # Remove 'v' prefix

            # Handle hierarchical provider/model structure
            for provider_dir in version_dir.iterdir():
                if not provider_dir.is_dir():
                    continue

                provider = provider_dir.name

                for model_dir in provider_dir.iterdir():
                    if not model_dir.is_dir():
                        continue

                    model_name = model_dir.name
                    # Combine provider and model for full model identifier
                    full_model = f"{provider}/{model_name}"

                    for strategy_dir in model_dir.iterdir():
                        if not strategy_dir.is_dir():
                            continue

                        strategy = strategy_dir.name

                        for run_dir in strategy_dir.iterdir():
                            if not run_dir.is_dir():
                                continue

                            try:
                                metrics = self._analyze_single_run(
                                    run_dir, version, full_model, strategy
                                )
                                if metrics:
                                    self.run_metrics.append(metrics)
                                    run_count += 1
                            except Exception as e:
                                print(f"Warning: Error analyzing {run_dir}: {e}")

        print(f"Analyzed {run_count} runs")
        self._aggregate_metrics()

    def _analyze_single_run(
        self, run_dir: Path, version: str, model: str, strategy: str
    ) -> RunMetrics | None:
        """Analyze a single run directory."""
        config_file = run_dir / "config.json"
        stats_file = run_dir / "stats.json"
        responses_file = run_dir / "responses.jsonl"

        # Require both config and stats files
        if not config_file.exists() or not stats_file.exists():
            return None

        # Load config and stats
        with open(config_file) as f:
            config = json.load(f)

        with open(stats_file) as f:
            stats = json.load(f)

        # Parse run directory name for metadata
        run_name = run_dir.name
        parts = run_name.split("_")
        if len(parts) < 4:
            return None

        deck = parts[1]
        stake_str = parts[2]
        stake = int(stake_str[1:]) if stake_str.startswith("s") else 1
        seed = parts[-1]
        challenge = parts[3] if len(parts) > 4 else None

        # Extract timestamps from stats
        started_at = datetime.fromisoformat(stats["started_at"])
        completed_at_str = stats.get("completed_at")
        completed_at = (
            datetime.fromisoformat(completed_at_str) if completed_at_str else None
        )
        duration_seconds = stats.get("run_duration_seconds")

        # Extract game outcome from stats
        won = stats.get("run_won", False)
        final_ante = stats.get("ante_reached", 0)
        final_round = stats.get("final_round", 0)
        final_money = stats.get("final_money", 0)
        peak_money = stats.get("peak_money_reached", final_money)

        # Extract strategy metrics from stats
        jokers_acquired = stats.get("jokers_acquired", 0)
        consumables_used = stats.get("consumables_used", 0)
        hands_played = stats.get("hands_played_total", 0)
        shop_visits = stats.get("shop_visits", 0)

        # Load and analyze responses for LLM metrics
        responses = []
        if responses_file.exists():
            responses = self._load_jsonl(responses_file)

        llm_metrics = self._extract_llm_metrics(responses, stats)

        return RunMetrics(
            version=version,
            model=model,
            strategy=strategy,
            deck=deck,
            stake=stake,
            seed=seed,
            challenge=challenge,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            completed=stats.get("completed_successfully", False),
            won=won,
            final_ante=final_ante,
            final_round=final_round,
            final_money=final_money,
            peak_money=peak_money,
            total_requests=len(responses),
            total_responses=stats.get("total_responses", len(responses)),
            success_rate=llm_metrics.get("success_rate", 0.0),
            avg_response_time=llm_metrics.get("avg_response_time", 0.0),
            total_tokens=llm_metrics.get("total_tokens", 0),
            avg_tokens_per_request=llm_metrics.get("avg_tokens_per_request", 0.0),
            hands_played=hands_played,
            total_chips_scored=0,  # Not easily extractable from v0.3.0 format
            avg_chips_per_hand=0.0,  # Not easily extractable from v0.3.0 format
            parsing_errors=llm_metrics.get("parsing_errors", 0),
            timeout_errors=llm_metrics.get("timeout_errors", 0),
            shop_purchases=shop_visits,  # Use shop_visits as proxy
            jokers_acquired=jokers_acquired,
            consumables_used=consumables_used,
            blinds_skipped=0,  # Not directly available in stats
            raw_config=config,
            raw_stats=stats,
            raw_responses=responses,
        )

    def _load_jsonl(self, file_path: Path) -> list[dict[str, Any]]:
        """Load JSONL file."""
        data = []
        if file_path.exists():
            with open(file_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        return data

    def _extract_llm_metrics(
        self, responses: list[dict[str, Any]], stats: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract LLM performance metrics from responses and stats."""
        if not responses:
            # Fallback to stats if available
            return {
                "success_rate": 1.0
                - (
                    stats.get("failed_requests", 0)
                    / max(stats.get("total_responses", 1), 1)
                ),
                "avg_response_time": stats.get("average_response_time_ms", 0)
                / 1000.0,  # Convert to seconds
                "total_tokens": 0,  # Not available in stats
                "avg_tokens_per_request": 0.0,
                "parsing_errors": stats.get("failed_requests", 0),
                "timeout_errors": 0,
            }

        # Process responses and count errors
        successful_responses = 0
        total_tokens = 0
        total_response_time = 0
        parsing_errors = 0
        timeout_errors = 0

        for response in responses:
            if self._is_error_response(response):
                error_type = response.get("error", {}).get("code", "")
                if "timeout" in error_type.lower():
                    timeout_errors += 1
                else:
                    parsing_errors += 1
                continue

            successful_responses += 1
            token_usage, response_time = self._extract_response_metrics(response)
            total_tokens += token_usage
            total_response_time += response_time

        return self._calculate_final_metrics(
            len(responses),
            successful_responses,
            total_tokens,
            total_response_time,
            parsing_errors,
            timeout_errors,
        )

    def _is_error_response(self, response: dict[str, Any]) -> bool:
        """Check if response contains an error."""
        return response.get("error") is not None

    def _extract_response_metrics(self, response: dict[str, Any]) -> tuple[int, float]:
        """Extract token usage and response time from a successful response."""
        body = response.get("response", {}).get("body", {})
        usage = body.get("usage", {})
        time_info = body.get("time_info", {})

        token_usage = usage.get("total_tokens", 0)
        response_time = time_info.get("total_time", 0)

        return token_usage, response_time

    def _calculate_final_metrics(
        self,
        total_requests: int,
        successful_responses: int,
        total_tokens: int,
        total_response_time: float,
        parsing_errors: int,
        timeout_errors: int,
    ) -> dict[str, Any]:
        """Calculate final LLM metrics."""
        success_rate = (
            successful_responses / total_requests if total_requests > 0 else 0
        )
        avg_response_time = (
            total_response_time / successful_responses
            if successful_responses > 0
            else 0
        )
        avg_tokens_per_request = (
            total_tokens / successful_responses if successful_responses > 0 else 0
        )

        return {
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "total_tokens": total_tokens,
            "avg_tokens_per_request": avg_tokens_per_request,
            "parsing_errors": parsing_errors,
            "timeout_errors": timeout_errors,
        }

    def _aggregate_metrics(self) -> None:
        """Aggregate metrics by version/model/strategy combination."""
        print("Aggregating metrics...")

        grouped_runs = defaultdict(list)
        for run in self.run_metrics:
            key = (run.version, run.model, run.strategy)
            grouped_runs[key].append(run)

        for (version, model, strategy), runs in grouped_runs.items():
            completed_runs = [r for r in runs if r.completed]

            if not runs:
                continue

            # Calculate aggregated metrics
            total_runs = len(runs)
            completed_count = len(completed_runs)
            completion_rate = completed_count / total_runs

            # Use completed runs for most metrics
            analysis_runs = completed_runs if completed_runs else runs

            # Performance metrics
            final_antes = [r.final_ante for r in analysis_runs]
            final_rounds = [r.final_round for r in analysis_runs]
            final_moneys = [r.final_money for r in analysis_runs]
            peak_moneys = [r.peak_money for r in analysis_runs]
            durations = [
                r.duration_seconds for r in analysis_runs if r.duration_seconds
            ]

            avg_final_ante = statistics.mean(final_antes) if final_antes else 0
            avg_final_round = statistics.mean(final_rounds) if final_rounds else 0
            avg_final_money = statistics.mean(final_moneys) if final_moneys else 0
            avg_peak_money = statistics.mean(peak_moneys) if peak_moneys else 0
            avg_duration = statistics.mean(durations) if durations else 0

            win_rate = (
                sum(1 for r in analysis_runs if r.won) / len(analysis_runs)
                if analysis_runs
                else 0
            )

            # LLM metrics
            success_rates = [r.success_rate for r in analysis_runs]
            response_times = [
                r.avg_response_time for r in analysis_runs if r.avg_response_time > 0
            ]
            total_tokens_list = [r.total_tokens for r in analysis_runs]
            tokens_per_request = [
                r.avg_tokens_per_request
                for r in analysis_runs
                if r.avg_tokens_per_request > 0
            ]

            avg_success_rate = statistics.mean(success_rates) if success_rates else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0
            avg_total_tokens = (
                statistics.mean(total_tokens_list) if total_tokens_list else 0
            )
            avg_tokens_per_req = (
                statistics.mean(tokens_per_request) if tokens_per_request else 0
            )

            # Consistency metrics
            std_final_ante = (
                statistics.stdev(final_antes) if len(final_antes) > 1 else 0
            )
            std_final_money = (
                statistics.stdev(final_moneys) if len(final_moneys) > 1 else 0
            )
            std_duration = statistics.stdev(durations) if len(durations) > 1 else 0

            # Efficiency metrics
            tokens_per_ante = (
                avg_total_tokens / avg_final_ante if avg_final_ante > 0 else 0
            )
            seconds_per_ante = (
                avg_duration / avg_final_ante if avg_final_ante > 0 else 0
            )
            money_efficiency = (
                avg_peak_money / avg_total_tokens if avg_total_tokens > 0 else 0
            )

            # Error rates
            parsing_errors = [r.parsing_errors for r in analysis_runs]
            timeout_errors = [r.timeout_errors for r in analysis_runs]

            avg_parsing_error_rate = (
                statistics.mean(parsing_errors) if parsing_errors else 0
            )
            avg_timeout_error_rate = (
                statistics.mean(timeout_errors) if timeout_errors else 0
            )

            # Strategy metrics
            shop_purchases = [r.shop_purchases for r in analysis_runs]
            jokers_acquired = [r.jokers_acquired for r in analysis_runs]
            consumables_used = [r.consumables_used for r in analysis_runs]
            blinds_skipped = [r.blinds_skipped for r in analysis_runs]

            avg_shop_purchases = (
                statistics.mean(shop_purchases) if shop_purchases else 0
            )
            avg_jokers_acquired = (
                statistics.mean(jokers_acquired) if jokers_acquired else 0
            )
            avg_consumables_used = (
                statistics.mean(consumables_used) if consumables_used else 0
            )
            avg_blinds_skipped = (
                statistics.mean(blinds_skipped) if blinds_skipped else 0
            )

            # Calculate composite performance score
            performance_score = self._calculate_performance_score(
                win_rate,
                avg_final_ante,
                avg_success_rate,
                money_efficiency,
                completion_rate,
            )

            self.aggregated_metrics[(version, model, strategy)] = AggregatedMetrics(
                version=version,
                model=model,
                strategy=strategy,
                total_runs=total_runs,
                completed_runs=completed_count,
                completion_rate=completion_rate,
                avg_duration_seconds=avg_duration,
                avg_final_ante=avg_final_ante,
                avg_final_round=avg_final_round,
                avg_final_money=avg_final_money,
                avg_peak_money=avg_peak_money,
                win_rate=win_rate,
                avg_success_rate=avg_success_rate,
                avg_response_time=avg_response_time,
                avg_total_tokens=avg_total_tokens,
                avg_tokens_per_request=avg_tokens_per_req,
                std_final_ante=std_final_ante,
                std_final_money=std_final_money,
                std_duration=std_duration,
                tokens_per_ante=tokens_per_ante,
                seconds_per_ante=seconds_per_ante,
                money_efficiency=money_efficiency,
                avg_parsing_error_rate=avg_parsing_error_rate,
                avg_timeout_error_rate=avg_timeout_error_rate,
                avg_shop_purchases=avg_shop_purchases,
                avg_jokers_acquired=avg_jokers_acquired,
                avg_consumables_used=avg_consumables_used,
                avg_blinds_skipped=avg_blinds_skipped,
                performance_score=performance_score,
                runs=runs,
            )

        print(f"Aggregated {len(self.aggregated_metrics)} unique combinations")

    def _calculate_performance_score(
        self,
        win_rate: float,
        avg_final_ante: float,
        success_rate: float,
        money_efficiency: float,
        completion_rate: float,
    ) -> float:
        """Calculate composite performance score (0-100)."""
        # Normalize components to 0-1 scale
        win_component = win_rate  # Already 0-1
        ante_component = min(avg_final_ante / 8, 1)  # Normalize to win ante (8)
        success_component = success_rate  # Already 0-1
        efficiency_component = min(money_efficiency / 100, 1)  # Arbitrary scaling
        completion_component = completion_rate  # Already 0-1

        # Weighted combination
        score = (
            win_component * 30  # 30% weight on winning
            + ante_component * 25  # 25% weight on progression
            + success_component * 20  # 20% weight on LLM reliability
            + efficiency_component * 15  # 15% weight on efficiency
            + completion_component * 10  # 10% weight on completion
        )

        return score

    def _get_efficiency_rating(self, metrics: AggregatedMetrics) -> str:
        """Get efficiency rating (S/A/B/C/D) based on composite metrics."""
        score = metrics.performance_score

        if score >= 80:
            return "S"
        elif score >= 65:
            return "A"
        elif score >= 50:
            return "B"
        elif score >= 35:
            return "C"
        else:
            return "D"

    def generate_leaderboard(
        self, output_dir: Path = Path("benchmark_results")
    ) -> None:
        """Generate leaderboard and detailed analysis files organized by version/strategy."""
        print("Generating leaderboard...")

        # Check if output directory exists and ask for confirmation
        if output_dir.exists() and any(output_dir.iterdir()):
            print(f"Output directory '{output_dir}' already exists and contains files.")
            response = (
                input("Do you want to overwrite the existing content? (y/N): ")
                .strip()
                .lower()
            )
            if response not in ("y", "yes"):
                print("Benchmark analysis cancelled.")
                return
            print("Proceeding with overwrite...")

        output_dir.mkdir(exist_ok=True)

        # Group metrics by version and strategy
        version_strategy_groups = defaultdict(lambda: defaultdict(list))
        for metrics in self.aggregated_metrics.values():
            version_strategy_groups[metrics.version][metrics.strategy].append(metrics)

        # Process each version
        for version, strategy_groups in version_strategy_groups.items():
            version_dir = output_dir / f"v{version}"
            version_dir.mkdir(exist_ok=True)

            # Process each strategy within the version
            for strategy, metrics_list in strategy_groups.items():
                strategy_dir = version_dir / strategy
                strategy_dir.mkdir(exist_ok=True)

                # Sort metrics within this strategy by average final round reached
                sorted_metrics = sorted(
                    metrics_list,
                    key=lambda x: x.avg_final_round,
                    reverse=True,
                )

                # Generate strategy-specific leaderboard entries
                leaderboard_entries = []
                for rank, metrics in enumerate(sorted_metrics, 1):
                    entry = LeaderboardEntry(
                        rank=rank,
                        version=metrics.version,
                        model=metrics.model,
                        strategy=metrics.strategy,
                        performance_score=metrics.performance_score,
                        win_rate=metrics.win_rate,
                        avg_final_ante=metrics.avg_final_ante,
                        avg_duration_seconds=metrics.avg_duration_seconds,
                        total_runs=metrics.total_runs,
                        completion_rate=metrics.completion_rate,
                        efficiency_rating=self._get_efficiency_rating(metrics),
                    )
                    leaderboard_entries.append(entry)

                # Write strategy-specific leaderboard.json
                leaderboard_data = {
                    "generated_at": datetime.now().isoformat(),
                    "version": version,
                    "strategy": strategy,
                    "total_entries": len(leaderboard_entries),
                    "total_runs_analyzed": sum(m.total_runs for m in metrics_list),
                    "entries": [
                        {
                            "rank": entry.rank,
                            "model": entry.model,
                            "performance_score": round(entry.performance_score, 2),
                            "win_rate": round(entry.win_rate, 3),
                            "avg_final_ante": round(entry.avg_final_ante, 2),
                            "avg_duration_seconds": round(
                                entry.avg_duration_seconds, 1
                            ),
                            "total_runs": entry.total_runs,
                            "completion_rate": round(entry.completion_rate, 3),
                            "efficiency_rating": entry.efficiency_rating,
                        }
                        for entry in leaderboard_entries
                    ],
                }

                leaderboard_file = strategy_dir / "leaderboard.json"
                with open(leaderboard_file, "w") as f:
                    json.dump(leaderboard_data, f, indent=2)

                # Write individual model files within the strategy directory
                for metrics in sorted_metrics:
                    model_filename = metrics.model.replace("/", "-") + ".json"
                    model_file = strategy_dir / model_filename

                    model_data = {
                        "version": metrics.version,
                        "model": metrics.model,
                        "strategy": metrics.strategy,
                        "name": metrics.runs[0].raw_config.get("name", "Unknown Name"),
                        "description": metrics.runs[0].raw_config.get(
                            "description", "Unknown Description"
                        ),
                        "author": metrics.runs[0].raw_config.get(
                            "author", "BalatroBench"
                        ),
                        "tags": metrics.runs[0].raw_config.get("tags", []),
                        "summary": {
                            "performance_score": round(metrics.performance_score, 2),
                            "efficiency_rating": self._get_efficiency_rating(metrics),
                            "total_runs": metrics.total_runs,
                            "completed_runs": metrics.completed_runs,
                            "completion_rate": round(metrics.completion_rate, 3),
                        },
                        "performance_metrics": {
                            "win_rate": round(metrics.win_rate, 3),
                            "avg_final_ante": round(metrics.avg_final_ante, 2),
                            "avg_final_money": round(metrics.avg_final_money, 1),
                            "avg_peak_money": round(metrics.avg_peak_money, 1),
                            "avg_duration_seconds": round(
                                metrics.avg_duration_seconds, 1
                            ),
                        },
                        "llm_metrics": {
                            "avg_success_rate": round(metrics.avg_success_rate, 3),
                            "avg_response_time": round(metrics.avg_response_time, 3),
                            "avg_total_tokens": round(metrics.avg_total_tokens, 1),
                            "avg_tokens_per_request": round(
                                metrics.avg_tokens_per_request, 1
                            ),
                            "avg_parsing_error_rate": round(
                                metrics.avg_parsing_error_rate, 3
                            ),
                            "avg_timeout_error_rate": round(
                                metrics.avg_timeout_error_rate, 3
                            ),
                        },
                        "consistency_metrics": {
                            "std_final_ante": round(metrics.std_final_ante, 2),
                            "std_final_money": round(metrics.std_final_money, 1),
                            "std_duration": round(metrics.std_duration, 1),
                        },
                        "efficiency_metrics": {
                            "tokens_per_ante": round(metrics.tokens_per_ante, 1),
                            "seconds_per_ante": round(metrics.seconds_per_ante, 1),
                            "money_efficiency": round(metrics.money_efficiency, 4),
                        },
                        "strategy_metrics": {
                            "avg_shop_purchases": round(metrics.avg_shop_purchases, 1),
                            "avg_jokers_acquired": round(
                                metrics.avg_jokers_acquired, 1
                            ),
                            "avg_consumables_used": round(
                                metrics.avg_consumables_used, 1
                            ),
                            "avg_blinds_skipped": round(metrics.avg_blinds_skipped, 1),
                        },
                        "individual_runs": [
                            {
                                "seed": run.seed,
                                "deck": run.deck,
                                "stake": run.stake,
                                "completed": run.completed,
                                "won": run.won,
                                "final_ante": run.final_ante,
                                "final_money": run.final_money,
                                "peak_money": run.peak_money,
                                "duration_seconds": run.duration_seconds,
                                "total_tokens": run.total_tokens,
                                "success_rate": round(run.success_rate, 3),
                                "parsing_errors": run.parsing_errors,
                                "timeout_errors": run.timeout_errors,
                            }
                            for run in metrics.runs
                        ],
                    }

                    with open(model_file, "w") as f:
                        json.dump(model_data, f, indent=2)

                print(f"Generated strategy leaderboard: {leaderboard_file}")

        # Generate global summary statistics
        total_entries = len(self.aggregated_metrics)
        total_runs = len(self.run_metrics)

        print(
            f"Generated benchmark results with {total_entries} model/strategy combinations"
        )
        print(f"Total runs analyzed: {total_runs}")
        print(f"Results organized by version/strategy in: {output_dir}/")

        # Print top performers across all strategies for immediate feedback
        all_sorted_metrics = sorted(
            self.aggregated_metrics.values(),
            key=lambda x: x.avg_final_round,
            reverse=True,
        )

        print("\nTop 5 Performers Overall:")
        for i, metrics in enumerate(all_sorted_metrics[:5]):
            print(
                f"{i + 1}. {metrics.model} ({metrics.strategy}, v{metrics.version}) - "
                f"Score: {metrics.performance_score:.1f}, "
                f"Win Rate: {metrics.win_rate:.1%}, "
                f"Avg Round: {metrics.avg_final_round:.1f}"
            )


def run_benchmark_analysis(
    runs_dir: Path = Path("runs"), output_dir: Path = Path("benchmark_results")
) -> None:
    """Analyze BalatroLLM runs and generate comprehensive leaderboards."""
    print("BalatroLLM Benchmark Analyzer")
    print(f"Analyzing runs in: {runs_dir}")
    print(f"Output directory: {output_dir}")

    analyzer = BenchmarkAnalyzer(runs_dir)
    analyzer.analyze_all_runs()
    analyzer.generate_leaderboard(output_dir)

    print("\nBenchmark analysis complete!")
