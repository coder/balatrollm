"""Configuration management for BalatroLLM."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for LLMBot."""

    model: str
    proxy_url: str = "http://localhost:4000"
    api_key: str = "sk-balatrollm-proxy-key"
    template: str = "default"

    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            model=os.getenv("LITELLM_MODEL", "cerebras-gpt-oss-120b"),
            proxy_url=os.getenv("LITELLM_PROXY_URL", "http://localhost:4000"),
            api_key=os.getenv("LITELLM_API_KEY", "sk-balatrollm-proxy-key"),
            template=os.getenv("BALATROLLM_TEMPLATE", "default"),
        )
