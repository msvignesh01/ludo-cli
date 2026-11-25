#!/usr/bin/env python3
"""Tests for pure GUI layout and duck-typed canvas drawing helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.contracts import build_config  # noqa: E402
from v1_initial.shared.gui_drawing import (  # noqa: E402
    SAFE_FILL,
    cell_center,
    cell_rectangle,
    contrast_text,
    describe_move,
    draw_board,
    draw_tokens,
    mix_hex,
    stack_offsets,
)
from v1_initial.shared.gui_support import build_gui_view_model  # noqa: E402
from v1_initial.oop_ludo.engine import LudoGame  # noqa: E402


class RecordingCanvas:
    """Record canvas calls without requiring Tk or a graphical display."""

    def __init__(self) -> None:
        """Initialize empty drawing records."""
        self.deleted: list[str] = []
        self.rectangles: list[tuple[tuple[float, ...], dict[str, Any]]] = []
        self.ovals: list[tuple[tuple[float, ...], dict[str, Any]]] = []
        self.texts: list[tuple[tuple[float, float], dict[str, Any]]] = []

    def delete(self, tag: str) -> None:
        """Record a canvas clear operation."""
        self.deleted.append(tag)

    def create_rectangle(self, *coordinates: float, **options: Any) -> None:
        """Record a rectangle."""
        self.rectangles.append((coordinates, options))

    def create_oval(self, *coordinates: float, **options: Any) -> None:
        """Record a token circle."""
        self.ovals.append((coordinates, options))

    def create_text(self, x: float, y: float, **options: Any) -> None:
        """Record a text label."""
        self.texts.append(((x, y), options))


class GuiLayoutTest(unittest.TestCase):
    """Verify pixel geometry, colors, and move descriptions."""

    def test_cell_coordinates_include_margin_and_half_cell_center(self) -> None:
        self.assertEqual(cell_rectangle([1, 2], 40, 10), (50, 90, 90, 130))
        self.assertEqual(cell_center([1, 2], 40, 10), (70, 110))

    def test_color_helpers_are_deterministic_and_readable(self) -> None:
        self.assertEqual(mix_hex("#000000", "#FFFFFF", 0.5), "#808080")
        self.assertEqual(contrast_text("#000000"), "#FFFFFF")
        self.assertEqual(contrast_text("#FFFFFF"), "#111827")
        self.assertEqual(contrast_text("#3B82F6"), "#FFFFFF")

    def test_stack_offsets_are_centered_and_unique(self) -> None:
        self.assertEqual(stack_offsets(1, 40), [(0.0, 0.0)])
        offsets = stack_offsets(4, 40)
        self.assertEqual(len(set(offsets)), 4)
        self.assertAlmostEqual(sum(item[0] for item in offsets), 0.0)
        self.assertAlmostEqual(sum(item[1] for item in offsets), 0.0)

    def test_move_description_exposes_destination_and_consequences(self) -> None:
        preview = {
            "label": "R1",
            "old_position": "T04",
            "new_position": "T08",
            "captured": ["Bala's G1"],
            "reached_home": False,
            "wrapped": True,
        }
        text = describe_move(preview)
        self.assertIn("R1", text)
        self.assertIn("T04 -> T08", text)
        self.assertIn("capture", text.lower())
        self.assertIn("wrap", text.lower())


class GuiDrawingTest(unittest.TestCase):
    """Verify board and token drawing from a canonical view model."""

    def make_model(self) -> dict[str, Any]:
        """Create a two-player Quick board with tokens in their yards."""
        config = build_config("quick", "classic", 2)
        game = LudoGame(config, ["Asha", "Bala"], seed=42)
        return build_gui_view_model(game.export_canonical_state())

    def test_board_draws_every_route_home_center_and_yard_cell(self) -> None:
        canvas = RecordingCanvas()
        model = self.make_model()
        draw_board(canvas, model, cell_size=40, margin=10)
        self.assertEqual(canvas.deleted, ["all"])
        expected = (
            len(model["geometry"]["track_cells"])
            + sum(len(lane) for lane in model["geometry"]["home_cells"])
            + 1
            + len(model["geometry"]["yard_boxes"])
        )
        self.assertEqual(len(canvas.rectangles), expected)
        safe_rectangles = [options for _, options in canvas.rectangles if options.get("fill") == SAFE_FILL]
        self.assertEqual(len(safe_rectangles), len(model["safe_tiles"]) - len(model["start_tiles"]))

    def test_tokens_draw_one_circle_and_label_per_token(self) -> None:
        canvas = RecordingCanvas()
        model = self.make_model()
        draw_tokens(canvas, model, cell_size=40, margin=10)
        self.assertEqual(len(canvas.ovals), len(model["markers"]))
        token_labels = [options["text"] for _, options in canvas.texts]
        self.assertEqual(token_labels.count("R1"), 1)
        self.assertEqual(token_labels.count("G2"), 1)

    def test_shared_tile_tokens_receive_distinct_offsets(self) -> None:
        canvas = RecordingCanvas()
        model = self.make_model()
        model["markers"] = [marker for marker in model["markers"] if marker["token_idx"] == 0]
        for marker in model["markers"]:
            marker["location"] = "track"
            marker["steps"] = 4
            marker["global_pos"] = 4 if marker["player_index"] == 0 else 8
            marker["cell"] = list(model["geometry"]["track_cells"][4])
        draw_tokens(canvas, model, cell_size=40, margin=10)
        self.assertEqual(len(canvas.ovals), 2)
        self.assertNotEqual(canvas.ovals[0][0], canvas.ovals[1][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
