"""BalatroLLM project."""

__version__ = "0.3.0"

import argparse
import asyncio
import sys
from pathlib import Path

from .benchmark import run_benchmark_analysis
from .bot import LLMBot, setup_logging
from .config import Config


def main() -> None:
    """Main CLI entry point for balatrollm."""
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
    """Run the balatrollm command."""

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

    else:
        with bot:
            await bot.play_game()


def cmd_benchmark(args) -> None:
    """Run the benchmark command."""
    try:
        run_benchmark_analysis(args.runs_dir, args.output_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Benchmark analysis failed: {e}")
        sys.exit(1)


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
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

    # Benchmark subcommand
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Analyze runs and generate leaderboards",
        description="Analyze BalatroLLM runs and generate comprehensive leaderboards",
    )
    benchmark_parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="Directory containing run data (default: runs)",
    )
    benchmark_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks"),
        help="Output directory for benchmark results (default: benchmarks)",
    )

    return parser
