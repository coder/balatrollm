"""Core LLM-powered Balatro bot implementation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from balatrobot import BalatroClient, BalatroError
from balatrobot.enums import State

from .config import Config
from .data_collection import RunStatsCollector, generate_run_directory
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

        file_handler = logging.FileHandler(log_file, mode="w")  # 'w' to overwrite
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


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
    """

    def __init__(self, config: Config, base_url: str, api_key: str):
        """Initialize the LLM bot.

        Args:
            config: Bot configuration containing model and strategy settings.
            base_url: Base URL for the LiteLLM proxy server.
            api_key: API key for LiteLLM proxy authentication.
        """
        self.config = config
        self.llm_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.balatro_client = BalatroClient()
        self.strategy_manager = StrategyManager(config.strategy)
        self.responses: list[ChatCompletion] = []
        self.tools = self.strategy_manager.load_tools()
        self.data_collector: RunStatsCollector

        # The last response is not a valid tool call (e.g. simple LLM text response)
        # We need to keep track that in order to notify the LLM for the next request.
        self.last_response_is_invalid: str | None = None

        # The last tool call is a valid tool call but an BotError occurred
        # (e.g. play hand with 6 cards)
        self.last_tool_called_failed: str | None = None

    def __enter__(self):
        self.balatro_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.balatro_client.disconnect()

    async def list_available_models(self) -> list[str]:
        """Get list of available models from the LiteLLM proxy.

        Returns:
            List of model IDs available from the proxy.
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
                self.strategy_manager.render_strategy(),
                self.strategy_manager.render_gamestate(state_name, game_state),
                self.strategy_manager.render_memory(
                    self.responses,
                    self.last_response_is_invalid,
                    self.last_tool_called_failed,
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

        # This should never be reached due to raise in the exception handler
        raise RuntimeError("All retry attempts exhausted without raising exception")

    def process_and_execute_tool_call(self, response: ChatCompletion) -> dict[str, Any]:
        """Extract tool call from LLM response and execute it.

        Parses the first tool call from the LLM response and executes it
        via the BalatroClient.

        Args:
            response: ChatCompletion response containing tool calls.

        Returns:
            Dictionary containing the result from executing the tool call.

        Raises:
            ValueError: If response has no tool calls or invalid format.
            json.JSONDecodeError: If tool call arguments are invalid JSON.
        """
        if not response.choices:
            raise ValueError("No response choices returned from LLM")

        message = response.choices[0].message

        # Check if response has tool calls. If not, just return the current game state
        # The data_collector will count the number of invalid tool call responses
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            msg = f"No tool calls in LLM response: {message}"
            self.last_response_is_invalid = msg
            logger.warning(msg)
            result = self.balatro_client.send_message("get_game_state", {})
            return result

        # Extract function details from first tool call
        tool_call = message.tool_calls[0]
        function_obj = getattr(tool_call, "function", tool_call)
        function_name = getattr(function_obj, "name", None)
        function_args_str = getattr(function_obj, "arguments", None)

        if not function_name or not function_args_str:
            msg = "Invalid tool call: missing name or arguments"
            self.last_response_is_invalid = msg
            logger.warning("Invalid tool call: missing name or arguments")
            result = self.balatro_client.send_message("get_game_state", {})
            return result

        # Parse JSON arguments
        try:
            arguments = json.loads(function_args_str)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in tool call arguments: {e}"
            self.last_response_is_invalid = msg
            logger.warning(msg)
            result = self.balatro_client.send_message("get_game_state", {})
            return result

        self.last_response_is_invalid = None

        # Execute tool call
        logger.info(f"Executing tool call: {function_name} with arguments: {arguments}")

        try:
            result = self.balatro_client.send_message(function_name, arguments)

        except BalatroError as e:
            msg = f"Error executing tool call: {e}"
            self.last_tool_called_failed = msg
            self.data_collector.failed_calls.append(str(e))
            logger.warning(f"Error executing tool call: {e}")
            result = self.balatro_client.send_message("get_game_state", {})
            return result

        self.last_tool_called_failed = None
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

        # Generate run directory
        run_dir = generate_run_directory(self.config, base_dir=base_dir)
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

        except Exception as e:
            logger.error(f"Game loop failed: {e}")
            raise

        finally:
            self.data_collector.write_stats()
