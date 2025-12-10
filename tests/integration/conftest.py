"""Configuration for integration tests."""

import pytest

from tests.conftest import is_balatrobot_available


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
