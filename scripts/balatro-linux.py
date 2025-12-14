#!/usr/bin/env python3
"""Balatro launcher for Linux (via Proton/Steam Play)."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Balatro Steam App ID
BALATRO_APP_ID = "2379780"

# Steam paths to check (in order of preference)
STEAM_PATHS = [
    Path.home() / ".local/share/Steam",
    Path.home() / ".steam/steam",
    Path.home() / "snap/steam/common/.local/share/Steam",
    Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
]

LOGS_DIR = Path("logs")


def find_steam_path() -> Path | None:
    """Find the Steam installation path."""
    for path in STEAM_PATHS:
        if (path / "steamapps/common/Balatro").exists():
            return path
    return None


def find_proton(steam_path: Path) -> Path | None:
    """Find a Proton installation."""
    proton_dirs = [
        steam_path / "steamapps/common/Proton - Experimental",
        steam_path / "steamapps/common/Proton 9.0",
        steam_path / "steamapps/common/Proton 8.0",
    ]
    # Also check for GE-Proton
    compattools = steam_path / "compatibilitytools.d"
    if compattools.exists():
        for tool in sorted(compattools.iterdir(), reverse=True):
            if tool.is_dir() and "proton" in tool.name.lower():
                proton_dirs.insert(0, tool)

    for proton_dir in proton_dirs:
        proton_exe = proton_dir / "proton"
        if proton_exe.exists():
            return proton_dir
    return None


def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    """Wait for port to be ready to accept connections."""
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


def kill_port(port: int):
    """Kill processes using the specified port."""
    print(f"Killing processes on port {port}...")
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.stdout.strip():
        pids = result.stdout.strip().split("\n")
        for pid in pids:
            print(f"  Killing PID {pid}")
            subprocess.run(["kill", "-9", pid], stderr=subprocess.DEVNULL)
        time.sleep(0.5)


def kill_balatro():
    """Kill all running Balatro instances."""
    print("Killing existing Balatro instances...")
    subprocess.run(["pkill", "-f", "Balatro"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    subprocess.run(["pkill", "-9", "-f", "Balatro"], stderr=subprocess.DEVNULL)


def start(args):
    """Start Balatro with the given configuration."""
    # Find Steam installation
    steam_path = find_steam_path()
    if not steam_path:
        print("ERROR: Balatro not found in any Steam location.")
        print("Checked paths:")
        for p in STEAM_PATHS:
            print(f"  - {p}/steamapps/common/Balatro")
        sys.exit(1)

    game_dir = steam_path / "steamapps/common/Balatro"
    balatro_exe = game_dir / "Balatro.exe"
    version_dll = game_dir / "version.dll"
    compat_data = steam_path / f"steamapps/compatdata/{BALATRO_APP_ID}"

    print(f"Found Balatro at: {game_dir}")

    if not balatro_exe.exists():
        print(f"ERROR: Balatro.exe not found at {balatro_exe}")
        sys.exit(1)

    if not version_dll.exists():
        print(f"ERROR: version.dll not found at {version_dll}")
        print("Make sure the lovely injector is installed.")
        sys.exit(1)

    # Find Proton
    proton_dir = find_proton(steam_path)
    if not proton_dir:
        print("ERROR: No Proton installation found.")
        print("Install Proton via Steam or download GE-Proton.")
        sys.exit(1)

    proton_exe = proton_dir / "proton"
    print(f"Using Proton: {proton_dir.name}")

    # Kill existing processes
    kill_port(args.port)
    kill_balatro()

    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)

    # Set environment variables
    env = os.environ.copy()

    # Proton environment
    env["STEAM_COMPAT_DATA_PATH"] = str(compat_data)
    env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_path)
    env["WINEDLLOVERRIDES"] = "version=n,b"

    # BalatroBot environment
    env["BALATROBOT_HOST"] = args.host
    env["BALATROBOT_PORT"] = str(args.port)

    if args.headless:
        env["BALATROBOT_HEADLESS"] = "1"
    if args.fast:
        env["BALATROBOT_FAST"] = "1"
    if args.render_on_api:
        env["BALATROBOT_RENDER_ON_API"] = "1"
    if args.audio:
        env["BALATROBOT_AUDIO"] = "1"
    if args.debug:
        env["BALATROBOT_DEBUG"] = "1"
    if args.no_shaders:
        env["BALATROBOT_NO_SHADERS"] = "1"

    # Open log file and start Balatro via Proton
    log_file = LOGS_DIR / f"balatro_{args.port}.log"
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            [str(proton_exe), "run", str(balatro_exe)],
            env=env,
            cwd=str(game_dir),
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    # Wait for port to be ready
    print(f"Waiting for port {args.port} to be ready...")
    if not wait_for_port(args.host, args.port, timeout=30):
        print(f"ERROR: Port {args.port} not ready after 30s. Check {log_file}")
        if process.poll() is not None:
            print("Balatro process has exited.")
        sys.exit(1)

    print("Balatro started successfully!")
    print(f"  Port: {args.port}")
    print(f"  PID: {process.pid}")
    print(f"  Log: {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Balatro launcher for Linux")

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=12346,
        help="Server port (default: 12346)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run in fast mode",
    )
    parser.add_argument(
        "--render-on-api",
        action="store_true",
        help="Render only on API calls",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Enable audio",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--no-shaders",
        action="store_true",
        help="Disable all shaders",
    )

    args = parser.parse_args()
    start(args)


if __name__ == "__main__":
    main()
