"""Core LLM-powered Balatro bot implementation."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from balatrobot.enums import State
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    ContentFilterFinishReasonError,
    LengthFinishReasonError,
)
from openai.types.chat import ChatCompletion

from balatrobot import BalatroClient, BalatroError

from .config import Config, load_model_config
from .data_collection import ChatCompletionError, ChatCompletionResponse, StatsCollector
from .strategies import StrategyManager

logger = logging.getLogger(__name__)


def setup_logging(log_file: Path | None = None) -> None:
    """Configure logging for the application.

    Sets up both console and optional file logging with consistent formatting.

    Args:
        log_file: Optional path to write log output to a file. If None,
            only console logging is configured.
    """
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

        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


class LLMBotError(Exception):
    """Base class for exceptions raised by the LLMBot class."""

    pass


class LLMBot:
    """LLM-powered Balatro bot.

    Manages game state processing, LLM communication, and strategy execution
    for automated Balatro gameplay.

    Attributes:
        config: Bot configuration containing model and strategy settings.
        llm_client: AsyncOpenAI client for LLM communication.
        balatro_client: BalatroClient for game interaction.
        strategy_manager: Manager for loading and rendering strategy templates.
        responses: List of LLM responses for memory and debugging.
        tools: Game state-specific tool definitions loaded from strategy.
        data_collector: Collector for structured run data and statistics.
        consecutive_failed_calls: Counter for consecutive failed/error calls.
        max_consecutive_failed_calls: Threshold for stopping the run (3 consecutive failed calls).
    """

    def __init__(self, config: Config, base_url: str, api_key: str, port: int = 12346):
        """Initialize the LLM bot.

        Args:
            config: Bot configuration containing model and strategy settings.
            base_url: Base URL for OpenAI compatible API.
            api_key: API key for authentication.
            port: Port for BalatroBot client connection.
        """
        self.config = config
        self.model_config = load_model_config(config.model)

        self.llm_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.balatro_client = BalatroClient(port=port)
        self.strategy_manager = StrategyManager(config.strategy)
        self.responses: list[ChatCompletion] = []
        self.tools = self.strategy_manager.load_tools()
        self.data_collector: StatsCollector

        # The last response is not a valid tool call (e.g. simple LLM text response)
        # We need to keep track that in order to notify the LLM for the next request.
        self.last_error_call_msg: str | None = None

        # The last tool call is a valid tool call but a BalatroError occurred
        # (e.g. play hand with 6 cards)
        self.last_failed_call_msg: str | None = None

        # Counter for consecutive failed/error calls. Prenvent infinite loop.
        self.error_or_failed_calls: int = 0
        self.max_error_or_failed_calls: int = 3

    def __enter__(self):
        self.balatro_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.balatro_client.disconnect()

    async def list_available_models(self) -> list[str]:
        """Get list of available models from the API.

        Returns:
            List of model IDs available from the API.
            Returns empty list if request fails.
        """
        try:
            models = await self.llm_client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    async def get_llm_response(self, game_state: dict) -> ChatCompletion:
        """Get LLM response for current game state.

        Renders strategy templates and makes LLM request with appropriate tools
        for the current game state.

        Args:
            game_state: Current game state dictionary from BalatroClient.

        Returns:
            ChatCompletion response from the LLM.

        Raises:
            Exception: If LLM request fails after all retries.
        """
        state_name = State(game_state["state"]).name

        # Generate prompts
        user_content = "\n\n".join(
            [
                self.strategy_manager.render_strategy(game_state),
                self.strategy_manager.render_gamestate(game_state),
                self.strategy_manager.render_memory(
                    self.responses,
                    self.last_error_call_msg,
                    self.last_failed_call_msg,
                ),
            ]
        )
        messages = [{"role": "user", "content": user_content}]
        tools = self.tools[state_name]

        # Make LLM request with retries
        return await self._make_llm_request_with_retries(messages, tools)

    async def _make_llm_request_with_retries(
        self, messages: list, tools: list, max_retries: int = 3
    ) -> ChatCompletion:
        """Make LLM request with exponential backoff retry logic.

        Args:
            messages: List of chat messages to send to the LLM.
            tools: List of tool definitions available for this game state.
            max_retries: Maximum number of retry attempts (default: 3).

        Returns:
            ChatCompletion response from the LLM.

        Raises:
            Exception: If all retry attempts fail.
        """
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                request_data = {
                    "model": self.config.model,
                    "messages": messages,
                    "tools": tools,
                }
                for key, value in self.model_config.items():
                    request_data[key] = value

                custom_id = self.data_collector.write_request(request_data)
                request_id = str(time.time_ns() // 1_000_000)
                response = await self.llm_client.chat.completions.create(**request_data)
                self.responses.append(response)
                self.balatro_client.screenshot(
                    self.data_collector.screenshot_dir / f"{custom_id}.png"
                )
                self.data_collector.write_response(
                    id=str(time.time_ns() // 1_000_000),
                    custom_id=custom_id,
                    response=ChatCompletionResponse(
                        request_id=request_id,
                        status_code=200,
                        body=response.to_dict(),
                    ),
                )
                return response

            except APITimeoutError as e:
                logger.error(e)
                self.data_collector.write_response(
                    id=str(time.time_ns() // 1_000_000),
                    custom_id=custom_id,
                    error=ChatCompletionError(
                        code="timeout",
                        message=str(e),
                    ),
                )

            except APIConnectionError as e:
                logger.error(e)
                self.data_collector.write_response(
                    id=str(time.time_ns() // 1_000_000),
                    custom_id=custom_id,
                    error=ChatCompletionError(
                        code="connection",
                        message=str(e),
                    ),
                )

            except APIStatusError as e:
                logger.error(e)
                self.data_collector.write_response(
                    id=str(time.time_ns() // 1_000_000),
                    custom_id=custom_id,
                    response=ChatCompletionResponse(
                        request_id=request_id,
                        status_code=e.status_code,
                        body={},
                    ),
                )

            except LengthFinishReasonError as e:
                logger.error(e)
                self.data_collector.write_response(
                    id=str(time.time_ns() // 1_000_000),
                    custom_id=custom_id,
                    response=ChatCompletionResponse(
                        request_id=request_id,
                        status_code=200,
                        body=e.completion.to_dict(),
                    ),
                    error=ChatCompletionError(
                        code="length",
                        message=str(e),
                    ),
                )

            except ContentFilterFinishReasonError as e:
                logger.error(e)
                self.data_collector.write_response(
                    id=str(time.time_ns() // 1_000_000),
                    custom_id=custom_id,
                    error=ChatCompletionError(
                        code="content_filter",
                        message=str(e),
                    ),
                )

            logger.warning(
                f"Retrying in {retry_delay} seconds [{attempt + 1}/{max_retries}]"
            )
            await asyncio.sleep(retry_delay)
            retry_delay *= 2

        # This should never be reached due to raise in the exception handler
        raise RuntimeError("All retry attempts exhausted without raising exception")

    def _error_call(self, msg):
        logger.warning(msg)
        self.last_error_call_msg = msg
        self.error_or_failed_calls += 1
        self.data_collector.call_stats.error += 1
        self.data_collector.call_stats.total += 1
        if self.error_or_failed_calls >= self.max_error_or_failed_calls:
            raise LLMBotError("Too many consecutive error/failed calls")
        return self.balatro_client.send_message("get_game_state", {})

    def _failed_call(self, msg):
        logger.warning(msg)
        self.last_failed_call_msg = msg
        self.error_or_failed_calls += 1
        self.data_collector.call_stats.failed += 1
        self.data_collector.call_stats.total += 1
        if self.error_or_failed_calls >= self.max_error_or_failed_calls:
            raise LLMBotError("Too many consecutive error/failed calls")
        return self.balatro_client.send_message("get_game_state", {})

    def process_and_execute_tool_call(self, response: ChatCompletion) -> dict[str, Any]:
        message = response.choices[0].message

        # Check that the response is not an error call

        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return self._error_call(f"No tool calls in LLM response: {message}")

        tool_call = message.tool_calls[0]
        function_obj = getattr(tool_call, "function", tool_call)

        fn_name = getattr(function_obj, "name", None)
        if not fn_name:
            return self._error_call("Invalid tool call: missing name")

        fn_args_str = getattr(function_obj, "arguments", None)
        if not fn_args_str:
            return self._error_call("Invalid tool call: missing arguments")

        try:
            fn_args = json.loads(fn_args_str)
        except json.JSONDecodeError as e:
            return self._error_call(f"Invalid JSON in tool call arguments: {e}")

        self.error_or_failed_calls = 0
        self.last_error_call_msg = None

        # Check that the response is not a failed call

        try:
            logger.info(f"Executing tool call: {fn_name} with arguments: {fn_args}")
            result = self.balatro_client.send_message(fn_name, fn_args)
        except BalatroError as e:
            return self._failed_call(f"Error executing tool call: {e}")

        self.last_failed_call_msg = None
        self.error_or_failed_calls = 0
        self.data_collector.call_stats.successful += 1
        self.data_collector.call_stats.total += 1

        return result

    async def _init_game(self, base_dir: Path = Path.cwd()) -> dict[str, Any]:
        """Initialize a new game run with data collection setup.

        Creates run directory, sets up data collection, configures logging,
        and starts a new Balatro game run.

        Args:
            base_dir: Base directory for storing run data (default: current directory).

        Returns:
            Initial game state dictionary from starting the run.
        """
        self.data_collector = StatsCollector(self.config, base_dir)
        self.config.to_config_file(self.data_collector.run_dir / "config.json")
        logger.info(f"Run data will be saved to: {self.data_collector.run_dir}")

        # Set up logging to write to run.log file
        log_path = self.data_collector.run_dir / "run.log"
        setup_logging(log_file=log_path)
        logger.info(f"Game log will be saved to: {log_path}")

        start_run_args = {
            "deck": self.config.deck,
            "stake": self.config.stake,
            "seed": self.config.seed,
            "challenge": self.config.challenge,
            "log_path": self.data_collector.run_dir / "gamestates.jsonl",
        }

        return self.balatro_client.send_message("start_run", start_run_args)

    async def _run_game_loop(self, game_state: dict[str, Any]) -> None:
        """Main game loop that processes game states until completion.

        Continuously processes game states, making LLM decisions and executing
        actions until the game ends.

        Args:
            game_state: Initial game state dictionary to start processing.
        """
        while True:
            current_state = State(game_state["state"])
            logger.info(f"Current state: {current_state}")

            match current_state:
                case State.SELECTING_HAND | State.SHOP:
                    response = await self.get_llm_response(game_state)
                    game_state = self.process_and_execute_tool_call(response)
                case State.ROUND_EVAL:
                    await asyncio.sleep(0.5)
                    game_state = self.balatro_client.send_message("cash_out")
                case State.BLIND_SELECT:
                    await asyncio.sleep(0.5)
                    game_state = self.balatro_client.send_message(
                        "skip_or_select_blind", arguments={"action": "select"}
                    )
                case State.GAME_OVER:
                    logger.info("Game over!")
                    break
                case _:
                    await asyncio.sleep(1)
                    game_state = self.balatro_client.send_message("get_game_state")

    async def play_game(self, runs_dir: Path = Path.cwd()) -> None:
        """Main game loop.

        Initializes a new game and runs the main game loop until completion
        or interruption.

        Args:
            runs_dir: Base directory for storing run data (default: current directory).

        Raises:
            Exception: If game loop fails due to unexpected errors.
        """
        logger.info("Starting LLM bot game loop")

        try:
            game_state = await self._init_game(base_dir=runs_dir)
            await self._run_game_loop(game_state)

        except KeyboardInterrupt:
            logger.info("Game interrupted by user")

        except LLMBotError as e:
            logger.error(f"Game stopped: {e}")
            raise

        except Exception as e:
            logger.error(f"Game loop failed: {e}")
            raise

        finally:
            self.data_collector.write_stats()
