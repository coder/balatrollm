"""Integration tests for BalatroClient against a real BalatroBot instance."""

import pytest

from balatrollm.client import BalatroClient, BalatroError

# ============================================================================
# TestBalatroClientConnection
# ============================================================================


class TestBalatroClientConnection:
    """Tests for BalatroClient connection to real BalatroBot instance."""

    def test_connect_and_disconnect(self) -> None:
        """Verify client can connect and disconnect from BalatroBot."""
        client = BalatroClient()
        assert client._client is None

        client.__enter__()
        assert client._client is not None

        client.__exit__(None, None, None)
        assert client._client is None

    def test_context_manager_workflow(self) -> None:
        """Verify context manager properly manages connection lifecycle."""
        with BalatroClient() as client:
            assert client._client is not None
        assert client._client is None


# ============================================================================
# TestBalatroClientGamestate
# ============================================================================


class TestBalatroClientGamestate:
    """Tests for gamestate retrieval from real BalatroBot instance."""

    def test_gamestate_returns_dict(self) -> None:
        """Verify gamestate call returns a dictionary."""
        with BalatroClient() as client:
            result = client.call("gamestate")

        assert isinstance(result, dict)

    def test_gamestate_contains_state_field(self) -> None:
        """Verify gamestate response contains the 'state' field."""
        with BalatroClient() as client:
            result = client.call("gamestate")

        assert "state" in result
        assert isinstance(result["state"], str)

    def test_multiple_gamestate_calls(self) -> None:
        """Verify multiple consecutive gamestate calls work correctly."""
        with BalatroClient() as client:
            result1 = client.call("gamestate")
            result2 = client.call("gamestate")
            result3 = client.call("gamestate")

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

    def test_invalid_method_raises_error(self) -> None:
        """Verify calling an invalid method raises BalatroError."""
        with BalatroClient() as client:
            with pytest.raises(BalatroError) as exc_info:
                client.call("nonexistent_method_xyz")

        error = exc_info.value
        assert error.data["name"] == "BAD_REQUEST"
        assert error.message == "Unknown method: nonexistent_method_xyz"
