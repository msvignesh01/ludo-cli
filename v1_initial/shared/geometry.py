"""Locked cross-shaped board geometry derived from mode presets."""

from __future__ import annotations

from typing import Any


def _boundary_cycle(size: int, center: int) -> list[list[int]]:
    """Trace the outer boundary of a three-cell-wide cross as one cycle."""
    cross = {
        (x, y)
        for x in range(size)
        for y in range(size)
        if center - 1 <= x <= center + 1 or center - 1 <= y <= center + 1
    }
    boundary = {
        (x, y)
        for x, y in cross
        if any(
            (x + dx, y + dy) not in cross
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    }
    orthogonal = ((1, 0), (-1, 0), (0, 1), (0, -1))
    links: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for cell in boundary:
        links[cell] = [
            (cell[0] + dx, cell[1] + dy)
            for dx, dy in orthogonal
            if (cell[0] + dx, cell[1] + dy) in boundary
        ]
    endpoints = [cell for cell, neighbors in links.items() if len(neighbors) == 1]
    for cell in endpoints:
        diagonal = [
            other
            for other in endpoints
            if other != cell
            and abs(other[0] - cell[0]) == 1
            and abs(other[1] - cell[1]) == 1
        ]
        if len(diagonal) == 1 and diagonal[0] not in links[cell]:
            links[cell].append(diagonal[0])
            links[diagonal[0]].append(cell)

    start = (0, center - 1)
    cycle: list[list[int]] = [list(start)]
    previous = start
    current = (1, center - 1)
    while current != start:
        cycle.append(list(current))
        candidates = [cell for cell in links[current] if cell != previous and list(cell) not in cycle]
        if not candidates:
            break
        previous, current = current, candidates[0]
    return cycle


def build_board_geometry(config: dict[str, Any]) -> dict[str, Any]:
    """Build route, home-lane, and yard coordinates for the active preset."""
    quadrants = int(config["track_len"]) // 4
    size = quadrants + 2
    center = size // 2
    home_len = int(config["home_len"])
    track_len = int(config["track_len"])
    track_cells = _boundary_cycle(size, center)
    all_home_cells = [
        [[x, center] for x in range(1, 1 + home_len)],
        [[center, y] for y in range(1, 1 + home_len)],
        [[x, center] for x in range(size - 2, size - 2 - home_len, -1)],
        [[center, y] for y in range(size - 2, size - 2 - home_len, -1)],
    ]
    corner = center - 1
    right_start = center + 2
    all_yard_boxes = [
        [0, 0, corner - 1, corner - 1],
        [right_start, 0, size - 1, corner - 1],
        [right_start, right_start, size - 1, size - 1],
        [0, right_start, corner - 1, size - 1],
    ]
    start_key = "start_indices_2p" if int(config["player_count"]) == 2 else "start_indices_4p"
    starts = config[start_key][: int(config["player_count"])]
    yard_count = len(all_yard_boxes)
    seat_quadrants = [(int(start) * yard_count // track_len) % yard_count for start in starts]
    home_cells = [all_home_cells[quadrant] for quadrant in seat_quadrants]
    yard_boxes = [all_yard_boxes[quadrant] for quadrant in seat_quadrants]
    return {
        "size": size,
        "center": center,
        "track_cells": track_cells,
        "home_cells": home_cells,
        "yard_boxes": yard_boxes,
        "home_center": [center, center],
    }
