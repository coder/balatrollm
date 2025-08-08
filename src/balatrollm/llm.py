"""LLM Bot implementation using BalatroClient"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from balatrobot import BalatroClient
from balatrobot.enums import State
from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LLMBot:
    """LLM-powered Balatro bot"""

    def __init__(
        self,
        model: str,
        proxy_url: str = "http://localhost:4000",
        api_key: str = "sk-balatrollm-proxy-key",
    ):
        self.llm_client = AsyncOpenAI(api_key=api_key, base_url=f"{proxy_url}/v1")
        self.model = model
        self.proxy_url = proxy_url
        self.api_key = api_key
        self.balatro_client = BalatroClient()

        # Set up Jinja2 templates
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.jinja_env.filters["from_json"] = json.loads
        self.responses: list[ChatCompletion] = []

        # Load tools from JSON file
        tools_file = Path(__file__).parent / "tools.json"
        with open(tools_file) as f:
            self.tools = json.load(f)

    async def validate_proxy_connection(self) -> bool:
        """Validate that the LiteLLM proxy is running and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                # Check if proxy health endpoint is available
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(
                    f"{self.proxy_url}/health", timeout=5.0, headers=headers
                )
                if response.status_code == 200:
                    logger.info(f"LiteLLM proxy is running at {self.proxy_url}")
                    return True
                else:
                    logger.error(
                        f"LiteLLM proxy health check failed: {response.status_code}"
                    )
                    return False
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to LiteLLM proxy at {self.proxy_url}: {e}")
            return False

    async def list_available_models(self) -> list[str]:
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
        if self.model in available_models:
            logger.info(f"Model '{self.model}' is available")
            return True
        else:
            logger.error(
                f"Model '{self.model}' not found. Available models: {available_models}"
            )
            return False

    def __enter__(self):
        self.balatro_client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.balatro_client.disconnect()

    def _get_tools_for_state(self, current_state: State) -> list[dict[str, Any]]:
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

        state_name = State(game_state["state"]).name

        # Generate prompt
        system_template = self.jinja_env.get_template("system.md.jinja")
        system_prompt = system_template.render()

        game_template = self.jinja_env.get_template("game_state.md.jinja")
        user_prompt = game_template.render(
            state_name=state_name,
            game=game_state.get("game"),
            hand=game_state.get("hand"),
            jokers=game_state.get("jokers"),
            shop_jokers=game_state.get("shop_jokers"),
            shop_vouchers=game_state.get("shop_vouchers"),
            shop_booster=game_state.get("shop_booster"),
            consumables=game_state.get("consumables"),
            responses=self.responses,
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Select tools based on current state
        tools = self.tools[state_name]

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                tools=tools,  # type: ignore
                tool_choice="auto",
                extra_body={"allowed_openai_params": ["reasoning_effort"]},
            )
            self.responses.append(response)

            # Extract tool call
            message = response.choices[0].message
            if not hasattr(message, "tool_calls") or not message.tool_calls:
                raise ValueError("No tool calls in LLM response")

            tool_call = message.tool_calls[0]
            function_obj = getattr(tool_call, "function", tool_call)
            function_name = getattr(function_obj, "name", None)
            if function_name is None:
                raise ValueError("Invalid tool call: missing name")
            function_args = getattr(function_obj, "arguments", None)
            if function_args is None:
                raise ValueError("Invalid tool call: missing arguments")
            logger.info(f"LLM tool call: {function_name} with args: {function_args}")
            return tool_call

        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            raise

    def execute_tool_call(self, tool_call: Any) -> dict[str, Any]:
        """Execute the action decided by the LLM."""
        function = getattr(tool_call, "function", tool_call)
        name = function.name
        arguments = json.loads(function.arguments)
        return self.balatro_client.send_message(name, arguments)

    async def play_game(self) -> None:
        """Main game loop"""
        logger.info("Starting LLM bot game loop")

        try:
            # Start a new run
            game_state = self.balatro_client.send_message(
                "start_run",
                {"deck": "Red Deck", "stake": 1, "seed": "OOOO155", "challenge": None},
            )

            while True:
                current_state = State(game_state["state"])
                logger.info(f"Current state: {current_state}")

                match current_state:
                    case State.BLIND_SELECT:
                        # TODO: Enable LLM decision for blind selection
                        # tool_call = await self.make_decision(game_state)
                        game_state = self.balatro_client.send_message(
                            "skip_or_select_blind", {"action": "select"}
                        )

                    case State.SELECTING_HAND:
                        tool_call = await self.get_tool_call(game_state)
                        game_state = self.execute_tool_call(tool_call)

                    case State.ROUND_EVAL:
                        logger.info("Cashing out")
                        game_state = self.balatro_client.send_message("cash_out")

                    case State.SHOP:
                        # TODO: Enable LLM decision for shop actions
                        # tool_call = await self.make_decision(game_state)
                        game_state = self.balatro_client.send_message(
                            "shop", {"action": "next_round"}
                        )

                    case State.GAME_OVER:
                        logger.info("Game over!")
                        break

                    case _:
                        # Wait and check state again
                        await asyncio.sleep(1)
                        game_state = self.balatro_client.send_message("get_game_state")

        except KeyboardInterrupt:
            logger.info("Game interrupted by user")
        except Exception as e:
            logger.error(f"Game loop failed: {e}")
            raise


async def main():
    """Example usage of the LLM bot."""

    # Configuration for LiteLLM proxy
    model = os.getenv("LITELLM_MODEL", "cerebras-120b")
    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
    api_key = os.getenv("LITELLM_API_KEY", "sk-balatrollm-proxy-key")

    bot = LLMBot(model=model, proxy_url=proxy_url, api_key=api_key)

    # Validate proxy connection and model before starting game
    if not await bot.validate_proxy_connection():
        logger.error(
            "Cannot connect to LiteLLM proxy. Please start the proxy with: litellm --config config/litellm.yaml"
        )
        return

    if not await bot.validate_model_exists():
        logger.error(
            f"Model '{model}' not available. Use --list-models to see available models."
        )
        return

    with bot:
        await bot.play_game()


if __name__ == "__main__":
    asyncio.run(main())
