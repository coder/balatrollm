"""LLM Bot implementation using BalatroClient"""

import asyncio
import json
import logging
import os
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from balatrobot import BalatroClient
from balatrobot.enums import State


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


logger = logging.getLogger(__name__)


class BalatroLLMError(Exception):
    """Custom exception for BalatroLLM errors."""

    pass


class TemplateManager:
    """Lightweight helper for managing Jinja2 templates."""

    def __init__(self, template_dir: Path, strategy: str):
        self.strategy = strategy
        self.strategy_dir = template_dir / strategy
        self.jinja_env = Environment(loader=FileSystemLoader(self.strategy_dir))
        self.jinja_env.filters["from_json"] = json.loads

    def render_strategy(self) -> str:
        """Render the strategy template."""
        template = self.jinja_env.get_template("STRATEGY.md.jinja")
        return template.render()

    def render_gamestate(self, state_name: str, game_state: Dict[str, Any]) -> str:
        """Render the game state template."""
        template = self.jinja_env.get_template("GAMESTATE.md.jinja")
        return template.render(
            state_name=state_name,
            game_state=game_state,
        )

    def render_memory(self, responses: List[Any]) -> str:
        """Render the memory template."""
        template = self.jinja_env.get_template("MEMORY.md.jinja")
        return template.render(responses=responses)

    def load_tools(self) -> Dict[str, Any]:
        """Load tools from the strategy-specific TOOLS.json file."""
        tools_file = self.strategy_dir / "TOOLS.json"
        with open(tools_file) as f:
            return json.load(f)


@dataclass
class Config:
    """Configuration for LLMBot."""

    model: str
    proxy_url: str = "http://localhost:4000"
    api_key: str = "sk-balatrollm-proxy-key"
    template: str = "default"

    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            model=os.getenv("LITELLM_MODEL", "cerebras-gpt-oss-120b"),
            proxy_url=os.getenv("LITELLM_PROXY_URL", "http://localhost:4000"),
            api_key=os.getenv("LITELLM_API_KEY", "sk-balatrollm-proxy-key"),
            template=os.getenv("BALATROLLM_TEMPLATE", "default"),
        )


class LLMBot:
    """LLM-powered Balatro bot"""

    def __init__(self, config: Config):
        self.config = config
        self.llm_client = AsyncOpenAI(
            api_key=config.api_key, base_url=f"{config.proxy_url}/v1"
        )
        self.balatro_client = BalatroClient()

        # Set up template manager
        template_dir = Path(__file__).parent / "templates"
        self.template_manager = TemplateManager(template_dir, config.template)
        self.responses: list[ChatCompletion] = []

        # Load tools from strategy-specific file
        self.tools = self.template_manager.load_tools()

        # Get project version from pyproject.toml
        self.project_version = self._get_project_version()

    def _get_project_version(self) -> str:
        """Get project version from pyproject.toml"""
        try:
            # Navigate up from src/balatrollm/llm.py to find pyproject.toml
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                return pyproject_data.get("project", {}).get("version", "unknown")
            else:
                logger.warning(f"pyproject.toml not found at {pyproject_path}")
                return "unknown"
        except Exception as e:
            logger.warning(f"Failed to read project version: {e}")
            return "unknown"

    def _generate_save_path(
        self,
        deck: str,
        stake: int,
        seed: str,
        challenge: Optional[str] = None,
        base_dir: Optional[Path] = None,
    ) -> Path:
        """Generate structured save path for the run log

        Args:
            deck: Deck name (e.g., "Red Deck")
            stake: Stake level (1-8)
            seed: Seed string
            challenge: Optional challenge name
            base_dir: Base directory for runs (defaults to ./runs)

        Returns:
            Full path for the run log file
        """
        if base_dir is None:
            base_dir = Path.cwd() / "runs"

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean up names for filesystem safety
        deck_clean = deck.replace(" ", "").replace("-", "")
        model_clean = self.config.model.replace("/", "-").replace(":", "-")

        # Build filename components
        filename_parts = [
            timestamp,
            deck_clean,
            f"s{stake}",
        ]

        if challenge:
            challenge_clean = challenge.replace(" ", "").replace("-", "")
            filename_parts.append(challenge_clean)

        filename_parts.append(seed)
        filename = "_".join(filename_parts) + ".jsonl"

        # Build directory structure: version/model/template/
        save_dir = (
            base_dir / f"v{self.project_version}" / model_clean / self.config.template
        )

        # Create directory structure
        save_dir.mkdir(parents=True, exist_ok=True)

        return save_dir / filename

    async def validate_proxy_connection(self) -> bool:
        """Validate that the LiteLLM proxy is running and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                # Check if proxy health endpoint is available
                headers = {"Authorization": f"Bearer {self.config.api_key}"}
                response = await client.get(
                    f"{self.config.proxy_url}/health", timeout=5.0, headers=headers
                )
                if response.status_code == 200:
                    logger.info(f"LiteLLM proxy is running at {self.config.proxy_url}")
                    return True
                else:
                    logger.error(
                        f"LiteLLM proxy health check failed: {response.status_code}"
                    )
                    return False
        except httpx.RequestError as e:
            logger.error(
                f"Failed to connect to LiteLLM proxy at {self.config.proxy_url}: {e}"
            )
            return False

    async def list_available_models(self) -> List[str]:
        """Get list of available models from the LiteLLM proxy"""
        try:
            models = await self.llm_client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get models from proxy: {e}")
            return []

    async def validate_model_exists(self) -> bool:
        """Validate that the specified model exists in the proxy"""
        available_models = await self.list_available_models()
        if self.config.model in available_models:
            logger.info(f"Model '{self.config.model}' is available")
            return True
        else:
            logger.error(
                f"Model '{self.config.model}' not found. Available models: {available_models}"
            )
            return False

    def __enter__(self):
        self.balatro_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.balatro_client.disconnect()

    def _get_tools_for_state(self, current_state: State) -> List[Dict[str, Any]]:
        """Get OpenAI tools definition for the given state"""
        try:
            state_name = current_state.name
            if state_name not in self.tools:
                raise ValueError(f"No tools defined for state: {state_name}")
            return self.tools[state_name]
        except ValueError as e:
            if "is not a valid State" in str(e):
                raise ValueError(f"Unsupported state for LLM decision: {current_state}")
            raise

    async def get_tool_call(self, game_state: dict):
        """Use LLM to make decisions based on current game state"""
        if not game_state or "state" not in game_state:
            raise ValueError("Invalid game state: missing 'state' field")

        try:
            state_name = State(game_state["state"]).name
        except (ValueError, KeyError) as e:
            raise ValueError(
                f"Invalid game state value: {game_state.get('state')}"
            ) from e

        # Generate prompt with error handling
        try:
            strategy_content = self.template_manager.render_strategy()
            gamestate_content = self.template_manager.render_gamestate(
                state_name, game_state
            )
            memory_content = self.template_manager.render_memory(self.responses)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise RuntimeError(f"Failed to generate prompts: {e}") from e

        # Combine all content into user message
        user_content = f"{strategy_content}\n\n{gamestate_content}\n\n{memory_content}"
        messages = [
            {"role": "user", "content": user_content},
        ]

        # Select tools based on current state
        tools = self.tools[state_name]

        # Add retry logic for LLM calls
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,  # type: ignore
                    tools=tools,  # type: ignore
                    tool_choice="auto",
                    extra_body={"allowed_openai_params": ["reasoning_effort"]},
                )
                self.responses.append(response)

                # Extract tool call with comprehensive validation
                if not response.choices:
                    raise ValueError("No response choices returned from LLM")

                message = response.choices[0].message
                if not hasattr(message, "tool_calls") or not message.tool_calls:
                    logger.warning(f"No tool calls in LLM response: {message}")
                    raise ValueError("No tool calls in LLM response")

                tool_call = message.tool_calls[0]
                function_obj = getattr(tool_call, "function", tool_call)
                function_name = getattr(function_obj, "name", None)
                if function_name is None:
                    raise ValueError("Invalid tool call: missing name")
                function_args = getattr(function_obj, "arguments", None)
                if function_args is None:
                    raise ValueError("Invalid tool call: missing arguments")

                # Validate JSON arguments
                try:
                    json.loads(function_args)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in tool call arguments: {e}") from e

                logger.info(
                    f"LLM tool call: {function_name} with args: {function_args}"
                )
                return tool_call

            except Exception as e:
                attempt_num = attempt + 1
                if attempt_num == max_retries:
                    logger.error(
                        f"LLM decision failed after {max_retries} attempts: {e}"
                    )
                    raise
                else:
                    logger.warning(
                        f"LLM attempt {attempt_num} failed, retrying in {retry_delay}s: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

    def execute_tool_call(self, tool_call: Any) -> Dict[str, Any]:
        """Execute the action decided by the LLM."""
        try:
            function = getattr(tool_call, "function", tool_call)
            name = function.name
            arguments = json.loads(function.arguments)

            logger.debug(f"Executing tool call: {name} with arguments: {arguments}")
            result = self.balatro_client.send_message(name, arguments)

            if not isinstance(result, dict):
                logger.warning(
                    f"Unexpected result type from balatro_client: {type(result)}"
                )

            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode tool call arguments: {e}")
            raise ValueError(f"Invalid JSON in tool call arguments: {e}") from e
        except Exception as e:
            logger.error(f"Tool call execution failed: {e}")
            raise RuntimeError(f"Failed to execute tool call '{name}': {e}") from e

    async def play_game(
        self,
        deck: str = "Red Deck",
        stake: int = 1,
        seed: str = "OOOO155",
        challenge: str | None = None,
    ) -> None:
        """Main game loop

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

    async def _initialize_game_run(
        self, deck: str, stake: int, seed: str, challenge: Optional[str]
    ) -> Dict[str, Any]:
        """Initialize a new game run with logging setup."""
        # Generate structured save path
        log_path = self._generate_save_path(
            deck=deck, stake=stake, seed=seed, challenge=challenge
        )
        logger.info(f"Run log will be saved to: {log_path}")

        # Start a new run with log path
        start_run_args = {
            "deck": deck,
            "stake": stake,
            "seed": seed,
            "log_path": str(log_path),
        }
        if challenge:
            start_run_args["challenge"] = challenge

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
        return self.execute_tool_call(tool_call)


async def main():
    """Example usage of the LLM bot."""

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
