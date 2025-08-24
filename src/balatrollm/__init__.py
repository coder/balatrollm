"""BalatroLLM project."""

__version__ = "0.2.0"

import argparse
import asyncio
import os
import sys
from pathlib import Path

from .benchmark import run_benchmark_analysis
from .bot import LLMBot, setup_logging
from .config import Config


def main() -> None:
    """Main CLI entry point for balatrollm."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    _setup_logging(args.verbose)

    # Handle benchmark command
    if args.command == "benchmark":
        _run_benchmark_command(args)
        return

    # Only validate config file for game commands
    _validate_config_file(args.litellm_config)
    asyncio.run(run_bot(args))


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="LLM-powered Balatro bot using LiteLLM proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  balatrollm --model cerebras-gpt-oss-120b
  balatrollm --model groq-qwen32b --base-url http://localhost:4000
  balatrollm --strategy aggressive
  balatrollm --strategy /path/to/my/custom/strategy
  balatrollm --strategy ../custom-strategies/experimental
  balatrollm --list-models
  balatrollm --from-config runs/v0.2.0/cerebras-qwen3-235b/default/20250824_145835_RedDeck_s1_OOOO155/config.json
  balatrollm benchmark --runs-dir runs --output-dir benchmark_results
        """,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default command (play game) - no subcommand needed, just use main parser
    parser.add_argument(
        "--model",
        default=os.getenv("LITELLM_MODEL", "cerebras-qwen3-235b"),
        help="Model name to use from LiteLLM proxy (default: cerebras-qwen3-235b)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
        help="LiteLLM base URL (default: http://localhost:4000)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("LITELLM_API_KEY", "sk-balatrollm-proxy-key"),
        help="LiteLLM proxy API key (default: sk-balatrollm-proxy-key)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models from the proxy and exit",
    )
    parser.add_argument(
        "--litellm-config",
        default="config/litellm.yaml",
        help="Path to LiteLLM configuration file (default: config/litellm.yaml)",
    )
    parser.add_argument(
        "--strategy",
        default=os.getenv("BALATROLLM_STRATEGY", "default"),
        help="Strategy to use. Can be a built-in strategy name (default, aggressive) or a path to a strategy directory (default: default)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--from-config",
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
        default=Path("benchmark_results"),
        help="Output directory for benchmark results (default: benchmark_results)",
    )

    return parser


def _setup_logging(verbose: bool) -> None:
    """Configure application logging."""
    setup_logging(verbose)


def _run_benchmark_command(args) -> None:
    """Run the benchmark analysis command."""
    try:
        run_benchmark_analysis(args.runs_dir, args.output_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Benchmark analysis failed: {e}")
        sys.exit(1)


def _validate_config_file(config_path: str) -> None:
    """Validate LiteLLM config file exists."""
    import logging

    config_file = Path(config_path)
    if not config_file.exists():
        logger = logging.getLogger(__name__)
        logger.error(f"LiteLLM config file not found: {config_file}")
        logger.error("Please create the config file or start the proxy manually:")
        logger.error(f"  litellm --config {config_file}")
        sys.exit(1)


async def run_bot(args) -> None:
    """Run the Balatro bot with the given arguments."""
    if args.from_config:
        config = Config.from_config_file(args.from_config)
    else:
        config = Config(
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            strategy=args.strategy,
        )
    bot = LLMBot(config, verbose=args.verbose)

    if args.list_models:
        await _list_models(bot, args)
        return

    await _start_game(bot, args)


async def _list_models(bot: LLMBot, args) -> None:
    """List available models and exit."""
    print("Checking available models from LiteLLM proxy...")

    if not await bot.validate_proxy_connection():
        print(f"❌ Cannot connect to LiteLLM proxy at {bot.config.base_url}")
        print(f"Please start the proxy with: litellm --config {args.litellm_config}")
        sys.exit(1)

    models = await bot.list_available_models()
    if models:
        print("✅ Available models:")
        for model in models:
            print(f"  - {model}")
    else:
        print("❌ No models available or failed to retrieve models")


async def _start_game(bot: LLMBot, args) -> None:
    """Start the game after validation."""
    print(f"🤖 Starting Balatro LLM Bot with model: {bot.config.model}")

    # Validate connections
    if not await bot.validate_proxy_connection():
        print(f"❌ Cannot connect to LiteLLM proxy at {bot.config.base_url}")
        print(f"Please start the proxy with: litellm --config {args.litellm_config}")
        sys.exit(1)

    if not await bot.validate_model_exists():
        print(f"❌ Model '{bot.config.model}' not available")
        print("Use --list-models to see available models")
        sys.exit(1)

    print("✅ Proxy connection validated, starting game...")

    try:
        with bot:
            await bot.play_game()
    except KeyboardInterrupt:
        print("\n🛑 Game interrupted by user")
    except Exception as e:
        print(f"❌ Game failed: {e}")
        sys.exit(1)
