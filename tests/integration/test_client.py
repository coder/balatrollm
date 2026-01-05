"""Integration tests for BalatroClient against a real BalatroBot instance."""

import pytest

from balatrollm.client import BalatroClient, BalatroError

# ============================================================================
# TestBalatroClientConnection
# ============================================================================


class TestBalatroClientConnection:
    """Tests for BalatroClient connection to real BalatroBot instance."""

    async def test_connect_and_disconnect(
        self, port: int, balatro_server: None
    ) -> None:
        """Verify client can connect and disconnect from BalatroBot."""
        client = BalatroClient(port=port)
        assert client._client is None

        await client.__aenter__()
        assert client._client is not None

        await client.__aexit__(None, None, None)
        assert client._client is None

    async def test_context_manager_workflow(
        self, port: int, balatro_server: None
    ) -> None:
        """Verify context manager properly manages connection lifecycle."""
        async with BalatroClient(port=port) as client:
            assert client._client is not None
        assert client._client is None


# ============================================================================
# TestBalatroClientGamestate
# ============================================================================


class TestBalatroClientGamestate:
    """Tests for gamestate retrieval from real BalatroBot instance."""

    async def test_gamestate_returns_dict(
        self, port: int, balatro_server: None
    ) -> None:
        """Verify gamestate call returns a dictionary."""
        async with BalatroClient(port=port) as client:
            result = await client.call("gamestate")

        assert isinstance(result, dict)

    async def test_gamestate_contains_state_field(
        self, port: int, balatro_server: None
    ) -> None:
        """Verify gamestate response contains the 'state' field."""
        async with BalatroClient(port=port) as client:
            result = await client.call("gamestate")

        assert "state" in result
        assert isinstance(result["state"], str)

    async def test_multiple_gamestate_calls(
        self, port: int, balatro_server: None
    ) -> None:
        """Verify multiple consecutive gamestate calls work correctly."""
        async with BalatroClient(port=port) as client:
            result1 = await client.call("gamestate")
            result2 = await client.call("gamestate")
            result3 = await client.call("gamestate")

        # All should return valid gamestates
        assert "state" in result1
        assert "state" in result2
        assert "state" in result3

        # Request ID should increment
        assert client._request_id == 3


# ============================================================================
# TestBalatroClientErrors
# ============================================================================


class TestBalatroClientErrors:
    """Tests for error handling with real BalatroBot instance."""

    async def test_invalid_method_raises_error(
        self, port: int, balatro_server: None
    ) -> None:
        """Verify calling an invalid method raises BalatroError."""
        async with BalatroClient(port=port) as client:
            with pytest.raises(BalatroError) as exc_info:
                await client.call("nonexistent_method_xyz")

        error = exc_info.value
        assert error.data["name"] == "BAD_REQUEST"
        assert error.message == "Unknown method: nonexistent_method_xyz"
