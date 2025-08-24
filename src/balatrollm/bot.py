"""Core LLM-powered Balatro bot implementation."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from balatrobot import BalatroClient
from balatrobot.enums import State

from . import __version__
from .config import Config
from .data_collection import RunDataCollector, generate_run_directory
from .strategies import StrategyManager

logger = logging.getLogger(__name__)


class BalatroLLMError(Exception):
    """Custom exception for BalatroLLM errors."""

    pass


class LLMBot:
    """LLM-powered Balatro bot."""

    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.llm_client = AsyncOpenAI(
            api_key=config.api_key, base_url=f"{config.base_url}/v1"
        )
        self.balatro_client = BalatroClient()

        # Set up strategy manager
        self.strategy_manager = StrategyManager(config.strategy)
        self.responses: list[ChatCompletion] = []

        # Load tools from strategy-specific file
        self.tools = self.strategy_manager.load_tools()

        # Get project version
        self.project_version = __version__

        # Data collector will be initialized when starting a run
        self.data_collector: Optional[RunDataCollector] = None

    def __enter__(self):
        self.balatro_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.balatro_client.disconnect()

    async def validate_proxy_connection(self) -> bool:
        """Validate that the LiteLLM proxy is running and accessible."""
        try:
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/health", timeout=5.0, headers=headers
                )

            if response.status_code == 200:
                logger.info(f"LiteLLM proxy is running at {self.config.base_url}")
                return True

            logger.error(f"LiteLLM proxy health check failed: {response.status_code}")
            return False

        except httpx.RequestError as e:
            logger.error(
                f"Failed to connect to LiteLLM proxy at {self.config.base_url}: {e}"
            )
            return False

    async def list_available_models(self) -> List[str]:
        """Get list of available models from the LiteLLM proxy."""
        try:
            models = await self.llm_client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get models from proxy: {e}")
            return []

    async def validate_model_exists(self) -> bool:
        """Validate that the specified model exists in the proxy."""
        available_models = await self.list_available_models()

        if self.config.model in available_models:
            logger.info(f"Model '{self.config.model}' is available")
            return True

        logger.error(
            f"Model '{self.config.model}' not found. Available models: {available_models}"
        )
        return False

    def _get_tools_for_state(self, current_state: State) -> List[Dict[str, Any]]:
        """Get OpenAI tools definition for the given state."""
        state_name = current_state.name
        if state_name not in self.tools:
            raise ValueError(f"No tools defined for state: {state_name}")
        return self.tools[state_name]

    async def get_tool_call(self, game_state: dict):
        """Use LLM to make decisions based on current game state."""
        self._validate_game_state(game_state)
        state_name = State(game_state["state"]).name

        # Generate prompts
        user_content = self._generate_prompt_content(state_name, game_state)
        messages = [{"role": "user", "content": user_content}]
        tools = self.tools[state_name]

        # Make LLM request with retries
        return await self._make_llm_request_with_retries(messages, tools)

    def _validate_game_state(self, game_state: dict) -> None:
        """Validate game state has required fields."""
        if not game_state or "state" not in game_state:
            raise ValueError("Invalid game state: missing 'state' field")

    def _generate_prompt_content(self, state_name: str, game_state: dict) -> str:
        """Generate combined prompt content from templates."""
        return "\n\n".join(
            [
                self.strategy_manager.render_strategy(),
                self.strategy_manager.render_gamestate(state_name, game_state),
                self.strategy_manager.render_memory(self.responses),
            ]
        )

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
                request_id = self._log_data("request", request_data)

                response = await self.llm_client.chat.completions.create(**request_data)

                self.responses.append(response)
                if self.data_collector and request_id:
                    self.data_collector.write_response(request_id, response)
                return self._extract_tool_call(response)

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

    def _log_data(self, data_type: str, data: dict) -> str | None:
        """Log data to data collector if available."""
        if not self.data_collector:
            return None

        if data_type == "request":
            return self.data_collector.write_request(data)
        return None

    def _extract_tool_call(self, response):
        """Extract and validate tool call from LLM response."""
        if not response.choices:
            raise ValueError("No response choices returned from LLM")

        message = response.choices[0].message
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            logger.warning(f"No tool calls in LLM response: {message}")
            raise ValueError("No tool calls in LLM response")

        tool_call = message.tool_calls[0]
        function_obj = getattr(tool_call, "function", tool_call)

        # Validate function call structure
        function_name = getattr(function_obj, "name", None)
        function_args = getattr(function_obj, "arguments", None)

        if not function_name or not function_args:
            raise ValueError("Invalid tool call: missing name or arguments")

        # Validate JSON arguments
        json.loads(function_args)  # Will raise JSONDecodeError if invalid

        logger.info(f"LLM tool call: {function_name} with args: {function_args}")
        return tool_call

    def execute_tool_call(self, tool_call: Any) -> Dict[str, Any]:
        """Execute the action decided by the LLM."""
        function = getattr(tool_call, "function", tool_call)
        name = function.name

        try:
            arguments = json.loads(function.arguments)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tool call arguments: {e}") from e

        logger.debug(f"Executing tool call: {name} with arguments: {arguments}")
        result = self.balatro_client.send_message(name, arguments)

        if not isinstance(result, dict):
            logger.warning(
                f"Unexpected result type from balatro_client: {type(result)}"
            )

        return result

    async def play_game(
        self,
        deck: str = "Red Deck",
        stake: int = 1,
        seed: str = "OOOO155",
        challenge: str | None = None,
    ) -> None:
        """Main game loop.

        Args:
            deck: Deck name to use
            stake: Stake level (1-8)
            seed: Seed for run generation
            challenge: Optional challenge name
        """
        logger.info("Starting LLM bot game loop")

        try:
            game_state = await self._initialize_game_run(deck, stake, seed, challenge)
            await self._run_game_loop(game_state)

        except KeyboardInterrupt:
            logger.info("Game interrupted by user")
        except Exception as e:
            logger.error(f"Game loop failed: {e}")
            raise
        finally:
            # Copy log files after game completion
            if self.data_collector:
                await self._finalize_run_data()

    async def _initialize_game_run(
        self, deck: str, stake: int, seed: str, challenge: Optional[str]
    ) -> Dict[str, Any]:
        """Initialize a new game run with data collection setup."""
        # Generate run directory
        run_dir = generate_run_directory(
            deck=deck,
            stake=stake,
            seed=seed,
            model=self.config.model,
            strategy=self.config.strategy,
            project_version=self.project_version,
            challenge=challenge,
        )
        logger.info(f"Run data will be saved to: {run_dir}")

        # Create data collector with run configuration
        run_config = {
            "model": self.config.model,
            "base_url": self.config.base_url,
            "api_key": self.config.api_key,
            "strategy": self.config.strategy,
            "deck": deck,
            "stake": stake,
            "seed": seed,
            "challenge": challenge,
            "started_at": datetime.now().isoformat(),
            "balatrollm_version": self.project_version,
            # Community metadata fields with defaults
            "name": "Unknown Name",
            "description": "Unknown Description",
            "author": "BalatroBench",
            "version": self.project_version,
            "tags": [],
        }

        self.data_collector = RunDataCollector(run_dir=run_dir, run_config=run_config)

        # Set up logging to write to run.log file
        log_path = run_dir / "run.log"
        setup_logging(verbose=self.verbose, log_file=log_path)
        logger.info("Logging configured for this run")

        # Start the game (removed log_path to prevent BalatroBot from writing game states to log file)
        start_run_args = {
            "deck": deck,
            "stake": stake,
            "seed": seed,
        }
        if challenge:
            start_run_args["challenge"] = challenge

        logger.info(f"Game log will be saved to: {log_path}")
        return self.balatro_client.send_message("start_run", start_run_args)

    async def _run_game_loop(self, game_state: Dict[str, Any]) -> None:
        """Main game loop that processes game states until completion."""
        while True:
            current_state = State(game_state["state"])
            logger.info(f"Current state: {current_state}")

            if current_state == State.GAME_OVER:
                logger.info("Game over!")
                break

            game_state = await self._handle_game_state(current_state, game_state)

    async def _handle_game_state(
        self, current_state: State, game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a specific game state and return the updated game state."""
        match current_state:
            case (
                State.BLIND_SELECT
                | State.SELECTING_HAND
                | State.ROUND_EVAL
                | State.SHOP
            ):
                return await self._process_llm_decision(game_state)
            case _:
                # Wait and check state again for unhandled states
                await asyncio.sleep(1)
                return self.balatro_client.send_message("get_game_state")

    async def _process_llm_decision(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Process an LLM decision for the current game state."""
        tool_call = await self.get_tool_call(game_state)
        result = self.execute_tool_call(tool_call)
        self._log_game_progression(game_state, tool_call, result)
        return result

    def _log_game_progression(
        self, game_state: Dict[str, Any], tool_call: Any, result: Dict[str, Any]
    ) -> None:
        """Log game state progression to data collector."""
        if not self.data_collector:
            return

        function_obj = getattr(tool_call, "function", tool_call)
        now_ms = int(datetime.now().timestamp() * 1000)

        self.data_collector.write_gamestate(
            {
                "game_state_before": game_state,
                "timestamp_ms_before": now_ms,
                "function": {
                    "name": getattr(function_obj, "name", "unknown"),
                    "arguments": json.loads(getattr(function_obj, "arguments", "{}")),
                },
                "timestamp_ms_after": now_ms,
                "game_state_after": result,
            }
        )

    async def _finalize_run_data(self) -> None:
        """Finalize run data and update final config."""
        if not self.data_collector:
            return

        logger.info("Finalizing run data...")
        log_path = self.data_collector.run_dir / "run.log"

        final_config = {
            "completed_at": datetime.now().isoformat(),
            "total_responses": len(self.responses),
            "log_file": "run.log" if log_path.exists() else None,
        }
        self.data_collector.update_config(final_config)

        if log_path.exists():
            logger.info(f"Game log saved to: {log_path}")
        else:
            logger.warning(f"Game log not found at: {log_path}")

        logger.info(f"Run data finalized in: {self.data_collector.run_dir}")


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO

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


async def main():
    """Example usage of the LLM bot."""
    from .config import Config

    config = Config.from_environment()
    bot = LLMBot(config)

    # Validate proxy connection and model before starting game
    if not await bot.validate_proxy_connection():
        logger.error(
            "Cannot connect to LiteLLM proxy. Please start the proxy with: litellm --config config/litellm.yaml"
        )
        return

    if not await bot.validate_model_exists():
        logger.error(
            f"Model '{config.model}' not available. Use --list-models to see available models."
        )
        return

    with bot:
        await bot.play_game()


if __name__ == "__main__":
    asyncio.run(main())
