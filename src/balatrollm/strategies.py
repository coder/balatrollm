"""Strategy management for BalatroLLM."""

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class StrategyManager:
    """Lightweight helper for managing Jinja2 strategy templates."""

    def __init__(
        self, strategy: str, strategies_dir=Path(__file__).parent / "strategies"
    ):
        """Initialize StrategyManager with a strategy path.

        Args:
            strategy: name of the strategy
            strategies_dir: path to the strategies directory
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

    def render_strategy(self) -> str:
        """Render the strategy template."""
        template = self.jinja_env.get_template("STRATEGY.md.jinja")
        return template.render()

    def render_gamestate(self, state_name: str, game_state: dict[str, Any]) -> str:
        """Render the game state template."""
        template = self.jinja_env.get_template("GAMESTATE.md.jinja")
        return template.render(
            state_name=state_name,
            game_state=game_state,
        )

    def render_memory(self, responses: list[Any]) -> str:
        """Render the memory template."""
        template = self.jinja_env.get_template("MEMORY.md.jinja")
        return template.render(responses=responses)

    def load_tools(self) -> dict[str, Any]:
        """Load tools from the strategy-specific TOOLS.json file."""
        tools_file = self.strategy_path / "TOOLS.json"
        with open(tools_file) as f:
            return json.load(f)
