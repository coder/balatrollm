"""BalatroLLM project."""

__version__ = "0.6.0"

import argparse
import asyncio
import sys
from pathlib import Path

from .benchmark import run_benchmark_analysis
from .bot import LLMBot, setup_logging
from .config import Config


def main() -> None:
    """Main CLI entry point for balatrollm.

    Parses command line arguments and executes the appropriate command.
    Supports both the main balatrollm command and benchmark subcommand.
    """
    parser = _create_argument_parser()
    args = parser.parse_args()

    setup_logging()

    match args.command:
        case "benchmark":
            cmd_benchmark(args)
        case None:
            asyncio.run(cmd_balatrollm(args))
        case _:
            print(f"Unknown command: {args.command}")
            sys.exit(1)


async def cmd_balatrollm(args) -> None:
    """Run the balatrollm command.

    Creates a bot configuration and runs the main game loop.

    Args:
        args: Parsed command line arguments containing model, strategy,
            base_url, api_key, config file path, runs count, and other options.
    """
    # Validate runs argument
    if args.runs < 1:
        print("Error: --runs must be at least 1")
        sys.exit(1)

    if args.config:
        config = Config.from_config_file(args.config)
    else:
        config = Config(
            model=args.model,
            strategy=args.strategy,
        )

    bot = LLMBot(config, base_url=args.base_url, api_key=args.api_key)

    if args.list_models:
        models = await bot.list_available_models()
        for model in models:
            print(model)
        return

    # Run the bot multiple times
    for run_number in range(1, args.runs + 1):
        if args.runs > 1:
            print(f"\n=== Run {run_number}/{args.runs} ===")

        try:
            with bot:
                await bot.play_game(runs_dir=args.runs_dir)
        except KeyboardInterrupt:
            print(f"\nInterrupted after {run_number - 1} completed runs")
            break
        except Exception as e:
            print(f"Run {run_number} failed: {e}")
            if args.runs > 1:
                print("Continuing to next run...")
            else:
                raise

        # Sleep between runs to prevent errors
        if run_number < args.runs:
            print("Waiting 3 seconds before next run...")
            await asyncio.sleep(3)


def cmd_benchmark(args) -> None:
    """Run the benchmark command.

    Analyzes run data and generates comprehensive leaderboards.

    Args:
        args: Parsed command line arguments containing runs_dir and output_dir.

    Raises:
        FileNotFoundError: If the runs directory doesn't exist.
        Exception: If benchmark analysis fails for any other reason.
    """
    try:
        run_benchmark_analysis(args.runs_dir, args.output_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Benchmark analysis failed: {e}")
        sys.exit(1)


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Sets up command line argument parsing for both the main balatrollm
    command and the benchmark subcommand.

    Returns:
        Configured ArgumentParser instance with all commands and options.
    """
    parser = argparse.ArgumentParser(
        description="LLM-powered Balatro bot using LiteLLM proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default command (play game) - no subcommand needed, just use main parser
    parser.add_argument(
        "--model",
        default="cerebras/gpt-oss-120b",
        help="Model name to use from LiteLLM proxy (default: cerebras/gpt-oss-120b)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models from the proxy and exit",
    )
    parser.add_argument(
        "--strategy",
        default="default",
        type=str,
        help="Name of the strategy to use (default: default)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:4000",
        help="LiteLLM base URL (default: http://localhost:4000)",
    )
    parser.add_argument(
        "--api-key",
        default="sk-balatrollm-proxy-key",
        help="LiteLLM proxy API key (default: sk-balatrollm-proxy-key)",
    )
    parser.add_argument(
        "--config",
        help="Load configuration from a previous run's config.json file",
    )
    parser.add_argument(
        "--runs-dir",
        type=lambda p: Path(p).resolve(),
        default=Path.cwd().resolve(),
        help="Base directory for storing run data (default: current directory)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of times to run the bot with the same configuration (default: 1)",
    )

    # Benchmark subcommand
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Analyze runs and generate leaderboards",
        description="Analyze BalatroLLM runs and generate comprehensive leaderboards",
    )
    benchmark_parser.add_argument(
        "--runs-dir",
        type=lambda p: Path(p).resolve(),
        default=Path("runs").resolve(),
        help="Directory containing run data (default: runs)",
    )
    benchmark_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks"),
        help="Output directory for benchmark results (default: benchmarks)",
    )

    return parser
