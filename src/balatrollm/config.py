"""Configuration management for BalatroLLM."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from . import __version__


def load_model_config(
    model: str, config_path: Path = Path("config/models.yaml")
) -> dict[str, Any]:
    """Load model-specific configuration from models.yaml.

    Merges model-specific settings with global defaults to create final
    parameters for OpenAI client requests.

    Args:
        model: Model identifier (e.g., 'openai/gpt-oss-20b')
        config_path: Path to models.yaml file

    Returns:
        Dictionary containing merged configuration for the model

    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If model not found in configuration
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Model config file not found: {config_path}")
    with config_path.open() as f:
        config = yaml.safe_load(f)

    model_config = None
    for model_entry in config.get("models", []):
        if model_entry.get("model") == model:
            model_config = model_entry.copy()
            break
    if model_config is None:
        raise KeyError(f"Model '{model}' not found in {config_path}")

    defaults = config.get("defaults", {})

    # Start with defaults, then merge model config
    # For nested dicts like extra_body, we need deep merging
    final_config = defaults.copy()

    for key, value in model_config.items():
        if (
            key in final_config
            and isinstance(final_config[key], dict)
            and isinstance(value, dict)
        ):
            # Deep merge for nested dicts
            final_config[key] = {**final_config[key], **value}
        else:
            final_config[key] = value

    return final_config


@dataclass
class StrategyManifest:
    """Strategy metadata from manifest.json.

    Stores all metadata for a game strategy including name, description,
    author, version, and tags.

    Attributes:
        name: Human-readable strategy name (e.g., 'Default', 'Aggressive').
        description: Strategy description.
        author: Strategy author identifier.
        version: Strategy version (distinct from BalatroLLM version).
        tags: List of tags for categorization.
    """

    name: str
    description: str
    author: str
    version: str
    tags: list[str]

    @classmethod
    def from_manifest_file(
        cls, strategy: str, strategies_dir: Path = Path("src/balatrollm/strategies")
    ) -> "StrategyManifest":
        """Load strategy metadata from manifest.json.

        Reads the manifest.json file for a given strategy to retrieve metadata.

        Args:
            strategy: Strategy name (e.g., 'default', 'aggressive')
            strategies_dir: Base directory containing strategy folders

        Returns:
            StrategyManifest instance loaded from the JSON file.

        Raises:
            FileNotFoundError: If manifest.json doesn't exist for the strategy
            json.JSONDecodeError: If manifest.json is malformed
            ValueError: If manifest.json is missing required fields
        """
        manifest_path = strategies_dir / strategy / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found for strategy '{strategy}': {manifest_path}"
            )

        with manifest_path.open() as f:
            data = json.load(f)

        # Validate required fields
        required_fields = {"name", "description", "author", "version", "tags"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(
                f"Manifest for strategy '{strategy}' missing required fields: {missing_fields}"
            )

        return cls(**data)

    def to_strategy_file(self, strategy_path: Path) -> None:
        """Write strategy metadata to a JSON file.

        Saves the current strategy manifest to a JSON file with proper
        formatting.

        Args:
            strategy_path: Path to the strategy file to write.
        """
        # Convert dataclass to dictionary
        strategy_data = asdict(self)

        # Create parent directory if it doesn't exist
        strategy_path.parent.mkdir(parents=True, exist_ok=True)

        with strategy_path.open("w") as f:
            json.dump(strategy_data, f, indent=2)


@dataclass
class Config:
    """Configuration for LLMBot.

    Stores all configuration parameters for bot execution including
    model settings and game parameters.

    Attributes:
        model: LLM model identifier (e.g., 'openai/gpt-oss-20b').
        strategy: Strategy name to use for game decisions (default: 'default').
        deck: Balatro deck type to use (default: 'Red Deck').
        stake: Difficulty stake level (default: 1).
        seed: Game seed for reproducible runs (default: 'OOOO155').
        challenge: Optional challenge mode identifier.
        take_screenshots: Whether to take screenshots during gameplay (default: True).
        use_default_paths: Whether to use BalatroBot's default storage paths (default: False).
        version: BalatroLLM version string (separate from strategy version).
    """

    model: str
    strategy: str = "default"
    deck: str = "Red Deck"
    stake: int = 1
    seed: str = "OOOO155"
    challenge: str | None = None
    take_screenshots: bool = True
    use_default_paths: bool = False
    version: str = __version__

    @classmethod
    def from_defaults(cls) -> "Config":
        """Create configuration with default values.

        Returns:
            Config instance with all default parameter values.
        """
        return cls(
            model="openai/gpt-oss-20b",
            strategy="default",
            deck="Red Deck",
            stake=1,
            seed="OOOO155",
            challenge=None,
            take_screenshots=True,
            use_default_paths=False,
        )

    @classmethod
    def from_config_file(cls, config_path: Path) -> "Config":
        """Create configuration from a previous run's config.json file.

        Loads model and strategy from config.json, uses CLI overrides if provided,
        otherwise falls back to environment defaults for base_url and api_key.

        Args:
            config_path: Path to the config.json file.

        Returns:
            Config instance loaded from the JSON file.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            ValueError: If config version doesn't match current repository version.
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with config_file.open() as f:
            config_data = json.load(f)

        # Version validation - check if config version matches current repo version
        if "version" in config_data:
            config_version = config_data["version"]
            if config_version != __version__:
                raise ValueError(
                    f"Version mismatch: Config file version '{config_version}' "
                    f"does not match current repository version '{__version__}'. "
                    f"Please use a config file from the same version or update your repository."
                )
        return cls(**config_data)

    def to_config_file(self, config_path: Path) -> None:
        """Write configuration to a JSON file.

        Saves the current configuration instance to a JSON file with proper
        formatting and version information.

        Args:
            config_path: Path to the config file to write.
        """
        # Convert dataclass to dictionary and ensure version is current
        config_data = asdict(self)
        config_data["version"] = __version__

        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with config_path.open("w") as f:
            json.dump(config_data, f, indent=2)
