"""Unit tests for the LLM client module."""

from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from balatrollm.llm import (
    LLMClient,
    LLMClientError,
    LLMRetryExhaustedError,
    LLMTimeoutError,
)

# ============================================================================
# Test LLMClient Initialization
# ============================================================================


class TestLLMClientInit:
    """Tests for LLMClient initialization."""

    def test_default_timeout(self) -> None:
        """Default timeout should be 240 seconds."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        assert client.timeout == 240.0

    def test_default_max_retries(self) -> None:
        """Default max_retries should be 3."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        assert client.max_retries == 3

    def test_custom_values(self) -> None:
        """Custom values should be applied."""
        client = LLMClient(
            base_url="https://custom.api.com",
            api_key="custom-key",
            timeout=60.0,
            max_retries=5,
        )
        assert client.base_url == "https://custom.api.com"
        assert client.api_key == "custom-key"
        assert client.timeout == 60.0
        assert client.max_retries == 5


# ============================================================================
# Test LLMClient Context Manager
# ============================================================================


class TestLLMClientContextManager:
    """Tests for async context manager behavior."""

    async def test_enter_creates_client(self) -> None:
        """__aenter__ should create AsyncOpenAI client."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        assert client._client is None

        mock_async_client = AsyncMock()
        with patch(
            "balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client
        ) as mock_openai:
            async with client:
                assert client._client is not None
                mock_openai.assert_called_once_with(
                    base_url="https://api.test.com",
                    api_key="test-key",
                    timeout=240.0,
                )

    async def test_exit_closes_client(self) -> None:
        """__aexit__ should close and clear the client."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")

        mock_async_client = AsyncMock()
        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                pass

        mock_async_client.close.assert_called_once()
        assert client._client is None

    async def test_consecutive_timeouts_reset_on_enter(self) -> None:
        """Consecutive timeout counter should reset on context entry."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        client._consecutive_timeouts = 2

        mock_async_client = AsyncMock()
        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                assert client._consecutive_timeouts == 0


# ============================================================================
# Test LLMClient.call
# ============================================================================


class TestLLMClientCall:
    """Tests for the call method."""

    async def test_call_without_context_raises(self) -> None:
        """Calling without context manager should raise RuntimeError."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Client not connected"):
            await client.call(
                model="gpt-4",
                messages=[{"role": "user", "content": "hello"}],
                tools=[],
            )

    async def test_successful_call(self) -> None:
        """Successful call should return response and reset timeout counter."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")

        mock_response = MagicMock()
        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                client._consecutive_timeouts = 2  # Simulate previous timeouts
                result = await client.call(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "hello"}],
                    tools=[{"type": "function", "function": {"name": "test"}}],
                )

        assert result == mock_response
        assert client._consecutive_timeouts == 0

    async def test_model_config_passed_to_request(self) -> None:
        """Model config should be passed to the API request."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")

        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(return_value=MagicMock())

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                await client.call(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "hello"}],
                    tools=[],
                    model_config={"seed": 42, "temperature": 0.7},
                )

        call_kwargs = mock_async_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["seed"] == 42
        assert call_kwargs["temperature"] == 0.7


# ============================================================================
# Test Retry Logic
# ============================================================================


class TestLLMClientRetry:
    """Tests for retry behavior."""

    async def test_retry_on_connection_error(self) -> None:
        """Should retry on APIConnectionError."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")

        mock_response = MagicMock()
        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=[
                openai.APIConnectionError(request=MagicMock()),
                mock_response,
            ]
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    result = await client.call(
                        model="gpt-4",
                        messages=[],
                        tools=[],
                    )

        assert result == mock_response
        assert mock_async_client.chat.completions.create.call_count == 2

    async def test_retry_on_status_error(self) -> None:
        """Should retry on APIStatusError."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")

        mock_response = MagicMock()
        mock_async_client = AsyncMock()

        status_error = openai.APIStatusError(
            message="Server error",
            response=MagicMock(status_code=500),
            body=None,
        )
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=[status_error, mock_response]
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    result = await client.call(
                        model="gpt-4",
                        messages=[],
                        tools=[],
                    )

        assert result == mock_response

    async def test_exhausted_retries_raises(self) -> None:
        """Should raise LLMRetryExhaustedError after max retries."""
        client = LLMClient(
            base_url="https://api.test.com", api_key="test-key", max_retries=3
        )

        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIConnectionError(request=MagicMock())
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    with pytest.raises(
                        LLMRetryExhaustedError, match="retry attempts exhausted"
                    ):
                        await client.call(model="gpt-4", messages=[], tools=[])

        assert mock_async_client.chat.completions.create.call_count == 3

    async def test_exponential_backoff(self) -> None:
        """Retry delays should increase exponentially."""
        client = LLMClient(
            base_url="https://api.test.com", api_key="test-key", max_retries=3
        )

        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIConnectionError(request=MagicMock())
        )

        sleep_delays: list[float] = []

        async def capture_sleep(delay: float) -> None:
            sleep_delays.append(delay)

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", side_effect=capture_sleep):
                async with client:
                    with pytest.raises(LLMRetryExhaustedError):
                        await client.call(model="gpt-4", messages=[], tools=[])

        # Should be called twice (not after last attempt)
        assert len(sleep_delays) == 2
        # Exponential: 1.0, 2.0
        assert sleep_delays[0] == 1.0
        assert sleep_delays[1] == 2.0


# ============================================================================
# Test Timeout Tracking
# ============================================================================


class TestLLMClientTimeoutTracking:
    """Tests for consecutive timeout tracking."""

    async def test_timeout_increments_counter(self) -> None:
        """APITimeoutError should increment consecutive timeout counter."""
        client = LLMClient(
            base_url="https://api.test.com", api_key="test-key", max_retries=2
        )

        mock_response = MagicMock()
        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=[
                openai.APITimeoutError(request=MagicMock()),
                mock_response,
            ]
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    # First call times out then succeeds
                    await client.call(model="gpt-4", messages=[], tools=[])
                    # Counter should be reset after success
                    assert client._consecutive_timeouts == 0

    async def test_three_consecutive_timeouts_raises(self) -> None:
        """Three consecutive timeouts should raise LLMTimeoutError."""
        client = LLMClient(
            base_url="https://api.test.com", api_key="test-key", max_retries=5
        )

        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=MagicMock())
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    with pytest.raises(LLMTimeoutError, match="3 consecutive"):
                        await client.call(model="gpt-4", messages=[], tools=[])

        # Should stop after 3 timeouts, not max_retries
        assert client._consecutive_timeouts == 3

    async def test_success_resets_timeout_counter(self) -> None:
        """Successful call should reset timeout counter."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        client._consecutive_timeouts = 2

        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(return_value=MagicMock())

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                await client.call(model="gpt-4", messages=[], tools=[])

        assert client._consecutive_timeouts == 0


# ============================================================================
# Test Length Error Handling
# ============================================================================


class TestLLMClientLengthError:
    """Tests for LengthFinishReasonError handling."""

    async def test_length_error_returns_partial_completion(self) -> None:
        """LengthFinishReasonError should return the partial completion."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")

        partial_completion = MagicMock()
        length_error = openai.LengthFinishReasonError(completion=partial_completion)

        mock_async_client = AsyncMock()
        mock_async_client.chat.completions.create = AsyncMock(side_effect=length_error)

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                result = await client.call(model="gpt-4", messages=[], tools=[])

        # Should return the partial completion, not raise
        assert result == partial_completion


# ============================================================================
# Test Exception Classes
# ============================================================================


class TestLLMExceptions:
    """Tests for LLM exception classes."""

    def test_llm_client_error_is_base(self) -> None:
        """LLMClientError should be base exception."""
        assert issubclass(LLMTimeoutError, LLMClientError)
        assert issubclass(LLMRetryExhaustedError, LLMClientError)

    def test_exceptions_are_exceptions(self) -> None:
        """All custom exceptions should inherit from Exception."""
        assert issubclass(LLMClientError, Exception)
        assert issubclass(LLMTimeoutError, Exception)
        assert issubclass(LLMRetryExhaustedError, Exception)


# ============================================================================
# Test Properties
# ============================================================================


class TestLLMClientProperties:
    """Tests for LLMClient properties and methods."""

    def test_consecutive_timeouts_property(self) -> None:
        """consecutive_timeouts property should return counter value."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        assert client.consecutive_timeouts == 0

        client._consecutive_timeouts = 2
        assert client.consecutive_timeouts == 2

    def test_reset_timeout_counter(self) -> None:
        """reset_timeout_counter should reset to zero."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        client._consecutive_timeouts = 3

        client.reset_timeout_counter()
        assert client._consecutive_timeouts == 0
