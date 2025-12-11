"""Test configuration and fixtures for BalatroLLM tests."""

from typing import Any, Generator

import httpx
import pytest

# ============================================================================
# Constants
# ============================================================================

HOST: str = "127.0.0.1"
PORT: int = 12346
CONNECTION_TIMEOUT: float = 60.0
REQUEST_TIMEOUT: float = 5.0

_request_id_counter: int = 0


# ============================================================================
# Helpers
# ============================================================================


def is_balatrobot_available() -> bool:
    """Check if BalatroBot API is reachable."""
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                f"http://{HOST}:{PORT}/",
                json={"jsonrpc": "2.0", "method": "gamestate", "params": {}, "id": 1},
            )
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def client() -> Generator[httpx.Client, None, None]:
    """Create an HTTP client connected to Balatro game instance."""
    with httpx.Client(
        base_url=f"http://{HOST}:{PORT}",
        timeout=httpx.Timeout(CONNECTION_TIMEOUT, read=REQUEST_TIMEOUT),
    ) as http_client:
        yield http_client


# ============================================================================
# API Helper
# ============================================================================


def api(
    client: httpx.Client,
    method: str,
    params: dict = {},
    timeout: float = REQUEST_TIMEOUT,
) -> dict[str, Any]:
    """Send a JSON-RPC 2.0 API call to Balatro."""
    global _request_id_counter
    _request_id_counter += 1

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": _request_id_counter,
    }

    response = client.post("/", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
