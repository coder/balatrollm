"""Strategy management for BalatroLLM."""

import json
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader


class StrategyManager:
    """Lightweight helper for managing Jinja2 strategy templates."""

    def __init__(self, strategy_path: Path | str):
        """Initialize StrategyManager with a strategy path.
        
        Args:
            strategy_path: Path to strategy directory (can be absolute or relative)
        """
        self.strategy_path = Path(strategy_path)
        
        # Resolve to absolute path
        if not self.strategy_path.is_absolute():
            # If relative path, check if it's a known strategy name
            builtin_strategies_dir = Path(__file__).parent / "strategies"
            if (builtin_strategies_dir / self.strategy_path).exists():
                self.strategy_path = builtin_strategies_dir / self.strategy_path
            else:
                # Resolve relative to current working directory
                self.strategy_path = self.strategy_path.resolve()
        
        if not self.strategy_path.exists():
            raise FileNotFoundError(f"Strategy directory not found: {self.strategy_path}")
        
        if not self.strategy_path.is_dir():
            raise NotADirectoryError(f"Strategy path is not a directory: {self.strategy_path}")
        
        # Extract strategy name from path for logging/identification
        self.strategy = self.strategy_path.name
        self.strategy_dir = self.strategy_path
        
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
