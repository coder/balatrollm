"""BalatroLLM - LLM-powered Balatro bot."""

__version__ = "1.0.0"

from .client import BalatroClient, BalatroError
from .strategy import StrategyManager

__all__ = [
    "BalatroClient",
    "BalatroError",
    "StrategyManager",
]
