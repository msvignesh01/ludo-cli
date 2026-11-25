"""Deterministic heuristic policy for functional bot seats."""

from __future__ import annotations

from typing import Any

from .rules import get_global_pos, is_safe_tile, preview_move


def _can_be_captured(state: dict[str, Any], player_idx: int, global_pos: int | None) -> bool:
    """Return whether an opponent can reach a tile with one die roll."""
    config = state["config"]
    if global_pos is None or is_safe_tile(state, global_pos):
        return False
    for opponent in state["players"]:
        if opponent["index"] == player_idx:
            continue
        for token in opponent["tokens"]:
            opponent_pos = get_global_pos(
                opponent["start_index"],
                token["steps"],
                int(config["track_len"]),
                int(config["outer_last_step"]),
            )
            if opponent_pos is None:
                continue
            distance = (global_pos - opponent_pos) % config["track_len"]
            if 1 <= distance <= 6:
                return True
    return False


def _token_in_danger(state: dict[str, Any], player_idx: int, token_idx: int) -> bool:
    """Return whether one token is exposed to capture."""
    config = state["config"]
    player = state["players"][player_idx]
    token = player["tokens"][token_idx]
    global_pos = get_global_pos(
        player["start_index"],
        token["steps"],
        int(config["track_len"]),
        int(config["outer_last_step"]),
    )
    return _can_be_captured(state, player_idx, global_pos)


def _score(state: dict[str, Any], player_idx: int, token_idx: int, roll: int) -> tuple[int, ...]:
    """Build the lexicographic priority score for one legal move."""
    config = state["config"]
    player = state["players"][player_idx]
    preview = preview_move(state, player_idx, token_idx, roll)
    captured = len(preview["captured"])
    unlock = bool(config["kill_to_enter"] and player["captures_made"] == 0 and captured)
    escape = _token_in_danger(state, player_idx, token_idx) and not _can_be_captured(
        state,
        player_idx,
        preview["global_pos"],
    )
    progress = int(preview["new_steps"])
    if preview["wrapped"]:
        progress += config["track_len"]
    return (
        int(bool(preview["reached_home"])),
        captured,
        int(unlock),
        int(bool(preview["safe"])),
        int(escape),
        progress,
        -token_idx,
    )


def decision_details(
    state: dict[str, Any],
    player_idx: int,
    roll: int,
    valid_moves: list[int],
) -> dict[str, Any]:
    """Return the selected token and the highest satisfied priority."""
    if not valid_moves:
        return {"token_idx": None, "reason": "No legal moves"}
    token_idx = max(valid_moves, key=lambda candidate: _score(state, player_idx, candidate, roll))
    config = state["config"]
    player = state["players"][player_idx]
    preview = preview_move(state, player_idx, token_idx, roll)
    if preview["reached_home"]:
        reason = "Finish Home"
    elif preview["captured"] and config["kill_to_enter"] and player["captures_made"] == 0:
        reason = "Unlock Kill-to-Enter"
    elif preview["captured"]:
        reason = "Capture"
    elif preview["safe"]:
        reason = "Safe tile"
    elif _token_in_danger(state, player_idx, token_idx) and not _can_be_captured(
        state,
        player_idx,
        preview["global_pos"],
    ):
        reason = "Escape danger"
    else:
        reason = "Advance furthest"
    return {"token_idx": token_idx, "reason": reason}


def choose_move(
    state: dict[str, Any],
    player_idx: int,
    roll: int,
    valid_moves: list[int],
) -> int | None:
    """Return one deterministic legal token index, or None when blocked."""
    token_idx = decision_details(state, player_idx, roll, valid_moves)["token_idx"]
    return int(token_idx) if token_idx is not None else None
