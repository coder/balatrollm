"""Test configuration and fixtures for BalatroLLM tests.

This module handles:
- Automatic spawning of Balatro instances for integration tests
- Port allocation for parallel execution with pytest-xdist
- Cache control for fixture regeneration
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import TYPE_CHECKING, Any

import httpx
import pytest

if TYPE_CHECKING:
    from balatrobot import BalatroInstance

# ============================================================================
# Constants
# ============================================================================

HOST: str = "127.0.0.1"
REQUEST_TIMEOUT: float = 30.0

_request_id_counter: int = 0

# Cache control (can be disabled via --no-caches)
_USE_CACHE_DEFAULT: bool = True


# ============================================================================
# Pytest Hooks
# ============================================================================


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options."""
    parser.addoption(
        "--no-caches",
        action="store_true",
        default=False,
        help="Force fixture regeneration (ignore cached .jkr files)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest and start Balatro instances for integration tests."""
    global _USE_CACHE_DEFAULT
    if config.getoption("--no-caches", default=False):
        _USE_CACHE_DEFAULT = False

    # Skip if running as xdist worker (master handles startup)
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        return

    # Only spawn for integration tests
    if not _should_run_integration(config):
        return

    # Determine parallelism (default: 1)
    numprocesses = getattr(config.option, "numprocesses", None)
    parallel = numprocesses if numprocesses and numprocesses > 0 else 1

    # Allocate random ports from a wide range to avoid collisions
    ports = random.sample(range(12346, 23456), parallel)
    os.environ["BALATROBOT_PORTS"] = ",".join(str(p) for p in ports)

    # Start instances (respects BALATROBOT_* env vars like BALATROBOT_HEADLESS)
    from balatrobot import BalatroInstance
    from balatrobot import Config as BalatrobotConfig

    base_config = BalatrobotConfig.from_env()
    instances: list[BalatroInstance] = []

    async def start_all() -> None:
        for port in ports:
            inst = BalatroInstance(base_config, port=port)
            instances.append(inst)
        await asyncio.gather(*[inst.start() for inst in instances])

    asyncio.run(start_all())
    config._balatro_instances = instances  # type: ignore[attr-defined]


def pytest_unconfigure(config: pytest.Config) -> None:
    """Stop Balatro instances after tests complete."""
    instances: list[BalatroInstance] | None = getattr(
        config, "_balatro_instances", None
    )
    if not instances:
        return

    async def stop_all() -> None:
        for inst in instances:
            await inst.stop()

    asyncio.run(stop_all())


def _should_run_integration(config: pytest.Config) -> bool:
    """Check if integration tests will run based on test paths."""
    # Check if any integration tests are selected
    # This is a heuristic - we spawn instances unless only unit tests are run
    args: list[str] = [str(a) for a in config.args] if config.args else []
    if not args:
        return True  # Default: spawn instances

    # Check if explicitly running only unit tests
    for arg in args:
        if "integration" in arg:
            return True
        if "unit" in arg and "integration" not in arg:
            return False

    # Default: spawn instances (safe choice)
    return True


def use_cache() -> bool:
    """Return current cache setting."""
    return _USE_CACHE_DEFAULT


# ============================================================================
# API Helper
# ============================================================================


def api(
    client: httpx.Client,
    method: str,
    params: dict[str, Any] | None = None,
    timeout: float = REQUEST_TIMEOUT,
) -> dict[str, Any]:
    """Send a JSON-RPC 2.0 API call to Balatro."""
    global _request_id_counter
    _request_id_counter += 1

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": _request_id_counter,
    }

    response = client.post("/", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
