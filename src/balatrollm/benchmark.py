import json
import re
import statistics
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from tqdm import tqdm

from balatrollm.config import Config, StrategyManifest
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
    runs: list[str]
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
    strategy: StrategyManifest | None


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
        self.benchmark_dir = benchmark_dir

    def analyze_all_runs(self) -> None:
        for version_dir in self.runs_dir.iterdir():
            if version_dir.is_dir():
                if re.match(r"^v[0-9]+\.[0-9]+\.[0-9]+$", version_dir.name):
                    for strategy_dir in version_dir.iterdir():
                        if strategy_dir.is_dir():
                            self.analyze_strategy_runs(strategy_dir)

    def analyze_version_by_models(self, version_dir: Path) -> None:
        """Analyze a single version by comparing models within each strategy.

        Args:
            version_dir: Path to version directory (e.g., runs/v0.13.2)
        """
        if not version_dir.is_dir():
            raise FileNotFoundError(f"Version directory not found: {version_dir}")

        for strategy_dir in version_dir.iterdir():
            if strategy_dir.is_dir():
                self.analyze_strategy_runs(strategy_dir)

    def analyze_version_by_strategies(self, version_dir: Path) -> None:
        """Analyze a single version by comparing strategies for each model.

        Args:
            version_dir: Path to version directory (e.g., runs/v0.13.2)
        """
        if not version_dir.is_dir():
            raise FileNotFoundError(f"Version directory not found: {version_dir}")

        # Collect all model_dirs with their strategy associations
        models_by_key: dict[
            str, list[tuple[Path, str]]
        ] = {}  # key -> [(model_dir, strategy)]

        for strategy_dir in version_dir.iterdir():
            if not strategy_dir.is_dir():
                continue
            strategy_name = strategy_dir.name

            for vendor_dir in strategy_dir.iterdir():
                if not vendor_dir.is_dir():
                    continue

                for model_dir in vendor_dir.iterdir():
                    if not model_dir.is_dir():
                        continue

                    # Create a unique key for this model (vendor/model)
                    model_key = f"{vendor_dir.name}/{model_dir.name}"
                    if model_key not in models_by_key:
                        models_by_key[model_key] = []
                    models_by_key[model_key].append((model_dir, strategy_name))

        # For each model, analyze strategies
        for model_key, model_dirs_with_strategies in models_by_key.items():
            vendor_name, model_name = model_key.split("/", 1)
            self._analyze_model_strategies(
                model_dirs_with_strategies, vendor_name, model_name
            )

    def _analyze_model_strategies(
        self,
        model_dirs_with_strategies: list[tuple[Path, str]],
        vendor: str,
        model: str,
    ) -> None:
        """Analyze strategies for a specific model.

        Args:
            model_dirs_with_strategies: List of (model_dir, strategy_name) tuples
            vendor: Vendor name (e.g., openrouter)
            model: Model name (e.g., openai/gpt-oss-20b)
        """
        models_stats = []

        for model_dir, strategy_name in model_dirs_with_strategies:
            model_stats = self.compute_model_stats(model_dir)
            models_stats.append((model_stats, strategy_name))

            # Save individual model stats
            output_dir = self.benchmark_dir / vendor / model / strategy_name
            model_stats_path = output_dir / "stats.json"
            model_stats_path.parent.mkdir(exist_ok=True, parents=True)
            stats_dict = asdict(model_stats)
            stats_dict["config"].pop("seed")
            with open(model_stats_path, "w") as f:
                json.dump(stats_dict, f, indent=2)

            # Create detailed run directories
            self.create_detailed_run_dirs(model_dir, output_dir)

        # Create leaderboard comparing strategies
        output_dir = self.benchmark_dir / vendor / model
        output_dir.mkdir(parents=True, exist_ok=True)

        strategy_stats = [stats for stats, _ in models_stats]
        leaderboard = self.compute_models_leaderboard(strategy_stats)
        leaderboard_path = output_dir / "leaderboard.json"
        with open(leaderboard_path, "w") as f:
            json.dump(asdict(leaderboard), f, indent=2)

    def analyze_strategy_runs(self, strategy_dir: Path) -> None:
        models_stats = []
        output_dir = self.benchmark_dir / strategy_dir.relative_to(self.runs_dir)
        for vendor_dir in strategy_dir.iterdir():
            if not vendor_dir.is_dir():
                continue
            for model_dir in vendor_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                model_stats = self.compute_model_stats(model_dir)
                models_stats.append(model_stats)
                model_stats_path = (
                    output_dir / vendor_dir.name / f"{model_dir.name}.json"
                )
                model_stats_path.parent.mkdir(exist_ok=True, parents=True)
                stats_dict = asdict(model_stats)
                stats_dict["config"].pop("seed")
                with open(model_stats_path, "w") as f:
                    json.dump(stats_dict, f, indent=2)

                # Create detailed run directories
                detailed_output_dir = output_dir / vendor_dir.name
                self.create_detailed_run_dirs(model_dir, detailed_output_dir)

        # Ensure output directory exists before writing leaderboard
        output_dir.mkdir(parents=True, exist_ok=True)
        leaderboard = self.compute_models_leaderboard(models_stats)
        leaderboard_path = output_dir / "leaderboard.json"
        with open(leaderboard_path, "w") as f:
            json.dump(asdict(leaderboard), f, indent=2)

    def compute_model_stats(self, model_dir: Path) -> ModelStatsFull:
        stats: list[Stats] = []
        configs: list[Config] = []
        strategies: list[StrategyManifest] = []
        run_names: list[str] = []
        for run_dir in model_dir.iterdir():
            if not run_dir.is_dir():
                continue

            # Skip runs that don't have required files
            stats_file = run_dir / "stats.json"
            config_file = run_dir / "config.json"
            strategy_file = run_dir / "strategy.json"
            if not stats_file.exists() or not config_file.exists():
                print(f"Skipping incomplete run: {run_dir.name}")
                continue

            with open(stats_file, "r") as f:
                stats.append(Stats.from_dict(json.load(f)))
            with open(config_file, "r") as f:
                configs.append(Config(**json.load(f)))

            # Load strategy manifest if available
            if strategy_file.exists():
                with open(strategy_file, "r") as f:
                    strategy_data = json.load(f)
                    strategies.append(StrategyManifest(**strategy_data))
            else:
                # Fallback: try to load from strategies directory
                try:
                    strategies.append(
                        StrategyManifest.from_manifest_file(configs[-1].strategy)
                    )
                except FileNotFoundError:
                    print(
                        f"Warning: Could not find strategy manifest for {configs[-1].strategy}"
                    )
                    continue

            run_names.append(run_dir.name)

        config = configs[0]
        strategy = strategies[0] if strategies else None

        for c in configs[1:]:
            # Compare all fields except seed (seeds can differ for multi-seed runs)
            assert (
                c.model == config.model
                and c.strategy == config.strategy
                and c.deck == config.deck
                and c.stake == config.stake
                and c.challenge == config.challenge
            ), f"Configs differ (excluding seed): {c} vs {config}"

        # Validate that all strategy manifests are identical
        if strategy is not None:
            for s in strategies[1:]:
                assert (
                    s.name == strategy.name
                    and s.description == strategy.description
                    and s.author == strategy.author
                    and s.version == strategy.version
                    and s.tags == strategy.tags
                ), f"Strategy manifests differ: {s} vs {strategy}"

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
            # total number of calls across all stats
            N = calls.total
            if N <= 1:
                return 0.0

            overall_mean = getattr(average, attr)

            numerator = 0.0
            for stat in stats:
                s_i = getattr(stat.std_dev, attr)  # group's sample std
                mean_i = getattr(stat.average, attr)  # group's mean
                n_i = stat.calls.total

                # within-group contribution: (n_i - 1) * s_i^2
                # between-group contribution: n_i * (mean_i - overall_mean)^2
                numerator += (n_i - 1) * (s_i**2) + n_i * ((mean_i - overall_mean) ** 2)

            pooled_var = numerator / (N - 1)
            return pooled_var**0.5

        std_dev = ModelAggregatedStats(
            tot_std_dev("input_tokens"),
            tot_std_dev("output_tokens"),
            tot_std_dev("input_cost"),
            tot_std_dev("output_cost"),
            tot_std_dev("total_cost"),
            tot_std_dev("time_ms"),
        )

        return ModelStatsFull(
            runs=run_names,
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
            strategy=strategy,
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

    def _convert_single_png(self, png_file: Path) -> None:
        """Convert a single PNG file to AVIF."""
        try:
            subprocess.run(
                [
                    "cavif",
                    "--overwrite",
                    "--quality=60",
                    "--speed=1",
                    "--quiet",
                    str(png_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            png_file.unlink()
        except subprocess.CalledProcessError as e:
            print(f"Warning: cavif conversion failed for {png_file}: {e.stderr}")
        except OSError as e:
            print(f"Warning: Could not remove {png_file}: {e}")

    def convert_pngs_to_avif(self, directory: Path) -> None:
        """Convert all PNG files in directory to AVIF using cavif with parallelization."""
        try:
            png_files = list(directory.rglob("screenshot.png"))
            if not png_files:
                return

            with ThreadPoolExecutor(max_workers=8) as executor:
                list(
                    tqdm(
                        executor.map(self._convert_single_png, png_files),
                        total=len(png_files),
                        desc="Converting to AVIF",
                    )
                )
        except FileNotFoundError:
            print("Warning: cavif not found, keeping PNG format")
        except Exception as e:
            print(f"Warning: cavif conversion error in {directory}: {e}")

    def extract_request_content(self, requests_file: Path) -> dict[str, str]:
        """Extract request content from requests.jsonl by custom_id."""
        content_by_id = {}
        if not requests_file.exists():
            return content_by_id

        with open(requests_file) as f:
            for line in f:
                data = json.loads(line.strip())
                custom_id = data.get("custom_id")
                if custom_id and "body" in data and "messages" in data["body"]:
                    messages = data["body"]["messages"]
                    if messages and len(messages) > 0:
                        content = messages[0].get("content", "")
                        if isinstance(content, list):
                            # Handle multimodal content: extract text from each item
                            text_parts = [
                                item.get("text", "")
                                for item in content
                                if "text" in item
                            ]
                            content_by_id[custom_id] = (
                                "\n".join(text_parts) or "Content not available"
                            )
                        else:
                            # Handle simple string content
                            content_by_id[custom_id] = (
                                content or "Content not available"
                            )
        return content_by_id

    def extract_reasoning_from_tool_calls(self, tool_calls: list) -> str:
        """Extract reasoning from tool call arguments if available.

        Looks for a "reasoning" field in the parsed arguments of tool calls.
        Returns the first reasoning found, or empty string if none found.
        """
        for tool_call in tool_calls:
            if "function" in tool_call:
                function = tool_call["function"]
                if "arguments" in function:
                    try:
                        # arguments is a JSON string that needs to be parsed
                        args = json.loads(function["arguments"])
                        if "reasoning" in args and args["reasoning"]:
                            return args["reasoning"]
                    except (json.JSONDecodeError, TypeError):
                        # Skip if arguments can't be parsed as JSON
                        continue
        return ""

    def extract_response_data(self, responses_file: Path) -> dict[str, dict]:
        """Extract reasoning and tool_call from responses.jsonl by custom_id."""
        response_by_id = {}
        if not responses_file.exists():
            return response_by_id

        with open(responses_file) as f:
            for line in f:
                data = json.loads(line.strip())
                custom_id = data.get("custom_id")
                if custom_id and "response" in data and "body" in data["response"]:
                    body = data["response"]["body"]
                    if "choices" in body and len(body["choices"]) > 0:
                        choice = body["choices"][0]
                        message = choice.get("message", {})

                        tool_calls = message.get("tool_calls", [])
                        # Try explicit reasoning first, then fall back to tool call arguments
                        reasoning = message.get(
                            "reasoning", ""
                        ) or self.extract_reasoning_from_tool_calls(tool_calls)

                        response_data = {
                            "reasoning": reasoning,
                            "tool_call": tool_calls,
                        }
                        response_by_id[custom_id] = response_data
        return response_by_id

    def create_detailed_run_dirs(self, model_dir: Path, output_dir: Path) -> None:
        """Create detailed run directories with extracted data."""
        model_name = model_dir.name
        detailed_model_dir = output_dir / model_name

        for run_dir in model_dir.iterdir():
            if not run_dir.is_dir():
                continue

            run_name = run_dir.name
            detailed_run_dir = detailed_model_dir / run_name

            # Extract request and response data
            requests_file = run_dir / "requests.jsonl"
            responses_file = run_dir / "responses.jsonl"
            screenshots_dir = run_dir / "screenshots"

            request_content = self.extract_request_content(requests_file)
            response_data = self.extract_response_data(responses_file)

            # Process each custom_id
            all_custom_ids = set(request_content.keys()) | set(response_data.keys())

            for custom_id in all_custom_ids:
                custom_id_dir = detailed_run_dir / custom_id
                custom_id_dir.mkdir(parents=True, exist_ok=True)

                # Write request.md
                if custom_id in request_content:
                    with open(custom_id_dir / "request.md", "w") as f:
                        f.write(request_content[custom_id])

                # Write reasoning.md and tool_call.json
                if custom_id in response_data:
                    data = response_data[custom_id]

                    with open(custom_id_dir / "reasoning.md", "w") as f:
                        f.write(data["reasoning"])

                    with open(custom_id_dir / "tool_call.json", "w") as f:
                        json.dump(data["tool_call"], f, indent=2)

                # Copy screenshot
                if screenshots_dir.exists():
                    png_file = screenshots_dir / f"{custom_id}.png"
                    if png_file.exists():
                        screenshot_dest = custom_id_dir / "screenshot.png"
                        screenshot_dest.write_bytes(png_file.read_bytes())

    def generate_manifest(self, base_dir: Path, current_version: str) -> None:
        """Generate manifest.json tracking available benchmark versions.

        Scans base_dir for all version directories (v*.*.* pattern),
        sorts them semantically in descending order, and marks the
        current version as latest.

        Args:
            base_dir: Base directory containing version subdirectories
                     (e.g., benchmarks/models or benchmarks/strategies)
            current_version: Current version string from __version__
        """
        if not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)

        # Find all version directories
        versions = []
        version_pattern = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

        for item in base_dir.iterdir():
            if item.is_dir():
                match = version_pattern.match(item.name)
                if match:
                    major, minor, patch = map(int, match.groups())
                    versions.append((item.name, (major, minor, patch)))

        # Sort versions in descending order (newest first)
        versions.sort(key=lambda x: x[1], reverse=True)

        # Create manifest entries
        manifest_entries = []
        for version_str, _ in versions:
            entry = {"version": version_str}
            if version_str == f"v{current_version}":
                entry["latest"] = True
            manifest_entries.append(entry)

        # Write manifest.json
        manifest = {"versions": manifest_entries}
        manifest_path = base_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
