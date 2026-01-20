"""CLI entry point for balatrollm command."""

import argparse
import asyncio
import sys
from pathlib import Path

from .config import Config, Task


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="balatrollm",
        description="LLM-powered Balatro bot",
    )

    # Positional config file (optional)
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        help="Config file path (YAML)",
    )

    # Game params (nargs='+' for lists)
    parser.add_argument("--model", nargs="+", help="Model(s) to use")
    parser.add_argument("--seed", nargs="+", help="Game seed(s)")
    parser.add_argument("--deck", nargs="+", help="Deck code(s): RED, BLUE, etc.")
    parser.add_argument("--stake", nargs="+", help="Stake code(s): WHITE, GOLD, etc.")
    parser.add_argument("--strategy", nargs="+", help="Strategy name(s)")

    # Execution
    parser.add_argument("--parallel", type=int, help="Concurrent instances")

    # Connection
    parser.add_argument("--host", help="BalatroBot host")
    parser.add_argument("--port", type=int, help="Starting port")
    parser.add_argument("--base-url", help="LLM API base URL")
    parser.add_argument("--api-key", help="LLM API key")

    # CLI-only
    parser.add_argument("--dry-run", action="store_true", help="Show tasks only")
    parser.add_argument(
        "--views", action="store_true", help="Start HTTP server on port 12345 for views"
    )

    return parser


def print_tasks(tasks: list[Task]) -> None:
    """Print task list for dry run."""
    total = len(tasks)
    for i, task in enumerate(tasks, 1):
        print(f"[{i:0{len(str(total))}d}/{total}] {task}")


async def execute(config: Config, tasks: list[Task]) -> int:
    """Execute all tasks. Returns exit code."""
    from .executor import Executor
    from .views import ViewsServer

    views_server: ViewsServer | None = None
    if config.views:
        # Serve from project root (where views/ and runs/ are located)
        project_root = Path.cwd()
        views_server = ViewsServer(root_dir=project_root)
        views_server.start()

    executor = Executor(config=config, tasks=tasks)

    try:
        await executor.run()
        return 0
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Execution failed: {e}")
        return 1
    finally:
        if views_server:
            views_server.stop()


def main() -> None:
    """Main entry point for balatrollm command."""
    parser = create_parser()
    args = parser.parse_args()

    # Build config with precedence: env < yaml < args
    try:
        config = Config.load(yaml_path=args.config, args=args)
        config.validate()
    except (FileNotFoundError, ValueError) as e:
        parser.error(str(e))

    # Generate tasks
    tasks = config.generate_tasks()

    # Dry run?
    if args.dry_run:
        print_tasks(tasks)
        return

    # Execute
    try:
        exit_code = asyncio.run(execute(config, tasks))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
