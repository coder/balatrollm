#!/usr/bin/env python3
"""Balatro launcher for macOS."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# macOS-specific paths
STEAM_PATH = Path.home() / "Library/Application Support/Steam/steamapps/common/Balatro"
BALATRO_EXE = STEAM_PATH / "Balatro.app/Contents/MacOS/love"
LOVELY_LIB = STEAM_PATH / "liblovely.dylib"
LOGS_DIR = Path("logs")


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
    subprocess.run(["pkill", "-f", "Balatro\\.app"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    # Force kill if still running
    subprocess.run(["pkill", "-9", "-f", "Balatro\\.app"], stderr=subprocess.DEVNULL)


def start(args):
    """Start Balatro with the given configuration."""
    # Verify paths exist
    if not BALATRO_EXE.exists():
        print(f"ERROR: Balatro not found at {BALATRO_EXE}")
        print("Make sure Balatro is installed via Steam.")
        sys.exit(1)

    if not LOVELY_LIB.exists():
        print(f"ERROR: liblovely.dylib not found at {LOVELY_LIB}")
        print("Make sure the lovely injector is installed.")
        sys.exit(1)

    # Kill existing processes
    kill_port(args.port)
    kill_balatro()

    # Create logs directory
    LOGS_DIR.mkdir(exist_ok=True)

    # Set environment variables
    env = os.environ.copy()
    env["DYLD_INSERT_LIBRARIES"] = str(LOVELY_LIB)
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
            [str(BALATRO_EXE)],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
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
    parser = argparse.ArgumentParser(description="Balatro launcher for macOS")

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
