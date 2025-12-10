"""Strategy management for BalatroLLM."""

import json
from pathlib import Path
from typing import Any

from balatrobot import enums
from jinja2 import Environment, FileSystemLoader

BALATRO_CONSTANTS = {
    "jokers": {j.name: j.value for j in enums.Jokers},
    "consumables": {c.name: c.value for c in enums.Consumables},
    "vouchers": {v.name: v.value for v in enums.Vouchers},
    "tags": {t.name: t.value for t in enums.Tags},
    "editions": {e.name: e.value for e in enums.Editions},
    "enhancements": {m.name: m.value for m in enums.Enhancements},
    "seals": {s.name: s.value for s in enums.Seals},
}


class StrategyManager:
    """Lightweight helper for managing Jinja2 strategy templates.

    Manages loading and rendering of strategy-specific templates for
    game state representation, strategy guidance, and memory management.

    Attributes:
        strategy_path: Path to the strategy directory containing templates.
        jinja_env: Jinja2 environment configured for template rendering.
    """

    def __init__(
        self, strategy: str, strategies_dir=Path(__file__).parent / "strategies"
    ):
        """Initialize StrategyManager with a strategy path.

        Args:
            strategy: Name of the strategy to load.
            strategies_dir: Path to the strategies directory
                (default: strategies/ relative to this module).

        Raises:
            FileNotFoundError: If strategy directory is missing required template files.
        """

        self.strategy_path = strategies_dir / strategy

        required_files = [
            "STRATEGY.md.jinja",
            "GAMESTATE.md.jinja",
            "MEMORY.md.jinja",
            "TOOLS.json",
        ]

        missing_files = []
        for file_name in required_files:
            if not (self.strategy_path / file_name).exists():
                missing_files.append(file_name)

        if missing_files:
            raise FileNotFoundError(
                f"Strategy directory missing required files: {missing_files}. "
                f"Required files: {required_files}"
            )

        self.jinja_env = Environment(loader=FileSystemLoader(self.strategy_path))
        self.jinja_env.filters["from_json"] = json.loads

    def render_strategy(self, game_state: dict[str, Any]) -> str:
        """Render the strategy template.

        Args:
            game_state: Optional game state for context-aware strategy rendering.

        Returns:
            Rendered strategy guidance content as a string.
        """
        template = self.jinja_env.get_template("STRATEGY.md.jinja")
        return template.render(
            G=game_state,
            constants=BALATRO_CONSTANTS,
        )

    def render_gamestate(self, game_state: dict[str, Any]) -> str:
        """Render the game state template.

        Args:
            game_state: Game state dictionary from BalatroClient.

        Returns:
            Rendered game state representation as a string.
        """
        template = self.jinja_env.get_template("GAMESTATE.md.jinja")
        return template.render(
            G=game_state,
            constants=BALATRO_CONSTANTS,
        )

    def render_memory(
        self,
        responses: list[Any],
        last_error_call_msg: str | None = None,
        last_failed_call_msg: str | None = None,
    ) -> str:
        """Render the memory template.

        Args:
            responses: List of previous LLM responses for context.
            last_response_is_invalid: Error message if last response was invalid.
            last_tool_called_failed: Error message if last tool call failed.

        Returns:
            Rendered memory/history content as a string.
        """
        template = self.jinja_env.get_template("MEMORY.md.jinja")
        return template.render(
            responses=responses,
            last_error_call_msg=last_error_call_msg,
            last_failed_call_msg=last_failed_call_msg,
            constants=BALATRO_CONSTANTS,
        )

    def load_tools(self) -> dict[str, Any]:
        """Load tools from the strategy-specific TOOLS.json file.

        Returns:
            Dictionary mapping game states to available tool definitions.

        Raises:
            FileNotFoundError: If TOOLS.json file is missing.
            json.JSONDecodeError: If TOOLS.json contains invalid JSON.
        """
        tools_file = self.strategy_path / "TOOLS.json"
        with open(tools_file) as f:
            return json.load(f)
