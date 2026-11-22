#!/usr/bin/env python3
"""Seeded engine fuzz and subprocess CLI parity tests."""

from __future__ import annotations

import importlib.util
import os
import random
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TARGET = os.environ.get("LUDO_TARGET_DIR", "v1_initial")


def load_module(name: str, path: Path) -> Any:
    """Load a module directly from a stage file."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oop = load_module("oop_parity", ROOT / TARGET / "ludo_oop.py")
func = load_module("func_parity", ROOT / TARGET / "ludo_func.py")


CONFIGS = (
    ("quick", 2, 200),
    ("quick", 3, 200),
    ("quick", 4, 200),
    ("classic", 2, 150),
    ("classic", 3, 150),
    ("classic", 4, 100),
)


class ParityTest(unittest.TestCase):
    """1,000-game headless and subprocess parity."""

    def test_1000_game_fuzz_parity(self) -> None:
        """Compare canonical state after every roll and move."""
        game_number = 0
        for mode, num_players, count in CONFIGS:
            for offset in range(count):
                game_number += 1
                seed = 10000 + game_number
                names = [f"P{i + 1}" for i in range(num_players)]
                max_turns = 100 if mode == "quick" else 250
                oop_game = oop.LudoGame(mode, names, max_turns, seed)
                func_state = func.create_game_state(mode, names, max_turns, seed)
                choice_rng = random.Random(seed + 777)
                while oop_game.status == "PLAYING" and func_state["status"] == "PLAYING":
                    oop_roll = oop_game.roll_die()
                    func_roll = func.roll_die(func_state)
                    self.assertEqual(oop_roll, func_roll)

                    oop_result = oop_game.process_roll(oop_roll)
                    func_result = func.process_roll(func_state, oop_roll)
                    self.assertEqual(oop_result, func_result)
                    self.assertEqual(oop_game.export_canonical_state(),
                                     func.export_canonical_state(func_state))

                    valid_moves = oop_result["valid_moves"]
                    if valid_moves:
                        choice_idx = choice_rng.randrange(len(valid_moves))
                        token_idx = valid_moves[choice_idx]
                        oop_preview = oop_game.preview_move(
                            oop_game.current_player_index, token_idx, oop_roll
                        )
                        func_preview = func.preview_move(
                            func_state, func_state["current_player"], token_idx, oop_roll
                        )
                        self.assertEqual(oop_preview, func_preview)

                        oop_move = oop_game.apply_move(token_idx, oop_roll)
                        func_move = func.apply_move(func_state, token_idx, oop_roll)
                        self.assertEqual(oop_move, func_move)
                        self.assertEqual(oop_game.export_canonical_state(),
                                         func.export_canonical_state(func_state))

                        if not oop_move["bonus_turn"] and oop_game.status == "PLAYING":
                            oop_game.advance_turn()
                            func.advance_turn(func_state)
                            self.assertEqual(oop_game.export_canonical_state(),
                                             func.export_canonical_state(func_state))

                    if oop_game.status != "PLAYING" or func_state["status"] != "PLAYING":
                        self.assertEqual(oop_game.status, func_state["status"])
                        self.assertEqual(oop_game.winner_index, func_state["winner_index"])
                        self.assertEqual(oop_game.draw_reason, func_state["draw_reason"])
                        self.assertEqual(oop_game.turn_count, func_state["turn_count"])
                        break

        self.assertEqual(game_number, 1000)

    def run_cli(self, script: str, arguments: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
        """Run one CLI transcript."""
        return subprocess.run(
            [sys.executable, str(ROOT / TARGET / script), *arguments],
            input=stdin,
            text=True,
            capture_output=True,
            timeout=30,
        )

    def assert_cli_pair(self, arguments: list[str], stdin: str) -> None:
        """Assert identical stdout and exit code for both engines."""
        oop_process = self.run_cli("ludo_oop.py", arguments, stdin)
        func_process = self.run_cli("ludo_func.py", arguments, stdin)
        self.assertEqual(oop_process.returncode, func_process.returncode)
        self.assertEqual(oop_process.returncode, 0)
        self.assertEqual(oop_process.stdout, func_process.stdout)

    def test_subprocess_quick_full_and_invalid_inputs(self) -> None:
        moves = ["2\nAlice\nBob\n"] + [
            "abc\n99\n-1\n   \n\n1\n" for _ in range(1)
        ]
        stdin = "".join(moves)
        stdin += "\n1\n" * 300
        self.assert_cli_pair(
            ["--mode", "quick", "--seed", "42", "--no-color", "--max-turns", "100"],
            stdin,
        )

    def test_subprocess_quick_max_turn_draw(self) -> None:
        stdin = "3\nA\nB\nC\n" + ("\n1\n" * 40)
        self.assert_cli_pair(
            ["--mode", "quick", "--seed", "7", "--no-color", "--max-turns", "4"],
            stdin,
        )

    def test_subprocess_mutual_draw_declined_and_accepted(self) -> None:
        stdin = "2\nA\nB\ndraw\nn\n\ndraw\ny\ny\n"
        self.assert_cli_pair(
            ["--mode", "quick", "--seed", "11", "--no-color", "--max-turns", "30"],
            stdin,
        )

    def test_subprocess_quick_quit_confirmed(self) -> None:
        stdin = "2\nA\nB\nquit\nn\nquit\ny\n"
        self.assert_cli_pair(
            ["--mode", "quick", "--seed", "3", "--no-color", "--max-turns", "30"],
            stdin,
        )

    def test_subprocess_classic_quit_confirmed(self) -> None:
        stdin = "4\nA\nB\nC\nD\nquit\ny\n"
        self.assert_cli_pair(
            ["--mode", "classic", "--seed", "5", "--no-color", "--max-turns", "30"],
            stdin,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
