#!/usr/bin/env python3
"""Bulk fixture generator for balatrollm tests.

Generates all fixtures defined in fixtures.json. Run this script with a
Balatro instance running BalatroBot to pre-generate all .jkr fixture files.

Usage:
    python tests/fixtures/generate.py

This is useful for CI environments where you want to pre-generate all fixtures
before running tests, rather than generating them lazily on first use.
"""

import json
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import httpx

# Constants
FIXTURES_DIR = Path(__file__).parent
FIXTURES_JSON = FIXTURES_DIR / "fixtures.json"
INTEGRATION_FIXTURES_DIR = Path(__file__).parent.parent / "integration" / "fixtures"
UNIT_FIXTURES_DIR = Path(__file__).parent.parent / "unit" / "fixtures"

HOST = "127.0.0.1"
PORT = 12346
TIMEOUT = 30.0


def api(client: httpx.Client, method: str, params: dict | None = None) -> dict:
    """Send a JSON-RPC 2.0 request."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1,
    }
    response = client.post("/", json=payload)
    response.raise_for_status()
    return response.json()


@dataclass
class FixtureSpec:
    """Specification for a fixture to generate."""

    group: str
    name: str
    steps: list[dict]
    output_path: Path


def steps_to_key(steps: list[dict]) -> str:
    """Convert steps to a hashable key for deduplication."""
    return json.dumps(steps, sort_keys=True)


def load_fixtures() -> list[FixtureSpec]:
    """Load fixture specifications from fixtures.json."""
    with FIXTURES_JSON.open() as f:
        data = json.load(f)

    specs = []
    for group_name, fixtures in data.items():
        if group_name.startswith("$"):
            continue  # Skip $schema and other meta keys

        for fixture_name, steps in fixtures.items():
            output_path = INTEGRATION_FIXTURES_DIR / group_name / f"{fixture_name}.jkr"
            specs.append(
                FixtureSpec(
                    group=group_name,
                    name=fixture_name,
                    steps=steps,
                    output_path=output_path,
                )
            )

    return specs


def deduplicate_fixtures(specs: list[FixtureSpec]) -> dict[str, list[FixtureSpec]]:
    """Group fixtures with identical setup steps."""
    groups: dict[str, list[FixtureSpec]] = defaultdict(list)
    for spec in specs:
        key = steps_to_key(spec.steps)
        groups[key].append(spec)
    return groups


def generate_fixture(client: httpx.Client, spec: FixtureSpec) -> bool:
    """Generate a single fixture.

    Returns True on success, False on failure.
    """
    # Execute setup steps
    for step in spec.steps:
        method = step["method"]
        params = step.get("params", {})
        response = api(client, method, params)

        if "error" in response:
            print(f"  ERROR at step {method}: {response['error']['message']}")
            return False

    # Save fixture
    spec.output_path.parent.mkdir(parents=True, exist_ok=True)
    save_response = api(client, "save", {"path": str(spec.output_path)})

    if "error" in save_response:
        print(f"  ERROR saving: {save_response['error']['message']}")
        return False

    return True


def main() -> None:
    """Main entry point."""
    print("BalatroLLM Fixture Generator")
    print("=" * 40)

    # Load fixtures
    specs = load_fixtures()
    print(f"Found {len(specs)} fixtures to generate")

    # Group by identical steps (optimization)
    groups = deduplicate_fixtures(specs)
    print(f"Deduplicated to {len(groups)} unique setups")
    print()

    # Connect to Balatro
    print(f"Connecting to BalatroBot at http://{HOST}:{PORT}...")
    with httpx.Client(base_url=f"http://{HOST}:{PORT}", timeout=TIMEOUT) as client:
        # Test connection
        try:
            api(client, "gamestate")
            print("Connected!")
        except Exception as e:
            print(f"ERROR: Could not connect to BalatroBot: {e}")
            print("Make sure Balatro is running with BalatroBot mod enabled.")
            return

        print()

        # Generate fixtures
        success_count = 0
        fail_count = 0

        for key, group_specs in groups.items():
            primary = group_specs[0]
            print(f"Generating: {primary.group}/{primary.name}")

            if generate_fixture(client, primary):
                success_count += 1

                # Copy to other paths with same setup
                for other in group_specs[1:]:
                    other.output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(primary.output_path, other.output_path)
                    print(f"  Copied to: {other.group}/{other.name}")
                    success_count += 1
            else:
                fail_count += len(group_specs)

            # Return to menu for next fixture
            api(client, "menu")

    print()
    print("=" * 40)
    print(f"Done! Generated {success_count} fixtures, {fail_count} failures")


if __name__ == "__main__":
    main()
