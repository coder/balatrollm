#!/usr/bin/env python3
"""Generate unit test fixtures (JSON gamestates + golden outputs) for BalatroLLM tests.

This script connects to a running Balatro instance with BalatroBot and:
1. Executes fixture recipes from fixtures.json
2. Saves gamestate as JSON (input fixture)
3. Renders templates and saves as .md files (golden outputs)

Usage:
    python tests/unit/fixtures/generate.py

Generated files for each fixture (e.g., state-SELECTING_HAND):
    - state-SELECTING_HAND.gamestate.json  # Gamestate input
    - state-SELECTING_HAND.gamestate.md    # Golden: render_gamestate() output
    - state-SELECTING_HAND.strategy.md     # Golden: render_strategy() output
    - state-SELECTING_HAND.memory.md       # Golden: render_memory() output
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import httpx
from tqdm import tqdm

# Import StrategyManager for rendering golden outputs
from balatrollm.strategy import StrategyManager

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
            path = FIXTURES_DIR / group_name / f"{fixture_name}.gamestate.json"
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


def generate_golden_outputs(
    gamestate: dict, output_dir: Path, fixture_name: str
) -> None:
    """Render templates and save as golden output files."""
    sm = StrategyManager("default")

    # Golden: gamestate template
    gamestate_output = sm.render_gamestate(gamestate)
    gamestate_path = output_dir / f"{fixture_name}.gamestate.md"
    gamestate_path.write_text(gamestate_output)

    # Golden: strategy template
    strategy_output = sm.render_strategy(gamestate)
    strategy_path = output_dir / f"{fixture_name}.strategy.md"
    strategy_path.write_text(strategy_output)

    # Golden: memory template (empty history)
    memory_output = sm.render_memory(history=[])
    memory_path = output_dir / f"{fixture_name}.memory.md"
    memory_path.write_text(memory_output)


def generate_fixture(client: httpx.Client, spec: FixtureSpec, pbar: tqdm) -> bool:
    primary_path = spec.paths[0]
    try:
        for method, params in spec.setup:
            response = api(client, method, params)
            if isinstance(response, dict) and "error" in response:
                pbar.write(f"  Error: {primary_path.name} - {response['error']}")
                return False

        # Get gamestate after executing all steps
        gamestate = api(client, "gamestate", {})
        if isinstance(gamestate, dict) and "error" in gamestate:
            pbar.write(
                f"  Error getting gamestate: {primary_path.name} - {gamestate['error']}"
            )
            return False

        # Save gamestate as JSON
        primary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(primary_path, "w") as f:
            json.dump(gamestate, f, indent=2)

        # Generate golden outputs
        # Remove .gamestate suffix to get base fixture name
        fixture_name = primary_path.stem.removesuffix(".gamestate")
        generate_golden_outputs(gamestate, primary_path.parent, fixture_name)

        # Copy to other paths with same setup (if any share the same recipe)
        for dest_path in spec.paths[1:]:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(primary_path.read_text())
            # Copy golden files too
            dest_fixture_name = dest_path.stem.removesuffix(".gamestate")
            for suffix in [".gamestate.md", ".strategy.md", ".memory.md"]:
                src = primary_path.parent / f"{fixture_name}{suffix}"
                dst = dest_path.parent / f"{dest_fixture_name}{suffix}"
                dst.write_text(src.read_text())

        return True
    except Exception as e:
        pbar.write(f"  Error: {primary_path.name} - {e}")
        return False


def main() -> int:
    print(f"BalatroLLM Unit Fixture Generator\nConnecting to {HOST}:{PORT}\n")

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
            print(
                "Generated files per fixture: .gamestate.json, .gamestate.md, .strategy.md, .memory.md"
            )
            return 1 if failed else 0

    except httpx.ConnectError:
        print(f"Error: Cannot connect to Balatro at {HOST}:{PORT}")
        return 1


if __name__ == "__main__":
    exit(main())
