#!/usr/bin/env python3
"""Tests for shared Ludo configuration and event contracts."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.contracts import (  # noqa: E402
    build_config,
    config_from_dict,
    get_start_indices,
    make_event,
)


class ContractTest(unittest.TestCase):
    """Protect configuration decisions shared by both paradigms."""

    def test_showcase_profile_enables_new_rules(self) -> None:
        config = build_config("quick", profile="showcase", player_count=2)
        self.assertEqual(config["track_len"], 28)
        self.assertEqual(config["home_len"], 4)
        self.assertEqual(config["home_finish"], 31)
        self.assertEqual(config["tokens_per_player"], 2)
        self.assertEqual(config["safe_tiles"], [0, 7, 14, 21])
        self.assertEqual(config["blockades"], "safe_pair")
        self.assertTrue(config["kill_to_enter"])
        self.assertTrue(config["podium_mode"])

    def test_classic_profile_restores_original_rules(self) -> None:
        config = build_config("classic", profile="classic", player_count=4)
        self.assertEqual(config["track_len"], 52)
        self.assertEqual(config["tokens_per_player"], 4)
        self.assertEqual(config["home_len"], 5)
        self.assertEqual(config["home_finish"], 56)
        self.assertEqual(config["safe_tiles"], [0, 8, 13, 21, 26, 34, 39, 47])
        self.assertEqual(config["blockades"], "none")
        self.assertFalse(config["kill_to_enter"])
        self.assertFalse(config["podium_mode"])

    def test_overrides_change_allowed_settings(self) -> None:
        config = build_config(
            "quick",
            profile="showcase",
            player_count=3,
            overrides={
                "tokens_per_player": 1,
                "max_turns": 7,
                "safe_tiles_enabled": False,
                "blockades": "strict",
                "exact_home_roll": False,
                "auto_delay": 0.0,
            },
        )
        self.assertEqual(config["tokens_per_player"], 1)
        self.assertEqual(config["max_turns"], 7)
        self.assertFalse(config["safe_tiles_enabled"])
        self.assertEqual(config["blockades"], "strict")
        self.assertFalse(config["exact_home_roll"])
        self.assertEqual(config["auto_delay"], 0.0)

    def test_geometry_overrides_are_rejected(self) -> None:
        for key, value in (
            ("track_len", 30),
            ("home_len", 6),
            ("home_finish", 40),
            ("outer_last_step", 29),
            ("start_indices_2p", [0, 15]),
            ("safe_tiles", [0, 1]),
        ):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    build_config("quick", overrides={key: value})

    def test_invalid_values_are_rejected(self) -> None:
        invalid_overrides = (
            {"tokens_per_player": 0},
            {"tokens_per_player": 5},
            {"max_turns": 0},
            {"auto_delay": -0.1},
            {"player_count": 1},
            {"player_count": 5},
            {"blockades": "wall"},
            {"safe_tiles_enabled": "yes"},
        )
        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    build_config("quick", overrides=overrides)

    def test_json_config_round_trip(self) -> None:
        original = build_config(
            "classic",
            profile="showcase",
            player_count=3,
            overrides={"tokens_per_player": 3, "seed": 42},
        )
        restored = config_from_dict(json.loads(json.dumps(original)))
        self.assertEqual(restored, original)

    def test_event_payload_is_json_serializable(self) -> None:
        event = make_event(
            "TOKEN_CAPTURED",
            turn=4,
            player=1,
            data={"captured": ["R1", "R2"]},
        )
        self.assertEqual(
            event,
            {
                "type": "TOKEN_CAPTURED",
                "turn": 4,
                "player": 1,
                "data": {"captured": ["R1", "R2"]},
            },
        )
        self.assertEqual(json.loads(json.dumps(event)), event)

    def test_start_indices_follow_seating_rules(self) -> None:
        self.assertEqual(get_start_indices(build_config("quick", player_count=2)), [0, 14])
        self.assertEqual(get_start_indices(build_config("quick", player_count=3)), [0, 7, 14])
        self.assertEqual(get_start_indices(build_config("quick", player_count=4)), [0, 7, 14, 21])
        self.assertEqual(get_start_indices(build_config("classic", player_count=2)), [0, 26])
        self.assertEqual(get_start_indices(build_config("classic", player_count=3)), [0, 13, 26])
        self.assertEqual(
            get_start_indices(build_config("classic", player_count=4)),
            [0, 13, 26, 39],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
