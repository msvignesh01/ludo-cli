"""Display-independent helpers shared by both graphical interfaces."""

from __future__ import annotations

from typing import Any

from .contracts import PLAYER_SPECS, get_start_indices
from .geometry import build_board_geometry


COMMENTARY_MODES: tuple[str, ...] = ("gameplay", "code", "both", "off")
SPEED_DELAYS: dict[str, float] = {"slow": 0.8, "normal": 0.35, "fast": 0.05}


def speed_delay(speed: str) -> float:
    """Return the validated delay in seconds for a named GUI speed."""
    normalized = speed.strip().lower()
    if normalized not in SPEED_DELAYS:
        raise ValueError("Speed must be slow, normal, or fast.")
    return SPEED_DELAYS[normalized]


def next_commentary_mode(mode: str) -> str:
    """Return the next commentary mode in the fixed rotation."""
    if mode not in COMMENTARY_MODES:
        raise ValueError("Unknown commentary mode.")
    index = COMMENTARY_MODES.index(mode)
    return COMMENTARY_MODES[(index + 1) % len(COMMENTARY_MODES)]


def format_commentary(event: dict[str, Any], mode: str, gameplay_text: str, code_text: str) -> list[str]:
    """Format one event using the selected audience and paradigm labels."""
    if mode == "off":
        return []
    if mode == "gameplay":
        return [gameplay_text]
    if mode == "code":
        return [code_text]
    if mode == "both":
        return [f"[Gameplay] {gameplay_text}", f"[Code] {code_text}"]
    raise ValueError("Commentary must be gameplay, code, both, or off.")


def build_gui_view_model(
    snapshot: dict[str, Any],
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map canonical tokens to board cells without importing a GUI toolkit."""
    config = snapshot["config"]
    board = geometry if geometry is not None else build_board_geometry(config)
    track_len = int(config["track_len"])
    home_finish = int(config["home_finish"])
    markers: list[dict[str, Any]] = []

    for player in snapshot["players"]:
        player_index = int(player["index"])
        spec = PLAYER_SPECS[player_index]
        for token_index, token in enumerate(player["tokens"]):
            steps = int(token["steps"])
            global_pos: int | None = None
            if steps == -1:
                location = "base"
                box = board["yard_boxes"][player_index]
                cell = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]
            elif steps == home_finish:
                location = "finished"
                cell = list(board["home_center"])
            elif steps >= track_len - 1:
                location = "home"
                lane_index = steps - (track_len - 1)
                cell = list(board["home_cells"][player_index][lane_index])
            else:
                location = "track"
                global_pos = (int(player["start_index"]) + steps) % track_len
                cell = list(board["track_cells"][global_pos])
            markers.append(
                {
                    "player_index": player_index,
                    "token_idx": token_index,
                    "label": token["label"],
                    "steps": steps,
                    "location": location,
                    "global_pos": global_pos,
                    "cell": cell,
                    "color": player["color"],
                    "color_hex": spec["hex"],
                    "prefix": spec["prefix"],
                }
            )

    players = [
        {
            **player,
            "color_hex": PLAYER_SPECS[int(player["index"])]["hex"],
            "prefix": PLAYER_SPECS[int(player["index"])]["prefix"],
        }
        for player in snapshot["players"]
    ]
    safe_tiles = list(config["safe_tiles"]) if config["safe_tiles_enabled"] else []
    return {
        "config": config,
        "geometry": board,
        "markers": markers,
        "players": players,
        "safe_tiles": safe_tiles,
        "start_tiles": get_start_indices(config),
        "current_player": snapshot["current_player"],
        "turn_count": snapshot["turn_count"],
        "status": snapshot["status"],
        "winner_index": snapshot["winner_index"],
        "draw_reason": snapshot["draw_reason"],
        "last_event": snapshot["last_event"],
    }
