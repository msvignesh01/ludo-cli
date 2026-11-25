"""Tkinter visual board and playback controls for zero-class functional Ludo."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from ..shared.gui_drawing import describe_move, draw_board, draw_tokens
from ..shared.gui_support import SPEED_DELAYS, build_gui_view_model
from .gui_session import (
    can_roll,
    create_gui_session,
    cycle_commentary,
    declare_draw,
    drain_commentary,
    get_previews,
    get_snapshot,
    is_automated_turn,
    next_delay_ms,
    roll_human,
    select_move,
    set_paused,
    set_speed,
    step,
)
from .gui_session import quit as quit_session
from .state import create_game_state


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def _configure_style(root: tk.Tk) -> None:
    """Apply a consistent dark theme to standard ttk widgets."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TFrame", background="#0F172A")
    style.configure("TLabel", background="#0F172A", foreground="#E2E8F0")
    style.configure("TLabelframe", background="#111C33", foreground="#F8FAFC")
    style.configure("TLabelframe.Label", background="#111C33", foreground="#F8FAFC")
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
    style.map("TButton", background=[("active", "#334155")])


def _button(parent: tk.Misc, text: str, command: Callable[[], None]) -> ttk.Button:
    """Create one standardized control button."""
    return ttk.Button(parent, text=text, command=command)


def _build_widgets(context: dict[str, Any]) -> None:
    """Lay out the board, player cards, controls, and commentary pane."""
    root = context["root"]
    session = context["session"]
    paradigm = context["paradigm"]
    layout = ttk.Frame(root, padding=16)
    layout.grid(sticky="nsew")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    layout.rowconfigure(0, weight=1)
    layout.columnconfigure(0, weight=1)
    layout.columnconfigure(1, weight=0)

    board_frame = ttk.Frame(layout)
    board_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
    model = build_gui_view_model(get_snapshot(session))
    size = int(model["geometry"]["size"])
    context["cell_size"] = max(28, min(52, 520 // size))
    context["margin"] = 12
    dimension = size * context["cell_size"] + context["margin"] * 2
    context["canvas"] = tk.Canvas(
        board_frame,
        width=dimension,
        height=dimension,
        background="#0F172A",
        highlightthickness=0,
    )
    context["canvas"].grid(row=0, column=0, sticky="nsew")
    board_frame.rowconfigure(0, weight=1)
    board_frame.columnconfigure(0, weight=1)

    panel = ttk.Frame(layout, width=330)
    panel.grid(row=0, column=1, sticky="nsew")
    panel.columnconfigure(0, weight=1)
    ttk.Label(panel, text=f"{paradigm} Ludo Showcase", font=("Segoe UI", 18, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 10)
    )
    ttk.Label(panel, textvariable=context["status_var"], font=("Segoe UI", 11, "bold")).grid(
        row=1, column=0, sticky="w"
    )
    ttk.Label(panel, textvariable=context["detail_var"], wraplength=310).grid(
        row=2, column=0, sticky="w", pady=(4, 10)
    )

    players_frame = ttk.LabelFrame(panel, text="Players", padding=8)
    players_frame.grid(row=3, column=0, sticky="ew")
    for player in session["state"]["players"]:
        variable = tk.StringVar()
        context["player_vars"].append(variable)
        ttk.Label(
            players_frame,
            textvariable=variable,
            foreground=player["color_hex"],
            font=("Segoe UI", 9, "bold"),
        ).grid(sticky="w", pady=2)

    context["move_frame"] = ttk.LabelFrame(panel, text="Legal moves", padding=8)
    context["move_frame"].grid(row=4, column=0, sticky="ew", pady=(10, 10))

    controls = ttk.Frame(panel)
    controls.grid(row=5, column=0, sticky="ew")
    controls.columnconfigure(0, weight=1)
    controls.columnconfigure(1, weight=1)
    buttons = context["buttons"]
    buttons["roll"] = _button(controls, "Roll die", lambda: _roll(context))
    buttons["roll"].grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)
    buttons["pause"] = _button(controls, "Pause", lambda: _pause(context))
    buttons["pause"].grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)
    buttons["step"] = _button(controls, "Step", lambda: _step(context))
    buttons["step"].grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)
    buttons["speed"] = _button(controls, "Speed: Normal", lambda: _speed(context))
    buttons["speed"].grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)
    buttons["commentary"] = _button(controls, "Commentary", lambda: _commentary(context))
    buttons["commentary"].grid(row=2, column=0, columnspan=2, sticky="ew", pady=3)
    buttons["draw"] = _button(controls, "Agree draw", lambda: _request_draw(context))
    buttons["draw"].grid(row=3, column=0, sticky="ew", padx=(0, 4), pady=3)
    buttons["quit"] = _button(controls, "Quit", lambda: _quit(context))
    buttons["quit"].grid(row=3, column=1, sticky="ew", padx=(4, 0), pady=3)

    commentary_frame = ttk.LabelFrame(panel, text="Live commentary", padding=8)
    commentary_frame.grid(row=6, column=0, sticky="nsew", pady=(10, 0))
    panel.rowconfigure(6, weight=1)
    context["commentary_text"] = tk.Text(
        commentary_frame,
        height=10,
        wrap="word",
        background="#020617",
        foreground="#CBD5E1",
        insertbackground="#E2E8F0",
        relief="flat",
        font=("Consolas", 9),
    )
    context["commentary_text"].grid(sticky="nsew")
    commentary_frame.rowconfigure(0, weight=1)
    commentary_frame.columnconfigure(0, weight=1)
    ttk.Label(
        panel,
        text="Human: Roll or choose a token. Bot/autoplay: Pause, Step, or change speed.",
        wraplength=310,
        font=("Segoe UI", 8),
    ).grid(row=7, column=0, sticky="w", pady=(8, 0))


def _create_window(
    session: dict[str, Any],
    paradigm: str,
    input_func: InputFunction,
    output_func: OutputFunction,
) -> dict[str, Any]:
    """Create a tkinter root and its functional GUI context dictionary."""
    root = tk.Tk()
    root.title(f"CIA1 Multiplayer Ludo - {paradigm}")
    root.configure(background="#0F172A")
    root.minsize(860, 620)
    speed_names = tuple(SPEED_DELAYS)
    speed_index = min(
        range(len(speed_names)),
        key=lambda index: abs(SPEED_DELAYS[speed_names[index]] - session["auto_delay"]),
    )
    context: dict[str, Any] = {
        "session": session,
        "paradigm": paradigm,
        "input_func": input_func,
        "output_func": output_func,
        "root": root,
        "after_id": None,
        "closed": False,
        "speed_names": speed_names,
        "speed_index": speed_index,
        "status_var": tk.StringVar(),
        "detail_var": tk.StringVar(),
        "player_vars": [],
        "buttons": {},
        "move_frame": None,
        "commentary_text": None,
        "canvas": None,
        "cell_size": 40,
        "margin": 12,
    }
    _configure_style(root)
    _build_widgets(context)
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(context))
    return context


def _draw(context: dict[str, Any]) -> None:
    """Redraw the canonical board and every token marker."""
    model = build_gui_view_model(get_snapshot(context["session"]))
    draw_board(context["canvas"], model, context["cell_size"], context["margin"])
    draw_tokens(context["canvas"], model, context["cell_size"], context["margin"])


def _refresh_moves(context: dict[str, Any]) -> None:
    """Rebuild legal move buttons for the pending human roll."""
    frame = context["move_frame"]
    for child in frame.winfo_children():
        child.destroy()
    previews = get_previews(context["session"])
    if not previews:
        if can_roll(context["session"]):
            message = "Roll the die to begin."
        elif context["session"]["state"]["status"] != "PLAYING":
            message = "Match complete."
        else:
            message = "Waiting for the active player."
        ttk.Label(frame, text=message).grid(sticky="w")
        return
    ttk.Label(
        frame,
        text=f"Rolled {context['session']['pending_roll']}: choose one token.",
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))
    for row, preview in enumerate(previews, start=1):
        token_idx = int(preview["token_idx"])
        _button(
            frame,
            describe_move(preview),
            lambda index=token_idx: _choose(context, index),
        ).grid(row=row, column=0, sticky="ew", pady=2)


def _refresh_status(context: dict[str, Any]) -> None:
    """Update match status, player statistics, and control availability."""
    session = context["session"]
    state = session["state"]
    snapshot = get_snapshot(session)
    status = snapshot["status"]
    if status == "PLAYING":
        player = state["players"][state["current_player"]]
        if session["pending_roll"] is not None:
            heading = f"Rolled {session['pending_roll']} - {player['name']} to move"
        else:
            heading = f"Turn {snapshot['turn_count'] + 1} - {player['name']} ({player['kind']})"
    elif status == "WON":
        winner = snapshot["players"][int(snapshot["winner_index"])]
        heading = f"Winner: {winner['name']}"
    elif status == "DRAW":
        heading = f"Draw: {snapshot['draw_reason']}"
    else:
        heading = "Match quit"
    context["status_var"].set(heading)
    context["detail_var"].set(snapshot["last_event"])

    home_finish = int(snapshot["config"]["home_finish"])
    for player, variable in zip(state["players"], context["player_vars"]):
        finished = sum(token["steps"] == home_finish for token in player["tokens"])
        variable.set(
            f"{player['name']} [{player['kind']}]  Home {finished}/{len(player['tokens'])}  "
            f"Captures {player['captures_made']}"
        )

    playing = status == "PLAYING"
    buttons = context["buttons"]
    buttons["roll"].configure(state="normal" if can_roll(session) else "disabled")
    automated = is_automated_turn(session)
    buttons["pause"].configure(state="normal" if automated else "disabled")
    buttons["pause"].configure(text="Resume" if session["paused"] else "Pause")
    buttons["step"].configure(state="normal" if playing else "disabled")
    buttons["draw"].configure(state="normal" if playing else "disabled")
    buttons["quit"].configure(state="normal" if playing else "disabled")
    speed_name = context["speed_names"][context["speed_index"]].capitalize()
    buttons["speed"].configure(text=f"Speed: {speed_name}")
    buttons["commentary"].configure(text=f"Commentary: {session['commentary_mode']}")


def _append_commentary(context: dict[str, Any], lines: list[str]) -> None:
    """Append newly emitted narration lines to the scrolling text pane."""
    if not lines:
        return
    text_widget = context["commentary_text"]
    text_widget.configure(state="normal")
    for line in lines:
        text_widget.insert("end", line + "\n")
    text_widget.configure(state="disabled")
    text_widget.see("end")


def _cancel_schedule(context: dict[str, Any]) -> None:
    """Cancel any pending tkinter after callback."""
    if context["after_id"] is not None:
        context["root"].after_cancel(context["after_id"])
        context["after_id"] = None


def _schedule(context: dict[str, Any]) -> None:
    """Schedule the next automated action when the session permits it."""
    _cancel_schedule(context)
    delay = next_delay_ms(context["session"])
    if delay is not None and not context["closed"]:
        context["after_id"] = context["root"].after(delay, lambda: _on_tick(context))


def _refresh(context: dict[str, Any]) -> None:
    """Redraw state, commentary, move controls, and automation scheduling."""
    if context["closed"]:
        return
    _draw(context)
    _refresh_status(context)
    _refresh_moves(context)
    _append_commentary(context, drain_commentary(context["session"]))
    _schedule(context)


def _on_tick(context: dict[str, Any]) -> None:
    """Execute one scheduled bot or autoplay action."""
    context["after_id"] = None
    if context["closed"]:
        return
    step(context["session"])
    _refresh(context)


def _roll(context: dict[str, Any]) -> None:
    """Handle the human roll button."""
    try:
        roll_human(context["session"])
    except ValueError as exc:
        messagebox.showwarning("Ludo", str(exc), parent=context["root"])
    _refresh(context)


def _choose(context: dict[str, Any], token_idx: int) -> None:
    """Handle one graphical token selection."""
    try:
        select_move(context["session"], token_idx)
    except ValueError as exc:
        messagebox.showwarning("Ludo", str(exc), parent=context["root"])
    _refresh(context)


def _step(context: dict[str, Any]) -> None:
    """Advance one roll or move while preserving pause state."""
    step(context["session"])
    _refresh(context)


def _pause(context: dict[str, Any]) -> None:
    """Toggle automatic scheduling without changing the match."""
    set_paused(context["session"], not context["session"]["paused"])
    _refresh(context)


def _speed(context: dict[str, Any]) -> None:
    """Cycle slow, normal, and fast automation speeds."""
    context["speed_index"] = (context["speed_index"] + 1) % len(context["speed_names"])
    set_speed(context["session"], context["speed_names"][context["speed_index"]])
    _refresh(context)


def _commentary(context: dict[str, Any]) -> None:
    """Cycle gameplay, code, combined, and off commentary."""
    cycle_commentary(context["session"])
    _refresh(context)


def _request_draw(context: dict[str, Any]) -> None:
    """Confirm unanimous agreement before ending the match as a draw."""
    question = "Do all players agree to end this match as a draw?"
    if messagebox.askyesno("Mutual draw", question, parent=context["root"]):
        declare_draw(context["session"])
        _refresh(context)


def _quit(context: dict[str, Any]) -> None:
    """Confirm and cleanly quit the current match."""
    if messagebox.askyesno("Quit match", "Quit this match now?", parent=context["root"]):
        quit_session(context["session"])
        _refresh(context)


def _on_close(context: dict[str, Any]) -> None:
    """Confirm window closure and cancel all pending callbacks."""
    if context["session"]["state"]["status"] == "PLAYING":
        if not messagebox.askyesno("Close match", "Close and quit this match?", parent=context["root"]):
            return
        quit_session(context["session"])
    context["closed"] = True
    _cancel_schedule(context)
    context["root"].destroy()


def run_gui(context: dict[str, Any]) -> int:
    """Display the initial board and enter tkinter's event loop."""
    _refresh(context)
    context["root"].mainloop()
    return 0


def main(
    setup: dict[str, Any],
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> int:
    """Create and run the zero-class functional graphical application."""
    try:
        state = create_game_state(
            setup["config"],
            setup["names"],
            seed=setup["config"]["seed"],
            player_kinds=setup["kinds"],
        )
        session = create_gui_session(state, autoplay=setup["autoplay"])
        context = _create_window(session, "Functional", input_func, output_func)
        return run_gui(context)
    except tk.TclError as exc:
        output_func(f"Could not open the graphical interface: {exc}")
        return 1
