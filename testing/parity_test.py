#!/usr/bin/env python3
"""Seeded full-game parity and subprocess CLI transcript verification."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.func_ludo.bot import decision_details as functional_decision
from v1_initial.func_ludo.rules import (
    apply_move as functional_apply_move,
    preview_move as functional_preview_move,
    process_roll as functional_process_roll,
    record_bot_decision as functional_record_bot_decision,
    roll_die as functional_roll_die,
)
from v1_initial.func_ludo.state import create_game_state, export_canonical_state
from v1_initial.oop_ludo.bot import BotPolicy
from v1_initial.oop_ludo.engine import LudoGame
from v1_initial.shared.contracts import build_config


SCENARIOS = (
    ("quick", 2, 2, "classic", "none", False, False, 120, 60),
    ("quick", 3, 3, "showcase", "safe_pair", True, True, 120, 60),
    ("quick", 4, 4, "showcase", "safe_pair", True, True, 120, 60),
    ("quick", 2, 1, "classic", "strict", False, False, 120, 60),
    ("quick", 3, 2, "classic", "strict", True, False, 120, 60),
    ("quick", 4, 3, "showcase", "safe_pair", False, True, 120, 60),
    ("classic", 2, 4, "classic", "none", False, False, 60, 120),
    ("classic", 3, 4, "showcase", "safe_pair", True, True, 60, 120),
    ("classic", 4, 4, "showcase", "safe_pair", True, True, 60, 120),
    ("classic", 2, 1, "classic", "strict", False, False, 60, 120),
    ("classic", 3, 2, "classic", "strict", True, False, 60, 120),
    ("classic", 4, 3, "showcase", "safe_pair", False, True, 60, 120),
)


def scenario_config(
    scenario: tuple[str, int, int, str, str, bool, bool, int, int],
    seed: int,
) -> dict[str, Any]:
    """Build one validated configuration from a fuzz scenario row."""
    mode, players, tokens, profile, blockades, kill, podium, _, max_turns = scenario
    return build_config(
        mode,
        profile,
        players,
        {
            "tokens_per_player": tokens,
            "blockades": blockades,
            "kill_to_enter": kill,
            "podium_mode": podium,
            "max_turns": max_turns,
            "seed": seed,
        },
    )


def cli_arguments(
    mode: str = "quick",
    players: int = 2,
    tokens: int = 1,
    seed: int = 42,
    max_turns: int = 30,
) -> list[str]:
    """Create deterministic human-seat CLI arguments for transcript tests."""
    arguments = [
        "--mode", mode,
        "--profile", "classic",
        "--players", str(players),
        "--tokens", str(tokens),
        "--max-turns", str(max_turns),
        "--seed", str(seed),
        "--auto-delay", "0",
        "--commentary", "off",
        "--no-color",
    ]
    for index in range(players):
        arguments.extend(["--name", chr(ord("A") + index)])
    return arguments


def build_human_script(seed: int, stop_event: str) -> str:
    """Generate exact human input until a seeded win or capture occurs."""
    config = build_config(
        "quick",
        "classic",
        2,
        {"tokens_per_player": 1, "max_turns": 100, "seed": seed},
    )
    game = LudoGame(config, ["A", "B"], seed=seed)
    answers: list[str] = []
    for _ in range(1000):
        if game.status != "PLAYING":
            break
        roll = game.roll_die()
        answers.append("\n")
        result = game.process_roll(roll)
        if result["valid_moves"]:
            answers.append("1\n")
            move = game.apply_move(result["valid_moves"][0], roll)
            if stop_event == "capture" and move["captured"]:
                answers.extend(["quit\n", "y\n"])
                return "".join(answers)
    if stop_event != "win" or game.status != "WON":
        raise AssertionError(f"Seed {seed} did not reach {stop_event}")
    return "".join(answers)


def normalize_code_narration(text: str) -> str:
    """Mask only paradigm-specific code lines before comparing transcripts."""
    return re.sub(r"(?:OOP:|Functional:)[^\n]*", "[Code] <paradigm-specific>", text)


class ParityTest(unittest.TestCase):
    """Verify 1,080 full games and observable CLI behavior."""

    def play_full_game(self, scenario: tuple[str, int, int, str, str, bool, bool, int, int], seed: int) -> dict[str, int]:
        """Compare both engines after every roll, decision, and move."""
        mode, players, _, _, _, _, _, _, _ = scenario
        names = [f"P{index + 1}" for index in range(players)]
        kinds = ["bot"] * players
        config = scenario_config(scenario, seed)
        oop_game = LudoGame(config, names, seed=seed, player_kinds=kinds)
        func_state = create_game_state(config, names, seed=seed, player_kinds=kinds)
        policy = BotPolicy()
        stats = {"rolls": 0, "moves": 0, "snapshots": 1}

        self.assertEqual(oop_game.export_canonical_state(), export_canonical_state(func_state))
        for _ in range(100_000):
            if oop_game.status != "PLAYING" or func_state["status"] != "PLAYING":
                break
            self.assertEqual(oop_game.status, func_state["status"])
            self.assertEqual(oop_game.current_player_index, func_state["current_player"])

            oop_roll = oop_game.roll_die()
            func_roll = functional_roll_die(func_state)
            self.assertEqual(oop_roll, func_roll)
            stats["rolls"] += 1

            oop_result = oop_game.process_roll(oop_roll)
            func_result = functional_process_roll(func_state, func_roll)
            self.assertEqual(oop_result, func_result)
            self.assertEqual(oop_game.export_canonical_state(), export_canonical_state(func_state))
            stats["snapshots"] += 1

            valid_moves = oop_result["valid_moves"]
            if valid_moves:
                oop_choice = policy.decision_details(oop_game, oop_roll, valid_moves)
                func_choice = functional_decision(
                    func_state,
                    func_state["current_player"],
                    func_roll,
                    valid_moves,
                )
                self.assertEqual(oop_choice, func_choice)
                token_idx = int(oop_choice["token_idx"])
                oop_game.record_bot_decision(token_idx, oop_roll, oop_choice["reason"])
                functional_record_bot_decision(
                    func_state,
                    token_idx,
                    func_roll,
                    func_choice["reason"],
                )
                self.assertEqual(oop_game.export_canonical_state(), export_canonical_state(func_state))
                stats["snapshots"] += 1

                oop_preview = oop_game.preview_move(
                    oop_game.current_player_index,
                    token_idx,
                    oop_roll,
                )
                func_preview = functional_preview_move(
                    func_state,
                    func_state["current_player"],
                    token_idx,
                    func_roll,
                )
                self.assertEqual(oop_preview, func_preview)

                oop_move = oop_game.apply_move(token_idx, oop_roll)
                func_move = functional_apply_move(func_state, token_idx, func_roll)
                self.assertEqual(oop_move, func_move)
                self.assertEqual(oop_game.export_canonical_state(), export_canonical_state(func_state))
                stats["moves"] += 1
                stats["snapshots"] += 1
        else:
            self.fail(f"Game exceeded the safety limit: {mode}, seed={seed}")

        oop_snapshot = oop_game.export_canonical_state()
        func_snapshot = export_canonical_state(func_state)
        self.assertEqual(oop_snapshot, func_snapshot)
        self.assertIn(oop_snapshot["status"], {"WON", "DRAW"})
        self.assertEqual(oop_snapshot["winner_index"], func_snapshot["winner_index"])
        self.assertEqual(oop_snapshot["draw_reason"], func_snapshot["draw_reason"])
        self.assertEqual(oop_snapshot["turn_count"], func_snapshot["turn_count"])
        json.dumps(oop_snapshot, sort_keys=True)
        stats["snapshots"] += 1
        stats["wins"] = int(oop_snapshot["status"] == "WON")
        stats["draws"] = int(oop_snapshot["status"] == "DRAW")
        return stats

    def test_1080_full_game_parity_matrix(self) -> None:
        """Cover both modes, all seat counts, token counts, and rule families."""
        totals = {"games": 0, "wins": 0, "draws": 0, "rolls": 0, "moves": 0, "snapshots": 0}
        game_number = 0
        for scenario in SCENARIOS:
            for _ in range(scenario[7]):
                game_number += 1
                seed = 20_000 + game_number
                with self.subTest(scenario=scenario[:7], seed=seed):
                    stats = self.play_full_game(scenario, seed)
                    totals["games"] += 1
                    totals["rolls"] += stats["rolls"]
                    totals["moves"] += stats["moves"]
                    totals["snapshots"] += stats["snapshots"]
                    totals["wins"] += stats["wins"]
                    totals["draws"] += stats["draws"]
        self.assertEqual(totals["games"], 1080)
        self.assertEqual(totals["wins"] + totals["draws"], 1080)
        self.assertGreater(totals["rolls"], 10_000)
        self.assertGreater(totals["moves"], 1_000)
        print(
            "Parity matrix: "
            + ", ".join(f"{key}={value}" for key, value in totals.items())
        )

    def run_cli(self, script: str, arguments: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
        """Run one real CLI process with scripted standard input."""
        return subprocess.run(
            [sys.executable, str(ROOT / "v1_initial" / script), *arguments],
            input=stdin,
            text=True,
            capture_output=True,
            timeout=90,
            cwd=ROOT,
        )

    def assert_cli_pair(self, arguments: list[str], stdin: str) -> tuple[str, str]:
        """Assert identical stdout, stderr, and successful exit codes."""
        oop_process = self.run_cli("ludo_oop.py", arguments, stdin)
        func_process = self.run_cli("ludo_func.py", arguments, stdin)
        self.assertEqual(oop_process.returncode, 0, oop_process.stderr)
        self.assertEqual(func_process.returncode, 0, func_process.stderr)
        self.assertEqual(oop_process.stdout, func_process.stdout)
        self.assertEqual(oop_process.stderr, func_process.stderr)
        self.assertNotIn("\033[", oop_process.stdout)
        return oop_process.stdout, func_process.stdout

    def test_subprocess_seeded_full_win(self) -> None:
        """Drive a complete two-player game through legal human choices."""
        output, _ = self.assert_cli_pair(
            cli_arguments(seed=0, max_turns=100),
            build_human_script(0, "win"),
        )
        self.assertIn("| WON", output)
        self.assertIn("Last event: B wins!", output)

    def test_subprocess_seeded_capture(self) -> None:
        """Play until a real capture appears in both CLI transcripts."""
        output, _ = self.assert_cli_pair(
            cli_arguments(seed=13, max_turns=100),
            build_human_script(13, "capture"),
        )
        self.assertIn("CAPTURES B's G1", output)
        self.assertIn("Game quit.", output)

    def test_subprocess_invalid_commands_and_quit_confirmation(self) -> None:
        """Reject malformed commands and require quit confirmation."""
        output, _ = self.assert_cli_pair(
            cli_arguments(),
            "abc\n99\n-1\n   \nquit\nn\nquit\ny\n",
        )
        self.assertEqual(output.count("Unknown command"), 3)
        self.assertIn("Quit cancelled.", output)
        self.assertIn("Game quit.", output)

    def test_subprocess_invalid_token_choices(self) -> None:
        """Reject non-integers, huge values, negatives, and blank token input."""
        output, _ = self.assert_cli_pair(
            cli_arguments(seed=42),
            "\nabc\n99\n-1\n   \n1\nquit\ny\n",
        )
        self.assertIn("Please enter a listed token number.", output)
        self.assertIn("That token is not a legal choice.", output)
        self.assertIn("Bonus roll for A.", output)

    def test_subprocess_mutual_draw_declined_then_accepted(self) -> None:
        """Resume after a declined draw and accept a later unanimous draw."""
        output, _ = self.assert_cli_pair(
            cli_arguments(seed=1),
            "draw\nn\n\ndraw\ny\n",
        )
        self.assertIn("Draw declined; play continues.", output)
        self.assertIn("Last event: Mutual agreement", output)
        self.assertIn("Turn 1/30 | Current: B | DRAW", output)

    def test_subprocess_max_turn_draw_with_bots(self) -> None:
        """Run three bot seats to the configured draw cap."""
        arguments = cli_arguments(players=3, tokens=2, seed=7, max_turns=4)
        arguments.extend(["--autoplay"])
        output, _ = self.assert_cli_pair(arguments, "")
        self.assertIn("Last event: Maximum turn limit reached", output)
        self.assertIn("Turn 4/4 | Current: B | DRAW", output)

    def test_subprocess_mixed_seats_autoplay(self) -> None:
        """Preserve human/bot seat metadata while autoplay drives the match."""
        arguments = cli_arguments(seed=1, max_turns=8)
        arguments.extend(["--seat", "human", "--seat", "bot", "--autoplay"])
        output, _ = self.assert_cli_pair(arguments, "")
        self.assertIn("A [HUMAN]", output)
        self.assertIn("B [BOT]", output)
        self.assertIn("Last event: Maximum turn limit reached", output)
        self.assertIn("Turn 8/8 | Current: A | DRAW", output)

    def test_subprocess_json_four_bot_showcase(self) -> None:
        """Load the four-bot JSON demo and override speed, cap, and commentary."""
        arguments = [
            "--config", str(ROOT / "configs" / "showcase.json"),
            "--max-turns", "12",
            "--auto-delay", "0",
            "--commentary", "gameplay",
            "--no-color",
        ]
        output, _ = self.assert_cli_pair(arguments, "")
        self.assertIn("LUDO - QUICK / SHOWCASE", output)
        self.assertIn("Red Bot [BOT]", output)
        self.assertIn("Draw: Maximum turn limit reached.", output)

    def test_subprocess_wizard_defaults_and_quit(self) -> None:
        """Complete the full wizard with defaults and quit cleanly."""
        output, _ = self.assert_cli_pair(
            ["--wizard", "--no-color"],
            ("\n" * 21) + "quit\ny\n",
        )
        self.assertIn("Ludo setup wizard", output)
        self.assertIn("LUDO - QUICK / SHOWCASE", output)
        self.assertIn("Game quit.", output)

    def test_subprocess_code_narration_is_paradigm_specific(self) -> None:
        """Keep code traces distinct without changing any gameplay output."""
        arguments = cli_arguments(seed=42)
        stdin = "\n1\ncommentary code\n\n1\nquit\ny\n"
        oop_process = self.run_cli("ludo_oop.py", arguments, stdin)
        func_process = self.run_cli("ludo_func.py", arguments, stdin)
        self.assertEqual((oop_process.returncode, func_process.returncode), (0, 0))
        self.assertIn("OOP: LudoGame.roll_die()", oop_process.stdout)
        self.assertIn("Functional: roll_die(state)", func_process.stdout)
        self.assertNotIn("Functional:", oop_process.stdout)
        self.assertNotIn("OOP:", func_process.stdout)
        self.assertEqual(
            normalize_code_narration(oop_process.stdout),
            normalize_code_narration(func_process.stdout),
        )

    def test_subprocess_eof_ends_cleanly(self) -> None:
        """Convert closed standard input into a clean quit in both CLIs."""
        output, _ = self.assert_cli_pair(cli_arguments(), "")
        self.assertIn("Input ended; leaving the match cleanly.", output)
        self.assertIn("Game quit.", output)

    def test_subprocess_invalid_max_turns_is_rejected(self) -> None:
        """Reject a zero turn cap before either CLI starts a match."""
        for script in ("ludo_oop.py", "ludo_func.py"):
            process = self.run_cli(script, ["--max-turns", "0"], "")
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("--max-turns must be a positive integer.", process.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
