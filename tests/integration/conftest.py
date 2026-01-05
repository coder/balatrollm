"""Configuration for integration tests.

Implements:
- Port-aware fixtures for pytest-xdist parallel execution
- Lazy fixture generation: .jkr files are generated on first use
- Health check waiting for Balatro instances
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.conftest import HOST, REQUEST_TIMEOUT, api, use_cache

# ============================================================================
# Constants
# ============================================================================

INTEGRATION_FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_JSON_PATH = Path(__file__).parent.parent / "fixtures" / "fixtures.json"
HEALTH_CHECK_TIMEOUT: float = 60.0


# ============================================================================
# Port-Aware Fixtures for pytest-xdist
# ============================================================================


@pytest.fixture(scope="session")
def worker_id(request: pytest.FixtureRequest) -> str:
    """Get pytest-xdist worker ID."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def port(worker_id: str) -> int:
    """Get assigned port for this worker from BALATROBOT_PORTS env var."""
    ports_str = os.environ.get("BALATROBOT_PORTS", "12346")
    ports = [int(p) for p in ports_str.split(",")]

    if worker_id == "master":
        return ports[0]

    # xdist workers are named "gw0", "gw1", etc.
    worker_num = int(worker_id.replace("gw", ""))
    return ports[worker_num]


@pytest.fixture(scope="session")
def balatro_server(port: int, worker_id: str) -> None:
    """Wait for Balatro instance to be healthy before running tests."""
    elapsed = 0.0
    while elapsed < HEALTH_CHECK_TIMEOUT:
        if _check_health(port):
            return
        time.sleep(0.5)
        elapsed += 0.5
    pytest.fail(
        f"[{worker_id}] Balatro on port {port} not responding "
        f"after {HEALTH_CHECK_TIMEOUT}s"
    )


def _check_health(port: int) -> bool:
    """Check if Balatro instance is responding on given port."""
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                f"http://{HOST}:{port}/",
                json={"jsonrpc": "2.0", "method": "gamestate", "params": {}, "id": 1},
            )
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


@pytest.fixture
def client(port: int, balatro_server: None) -> Generator[httpx.Client, None, None]:
    """HTTP client connected to this worker's Balatro instance."""
    with httpx.Client(
        base_url=f"http://{HOST}:{port}",
        timeout=httpx.Timeout(60.0, read=REQUEST_TIMEOUT),
    ) as http_client:
        yield http_client


# ============================================================================
# Fixtures JSON Loading
# ============================================================================


def load_fixtures_json() -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Load fixture recipes from fixtures.json."""
    if not FIXTURES_JSON_PATH.exists():
        raise FileNotFoundError(f"Fixtures JSON not found: {FIXTURES_JSON_PATH}")
    with FIXTURES_JSON_PATH.open() as f:
        return json.load(f)


# ============================================================================
# Integration Fixture Loading (.jkr files - requires Balatro)
# ============================================================================


def get_integration_fixture_path(group: str, fixture_name: str) -> Path:
    """Get path to an integration .jkr fixture file."""
    return INTEGRATION_FIXTURES_DIR / group / f"{fixture_name}.jkr"


def load_integration_fixture(
    client: httpx.Client,
    group: str,
    fixture_name: str,
    cache: bool | None = None,
) -> dict[str, Any]:
    """Load a .jkr fixture and return the gamestate.

    If the fixture doesn't exist or cache=False, it will be automatically
    generated using the setup steps defined in fixtures.json.

    Args:
        client: HTTP client connected to Balatro
        group: Fixture group name (e.g., "strategy", "bot")
        fixture_name: Fixture name (e.g., "state-SELECTING_HAND")
        cache: Override cache setting (None uses global default)

    Returns:
        The gamestate dict from Balatro
    """
    if cache is None:
        cache = use_cache()

    fixture_path = get_integration_fixture_path(group, fixture_name)

    # Generate fixture if it doesn't exist or cache is disabled
    if not fixture_path.exists() or not cache:
        fixtures_data = load_fixtures_json()

        if group not in fixtures_data:
            raise KeyError(f"Fixture group '{group}' not found in fixtures.json")
        if fixture_name not in fixtures_data[group]:
            raise KeyError(
                f"Fixture '{fixture_name}' not found in fixtures.json['{group}']"
            )

        setup_steps = fixtures_data[group][fixture_name]

        # Execute each setup step
        for step in setup_steps:
            step_method = step["method"]
            step_params = step.get("params", {})
            response = api(client, step_method, step_params)

            # Check for errors during generation
            if "error" in response:
                error_msg = response["error"]["message"]
                raise RuntimeError(
                    f"Fixture generation failed at step {step_method}: {error_msg}"
                )

        # Save the fixture
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        save_response = api(client, "save", {"path": str(fixture_path)})
        if "error" in save_response:
            raise RuntimeError(f"Failed to save fixture: {save_response}")

    # Load the .jkr save file
    response = api(client, "load", {"path": str(fixture_path)})
    if "error" in response:
        raise RuntimeError(f"Failed to load fixture: {response}")

    # Get and return the gamestate
    gamestate_response = api(client, "gamestate", {})
    if "error" in gamestate_response:
        raise RuntimeError(f"Failed to get gamestate: {gamestate_response}")

    return gamestate_response["result"]
