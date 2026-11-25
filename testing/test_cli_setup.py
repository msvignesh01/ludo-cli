#!/usr/bin/env python3
"""Tests for shared CLI parsing, setup precedence, and input safety."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.cli_support import (  # noqa: E402
    create_parser,
    load_json_setup,
    merge_setup,
    normalize_player_kinds,
    normalize_player_names,
    read_bool,
    read_choice,
    read_int,
    strip_ansi,
)


class CliSetupTest(unittest.TestCase):
    """Verify configuration sources and robust interactive helpers."""

    def test_parser_exposes_full_granular_flags(self) -> None:
        args = create_parser().parse_args(
            [
                "--mode", "classic",
                "--profile", "classic",
                "--players", "4",
                "--tokens", "3",
                "--seat", "bot",
                "--seat", "human",
                "--name", "Ada",
                "--blockades", "strict",
                "--no-kill-to-enter",
                "--no-podium-mode",
                "--no-exact-home-roll",
                "--no-triple-six-forfeit",
                "--no-safe-tiles",
                "--no-bonus-on-capture",
                "--no-bonus-on-home",
                "--max-turns", "12",
                "--seed", "7",
                "--auto-delay", "0",
                "--commentary", "both",
                "--autoplay",
                "--no-color",
            ]
        )
        self.assertEqual(args.player_count, 4)
        self.assertEqual(args.tokens_per_player, 3)
        self.assertEqual(args.seat, ["bot", "human"])
        self.assertEqual(args.kill_to_enter, False)
        self.assertEqual(args.safe_tiles_enabled, False)
        self.assertEqual(args.autoplay, True)
        self.assertTrue(args.no_color)

    def test_cli_overrides_wizard_and_json(self) -> None:
        json_setup = {
            "mode": "quick",
            "profile": "showcase",
            "player_count": 2,
            "blockades": "safe_pair",
            "max_turns": 80,
            "names": ["JSON One", "JSON Two"],
            "kinds": ["human", "bot"],
        }
        wizard = {"player_count": 3, "blockades": "none", "commentary": "code"}
        cli = {
            "mode": "classic",
            "profile": "classic",
            "max_turns": 9,
            "names": ["CLI One", "CLI Two", "CLI Three"],
            "kinds": ["bot"],
        }
        setup = merge_setup(json_setup, wizard, cli)
        self.assertEqual(setup["config"]["mode"], "classic")
        self.assertEqual(setup["config"]["profile"], "classic")
        self.assertEqual(setup["config"]["player_count"], 3)
        self.assertEqual(setup["config"]["blockades"], "none")
        self.assertEqual(setup["config"]["max_turns"], 9)
        self.assertEqual(setup["config"]["commentary"], "code")
        self.assertEqual(setup["names"], ["CLI One", "CLI Two", "CLI Three"])
        self.assertEqual(setup["kinds"], ["bot", "human", "human"])

    def test_json_round_trip_and_locked_geometry_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preset.json"
            path.write_text(
                json.dumps(
                    {
                        "mode": "quick",
                        "profile": "showcase",
                        "player_count": 4,
                        "tokens_per_player": 3,
                        "track_len": 28,
                        "names": ["A", "B", "C", "D"],
                        "kinds": ["bot", "bot", "bot", "bot"],
                        "autoplay": True,
                    }
                ),
                encoding="utf-8",
            )
            setup = load_json_setup(path)
            self.assertEqual(setup["config"]["tokens_per_player"], 3)
            self.assertEqual(setup["names"], ["A", "B", "C", "D"])
            self.assertTrue(setup["autoplay"])

            path.write_text(json.dumps({"mode": "quick", "track_len": 99}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_json_setup(path)

    def test_names_are_stripped_defaulted_and_unique(self) -> None:
        names = normalize_player_names([" Ada ", "", "Ada", "Grace"], 4)
        self.assertEqual(names, ["Ada", "Player 2", "Ada (3)", "Grace"])
        defaults = normalize_player_names([], 3)
        self.assertEqual(defaults, ["Player 1", "Player 2", "Player 3"])

    def test_seat_kinds_are_padded_and_validated(self) -> None:
        self.assertEqual(normalize_player_kinds(["bot"], 3), ["bot", "human", "human"])
        with self.assertRaises(ValueError):
            normalize_player_kinds(["robot"], 2)
        with self.assertRaises(ValueError):
            normalize_player_kinds(["human", "bot", "human"], 2)

    def test_prompt_helpers_reject_bad_input_without_crashing(self) -> None:
        answers = iter(["abc", "-1", "4"])
        output: list[str] = []
        value = read_int("Count", 2, 4, 3, lambda _: next(answers), output.append)
        self.assertEqual(value, 4)
        self.assertEqual(len(output), 2)

        answers = iter(["maybe", "Y"])
        self.assertTrue(read_bool("Enable", True, lambda _: next(answers), lambda _: None))
        self.assertEqual(
            read_choice("Mode", {"1": "quick", "2": "classic"}, "quick", lambda _: "2", lambda _: None),
            "classic",
        )

    def test_prompt_eof_returns_none(self) -> None:
        def eof(_: str) -> str:
            raise EOFError

        self.assertIsNone(read_int("Count", 2, 4, 2, eof, lambda _: None))

    def test_ansi_is_stripped_cleanly(self) -> None:
        self.assertEqual(strip_ansi("\033[91mRED\033[0m"), "RED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
