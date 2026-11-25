#!/usr/bin/env python3
"""Headless tests for GUI turn control, commentary, and token markers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.contracts import build_config  # noqa: E402
from v1_initial.shared.geometry import build_board_geometry  # noqa: E402
from v1_initial.shared.gui_support import build_gui_view_model  # noqa: E402
from v1_initial.oop_ludo.engine import LudoGame  # noqa: E402
from v1_initial.oop_ludo.gui_session import GuiSession  # noqa: E402
from v1_initial.func_ludo.gui_session import (  # noqa: E402
    can_roll,
    create_gui_session,
    cycle_commentary,
    declare_draw,
    drain_commentary,
    get_pending_roll,
    get_previews,
    get_snapshot,
    get_valid_moves,
    is_automated_turn,
    is_human_turn,
    next_delay_ms,
    quit,
    roll_human,
    run_automated_turn,
    select_move,
    set_commentary,
    set_paused,
    set_speed,
    step,
)
from v1_initial.func_ludo.state import create_game_state  # noqa: E402


NAMES = ["Asha", "Bala"]
KINDS = ["human", "human"]


class OopSessionAdapter:
    """Expose the OOP GUI session through the shared test vocabulary."""

    def __init__(self, seed: int = 42, **overrides: Any) -> None:
        """Create an OOP session with deterministic defaults."""
        kinds = overrides.pop("kinds", KINDS)
        autoplay = overrides.pop("autoplay", False)
        config = build_config("quick", "classic", 2, overrides)
        game = LudoGame(config, NAMES, seed=seed, player_kinds=kinds)
        self.session = GuiSession(game, autoplay=autoplay)

    def snapshot(self) -> dict[str, Any]:
        """Return the current canonical state."""
        return self.session.snapshot()

    def pending(self) -> int | None:
        """Return the roll waiting for token selection."""
        return self.session.pending_roll

    def moves(self) -> list[int]:
        """Return legal token indices for the pending roll."""
        return list(self.session.valid_moves)

    def previews(self) -> list[dict[str, Any]]:
        """Return legal move previews."""
        return list(self.session.previews)

    def human(self) -> bool:
        """Return whether a person must act now."""
        return self.session.is_human_turn()

    def automated(self) -> bool:
        """Return whether automation owns the current turn."""
        return self.session.is_automated_turn()

    def can_roll(self) -> bool:
        """Return whether the roll button should be enabled."""
        return self.session.can_roll()

    def delay(self) -> int | None:
        """Return the scheduler delay in milliseconds."""
        return self.session.next_delay_ms()

    def roll(self) -> None:
        """Roll for the active human."""
        self.session.roll_human()

    def choose(self, token_idx: int) -> None:
        """Apply a pending human move."""
        self.session.select_move(token_idx)

    def auto(self) -> bool:
        """Run one automated turn."""
        return self.session.run_automated_turn()

    def step(self) -> bool:
        """Advance exactly one GUI action."""
        return self.session.step()

    def pause(self, value: bool) -> None:
        """Pause or resume automatic scheduling."""
        self.session.set_paused(value)

    def speed(self, value: str) -> None:
        """Set the automatic speed."""
        self.session.set_speed(value)

    def cycle(self) -> str:
        """Cycle the commentary mode."""
        return self.session.cycle_commentary()

    def commentary(self, value: str) -> None:
        """Set the commentary mode."""
        self.session.set_commentary(value)

    def lines(self) -> list[str]:
        """Drain newly generated commentary lines."""
        return self.session.drain_commentary()

    def draw(self) -> None:
        """End the match by mutual agreement."""
        self.session.declare_mutual_draw()

    def stop(self) -> None:
        """Quit the match."""
        self.session.quit()


class FuncSessionAdapter:
    """Expose the functional GUI session through the same test vocabulary."""

    def __init__(self, seed: int = 42, **overrides: Any) -> None:
        """Create a functional session with deterministic defaults."""
        kinds = overrides.pop("kinds", KINDS)
        autoplay = overrides.pop("autoplay", False)
        config = build_config("quick", "classic", 2, overrides)
        state = create_game_state(config, NAMES, seed=seed, player_kinds=kinds)
        self.session = create_gui_session(state, autoplay=autoplay)

    def snapshot(self) -> dict[str, Any]:
        """Return the current canonical state."""
        return get_snapshot(self.session)

    def pending(self) -> int | None:
        """Return the roll waiting for token selection."""
        return get_pending_roll(self.session)

    def moves(self) -> list[int]:
        """Return legal token indices for the pending roll."""
        return get_valid_moves(self.session)

    def previews(self) -> list[dict[str, Any]]:
        """Return legal move previews."""
        return get_previews(self.session)

    def human(self) -> bool:
        """Return whether a person must act now."""
        return is_human_turn(self.session)

    def automated(self) -> bool:
        """Return whether automation owns the current turn."""
        return is_automated_turn(self.session)

    def can_roll(self) -> bool:
        """Return whether the roll button should be enabled."""
        return can_roll(self.session)

    def delay(self) -> int | None:
        """Return the scheduler delay in milliseconds."""
        return next_delay_ms(self.session)

    def roll(self) -> None:
        """Roll for the active human."""
        roll_human(self.session)

    def choose(self, token_idx: int) -> None:
        """Apply a pending human move."""
        select_move(self.session, token_idx)

    def auto(self) -> bool:
        """Run one automated turn."""
        return run_automated_turn(self.session)

    def step(self) -> bool:
        """Advance exactly one GUI action."""
        return step(self.session)

    def pause(self, value: bool) -> None:
        """Pause or resume automatic scheduling."""
        set_paused(self.session, value)

    def speed(self, value: str) -> None:
        """Set the automatic speed."""
        set_speed(self.session, value)

    def cycle(self) -> str:
        """Cycle the commentary mode."""
        return cycle_commentary(self.session)

    def commentary(self, value: str) -> None:
        """Set the commentary mode."""
        set_commentary(self.session, value)

    def lines(self) -> list[str]:
        """Drain newly generated commentary lines."""
        return drain_commentary(self.session)

    def draw(self) -> None:
        """End the match by mutual agreement."""
        declare_draw(self.session)

    def stop(self) -> None:
        """Quit the match."""
        quit(self.session)


class GuiSessionTest(unittest.TestCase):
    """Verify both GUI controllers without opening a display."""

    def sessions(self, seed: int = 42, **overrides: Any) -> tuple[Any, Any]:
        """Create matching OOP and functional sessions."""
        return OopSessionAdapter(seed, **overrides), FuncSessionAdapter(seed, **overrides)

    def assert_parity(self, oop: Any, func: Any) -> None:
        """Assert canonical state and shared controls remain identical."""
        self.assertEqual(oop.snapshot(), func.snapshot())
        self.assertEqual(oop.pending(), func.pending())
        self.assertEqual(oop.moves(), func.moves())
        self.assertEqual(oop.previews(), func.previews())
        self.assertEqual(oop.human(), func.human())
        self.assertEqual(oop.automated(), func.automated())
        self.assertEqual(oop.can_roll(), func.can_roll())
        self.assertEqual(oop.delay(), func.delay())

    def test_initial_human_turn_waits_for_roll(self) -> None:
        oop, func = self.sessions()
        self.assert_parity(oop, func)
        self.assertIsNone(oop.pending())
        self.assertTrue(oop.human())
        self.assertFalse(oop.automated())
        self.assertTrue(oop.can_roll())
        self.assertIsNone(oop.delay())
        self.assertEqual(oop.lines(), ["Match started."])
        self.assertEqual(oop.lines(), [])

    def test_human_roll_and_selection_preserve_bonus_turn(self) -> None:
        oop, func = self.sessions()
        oop.roll()
        func.roll()
        self.assert_parity(oop, func)
        self.assertEqual(oop.pending(), 6)
        self.assertEqual(oop.moves(), [0, 1])
        self.assertEqual([item["token_idx"] for item in oop.previews()], [0, 1])
        self.assertFalse(oop.can_roll())

        before = oop.snapshot()
        with self.assertRaises(ValueError):
            oop.choose(7)
        self.assertEqual(oop.snapshot(), before)

        oop.choose(0)
        func.choose(0)
        self.assert_parity(oop, func)
        self.assertIsNone(oop.pending())
        self.assertEqual(oop.snapshot()["current_player"], 0)
        self.assertEqual(oop.snapshot()["turn_count"], 0)
        self.assertTrue(oop.can_roll())

    def test_human_no_move_advances_to_bot_and_schedules_it(self) -> None:
        oop, func = self.sessions(seed=1, kinds=["human", "bot"])
        oop.roll()
        func.roll()
        self.assert_parity(oop, func)
        self.assertIsNone(oop.pending())
        self.assertEqual(oop.snapshot()["current_player"], 1)
        self.assertFalse(oop.human())
        self.assertTrue(oop.automated())
        self.assertEqual(oop.delay(), 350)

    def test_bot_turn_is_one_deterministic_action(self) -> None:
        oop, func = self.sessions(kinds=["bot", "bot"])
        self.assert_parity(oop, func)
        self.assertEqual(oop.delay(), 350)
        self.assertTrue(oop.auto())
        self.assertTrue(func.auto())
        self.assert_parity(oop, func)
        self.assertEqual(oop.snapshot()["players"][0]["tokens"][0]["steps"], 0)
        self.assertEqual(oop.snapshot()["current_player"], 0)
        self.assertIn("BOT_DECISION", [event["type"] for event in oop.snapshot()["events"]])

    def test_autoplay_can_drive_human_seats(self) -> None:
        oop, func = self.sessions(autoplay=True)
        self.assert_parity(oop, func)
        self.assertFalse(oop.human())
        self.assertTrue(oop.automated())
        self.assertFalse(oop.can_roll())
        self.assertTrue(oop.step())
        self.assertTrue(func.step())
        self.assert_parity(oop, func)

    def test_pause_blocks_scheduling_but_step_still_works(self) -> None:
        oop, func = self.sessions(kinds=["bot", "bot"])
        oop.pause(True)
        func.pause(True)
        self.assertIsNone(oop.delay())
        self.assertIsNone(func.delay())
        self.assertTrue(oop.step())
        self.assertTrue(func.step())
        self.assert_parity(oop, func)
        oop.pause(False)
        func.pause(False)
        self.assertEqual(oop.delay(), 350)

    def test_step_rolls_human_then_selects_a_legal_move(self) -> None:
        oop, func = self.sessions()
        self.assertTrue(oop.step())
        self.assertTrue(func.step())
        self.assert_parity(oop, func)
        self.assertEqual(oop.pending(), 6)
        self.assertTrue(oop.step())
        self.assertTrue(func.step())
        self.assert_parity(oop, func)
        self.assertIsNone(oop.pending())
        self.assertNotIn("BOT_DECISION", [event["type"] for event in oop.snapshot()["events"]])

    def test_speed_controls_change_only_scheduler_delay(self) -> None:
        oop, func = self.sessions(kinds=["bot", "bot"])
        for speed, expected in (("slow", 800), ("normal", 350), ("fast", 50)):
            oop.speed(speed)
            func.speed(speed)
            self.assertEqual(oop.delay(), expected)
            self.assertEqual(func.delay(), expected)
        with self.assertRaises(ValueError):
            oop.speed("turbo")
        with self.assertRaises(ValueError):
            func.speed("turbo")

    def test_commentary_modes_are_shared_except_code_entry_points(self) -> None:
        oop, func = self.sessions()
        self.assertEqual(oop.cycle(), "code")
        self.assertEqual(func.cycle(), "code")
        self.assertEqual(oop.lines(), ["OOP: LudoGame.__init__()"])
        self.assertEqual(func.lines(), ["Functional: create_game_state(config, player_names)"])
        oop.commentary("both")
        func.commentary("both")
        self.assertEqual(oop.cycle(), "off")
        self.assertEqual(func.cycle(), "off")
        self.assertEqual(oop.lines(), [])
        self.assertEqual(func.lines(), [])

    def test_terminal_draw_disables_all_turn_controls(self) -> None:
        oop, func = self.sessions(seed=1, max_turns=1, kinds=["bot", "bot"])
        self.assertTrue(oop.step())
        self.assertTrue(func.step())
        self.assert_parity(oop, func)
        self.assertEqual(oop.snapshot()["status"], "DRAW")
        self.assertEqual(oop.snapshot()["draw_reason"], "Maximum turn limit reached")
        self.assertFalse(oop.step())
        self.assertFalse(oop.auto())
        self.assertFalse(oop.can_roll())
        self.assertIsNone(oop.delay())

    def test_draw_and_quit_emit_clean_terminal_events(self) -> None:
        for action in ("draw", "stop"):
            with self.subTest(action=action):
                oop, func = self.sessions()
                getattr(oop, action)()
                getattr(func, action)()
                self.assert_parity(oop, func)
                expected = "DRAW" if action == "draw" else "QUIT"
                self.assertEqual(oop.snapshot()["status"], expected)
                self.assertFalse(oop.human())
                self.assertFalse(oop.automated())

    def test_short_automated_match_has_exact_controller_parity(self) -> None:
        oop, func = self.sessions(seed=9, max_turns=12, kinds=["bot", "bot"])
        for _ in range(12):
            if oop.snapshot()["status"] != "PLAYING":
                break
            oop.step()
            func.step()
            self.assert_parity(oop, func)
            self.assertEqual(oop.lines(), func.lines())


class GuiViewModelTest(unittest.TestCase):
    """Verify display-independent marker placement."""

    def test_tokens_map_to_track_home_base_and_finish_cells(self) -> None:
        config = build_config("quick", "classic", 2)
        game = LudoGame(config, NAMES, seed=42)
        game.players[0].tokens[0].steps = 4
        game.players[0].tokens[1].steps = 27
        game.players[1].tokens[0].steps = 22
        game.players[1].tokens[1].steps = 31
        geometry = build_board_geometry(config)
        model = build_gui_view_model(game.export_canonical_state(), geometry)
        markers = {(item["player_index"], item["token_idx"]): item for item in model["markers"]}

        self.assertEqual(markers[(0, 0)]["location"], "track")
        self.assertEqual(markers[(0, 0)]["global_pos"], 4)
        self.assertEqual(markers[(0, 0)]["cell"], geometry["track_cells"][4])
        self.assertEqual(markers[(1, 0)]["location"], "track")
        self.assertEqual(markers[(1, 0)]["global_pos"], 8)
        self.assertEqual(markers[(0, 1)]["location"], "home")
        self.assertEqual(markers[(0, 1)]["cell"], geometry["home_cells"][0][0])
        self.assertEqual(markers[(1, 1)]["location"], "finished")
        self.assertEqual(markers[(1, 1)]["cell"], geometry["home_center"])
        self.assertEqual(model["current_player"], 0)
        self.assertEqual(model["safe_tiles"], [0, 7, 14, 21])

    def test_base_tokens_use_their_players_yard(self) -> None:
        config = build_config("quick", "classic", 2)
        game = LudoGame(config, NAMES, seed=42)
        model = build_gui_view_model(game.export_canonical_state())
        for marker in model["markers"]:
            self.assertEqual(marker["location"], "base")
            self.assertEqual(marker["steps"], -1)
            self.assertIsInstance(marker["cell"][0], (int, float))
            self.assertIsInstance(marker["cell"][1], (int, float))


if __name__ == "__main__":
    unittest.main(verbosity=2)
