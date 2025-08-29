"""Core LLM-powered Balatro bot implementation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from balatrobot import BalatroClient
from balatrobot.enums import State

from .config import Config
from .data_collection import RunStatsCollector, generate_run_directory
from .strategies import StrategyManager

logger = logging.getLogger(__name__)


def setup_logging(log_file: Path | None = None) -> None:
    """Configure logging for the application."""
    level = logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if log_file is provided
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="w")  # 'w' to overwrite
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


class LLMBot:
    """LLM-powered Balatro bot."""

    def __init__(self, config: Config, base_url: str, api_key: str):
        self.config = config
        self.llm_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.balatro_client = BalatroClient()
        self.strategy_manager = StrategyManager(config.strategy)
        self.responses: list[ChatCompletion] = []
        self.tools = self.strategy_manager.load_tools()
        self.data_collector: RunStatsCollector

    def __enter__(self):
        self.balatro_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.balatro_client.disconnect()

    async def list_available_models(self) -> list[str]:
        """Get list of available models from the LiteLLM proxy."""
        try:
            models = await self.llm_client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    async def get_llm_response(self, game_state: dict):
        """Get LLM response for current game state."""
        state_name = State(game_state["state"]).name

        # Generate prompts
        user_content = "\n\n".join(
            [
                self.strategy_manager.render_strategy(),
                self.strategy_manager.render_gamestate(state_name, game_state),
                self.strategy_manager.render_memory(self.responses),
            ]
        )
        messages = [{"role": "user", "content": user_content}]
        tools = self.tools[state_name]

        # Make LLM request with retries
        return await self._make_llm_request_with_retries(messages, tools)

    async def _make_llm_request_with_retries(
        self, messages: list, tools: list, max_retries: int = 3
    ):
        """Make LLM request with exponential backoff retry logic."""
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                request_data = {
                    "model": self.config.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "extra_body": {"allowed_openai_params": ["reasoning_effort"]},
                }
                request_id = self.data_collector.write_request(request_data)

                response = await self.llm_client.chat.completions.create(**request_data)

                self.responses.append(response)
                if self.data_collector and request_id:
                    self.data_collector.write_response(request_id, response)
                return response

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"LLM decision failed after {max_retries} attempts: {e}"
                    )
                    if self.data_collector and request_id:
                        self.data_collector.write_response(
                            request_id, error=e, status_code=500
                        )
                    raise

                logger.warning(
                    f"LLM attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

    def process_and_execute_tool_call(self, response) -> dict[str, Any]:
        """Extract tool call from LLM response and execute it."""
        if not response.choices:
            raise ValueError("No response choices returned from LLM")

        message = response.choices[0].message
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            logger.warning(f"No tool calls in LLM response: {message}")
            raise ValueError("No tool calls in LLM response")

        # Extract function details from first tool call
        tool_call = message.tool_calls[0]
        function_obj = getattr(tool_call, "function", tool_call)
        function_name = getattr(function_obj, "name", None)
        function_args_str = getattr(function_obj, "arguments", None)

        if not function_name or not function_args_str:
            raise ValueError("Invalid tool call: missing name or arguments")

        # Parse JSON arguments
        try:
            arguments = json.loads(function_args_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tool call arguments: {e}") from e

        # Execute tool call
        logger.info(f"Executing tool call: {function_name} with arguments: {arguments}")
        result = self.balatro_client.send_message(function_name, arguments)

        if not isinstance(result, dict):
            logger.warning(
                f"Unexpected result type from balatro_client: {type(result)}"
            )

        return result

    async def _init_game(self) -> dict[str, Any]:
        """Initialize a new game run with data collection setup."""

        # Generate run directory
        run_dir = generate_run_directory(self.config)
        logger.info(f"Run data will be saved to: {run_dir}")

        self.config.to_config_file(run_dir / "config.json")
        self.data_collector = RunStatsCollector(run_dir=run_dir, config=self.config)

        # Set up logging to write to run.log file
        log_path = run_dir / "run.log"
        setup_logging(log_file=log_path)
        logger.info(f"Game log will be saved to: {log_path}")

        start_run_args = {
            "deck": self.config.deck,
            "stake": self.config.stake,
            "seed": self.config.seed,
            "challenge": self.config.challenge,
            "log_path": run_dir / "gamestates.jsonl",
        }

        return self.balatro_client.send_message("start_run", start_run_args)

    async def _run_game_loop(self, game_state: dict[str, Any]) -> None:
        """Main game loop that processes game states until completion."""
        while True:
            current_state = State(game_state["state"])
            logger.info(f"Current state: {current_state}")

            match current_state:
                case (
                    State.BLIND_SELECT
                    | State.SELECTING_HAND
                    | State.ROUND_EVAL
                    | State.SHOP
                ):
                    response = await self.get_llm_response(game_state)
                    game_state = self.process_and_execute_tool_call(response)
                case State.GAME_OVER:
                    logger.info("Game over!")
                    break
                case _:
                    await asyncio.sleep(1)
                    game_state = self.balatro_client.send_message("get_game_state")

    async def play_game(self) -> None:
        """Main game loop.

        Args:
            deck: Deck name to use
            stake: Stake level (1-8)
            seed: Seed for run generation
            challenge: Optional challenge name
        """
        logger.info("Starting LLM bot game loop")

        try:
            game_state = await self._init_game()
            await self._run_game_loop(game_state)

        except KeyboardInterrupt:
            logger.info("Game interrupted by user")

        except Exception as e:
            logger.error(f"Game loop failed: {e}")
            raise

        finally:
            self.data_collector.write_stats()
