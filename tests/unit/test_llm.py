"""Unit tests for the LLM client module."""

from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest
from anthropic.types import Message
from openai.types.responses import Response

from balatrollm.llm import (
    LLMClient,
    LLMClientError,
    LLMRetryExhaustedError,
    LLMTimeoutError,
    ResponsesFailedError,
    anthropic_to_chat_completion,
    to_anthropic_messages,
    to_anthropic_model,
    to_anthropic_params,
    to_anthropic_tools,
    to_chat_completion,
    to_responses_input,
    to_responses_params,
    to_responses_tools,
)


def make_message(**overrides) -> Message:
    """Build a real Anthropic SDK Message object for adapter tests."""
    data = {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5",
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "content": [
            {"type": "thinking", "thinking": "Three Kings.", "signature": "sig"},
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "play",
                "input": {"cards": [0, 1]},
            },
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_creation_input_tokens": 300,
            "cache_read_input_tokens": 600,
        },
    }
    data.update(overrides)
    return Message.model_validate(data)


def make_response(**overrides) -> Response:
    """Build a real SDK Response object for adapter tests."""
    data = {
        "id": "resp_123",
        "object": "response",
        "created_at": 1760000000.5,
        "model": "gpt-6.1-sol",
        "status": "completed",
        "output": [
            {
                "type": "reasoning",
                "id": "rs_1",
                "summary": [],
            },
            {
                "type": "function_call",
                "id": "fc_1",
                "call_id": "call_abc",
                "name": "play",
                "arguments": '{"cards": [0, 1]}',
                "status": "completed",
            },
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "input_tokens_details": {"cached_tokens": 40},
            "output_tokens_details": {"reasoning_tokens": 8},
        },
        "parallel_tool_calls": False,
        "tool_choice": "auto",
        "tools": [],
    }
    data.update(overrides)
    return Response.model_validate(data)


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


# ============================================================================
# Test Responses API Adapters
# ============================================================================


class TestToResponsesInput:
    """Tests for Chat Completions messages -> Responses input conversion."""

    def test_text_parts_converted_and_cache_control_mapped(self) -> None:
        """Text parts become input_text; cache_control becomes a breakpoint."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "S", "cache_control": {"x": 1}},
                    {"type": "text", "text": "G"},
                ],
            }
        ]
        assert to_responses_input(messages) == [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "S",
                        "prompt_cache_breakpoint": {"mode": "explicit"},
                    },
                    {"type": "input_text", "text": "G"},
                ],
            }
        ]

    def test_string_content_passthrough(self) -> None:
        """String content is passed through unchanged."""
        messages = [{"role": "user", "content": "hello"}]
        assert to_responses_input(messages) == messages


class TestToResponsesTools:
    """Tests for Chat Completions tools -> Responses tools conversion."""

    def test_function_tool_flattened(self) -> None:
        """Nested function definitions are flattened."""
        tools = [
            {
                "type": "function",
                "function": {"name": "play", "strict": False, "parameters": {}},
            }
        ]
        assert to_responses_tools(tools) == [
            {"type": "function", "name": "play", "strict": False, "parameters": {}}
        ]


class TestToResponsesParams:
    """Tests for model config -> Responses params conversion."""

    def test_defaults_store_false(self) -> None:
        """Benchmark calls are not stored by default."""
        assert to_responses_params({}) == {"store": False}

    def test_store_overridable(self) -> None:
        """User config can override store."""
        assert to_responses_params({"store": True})["store"] is True

    def test_renamed_params(self) -> None:
        """Token limit params are renamed to max_output_tokens."""
        assert to_responses_params({"max_tokens": 64})["max_output_tokens"] == 64

    def test_reasoning_effort_merged_without_mutation(self) -> None:
        """reasoning_effort merges into reasoning regardless of key order."""
        reasoning = {"summary": "auto"}
        config = {"reasoning_effort": "high", "reasoning": reasoning}
        params = to_responses_params(config)
        assert params["reasoning"] == {"summary": "auto", "effort": "high"}
        assert reasoning == {"summary": "auto"}

    def test_named_tool_choice_flattened(self) -> None:
        """Named tool choice is flattened to the Responses format."""
        config = {"tool_choice": {"type": "function", "function": {"name": "play"}}}
        params = to_responses_params(config)
        assert params["tool_choice"] == {"type": "function", "name": "play"}

    def test_chat_only_params_rejected(self) -> None:
        """Params without a Responses equivalent raise ValueError."""
        with pytest.raises(ValueError, match="seed"):
            to_responses_params({"seed": 42})


class TestToChatCompletion:
    """Tests for Responses -> ChatCompletion conversion."""

    def test_function_call_mapped_to_tool_call(self) -> None:
        """Function call items become tool calls; reasoning items are skipped."""
        result = to_chat_completion(make_response())
        choice = result.choices[0]
        assert choice.finish_reason == "tool_calls"
        assert choice.message.tool_calls is not None
        tool_call = choice.message.tool_calls[0]
        assert tool_call.id == "call_abc"
        assert tool_call.function.name == "play"  # type: ignore[union-attr]
        assert tool_call.function.arguments == '{"cards": [0, 1]}'  # type: ignore[union-attr]
        assert result.created == 1760000000

    def test_usage_mapped_to_chat_fields(self) -> None:
        """Usage uses Chat Completions field names (read by collector)."""
        usage = to_chat_completion(make_response()).model_dump()["usage"]
        assert usage["prompt_tokens"] == 100
        assert usage["completion_tokens"] == 20
        assert usage["prompt_tokens_details"]["cached_tokens"] == 40
        assert usage["completion_tokens_details"]["reasoning_tokens"] == 8

    def test_missing_usage(self) -> None:
        """Missing usage is preserved as None."""
        assert to_chat_completion(make_response(usage=None)).usage is None

    def test_text_message_without_tool_call(self) -> None:
        """Text-only output maps to content with finish_reason stop."""
        output = [
            {
                "type": "message",
                "id": "msg_1",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "hi", "annotations": []}],
            }
        ]
        choice = to_chat_completion(make_response(output=output)).choices[0]
        assert choice.finish_reason == "stop"
        assert choice.message.content == "hi"
        assert choice.message.tool_calls is None

    def test_refusal_preserved(self) -> None:
        """Refusal content is mapped to message.refusal."""
        output = [
            {
                "type": "message",
                "id": "msg_1",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "refusal", "refusal": "no"}],
            }
        ]
        message = to_chat_completion(make_response(output=output)).choices[0].message
        assert message.refusal == "no"

    def test_incomplete_drops_tool_calls(self) -> None:
        """Truncated responses expose no (possibly partial) tool calls."""
        response = make_response(
            status="incomplete",
            incomplete_details={"reason": "max_output_tokens"},
        )
        choice = to_chat_completion(response).choices[0]
        assert choice.finish_reason == "length"
        assert choice.message.tool_calls is None

    def test_incomplete_function_call_item_dropped(self) -> None:
        """Function call items that are not completed are skipped."""
        output = [
            {
                "type": "function_call",
                "call_id": "call_abc",
                "name": "play",
                "arguments": '{"cards": [0',
                "status": "incomplete",
            }
        ]
        choice = to_chat_completion(make_response(output=output)).choices[0]
        assert choice.finish_reason == "stop"
        assert choice.message.tool_calls is None

    def test_failed_raises(self) -> None:
        """Failed responses raise ResponsesFailedError."""
        response = make_response(
            status="failed",
            error={"code": "server_error", "message": "boom"},
        )
        with pytest.raises(ResponsesFailedError, match="boom"):
            to_chat_completion(response)


class TestLLMClientResponsesApi:
    """Tests for LLMClient with api="responses"."""

    async def test_routes_to_responses_endpoint(self) -> None:
        """api=responses calls responses.create with translated request."""
        client = LLMClient(
            base_url="https://api.test.com", api_key="test-key", api="responses"
        )

        mock_async_client = AsyncMock()
        mock_async_client.responses.create = AsyncMock(return_value=make_response())

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                result = await client.call(
                    model="gpt-6.1-sol",
                    messages=[{"role": "user", "content": "hello"}],
                    tools=[{"type": "function", "function": {"name": "play"}}],
                    model_config={"reasoning": {"effort": "medium"}},
                )

        mock_async_client.chat.completions.create.assert_not_called()
        kwargs = mock_async_client.responses.create.call_args.kwargs
        assert kwargs["input"] == [{"role": "user", "content": "hello"}]
        assert kwargs["tools"] == [{"type": "function", "name": "play"}]
        assert kwargs["reasoning"] == {"effort": "medium"}
        assert kwargs["store"] is False
        assert "messages" not in kwargs
        assert result.choices[0].message.tool_calls is not None

    async def test_openai_api_strips_prefix_and_sets_provider(self) -> None:
        """On api.openai.com the openai/ prefix is stripped; provider is set."""
        client = LLMClient(
            base_url="https://api.openai.com/v1", api_key="k", api="responses"
        )
        mock_async_client = AsyncMock()
        mock_async_client.responses.create = AsyncMock(return_value=make_response())

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                result = await client.call(
                    model="openai/gpt-6.1-sol", messages=[], tools=[]
                )

        kwargs = mock_async_client.responses.create.call_args.kwargs
        assert kwargs["model"] == "gpt-6.1-sol"
        body = result.model_dump()
        assert body["provider"] == "OpenAI"
        # make_response: 100 in (40 cached), 20 out at gpt-6.1-sol prices
        expected = (60 * 2.00 + 40 * 0.10 + 20 * 10.00) / 1_000_000
        assert body["usage"]["cost"] == pytest.approx(expected)

    async def test_other_hosts_keep_prefix(self) -> None:
        """Other hosts (e.g. OpenRouter) keep the vendor prefix."""
        client = LLMClient(
            base_url="https://openrouter.ai/api/v1", api_key="k", api="responses"
        )
        mock_async_client = AsyncMock()
        mock_async_client.responses.create = AsyncMock(return_value=make_response())

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            async with client:
                result = await client.call(
                    model="openai/gpt-6.1-sol", messages=[], tools=[]
                )

        kwargs = mock_async_client.responses.create.call_args.kwargs
        assert kwargs["model"] == "openai/gpt-6.1-sol"
        body = result.model_dump()
        assert "provider" not in body
        assert "cost" not in body["usage"]

    async def test_retries_failed_response(self) -> None:
        """Failed responses are retried."""
        client = LLMClient(
            base_url="https://api.test.com", api_key="test-key", api="responses"
        )

        failed = make_response(
            status="failed", error={"code": "server_error", "message": "y"}
        )
        mock_async_client = AsyncMock()
        mock_async_client.responses.create = AsyncMock(
            side_effect=[failed, make_response()]
        )

        with patch("balatrollm.llm.openai.AsyncOpenAI", return_value=mock_async_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    result = await client.call(model="m", messages=[], tools=[])

        assert mock_async_client.responses.create.call_count == 2
        assert result.choices[0].finish_reason == "tool_calls"

    def test_default_api_is_chat(self) -> None:
        """Chat Completions remains the default API."""
        client = LLMClient(base_url="https://api.test.com", api_key="test-key")
        assert client.api == "chat"


# ============================================================================
# Test Anthropic Messages API Adapters
# ============================================================================


class TestToAnthropicRequest:
    """Tests for Chat Completions request -> Anthropic request conversion."""

    def test_vendor_prefix_stripped(self) -> None:
        """The anthropic/ prefix (used for run paths) is not sent to the API."""
        assert to_anthropic_model("anthropic/claude-haiku-5-5") == "claude-haiku-5-5"
        assert to_anthropic_model("claude-haiku-5-5") == "claude-haiku-5-5"

    def test_messages_keep_cache_control(self) -> None:
        """Text parts pass through unchanged, including cache_control."""
        part = {"type": "text", "text": "S", "cache_control": {"type": "ephemeral"}}
        system, messages = to_anthropic_messages([{"role": "user", "content": [part]}])
        assert system == []
        assert messages == [{"role": "user", "content": [part]}]

    def test_system_messages_extracted(self) -> None:
        """System messages move to the top-level system param."""
        system, messages = to_anthropic_messages(
            [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "hi"},
            ]
        )
        assert system == [{"type": "text", "text": "Be brief."}]
        assert messages == [{"role": "user", "content": "hi"}]

    def test_tools_converted(self) -> None:
        """Function tools become Anthropic tools with input_schema."""
        schema = {"type": "object", "properties": {}}
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "play",
                    "description": "Play cards",
                    "strict": False,
                    "parameters": schema,
                },
            }
        ]
        assert to_anthropic_tools(tools) == [
            {"name": "play", "description": "Play cards", "input_schema": schema}
        ]

    def test_default_params(self) -> None:
        """DEFAULT_MODEL_CONFIG maps to single auto tool choice and defaults."""
        params = to_anthropic_params(
            {"parallel_tool_calls": False, "tool_choice": "auto"}
        )
        assert params["tool_choice"] == {
            "type": "auto",
            "disable_parallel_tool_use": True,
        }
        assert params["max_tokens"] == 16000
        assert params["thinking"] == {"type": "adaptive", "display": "summarized"}

    def test_reasoning_effort_mapped(self) -> None:
        """OpenRouter-style reasoning.effort maps to output_config.effort."""
        params = to_anthropic_params({"reasoning": {"effort": "low"}})
        assert params["output_config"] == {"effort": "low"}

    def test_named_tool_choice(self) -> None:
        """Named tool choice maps to type tool."""
        params = to_anthropic_params(
            {"tool_choice": {"type": "function", "function": {"name": "play"}}}
        )
        assert params["tool_choice"] == {"type": "tool", "name": "play"}

    def test_passthrough_and_renames(self) -> None:
        """max_tokens/stop are mapped; extra_headers passes through."""
        params = to_anthropic_params(
            {"max_tokens": 64, "stop": "END", "extra_headers": {"X": "1"}}
        )
        assert params["max_tokens"] == 64
        assert params["stop_sequences"] == ["END"]
        assert params["extra_headers"] == {"X": "1"}

    def test_unsupported_params_rejected(self) -> None:
        """Params without a Messages API equivalent raise ValueError."""
        with pytest.raises(ValueError, match="seed"):
            to_anthropic_params({"seed": 42})


class TestAnthropicToChatCompletion:
    """Tests for Anthropic Message -> ChatCompletion conversion."""

    def test_tool_use_mapped(self) -> None:
        """tool_use blocks become tool calls with JSON string arguments."""
        choice = anthropic_to_chat_completion(make_message()).choices[0]
        assert choice.finish_reason == "tool_calls"
        assert choice.message.tool_calls is not None
        tool_call = choice.message.tool_calls[0]
        assert tool_call.id == "toolu_1"
        assert tool_call.function.name == "play"  # type: ignore[union-attr]
        assert tool_call.function.arguments == '{"cards": [0, 1]}'  # type: ignore[union-attr]

    def test_balatrobench_fields(self) -> None:
        """Fields read by BalatroBench: reasoning, provider and usage."""
        body = anthropic_to_chat_completion(make_message()).model_dump()
        assert body["provider"] == "Anthropic"
        assert body["choices"][0]["message"]["reasoning"] == "Three Kings."
        # prompt_tokens counts uncached + cache write + cache read tokens
        assert body["usage"]["prompt_tokens"] == 1000
        assert body["usage"]["completion_tokens"] == 20
        assert body["usage"]["prompt_tokens_details"]["cached_tokens"] == 600
        assert body["usage"]["prompt_tokens_details"]["cache_write_tokens"] == 300

    def test_cost_estimated(self) -> None:
        """Cost is estimated from Haiku 5.5 prices (Anthropic reports none)."""
        usage = anthropic_to_chat_completion(make_message()).model_dump()["usage"]
        # 100 uncached * 0.10 + 600 read * 0.01 + 300 write * 0.125 + 20 out * 0.50
        expected = (100 * 0.10 + 600 * 0.01 + 300 * 0.125 + 20 * 0.50) / 1_000_000
        assert usage["cost"] == pytest.approx(expected)
        assert usage["cost_details"]["estimated"] is True

    def test_text_only(self) -> None:
        """Text-only responses map to content with finish_reason stop."""
        message = make_message(
            stop_reason="end_turn", content=[{"type": "text", "text": "hi"}]
        )
        choice = anthropic_to_chat_completion(message).choices[0]
        assert choice.finish_reason == "stop"
        assert choice.message.content == "hi"
        assert choice.message.tool_calls is None

    def test_max_tokens_drops_tool_calls(self) -> None:
        """Truncated responses expose no (possibly partial) tool calls."""
        choice = anthropic_to_chat_completion(
            make_message(stop_reason="max_tokens")
        ).choices[0]
        assert choice.finish_reason == "length"
        assert choice.message.tool_calls is None

    def test_refusal(self) -> None:
        """Refusals map to content_filter with message.refusal set."""
        message = make_message(stop_reason="refusal", content=[])
        choice = anthropic_to_chat_completion(message).choices[0]
        assert choice.finish_reason == "content_filter"
        assert choice.message.refusal
        assert choice.message.tool_calls is None


class TestLLMClientAnthropicApi:
    """Tests for LLMClient with api="anthropic"."""

    async def test_enter_creates_anthropic_client(self) -> None:
        """api=anthropic creates an AsyncAnthropic client (SDK default key)."""
        client = LLMClient(base_url=None, api_key=None, api="anthropic")
        with patch("balatrollm.llm.anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic.return_value = AsyncMock()
            async with client:
                pass
        mock_anthropic.assert_called_once_with(
            base_url=None, api_key=None, timeout=240.0
        )

    async def test_routes_to_messages_endpoint(self) -> None:
        """api=anthropic calls messages.create with the translated request."""
        import anthropic

        client = LLMClient(base_url=None, api_key="k", api="anthropic")
        mock_client = MagicMock(spec=anthropic.AsyncAnthropic)
        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=make_message())
        mock_client.close = AsyncMock()

        with patch("balatrollm.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            async with client:
                result = await client.call(
                    model="anthropic/claude-haiku-5-5",
                    messages=[{"role": "user", "content": "hello"}],
                    tools=[{"type": "function", "function": {"name": "play"}}],
                    model_config={"reasoning": {"effort": "medium"}},
                )

        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-haiku-5-5"
        assert kwargs["messages"] == [{"role": "user", "content": "hello"}]
        assert kwargs["tools"] == [{"name": "play", "input_schema": {"type": "object"}}]
        assert kwargs["output_config"] == {"effort": "medium"}
        assert "system" not in kwargs
        assert result.choices[0].finish_reason == "tool_calls"

    async def test_retries_anthropic_status_error(self) -> None:
        """Anthropic API status errors are retried."""
        import anthropic
        import httpx2

        client = LLMClient(base_url=None, api_key="k", api="anthropic")
        request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
        error = anthropic.InternalServerError(
            "boom", response=httpx2.Response(500, request=request), body=None
        )
        mock_client = MagicMock(spec=anthropic.AsyncAnthropic)
        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=[error, make_message()])
        mock_client.close = AsyncMock()

        with patch("balatrollm.llm.anthropic.AsyncAnthropic", return_value=mock_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with client:
                    result = await client.call(model="m", messages=[], tools=[])

        assert mock_client.messages.create.call_count == 2
        assert result.choices[0].finish_reason == "tool_calls"
