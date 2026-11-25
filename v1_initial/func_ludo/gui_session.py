"""Headless turn controller for the zero-class functional tkinter application."""

from __future__ import annotations

from typing import Any

from ..shared.gui_support import (
    COMMENTARY_MODES,
    format_commentary,
    next_commentary_mode,
    speed_delay,
)
from .bot import decision_details
from .commentary import code_message, gameplay_message
from .rules import (
    apply_move as apply_game_move,
    declare_mutual_draw as declare_game_draw,
    get_valid_moves as get_game_moves,
    process_roll as process_game_roll,
    preview_move,
    quit as quit_game,
    record_bot_decision as record_game_bot_decision,
    roll_die as roll_game_die,
)
from .state import export_canonical_state


def create_gui_session(
    state: dict[str, Any],
    autoplay: bool = False,
    auto_delay: float | None = None,
) -> dict[str, Any]:
    """Create an explicit playback context around functional match state."""
    return {
        "state": state,
        "autoplay": bool(autoplay),
        "auto_delay": float(state["config"]["auto_delay"] if auto_delay is None else auto_delay),
        "paused": False,
        "commentary_mode": state["config"]["commentary"],
        "pending_roll": None,
        "valid_moves": [],
        "previews": [],
        "event_cursor": 0,
    }


def get_snapshot(session: dict[str, Any]) -> dict[str, Any]:
    """Return the current canonical match snapshot."""
    return export_canonical_state(session["state"])


def is_automated_turn(session: dict[str, Any]) -> bool:
    """Return whether bot policy or autoplay owns the active turn."""
    state = session["state"]
    player = state["players"][state["current_player"]]
    return state["status"] == "PLAYING" and (session["autoplay"] or player["kind"] == "bot")


def is_human_turn(session: dict[str, Any]) -> bool:
    """Return whether a person must roll or choose the active move."""
    return session["state"]["status"] == "PLAYING" and not is_automated_turn(session)


def can_roll(session: dict[str, Any]) -> bool:
    """Return whether the human roll control is currently legal."""
    return is_human_turn(session) and session["pending_roll"] is None


def next_delay_ms(session: dict[str, Any]) -> int | None:
    """Return the next scheduler delay, or none when a person must act."""
    if session["paused"] or not is_automated_turn(session) or session["pending_roll"] is not None:
        return None
    return max(1, int(round(session["auto_delay"] * 1000)))


def _clear_pending(session: dict[str, Any]) -> None:
    """Discard move choices after a move or terminal transition."""
    session["pending_roll"] = None
    session["valid_moves"] = []
    session["previews"] = []


def _roll(session: dict[str, Any]) -> dict[str, Any]:
    """Roll and resolve automatic skips for the active player."""
    state = session["state"]
    roll = roll_game_die(state)
    result = process_game_roll(state, roll)
    if result["event"] == "SELECT_MOVE":
        session["pending_roll"] = roll
        session["valid_moves"] = list(result["valid_moves"])
        player_index = state["current_player"]
        session["previews"] = [
            preview_move(state, player_index, token_idx, roll)
            for token_idx in session["valid_moves"]
        ]
    else:
        _clear_pending(session)
    return result


def roll_human(session: dict[str, Any]) -> None:
    """Roll for a human seat that is waiting for its next action."""
    if not can_roll(session):
        raise ValueError("A human roll is not available now.")
    _roll(session)


def get_pending_roll(session: dict[str, Any]) -> int | None:
    """Return the roll waiting for token selection."""
    return session["pending_roll"]


def get_valid_moves(session: dict[str, Any]) -> list[int]:
    """Return legal token indices for the pending roll."""
    return list(session["valid_moves"])


def get_previews(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Return legal move previews for graphical controls."""
    return list(session["previews"])


def select_move(session: dict[str, Any], token_idx: int) -> dict[str, Any]:
    """Apply one selected legal token move."""
    if session["pending_roll"] is None or token_idx not in session["valid_moves"]:
        raise ValueError("That token is not a legal choice.")
    roll = session["pending_roll"]
    _clear_pending(session)
    return apply_game_move(session["state"], token_idx, roll)


def run_automated_turn(session: dict[str, Any]) -> bool:
    """Execute one complete bot or autoplay turn when available."""
    if not is_automated_turn(session) or session["pending_roll"] is not None:
        return False
    state = session["state"]
    result = _roll(session)
    if result["event"] == "SELECT_MOVE":
        roll = session["pending_roll"]
        valid_moves = list(session["valid_moves"])
        decision = decision_details(state, state["current_player"], roll, valid_moves)
        token_idx = int(decision["token_idx"])
        record_game_bot_decision(state, token_idx, roll, decision["reason"])
        _clear_pending(session)
        apply_game_move(state, token_idx, roll)
    return True


def step(session: dict[str, Any]) -> bool:
    """Advance one roll or move without starting a background timer."""
    state = session["state"]
    if state["status"] != "PLAYING":
        return False
    if session["pending_roll"] is not None:
        roll = session["pending_roll"]
        valid_moves = list(session["valid_moves"])
        decision = decision_details(state, state["current_player"], roll, valid_moves)
        select_move(session, int(decision["token_idx"]))
        return True
    if is_automated_turn(session):
        return run_automated_turn(session)
    roll_human(session)
    return True


def set_paused(session: dict[str, Any], paused: bool) -> None:
    """Pause or resume background turn scheduling."""
    session["paused"] = bool(paused)


def set_speed(session: dict[str, Any], speed: str) -> None:
    """Change the background delay without altering match rules."""
    session["auto_delay"] = speed_delay(speed)


def cycle_commentary(session: dict[str, Any]) -> str:
    """Rotate commentary and return the newly selected mode."""
    session["commentary_mode"] = next_commentary_mode(session["commentary_mode"])
    return session["commentary_mode"]


def set_commentary(session: dict[str, Any], mode: str) -> None:
    """Select a validated commentary mode."""
    normalized = mode.strip().lower()
    if normalized not in COMMENTARY_MODES:
        raise ValueError("Commentary must be gameplay, code, both, or off.")
    session["commentary_mode"] = normalized


def drain_commentary(session: dict[str, Any]) -> list[str]:
    """Return each unseen event once using the active narration style."""
    state = session["state"]
    events = state["events"][session["event_cursor"] :]
    session["event_cursor"] = len(state["events"])
    names = [player["name"] for player in state["players"]]
    lines: list[str] = []
    for event in events:
        lines.extend(
            format_commentary(
                event,
                session["commentary_mode"],
                gameplay_message(event, names),
                code_message(event, names),
            )
        )
    return lines


def declare_draw(session: dict[str, Any]) -> None:
    """End the match by unanimous agreement and clear pending input."""
    _clear_pending(session)
    declare_game_draw(session["state"])


def quit(session: dict[str, Any]) -> None:
    """End the match cleanly and clear pending input."""
    _clear_pending(session)
    quit_game(session["state"])
