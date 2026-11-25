"""Tkinter visual board and playback controls for the OOP Ludo engine."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from ..shared.gui_drawing import describe_move, draw_board, draw_tokens
from ..shared.gui_support import SPEED_DELAYS, build_gui_view_model
from .engine import LudoGame
from .gui_session import GuiSession


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


class LudoGUI:
    """Present one OOP match as an interactive tkinter board."""

    def __init__(
        self,
        session: GuiSession,
        paradigm: str = "OOP",
        input_func: InputFunction = input,
        output_func: OutputFunction = print,
    ) -> None:
        """Create the window and bind controls to the headless session."""
        self.session = session
        self.paradigm = paradigm
        self.input_func = input_func
        self.output_func = output_func
        self.root = tk.Tk()
        self.root.title(f"CIA1 Multiplayer Ludo - {paradigm}")
        self.root.configure(background="#0F172A")
        self.root.minsize(860, 620)
        self.after_id: str | None = None
        self.closed = False
        self.speed_names = tuple(SPEED_DELAYS)
        self.speed_index = min(
            range(len(self.speed_names)),
            key=lambda index: abs(SPEED_DELAYS[self.speed_names[index]] - session.auto_delay),
        )
        self.status_var = tk.StringVar()
        self.detail_var = tk.StringVar()
        self.player_vars: list[tk.StringVar] = []
        self.buttons: dict[str, ttk.Button] = {}
        self.move_frame = ttk.Frame()
        self.commentary_text = tk.Text()
        self.canvas = tk.Canvas()
        self._configure_style()
        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_style(self) -> None:
        """Apply a consistent dark theme to standard ttk widgets."""
        style = ttk.Style(self.root)
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

    def _button(self, parent: tk.Misc, text: str, command: Callable[[], None]) -> ttk.Button:
        """Create one standardized control button."""
        return ttk.Button(parent, text=text, command=command)

    def _build_widgets(self) -> None:
        """Lay out the board, player cards, controls, and commentary pane."""
        layout = ttk.Frame(self.root, padding=16)
        layout.grid(sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        layout.rowconfigure(0, weight=1)
        layout.columnconfigure(0, weight=1)
        layout.columnconfigure(1, weight=0)

        board_frame = ttk.Frame(layout)
        board_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        model = build_gui_view_model(self.session.snapshot())
        size = int(model["geometry"]["size"])
        self.cell_size = max(28, min(52, 520 // size))
        self.margin = 12
        dimension = size * self.cell_size + self.margin * 2
        self.canvas = tk.Canvas(
            board_frame,
            width=dimension,
            height=dimension,
            background="#0F172A",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        board_frame.rowconfigure(0, weight=1)
        board_frame.columnconfigure(0, weight=1)

        panel = ttk.Frame(layout, width=330)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        title = ttk.Label(
            panel,
            text=f"{self.paradigm} Ludo Showcase",
            font=("Segoe UI", 18, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        ttk.Label(panel, textvariable=self.status_var, font=("Segoe UI", 11, "bold")).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(panel, textvariable=self.detail_var, wraplength=310).grid(
            row=2, column=0, sticky="w", pady=(4, 10)
        )

        players_frame = ttk.LabelFrame(panel, text="Players", padding=8)
        players_frame.grid(row=3, column=0, sticky="ew")
        for player in self.session.game.players:
            variable = tk.StringVar()
            self.player_vars.append(variable)
            ttk.Label(
                players_frame,
                textvariable=variable,
                foreground=player.color_hex,
                font=("Segoe UI", 9, "bold"),
            ).grid(sticky="w", pady=2)

        self.move_frame = ttk.LabelFrame(panel, text="Legal moves", padding=8)
        self.move_frame.grid(row=4, column=0, sticky="ew", pady=(10, 10))

        controls = ttk.Frame(panel)
        controls.grid(row=5, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        self.buttons["roll"] = self._button(controls, "Roll die", self._roll)
        self.buttons["roll"].grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)
        self.buttons["pause"] = self._button(controls, "Pause", self._pause)
        self.buttons["pause"].grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)
        self.buttons["step"] = self._button(controls, "Step", self._step)
        self.buttons["step"].grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)
        self.buttons["speed"] = self._button(controls, "Speed: Normal", self._speed)
        self.buttons["speed"].grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)
        self.buttons["commentary"] = self._button(controls, "Commentary", self._commentary)
        self.buttons["commentary"].grid(row=2, column=0, columnspan=2, sticky="ew", pady=3)
        self.buttons["draw"] = self._button(controls, "Agree draw", self._request_draw)
        self.buttons["draw"].grid(row=3, column=0, sticky="ew", padx=(0, 4), pady=3)
        self.buttons["quit"] = self._button(controls, "Quit", self._quit)
        self.buttons["quit"].grid(row=3, column=1, sticky="ew", padx=(4, 0), pady=3)

        commentary_frame = ttk.LabelFrame(panel, text="Live commentary", padding=8)
        commentary_frame.grid(row=6, column=0, sticky="nsew", pady=(10, 0))
        panel.rowconfigure(6, weight=1)
        self.commentary_text = tk.Text(
            commentary_frame,
            height=10,
            wrap="word",
            background="#020617",
            foreground="#CBD5E1",
            insertbackground="#E2E8F0",
            relief="flat",
            font=("Consolas", 9),
        )
        self.commentary_text.grid(sticky="nsew")
        commentary_frame.rowconfigure(0, weight=1)
        commentary_frame.columnconfigure(0, weight=1)
        ttk.Label(
            panel,
            text="Human: Roll or choose a token. Bot/autoplay: Pause, Step, or change speed.",
            wraplength=310,
            font=("Segoe UI", 8),
        ).grid(row=7, column=0, sticky="w", pady=(8, 0))

    def _draw(self) -> None:
        """Redraw the canonical board and every token marker."""
        model = build_gui_view_model(self.session.snapshot())
        draw_board(self.canvas, model, self.cell_size, self.margin)
        draw_tokens(self.canvas, model, self.cell_size, self.margin)

    def _refresh_moves(self) -> None:
        """Rebuild legal move buttons for the pending human roll."""
        for child in self.move_frame.winfo_children():
            child.destroy()
        previews = self.session.previews
        if not previews:
            message = "Roll the die to begin." if self.session.can_roll() else "Waiting for the active player."
            if self.session.game.status != "PLAYING":
                message = "Match complete."
            ttk.Label(self.move_frame, text=message).grid(sticky="w")
            return
        ttk.Label(self.move_frame, text=f"Rolled {self.session.pending_roll}: choose one token.").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        for row, preview in enumerate(previews, start=1):
            token_idx = int(preview["token_idx"])
            self._button(
                self.move_frame,
                describe_move(preview),
                lambda index=token_idx: self._choose(index),
            ).grid(row=row, column=0, sticky="ew", pady=2)

    def _refresh_status(self) -> None:
        """Update match status, player statistics, and control availability."""
        snapshot = self.session.snapshot()
        status = snapshot["status"]
        if status == "PLAYING":
            player = self.session.game.current_player()
            if self.session.pending_roll is not None:
                heading = f"Rolled {self.session.pending_roll} - {player.name} to move"
            else:
                heading = f"Turn {snapshot['turn_count'] + 1} - {player.name} ({player.kind})"
        elif status == "WON":
            winner = snapshot["players"][int(snapshot["winner_index"])]
            heading = f"Winner: {winner['name']}"
        elif status == "DRAW":
            heading = f"Draw: {snapshot['draw_reason']}"
        else:
            heading = "Match quit"
        self.status_var.set(heading)
        self.detail_var.set(snapshot["last_event"])

        home_finish = int(snapshot["config"]["home_finish"])
        for player, variable in zip(self.session.game.players, self.player_vars):
            finished = sum(token.is_finished(home_finish) for token in player.tokens)
            variable.set(
                f"{player.name} [{player.kind}]  Home {finished}/{len(player.tokens)}  "
                f"Captures {player.captures_made}"
            )

        playing = status == "PLAYING"
        self.buttons["roll"].configure(state="normal" if self.session.can_roll() else "disabled")
        automated = self.session.is_automated_turn()
        self.buttons["pause"].configure(state="normal" if automated else "disabled")
        self.buttons["pause"].configure(text="Resume" if self.session.paused else "Pause")
        self.buttons["step"].configure(state="normal" if playing else "disabled")
        self.buttons["draw"].configure(state="normal" if playing else "disabled")
        self.buttons["quit"].configure(state="normal" if playing else "disabled")
        speed_name = self.speed_names[self.speed_index].capitalize()
        self.buttons["speed"].configure(text=f"Speed: {speed_name}")
        self.buttons["commentary"].configure(text=f"Commentary: {self.session.commentary_mode}")

    def _append_commentary(self, lines: list[str]) -> None:
        """Append newly emitted narration lines to the scrolling text pane."""
        if not lines:
            return
        self.commentary_text.configure(state="normal")
        for line in lines:
            self.commentary_text.insert("end", line + "\n")
        self.commentary_text.configure(state="disabled")
        self.commentary_text.see("end")

    def _cancel_schedule(self) -> None:
        """Cancel any pending tkinter after callback."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _schedule(self) -> None:
        """Schedule the next automated action when the session permits it."""
        self._cancel_schedule()
        delay = self.session.next_delay_ms()
        if delay is not None and not self.closed:
            self.after_id = self.root.after(delay, self._on_tick)

    def _refresh(self) -> None:
        """Redraw state, commentary, move controls, and automation scheduling."""
        if self.closed:
            return
        self._draw()
        self._refresh_status()
        self._refresh_moves()
        self._append_commentary(self.session.drain_commentary())
        self._schedule()

    def _on_tick(self) -> None:
        """Execute one scheduled bot or autoplay action."""
        self.after_id = None
        if self.closed:
            return
        self.session.step()
        self._refresh()

    def _roll(self) -> None:
        """Handle the human roll button."""
        try:
            self.session.roll_human()
        except ValueError as exc:
            messagebox.showwarning("Ludo", str(exc), parent=self.root)
        self._refresh()

    def _choose(self, token_idx: int) -> None:
        """Handle one graphical token selection."""
        try:
            self.session.select_move(token_idx)
        except ValueError as exc:
            messagebox.showwarning("Ludo", str(exc), parent=self.root)
        self._refresh()

    def _step(self) -> None:
        """Advance one roll or move while preserving pause state."""
        self.session.step()
        self._refresh()

    def _pause(self) -> None:
        """Toggle automatic scheduling without changing the match."""
        self.session.set_paused(not self.session.paused)
        self._refresh()

    def _speed(self) -> None:
        """Cycle slow, normal, and fast automation speeds."""
        self.speed_index = (self.speed_index + 1) % len(self.speed_names)
        self.session.set_speed(self.speed_names[self.speed_index])
        self._refresh()

    def _commentary(self) -> None:
        """Cycle gameplay, code, combined, and off commentary."""
        self.session.cycle_commentary()
        self._refresh()

    def _request_draw(self) -> None:
        """Confirm unanimous agreement before ending the match as a draw."""
        if messagebox.askyesno("Mutual draw", "Do all players agree to end this match as a draw?", parent=self.root):
            self.session.declare_mutual_draw()
            self._refresh()

    def _quit(self) -> None:
        """Confirm and cleanly quit the current match."""
        if messagebox.askyesno("Quit match", "Quit this match now?", parent=self.root):
            self.session.quit()
            self._refresh()

    def _on_close(self) -> None:
        """Confirm window closure and cancel all pending callbacks."""
        if self.session.game.status == "PLAYING":
            if not messagebox.askyesno("Close match", "Close and quit this match?", parent=self.root):
                return
            self.session.quit()
        self.closed = True
        self._cancel_schedule()
        self.root.destroy()

    def run(self) -> int:
        """Display the initial board and enter tkinter's event loop."""
        self._refresh()
        self.root.mainloop()
        return 0


def main(
    setup: dict[str, Any],
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
) -> int:
    """Create and run the object-oriented graphical application."""
    try:
        game = LudoGame(
            setup["config"],
            setup["names"],
            seed=setup["config"]["seed"],
            player_kinds=setup["kinds"],
        )
        session = GuiSession(game, autoplay=setup["autoplay"])
        return LudoGUI(session, "OOP", input_func, output_func).run()
    except tk.TclError as exc:
        output_func(f"Could not open the graphical interface: {exc}")
        return 1
