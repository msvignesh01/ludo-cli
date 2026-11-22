#!/usr/bin/env python3
"""Choose and launch a Ludo implementation from the project directory."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def choose_engine(engine: str | None) -> str | None:
    """Return the selected engine, prompting when none was provided."""
    if engine is not None:
        return engine
    print("Choose a Ludo version:")
    print("  1. Object-oriented")
    print("  2. Function-based")
    while True:
        try:
            answer = input("Enter 1 or 2 (q to cancel): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nLaunch cancelled.")
            return None
        if answer == "1":
            return "oop"
        if answer == "2":
            return "functional"
        if answer in ("q", "quit"):
            return None
        print("Please enter 1, 2, or q.")


def main(argv: list[str] | None = None) -> int:
    """Validate the runtime and launch the selected game."""
    parser = argparse.ArgumentParser(
        description="Launch the Multiplayer Ludo game. Game options are forwarded."
    )
    parser.add_argument(
        "--engine",
        choices=("oop", "functional"),
        help="Choose the OOP or functional game without a launcher prompt.",
    )
    args, game_args = parser.parse_known_args(argv)

    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required to play.")
        return 1

    engine = choose_engine(args.engine)
    if engine is None:
        return 0

    filename = "ludo_oop.py" if engine == "oop" else "ludo_func.py"
    project_dir = Path(__file__).resolve().parent
    game_path = project_dir / "v1_initial" / filename
    if not game_path.is_file():
        print(f"Could not find the game file: {game_path}")
        return 1

    command = [sys.executable, str(game_path), *game_args]
    try:
        result = subprocess.run(command, cwd=str(project_dir), check=False)
    except OSError as exc:
        print(f"Could not start the game: {exc}")
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
