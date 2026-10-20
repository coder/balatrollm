"""Async OpenAI client wrapper with retry logic."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Literal, cast
from urllib.parse import urlparse

import anthropic
import openai
from anthropic.types import Message, TextBlock, ThinkingBlock, ToolUseBlock
from openai.types.chat import ChatCompletion
from openai.types.responses import (
    Response,
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputRefusal,
)

from .pricing import add_cost

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


class ResponsesFailedError(LLMClientError):
    """Raised when a Responses API response has status "failed" (retried)."""

    pass


# Which API to call: OpenAI Chat Completions, OpenAI Responses, or the
# Anthropic Messages API (via the official anthropic SDK)
API = Literal["chat", "responses", "anthropic"]
VALID_APIS: frozenset[str] = frozenset({"chat", "responses", "anthropic"})

# Default base URL for the OpenAI SDK (chat and responses APIs)
DEFAULT_OPENAI_BASE_URL = "https://openrouter.ai/api/v1"

# OpenAI's own API host. Model names there have no vendor prefix, so a
# configured "openai/<model>" (which stores runs under runs/.../openai/<model>/,
# matching BalatroBench) is stripped before calling it.
OPENAI_API_HOST = "api.openai.com"
OPENAI_VENDOR_PREFIX = "openai/"

# Chat Completions params renamed in the Responses API
RESPONSES_RENAMED_PARAMS: dict[str, str] = {
    "max_tokens": "max_output_tokens",
    "max_completion_tokens": "max_output_tokens",
}

# Chat Completions params with no Responses API equivalent
CHAT_ONLY_PARAMS: frozenset[str] = frozenset(
    {
        "seed",
        "n",
        "stop",
        "logprobs",
        "logit_bias",
        "frequency_penalty",
        "presence_penalty",
        "response_format",
        "modalities",
        "audio",
        "stream_options",
    }
)


################################################################################
# Responses API adapters (Chat Completions request in, ChatCompletion out)
################################################################################


def to_responses_text_part(part: dict[str, Any]) -> dict[str, Any]:
    """Convert a Chat Completions text part to a Responses input_text part.

    A `cache_control` marker becomes an explicit prompt cache breakpoint.
    OpenAI's implicit caching only places a breakpoint at the end of the
    prompt, so without it a prompt whose tail changes on every call (the
    game state) never reuses the static prefix (the strategy).
    """
    result: dict[str, Any] = {"type": "input_text", "text": part["text"]}
    if "cache_control" in part:
        result["prompt_cache_breakpoint"] = {"mode": "explicit"}
    return result


def to_responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Chat Completions messages to Responses API input items."""
    items: list[dict[str, Any]] = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, list):
            content = [
                to_responses_text_part(part)
                for part in content
                if part.get("type") == "text"
            ]
        items.append({"role": message["role"], "content": content})
    return items


def to_responses_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Chat Completions tools to flat Responses API function tools."""
    result: list[dict[str, Any]] = []
    for tool in tools:
        if tool.get("type") == "function" and "function" in tool:
            result.append({"type": "function", **tool["function"]})
        else:
            result.append(tool)
    return result


def to_responses_params(model_config: dict[str, Any]) -> dict[str, Any]:
    """Convert Chat Completions model config to Responses API parameters.

    Raises ValueError for Chat Completions params the Responses API rejects.
    """
    unsupported = sorted(CHAT_ONLY_PARAMS & model_config.keys())
    if unsupported:
        raise ValueError(
            f"model_config params not supported by the Responses API: {unsupported}"
        )

    params: dict[str, Any] = {"store": False}  # Don't persist benchmark calls
    for key, value in model_config.items():
        if key in ("reasoning", "reasoning_effort"):
            continue
        params[RESPONSES_RENAMED_PARAMS.get(key, key)] = value

    # Merge reasoning settings without mutating the caller's config
    reasoning = dict(model_config.get("reasoning") or {})
    if "reasoning_effort" in model_config:
        reasoning["effort"] = model_config["reasoning_effort"]
    if reasoning:
        params["reasoning"] = reasoning

    # Named tool choice: {"type": "function", "function": {"name": ...}}
    tool_choice = params.get("tool_choice")
    if isinstance(tool_choice, dict) and "function" in tool_choice:
        params["tool_choice"] = {
            "type": "function",
            "name": tool_choice["function"]["name"],
        }

    return params


def to_chat_completion(
    response: Response, provider: str | None = None
) -> ChatCompletion:
    """Convert a Responses API response to a ChatCompletion.

    Keeps the bot and collector (and downstream BalatroBench analysis)
    independent of which API produced the response.

    Raises ResponsesFailedError if the response failed server-side.
    """
    if response.status == "failed":
        error = response.error.message if response.error else "unknown error"
        raise ResponsesFailedError(f"Responses API request failed: {error}")

    # Only expose tool calls from a complete response: a truncated
    # function call may carry partial (unparseable or wrong) arguments
    tool_calls: list[dict[str, Any]] = []
    refusal: str | None = None
    for item in response.output:
        if isinstance(item, ResponseFunctionToolCall) and item.status in (
            None,
            "completed",
        ):
            tool_calls.append(
                {
                    "id": item.call_id,
                    "type": "function",
                    "function": {"name": item.name, "arguments": item.arguments},
                }
            )
        elif isinstance(item, ResponseOutputMessage):
            for part in item.content:
                if isinstance(part, ResponseOutputRefusal):
                    refusal = part.refusal

    if response.status == "incomplete":
        tool_calls = []
        reason = response.incomplete_details and response.incomplete_details.reason
        finish_reason = "content_filter" if reason == "content_filter" else "length"
    elif tool_calls:
        finish_reason = "tool_calls"
    else:
        finish_reason = "stop"

    usage: dict[str, Any] | None = None
    if response.usage is not None:
        input_details = getattr(response.usage, "input_tokens_details", None)
        output_details = getattr(response.usage, "output_tokens_details", None)
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens_details": {
                "cached_tokens": getattr(input_details, "cached_tokens", None),
                "cache_write_tokens": getattr(
                    input_details, "cache_write_tokens", None
                ),
            },
            "completion_tokens_details": {
                "reasoning_tokens": getattr(output_details, "reasoning_tokens", None)
            },
        }
        # Keep a provider-reported cost (e.g. OpenRouter); estimate it for
        # direct OpenAI calls, which don't report one
        if (cost := getattr(response.usage, "cost", None)) is not None:
            usage["cost"] = cost
        elif provider == "OpenAI":
            add_cost(usage, response.model)

    body: dict[str, Any] = {}
    if provider:
        body["provider"] = provider  # Read by BalatroBench (as OpenRouter sets it)

    return ChatCompletion.model_validate(
        {
            **body,
            "id": response.id,
            "object": "chat.completion",
            "created": int(response.created_at),
            "model": response.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {
                        "role": "assistant",
                        "content": response.output_text or None,
                        "refusal": refusal,
                        "tool_calls": tool_calls or None,
                    },
                }
            ],
            "usage": usage,
        }
    )


################################################################################
# Anthropic Messages API adapters (Chat Completions request in, ChatCompletion out)
################################################################################

# Model name prefix stripped before calling the Anthropic API. Keeping it in the
# configured model name stores runs under runs/.../anthropic/<model>/, matching
# the vendor/model layout BalatroBench uses for the leaderboard.
ANTHROPIC_VENDOR_PREFIX = "anthropic/"

# Default max_tokens for Anthropic requests (required by the Messages API).
# Leaves room for adaptive thinking before the tool call.
ANTHROPIC_DEFAULT_MAX_TOKENS = 16000

# Chat Completions params with no Messages API equivalent
ANTHROPIC_UNSUPPORTED_PARAMS: frozenset[str] = frozenset(
    {
        "seed",
        "n",
        "logprobs",
        "top_logprobs",
        "logit_bias",
        "frequency_penalty",
        "presence_penalty",
        "response_format",
        "modalities",
        "audio",
        "stream_options",
        "store",
    }
)

# Messages API stop_reason -> Chat Completions finish_reason
ANTHROPIC_FINISH_REASONS: dict[str, str] = {
    "tool_use": "tool_calls",
    "end_turn": "stop",
    "stop_sequence": "stop",
    "pause_turn": "stop",
    "max_tokens": "length",
    "model_context_window_exceeded": "length",
    "refusal": "content_filter",
}


def to_anthropic_model(model: str) -> str:
    """Strip the "anthropic/" vendor prefix from a model name."""
    return model.removeprefix(ANTHROPIC_VENDOR_PREFIX)


def to_anthropic_messages(
    messages: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split Chat Completions messages into Anthropic (system, messages).

    Text parts (including cache_control) already use the Messages API format.
    """
    system: list[dict[str, Any]] = []
    result: list[dict[str, Any]] = []
    for message in messages:
        content = message.get("content", "")
        if message["role"] in ("system", "developer"):
            if isinstance(content, str):
                system.append({"type": "text", "text": content})
            else:
                system.extend(content)
        else:
            result.append({"role": message["role"], "content": content})
    return system, result


def to_anthropic_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Chat Completions function tools to Anthropic tools."""
    result: list[dict[str, Any]] = []
    for tool in tools:
        function = tool["function"]
        anthropic_tool: dict[str, Any] = {
            "name": function["name"],
            "input_schema": function.get("parameters", {"type": "object"}),
        }
        if "description" in function:
            anthropic_tool["description"] = function["description"]
        if function.get("strict"):
            anthropic_tool["strict"] = True
        result.append(anthropic_tool)
    return result


def to_anthropic_params(model_config: dict[str, Any]) -> dict[str, Any]:
    """Convert Chat Completions model config to Messages API parameters.

    Raises ValueError for Chat Completions params the Messages API rejects.
    """
    unsupported = sorted(ANTHROPIC_UNSUPPORTED_PARAMS & model_config.keys())
    if unsupported:
        raise ValueError(
            f"model_config params not supported by the Anthropic API: {unsupported}"
        )

    config = dict(model_config)
    params: dict[str, Any] = {
        "max_tokens": config.pop(
            "max_completion_tokens",
            config.pop("max_tokens", ANTHROPIC_DEFAULT_MAX_TOKENS),
        ),
        # Summarized thinking is stored as message.reasoning (read by
        # BalatroBench). Display does not change how thinking is billed.
        "thinking": config.pop(
            "thinking", {"type": "adaptive", "display": "summarized"}
        ),
    }

    # Effort: OpenRouter-style reasoning.effort or reasoning_effort
    output_config = dict(config.pop("output_config", None) or {})
    reasoning = config.pop("reasoning", None) or {}
    effort = config.pop("reasoning_effort", reasoning.get("effort"))
    if effort is not None:
        output_config["effort"] = effort
    if output_config:
        params["output_config"] = output_config

    # Tool choice: chat "auto"/"none"/"required"/named + parallel_tool_calls
    tool_choice = config.pop("tool_choice", "auto")
    parallel_tool_calls = config.pop("parallel_tool_calls", None)
    if isinstance(tool_choice, dict):
        if "function" in tool_choice:
            choice: dict[str, Any] = {
                "type": "tool",
                "name": tool_choice["function"]["name"],
            }
        else:
            choice = dict(tool_choice)
    else:
        choice = {"type": "any" if tool_choice == "required" else tool_choice}
    if parallel_tool_calls is False and choice["type"] != "none":
        choice["disable_parallel_tool_use"] = True
    params["tool_choice"] = choice

    if "stop" in config:
        stop = config.pop("stop")
        params["stop_sequences"] = [stop] if isinstance(stop, str) else stop

    # Remaining params (temperature, extra_headers, extra_body, ...) pass through
    params.update(config)
    return params


def anthropic_to_chat_completion(message: Message) -> ChatCompletion:
    """Convert an Anthropic Messages API response to a ChatCompletion.

    Field mapping follows what BalatroBench reads from responses.jsonl:
    tool_calls, message.reasoning, usage.prompt_tokens/completion_tokens and
    body.provider.
    """
    texts: list[str] = []
    thinking: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            texts.append(block.text)
        elif isinstance(block, ThinkingBlock) and block.thinking:
            thinking.append(block.thinking)
        elif isinstance(block, ToolUseBlock):
            tool_calls.append(
                {
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                }
            )

    stop_reason = message.stop_reason or "end_turn"
    finish_reason = ANTHROPIC_FINISH_REASONS.get(stop_reason, "stop")

    refusal: str | None = None
    if stop_reason == "refusal":
        stop_details = getattr(message, "stop_details", None)
        refusal = getattr(stop_details, "explanation", None) or "refusal"

    # Only expose tool calls the model finished: a max_tokens or refusal stop
    # may cut a tool call short
    if finish_reason != "tool_calls":
        tool_calls = []

    # prompt_tokens counts every input token (uncached, cache write, cache
    # read), matching the OpenAI/OpenRouter meaning of prompt_tokens
    usage = message.usage
    cache_write = usage.cache_creation_input_tokens or 0
    cache_read = usage.cache_read_input_tokens or 0
    prompt_tokens = usage.input_tokens + cache_write + cache_read
    chat_usage: dict[str, Any] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": usage.output_tokens,
        "total_tokens": prompt_tokens + usage.output_tokens,
        "prompt_tokens_details": {
            "cached_tokens": cache_read,
            "cache_write_tokens": cache_write,
        },
    }
    # The Anthropic API doesn't report cost; estimate it (read by BalatroBench)
    add_cost(chat_usage, message.model)

    return ChatCompletion.model_validate(
        {
            "id": message.id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": message.model,
            "provider": "Anthropic",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {
                        "role": "assistant",
                        "content": "".join(texts) or None,
                        "refusal": refusal,
                        "reasoning": "\n\n".join(thinking) or None,
                        "tool_calls": tool_calls or None,
                    },
                }
            ],
            "usage": chat_usage,
        }
    )


@dataclass
class LLMClient:
    """Async OpenAI client wrapper with retry logic."""

    base_url: str | None
    api_key: str | None
    timeout: float = 240.0  # We assume that LLMs respond in 240s
    max_retries: int = 3
    api: API = "chat"

    _client: openai.AsyncOpenAI | anthropic.AsyncAnthropic | None = field(
        default=None, init=False, repr=False
    )
    _consecutive_timeouts: int = field(default=0, init=False, repr=False)

    async def __aenter__(self) -> "LLMClient":
        """Create the async API client (OpenAI or Anthropic SDK)."""
        if self.api == "anthropic":
            # None falls back to the SDK defaults (ANTHROPIC_API_KEY env var,
            # https://api.anthropic.com)
            self._client = anthropic.AsyncAnthropic(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
            )
        else:
            self._client = openai.AsyncOpenAI(
                base_url=self.base_url or DEFAULT_OPENAI_BASE_URL,
                api_key=self.api_key or "",
                timeout=self.timeout,
            )
        self._consecutive_timeouts = 0
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Close the async API client."""
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

        if self.api == "anthropic":
            system, anthropic_messages = to_anthropic_messages(messages)
            request_data: dict[str, Any] = {
                "model": to_anthropic_model(model),
                "messages": anthropic_messages,
                "tools": to_anthropic_tools(tools),
                **to_anthropic_params(model_config or {}),
            }
            if system:
                request_data["system"] = system
        elif self.api == "responses":
            if self._is_openai_api:
                model = model.removeprefix(OPENAI_VENDOR_PREFIX)
            request_data = {
                "model": model,
                "input": to_responses_input(messages),
                "tools": to_responses_tools(tools),
                **to_responses_params(model_config or {}),
            }
        else:
            request_data = {
                "model": model,
                "messages": messages,
                "tools": tools,
                **(model_config or {}),
            }

        retry_delay = 1.0
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                if self.api == "anthropic":
                    client = cast(anthropic.AsyncAnthropic, self._client)
                    response = anthropic_to_chat_completion(
                        await client.messages.create(**request_data)
                    )
                elif self.api == "responses":
                    client = cast(openai.AsyncOpenAI, self._client)
                    # Params are built dynamically from model_config, which the
                    # type checker can't match against the SDK's overloads
                    create = cast(Any, client.responses.create)
                    response = to_chat_completion(
                        await create(**request_data),
                        provider="OpenAI" if self._is_openai_api else None,
                    )
                else:
                    client = cast(openai.AsyncOpenAI, self._client)
                    response = await client.chat.completions.create(**request_data)
                self._consecutive_timeouts = 0

                # Guard against API returning empty/None choices
                if not response.choices:
                    raise LLMClientError("API returned empty response (no choices)")

                return response

            except (openai.APITimeoutError, anthropic.APITimeoutError) as e:
                self._consecutive_timeouts += 1
                logger.error(f"LLM timeout ({self._consecutive_timeouts}/3): {e}")
                last_exception = e

                if self._consecutive_timeouts >= 3:
                    raise LLMTimeoutError("3 consecutive LLM request timeouts") from e

            except (openai.APIConnectionError, anthropic.APIConnectionError) as e:
                logger.error(f"LLM connection error: {e}")
                last_exception = e

            except (openai.APIStatusError, anthropic.APIStatusError) as e:
                logger.error(f"LLM status error ({e.status_code}): {e}")
                last_exception = e

            except openai.LengthFinishReasonError as e:
                logger.error(f"LLM length error: {e}")
                return e.completion

            except openai.ContentFilterFinishReasonError as e:
                logger.error(f"LLM content filter error: {e}")
                last_exception = e

            except json.JSONDecodeError as e:
                logger.error(f"LLM response parse error (malformed JSON): {e}")
                last_exception = e

            except ResponsesFailedError as e:
                logger.error(f"LLM response failed: {e}")
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
    def _is_openai_api(self) -> bool:
        """Whether requests go to OpenAI's own API (not OpenRouter or a proxy)."""
        return urlparse(self.base_url or "").hostname == OPENAI_API_HOST

    @property
    def consecutive_timeouts(self) -> int:
        """Get current consecutive timeout count."""
        return self._consecutive_timeouts

    def reset_timeout_counter(self) -> None:
        """Reset the consecutive timeout counter."""
        self._consecutive_timeouts = 0
