#!/usr/bin/env python3
"""Tests for locked Quick and Classic cross-board geometry."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1_initial.shared.contracts import build_config  # noqa: E402
from v1_initial.shared.geometry import build_board_geometry  # noqa: E402


class GuiGeometryTest(unittest.TestCase):
    """Verify geometry is complete, cyclic, and JSON-serializable."""

    def test_quick_is_nine_by_nine_with_twenty_eight_route_cells(self) -> None:
        geometry = build_board_geometry(build_config("quick"))
        self.assertEqual(geometry["size"], 9)
        self.assertEqual(len(geometry["track_cells"]), 28)
        self.assertEqual(len({tuple(cell) for cell in geometry["track_cells"]}), 28)

    def test_classic_is_fifteen_by_fifteen_with_fifty_two_route_cells(self) -> None:
        geometry = build_board_geometry(build_config("classic"))
        self.assertEqual(geometry["size"], 15)
        self.assertEqual(len(geometry["track_cells"]), 52)
        self.assertEqual(len({tuple(cell) for cell in geometry["track_cells"]}), 52)

    def test_route_is_one_closed_adjacent_cycle(self) -> None:
        for mode in ("quick", "classic"):
            with self.subTest(mode=mode):
                cells = build_board_geometry(build_config(mode))["track_cells"]
                for index, cell in enumerate(cells):
                    following = cells[(index + 1) % len(cells)]
                    dx = abs(cell[0] - following[0])
                    dy = abs(cell[1] - following[1])
                    self.assertTrue(dx + dy == 1 or (dx == 1 and dy == 1))

    def test_home_lanes_have_configured_length_and_do_not_overlap_track(self) -> None:
        for mode in ("quick", "classic"):
            with self.subTest(mode=mode):
                config = build_config(mode)
                geometry = build_board_geometry(config)
                track = {tuple(cell) for cell in geometry["track_cells"]}
                for lane in geometry["home_cells"]:
                    self.assertEqual(len(lane), config["home_len"])
                    self.assertTrue(track.isdisjoint(tuple(cell) for cell in lane))

    def test_two_player_yards_match_diagonal_seating(self) -> None:
        for mode in ("quick", "classic"):
            with self.subTest(mode=mode):
                geometry = build_board_geometry(build_config(mode, player_count=2))
                boxes = geometry["yard_boxes"]
                self.assertEqual(boxes[0][0], boxes[0][1])
                self.assertEqual(boxes[1][0], boxes[1][1])
                self.assertNotEqual(boxes[0][0], boxes[1][0])
                self.assertNotEqual(boxes[0][1], boxes[1][1])
                first_home = geometry["home_cells"][0][0]
                second_home = geometry["home_cells"][1][0]
                self.assertLess(first_home[0], geometry["center"])
                self.assertGreater(second_home[0], geometry["center"])

    def test_geometry_is_json_serializable(self) -> None:
        geometry = build_board_geometry(build_config("quick", player_count=3))
        json.dumps(geometry)
        self.assertEqual(len(geometry["yard_boxes"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
