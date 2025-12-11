#!/usr/bin/env python3
"""Generate integration test fixtures (.jkr save files) for BalatroLLM tests.

This script connects to a running Balatro instance with BalatroBot and executes
fixture recipes defined in fixtures.json, saving the resulting game states as
.jkr save files that can be loaded during integration tests.

Usage:
    1. Start Balatro with BalatroBot mod installed
    2. Run: python tests/integration/fixtures/generate.py

Fixture files are saved to subdirectories matching the group name in fixtures.json.
For example, fixtures.json entry:
    {"strategy": {"state-SELECTING_HAND": [...]}}
Will generate:
    tests/integration/fixtures/strategy/state-SELECTING_HAND.jkr

Note: Integration tests require Balatro running to load these .jkr fixtures.
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import httpx
from tqdm import tqdm

FIXTURES_DIR = Path(__file__).parent
HOST = "127.0.0.1"
PORT = 12346

_request_id: int = 0


@dataclass
class FixtureSpec:
    paths: list[Path]
    setup: list[tuple[str, dict]]


def api(client: httpx.Client, method: str, params: dict) -> dict:
    """Send a JSON-RPC 2.0 request to BalatroBot."""
    global _request_id
    _request_id += 1
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": _request_id,
    }
    response = client.post("/", json=payload)
    data = response.json()
    if "error" in data:
        return {"error": data["error"]}
    return data.get("result", {})


def load_fixtures_json() -> dict:
    with open(FIXTURES_DIR / "fixtures.json") as f:
        return json.load(f)


def steps_to_key(steps: list[dict]) -> str:
    return json.dumps(steps, sort_keys=True, separators=(",", ":"))


def aggregate_fixtures(json_data: dict) -> list[FixtureSpec]:
    setup_to_paths: dict[str, list[Path]] = defaultdict(list)
    setup_to_steps: dict[str, list[dict]] = {}

    for group_name, fixtures in json_data.items():
        if group_name == "$schema":
            continue
        for fixture_name, steps in fixtures.items():
            path = FIXTURES_DIR / group_name / f"{fixture_name}.jkr"
            key = steps_to_key(steps)
            setup_to_paths[key].append(path)
            if key not in setup_to_steps:
                setup_to_steps[key] = steps

    return [
        FixtureSpec(
            paths=paths,
            setup=[(s["method"], s["params"]) for s in setup_to_steps[key]],
        )
        for key, paths in setup_to_paths.items()
    ]


def generate_fixture(client: httpx.Client, spec: FixtureSpec, pbar: tqdm) -> bool:
    primary_path = spec.paths[0]
    try:
        for method, params in spec.setup:
            response = api(client, method, params)
            if isinstance(response, dict) and "error" in response:
                pbar.write(f"  Error: {primary_path.name} - {response['error']}")
                return False

        primary_path.parent.mkdir(parents=True, exist_ok=True)
        response = api(client, "save", {"path": str(primary_path)})
        if isinstance(response, dict) and "error" in response:
            pbar.write(f"  Error: {primary_path.name} - {response['error']}")
            return False

        # Copy to other paths with same setup
        for dest_path in spec.paths[1:]:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(primary_path.read_bytes())

        return True
    except Exception as e:
        pbar.write(f"  Error: {primary_path.name} - {e}")
        return False


def main() -> int:
    print(f"BalatroLLM Integration Fixture Generator\nConnecting to {HOST}:{PORT}\n")

    json_data = load_fixtures_json()
    fixtures = aggregate_fixtures(json_data)
    print(f"Loaded {len(fixtures)} unique fixture configurations\n")

    try:
        with httpx.Client(
            base_url=f"http://{HOST}:{PORT}",
            timeout=httpx.Timeout(60.0, read=10.0),
        ) as client:
            success = failed = 0
            with tqdm(total=len(fixtures), desc="Generating", unit="fixture") as pbar:
                for spec in fixtures:
                    if generate_fixture(client, spec, pbar):
                        success += 1
                    else:
                        failed += 1
                    pbar.update(1)

            api(client, "menu", {})
            print(f"\nDone: {success} generated, {failed} failed")
            return 1 if failed else 0

    except httpx.ConnectError:
        print(f"Error: Cannot connect to Balatro at {HOST}:{PORT}")
        return 1


if __name__ == "__main__":
    exit(main())
