"""Pure layout and duck-typed canvas drawing shared by both GUIs."""

from __future__ import annotations

import math
from typing import Any


SAFE_FILL = "#D1FAE5"
BOARD_OUTLINE = "#CBD5E1"
BOARD_TEXT = "#475569"
CENTER_FILL = "#0F172A"


def mix_hex(first: str, second: str, amount: float) -> str:
    """Blend two six-digit hex colors using the second color's weight."""
    first_rgb = [int(first[index : index + 2], 16) for index in (1, 3, 5)]
    second_rgb = [int(second[index : index + 2], 16) for index in (1, 3, 5)]
    channels = [
        round(start + (end - start) * amount)
        for start, end in zip(first_rgb, second_rgb)
    ]
    return "#" + "".join(f"{channel:02X}" for channel in channels)


def contrast_text(background: str) -> str:
    """Return white or dark text based on relative visual brightness."""
    channels = [int(background[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
    return "#FFFFFF" if luminance < 0.5 else "#111827"


def cell_rectangle(cell: list[float], cell_size: int, margin: int) -> tuple[float, float, float, float]:
    """Convert a grid cell into canvas pixel coordinates."""
    x, y = cell
    left = margin + x * cell_size
    top = margin + y * cell_size
    return left, top, left + cell_size, top + cell_size


def cell_center(cell: list[float], cell_size: int, margin: int) -> tuple[float, float]:
    """Return the pixel center of a grid cell."""
    x, y = cell
    return margin + (x + 0.5) * cell_size, margin + (y + 0.5) * cell_size


def stack_offsets(count: int, cell_size: int) -> list[tuple[float, float]]:
    """Arrange stacked tokens in a compact centered grid."""
    if count <= 0:
        return []
    columns = int(math.ceil(math.sqrt(count)))
    rows = int(math.ceil(count / columns))
    spacing = cell_size * 0.42
    return [
        (
            (column - (columns - 1) / 2) * spacing,
            (row - (rows - 1) / 2) * spacing,
        )
        for row in range(rows)
        for column in range(columns)
    ][:count]


def describe_move(preview: dict[str, Any]) -> str:
    """Build one concise label for a graphical token button."""
    effects: list[str] = []
    if preview.get("captured"):
        effects.append("capture")
    if preview.get("reached_home"):
        effects.append("home")
    if preview.get("wrapped"):
        effects.append("wrap")
    if preview.get("blockade_formed"):
        effects.append("pair")
    suffix = f" ({', '.join(effects)})" if effects else ""
    return f"{preview['label']}: {preview['old_position']} -> {preview['new_position']}{suffix}"


def draw_board(canvas: Any, model: dict[str, Any], cell_size: int, margin: int) -> None:
    """Draw route, home lanes, center, and player yards on a canvas-like object."""
    canvas.delete("all")
    geometry = model["geometry"]
    players = model["players"]
    safe_tiles = set(model["safe_tiles"])
    start_colors = {
        int(tile): players[index]["color_hex"]
        for index, tile in enumerate(model["start_tiles"])
    }
    tile_font = ("Segoe UI", max(6, int(cell_size * 0.18)), "bold")

    for tile, cell in enumerate(geometry["track_cells"]):
        left, top, right, bottom = cell_rectangle(cell, cell_size, margin)
        if tile in start_colors:
            fill = mix_hex("#FFFFFF", start_colors[tile], 0.35)
        elif tile in safe_tiles:
            fill = SAFE_FILL
        else:
            fill = "#F8FAFC"
        canvas.create_rectangle(left, top, right, bottom, fill=fill, outline=BOARD_OUTLINE, width=1)
        center_x, center_y = cell_center(cell, cell_size, margin)
        canvas.create_text(center_x, center_y, text=str(tile), fill=BOARD_TEXT, font=tile_font)
        if tile in safe_tiles:
            canvas.create_text(
                left + cell_size * 0.2,
                top + cell_size * 0.2,
                text="S",
                fill="#047857",
                font=("Segoe UI", max(6, int(cell_size * 0.16)), "bold"),
            )

    for player_index, lane in enumerate(geometry["home_cells"]):
        color = players[player_index]["color_hex"]
        for lane_index, cell in enumerate(lane):
            left, top, right, bottom = cell_rectangle(cell, cell_size, margin)
            canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                fill=mix_hex("#FFFFFF", color, 0.72),
                outline=color,
                width=1,
            )
            center_x, center_y = cell_center(cell, cell_size, margin)
            canvas.create_text(
                center_x,
                center_y,
                text=f"H{lane_index + 1}",
                fill=BOARD_TEXT,
                font=tile_font,
            )

    center_cell = [geometry["center"], geometry["center"]]
    left, top, right, bottom = cell_rectangle(center_cell, cell_size, margin)
    canvas.create_rectangle(left, top, right, bottom, fill=CENTER_FILL, outline="#334155", width=2)
    center_x, center_y = cell_center(center_cell, cell_size, margin)
    canvas.create_text(
        center_x,
        center_y,
        text="HOME",
        fill="#FFFFFF",
        font=("Segoe UI", max(8, int(cell_size * 0.24)), "bold"),
    )

    for player_index, box in enumerate(geometry["yard_boxes"]):
        player = players[player_index]
        color = player["color_hex"]
        left = margin + box[0] * cell_size
        top = margin + box[1] * cell_size
        right = margin + (box[2] + 1) * cell_size
        bottom = margin + (box[3] + 1) * cell_size
        active = player_index == model["current_player"] and model["status"] == "PLAYING"
        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=mix_hex("#FFFFFF", color, 0.86),
            outline=color,
            width=4 if active else 2,
        )
        canvas.create_text(
            left + cell_size * 0.35,
            top + cell_size * 0.35,
            text=player["name"],
            anchor="w",
            fill=CENTER_FILL,
            font=("Segoe UI", max(8, int(cell_size * 0.24)), "bold"),
        )


def draw_tokens(canvas: Any, model: dict[str, Any], cell_size: int, margin: int) -> None:
    """Draw color-coded token circles with distinct offsets for shared cells."""
    groups: dict[tuple[str, tuple[float, float]], list[dict[str, Any]]] = {}
    for marker in model["markers"]:
        key = (marker["location"], tuple(marker["cell"]))
        groups.setdefault(key, []).append(marker)

    for (location, _), markers in groups.items():
        offsets = stack_offsets(len(markers), cell_size)
        if len(markers) <= 2:
            radius = cell_size * 0.22
        elif len(markers) <= 4:
            radius = cell_size * 0.17
        else:
            radius = cell_size * 0.12
        if location == "base":
            radius *= 0.9
        for marker, (offset_x, offset_y) in zip(markers, offsets):
            center_x, center_y = cell_center(list(marker["cell"]), cell_size, margin)
            center_x += offset_x
            center_y += offset_y
            color = marker["color_hex"]
            text_color = contrast_text(color)
            active = marker["player_index"] == model["current_player"] and model["status"] == "PLAYING"
            canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                fill=color,
                outline="#FFFFFF" if active else text_color,
                width=2 if active else 1,
            )
            canvas.create_text(
                center_x,
                center_y,
                text=marker["label"],
                fill=text_color,
                font=("Segoe UI", max(5, int(cell_size * 0.14)), "bold"),
            )
