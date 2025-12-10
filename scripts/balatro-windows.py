#!/usr/bin/env python3
"""Balatro launcher for Windows."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Windows Steam paths to check
STEAM_PATHS = [
    Path("C:/Program Files (x86)/Steam/steamapps/common/Balatro"),
    Path("C:/Program Files/Steam/steamapps/common/Balatro"),
    Path.home() / "Steam/steamapps/common/Balatro",
]

LOGS_DIR = Path("logs")


def find_game_path() -> Path | None:
    """Find the Balatro installation path."""
    for path in STEAM_PATHS:
        if path.exists() and (path / "Balatro.exe").exists():
            return path
    return None


def kill_port(port: int):
    """Kill processes using the specified port."""
    print(f"Killing processes on port {port}...")
    try:
        # Use netstat to find PIDs listening on the port
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pids = set()
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit():
                        pids.add(pid)

        for pid in pids:
            print(f"  Killing PID {pid}")
            subprocess.run(
                ["taskkill", "/F", "/PID", pid],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        if pids:
            time.sleep(0.5)
    except Exception as e:
        print(f"  Warning: Could not kill port processes: {e}")


def kill_balatro():
    """Kill all running Balatro instances."""
    print("Killing existing Balatro instances...")
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "Balatro.exe"],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(1)
    except Exception:
        pass


def start(args):
    """Start Balatro with the given configuration."""
    # Find game installation
    game_dir = find_game_path()
    if not game_dir:
        print("ERROR: Balatro not found in any Steam location.")
        print("Checked paths:")
        for p in STEAM_PATHS:
            print(f"  - {p}")
        sys.exit(1)

    balatro_exe = game_dir / "Balatro.exe"
    version_dll = game_dir / "version.dll"

    print(f"Found Balatro at: {game_dir}")

    if not version_dll.exists():
        print(f"ERROR: version.dll not found at {version_dll}")
        print("Make sure the lovely injector is installed.")
        sys.exit(1)

    # Kill existing processes
    kill_port(args.port)
    kill_balatro()

    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)

    # Set environment variables
    env = os.environ.copy()
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

    # Open log file and start Balatro
    log_file = LOGS_DIR / f"balatro_{args.port}.log"
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            [str(balatro_exe)],
            env=env,
            cwd=str(game_dir),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    # Wait and verify process started
    time.sleep(3)
    if process.poll() is not None:
        print(f"ERROR: Balatro failed to start. Check {log_file}")
        sys.exit(1)

    print("Balatro started successfully!")
    print(f"  Port: {args.port}")
    print(f"  PID: {process.pid}")
    print(f"  Log: {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Balatro launcher for Windows")

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
