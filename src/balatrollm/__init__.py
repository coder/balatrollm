"""BalatroLLM project."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from .llm import Config, LLMBot, setup_logging


def main() -> None:
    """Main CLI entry point for balatrollm."""
    parser = argparse.ArgumentParser(
        description="LLM-powered Balatro bot using LiteLLM proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  balatrollm --model cerebras-gpt-oss-120b
  balatrollm --model groq-qwen32b --proxy-url http://localhost:4000
  balatrollm --list-models
        """,
    )

    parser.add_argument(
        "--model",
        default=os.getenv("LITELLM_MODEL", "cerebras-qwen3-235b"),
        help="Model name to use from LiteLLM proxy (default: cerebras-qwen3-235b)",
    )

    parser.add_argument(
        "--proxy-url",
        default=os.getenv("LITELLM_PROXY_URL", "http://localhost:4000"),
        help="LiteLLM proxy URL (default: http://localhost:4000)",
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
        "--config",
        default="config/litellm.yaml",
        help="Path to LiteLLM configuration file (default: config/litellm.yaml)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    import logging

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"LiteLLM config file not found: {config_path}")
        logger.error("Please create the config file or start the proxy manually:")
        logger.error(f"  litellm --config {config_path}")
        sys.exit(1)

    # Create and run the bot
    asyncio.run(run_bot(args))


async def run_bot(args) -> None:
    """Run the Balatro bot with the given arguments."""
    config = Config(
        model=args.model,
        proxy_url=args.proxy_url,
        api_key=args.api_key,
        template="default",  # Default template, could be made configurable
    )
    bot = LLMBot(config)

    # List models if requested
    if args.list_models:
        print("Checking available models from LiteLLM proxy...")
        if not await bot.validate_proxy_connection():
            print(f"❌ Cannot connect to LiteLLM proxy at {args.proxy_url}")
            print(f"Please start the proxy with: litellm --config {args.config}")
            sys.exit(1)

        models = await bot.list_available_models()
        if models:
            print("✅ Available models:")
            for model in models:
                print(f"  - {model}")
        else:
            print("❌ No models available or failed to retrieve models")
        return

    # Validate proxy connection and model before starting game
    print(f"🤖 Starting Balatro LLM Bot with model: {args.model}")

    if not await bot.validate_proxy_connection():
        print(f"❌ Cannot connect to LiteLLM proxy at {args.proxy_url}")
        print(f"Please start the proxy with: litellm --config {args.config}")
        sys.exit(1)

    if not await bot.validate_model_exists():
        print(f"❌ Model '{args.model}' not available")
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
