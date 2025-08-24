"""Configuration management for BalatroLLM."""

import json
import os
from dataclasses import dataclass
from pathlib import Path


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
    def from_config_file(cls, config_path: str) -> "Config":
        """Create configuration from a previous run's config.json file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with config_file.open() as f:
            config_data = json.load(f)
        
        # Map the config.json fields to Config fields
        # config.json uses 'base_url' and 'strategy' (updated field names)
        return cls(
            model=config_data["model"],
            base_url=config_data["base_url"],
            api_key=config_data["api_key"],
            strategy=config_data["strategy"],
        )
