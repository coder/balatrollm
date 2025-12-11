"""Configuration for unit tests.

Unit tests don't require BalatroBot - they use pre-generated JSON fixtures.
No special pytest hooks needed.
"""

import json
from pathlib import Path
from typing import Any

# ============================================================================
# Constants
# ============================================================================

UNIT_FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================================
# Unit Fixture Loading (JSON files - no Balatro needed)
# ============================================================================


def load_unit_fixture(group: str, fixture_name: str) -> dict[str, Any]:
    """Load a unit test fixture from JSON file.

    Args:
        group: Fixture group name (e.g., "strategy")
        fixture_name: Fixture name (e.g., "state-SELECTING_HAND")

    Returns:
        The gamestate dict loaded from JSON file

    Raises:
        FileNotFoundError: If fixture JSON file doesn't exist
    """
    fixture_path = UNIT_FIXTURES_DIR / group / f"{fixture_name}.gamestate.json"
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Unit fixture not found: {fixture_path}\n"
            f"Run 'python tests/unit/fixtures/generate.py' with Balatro running to generate fixtures."
        )
    with open(fixture_path) as f:
        return json.load(f)


def load_unit_golden(group: str, fixture_name: str, template: str) -> str:
    """Load a golden output file for comparison.

    Args:
        group: Fixture group name (e.g., "strategy")
        fixture_name: Fixture name (e.g., "state-SELECTING_HAND")
        template: Template type ("gamestate", "strategy", or "memory")

    Returns:
        The expected rendered output as string

    Raises:
        FileNotFoundError: If golden file doesn't exist
    """
    golden_path = UNIT_FIXTURES_DIR / group / f"{fixture_name}.{template}.md"
    if not golden_path.exists():
        raise FileNotFoundError(
            f"Golden file not found: {golden_path}\n"
            f"Run 'python tests/unit/fixtures/generate.py' with Balatro running to generate fixtures."
        )
    return golden_path.read_text()
