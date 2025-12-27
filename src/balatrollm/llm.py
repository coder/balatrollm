"""Async OpenAI client wrapper with retry logic."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import openai
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMTimeoutError(LLMClientError):
    """Raised after max consecutive LLM timeouts."""

    pass


class LLMRetryExhaustedError(LLMClientError):
    """Raised when all retry attempts are exhausted."""

    pass


@dataclass
class LLMClient:
    """Async OpenAI client wrapper with retry logic."""

    base_url: str
    api_key: str
    timeout: float = 240.0  # We assume that LLMs respond in 240s
    max_retries: int = 3

    _client: openai.AsyncOpenAI | None = field(default=None, init=False, repr=False)
    _consecutive_timeouts: int = field(default=0, init=False, repr=False)

    async def __aenter__(self) -> "LLMClient":
        """Create the async OpenAI client."""
        self._client = openai.AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )
        self._consecutive_timeouts = 0
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Close the async OpenAI client."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def call(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model_config: dict[str, Any] | None = None,
    ) -> ChatCompletion:
        """Make a chat completion request with retry logic."""
        if self._client is None:
            raise RuntimeError(
                "Client not connected. Use 'async with LLMClient() as client:'"
            )

        request_data: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "tools": tools,
        }

        if model_config:
            for key, value in model_config.items():
                request_data[key] = value

        retry_delay = 1.0
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.chat.completions.create(**request_data)
                self._consecutive_timeouts = 0
                return response

            except openai.APITimeoutError as e:
                self._consecutive_timeouts += 1
                logger.error(f"LLM timeout ({self._consecutive_timeouts}/3): {e}")
                last_exception = e

                if self._consecutive_timeouts >= 3:
                    raise LLMTimeoutError("3 consecutive LLM request timeouts") from e

            except openai.APIConnectionError as e:
                logger.error(f"LLM connection error: {e}")
                last_exception = e

            except openai.APIStatusError as e:
                logger.error(f"LLM status error ({e.status_code}): {e}")
                last_exception = e

            except openai.LengthFinishReasonError as e:
                logger.error(f"LLM length error: {e}")
                return e.completion

            except openai.ContentFilterFinishReasonError as e:
                logger.error(f"LLM content filter error: {e}")
                last_exception = e

            if attempt < self.max_retries - 1:
                logger.warning(
                    f"Retrying in {retry_delay}s [{attempt + 1}/{self.max_retries}]"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

        raise LLMRetryExhaustedError(
            f"All {self.max_retries} retry attempts exhausted"
        ) from last_exception

    @property
    def consecutive_timeouts(self) -> int:
        """Get current consecutive timeout count."""
        return self._consecutive_timeouts

    def reset_timeout_counter(self) -> None:
        """Reset the consecutive timeout counter."""
        self._consecutive_timeouts = 0
