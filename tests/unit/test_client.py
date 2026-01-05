"""Tests for the BalatroLLM client module."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from httpx import Response

from balatrollm.client import BalatroClient, BalatroError

# ============================================================================
# TestBalatroError
# ============================================================================


class TestBalatroError:
    """Tests for BalatroError exception class."""

    def test_error_attributes(self) -> None:
        """Verify code, message, data attributes are set."""
        error = BalatroError(
            code=-32001,
            message="Invalid parameters or protocol error",
            data={"name": "BAD_REQUEST"},
        )
        assert error.code == -32001
        assert error.message == "Invalid parameters or protocol error"
        assert error.data == {"name": "BAD_REQUEST"}

    def test_error_is_exception(self) -> None:
        """Verify BalatroError inherits from Exception."""
        error = BalatroError(
            code=-32001,
            message="Invalid parameters or protocol error",
            data={"name": "BAD_REQUEST"},
        )
        assert isinstance(error, Exception)

    def test_error_str_representation(self) -> None:
        """Verify string representation includes code and message."""
        error = BalatroError(
            code=-32001,
            message="Invalid parameters or protocol error",
            data={"name": "BAD_REQUEST"},
        )
        assert "[BAD_REQUEST]" in str(error)
        assert "Invalid parameters or protocol error" in str(error)


# ============================================================================
# TestBalatroClient
# ============================================================================


class TestBalatroClient:
    """Tests for BalatroClient initialization and context manager."""

    def test_init_default_values(self) -> None:
        """Verify default host, port, timeout values."""
        client = BalatroClient()
        assert client.host == "127.0.0.1"
        assert client.port == 12346
        assert client.timeout == 30.0

    def test_init_custom_values(self) -> None:
        """Verify custom values are applied correctly."""
        client = BalatroClient(host="localhost", port=8080, timeout=60.0)
        assert client.host == "localhost"
        assert client.port == 8080
        assert client.timeout == 60.0

    async def test_context_manager_creates_client(self) -> None:
        """Verify __aenter__ creates httpx.AsyncClient."""
        client = BalatroClient()
        assert client._client is None

        async with respx.mock:
            async with client:
                assert client._client is not None

    async def test_context_manager_closes_client(self) -> None:
        """Verify __aexit__ closes the client and sets _client to None."""
        client = BalatroClient()
        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        client._client = mock_http_client

        await client.__aexit__(None, None, None)

        mock_http_client.aclose.assert_called_once()
        assert client._client is None

    async def test_call_without_context_raises_error(self) -> None:
        """Verify calling without context manager raises RuntimeError."""
        client = BalatroClient()
        with pytest.raises(RuntimeError, match="Client not connected"):
            await client.call("test_method")


# ============================================================================
# TestBalatroClientCall
# ============================================================================


@pytest.mark.respx(base_url="http://127.0.0.1:12346", assert_all_called=False)
class TestBalatroClientCall:
    """Tests for BalatroClient.call method using respx mocking."""

    async def test_call_increments_request_id(
        self, respx_mock: respx.MockRouter
    ) -> None:
        """Each call increments the internal request ID."""
        respx_mock.post("/").mock(
            return_value=Response(200, json={"jsonrpc": "2.0", "result": {}, "id": 1})
        )

        async with BalatroClient() as client:
            assert client._request_id == 0
            await client.call("method1")
            assert client._request_id == 1
            await client.call("method2")
            assert client._request_id == 2

    async def test_call_formats_request_correctly(
        self, respx_mock: respx.MockRouter
    ) -> None:
        """Verify JSON-RPC 2.0 format with jsonrpc, method, params, id."""
        route = respx_mock.post("/").mock(
            return_value=Response(
                200, json={"jsonrpc": "2.0", "result": {"status": "ok"}, "id": 1}
            )
        )

        async with BalatroClient() as client:
            await client.call("test_method")

        # Inspect the captured request
        request = route.calls.last.request
        json_payload = json.loads(request.content)

        assert json_payload["jsonrpc"] == "2.0"
        assert json_payload["method"] == "test_method"
        assert json_payload["params"] == {}
        assert json_payload["id"] == 1

    async def test_call_returns_result(self, respx_mock: respx.MockRouter) -> None:
        """Verify the result field is extracted and returned."""
        expected_result = {"state": "SELECTING_HAND", "hand": []}
        respx_mock.post("/").mock(
            return_value=Response(
                200, json={"jsonrpc": "2.0", "result": expected_result, "id": 1}
            )
        )

        async with BalatroClient() as client:
            result = await client.call("gamestate")

        assert result == expected_result

    async def test_call_with_params(self, respx_mock: respx.MockRouter) -> None:
        """Verify params are passed correctly."""
        route = respx_mock.post("/").mock(
            return_value=Response(200, json={"jsonrpc": "2.0", "result": {}, "id": 1})
        )

        params = {"deck": "Red Deck", "stake": 1, "seed": "ABC123"}
        async with BalatroClient() as client:
            await client.call("start", params)

        json_payload = json.loads(route.calls.last.request.content)
        assert json_payload["params"] == params

    async def test_call_raises_balatro_error_on_error_response(
        self, respx_mock: respx.MockRouter
    ) -> None:
        """Verify BalatroError is raised with correct code, message, data."""
        respx_mock.post("/").mock(
            return_value=Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": "Invalid parameters or protocol error",
                        "data": {"name": "BAD_REQUEST"},
                    },
                    "id": 1,
                },
            )
        )

        async with BalatroClient() as client:
            with pytest.raises(BalatroError) as exc_info:
                await client.call("start", params={"deck": "INVALID_DECK"})

        error = exc_info.value
        assert error.code == -32001
        assert error.message == "Invalid parameters or protocol error"
        assert error.data == {"name": "BAD_REQUEST"}

    async def test_call_raises_invalid_state_error(
        self, respx_mock: respx.MockRouter
    ) -> None:
        """Verify INVALID_STATE error is raised correctly."""
        respx_mock.post("/").mock(
            return_value=Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32002,
                        "message": "Action not allowed in current game state",
                        "data": {"name": "INVALID_STATE"},
                    },
                    "id": 1,
                },
            )
        )

        async with BalatroClient() as client:
            with pytest.raises(BalatroError) as exc_info:
                await client.call("play", params={"cards": [0, 1, 2]})

        error = exc_info.value
        assert error.code == -32002
        assert error.message == "Action not allowed in current game state"
        assert error.data == {"name": "INVALID_STATE"}

    async def test_call_raises_not_allowed_error(
        self, respx_mock: respx.MockRouter
    ) -> None:
        """Verify NOT_ALLOWED error is raised correctly."""
        respx_mock.post("/").mock(
            return_value=Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32003,
                        "message": "Game rules prevent this action",
                        "data": {"name": "NOT_ALLOWED"},
                    },
                    "id": 1,
                },
            )
        )

        async with BalatroClient() as client:
            with pytest.raises(BalatroError) as exc_info:
                await client.call("reroll")

        error = exc_info.value
        assert error.code == -32003
        assert error.message == "Game rules prevent this action"
        assert error.data == {"name": "NOT_ALLOWED"}

    async def test_call_raises_internal_error(
        self, respx_mock: respx.MockRouter
    ) -> None:
        """Verify INTERNAL_ERROR is raised correctly."""
        respx_mock.post("/").mock(
            return_value=Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Server-side failure",
                        "data": {"name": "INTERNAL_ERROR"},
                    },
                    "id": 1,
                },
            )
        )

        async with BalatroClient() as client:
            with pytest.raises(BalatroError) as exc_info:
                await client.call("save", params={"path": "/invalid/path/save.jkr"})

        error = exc_info.value
        assert error.code == -32000
        assert error.message == "Server-side failure"
        assert error.data == {"name": "INTERNAL_ERROR"}
