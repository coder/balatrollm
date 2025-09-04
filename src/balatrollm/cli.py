"""BalatroLLM CLI module."""

import argparse
import asyncio
import os
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

    # Handle port default value
    ports = args.port if args.port else [12346]

    if args.config:
        config = Config.from_config_file(args.config)
    else:
        config = Config(
            model=args.model,
            strategy=args.strategy,
        )

    # Create a bot for model listing (using first port)
    if args.list_models:
        bot = LLMBot(
            config, base_url=args.base_url, api_key=args.api_key, port=ports[0]
        )
        models = await bot.list_available_models()
        for model in models:
            print(model)
        return

    # Create work queue with all run numbers
    work_queue: asyncio.Queue[int] = asyncio.Queue()
    for run_number in range(1, args.runs + 1):
        work_queue.put_nowait(run_number)

    print(
        f"Running {args.runs} total runs across {len(ports)} ports (dynamic allocation):"
    )
    for port in ports:
        print(f"  Port {port}: available")

    # Create worker tasks - one per port
    workers = []
    for port in ports:
        worker = asyncio.create_task(
            _port_worker(
                work_queue,
                config,
                args.base_url,
                args.api_key,
                port,
                args.runs_dir,
                args.runs,
            )
        )
        workers.append(worker)

    # Run all workers in parallel
    try:
        await asyncio.gather(*workers)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        # Cancel remaining workers
        for worker in workers:
            if not worker.done():
                worker.cancel()
        # Wait for cancellation to complete
        await asyncio.gather(*workers, return_exceptions=True)


async def _port_worker(
    work_queue: asyncio.Queue[int],
    config: Config,
    base_url: str,
    api_key: str,
    port: int,
    runs_dir: Path,
    total_runs: int,
) -> None:
    """Worker that pulls runs from queue and executes them on assigned port.

    Args:
        work_queue: Queue containing run numbers to process.
        config: Bot configuration.
        base_url: LiteLLM base URL.
        api_key: LiteLLM API key.
        port: Port number for this worker.
        runs_dir: Directory for storing run data.
        total_runs: Total number of runs (for progress display).
    """
    while True:
        try:
            # Get next run from queue (non-blocking)
            run_number = work_queue.get_nowait()
        except asyncio.QueueEmpty:
            # No more work available
            print(f"Port {port}: No more work, shutting down")
            break

        print(f"\n=== Port {port} - Run {run_number}/{total_runs} ===")

        # Create bot for this run
        bot = LLMBot(config, base_url=base_url, api_key=api_key, port=port)

        try:
            with bot:
                await bot.play_game(runs_dir=runs_dir)
            print(f"Port {port} - Run {run_number} completed successfully")
        except KeyboardInterrupt:
            print(f"\nPort {port} interrupted during run {run_number}")
            # Put the run back in queue for potential retry by another worker
            work_queue.put_nowait(run_number)
            raise
        except Exception as e:
            print(f"Port {port} - Run {run_number} failed: {e}")
            # Continue to next run (don't put failed run back in queue)

        # Mark this work as done
        work_queue.task_done()

        # Brief pause between runs on same port
        await asyncio.sleep(1)


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
        description="LLM-powered Balatro bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default command (play game) - no subcommand needed, just use main parser
    parser.add_argument(
        "-m",
        "--model",
        default="openai/gpt-oss-20b",
        help="Model name to use from OpenRouter (default: openai/gpt-oss-20b)",
    )
    parser.add_argument(
        "-l",
        "--list-models",
        action="store_true",
        help="List available models from OpenRouter and exit",
    )
    parser.add_argument(
        "-s",
        "--strategy",
        default="default",
        type=str,
        help="Name of the strategy to use (default: default)",
    )
    parser.add_argument(
        "-u",
        "--base-url",
        default="https://openrouter.ai/api/v1",
        help="OpenAI API base URL (default: https://openrouter.ai/api/v1)",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        default=os.getenv("OPENROUTER_API_KEY"),
        help="API key (default: OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Load configuration from a previous run's config.json file",
    )
    parser.add_argument(
        "-d",
        "--runs-dir",
        type=lambda p: Path(p).resolve(),
        default=Path.cwd().resolve(),
        help="Base directory for storing run data (default: current directory)",
    )
    parser.add_argument(
        "-r",
        "--runs",
        type=int,
        default=1,
        help="Number of times to run the bot with the same configuration (default: 1)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        action="append",
        help="Port for BalatroBot client connection (can specify multiple, default: 12346)",
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
