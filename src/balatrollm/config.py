"""Configuration management for BalatroLLM."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import __version__


@dataclass
class Config:
    """Configuration for LLMBot.

    Stores all configuration parameters for bot execution including
    model settings, game parameters, and metadata.

    Attributes:
        model: LLM model identifier (e.g., 'cerebras/gpt-oss-120b').
        strategy: Strategy name to use for game decisions (default: 'default').
        deck: Balatro deck type to use (default: 'Red Deck').
        stake: Difficulty stake level (default: 1).
        seed: Game seed for reproducible runs (default: 'OOOO155').
        challenge: Optional challenge mode identifier.
        version: Software version string.
        name: Human-readable configuration name.
        description: Configuration description.
        author: Configuration author identifier.
        tags: List of tags for categorization.
    """

    model: str
    strategy: str = "default"
    deck: str = "Red Deck"
    stake: int = 1
    seed: str = "OOOO155"
    challenge: str | None = None
    version: str = __version__
    name: str = "Unknown Name"
    description: str = "Unknown Description"
    author: str = "BalatroBench"
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_defaults(cls) -> "Config":
        """Create configuration with default values.

        Returns:
            Config instance with all default parameter values.
        """
        return cls(
            model="cerebras/gpt-oss-120b",
            strategy="default",
            deck="Red Deck",
            stake=1,
            seed="OOOO155",
            challenge=None,
            version="",
            name="Unknown Name",
            description="Unknown Description",
            author="BalatroBench",
            tags=[],
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
