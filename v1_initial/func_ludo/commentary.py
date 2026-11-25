"""Gameplay and zero-class functional call-trace commentary."""

from __future__ import annotations

from typing import Any


def _name(player_names: list[str], player_index: int | None) -> str:
    """Return a safe player label for an event."""
    if player_index is None or not 0 <= player_index < len(player_names):
        return "Game"
    return player_names[player_index]


def gameplay_message(event: dict[str, Any], player_names: list[str]) -> str:
    """Render one event for a general audience."""
    kind = event["type"]
    player = _name(player_names, event["player"])
    data = event["data"]
    if kind == "GAME_STARTED":
        return "Match started."
    if kind == "DICE_ROLLED":
        return f"{player} rolls {data.get('roll')}."
    if kind == "NO_VALID_MOVES":
        return f"{player} has no legal move and skips."
    if kind == "TRIPLE_SIX_FORFEIT":
        return f"{player} forfeits the third consecutive six."
    if kind == "BOT_DECISION":
        return f"{player} bot chooses {data.get('token')}: {data.get('reason')}."
    if kind == "TOKEN_MOVED":
        return (
            f"{player} moves {data.get('token')} "
            f"from steps {data.get('old_steps')} to {data.get('new_steps')}."
        )
    if kind == "TOKEN_CAPTURED":
        victim = _name(player_names, data.get("victim_player"))
        return f"{player} captures {victim}'s {data.get('victim_token')}."
    if kind == "BLOCKADE_FORMED":
        return f"{player} forms a blockade on T{int(data.get('tile', 0)):02d}."
    if kind == "PLAYER_FINISHED":
        return f"{player} finishes in place {data.get('place')}."
    if kind == "BONUS_TURN":
        return f"{player} earns another roll."
    if kind == "TURN_ADVANCED":
        return f"Next turn: {player}."
    if kind == "GAME_WON":
        return f"{player} wins!"
    if kind == "GAME_DRAW":
        return f"Draw: {data.get('reason')}."
    if kind == "GAME_QUIT":
        return "Game quit."
    return f"{kind}."


def code_message(event: dict[str, Any], player_names: list[str]) -> str:
    """Render one event as a functional execution trace."""
    kind = event["type"]
    data = event["data"]
    if kind == "GAME_STARTED":
        return "Functional: create_game_state(config, player_names)"
    if kind == "DICE_ROLLED":
        return f"Functional: roll_die(state) -> process_roll(state, roll={data.get('roll')})"
    if kind == "NO_VALID_MOVES":
        return "Functional: process_roll(state, roll) -> advance_turn(state)"
    if kind == "TRIPLE_SIX_FORFEIT":
        return "Functional: process_roll(state, roll) -> advance_turn(state)"
    if kind == "BOT_DECISION":
        return "Functional: choose_move(state, player_idx, roll, valid_moves)"
    if kind == "TOKEN_MOVED":
        return f"Functional: apply_move(state, token_idx={data.get('token_idx')}, roll={data.get('roll')})"
    if kind == "TOKEN_CAPTURED":
        return "Functional: victim['steps'] = -1"
    if kind == "BLOCKADE_FORMED":
        return 'Functional: _emit(state, "BLOCKADE_FORMED")'
    if kind == "PLAYER_FINISHED":
        return "Functional: _all_finished(player, home_finish)"
    if kind == "BONUS_TURN":
        return "Functional: apply_move() -> bonus_turn"
    if kind == "TURN_ADVANCED":
        return "Functional: advance_turn(state)"
    if kind == "GAME_WON":
        return "Functional: state['status'] = WON"
    if kind == "GAME_DRAW":
        return "Functional: declare_mutual_draw(state) or advance_turn(state)"
    if kind == "GAME_QUIT":
        return "Functional: quit(state)"
    return f"Functional: {kind}"
