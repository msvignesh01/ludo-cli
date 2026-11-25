"""Deterministic heuristic policy for object-oriented bot seats."""

from __future__ import annotations

from typing import Any

from .engine import LudoGame
from .models import Token


class BotPolicy:
    """Choose legal moves using the fixed showcase priority order."""

    def _can_be_captured(self, game: LudoGame, global_pos: int | None) -> bool:
        """Return whether an opponent can reach a tile with one die roll."""
        if global_pos is None or game.board.is_safe_tile(global_pos):
            return False
        player = game.current_player()
        for opponent in game.players:
            if opponent.index == player.index:
                continue
            for token in opponent.tokens:
                opponent_pos = game.board.get_global_pos(opponent.start_index, token.steps)
                if opponent_pos is None:
                    continue
                distance = (global_pos - opponent_pos) % game.board.track_len
                if 1 <= distance <= 6:
                    return True
        return False

    def _token_in_danger(self, game: LudoGame, token: Token) -> bool:
        """Return whether the active player's token is exposed to capture."""
        player = game.current_player()
        return self._can_be_captured(
            game,
            game.board.get_global_pos(player.start_index, token.steps),
        )

    def _score(self, game: LudoGame, token_idx: int, roll: int) -> tuple[int, ...]:
        """Build the lexicographic priority score for one legal move."""
        player = game.current_player()
        preview = game.preview_move(player.index, token_idx, roll)
        captured = len(preview["captured"])
        unlock = bool(game.config["kill_to_enter"] and player.captures_made == 0 and captured)
        escape = self._token_in_danger(game, player.tokens[token_idx]) and not self._can_be_captured(
            game,
            preview["global_pos"],
        )
        progress = int(preview["new_steps"])
        if preview["wrapped"]:
            progress += game.board.track_len
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
        self,
        game: LudoGame,
        roll: int,
        valid_moves: list[int],
    ) -> dict[str, Any]:
        """Return the selected token and the highest satisfied priority."""
        if not valid_moves:
            return {"token_idx": None, "reason": "No legal moves"}
        token_idx = max(valid_moves, key=lambda candidate: self._score(game, candidate, roll))
        player = game.current_player()
        preview = game.preview_move(player.index, token_idx, roll)
        if preview["reached_home"]:
            reason = "Finish Home"
        elif preview["captured"] and game.config["kill_to_enter"] and player.captures_made == 0:
            reason = "Unlock Kill-to-Enter"
        elif preview["captured"]:
            reason = "Capture"
        elif preview["safe"]:
            reason = "Safe tile"
        elif self._token_in_danger(game, player.tokens[token_idx]) and not self._can_be_captured(
            game,
            preview["global_pos"],
        ):
            reason = "Escape danger"
        else:
            reason = "Advance furthest"
        return {"token_idx": token_idx, "reason": reason}

    def choose_move(self, game: LudoGame, roll: int, valid_moves: list[int]) -> int | None:
        """Return one deterministic legal token index, or None when blocked."""
        token_idx = self.decision_details(game, roll, valid_moves)["token_idx"]
        return int(token_idx) if token_idx is not None else None
