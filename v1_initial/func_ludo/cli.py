"""Zero-class functional wizard, hot-seat CLI, and auto-play application."""

from __future__ import annotations

import time
from typing import Any, Callable

from ..shared.cli_support import create_parser, resolve_cli_setup
from .bot import decision_details
from .commentary import code_message, gameplay_message
from .renderer import create_renderer_settings, render_board, render_moves
from .rules import (
    apply_move,
    declare_mutual_draw,
    get_valid_moves,
    process_roll,
    quit,
    record_bot_decision,
    roll_die,
)
from .state import create_game_state, export_canonical_state


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]
SleepFunction = Callable[[float], None]


def _write(context: dict[str, Any], text: str = "") -> None:
    """Write one line through the injected output adapter."""
    context["output_func"](text)


def _read(context: dict[str, Any], prompt: str) -> str | None:
    """Read input while converting EOF and interruption into clean cancellation."""
    try:
        return context["input_func"](prompt)
    except (EOFError, KeyboardInterrupt):
        _write(context, "\nInput ended; leaving the match cleanly.")
        quit(context["state"])
        return None


def _render(context: dict[str, Any]) -> None:
    """Render the current centralized state dictionary."""
    use_color, use_unicode = context["renderer_settings"]
    _write(context, render_board(export_canonical_state(context["state"]), use_color, use_unicode))
    _write(context)


def _show_new_events(context: dict[str, Any]) -> None:
    """Display new state events once using the selected commentary style."""
    state = context["state"]
    events = state["events"][context["event_cursor"] :]
    context["event_cursor"] = len(state["events"])
    mode = context["commentary_mode"]
    for event in events:
        if mode in {"gameplay", "both"}:
            prefix = "[Gameplay] " if mode == "both" else ""
            _write(context, prefix + gameplay_message(event, context["names"]))
        if mode in {"code", "both"}:
            prefix = "[Code] " if mode == "both" else ""
            _write(context, prefix + code_message(event, context["names"]))


def _confirm_quit(context: dict[str, Any]) -> bool:
    """Ask for explicit quit confirmation."""
    answer = _read(context, "Quit this match? [y/n]: ")
    if answer is None:
        return True
    confirmed = answer.strip().lower() in {"y", "yes"}
    if confirmed:
        quit(context["state"])
        _show_new_events(context)
    else:
        _write(context, "Quit cancelled.")
    return confirmed


def _request_draw(context: dict[str, Any]) -> bool:
    """Prompt every other player for unanimous draw agreement."""
    state = context["state"]
    active = state["players"][state["current_player"]]
    for other in state["players"]:
        if other["index"] == active["index"]:
            continue
        answer = _read(context, f"{other['name']}, accept a mutual draw? [y/n]: ")
        if answer is None:
            return True
        if answer.strip().lower() not in {"y", "yes"}:
            _write(context, "Draw declined; play continues.")
            return False
    declare_mutual_draw(state)
    _show_new_events(context)
    return True


def _set_command(context: dict[str, Any], command: str) -> None:
    """Change commentary or auto-play speed during a match."""
    parts = command.split(maxsplit=1)
    if parts[0] == "commentary":
        if len(parts) == 1:
            modes = ("gameplay", "code", "both", "off")
            next_mode = modes[(modes.index(context["commentary_mode"]) + 1) % len(modes)]
        else:
            next_mode = parts[1].strip().lower()
        if next_mode not in {"gameplay", "code", "both", "off"}:
            _write(context, "Commentary must be gameplay, code, both, or off.")
            return
        context["commentary_mode"] = next_mode
        _write(context, f"Commentary set to {next_mode}.")
        return
    speed = parts[1].strip().lower() if len(parts) > 1 else ""
    delays = {"slow": 0.8, "normal": 0.35, "fast": 0.05}
    if speed not in delays:
        _write(context, "Speed must be slow, normal, or fast.")
        return
    context["auto_delay"] = delays[speed]
    _write(context, f"Auto-play speed set to {speed}.")


def _choose_human_move(context: dict[str, Any], roll: int, valid_moves: list[int]) -> int | None:
    """Prompt until the human selects a forced legal move or quits."""
    state = context["state"]
    player_idx = state["current_player"]
    from .rules import preview_move

    previews = [preview_move(state, player_idx, token_idx, roll) for token_idx in valid_moves]
    use_color, use_unicode = context["renderer_settings"]
    _write(context, render_moves(previews, use_color, use_unicode))
    while True:
        answer = _read(context, f"Choose token 1-{len(valid_moves)} (q to quit): ")
        if answer is None:
            return None
        raw = answer.strip().lower()
        if raw in {"q", "quit"}:
            return None if _confirm_quit(context) else -1
        try:
            selection = int(raw)
        except ValueError:
            _write(context, "Please enter a listed token number.")
            continue
        if 1 <= selection <= len(valid_moves):
            return valid_moves[selection - 1]
        _write(context, "That token is not a legal choice.")


def _roll_and_move(context: dict[str, Any], automated: bool) -> None:
    """Roll, resolve skips, choose one move, and render the resulting state."""
    state = context["state"]
    roll = roll_die(state)
    result = process_roll(state, roll)
    _show_new_events(context)
    if result["event"] == "SELECT_MOVE":
        valid_moves = result["valid_moves"]
        if automated:
            decision = decision_details(state, state["current_player"], roll, valid_moves)
            token_idx = int(decision["token_idx"])
            record_bot_decision(state, token_idx, roll, decision["reason"])
            _show_new_events(context)
        else:
            token_idx = _choose_human_move(context, roll, valid_moves)
            if token_idx is None or token_idx == -1:
                return
        apply_move(state, token_idx, roll)
        _show_new_events(context)
    _render(context)


def _human_turn(context: dict[str, Any]) -> None:
    """Read one hot-seat command and execute it."""
    state = context["state"]
    player = state["players"][state["current_player"]]
    answer = _read(
        context,
        f"{player['name']}'s turn. ENTER=roll, draw, quit, "
        "commentary [gameplay|code|both|off], speed [slow|normal|fast]: ",
    )
    if answer is None:
        return
    command = answer.strip().lower()
    if not command:
        _roll_and_move(context, False)
    elif command in {"q", "quit"}:
        _confirm_quit(context)
    elif command == "draw":
        _request_draw(context)
    elif command.startswith("commentary") or command.startswith("speed"):
        _set_command(context, command)
    else:
        _write(context, "Unknown command. Use ENTER, draw, quit, commentary, or speed.")


def _bot_turn(context: dict[str, Any]) -> None:
    """Execute one automated roll with the configured delay."""
    if context["auto_delay"] > 0:
        context["sleep_func"](context["auto_delay"])
    _roll_and_move(context, True)


def run_cli(
    state: dict[str, Any],
    names: list[str],
    renderer_settings: tuple[bool, bool],
    autoplay: bool,
    auto_delay: float,
    input_func: InputFunction,
    output_func: OutputFunction,
    sleep_func: SleepFunction,
) -> int:
    """Run a functional match until win, draw, quit, or clean cancellation."""
    context: dict[str, Any] = {
        "state": state,
        "names": names,
        "renderer_settings": renderer_settings,
        "autoplay": autoplay,
        "auto_delay": auto_delay,
        "input_func": input_func,
        "output_func": output_func,
        "sleep_func": sleep_func,
        "commentary_mode": state["config"]["commentary"],
        "event_cursor": 0,
    }
    _render(context)
    _show_new_events(context)
    while state["status"] == "PLAYING":
        player = state["players"][state["current_player"]]
        if autoplay or player["kind"] == "bot":
            _bot_turn(context)
        else:
            _human_turn(context)
    _render(context)
    return 0


def main(
    argv: list[str] | None = None,
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
    sleep_func: SleepFunction = time.sleep,
) -> int:
    """Parse setup and run the zero-class functional CLI application."""
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.max_turns is not None and args.max_turns <= 0:
        parser.error("--max-turns must be a positive integer.")
    try:
        setup = resolve_cli_setup(args, input_func, output_func)
    except ValueError as exc:
        parser.error(str(exc))
    if setup is None:
        return 0
    if setup["config"]["ui"] == "gui":
        from .gui import main as gui_main

        return gui_main(setup, input_func=input_func, output_func=output_func)
    state = create_game_state(
        setup["config"],
        setup["names"],
        seed=setup["config"]["seed"],
        player_kinds=setup["kinds"],
    )
    renderer_settings = create_renderer_settings(not args.no_color)
    return run_cli(
        state,
        setup["names"],
        renderer_settings,
        setup["autoplay"],
        float(setup["config"]["auto_delay"]),
        input_func,
        output_func,
        sleep_func,
    )
