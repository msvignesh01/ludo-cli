"""Object-oriented wizard, hot-seat CLI, and auto-play application."""

from __future__ import annotations

import time
from typing import Any, Callable

from ..shared.cli_support import create_parser, resolve_cli_setup
from .bot import BotPolicy
from .commentary import Commentary
from .engine import LudoGame
from .renderer import CLIRenderer


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]
SleepFunction = Callable[[float], None]


class CliApplication:
    """Drive one OOP match through terminal input and event commentary."""

    def __init__(
        self,
        game: LudoGame,
        renderer: CLIRenderer,
        autoplay: bool = False,
        auto_delay: float = 0.35,
        input_func: InputFunction = input,
        output_func: OutputFunction = print,
        sleep_func: SleepFunction = time.sleep,
    ) -> None:
        """Initialize terminal adapters without changing game rules."""
        self.game = game
        self.renderer = renderer
        self.autoplay = autoplay
        self.auto_delay = auto_delay
        self.input_func = input_func
        self.output_func = output_func
        self.sleep_func = sleep_func
        self.bot_policy = BotPolicy()
        self.commentary = Commentary([player.name for player in game.players])
        self.commentary_mode = game.config["commentary"]
        self.event_cursor = 0

    def _write(self, text: str = "") -> None:
        """Write one line through the injected output adapter."""
        self.output_func(text)

    def _read(self, prompt: str) -> str | None:
        """Read input while converting EOF and interruption into clean cancellation."""
        try:
            return self.input_func(prompt)
        except (EOFError, KeyboardInterrupt):
            self._write("\nInput ended; leaving the match cleanly.")
            self.game.quit()
            return None

    def _render(self) -> None:
        """Render the current canonical board state."""
        self._write(self.renderer.render(self.game.export_canonical_state()))
        self._write()

    def _show_new_events(self) -> None:
        """Display events once using the selected commentary style."""
        events = self.game.events[self.event_cursor :]
        self.event_cursor = len(self.game.events)
        for event in events:
            if self.commentary_mode in {"gameplay", "both"}:
                prefix = "[Gameplay] " if self.commentary_mode == "both" else ""
                self._write(prefix + self.commentary.gameplay(event))
            if self.commentary_mode in {"code", "both"}:
                prefix = "[Code] " if self.commentary_mode == "both" else ""
                self._write(prefix + self.commentary.code(event))

    def _confirm_quit(self) -> bool:
        """Ask for explicit quit confirmation."""
        answer = self._read("Quit this match? [y/n]: ")
        if answer is None:
            return True
        confirmed = answer.strip().lower() in {"y", "yes"}
        if confirmed:
            self.game.quit()
            self._show_new_events()
        else:
            self._write("Quit cancelled.")
        return confirmed

    def _request_draw(self) -> bool:
        """Prompt every other player for unanimous draw agreement."""
        active = self.game.current_player()
        for other in self.game.players:
            if other.index == active.index:
                continue
            answer = self._read(f"{other.name}, accept a mutual draw? [y/n]: ")
            if answer is None:
                return True
            if answer.strip().lower() not in {"y", "yes"}:
                self._write("Draw declined; play continues.")
                return False
        self.game.declare_mutual_draw()
        self._show_new_events()
        return True

    def _set_command(self, command: str) -> None:
        """Change commentary or auto-play speed during a match."""
        parts = command.split(maxsplit=1)
        if parts[0] == "commentary":
            if len(parts) == 1:
                modes = ("gameplay", "code", "both", "off")
                next_mode = modes[(modes.index(self.commentary_mode) + 1) % len(modes)]
            else:
                next_mode = parts[1].strip().lower()
            if next_mode not in {"gameplay", "code", "both", "off"}:
                self._write("Commentary must be gameplay, code, both, or off.")
                return
            self.commentary_mode = next_mode
            self._write(f"Commentary set to {next_mode}.")
            return
        speed = parts[1].strip().lower() if len(parts) > 1 else ""
        delays = {"slow": 0.8, "normal": 0.35, "fast": 0.05}
        if speed not in delays:
            self._write("Speed must be slow, normal, or fast.")
            return
        self.auto_delay = delays[speed]
        self._write(f"Auto-play speed set to {speed}.")

    def _choose_human_move(self, roll: int, valid_moves: list[int]) -> int | None:
        """Prompt until the human selects a forced legal move or quits."""
        player = self.game.current_player()
        previews = [self.game.preview_move(player.index, token_idx, roll) for token_idx in valid_moves]
        self._write(self.renderer.render_moves(previews))
        while True:
            answer = self._read(f"Choose token 1-{len(valid_moves)} (q to quit): ")
            if answer is None:
                return None
            raw = answer.strip().lower()
            if raw in {"q", "quit"}:
                return None if self._confirm_quit() else -1
            try:
                selection = int(raw)
            except ValueError:
                self._write("Please enter a listed token number.")
                continue
            if 1 <= selection <= len(valid_moves):
                return valid_moves[selection - 1]
            self._write("That token is not a legal choice.")

    def _roll_and_move(self, automated: bool) -> None:
        """Roll, resolve skips, choose one move, and render the resulting state."""
        roll = self.game.roll_die()
        result = self.game.process_roll(roll)
        self._show_new_events()
        if result["event"] == "SELECT_MOVE":
            valid_moves = result["valid_moves"]
            if automated:
                decision = self.bot_policy.decision_details(self.game, roll, valid_moves)
                token_idx = int(decision["token_idx"])
                self.game.record_bot_decision(token_idx, roll, decision["reason"])
                self._show_new_events()
            else:
                token_idx = self._choose_human_move(roll, valid_moves)
                if token_idx is None:
                    return
                if token_idx == -1:
                    return
            self.game.apply_move(token_idx, roll)
            self._show_new_events()
        self._render()

    def _human_turn(self) -> None:
        """Read one hot-seat command and execute it."""
        player = self.game.current_player()
        answer = self._read(
            f"{player.name}'s turn. ENTER=roll, draw, quit, "
            "commentary [gameplay|code|both|off], speed [slow|normal|fast]: "
        )
        if answer is None:
            return
        command = answer.strip().lower()
        if not command:
            self._roll_and_move(False)
        elif command in {"q", "quit"}:
            self._confirm_quit()
        elif command == "draw":
            self._request_draw()
        elif command.startswith("commentary") or command.startswith("speed"):
            self._set_command(command)
        else:
            self._write("Unknown command. Use ENTER, draw, quit, commentary, or speed.")

    def _bot_turn(self) -> None:
        """Execute one automated roll with the configured delay."""
        if self.auto_delay > 0:
            self.sleep_func(self.auto_delay)
        self._roll_and_move(True)

    def run(self) -> int:
        """Run until win, draw, quit, or clean input cancellation."""
        self._render()
        self._show_new_events()
        while self.game.status == "PLAYING":
            player = self.game.current_player()
            if self.autoplay or player.kind == "bot":
                self._bot_turn()
            else:
                self._human_turn()
        self._render()
        return 0


def main(
    argv: list[str] | None = None,
    input_func: InputFunction = input,
    output_func: OutputFunction = print,
    sleep_func: SleepFunction = time.sleep,
) -> int:
    """Parse setup and run the object-oriented CLI application."""
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
    game = LudoGame(
        setup["config"],
        setup["names"],
        seed=setup["config"]["seed"],
        player_kinds=setup["kinds"],
    )
    renderer = CLIRenderer(use_color=not args.no_color)
    application = CliApplication(
        game,
        renderer,
        autoplay=setup["autoplay"],
        auto_delay=float(setup["config"]["auto_delay"]),
        input_func=input_func,
        output_func=output_func,
        sleep_func=sleep_func,
    )
    return application.run()
