"""Configuration for integration tests."""

from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.conftest import api, is_balatrobot_available

# ============================================================================
# Constants
# ============================================================================

INTEGRATION_FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
) -> dict[str, Any]:
    """Load a .jkr fixture and return the gamestate.

    Args:
        client: HTTP client connected to Balatro
        group: Fixture group name (e.g., "strategy", "bot")
        fixture_name: Fixture name (e.g., "state-SELECTING_HAND")

    Returns:
        The gamestate dict from Balatro
    """
    fixture_path = get_integration_fixture_path(group, fixture_name)

    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Integration fixture not found: {fixture_path}\n"
            f"Run 'python tests/integration/fixtures/generate.py' with Balatro running to generate fixtures."
        )

    # Load the .jkr save file
    response = api(client, "load", {"path": str(fixture_path)})
    if "error" in response:
        raise RuntimeError(f"Failed to load fixture: {response}")

    # Get and return the gamestate
    gamestate_response = api(client, "gamestate", {})
    if "error" in gamestate_response:
        raise RuntimeError(f"Failed to get gamestate: {gamestate_response}")

    return gamestate_response["result"]


# ============================================================================
# Pytest Hooks
# ============================================================================


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply skip marker to integration tests if BalatroBot unavailable."""
    if is_balatrobot_available():
        return

    skip_marker = pytest.mark.skip(
        reason="BalatroBot API not available (is Balatro running with BalatroBot mod?)"
    )
    for item in items:
        # Only skip tests in the integration directory
        if "integration" in str(item.fspath):
            item.add_marker(skip_marker)
