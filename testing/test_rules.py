#!/usr/bin/env python3
"""Cross-engine tests for configurable Ludo rules and event parity."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.contracts import build_config  # noqa: E402
from v1_initial.oop_ludo.engine import LudoGame  # noqa: E402
from v1_initial.oop_ludo.models import Board  # noqa: E402
from v1_initial.func_ludo.state import create_game_state  # noqa: E402
from v1_initial.func_ludo import rules as func_rules  # noqa: E402


def make_config(
    mode: str = "quick",
    profile: str = "showcase",
    count: int = 2,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a test configuration with explicit player count."""
    return build_config(mode, profile, count, overrides)


class OopAdapter:
    """Expose one common test interface for the OOP engine."""

    def create(self, config: dict[str, Any], seed: int | None = None) -> LudoGame:
        """Create an OOP game."""
        names = [f"P{index + 1}" for index in range(config["player_count"])]
        return LudoGame(config, names, seed=seed)

    def roll(self, game: LudoGame) -> int:
        """Roll the OOP die."""
        return game.roll_die()

    def process(self, game: LudoGame, roll: int) -> dict[str, Any]:
        """Process an OOP roll."""
        return game.process_roll(roll)

    def valid(self, game: LudoGame, roll: int) -> list[int]:
        """Return OOP valid moves."""
        return game.get_valid_moves(roll)

    def preview(self, game: LudoGame, token_idx: int, roll: int) -> dict[str, Any]:
        """Preview an OOP move."""
        return game.preview_move(game.current_player_index, token_idx, roll)

    def apply(self, game: LudoGame, token_idx: int, roll: int) -> dict[str, Any]:
        """Apply an OOP move."""
        return game.apply_move(token_idx, roll)

    def advance(self, game: LudoGame) -> None:
        """Advance an OOP turn."""
        game.advance_turn()

    def draw(self, game: LudoGame) -> None:
        """Declare an OOP mutual draw."""
        game.declare_mutual_draw()

    def set_token(self, game: LudoGame, player_idx: int, token_idx: int, steps: int) -> None:
        """Set an OOP token position."""
        game.players[player_idx].tokens[token_idx].steps = steps

    def set_captures(self, game: LudoGame, player_idx: int, captures: int) -> None:
        """Set an OOP capture count."""
        game.players[player_idx].captures_made = captures

    def token_steps(self, game: LudoGame, player_idx: int, token_idx: int) -> int:
        """Read an OOP token position."""
        return game.players[player_idx].tokens[token_idx].steps

    def captures(self, game: LudoGame, player_idx: int) -> int:
        """Read an OOP capture count."""
        return game.players[player_idx].captures_made

    def canonical(self, game: LudoGame) -> dict[str, Any]:
        """Export an OOP snapshot."""
        return game.export_canonical_state()

    def current(self, game: LudoGame) -> int:
        """Read the OOP active player."""
        return game.current_player_index

    def set_current(self, game: LudoGame, player_idx: int) -> None:
        """Set the OOP active player for a focused fixture."""
        game.current_player_index = player_idx

    def status(self, game: LudoGame) -> str:
        """Read the OOP match status."""
        return game.status

    def finish_order(self, game: LudoGame) -> list[int]:
        """Read the OOP finish order."""
        return list(game.finish_order)


class FuncAdapter:
    """Expose the same test interface for the functional engine."""

    def create(self, config: dict[str, Any], seed: int | None = None) -> dict[str, Any]:
        """Create a functional state."""
        names = [f"P{index + 1}" for index in range(config["player_count"])]
        return create_game_state(config, names, seed=seed)

    def roll(self, state: dict[str, Any]) -> int:
        """Roll the functional die."""
        return func_rules.roll_die(state)

    def process(self, state: dict[str, Any], roll: int) -> dict[str, Any]:
        """Process a functional roll."""
        return func_rules.process_roll(state, roll)

    def valid(self, state: dict[str, Any], roll: int) -> list[int]:
        """Return functional valid moves."""
        return func_rules.get_valid_moves(state, state["current_player"], roll)

    def preview(self, state: dict[str, Any], token_idx: int, roll: int) -> dict[str, Any]:
        """Preview a functional move."""
        return func_rules.preview_move(state, state["current_player"], token_idx, roll)

    def apply(self, state: dict[str, Any], token_idx: int, roll: int) -> dict[str, Any]:
        """Apply a functional move."""
        return func_rules.apply_move(state, token_idx, roll)

    def advance(self, state: dict[str, Any]) -> None:
        """Advance a functional turn."""
        func_rules.advance_turn(state)

    def draw(self, state: dict[str, Any]) -> None:
        """Declare a functional mutual draw."""
        func_rules.declare_mutual_draw(state)

    def set_token(self, state: dict[str, Any], player_idx: int, token_idx: int, steps: int) -> None:
        """Set a functional token position."""
        state["players"][player_idx]["tokens"][token_idx]["steps"] = steps

    def set_captures(self, state: dict[str, Any], player_idx: int, captures: int) -> None:
        """Set a functional capture count."""
        state["players"][player_idx]["captures_made"] = captures

    def token_steps(self, state: dict[str, Any], player_idx: int, token_idx: int) -> int:
        """Read a functional token position."""
        return state["players"][player_idx]["tokens"][token_idx]["steps"]

    def captures(self, state: dict[str, Any], player_idx: int) -> int:
        """Read a functional capture count."""
        return state["players"][player_idx]["captures_made"]

    def canonical(self, state: dict[str, Any]) -> dict[str, Any]:
        """Export a functional snapshot."""
        return func_rules.export_canonical_state(state)

    def current(self, state: dict[str, Any]) -> int:
        """Read the functional active player."""
        return state["current_player"]

    def set_current(self, state: dict[str, Any], player_idx: int) -> None:
        """Set the functional active player for a focused fixture."""
        state["current_player"] = player_idx

    def status(self, state: dict[str, Any]) -> str:
        """Read the functional match status."""
        return state["status"]

    def finish_order(self, state: dict[str, Any]) -> list[int]:
        """Read the functional finish order."""
        return list(state["finish_order"])


ADAPTERS = (OopAdapter(), FuncAdapter())


class ConfigurableRuleTest(unittest.TestCase):
    """Exercise the same observable rules through both paradigms."""

    def test_initial_snapshots_and_events_match(self) -> None:
        config = make_config(count=3, overrides={"tokens_per_player": 3})
        oop_game = ADAPTERS[0].create(config, seed=42)
        func_state = ADAPTERS[1].create(config, seed=42)
        self.assertEqual(ADAPTERS[0].canonical(oop_game), ADAPTERS[1].canonical(func_state))
        self.assertEqual(ADAPTERS[0].roll(oop_game), ADAPTERS[1].roll(func_state))
        self.assertEqual(ADAPTERS[0].canonical(oop_game), ADAPTERS[1].canonical(func_state))

    def test_base_unlock_and_exact_home(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"))
                self.assertEqual(adapter.valid(game, 5), [])
                adapter.process(game, 6)
                move = adapter.apply(game, 0, 6)
                self.assertEqual(adapter.token_steps(game, 0, 0), 0)
                self.assertTrue(move["bonus_turn"])
                adapter.set_token(game, 0, 0, 29)
                self.assertEqual(adapter.valid(game, 2), [0])
                self.assertEqual(adapter.valid(game, 3), [])

    def test_circular_wrap_and_private_home_boundary(self) -> None:
        board = Board(make_config(profile="classic"))
        self.assertEqual(board.get_global_pos(14, 13), 27)
        self.assertEqual(board.get_global_pos(14, 14), 0)
        self.assertIsNone(board.get_global_pos(0, 27))
        self.assertEqual(func_rules.get_global_pos(14, 13, 28, 26), 27)
        self.assertEqual(func_rules.get_global_pos(14, 14, 28, 26), 0)
        self.assertIsNone(func_rules.get_global_pos(0, 27, 28, 26))
        classic = Board(make_config(mode="classic", profile="classic"))
        self.assertEqual(classic.get_global_pos(39, 50), 37)
        self.assertIsNone(classic.get_global_pos(39, 51))

    def test_friendly_stack_is_not_captured_or_blocking(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 2)
                adapter.set_token(game, 0, 1, 3)
                move = adapter.apply(game, 0, 1)
                self.assertEqual(move["captured"], [])
                self.assertEqual(adapter.token_steps(game, 0, 1), 3)

                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 6)
                adapter.set_token(game, 0, 1, 6)
                adapter.set_token(game, 1, 0, 15)
                adapter.set_current(game, 1)
                self.assertIn(0, adapter.valid(game, 2))
                move = adapter.apply(game, 0, 2)
                self.assertEqual(move["captured"], [])
                self.assertEqual(adapter.token_steps(game, 0, 0), 6)
                self.assertEqual(adapter.token_steps(game, 0, 1), 6)

    def test_home_bonus_resets_six_streak(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"))
                adapter.process(game, 6)
                adapter.apply(game, 0, 6)
                adapter.set_token(game, 0, 0, 25)
                adapter.set_token(game, 0, 1, 30)
                result = adapter.process(game, 6)
                self.assertEqual(result["valid_moves"], [0])
                move = adapter.apply(game, 0, 6)
                self.assertTrue(move["reached_home"])
                self.assertTrue(move["bonus_turn"])
                state = adapter.canonical(game)
                self.assertEqual(state["consecutive_sixes"], 0)
                self.assertEqual(state["current_player"], 0)

    def test_capture_bonus_does_not_stack(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 4)
                adapter.set_token(game, 1, 0, 22)
                adapter.process(game, 6)
                capture = adapter.apply(game, 0, 6)
                self.assertTrue(capture["bonus_turn"])
                self.assertEqual(adapter.current(game), 0)
                self.assertEqual(adapter.canonical(game)["consecutive_sixes"], 1)

                adapter.set_token(game, 0, 0, 8)
                adapter.set_token(game, 0, 1, 31)
                adapter.set_token(game, 1, 0, 31)
                adapter.process(game, 1)
                normal_move = adapter.apply(game, 0, 1)
                self.assertFalse(normal_move["bonus_turn"])
                self.assertEqual(adapter.current(game), 1)
                self.assertEqual(adapter.canonical(game)["turn_count"], 1)

    def test_triple_six_forfeit_and_auto_skip(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__, event="triple_six"):
                game = adapter.create(make_config(profile="classic"))
                self.assertEqual(adapter.process(game, 6)["event"], "SELECT_MOVE")
                self.assertEqual(adapter.process(game, 6)["event"], "SELECT_MOVE")
                result = adapter.process(game, 6)
                state = adapter.canonical(game)
                self.assertEqual(result["event"], "TRIPLE_SIX_FORFEIT")
                self.assertEqual(state["consecutive_sixes"], 0)
                self.assertEqual(state["turn_count"], 1)
                self.assertEqual(state["current_player"], 1)
            with self.subTest(adapter=type(adapter).__name__, event="auto_skip"):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 30)
                adapter.set_token(game, 0, 1, 31)
                result = adapter.process(game, 6)
                state = adapter.canonical(game)
                self.assertEqual(result["event"], "NO_VALID_MOVES")
                self.assertEqual(state["consecutive_sixes"], 0)
                self.assertEqual(state["turn_count"], 1)
                self.assertEqual(state["current_player"], 1)

    def test_immediate_two_player_victory(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 30)
                adapter.set_token(game, 0, 1, 31)
                move = adapter.apply(game, 0, 1)
                state = adapter.canonical(game)
                self.assertTrue(move["won"])
                self.assertFalse(move["bonus_turn"])
                self.assertEqual(state["status"], "WON")
                self.assertEqual(state["winner_index"], 0)
                self.assertEqual(state["turn_count"], 0)

    def test_mutual_draw_preserves_turn_count(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"))
                adapter.draw(game)
                state = adapter.canonical(game)
                self.assertEqual(state["status"], "DRAW")
                self.assertEqual(state["draw_reason"], "Mutual agreement")
                self.assertEqual(state["turn_count"], 0)

    def test_non_exact_home_clamps_finish(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                config = make_config(profile="classic", overrides={"exact_home_roll": False})
                game = adapter.create(config)
                adapter.set_token(game, 0, 0, 29)
                move = adapter.apply(game, 0, 6)
                self.assertEqual(adapter.token_steps(game, 0, 0), 31)
                self.assertTrue(move["reached_home"])

    def test_safe_tile_and_disabled_safe_tiles(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__, safe=True):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 6)
                adapter.set_token(game, 1, 0, 21)
                move = adapter.apply(game, 0, 1)
                self.assertEqual(move["captured"], [])
                self.assertEqual(adapter.token_steps(game, 1, 0), 21)
            with self.subTest(adapter=type(adapter).__name__, safe=False):
                config = make_config(profile="classic", overrides={"safe_tiles_enabled": False})
                game = adapter.create(config)
                adapter.set_token(game, 1, 0, 14)
                move = adapter.apply(game, 0, 6)
                self.assertEqual(adapter.token_steps(game, 1, 0), -1)
                self.assertEqual(adapter.captures(game, 0), 1)

    def test_single_and_multi_token_capture(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__, stacked=False):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 4)
                adapter.set_token(game, 1, 0, 22)
                move = adapter.apply(game, 0, 4)
                self.assertEqual(len(move["captured"]), 1)
                self.assertEqual(adapter.token_steps(game, 1, 0), -1)
            with self.subTest(adapter=type(adapter).__name__, stacked=True):
                game = adapter.create(make_config(profile="classic"))
                adapter.set_token(game, 0, 0, 4)
                adapter.set_token(game, 1, 0, 22)
                adapter.set_token(game, 1, 1, 22)
                move = adapter.apply(game, 0, 4)
                self.assertEqual(len(move["captured"]), 2)
                self.assertEqual(adapter.captures(game, 0), 2)

    def test_strict_blockade_blocks_landing_and_crossing(self) -> None:
        for adapter in ADAPTERS:
            for start_steps, roll in ((2, 4), (1, 5)):
                with self.subTest(adapter=type(adapter).__name__, start=start_steps):
                    config = make_config(overrides={"blockades": "strict"})
                    game = adapter.create(config)
                    adapter.set_token(game, 0, 0, start_steps)
                    adapter.set_token(game, 1, 0, 20)
                    adapter.set_token(game, 1, 1, 20)
                    self.assertNotIn(0, adapter.valid(game, roll))

    def test_strict_blockade_checks_intermediate_tiles(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                config = make_config(overrides={"blockades": "strict"})
                game = adapter.create(config)
                adapter.set_token(game, 0, 0, 1)
                adapter.set_token(game, 1, 0, 18)
                adapter.set_token(game, 1, 1, 18)
                self.assertNotIn(0, adapter.valid(game, 5))

    def test_safe_pair_can_be_passed_but_not_captured(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(overrides={"blockades": "safe_pair"}))
                adapter.set_token(game, 0, 0, 2)
                adapter.set_token(game, 1, 0, 20)
                adapter.set_token(game, 1, 1, 20)
                self.assertIn(0, adapter.valid(game, 4))
                move = adapter.apply(game, 0, 4)
                self.assertEqual(move["captured"], [])
                self.assertEqual(adapter.token_steps(game, 1, 0), 20)

    def test_no_blockade_mode_captures_stack(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(overrides={"blockades": "none"}))
                adapter.set_token(game, 0, 0, 2)
                adapter.set_token(game, 1, 0, 20)
                adapter.set_token(game, 1, 1, 20)
                move = adapter.apply(game, 0, 4)
                self.assertEqual(len(move["captured"]), 2)

    def test_kill_to_enter_loops_until_first_capture(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__, unlocked=False):
                game = adapter.create(make_config())
                adapter.set_token(game, 0, 0, 26)
                move = adapter.apply(game, 0, 1)
                self.assertEqual(adapter.token_steps(game, 0, 0), 0)
                self.assertTrue(move["wrapped"])
            with self.subTest(adapter=type(adapter).__name__, unlocked=True):
                game = adapter.create(make_config())
                adapter.set_token(game, 0, 0, 26)
                adapter.set_token(game, 0, 1, 26)
                adapter.set_captures(game, 0, 1)
                self.assertEqual(adapter.valid(game, 1), [0, 1])
                move = adapter.apply(game, 0, 1)
                self.assertEqual(adapter.token_steps(game, 0, 0), 27)
                self.assertFalse(move["wrapped"])

    def test_podium_continues_until_one_player_remains(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                config = make_config(count=3, overrides={"tokens_per_player": 2})
                game = adapter.create(config)
                adapter.set_token(game, 0, 0, 30)
                adapter.set_token(game, 0, 1, 31)
                adapter.apply(game, 0, 1)
                self.assertEqual(adapter.finish_order(game), [0])
                self.assertEqual(adapter.status(game), "PLAYING")
                self.assertNotEqual(adapter.current(game), 0)

                adapter.set_token(game, 1, 0, 30)
                adapter.set_token(game, 1, 1, 31)
                adapter.apply(game, 0, 1)
                self.assertEqual(adapter.finish_order(game), [0, 1])
                self.assertEqual(adapter.status(game), "WON")
                self.assertEqual(adapter.canonical(game)["winner_index"], 0)

    def test_bonus_toggles_are_independent(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__, source="capture"):
                config = make_config(
                    profile="classic",
                    overrides={"bonus_on_capture": False},
                )
                game = adapter.create(config)
                adapter.set_token(game, 0, 0, 4)
                adapter.set_token(game, 1, 0, 22)
                move = adapter.apply(game, 0, 4)
                self.assertFalse(move["bonus_turn"])
            with self.subTest(adapter=type(adapter).__name__, source="home"):
                config = make_config(
                    profile="classic",
                    overrides={"bonus_on_home": False},
                )
                game = adapter.create(config)
                adapter.set_token(game, 0, 0, 29)
                move = adapter.apply(game, 0, 2)
                self.assertTrue(move["reached_home"])
                self.assertFalse(move["bonus_turn"])

    def test_triple_six_forfeit_can_be_disabled(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                config = make_config(
                    profile="classic",
                    overrides={"triple_six_forfeit": False},
                )
                game = adapter.create(config)
                results = [adapter.process(game, 6) for _ in range(3)]
                self.assertTrue(all(result["event"] == "SELECT_MOVE" for result in results))
                self.assertEqual(adapter.canonical(game)["consecutive_sixes"], 3)

    def test_canonical_snapshots_are_independent_copies(self) -> None:
        for adapter in ADAPTERS:
            with self.subTest(adapter=type(adapter).__name__):
                game = adapter.create(make_config(profile="classic"), seed=42)
                snapshot = adapter.canonical(game)
                snapshot["config"]["safe_tiles"].append(99)
                snapshot["players"][0]["tokens"][0]["steps"] = 99
                snapshot["events"][0]["data"]["mode"] = "changed"
                snapshot["events"].append({"type": "GAME_QUIT"})
                fresh = adapter.canonical(game)
                self.assertNotIn(99, fresh["config"]["safe_tiles"])
                self.assertEqual(fresh["players"][0]["tokens"][0]["steps"], -1)
                self.assertEqual(fresh["events"][0]["data"]["mode"], "quick")
                self.assertEqual(len(fresh["events"]), 1)

    def test_max_turn_draw_and_event_parity(self) -> None:
        config = make_config(profile="classic", overrides={"max_turns": 1})
        oop_game = ADAPTERS[0].create(config, seed=9)
        func_state = ADAPTERS[1].create(config, seed=9)
        ADAPTERS[0].advance(oop_game)
        ADAPTERS[1].advance(func_state)
        self.assertEqual(ADAPTERS[0].status(oop_game), "DRAW")
        self.assertEqual(ADAPTERS[0].canonical(oop_game), ADAPTERS[1].canonical(func_state))
        event_types = [event["type"] for event in ADAPTERS[0].canonical(oop_game)["events"]]
        self.assertIn("GAME_STARTED", event_types)
        self.assertIn("TURN_ADVANCED", event_types)
        self.assertIn("GAME_DRAW", event_types)


if __name__ == "__main__":
    unittest.main(verbosity=2)
