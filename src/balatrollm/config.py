"""Configuration for BalatroLLM."""

import os
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import yaml

STRATEGIES_DIR = Path(__file__).parent / "strategies"


################################################################################
# Default model configuration
################################################################################

DEFAULT_MODEL_CONFIG: dict[str, bool | int | str | dict] = {
    "seed": 1,
    "parallel_tool_calls": False,
    "tool_choice": "auto",
    "extra_headers": {
        "HTTP-Referer": "https://github.com/coder/balatrollm",
        "X-Title": "BalatroLLM",
    },
    "extra_body": {
        "usage": {"include": True},
    },
}

################################################################################
# Mapping: config field -> env var
################################################################################

ENV_MAP: dict[str, str] = {
    "model": "BALATROLLM_MODEL",
    "seed": "BALATROLLM_SEED",
    "deck": "BALATROLLM_DECK",
    "stake": "BALATROLLM_STAKE",
    "strategy": "BALATROLLM_STRATEGY",
    "parallel": "BALATROLLM_PARALLEL",
    "host": "BALATROLLM_HOST",
    "port": "BALATROLLM_PORT",
    "base_url": "BALATROLLM_BASE_URL",
    "api_key": "BALATROLLM_API_KEY",
}

################################################################################
# Types for config conversion
################################################################################

BOOL_FIELDS: frozenset[str] = frozenset()
LIST_FIELDS: frozenset[str] = frozenset({"model", "seed", "deck", "stake", "strategy"})
STRING_FIELDS: frozenset[str] = frozenset({"host", "base_url", "api_key"})
INT_FIELDS: frozenset[str] = frozenset({"parallel", "port"})

################################################################################
# Enums for config validation
################################################################################

# fmt: off
VALID_DECKS: frozenset[str] = frozenset(
    { "RED", "BLUE", "YELLOW", "GREEN", "BLACK", "MAGIC", "NEBULA",
      "GHOST", "ABANDONED", "CHECKERED", "ZODIAC", "PAINTED",
      "ANAGLYPH", "PLASMA", "ERRATIC" }
)
VALID_STAKES: frozenset[str] = frozenset(
    { "WHITE", "RED", "GREEN", "BLACK", "BLUE", "PURPLE", "ORANGE", "GOLD" },
)
# fmt: on


def _ensure_list(value: None | str | list[str]) -> list[str]:
    """Ensure value is a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _parse_env_value(field_name: str, value: str) -> bool | int | str | list:
    """Convert env var string to proper type."""
    if field_name in BOOL_FIELDS:
        return value == "1"
    if field_name in INT_FIELDS:
        return int(value)
    if field_name in LIST_FIELDS:
        return [value]
    return value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_model_config(user_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get model config with defaults deep-merged with user overrides."""
    if user_config is None or not user_config:
        return DEFAULT_MODEL_CONFIG.copy()
    return _deep_merge(DEFAULT_MODEL_CONFIG, user_config)


def _load_from_env() -> dict[str, Any]:
    """Load config from BALATROLLM_* environment variables."""
    result: dict[str, Any] = {}
    for field_name, env_var in ENV_MAP.items():
        if (val := os.environ.get(env_var)) is not None:
            result[field_name] = _parse_env_value(field_name, val)
    return result


def _load_from_yaml(path: Path) -> dict[str, Any]:
    """Load config from YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f) or {}

    result: dict[str, Any] = {}
    for field_name in LIST_FIELDS:
        if field_name in data:
            result[field_name] = _ensure_list(data[field_name])
    for field_name in INT_FIELDS | STRING_FIELDS:
        if field_name in data:
            result[field_name] = data[field_name]
    if "model_config" in data and isinstance(data["model_config"], dict):
        result["model_config"] = data["model_config"]
    return result


def _load_from_args(args: Namespace) -> dict[str, Any]:
    """Load config from CLI arguments."""
    result: dict[str, Any] = {}
    for field_name in LIST_FIELDS:
        if (val := getattr(args, field_name, None)) is not None:
            result[field_name] = val if isinstance(val, list) else [val]
    for field_name in INT_FIELDS | STRING_FIELDS:
        if (val := getattr(args, field_name, None)) is not None:
            result[field_name] = val
    return result


@dataclass(frozen=True)
class Task:
    """Single run configuration (immutable)."""

    model: str
    seed: str
    deck: str
    stake: str
    strategy: str

    def __str__(self) -> str:
        """Human-readable task description."""
        return (
            f"{self.deck} | {self.stake} | {self.seed} | {self.strategy} | {self.model}"
        )


@dataclass
class Config:
    """Bot configuration with list support for game parameters."""

    # Game params (always lists internally)
    model: list[str] = field(default_factory=list)
    seed: list[str] = field(default_factory=lambda: ["AAAAAAA"])
    deck: list[str] = field(default_factory=lambda: ["RED"])
    stake: list[str] = field(default_factory=lambda: ["WHITE"])
    strategy: list[str] = field(default_factory=lambda: ["default"])

    # Execution
    parallel: int = 1

    # Connection
    host: str = "127.0.0.1"
    port: int = 12346
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str | None = None

    # Model config (merged with DEFAULT_MODEL_CONFIG)
    model_config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(
        cls,
        yaml_path: Path | None = None,
        args: Namespace | None = None,
    ) -> Self:
        """Load config with precedence: env < yaml < cli."""
        data: dict[str, Any] = {}

        # Layer 1: env vars (lowest priority)
        data.update(_load_from_env())

        # Layer 2: YAML file
        if yaml_path:
            yaml_data = _load_from_yaml(yaml_path)
            # Deep merge model_config
            if "model_config" in data and "model_config" in yaml_data:
                yaml_data["model_config"] = _deep_merge(
                    data["model_config"], yaml_data["model_config"]
                )
            data.update(yaml_data)

        # Layer 3: CLI args (highest priority)
        if args:
            data.update(_load_from_args(args))

        return cls(**data)

    def validate(self) -> None:
        """Validate config. Raises ValueError if invalid."""
        if not self.model:
            raise ValueError("At least one model is required")

        if self.parallel < 1:
            raise ValueError("parallel must be >= 1")

        if self.port < 1 or self.port > 65535:
            raise ValueError("port must be between 1 and 65535")

        for deck in self.deck:
            if deck not in VALID_DECKS:
                raise ValueError(f"Invalid deck: {deck}. Valid: {VALID_DECKS}")

        for stake in self.stake:
            if stake.upper() not in VALID_STAKES:
                raise ValueError(f"Invalid stake: {stake}. Valid: {VALID_STAKES}")

        for strategy in self.strategy:
            strategy_path = STRATEGIES_DIR / strategy
            if not strategy_path.exists():
                raise ValueError(f"Strategy not found: {strategy}")

    def generate_tasks(self) -> list[Task]:
        """Generate all run combinations as Tasks."""
        tasks: list[Task] = []

        # Order: strategy → model → deck → stake → seed
        for strategy in self.strategy:
            for model in self.model:
                for deck in self.deck:
                    for stake in self.stake:
                        for seed in self.seed:
                            tasks.append(
                                Task(
                                    model=model,
                                    seed=seed,
                                    deck=deck.upper(),
                                    stake=stake.upper(),
                                    strategy=strategy,
                                )
                            )

        return tasks

    @property
    def total_runs(self) -> int:
        """Calculate total number of runs."""
        return (
            len(self.model)
            * len(self.seed)
            * len(self.deck)
            * len(self.stake)
            * len(self.strategy)
        )
