#!/usr/bin/env python3
"""End-to-end in-process tests for both command-line runtimes."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.cli_support import strip_ansi  # noqa: E402
from v1_initial.shared.contracts import build_config  # noqa: E402
from v1_initial.oop_ludo.cli import main as oop_main  # noqa: E402
from v1_initial.oop_ludo.renderer import CLIRenderer  # noqa: E402
from v1_initial.oop_ludo.engine import LudoGame  # noqa: E402
from v1_initial.func_ludo.cli import main as func_main  # noqa: E402
from v1_initial.func_ludo.renderer import render_board, render_moves  # noqa: E402
from v1_initial.func_ludo.state import create_game_state  # noqa: E402


def run_main(main: Any, args: list[str], answers: list[str]) -> tuple[int, str]:
    """Run one CLI with scripted input and no real sleeping."""
    answer_iter = iter(answers)

    def input_func(prompt: str) -> str:
        try:
            return next(answer_iter)
        except StopIteration as exc:
            raise EOFError from exc

    output = io.StringIO()
    code = main(args, input_func=input_func, output_func=output.write, sleep_func=lambda _: None)
    return code, output.getvalue()


def common_args(seats: list[str], max_turns: int = 5) -> list[str]:
    """Create deterministic CLI arguments shared by both paradigms."""
    args = [
        "--mode", "quick",
        "--profile", "classic",
        "--players", "2",
        "--tokens", "1",
        "--name", "Alice",
        "--name", "Bob",
        "--max-turns", str(max_turns),
        "--seed", "42",
        "--auto-delay", "0",
        "--no-color",
    ]
    for seat in seats:
        args.extend(["--seat", seat])
    return args


class CliRuntimeTest(unittest.TestCase):
    """Verify observable CLI parity without external processes."""

    def test_renderers_are_byte_identical(self) -> None:
        config = build_config("quick", "showcase", 3, {"tokens_per_player": 3})
        names = ["Alice", "Bob", "Cara"]
        oop_game = LudoGame(config, names, seed=42)
        func_state = create_game_state(config, names, seed=42)
        oop_text = CLIRenderer(use_color=False, use_unicode=True).render(
            oop_game.export_canonical_state()
        )
        func_text = render_board(
            func_state,
            use_color=False,
            use_unicode=True,
        )
        self.assertEqual(oop_text, func_text)
        self.assertNotIn("\033[", oop_text)
        self.assertIn("T00", oop_text)

    def test_move_renderers_are_byte_identical(self) -> None:
        config = build_config("quick", "classic", 2)
        oop_game = LudoGame(config, ["Alice", "Bob"])
        func_state = create_game_state(config, ["Alice", "Bob"])
        oop_previews = [oop_game.preview_move(0, 0, 6)]
        from v1_initial.func_ludo.rules import preview_move

        func_previews = [preview_move(func_state, 0, 0, 6)]
        self.assertEqual(
            CLIRenderer(False, False).render_moves(oop_previews),
            render_moves(func_previews, use_color=False, use_unicode=False),
        )

    def test_four_bot_autoplay_reaches_turn_cap_identically(self) -> None:
        args = common_args(["bot", "bot"], max_turns=2) + ["--autoplay"]
        oop_code, oop_output = run_main(oop_main, args, [])
        func_code, func_output = run_main(func_main, args, [])
        self.assertEqual(oop_code, 0)
        self.assertEqual(func_code, 0)
        self.assertEqual(oop_output, func_output)
        self.assertIn("Draw: Maximum turn limit reached.", oop_output)

    def test_mutual_draw_with_human_and_bot(self) -> None:
        args = common_args(["human", "bot"])
        oop_code, oop_output = run_main(oop_main, args, ["draw", "y"])
        func_code, func_output = run_main(func_main, args, ["draw", "y"])
        self.assertEqual((oop_code, func_code), (0, 0))
        self.assertEqual(oop_output, func_output)
        self.assertIn("Draw: Mutual agreement.", oop_output)

    def test_quit_confirmation_and_invalid_command(self) -> None:
        args = common_args(["human", "bot"])
        oop_code, oop_output = run_main(oop_main, args, ["nonsense", "quit", "y"])
        func_code, func_output = run_main(func_main, args, ["nonsense", "quit", "y"])
        self.assertEqual((oop_code, func_code), (0, 0))
        self.assertEqual(oop_output, func_output)
        self.assertIn("Unknown command", oop_output)
        self.assertIn("Game quit.", oop_output)

    def test_commentary_can_switch_mid_match(self) -> None:
        args = common_args(["human", "bot"])
        _, oop_output = run_main(oop_main, args, ["commentary code", "quit", "y"])
        _, func_output = run_main(func_main, args, ["commentary code", "quit", "y"])
        self.assertIn("Commentary set to code.", oop_output)
        self.assertIn("Commentary set to code.", func_output)
        self.assertIn("OOP: LudoGame.quit()", oop_output)
        self.assertIn("Functional: quit(state)", func_output)

    def test_no_color_output_contains_no_ansi(self) -> None:
        args = common_args(["human", "bot"])
        _, output = run_main(oop_main, args, ["quit", "y"])
        self.assertNotIn("\033[", output)
        self.assertNotIn("★", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
