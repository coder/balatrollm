"""BalatroLLM CLI module."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from .bot import LLMBot, setup_logging
from .config import Config


def main() -> None:
    """Main CLI entry point for balatrollm.

    Parses command line arguments and executes the game.
    """
    parser = _create_argument_parser()
    args = parser.parse_args()

    setup_logging()
    asyncio.run(cmd_balatrollm(args))


async def cmd_balatrollm(args) -> None:
    """Run the balatrollm command.

    Creates a bot configuration and runs the main game loop.

    Args:
        args: Parsed command line arguments containing model, strategy,
            base_url, api_key, config file path, runs count, and other options.
    """
    # Validate runs argument
    if args.runs_per_seed < 1:
        print("Error: --runs-per-seed must be at least 1")
        sys.exit(1)

    # Handle port default value
    ports = args.port if args.port else [12346]

    if args.config:
        config = Config.from_config_file(args.config)
    else:
        config = Config(
            model=args.model,
            strategy=args.strategy,
            take_screenshots=args.take_screenshots,
            use_default_paths=args.use_default_paths,
        )

    # Parse seeds
    seeds = args.seeds.split(",") if args.seeds else [config.seed]

    # Create a bot for model listing (using first port)
    if args.list_models:
        bot = LLMBot(
            config, base_url=args.base_url, api_key=args.api_key, port=ports[0]
        )
        models = await bot.list_available_models()
        for model in models:
            print(model)
        return

    # Create work queue with (seed, run_number) pairs
    work_queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
    for seed in seeds:
        for run_number in range(1, args.runs_per_seed + 1):
            work_queue.put_nowait((seed, run_number))

    total_runs = len(seeds) * args.runs_per_seed
    print(
        f"Running {total_runs} total runs ({len(seeds)} seeds × {args.runs_per_seed} runs/seed) "
        f"across {len(ports)} ports (dynamic allocation):"
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
                total_runs,
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
    work_queue: asyncio.Queue[tuple[str, int]],
    config: Config,
    base_url: str,
    api_key: str,
    port: int,
    runs_dir: Path,
    total_runs: int,
) -> None:
    """Worker that pulls runs from queue and executes them on assigned port.

    Args:
        work_queue: Queue containing (seed, run_number) tuples to process.
        config: Bot configuration template.
        base_url: OpenAI-compatible API base URL.
        api_key: API key.
        port: Port number for this worker.
        runs_dir: Directory for storing run data.
        total_runs: Total number of runs (for progress display).
    """
    while True:
        try:
            # Get next run from queue (non-blocking)
            seed, run_number = work_queue.get_nowait()
        except asyncio.QueueEmpty:
            # No more work available
            print(f"Port {port}: No more work, shutting down")
            break

        print(f"\n=== Port {port} - Seed {seed}, Run {run_number}/{total_runs} ===")

        # Create config with specific seed for this run
        run_config = Config(
            model=config.model,
            strategy=config.strategy,
            seed=seed,
            take_screenshots=config.take_screenshots,
            use_default_paths=config.use_default_paths,
        )

        # Create bot for this run
        bot = LLMBot(run_config, base_url=base_url, api_key=api_key, port=port)

        try:
            with bot:
                await bot.play_game(runs_dir=runs_dir)
            print(f"Port {port} - Seed {seed}, Run {run_number} completed successfully")
        except KeyboardInterrupt:
            print(f"\nPort {port} interrupted during seed {seed}, run {run_number}")
            # Put the run back in queue for potential retry by another worker
            work_queue.put_nowait((seed, run_number))
            raise
        except Exception as e:
            print(f"Port {port} - Seed {seed}, Run {run_number} failed: {e}")
            # Continue to next run (don't put failed run back in queue)

        # Mark this work as done
        work_queue.task_done()

        # Brief pause between runs on same port
        await asyncio.sleep(1)


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Sets up command line argument parsing for the balatrollm command.

    Returns:
        Configured ArgumentParser instance with all options.
    """
    parser = argparse.ArgumentParser(
        description="LLM-powered Balatro bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-m",
        "--model",
        default="openai/gpt-oss-20b",
        help="Model name to use from OpenAI-compatible API (default: openai/gpt-oss-20b)",
    )
    parser.add_argument(
        "-l",
        "--list-models",
        action="store_true",
        help="List available models from OpenAI-compatible API and exit",
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
        help="OpenAI-compatible API base URL (default: https://openrouter.ai/api/v1)",
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
        "--runs-per-seed",
        type=int,
        default=1,
        dest="runs_per_seed",
        help="Number of runs per seed (default: 1)",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma-separated list of seeds (e.g., AAAA123,BBBB456,CCCC789)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        action="append",
        help="Port for BalatroBot client connection (can specify multiple, default: 12346)",
    )
    parser.add_argument(
        "--no-screenshot",
        action="store_false",
        dest="take_screenshots",
        help="Disable taking screenshots during gameplay",
    )
    parser.add_argument(
        "--use-default-paths",
        action="store_true",
        help="Use BalatroBot's default storage paths for screenshots and game logs",
    )

    return parser
