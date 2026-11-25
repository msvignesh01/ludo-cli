#!/usr/bin/env python3
"""Tests for deterministic bot policy and dual-style commentary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.contracts import build_config, make_event  # noqa: E402
from v1_initial.oop_ludo.bot import BotPolicy  # noqa: E402
from v1_initial.oop_ludo.commentary import Commentary as OopCommentary  # noqa: E402
from v1_initial.oop_ludo.engine import LudoGame  # noqa: E402
from v1_initial.func_ludo.bot import choose_move, decision_details  # noqa: E402
from v1_initial.func_ludo.commentary import code_message, gameplay_message  # noqa: E402
from v1_initial.func_ludo.rules import record_bot_decision  # noqa: E402
from v1_initial.func_ludo.state import create_game_state, export_canonical_state  # noqa: E402


NAMES = ["P1", "P2"]


def make_config(**overrides: Any) -> dict[str, Any]:
    """Create a standard two-player test configuration."""
    return build_config("quick", "classic", 2, overrides)


def make_oop(seed: int = 42, **overrides: Any) -> LudoGame:
    """Create an OOP game for bot tests."""
    return LudoGame(make_config(**overrides), NAMES, seed=seed)


def make_func(seed: int = 42, **overrides: Any) -> dict[str, Any]:
    """Create a functional state for bot tests."""
    return create_game_state(make_config(**overrides), NAMES, seed=seed)


def set_steps(game: Any, paradigm: str, player: int, token: int, steps: int) -> None:
    """Set a token fixture in either paradigm."""
    if paradigm == "oop":
        game.players[player].tokens[token].steps = steps
    else:
        game["players"][player]["tokens"][token]["steps"] = steps


class BotPolicyTest(unittest.TestCase):
    """Verify the requested priority list and deterministic behavior."""

    def test_home_finish_has_highest_priority(self) -> None:
        game = make_oop()
        set_steps(game, "oop", 0, 0, 29)
        set_steps(game, "oop", 0, 1, 4)
        set_steps(game, "oop", 1, 0, 22)
        choice = BotPolicy().choose_move(game, 2, [0, 1])
        self.assertEqual(choice, 0)
        self.assertEqual(BotPolicy().decision_details(game, 2, [0, 1])["reason"], "Finish Home")

    def test_capture_has_priority_over_safe_landing(self) -> None:
        game = make_oop()
        set_steps(game, "oop", 0, 0, 4)
        set_steps(game, "oop", 0, 1, 6)
        set_steps(game, "oop", 1, 0, 22)
        choice = BotPolicy().choose_move(game, 4, [0, 1])
        self.assertEqual(choice, 0)
        self.assertEqual(BotPolicy().decision_details(game, 4, [0, 1])["reason"], "Capture")

    def test_safe_tile_has_priority_over_advance(self) -> None:
        game = make_oop()
        set_steps(game, "oop", 0, 0, 3)
        set_steps(game, "oop", 0, 1, 8)
        choice = BotPolicy().choose_move(game, 4, [0, 1])
        self.assertEqual(choice, 0)
        self.assertEqual(BotPolicy().decision_details(game, 4, [0, 1])["reason"], "Safe tile")

    def test_escape_danger_beats_slower_safe_advance(self) -> None:
        game = make_oop(safe_tiles_enabled=False)
        set_steps(game, "oop", 0, 0, 4)
        set_steps(game, "oop", 0, 1, 2)
        set_steps(game, "oop", 1, 0, 12)
        choice = BotPolicy().choose_move(game, 6, [0, 1])
        self.assertEqual(choice, 0)
        self.assertEqual(BotPolicy().decision_details(game, 6, [0, 1])["reason"], "Escape danger")

    def test_furthest_advance_and_lowest_index_tie_break(self) -> None:
        game = make_oop()
        set_steps(game, "oop", 0, 0, 8)
        set_steps(game, "oop", 0, 1, 9)
        choice = BotPolicy().choose_move(game, 1, [0, 1])
        self.assertEqual(choice, 1)
        self.assertEqual(BotPolicy().decision_details(game, 1, [0, 1])["reason"], "Advance furthest")

        set_steps(game, "oop", 0, 1, 8)
        self.assertEqual(BotPolicy().choose_move(game, 1, [0, 1]), 0)

    def test_empty_valid_list_returns_no_decision(self) -> None:
        game = make_oop()
        self.assertIsNone(BotPolicy().choose_move(game, 3, []))
        self.assertEqual(BotPolicy().decision_details(game, 3, []), {"token_idx": None, "reason": "No legal moves"})

    def test_both_paradigms_choose_the_same_move(self) -> None:
        oop_game = make_oop()
        func_game = make_func()
        for paradigm, game in (("oop", oop_game), ("func", func_game)):
            set_steps(game, paradigm, 0, 0, 4)
            set_steps(game, paradigm, 0, 1, 8)
        oop_choice = BotPolicy().choose_move(oop_game, 4, [0, 1])
        func_choice = choose_move(func_game, 0, 4, [0, 1])
        self.assertEqual(oop_choice, func_choice)
        self.assertEqual(
            BotPolicy().decision_details(oop_game, 4, [0, 1]),
            decision_details(func_game, 0, 4, [0, 1]),
        )

    def test_bot_decision_event_has_exact_parity(self) -> None:
        oop_game = make_oop()
        func_game = make_func()
        oop_game.record_bot_decision(1, 4, "Safe tile")
        record_bot_decision(func_game, 1, 4, "Safe tile")
        self.assertEqual(
            oop_game.export_canonical_state(),
            export_canonical_state(func_game),
        )


class CommentaryTest(unittest.TestCase):
    """Verify gameplay parity and paradigm-specific code narration."""

    def test_gameplay_commentary_is_identical_for_same_events(self) -> None:
        events = [
            make_event("DICE_ROLLED", 0, 0, {"roll": 6}),
            make_event("TOKEN_MOVED", 0, 0, {"token": "R1", "token_idx": 0, "roll": 6}),
            make_event("TOKEN_CAPTURED", 0, 0, {"victim_player": 1, "victim_token": "G1"}),
            make_event("GAME_WON", 4, 0, {}),
        ]
        oop = OopCommentary(NAMES)
        for event in events:
            self.assertEqual(oop.gameplay(event), gameplay_message(event, NAMES))

    def test_code_commentary_names_real_entry_points(self) -> None:
        roll = make_event("DICE_ROLLED", 0, 0, {"roll": 3})
        move = make_event(
            "TOKEN_MOVED",
            0,
            0,
            {"token": "R1", "token_idx": 0, "roll": 3, "old_steps": -1, "new_steps": 0},
        )
        oop = OopCommentary(NAMES)
        self.assertEqual(oop.code(roll), "OOP: LudoGame.roll_die() -> process_roll(roll=3)")
        self.assertEqual(oop.code(move), "OOP: LudoGame.apply_move(token_idx=0, roll=3)")
        self.assertEqual(code_message(roll, NAMES), "Functional: roll_die(state) -> process_roll(state, roll=3)")
        self.assertEqual(
            code_message(move, NAMES),
            "Functional: apply_move(state, token_idx=0, roll=3)",
        )

    def test_all_event_types_have_safe_commentary(self) -> None:
        from v1_initial.shared.contracts import EVENT_TYPES

        oop = OopCommentary(NAMES)
        for event_type in EVENT_TYPES:
            event = make_event(
                event_type,
                1,
                0,
                {
                    "roll": 6,
                    "token": "R1",
                    "token_idx": 0,
                    "victim_player": 1,
                    "victim_token": "G1",
                    "tile": 4,
                    "place": 1,
                    "reason": "Capture",
                    "finish_order": [0],
                },
            )
            self.assertIsInstance(oop.gameplay(event), str)
            self.assertIsInstance(oop.code(event), str)
            self.assertIsInstance(gameplay_message(event, NAMES), str)
            self.assertIsInstance(code_message(event, NAMES), str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
