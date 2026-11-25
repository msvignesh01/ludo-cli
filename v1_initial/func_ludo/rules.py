"""Pure query helpers and explicit state transitions for functional Ludo."""

from __future__ import annotations

from typing import Any

from ..shared.contracts import make_event
from .state import export_canonical_state


def _emit(
    state: dict[str, Any],
    event_type: str,
    player_index: int | None,
    data: dict[str, Any] | None = None,
) -> None:
    """Append one deterministic event to the state's event stream."""
    state["events"].append(make_event(event_type, state["turn_count"], player_index, data))


def roll_die(state: dict[str, Any]) -> int:
    """Roll the isolated six-sided die stored in the state."""
    return state["rng"].randint(1, 6)


def get_global_pos(start_index: int, steps: int, track_len: int, outer_last_step: int) -> int | None:
    """Translate personal steps to a shared outer-track index."""
    if steps < 0 or steps > outer_last_step:
        return None
    return (start_index + steps) % track_len


def is_safe_tile(state: dict[str, Any], global_pos: int | None) -> bool:
    """Return whether captures are disabled on a shared tile."""
    config = state["config"]
    return (
        bool(config["safe_tiles_enabled"])
        and global_pos is not None
        and global_pos in set(config["safe_tiles"])
    )


def format_position(state: dict[str, Any], start_index: int, steps: int) -> str:
    """Return a compact human-readable token position."""
    config = state["config"]
    if steps == -1:
        return "BASE"
    if steps == config["home_finish"]:
        return "HOME"
    if steps >= config["track_len"] - 1:
        return f"H{steps - (config['track_len'] - 1) + 1}"
    global_pos = get_global_pos(
        start_index,
        steps,
        int(config["track_len"]),
        int(config["outer_last_step"]),
    )
    return f"T{global_pos:02d}" if global_pos is not None else "BASE"


def _all_finished(player: dict[str, Any], home_finish: int) -> bool:
    """Return whether every token in a player dictionary is home."""
    return all(token["steps"] == home_finish for token in player["tokens"])


def _tokens_at(state: dict[str, Any], player: dict[str, Any], global_pos: int) -> list[dict[str, Any]]:
    """Return one player's tokens occupying a shared tile."""
    config = state["config"]
    return [
        token
        for token in player["tokens"]
        if get_global_pos(
            player["start_index"],
            token["steps"],
            int(config["track_len"]),
            int(config["outer_last_step"]),
        )
        == global_pos
    ]


def _kill_locked(state: dict[str, Any], player: dict[str, Any]) -> bool:
    """Return whether a player still needs a capture to enter home."""
    return bool(state["config"]["kill_to_enter"]) and player["captures_made"] == 0


def _compute_target(
    state: dict[str, Any],
    player: dict[str, Any],
    token: dict[str, Any],
    roll: int,
) -> tuple[int, bool, list[int]] | None:
    """Compute target steps, wrap status, and visited personal steps."""
    config = state["config"]
    if token["steps"] == -1:
        if roll != 6:
            return None
        return 0, False, [0]
    if token["steps"] == config["home_finish"]:
        return None

    old_steps = int(token["steps"])
    raw_target = old_steps + roll
    if (
        _kill_locked(state, player)
        and 0 <= old_steps <= config["outer_last_step"]
        and raw_target >= config["track_len"] - 1
    ):
        lap_len = int(config["track_len"]) - 1
        new_steps = raw_target % lap_len
        path = list(range(old_steps + 1, int(config["outer_last_step"]) + 1))
        path.extend(range(0, new_steps + 1))
        return new_steps, True, path

    if raw_target > config["home_finish"]:
        if config["exact_home_roll"]:
            return None
        new_steps = int(config["home_finish"])
    else:
        new_steps = raw_target
    path = [
        steps
        for steps in range(old_steps + 1, new_steps + 1)
        if steps <= config["outer_last_step"]
    ]
    return new_steps, False, path


def _global_path(state: dict[str, Any], player: dict[str, Any], path: list[int]) -> list[int]:
    """Translate visited personal steps into shared tile indices."""
    config = state["config"]
    positions: list[int] = []
    for steps in path:
        global_pos = get_global_pos(
            player["start_index"],
            steps,
            int(config["track_len"]),
            int(config["outer_last_step"]),
        )
        if global_pos is not None:
            positions.append(global_pos)
    return positions


def _strict_path_blocked(state: dict[str, Any], player: dict[str, Any], path: list[int]) -> bool:
    """Return whether a strict enemy blockade intersects the move path."""
    if state["config"]["blockades"] != "strict":
        return False
    for global_pos in _global_path(state, player, path):
        for opponent in state["players"]:
            if opponent["index"] != player["index"] and len(_tokens_at(state, opponent, global_pos)) >= 2:
                return True
    return False


def _capturable_tokens(
    state: dict[str, Any],
    player: dict[str, Any],
    global_pos: int | None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return opponent token dictionaries that a landing would capture."""
    if global_pos is None or is_safe_tile(state, global_pos):
        return []
    captured: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for opponent in state["players"]:
        if opponent["index"] == player["index"]:
            continue
        tokens = _tokens_at(state, opponent, global_pos)
        if state["config"]["blockades"] == "safe_pair" and len(tokens) >= 2:
            continue
        captured.extend((opponent, token) for token in tokens)
    return captured


def preview_move(
    state: dict[str, Any],
    player_idx: int,
    token_idx: int,
    roll: int,
) -> dict[str, Any]:
    """Describe a move and its consequences without mutating state."""
    config = state["config"]
    player = state["players"][player_idx]
    token = player["tokens"][token_idx]
    target = _compute_target(state, player, token, roll)
    if target is None:
        return {"legal": False, "reason": "Move is not legal for this roll."}
    new_steps, wrapped, path = target
    if _strict_path_blocked(state, player, path):
        return {"legal": False, "reason": "A strict blockade blocks the path."}
    global_pos = get_global_pos(
        player["start_index"],
        new_steps,
        int(config["track_len"]),
        int(config["outer_last_step"]),
    )
    captured = _capturable_tokens(state, player, global_pos)
    reached_home = new_steps == config["home_finish"]
    friendly_before = len(_tokens_at(state, player, global_pos)) if global_pos is not None else 0
    blockade_formed = global_pos is not None and friendly_before < 2 and friendly_before + 1 >= 2
    return {
        "legal": True,
        "label": token["label"],
        "token_idx": token_idx,
        "old_steps": token["steps"],
        "new_steps": new_steps,
        "old_position": format_position(state, player["start_index"], token["steps"]),
        "new_position": format_position(state, player["start_index"], new_steps),
        "global_pos": global_pos,
        "captured": [f"{owner['name']}'s {victim['label']}" for owner, victim in captured],
        "reached_home": reached_home,
        "safe": is_safe_tile(state, global_pos),
        "wrapped": wrapped,
        "blockade_formed": blockade_formed,
    }


def get_valid_moves(state: dict[str, Any], player_idx: int, roll: int) -> list[int]:
    """Return every legal token index for a player and roll."""
    player = state["players"][player_idx]
    return [
        int(token["token_idx"])
        for token in player["tokens"]
        if preview_move(state, player_idx, int(token["token_idx"]), roll)["legal"]
    ]


def process_roll(state: dict[str, Any], roll: int) -> dict[str, Any]:
    """Resolve the die roll, triple-six penalty, and automatic skips."""
    player_index = state["current_player"]
    _emit(state, "DICE_ROLLED", player_index, {"roll": roll})
    if roll == 6:
        state["consecutive_sixes"] += 1
        if state["config"]["triple_six_forfeit"] and state["consecutive_sixes"] == 3:
            state["consecutive_sixes"] = 0
            state["last_event"] = "Third consecutive six forfeited."
            _emit(state, "TRIPLE_SIX_FORFEIT", player_index)
            advance_turn(state)
            return {"event": "TRIPLE_SIX_FORFEIT", "valid_moves": []}
    else:
        state["consecutive_sixes"] = 0

    valid_moves = get_valid_moves(state, player_index, roll)
    if not valid_moves:
        state["consecutive_sixes"] = 0
        state["last_event"] = f"No legal move for roll {roll}; turn skipped."
        _emit(state, "NO_VALID_MOVES", player_index, {"roll": roll})
        advance_turn(state)
        return {"event": "NO_VALID_MOVES", "valid_moves": []}
    state["last_event"] = f"Rolled {roll}; choose a token."
    return {"event": "SELECT_MOVE", "valid_moves": valid_moves}


def apply_move(state: dict[str, Any], token_idx: int, roll: int) -> dict[str, Any]:
    """Apply one legal move, captures, finishing, and turn rewards."""
    config = state["config"]
    player_index = state["current_player"]
    player = state["players"][player_index]
    token = player["tokens"][token_idx]
    preview = preview_move(state, player_index, token_idx, roll)
    if not preview["legal"]:
        raise ValueError("Illegal move")
    old_steps = int(token["steps"])
    new_steps = int(preview["new_steps"])
    token["steps"] = new_steps
    _emit(
        state,
        "TOKEN_MOVED",
        player_index,
        {
            "token": token["label"],
            "token_idx": token_idx,
            "roll": roll,
            "old_steps": old_steps,
            "new_steps": new_steps,
            "wrapped": preview["wrapped"],
        },
    )

    captured_labels: list[str] = []
    global_pos = preview["global_pos"]
    for owner, victim in _capturable_tokens(state, player, global_pos):
        victim["steps"] = -1
        player["captures_made"] += 1
        captured_labels.append(f"{owner['name']}'s {victim['label']}")
        _emit(
            state,
            "TOKEN_CAPTURED",
            player_index,
            {
                "mover": token["label"],
                "victim_player": owner["index"],
                "victim_token": victim["label"],
            },
        )

    if preview["blockade_formed"] and global_pos is not None:
        _emit(
            state,
            "BLOCKADE_FORMED",
            player_index,
            {"tile": global_pos, "token": token["label"]},
        )

    reached_home = bool(preview["reached_home"])
    if reached_home:
        state["consecutive_sixes"] = 0
    player_finished = _all_finished(player, int(config["home_finish"]))
    if player_finished and player_index not in state["finish_order"]:
        state["finish_order"].append(player_index)
        _emit(state, "PLAYER_FINISHED", player_index, {"place": len(state["finish_order"])})

    required_finishers = config["player_count"] - 1 if config["podium_mode"] else 1
    won = player_finished and len(state["finish_order"]) >= required_finishers
    bonus_turn = False
    if won:
        state["status"] = "WON"
        state["winner_index"] = state["finish_order"][0]
        state["last_event"] = f"{state['players'][state['winner_index']]['name']} wins!"
        _emit(state, "GAME_WON", state["winner_index"], {"finish_order": list(state["finish_order"])})
    elif player_finished:
        state["last_event"] = f"{player['name']} finished; advancing to the remaining players."
        advance_turn(state)
    else:
        bonus_turn = bool(
            roll == 6
            or (captured_labels and config["bonus_on_capture"])
            or (reached_home and config["bonus_on_home"])
        )
        if bonus_turn:
            state["last_event"] = f"Bonus roll for {player['name']}."
            _emit(state, "BONUS_TURN", player_index, {"roll": roll})
        else:
            state["consecutive_sixes"] = 0
            advance_turn(state)

    return {
        "old_steps": old_steps,
        "new_steps": new_steps,
        "captured": captured_labels,
        "reached_home": reached_home,
        "wrapped": bool(preview["wrapped"]),
        "player_finished": player_finished,
        "won": won,
        "bonus_turn": bonus_turn,
        "blockade_formed": bool(preview["blockade_formed"]),
    }


def record_bot_decision(state: dict[str, Any], token_idx: int, roll: int, reason: str) -> None:
    """Record a deterministic bot choice in the shared event stream."""
    player = state["players"][state["current_player"]]
    _emit(
        state,
        "BOT_DECISION",
        player["index"],
        {
            "token": player["tokens"][token_idx]["label"],
            "token_idx": token_idx,
            "roll": roll,
            "reason": reason,
        },
    )


def advance_turn(state: dict[str, Any]) -> None:
    """Advance to the next unfinished player and enforce the turn cap."""
    if state["status"] != "PLAYING":
        return
    state["consecutive_sixes"] = 0
    for offset in range(1, len(state["players"]) + 1):
        candidate = (state["current_player"] + offset) % len(state["players"])
        if not _all_finished(state["players"][candidate], int(state["config"]["home_finish"])):
            state["current_player"] = candidate
            break
    state["turn_count"] += 1
    _emit(state, "TURN_ADVANCED", state["current_player"])
    if state["turn_count"] >= state["max_turns"]:
        state["status"] = "DRAW"
        state["draw_reason"] = "Maximum turn limit reached"
        state["last_event"] = state["draw_reason"]
        _emit(state, "GAME_DRAW", None, {"reason": state["draw_reason"]})


def declare_mutual_draw(state: dict[str, Any]) -> None:
    """End the match by mutual agreement."""
    state["status"] = "DRAW"
    state["draw_reason"] = "Mutual agreement"
    state["last_event"] = state["draw_reason"]
    _emit(state, "GAME_DRAW", None, {"reason": state["draw_reason"]})


def quit(state: dict[str, Any]) -> None:
    """End the match with a clean quit status."""
    state["status"] = "QUIT"
    state["last_event"] = "Game quit."
    _emit(state, "GAME_QUIT", None)
