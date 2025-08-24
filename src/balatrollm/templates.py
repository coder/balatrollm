"""Template management for BalatroLLM."""

import json
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader


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
