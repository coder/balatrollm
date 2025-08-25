"""Configuration management for BalatroLLM."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from . import __version__


@dataclass
class Config:
    """Configuration for LLMBot."""

    model: str
    base_url: str = "http://localhost:4000"
    api_key: str = "sk-balatrollm-proxy-key"
    strategy: str = "default"  # Can be strategy name or path to strategy directory

    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            model=os.getenv("LITELLM_MODEL", "cerebras-gpt-oss-120b"),
            base_url=os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
            api_key=os.getenv("LITELLM_API_KEY", "sk-balatrollm-proxy-key"),
            strategy=os.getenv("BALATROLLM_STRATEGY", "default"),
        )

    @classmethod
    def from_config_file(
        cls, config_path: str, base_url: str | None = None, api_key: str | None = None
    ) -> "Config":
        """Create configuration from a previous run's config.json file.

        Loads model and strategy from config.json, uses CLI overrides if provided,
        otherwise falls back to environment defaults for base_url and api_key.

        Args:
            config_path: Path to the config.json file
            base_url: Optional CLI override for base_url
            api_key: Optional CLI override for api_key
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

        # Create config with values from file, CLI overrides, or environment defaults
        return cls(
            model=config_data["model"],
            base_url=base_url or os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
            api_key=api_key or os.getenv("LITELLM_API_KEY", "sk-balatrollm-proxy-key"),
            strategy=config_data["strategy"],
        )
