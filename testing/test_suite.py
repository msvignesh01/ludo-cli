#!/usr/bin/env python3
"""Unit and edge-case tests for both Ludo engines."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TARGET = os.environ.get("LUDO_TARGET_DIR", "v1_initial")


def load_module(name: str, path: Path) -> Any:
    """Load a Python module from an explicit path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oop = load_module("oop_ludo", ROOT / TARGET / "ludo_oop.py")
func = load_module("func_ludo", ROOT / TARGET / "ludo_func.py")


class OopAdapter:
    """Small test adapter for the class-based engine."""

    def create(self, mode: str, names: list[str], max_turns: int | None = None,
               seed: int | None = None) -> Any:
        """Create an OOP game."""
        return oop.LudoGame(mode, names, max_turns, seed)

    def roll(self, game: Any) -> int:
        """Roll in an OOP game."""
        return game.roll_die()

    def process(self, game: Any, roll: int) -> dict[str, Any]:
        """Process a roll."""
        return game.process_roll(roll)

    def valid(self, game: Any, roll: int) -> list[int]:
        """Get valid moves."""
        return game.get_valid_moves(roll)

    def preview(self, game: Any, player_idx: int, token_idx: int, roll: int) -> dict[str, Any]:
        """Preview a move."""
        return game.preview_move(player_idx, token_idx, roll)

    def apply(self, game: Any, token_idx: int, roll: int) -> dict[str, Any]:
        """Apply a move."""
        return game.apply_move(token_idx, roll)

    def advance(self, game: Any) -> None:
        """Advance one turn."""
        game.advance_turn()

    def draw(self, game: Any) -> None:
        """Declare a draw."""
        game.declare_mutual_draw()

    def canonical(self, game: Any) -> dict[str, Any]:
        """Export canonical state."""
        return game.export_canonical_state()

    def set_token(self, game: Any, player_idx: int, token_idx: int, steps: int) -> None:
        """Set a token position."""
        game.players[player_idx].tokens[token_idx].steps = steps

    def token_steps(self, game: Any, player_idx: int, token_idx: int) -> int:
        """Read a token position."""
        return game.players[player_idx].tokens[token_idx].steps

    def global_pos(self, game: Any, player_idx: int, steps: int) -> int | None:
        """Compute a global position."""
        return game.board.get_global_pos(game.players[player_idx].start_index, steps)

    def board(self, game: Any) -> Any:
        """Return the board."""
        return game.board


class FuncAdapter:
    """Small test adapter for the function-based engine."""

    def create(self, mode: str, names: list[str], max_turns: int | None = None,
               seed: int | None = None) -> dict[str, Any]:
        """Create functional state."""
        return func.create_game_state(mode, names, max_turns, seed)

    def roll(self, state: dict[str, Any]) -> int:
        """Roll in functional state."""
        return func.roll_die(state)

    def process(self, state: dict[str, Any], roll: int) -> dict[str, Any]:
        """Process a roll."""
        return func.process_roll(state, roll)

    def valid(self, state: dict[str, Any], roll: int) -> list[int]:
        """Get valid moves."""
        return func.get_valid_moves(state, state["current_player"], roll)

    def preview(self, state: dict[str, Any], player_idx: int, token_idx: int,
                roll: int) -> dict[str, Any]:
        """Preview a move."""
        return func.preview_move(state, player_idx, token_idx, roll)

    def apply(self, state: dict[str, Any], token_idx: int, roll: int) -> dict[str, Any]:
        """Apply a move."""
        return func.apply_move(state, token_idx, roll)

    def advance(self, state: dict[str, Any]) -> None:
        """Advance one turn."""
        func.advance_turn(state)

    def draw(self, state: dict[str, Any]) -> None:
        """Declare a draw."""
        func.declare_mutual_draw(state)

    def canonical(self, state: dict[str, Any]) -> dict[str, Any]:
        """Export canonical state."""
        return func.export_canonical_state(state)

    def set_token(self, state: dict[str, Any], player_idx: int, token_idx: int, steps: int) -> None:
        """Set a token position."""
        state["players"][player_idx]["tokens"][token_idx]["steps"] = steps

    def token_steps(self, state: dict[str, Any], player_idx: int, token_idx: int) -> int:
        """Read a token position."""
        return state["players"][player_idx]["tokens"][token_idx]["steps"]

    def global_pos(self, state: dict[str, Any], player_idx: int, steps: int) -> int | None:
        """Compute a global position."""
        player = state["players"][player_idx]
        return func.get_global_pos(player["start_index"], steps, state["config"]["track_len"])

    def board(self, state: dict[str, Any]) -> dict[str, Any]:
        """Return configuration as an equivalent board view."""
        return state["config"]


ADAPTERS = (OopAdapter(), FuncAdapter())


class RuleTest(unittest.TestCase):
    """Exhaustive cross-engine unit tests."""

    def test_01_quick_preset(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            board = adapter.board(game)
            if hasattr(board, "track_len"):
                values = (board.track_len, board.home_len, board.tokens_per_player,
                          board.home_finish, set(board.safe_tiles))
            else:
                values = (board["track_len"], board["home_len"], board["tokens_per_player"],
                          board["home_finish"], set(board["safe_tiles"]))
            self.assertEqual(values, (28, 4, 2, 31, {0, 7, 14, 21}))

    def test_02_classic_preset(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("classic", ["A", "B"])
            board = adapter.board(game)
            values = ((board.track_len, board.home_len, board.tokens_per_player,
                       board.home_finish, set(board.safe_tiles)) if hasattr(board, "track_len")
                      else (board["track_len"], board["home_len"], board["tokens_per_player"],
                            board["home_finish"], set(board["safe_tiles"])))
            self.assertEqual(values, (52, 5, 4, 56, {0, 8, 13, 21, 26, 34, 39, 47}))

    def test_03_seating_2p(self) -> None:
        for mode, expected in (("quick", [0, 14]), ("classic", [0, 26])):
            game_o = oop.LudoGame(mode, ["A", "B"])
            game_f = func.create_game_state(mode, ["A", "B"])
            self.assertEqual([p.start_index for p in game_o.players], expected)
            self.assertEqual([p["start_index"] for p in game_f["players"]], expected)

    def test_04_seating_3p_4p(self) -> None:
        game_o = oop.LudoGame("quick", ["A", "B", "C", "D"])
        game_f = func.create_game_state("quick", ["A", "B", "C", "D"])
        self.assertEqual([p.start_index for p in game_o.players], [0, 7, 14, 21])
        self.assertEqual([p["start_index"] for p in game_f["players"]], [0, 7, 14, 21])
        classic = oop.LudoGame("classic", ["A", "B", "C", "D"])
        self.assertEqual([p.start_index for p in classic.players], [0, 13, 26, 39])

    def test_05_unlock_blocked_rolls_1_to_5(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            for roll in range(1, 6):
                self.assertEqual(adapter.valid(game, roll), [])

    def test_06_unlock_on_six_and_bonus(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            result = adapter.process(game, 6)
            self.assertIn(0, result["valid_moves"])
            move = adapter.apply(game, result["valid_moves"][0], 6)
            self.assertEqual(adapter.token_steps(game, 0, 0), 0)
            self.assertTrue(move["bonus_turn"])

    def test_07_wrap_modulo(self) -> None:
        self.assertIsNone(oop.Board("quick").get_global_pos(14, -1))
        self.assertEqual(oop.Board("quick").get_global_pos(14, 13), 27)
        self.assertEqual(oop.Board("quick").get_global_pos(14, 14), 0)
        self.assertEqual(func.get_global_pos(14, 13, 28), 27)
        self.assertEqual(func.get_global_pos(14, 14, 28), 0)

    def test_08_private_home_entry(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 26)
            move = adapter.apply(game, 0, 1)
            self.assertEqual(adapter.token_steps(game, 0, 0), 27)
            self.assertIsNone(adapter.global_pos(game, 0, 27))

    def test_09_exact_home_and_overshoot(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 29)
            self.assertEqual(adapter.valid(game, 1), [0])
            self.assertEqual(adapter.valid(game, 2), [0])
            self.assertEqual(adapter.valid(game, 3), [])
            move = adapter.apply(game, 0, 2)
            self.assertTrue(move["reached_home"])
            self.assertEqual(adapter.token_steps(game, 0, 0), 31)

    def test_10_single_capture(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 4)
            adapter.set_token(game, 1, 0, 22)
            move = adapter.apply(game, 0, 4)
            self.assertIn("G1", " ".join(move["captured"]))
            self.assertTrue(move["bonus_turn"])
            self.assertEqual(adapter.token_steps(game, 1, 0), -1)

    def test_11_multi_token_capture(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("classic", ["A", "B"])
            adapter.set_token(game, 0, 0, 4)
            adapter.set_token(game, 1, 0, 35)
            adapter.set_token(game, 1, 1, 35)
            move = adapter.apply(game, 0, 5)
            self.assertEqual(len(move["captured"]), 2)
            self.assertTrue(move["bonus_turn"])
            self.assertEqual(adapter.token_steps(game, 1, 0), -1)
            self.assertEqual(adapter.token_steps(game, 1, 1), -1)

    def test_12_safe_tile_no_capture(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 6)
            adapter.set_token(game, 1, 0, 21)
            move = adapter.apply(game, 0, 1)
            self.assertEqual(move["captured"], [])
            self.assertFalse(move["bonus_turn"])
            self.assertEqual(adapter.token_steps(game, 1, 0), 21)

    def test_13_same_color_stack_no_capture(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 2)
            adapter.set_token(game, 0, 1, 3)
            move = adapter.apply(game, 0, 1)
            self.assertEqual(move["captured"], [])
            self.assertEqual(adapter.token_steps(game, 0, 1), 3)

    def test_14_home_bonus_and_reset_sixes(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 29)
            adapter.set_token(game, 0, 1, 30)
            move = adapter.apply(game, 0, 2)
            self.assertTrue(move["reached_home"])
            self.assertTrue(move["bonus_turn"])

    def test_15_bonus_non_stacking_and_next_passes(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 4)
            adapter.set_token(game, 1, 0, 4)
            move = adapter.apply(game, 0, 6)
            self.assertTrue(move["bonus_turn"])
            adapter.set_token(game, 0, 0, 30)
            move = adapter.apply(game, 0, 1)
            self.assertTrue(move["reached_home"])

    def test_16_triple_six_forfeit(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.process(game, 6)
            adapter.process(game, 6)
            before = adapter.canonical(game)["turn_count"]
            result = adapter.process(game, 6)
            state = adapter.canonical(game)
            self.assertEqual(result["event"], "TRIPLE_SIX_FORFEIT")
            self.assertEqual(state["consecutive_sixes"], 0)
            self.assertEqual(state["turn_count"], before + 1)

    def test_17_six_streak_reset_on_non_six_capture(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.process(game, 6)
            adapter.process(game, 4)
            state = adapter.canonical(game)
            self.assertEqual(state["consecutive_sixes"], 0)

    def test_18_auto_skip_roll_six_no_legal_move(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 30)
            adapter.set_token(game, 0, 1, 31)
            before = adapter.canonical(game)["turn_count"]
            result = adapter.process(game, 6)
            state = adapter.canonical(game)
            self.assertEqual(result["event"], "NO_VALID_MOVES")
            self.assertEqual(state["turn_count"], before + 1)

    def test_19_immediate_victory(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            adapter.set_token(game, 0, 0, 30)
            adapter.set_token(game, 0, 1, 31)
            move = adapter.apply(game, 0, 1)
            state = adapter.canonical(game)
            self.assertTrue(move["won"])
            self.assertFalse(move["bonus_turn"])
            self.assertEqual(state["status"], "WON")
            self.assertEqual(state["winner_index"], 0)

    def test_20_max_turn_draw(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"], max_turns=1)
            adapter.advance(game)
            state = adapter.canonical(game)
            self.assertEqual(state["status"], "DRAW")
            self.assertEqual(state["draw_reason"], "Maximum turn limit reached")

    def test_21_mutual_draw_accepted_and_declined(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            before = adapter.canonical(game)["turn_count"]
            adapter.draw(game)
            state = adapter.canonical(game)
            self.assertEqual(state["status"], "DRAW")
            self.assertEqual(state["draw_reason"], "Mutual agreement")
            self.assertEqual(state["turn_count"], before)

    def test_22_invalid_inputs_resilience(self) -> None:
        for value in ("", "abc", "@#$", "-5", "99", "1.5", "   "):
            for adapter in ADAPTERS:
                game = adapter.create("quick", ["A", "B"])
                try:
                    int(value.strip())
                except ValueError:
                    valid = adapter.valid(game, 1)
                    self.assertIsInstance(valid, list)

    def test_23_no_color_purity(self) -> None:
        for script in ("ludo_oop.py", "ludo_func.py"):
            result = subprocess.run(
                [sys.executable, str(ROOT / TARGET / script), "--mode", "quick",
                 "--seed", "1", "--no-color", "--max-turns", "1"],
                input="2\nA\nB\nq\nn\n",
                text=True,
                capture_output=True,
                timeout=15,
            )
            self.assertNotIn("\033[", result.stdout)

    def test_24_invalid_max_turns_zero(self) -> None:
        for script in ("ludo_oop.py", "ludo_func.py"):
            result = subprocess.run(
                [sys.executable, str(ROOT / TARGET / script), "--max-turns", "0"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_25_canonical_states_match_initially(self) -> None:
        game_o = oop.LudoGame("quick", ["A", "B"], 100, 42)
        game_f = func.create_game_state("quick", ["A", "B"], 100, 42)
        self.assertEqual(game_o.export_canonical_state(),
                         func.export_canonical_state(game_f))

    def test_26_classic_wrap_boundary(self) -> None:
        board = oop.Board("classic")
        self.assertEqual(board.get_global_pos(39, 50), 37)
        self.assertIsNone(board.get_global_pos(39, 51))

    def test_27_safe_tiles_classic(self) -> None:
        board = oop.Board("classic")
        for tile in (8, 21, 34, 47):
            self.assertTrue(board.is_safe_tile(tile))

    def test_28_quit_status_option(self) -> None:
        for adapter in ADAPTERS:
            game = adapter.create("quick", ["A", "B"])
            if isinstance(game, oop.LudoGame):
                game.status = "QUIT"
                self.assertEqual(adapter.canonical(game)["status"], "QUIT")
            else:
                game["status"] = "QUIT"
                self.assertEqual(adapter.canonical(game)["status"], "QUIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
