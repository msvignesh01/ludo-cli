"""Headless turn controller for the object-oriented tkinter application."""

from __future__ import annotations

from typing import Any

from ..shared.gui_support import (
    COMMENTARY_MODES,
    format_commentary,
    next_commentary_mode,
    speed_delay,
)
from .bot import BotPolicy
from .commentary import Commentary
from .engine import LudoGame


class GuiSession:
    """Own GUI playback state while delegating every rule decision to LudoGame."""

    def __init__(
        self,
        game: LudoGame,
        autoplay: bool = False,
        auto_delay: float | None = None,
    ) -> None:
        """Initialize playback controls around an existing match."""
        self.game = game
        self.autoplay = bool(autoplay)
        self.auto_delay = float(game.config["auto_delay"] if auto_delay is None else auto_delay)
        self.paused = False
        self.commentary_mode = game.config["commentary"]
        self.pending_roll: int | None = None
        self.valid_moves: list[int] = []
        self.previews: list[dict[str, Any]] = []
        self.event_cursor = 0
        self.bot_policy = BotPolicy()
        self.commentary = Commentary([player.name for player in game.players])

    def snapshot(self) -> dict[str, Any]:
        """Return the current canonical match snapshot."""
        return self.game.export_canonical_state()

    def is_automated_turn(self) -> bool:
        """Return whether bot policy or autoplay owns the active turn."""
        return self.game.status == "PLAYING" and (
            self.autoplay or self.game.current_player().kind == "bot"
        )

    def is_human_turn(self) -> bool:
        """Return whether a person must roll or choose the active move."""
        return self.game.status == "PLAYING" and not self.is_automated_turn()

    def can_roll(self) -> bool:
        """Return whether the human roll control is currently legal."""
        return self.is_human_turn() and self.pending_roll is None

    def next_delay_ms(self) -> int | None:
        """Return the next scheduler delay, or none when a person must act."""
        if self.paused or not self.is_automated_turn() or self.pending_roll is not None:
            return None
        return max(1, int(round(self.auto_delay * 1000)))

    def _clear_pending(self) -> None:
        """Discard move choices after a move or terminal transition."""
        self.pending_roll = None
        self.valid_moves = []
        self.previews = []

    def _roll(self) -> dict[str, Any]:
        """Roll and resolve automatic skips for the active player."""
        roll = self.game.roll_die()
        result = self.game.process_roll(roll)
        if result["event"] == "SELECT_MOVE":
            self.pending_roll = roll
            self.valid_moves = list(result["valid_moves"])
            player_index = self.game.current_player_index
            self.previews = [
                self.game.preview_move(player_index, token_idx, roll)
                for token_idx in self.valid_moves
            ]
        else:
            self._clear_pending()
        return result

    def roll_human(self) -> None:
        """Roll for a human seat that is waiting for its next action."""
        if not self.can_roll():
            raise ValueError("A human roll is not available now.")
        self._roll()

    def select_move(self, token_idx: int) -> dict[str, Any]:
        """Apply one selected legal token move."""
        if self.pending_roll is None or token_idx not in self.valid_moves:
            raise ValueError("That token is not a legal choice.")
        roll = self.pending_roll
        self._clear_pending()
        return self.game.apply_move(token_idx, roll)

    def run_automated_turn(self) -> bool:
        """Execute one complete bot or autoplay turn when available."""
        if not self.is_automated_turn() or self.pending_roll is not None:
            return False
        result = self._roll()
        if result["event"] == "SELECT_MOVE":
            roll = self.pending_roll
            valid_moves = list(self.valid_moves)
            decision = self.bot_policy.decision_details(self.game, roll, valid_moves)
            token_idx = int(decision["token_idx"])
            self.game.record_bot_decision(token_idx, roll, decision["reason"])
            self._clear_pending()
            self.game.apply_move(token_idx, roll)
        return True

    def step(self) -> bool:
        """Advance one roll or move without starting a background timer."""
        if self.game.status != "PLAYING":
            return False
        if self.pending_roll is not None:
            roll = self.pending_roll
            valid_moves = list(self.valid_moves)
            decision = self.bot_policy.decision_details(self.game, roll, valid_moves)
            self.select_move(int(decision["token_idx"]))
            return True
        if self.is_automated_turn():
            return self.run_automated_turn()
        self.roll_human()
        return True

    def set_paused(self, paused: bool) -> None:
        """Pause or resume background turn scheduling."""
        self.paused = bool(paused)

    def set_speed(self, speed: str) -> None:
        """Change the background delay without altering match rules."""
        self.auto_delay = speed_delay(speed)

    def cycle_commentary(self) -> str:
        """Rotate commentary and return the newly selected mode."""
        self.commentary_mode = next_commentary_mode(self.commentary_mode)
        return self.commentary_mode

    def set_commentary(self, mode: str) -> None:
        """Select a validated commentary mode."""
        normalized = mode.strip().lower()
        if normalized not in COMMENTARY_MODES:
            raise ValueError("Commentary must be gameplay, code, both, or off.")
        self.commentary_mode = normalized

    def drain_commentary(self) -> list[str]:
        """Return each unseen event once using the active narration style."""
        events = self.game.events[self.event_cursor :]
        self.event_cursor = len(self.game.events)
        lines: list[str] = []
        for event in events:
            lines.extend(
                format_commentary(
                    event,
                    self.commentary_mode,
                    self.commentary.gameplay(event),
                    self.commentary.code(event),
                )
            )
        return lines

    def declare_mutual_draw(self) -> None:
        """End the match by unanimous agreement and clear pending input."""
        self._clear_pending()
        self.game.declare_mutual_draw()

    def quit(self) -> None:
        """End the match cleanly and clear pending input."""
        self._clear_pending()
        self.game.quit()
