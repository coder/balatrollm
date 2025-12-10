"""Test configuration and fixtures for BalatroLLM tests."""

from pathlib import Path
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


# ============================================================================
# Fixture Loading
# ============================================================================


def get_fixture_path(test_module: str, fixture_name: str) -> Path:
    """Get path to a .jkr fixture file."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return fixtures_dir / test_module / f"{fixture_name}.jkr"


def load_fixture(
    client: httpx.Client,
    test_module: str,
    fixture_name: str,
) -> dict[str, Any]:
    """Load a .jkr fixture and return the gamestate.

    Args:
        client: HTTP client connected to Balatro
        test_module: Test module name (e.g., "strategies", "bot")
        fixture_name: Fixture name (e.g., "state-SELECTING_HAND")

    Returns:
        The gamestate dict from Balatro
    """
    fixture_path = get_fixture_path(test_module, fixture_name)

    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture not found: {fixture_path}\n"
            f"Run 'python tests/fixtures/generate.py' to generate fixtures."
        )

    # Load the .jkr save file
    response = api(client, "load", {"path": str(fixture_path)})
    assert "result" in response, f"Failed to load fixture: {response}"

    # Get and return the gamestate
    gamestate_response = api(client, "gamestate", {})
    assert "result" in gamestate_response, (
        f"Failed to get gamestate: {gamestate_response}"
    )

    return gamestate_response["result"]
