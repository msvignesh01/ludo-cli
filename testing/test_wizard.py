#!/usr/bin/env python3
"""Tests for the interactive Ludo configuration wizard."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.cli_support import run_wizard  # noqa: E402


class WizardTest(unittest.TestCase):
    """Verify wizard defaults, metadata prompts, and cancellation."""

    def test_blank_answers_select_showcase_defaults(self) -> None:
        answers = iter([""] * 21)
        output: list[str] = []
        result = run_wizard({}, lambda _: next(answers), output.append)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["mode"], "quick")
        self.assertEqual(result["profile"], "showcase")
        self.assertEqual(result["player_count"], 2)
        self.assertEqual(result["tokens_per_player"], 2)
        self.assertEqual(result["blockades"], "safe_pair")
        self.assertTrue(result["kill_to_enter"])
        self.assertTrue(result["podium_mode"])
        self.assertEqual(result["names"], ["Player 1", "Player 2"])
        self.assertEqual(result["kinds"], ["human", "human"])
        self.assertFalse(result["autoplay"])
        self.assertIn("wizard", output[0].lower())

    def test_existing_values_are_not_reprompted_and_seats_can_mix(self) -> None:
        base: dict[str, Any] = {
            "mode": "classic",
            "profile": "classic",
            "player_count": 3,
            "tokens_per_player": 4,
            "blockades": "none",
            "kill_to_enter": False,
            "podium_mode": False,
            "exact_home_roll": True,
            "triple_six_forfeit": True,
            "safe_tiles_enabled": True,
            "bonus_on_capture": True,
            "bonus_on_home": True,
            "max_turns": 250,
            "commentary": "gameplay",
            "ui": "cli",
            "auto_delay": 0.35,
            "autoplay": False,
        }
        answers = iter(["Ada", "", "Ada", "bot", "human", "bot"])
        result = run_wizard(base, lambda _: next(answers), lambda _: None)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["mode"], "classic")
        self.assertEqual(result["names"], ["Ada", "Player 2", "Ada (3)"])
        self.assertEqual(result["kinds"], ["bot", "human", "bot"])

    def test_eof_cancels_without_partial_setup(self) -> None:
        def eof(_: str) -> str:
            raise EOFError

        self.assertIsNone(run_wizard({}, eof, lambda _: None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
