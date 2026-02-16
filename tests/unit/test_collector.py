"""Unit tests for the collector module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from balatrollm.collector import (
    ChatCompletionError,
    ChatCompletionRequestInput,
    ChatCompletionRequestOutput,
    ChatCompletionResponse,
    Collector,
    Stats,
    _generate_run_dir,
)
from balatrollm.config import Task

# ============================================================================
# Test _generate_run_dir
# ============================================================================


class TestGenerateRunDir:
    """Tests for _generate_run_dir function."""

    def test_basic_path_structure(self, tmp_path: Path) -> None:
        """Path should follow expected structure."""
        task = Task(
            model="openai/gpt-4",
            seed="AAAAAAA",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        with patch("balatrollm.collector.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000_123"
            result = _generate_run_dir(task, tmp_path)

        # Check path structure: base/runs/v{version}/{strategy}/{vendor}/{model}/{timestamp}_{deck}_{stake}_{seed}
        assert "runs" in str(result)
        assert "default" in str(result)  # strategy
        assert "openai" in str(result)  # vendor
        assert "gpt-4" in str(result)  # model
        assert "RED" in str(result)
        assert "WHITE" in str(result)
        assert "AAAAAAA" in str(result)

    def test_model_with_colon_in_name(self, tmp_path: Path) -> None:
        """Model names with colons should work (e.g., meta-llama/llama-3:70b)."""
        task = Task(
            model="meta-llama/llama-3:70b",
            seed="TEST",
            deck="BLUE",
            stake="RED",
            strategy="default",
        )
        with patch("balatrollm.collector.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000_123"
            result = _generate_run_dir(task, tmp_path)

        assert "meta-llama" in str(result)
        assert "llama-3:70b" in str(result)

    def test_model_without_vendor_defaults_to_other(self, tmp_path: Path) -> None:
        """Models without vendor should default to 'other'."""
        task = Task(
            model="invalid_model",  # Missing vendor/
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        result = _generate_run_dir(task, tmp_path)
        assert "other" in str(result)
        assert "invalid_model" in str(result)


# ============================================================================
# Test ChatCompletion Dataclasses
# ============================================================================


class TestChatCompletionRequestInput:
    """Tests for ChatCompletionRequestInput dataclass."""

    def test_defaults(self) -> None:
        """Default values should be set correctly."""
        req = ChatCompletionRequestInput(custom_id="test-001")
        assert req.custom_id == "test-001"
        assert req.method == "POST"
        assert req.url == "/v1/chat/completions"
        assert req.body == {}

    def test_custom_body(self) -> None:
        """Custom body should be stored."""
        body = {"model": "gpt-4", "messages": []}
        req = ChatCompletionRequestInput(custom_id="test-002", body=body)
        assert req.body == body


class TestChatCompletionResponse:
    """Tests for ChatCompletionResponse dataclass."""

    def test_fields(self) -> None:
        """All fields should be accessible."""
        resp = ChatCompletionResponse(
            request_id="12345",
            status_code=200,
            body={"id": "chatcmpl-123"},
        )
        assert resp.request_id == "12345"
        assert resp.status_code == 200
        assert resp.body["id"] == "chatcmpl-123"


class TestChatCompletionError:
    """Tests for ChatCompletionError dataclass."""

    def test_fields(self) -> None:
        """All fields should be accessible."""
        error = ChatCompletionError(code="rate_limit", message="Too many requests")
        assert error.code == "rate_limit"
        assert error.message == "Too many requests"


class TestChatCompletionRequestOutput:
    """Tests for ChatCompletionRequestOutput dataclass."""

    def test_from_dict_with_response(self) -> None:
        """Should parse dict with response correctly."""
        data = {
            "id": "67890",
            "custom_id": "request-00001",
            "response": {
                "request_id": "12345",
                "status_code": 200,
                "body": {"id": "chatcmpl-123"},
            },
            "error": None,
        }
        result = ChatCompletionRequestOutput.from_dict(data)

        assert result.id == "67890"
        assert result.custom_id == "request-00001"
        assert result.response is not None
        assert result.response.status_code == 200
        assert result.error is None

    def test_from_dict_with_error(self) -> None:
        """Should parse dict with error correctly."""
        data = {
            "id": "67890",
            "custom_id": "request-00001",
            "response": None,
            "error": {"code": "server_error", "message": "Internal error"},
        }
        result = ChatCompletionRequestOutput.from_dict(data)

        assert result.response is None
        assert result.error is not None
        assert result.error.code == "server_error"
        assert result.error.message == "Internal error"

    def test_from_dict_empty_response_and_error(self) -> None:
        """Should handle missing response and error."""
        data = {
            "id": "67890",
            "custom_id": "request-00001",
        }
        result = ChatCompletionRequestOutput.from_dict(data)

        assert result.response is None
        assert result.error is None


# ============================================================================
# Test Collector Initialization
# ============================================================================


class TestCollectorInit:
    """Tests for Collector initialization."""

    def test_creates_directories(self, tmp_path: Path) -> None:
        """Should create run and screenshot directories."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        assert collector.run_dir.exists()
        assert collector.screenshot_dir.exists()
        assert collector.screenshot_dir == collector.run_dir / "screenshots"

    def test_writes_task_json(self, tmp_path: Path) -> None:
        """Should write task.json on init."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        task_file = collector.run_dir / "task.json"
        assert task_file.exists()

        with task_file.open() as f:
            data = json.load(f)

        assert data["model"]["vendor"] == "openai"
        assert data["model"]["name"] == "gpt-4"
        assert data["seed"] == "TEST"
        assert data["deck"] == "RED"
        assert data["stake"] == "WHITE"
        assert data["strategy"] == "default"

    def test_writes_strategy_json(self, tmp_path: Path) -> None:
        """Should write strategy.json on init."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        strategy_file = collector.run_dir / "strategy.json"
        assert strategy_file.exists()

        with strategy_file.open() as f:
            data = json.load(f)

        assert "name" in data
        assert "version" in data


# ============================================================================
# Test Collector.record_call
# ============================================================================


class TestCollectorRecordCall:
    """Tests for record_call method."""

    def test_record_successful(self, tmp_path: Path) -> None:
        """Should increment success counter."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        collector.record_call("successful")
        assert collector._calls_success == 1
        assert collector._calls_total == 1

    def test_record_error(self, tmp_path: Path) -> None:
        """Should increment error counter."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        collector.record_call("error")
        assert collector._calls_error == 1
        assert collector._calls_total == 1

    def test_record_failed(self, tmp_path: Path) -> None:
        """Should increment failed counter."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        collector.record_call("failed")
        assert collector._calls_failed == 1
        assert collector._calls_total == 1

    def test_invalid_outcome_raises(self, tmp_path: Path) -> None:
        """Invalid outcome should raise ValueError."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        with pytest.raises(ValueError, match="Invalid call outcome"):
            collector.record_call("invalid")  # type: ignore[arg-type]


# ============================================================================
# Test Collector.write_request
# ============================================================================


class TestCollectorWriteRequest:
    """Tests for write_request method."""

    def test_writes_to_jsonl(self, tmp_path: Path) -> None:
        """Should write request to requests.jsonl."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        body = {"model": "gpt-4", "messages": []}
        custom_id = collector.write_request(body)

        assert custom_id == "request-00001"

        requests_file = collector.run_dir / "requests.jsonl"
        assert requests_file.exists()

        with requests_file.open() as f:
            line = f.readline()
            data = json.loads(line)

        assert data["custom_id"] == "request-00001"
        assert data["body"] == body

    def test_increments_request_count(self, tmp_path: Path) -> None:
        """Should increment request count."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        id1 = collector.write_request({})
        id2 = collector.write_request({})
        id3 = collector.write_request({})

        assert id1 == "request-00001"
        assert id2 == "request-00002"
        assert id3 == "request-00003"


# ============================================================================
# Test Collector.write_response
# ============================================================================


class TestCollectorWriteResponse:
    """Tests for write_response method."""

    def test_writes_success_response(self, tmp_path: Path) -> None:
        """Should write successful response to responses.jsonl."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        response = ChatCompletionResponse(
            request_id="12345",
            status_code=200,
            body={"id": "chatcmpl-123"},
        )
        collector.write_response(
            id="67890", custom_id="request-00001", response=response
        )

        responses_file = collector.run_dir / "responses.jsonl"
        assert responses_file.exists()

        with responses_file.open() as f:
            data = json.loads(f.readline())

        assert data["id"] == "67890"
        assert data["custom_id"] == "request-00001"
        assert data["response"]["status_code"] == 200

    def test_writes_error_response(self, tmp_path: Path) -> None:
        """Should write error response to responses.jsonl."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        error = ChatCompletionError(code="rate_limit", message="Too many requests")
        collector.write_response(id="67890", custom_id="request-00001", error=error)

        responses_file = collector.run_dir / "responses.jsonl"
        with responses_file.open() as f:
            data = json.loads(f.readline())

        assert data["error"]["code"] == "rate_limit"
        assert data["error"]["message"] == "Too many requests"


# ============================================================================
# Test Collector.write_gamestate
# ============================================================================


class TestCollectorWriteGamestate:
    """Tests for write_gamestate method."""

    def test_writes_to_jsonl(self, tmp_path: Path) -> None:
        """Should write gamestate to gamestates.jsonl."""
        task = Task(
            model="openai/gpt-4",
            seed="TEST",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        collector = Collector(task, tmp_path)

        gamestate = {"state": "SELECTING_HAND", "ante_num": 1, "round_num": 1}
        collector.write_gamestate(gamestate)

        gamestates_file = collector.run_dir / "gamestates.jsonl"
        assert gamestates_file.exists()

        with gamestates_file.open() as f:
            data = json.loads(f.readline())

        assert data == gamestate


# ============================================================================
# Test Stats dataclass
# ============================================================================


class TestStats:
    """Tests for Stats dataclass."""

    def test_all_fields_present(self) -> None:
        """Stats should have all required fields."""
        stats = Stats(
            run_won=True,
            run_completed=True,
            final_ante=8,
            final_round=24,
            finish_reason="won",
            providers={"anthropic": 10, "openai": 5},
            calls_total=15,
            calls_success=14,
            calls_error=1,
            calls_failed=0,
            tokens_in_total=10000,
            tokens_out_total=5000,
            tokens_in_avg=666.67,
            tokens_out_avg=333.33,
            tokens_in_std=100.0,
            tokens_out_std=50.0,
            time_total_ms=60000,
            time_avg_ms=4000.0,
            time_std_ms=500.0,
            cost_total=0.50,
            cost_avg=0.033,
            cost_std=0.01,
        )

        assert stats.run_won is True
        assert stats.final_ante == 8
        assert stats.finish_reason == "won"
        assert stats.providers == {"anthropic": 10, "openai": 5}
        assert stats.calls_total == 15
        assert stats.tokens_in_total == 10000
        assert stats.cost_total == 0.50
