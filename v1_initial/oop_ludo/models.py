"""Domain models for the object-oriented Ludo engine."""

from __future__ import annotations

from typing import Any

from ..shared.contracts import PLAYER_SPECS, get_start_indices


class Token:
    """Represent one token and its personal board coordinate."""

    def __init__(self, token_idx: int, label: str) -> None:
        """Initialize a token in the base yard."""
        self.token_idx = token_idx
        self.label = label
        self.steps = -1

    def is_in_base(self) -> bool:
        """Return whether the token is waiting in its yard."""
        return self.steps == -1

    def is_finished(self, home_finish: int) -> bool:
        """Return whether the token has reached home."""
        return self.steps == home_finish

    def is_on_outer_track(self, outer_last_step: int) -> bool:
        """Return whether the token occupies the shared outer track."""
        return 0 <= self.steps <= outer_last_step

    def is_in_home_stretch(self, track_len: int, home_finish: int) -> bool:
        """Return whether the token occupies its private home lane."""
        return track_len - 1 <= self.steps < home_finish

    def can_move(self, roll: int, home_finish: int, exact_home_roll: bool = True) -> bool:
        """Return whether a simple non-blockaded move is legal."""
        if self.is_in_base():
            return roll == 6
        if self.is_finished(home_finish):
            return False
        if exact_home_roll:
            return self.steps + roll <= home_finish
        return True

    def target_steps(self, roll: int) -> int:
        """Return the simple target coordinate for this roll."""
        if self.is_in_base() and roll == 6:
            return 0
        return self.steps + roll

    def move_to(self, new_steps: int) -> None:
        """Move the token to a new personal coordinate."""
        self.steps = new_steps

    def send_to_base(self) -> None:
        """Return the token to its base yard."""
        self.steps = -1


class Player:
    """Represent one seat, its tokens, and match statistics."""

    def __init__(
        self,
        index: int,
        name: str,
        kind: str,
        start_index: int,
        tokens_per_player: int,
    ) -> None:
        """Initialize a player using the fixed seat metadata."""
        spec = PLAYER_SPECS[index]
        self.index = index
        self.name = name
        self.kind = kind
        self.color = spec["color"]
        self.color_hex = spec["hex"]
        self.color_code = spec["ansi"]
        self.prefix = spec["prefix"]
        self.start_index = start_index
        self.captures_made = 0
        self.tokens = [
            Token(token_idx, f"{self.prefix}{token_idx + 1}")
            for token_idx in range(tokens_per_player)
        ]

    def all_finished(self, home_finish: int) -> bool:
        """Return whether every token has reached home."""
        return all(token.is_finished(home_finish) for token in self.tokens)

    def finished_count(self, home_finish: int) -> int:
        """Return the number of finished tokens."""
        return sum(token.is_finished(home_finish) for token in self.tokens)

    def tokens_at(self, board: Board, global_pos: int) -> list[Token]:
        """Return this player's tokens occupying a shared tile."""
        return [
            token
            for token in self.tokens
            if board.get_global_pos(self.start_index, token.steps) == global_pos
        ]


class Board:
    """Wrap locked board geometry and coordinate translation."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize geometry from a validated configuration."""
        self.config = config
        self.mode = config["mode"]
        self.track_len = int(config["track_len"])
        self.home_len = int(config["home_len"])
        self.tokens_per_player = int(config["tokens_per_player"])
        self.outer_last_step = int(config["outer_last_step"])
        self.home_finish = int(config["home_finish"])
        self.safe_tiles = frozenset(config["safe_tiles"])

    def get_start_indices(self) -> list[int]:
        """Return the configured seating positions."""
        return get_start_indices(self.config)

    def get_global_pos(self, start_index: int, steps: int) -> int | None:
        """Translate personal steps to a shared outer-track index."""
        if steps < 0 or steps > self.outer_last_step:
            return None
        return (start_index + steps) % self.track_len

    def is_safe_tile(self, global_pos: int | None) -> bool:
        """Return whether captures are disabled on a shared tile."""
        return (
            bool(self.config["safe_tiles_enabled"])
            and global_pos is not None
            and global_pos in self.safe_tiles
        )

    def format_position(self, start_index: int, steps: int) -> str:
        """Return a compact human-readable token position."""
        if steps == -1:
            return "BASE"
        if steps == self.home_finish:
            return "HOME"
        if steps >= self.track_len - 1:
            return f"H{steps - (self.track_len - 1) + 1}"
        global_pos = self.get_global_pos(start_index, steps)
        return f"T{global_pos:02d}" if global_pos is not None else "BASE"
